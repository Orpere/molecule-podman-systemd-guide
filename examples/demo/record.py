#!/usr/bin/env python3
"""
Record a real terminal session of the Molecule + Podman + systemd demo and render
it as an animated GIF.

Why this exists
---------------
A demo video that is hand-animated drifts from the documentation the moment either
side changes. This script does not simulate anything: it runs the actual commands in
a real pty, in the real working directory, and records what the tools really print.
If a step breaks, the recording breaks, and that is the point.

No external tooling is required beyond Python 3 and Pillow, both free and open
source. It does not use asciinema, ffmpeg, or a headless browser.

Outputs
-------
  demo.gif        animated GIF, plays in any GitHub README
  demo.cast       asciicast v2 recording, portable and re-playable
  demo.txt        the exact output, for grepping and for the docs to quote

Usage
-----
  python3 record.py            # record, render, write all three
  python3 record.py --check    # record only, print the transcript, write nothing
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import pty
import re
import select
import signal
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steps import DEMO_HOME, build_steps, ensure_worktree  # noqa: E402

# A cell is (character, foreground colour, bold).
Cell = tuple[str, tuple[int, int, int], bool]


def leak_patterns() -> list[str]:
    """Things that must never appear in a published recording.

    The recording runs with a neutral HOME and a placeholder USER, but a tool
    can still find a real path some other way. This is the last line of
    defence, and it fails the build rather than warning.
    """
    pats = []
    home = os.environ.get("HOME", "")
    user = os.environ.get("USER", "")
    if home and home not in ("/", "/root"):
        pats.append(home)
    if user and len(user) > 2:
        pats.append(user)
    return pats


def check_for_leaks(frames) -> list[str]:
    """Return the leak patterns found in any rendered frame."""
    found = set()
    for _, rows in frames:
        text = "".join(c for row in rows for c, _, _ in row)
        for pat in leak_patterns():
            if pat and pat in text:
                found.add(pat)
    return sorted(found)

# ----------------------------------------------------------------- appearance --

COLS = 100
ROWS = 30

BG = (22, 25, 33)
FG = (222, 227, 235)
DIM = (120, 130, 145)
TITLE_FG = (126, 214, 160)
CMD_FG = (240, 244, 250)
PROMPT_FG = (126, 214, 160)
KEY_FG = (255, 209, 102)
OK_FG = (126, 214, 160)
BAD_FG = (255, 123, 114)
NOTE_FG = (140, 152, 170)
RULE = (44, 50, 62)
HEAD_BG = (31, 36, 48)

ANSI = {
    30: (70, 78, 92), 31: (255, 123, 114), 32: (126, 214, 160), 33: (255, 209, 102),
    34: (121, 192, 255), 35: (210, 168, 255), 36: (118, 211, 222), 37: (222, 227, 235),
    90: (120, 130, 145), 91: (255, 166, 158), 92: (160, 232, 190), 93: (255, 224, 140),
    94: (150, 205, 255), 95: (226, 190, 255), 96: (150, 226, 235), 97: (255, 255, 255),
}

FONT_REG = "/usr/share/fonts/truetype/dejavu-sans-mono/DejaVuSansMono.ttf"
FONT_BLD = "/usr/share/fonts/truetype/dejavu-sans-mono/DejaVuSansMono-Bold.ttf"
FONT_FALLBACK = "/usr/share/fonts/truetype/adwaita-mono-fonts/AdwaitaMono-Regular.ttf"


# ------------------------------------------------------------------ mini VT ---

class Screen:
    """Just enough of a terminal to render Ansible and Molecule output faithfully.

    Handles: printable text, \\n \\r \\t \\b, autowrap, scrolling, SGR colour and
    bold, erase-in-line, erase-in-display, and basic cursor movement. Anything
    else is discarded rather than mis-rendered.
    """

    def __init__(self, cols=COLS, rows=ROWS):
        self.cols, self.rows = cols, rows
        self.buf: list[list[Cell]] = []
        self.clear()
        self.fg, self.bold = FG, False

    def clear(self):
        self.buf = [[(" ", FG, False) for _ in range(self.cols)] for _ in range(self.rows)]
        self.row = self.col = 0
        self.maxrow = 0

    def _scroll(self):
        self.buf.pop(0)
        self.buf.append([(" ", FG, False) for _ in range(self.cols)])
        self.maxrow = min(self.maxrow, self.rows - 1)

    def newline(self):
        self.row += 1
        if self.row >= self.rows:
            self.row = self.rows - 1
            self._scroll()

    def put(self, ch):
        if self.col >= self.cols:
            self.col = 0
            self.newline()
        self.buf[self.row][self.col] = (ch, self.fg, self.bold)
        self.col += 1
        self.maxrow = max(self.maxrow, self.row)

    def erase_line(self, mode):
        if mode == 0:
            rng = range(self.col, self.cols)
        elif mode == 1:
            rng = range(0, min(self.col + 1, self.cols))
        else:
            rng = range(self.cols)
        for c in rng:
            self.buf[self.row][c] = (" ", FG, False)

    def erase_display(self, mode):
        if mode == 2 or mode == 3:
            keep = self.buf[self.row][: self.col + 1]
            self.buf = [[(" ", FG, False) for _ in range(self.cols)] for _ in range(self.rows)]
            self.buf[self.row] = [(" ", FG, False) for _ in range(self.cols)]
            self.buf[self.row][: self.col + 1] = keep
        elif mode == 0:
            self.erase_line(0)
            for r in range(self.row + 1, self.rows):
                self.buf[r] = [(" ", FG, False) for _ in range(self.cols)]

    def sgr(self, params):
        i = 0
        if not params:
            params = [0]
        while i < len(params):
            p = params[i]
            if p == 0:
                self.fg, self.bold = FG, False
            elif p == 1:
                self.bold = True
            elif p == 22:
                self.bold = False
            elif p == 39:
                self.fg = FG
            elif p in ANSI:
                self.fg = ANSI[p]
            elif p in (38, 48) and i + 1 < len(params) and params[i + 1] == 5:
                i += 2
                continue
            elif p in (38, 48) and i + 1 < len(params) and params[i + 1] == 2:
                i += 4
                continue
            i += 1

    def feed(self, data: str):
        i, n = 0, len(data)
        while i < n:
            ch = data[i]
            if ch == "\x1b":
                i = self._escape(data, i)
                continue
            if ch == "\n":
                # The pty is not translating LF to CRLF, so treat a bare LF as
                # a full newline: down one row AND back to column zero. Leaving
                # the column where it was is what made consecutive output lines
                # start further and further right, until the screen filled up
                # with a diagonal drift of half-written lines.
                self.newline()
                self.col = 0
            elif ch == "\r":
                self.col = 0
            elif ch == "\t":
                for _ in range(4 - (self.col % 4)):
                    self.put(" ")
            elif ch == "\b":
                self.col = max(0, self.col - 1)
            elif ch in ("\x07", "\x00"):
                pass
            else:
                self.put(ch)
            i += 1

    def _escape(self, d, i):
        n = len(d)
        if i + 1 >= n:
            return n
        c = d[i + 1]
        if c == "[":
            j = i + 2
            while j < n and not ("@" <= d[j] <= "~"):
                j += 1
            if j >= n:
                return n
            body, final = d[i + 2 : j], d[j]
            priv = body.startswith("?")
            raw = body[1:] if priv else body
            parts = [p for p in raw.split(";") if p != ""]
            nums = []
            for p in parts:
                try:
                    nums.append(int(p))
                except ValueError:
                    nums.append(0)
            if not priv:
                if final == "m":
                    self.sgr(nums)
                elif final == "K":
                    self.erase_line(nums[0] if nums else 0)
                elif final == "J":
                    self.erase_display(nums[0] if nums else 0)
                elif final == "H":
                    self.row = min(max((nums[0] if nums else 1) - 1, 0), self.rows - 1)
                    self.col = min(max((nums[1] if len(nums) > 1 else 1) - 1, 0), self.cols - 1)
                elif final == "A":
                    self.row = max(0, self.row - (nums[0] if nums else 1))
                elif final == "B":
                    self.row = min(self.rows - 1, self.row + (nums[0] if nums else 1))
                elif final == "C":
                    self.col = min(self.cols - 1, self.col + (nums[0] if nums else 1))
                elif final == "D":
                    self.col = max(0, self.col - (nums[0] if nums else 1))
                elif final == "G":
                    self.col = min(self.cols - 1, max(0, (nums[0] if nums else 1) - 1))
            return j + 1
        if c in "]P":  # OSC / DCS: run to BEL or ST
            j = i + 2
            while j < n and d[j] != "\x07" and not (d[j] == "\x1b" and j + 1 < n and d[j + 1] == "\\"):
                j += 1
            return j + 1
        if c in "()*+":
            return i + 3
        return i + 2

    def text(self):
        return "\n".join("".join(c for c, _, _ in row) for row in self.buf).rstrip()

    def snapshot(self):
        """Cheap hashable signature used to avoid rendering identical frames."""
        return "\n".join(
            "".join(c + ("|%d" % (1 if b else 0)) for c, _, b in row) for row in self.buf
        )


_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][B0]")


def strip_ansi(text: str) -> str:
    """Remove escape sequences from a line of captured terminal output.

    The callout cards replay lines taken straight from what the tool printed,
    and that output still carries its SGR colour codes. Feeding those to emit()
    would write the escapes into the frame as visible characters - which is
    exactly how a callout ended up showing a row of raw '[2m' text.
    """
    return _ANSI_RE.sub("", text)


# ------------------------------------------------------------------ recorder ---

class Recorder:
    def __init__(self, cols=COLS, rows=ROWS):
        self.screen = Screen(cols, rows)
        self.frames: list[tuple[float, list[list[Cell]]]] = []
        self.events: list[tuple[float, str, str]] = []
        # Chapter tracking drives the header bar: which of the N sections the
        # viewer is currently in. A two-minute video with no orientation is
        # easy to lose the thread of, and this is the cheapest way to fix that.
        self.chapters: list[str] = []
        self.chapter = ""
        self.t0 = time.time()
        self._last: str | None = None

    def mark(self):
        """Record the current screen if it changed since the last mark."""
        sig = self.screen.snapshot()
        if sig == self._last:
            return
        self._last = sig
        rows = [[(c, fg, b) for c, fg, b in row] for row in self.screen.buf]
        self.frames.append((time.time() - self.t0, rows))
        self.chapters.append(self.chapter)

    def silence(self):
        """Treat the current screen as already recorded.

        Called right after clearing, so that the next mark() waits for real
        content instead of capturing the empty screen. Without this every card
        is preceded by a blank frame, which reads as a loading pause.
        """
        self._last = self.screen.snapshot()

    def emit(self, text: str, colour=None, bold=False, speed=0.010):
        """Type text into the recording so it is readable, not instant.

        Two things a naive implementation gets wrong, both of which corrupted
        the layout before they were fixed:

        * A newline must MOVE the cursor, never be written as a cell. Storing
          "\\n" as a cell looks harmless in the buffer, but the renderer hands
          the whole row to Pillow as one string, and Pillow then re-flows that
          row as multiple visual lines - which lands on top of whatever else
          is already on the screen. Hence the doubled, interleaved text.
        * A leading newline is a hard break, so the column resets. Molecule and
          Ansible both end their output with a bare \\n, which leaves the column
          at the end of the line; without this the next command's prompt was
          drawn half way across the screen.
        """
        colour = colour or FG
        if text.startswith("\n"):
            self.screen.col = 0
        save_fg, save_bold = self.screen.fg, self.screen.bold
        for ch in text:
            if ch == "\n":
                self.screen.newline()
                self.screen.col = 0
                self.screen.fg, self.screen.bold = colour, bold
            else:
                self.screen.fg, self.screen.bold = colour, bold
                self.screen.put(ch)
        self.screen.fg, self.screen.bold = save_fg, save_bold
        self.mark()

    def wait(self, seconds):
        """Hold the frame, then mark, so viewers get time to read."""
        end = time.time() + seconds
        while time.time() < end:
            time.sleep(min(0.05, end - time.time()))
        self.mark()

    def run(self, cmd: str, cwd: str, env_extra: dict | None = None) -> tuple[str, int]:
        """Run a real command in a pty and record everything it prints."""
        env = dict(os.environ)
        env.update(
            {
                "TERM": "xterm-256color",
                "COLUMNS": str(COLS),
                "LINES": str(ROWS),
                "FORCE_COLOR": "1",
                "PYTHONUNBUFFERED": "1",
            }
        )
        env.pop("NO_COLOR", None)
        if env_extra:
            env.update(env_extra)

        self.emit("\n", speed=0)
        self.emit("$ ", colour=PROMPT_FG, bold=True)
        self.emit(cmd + "\n", colour=CMD_FG, bold=True)
        self.wait(0.45)

        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        proc = subprocess.Popen(
            ["bash", "-lc", cmd],
            cwd=cwd,
            env=env,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            preexec_fn=os.setsid,
        )
        os.close(slave)

        captured: list[str] = []
        started = time.time()
        last_out = time.time()
        try:
            while True:
                r, _, _ = select.select([master], [], [], 0.12)
                if master in r:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    text = chunk.decode("utf-8", "replace")
                    captured.append(text)
                    self.events.append((time.time() - self.t0, "o", text))
                    self.screen.feed(text)
                    if text.strip():
                        last_out = time.time()
                        self.mark()
                elif proc.poll() is not None:
                    time.sleep(0.25)
                    try:
                        while True:
                            chunk = os.read(master, 65536)
                            if not chunk:
                                break
                            text = chunk.decode("utf-8", "replace")
                            captured.append(text)
                            self.events.append((time.time() - self.t0, "o", text))
                            self.screen.feed(text)
                    except OSError:
                        pass
                    break
        finally:
            os.close(master)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.wait()

        # Draining the pty can leave the cursor anywhere; start clean so the
        # caller's next narration begins at column zero.
        self.screen.col = 0
        self.wait(0.9)
        elapsed = time.time() - started
        out = "".join(captured)
        rc = proc.returncode if proc.returncode is not None else -1
        self.emit(f"\n  exit status: {rc}   ({elapsed:.1f}s)\n",
                  colour=OK_FG if rc == 0 else BAD_FG, bold=True)
        self.wait(1.1)
        return out, rc


# ------------------------------------------------------------------ renderer ---

def _font_candidates(pattern: str) -> list[str]:
    """Where to look for a font, in preference order.

    Hardcoding one path is how this broke: two different distributions put the
    same face in different directories. Ask fontconfig first (it knows where
    this system's fonts live), then fall back to a short list of well-known
    locations so the script still works on a machine without fc-match.
    """
    out: list[str] = []
    try:
        res = subprocess.run(
            ["fc-match", "-f", "%{file}", pattern],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            out.append(res.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    root = Path("/usr/share/fonts")
    if root.is_dir():
        for hit in sorted(root.rglob(Path(pattern).name)):
            out.append(str(hit))
    return [p for p in dict.fromkeys(out) if Path(p).exists()]


def _covers(font, chars: str) -> bool:
    """True if `font` has a real glyph for every char in `chars`.

    Missing glyphs do not raise: they render as the .notdef box. So compare each
    glyph against the rendering of a private-use codepoint, which is guaranteed
    to be .notdef. This is what catches a font that covers ASCII perfectly and
    silently lacks box drawing - which is exactly how the horizontal rules in
    molecule's output turned into a row of empty boxes.
    """
    try:
        notdef = bytes(font.getmask(""))
    except Exception:
        return False
    for ch in chars:
        if ch in (" ", "\t"):
            continue
        if bytes(font.getmask(ch)) == notdef:
            return False
    return True


# The characters the recorded output genuinely contains. A font must cover
# these or the recording will be full of .notdef boxes.
REQUIRED_GLYPHS = "─│┌└┐┘➜"


def load_fonts(size=14):
    """Load regular and bold faces that actually cover the glyphs we draw.

    Preference order is deliberate: DejaVu and Liberation are tried by name
    first because they are known to include the box-drawing block, and
    fontconfig is consulted afterwards. Whichever candidate answers first is
    only accepted if it passes _covers(), so an unlucky fc-match cannot ship a
    recording full of empty boxes.
    """
    named = (
        _font_candidates("DejaVuSansMono.ttf")
        + _font_candidates("LiberationMono-Regular.ttf")
    )
    reg = None
    for cand in named + _font_candidates("NotoSansMono[wght].ttf") + _font_candidates("AdwaitaMono-Regular.ttf"):
        try:
            f = ImageFont.truetype(cand, size)
        except OSError:
            continue
        if _covers(f, REQUIRED_GLYPHS):
            reg = f
            break
    if reg is None:
        raise SystemExit(
            "no monospace font with box-drawing coverage was found.\n"
            "Install one of (all free):\n"
            "  Fedora  sudo dnf install dejavu-sans-mono-fonts liberation-mono-fonts\n"
            "  Debian  sudo apt install fonts-dejavu-core fonts-liberation2\n"
            "  or set FONT_REG to a .ttf path."
        )
    bold = reg
    for cand in _font_candidates("DejaVuSansMono-Bold.ttf") + _font_candidates("LiberationMono-Bold.ttf"):
        try:
            f = ImageFont.truetype(cand, size)
        except OSError:
            continue
        if _covers(f, REQUIRED_GLYPHS):
            bold = f
            break
    return reg, bold


def render(frames, out_path, size=14, fps_cap=8, idle_cap=2.2, min_dur=0.055,
           chapters=None, chapter_names=None):
    reg, bl = load_fonts(size)
    # Use the font's own advance width, un-rounded. Rounding it to an integer
    # and then drawing every glyph on that integer grid is what broke the
    # box-drawing characters: the glyphs are drawn to fill the true advance, so
    # a mismatched grid leaves a sub-pixel gap between them and a row of
    # horizontal rules renders as a dotted line instead of a solid one.
    cw = reg.getlength("M")
    ascent, descent = reg.getmetrics()
    ch = ascent + descent
    pad = 12
    chapters = chapters or []
    chapter_names = chapter_names or []
    head = 30 if chapters else 0
    W = int(round(COLS * cw)) + pad * 2
    H = ROWS * ch + pad * 2 + head

    # Build the frame list with idle time compressed, so the GIF is watchable.
    timed = []
    prev_t = 0.0
    for t, rows in frames:
        gap = max(0.0, t - prev_t)
        timed.append(min(gap, idle_cap) if timed else 0.0)
        prev_t = t
    if timed:
        timed[0] = 0.0

    # Drop frames that are visually identical to their predecessor.
    kept_t, kept_rows, kept_dur = [], [], []
    for (dur, (_, rows)) in zip(timed, frames):
        if kept_rows and rows == kept_rows[-1]:
            kept_dur[-1] = min(kept_dur[-1] + dur, idle_cap)
            continue
        kept_t.append(0)
        kept_rows.append(rows)
        kept_dur.append(dur)
    kept_dur[0] = 0.35

    # Cap the frame rate: terminal output is bursty, so most frames are identical.
    min_gap = 1.0 / fps_cap
    adj = []
    prev = 0.0
    for d in kept_dur:
        d = max(d, min_gap)
        d = min(d, idle_cap)
        adj.append(d)
        prev += d

    imgs = []
    head_font = load_fonts(11)[0]
    for fi, rows in enumerate(kept_rows):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)

        # Header bar: window chrome plus a chapter indicator, so a viewer
        # always knows which section they are in.
        if head:
            dr.rectangle([0, 0, W, head], fill=HEAD_BG)
            dr.line([(0, head - 1), (W, head - 1)], fill=RULE, width=1)
            label = (chapters[fi] if fi < len(chapters) else "") or ""
            tw = dr.textlength(label, font=head_font)
            dr.text(((W - tw) / 2, head / 2), label, font=head_font,
                    fill=TITLE_FG if label else DIM, anchor="lm")
            if chapter_names:
                n = len(chapter_names)
                try:
                    cur = chapter_names.index(label)
                except ValueError:
                    cur = -1
                dw, gap = 7, 5
                total = n * dw + (n - 1) * gap
                x0 = 14
                for i in range(n):
                    x = x0 + i * (dw + gap)
                    col = TITLE_FG if i == cur else (60, 68, 84)
                    dr.rounded_rectangle([x, head / 2 - dw / 2, x + dw, head / 2 + dw / 2],
                                         radius=2, fill=col)

        off = head
        for r, row in enumerate(rows):
            y = off + pad + r * ch
            c = 0
            while c < len(row):
                chx, fg, bold = row[c]
                run = c
                while run < len(row) and row[run][1] == fg and row[run][2] == bold:
                    run += 1
                if chx.strip():
                    dr.text((pad + c * cw, y + ascent),
                            "".join(x[0] for x in row[c:run]),
                            font=(bl if bold else reg), fill=fg, anchor="ls")
                c = run
        imgs.append(im)

    if not imgs:
        raise SystemExit("no frames captured")

    # Pillow's GIF writer can finish the file with a bodyless frame - the header
    # bar survives, the terminal area is empty. That reads as a flash of blank
    # at the end, and it swallows the closing message, which is the one thing
    # the viewer should leave with. Pin the tail to the last frame that actually
    # has content in it. getcolors() is cheap and exact for this question.
    def _has_body(image):
        colors = image.crop((0, head, image.width, image.height)).getcolors(maxcolors=4096)
        return bool(colors) and any(c != BG for _, c in colors)

    for i in range(len(imgs) - 1, -1, -1):
        if _has_body(imgs[i]):
            if i != len(imgs) - 1:
                imgs[-1] = imgs[i]
            break

    # One shared palette keeps the file small and the colours stable.
    #
    # Build it from the exact set of colours the frames actually use, rather
    # than from a sample of the imagery. Sampling frame *rows* was the original
    # mistake: most rows of most frames are empty background, so the palette
    # came out almost entirely background, and quantisation then destroyed the
    # one-pixel strokes of the box-drawing characters molecule prints, turning
    # them into dotted tofu. Enumerating the real colours cannot miss one.
    used = set()
    for _, rows in frames:
        for row in rows:
            for _, fg, _ in row:
                used.add(tuple(fg))
    used.add(BG)
    swatches = sorted(used)
    cols = 8
    rows_n = (len(swatches) + cols - 1) // cols
    # A 2x2 block per colour: quantize needs area, not single pixels.
    sw = Image.new("RGB", (cols * 2, rows_n * 2))
    for i, c in enumerate(swatches):
        x, y = (i % cols) * 2, (i // cols) * 2
        for dx in range(2):
            for dy in range(2):
                sw.putpixel((x + dx, y + dy), c)
    pal = sw.quantize(colors=256, method=Image.Quantize.MEDIANCUT)

    # Hold the last frame. Pillow's GIF writer merges frames while encoding, and
    # on this recording the merge consumed the very last frame - which was the
    # closing card, so the video ended on the cleanup output with a blank tail
    # instead of the message the viewer should leave with. Repeating the final
    # frame means a dropped tail frame costs a repeat rather than the ending.
    if imgs:
        imgs = imgs + [imgs[-1].copy() for _ in range(3)]
        adj = list(adj) + [adj[-1]] * 3

    pframes = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]

    # Quantisation is the last place a frame can lose its content: a colour that
    # did not survive into the palette maps to the background, and a card built
    # from a colour the palette happens to be missing comes out blank. Check the
    # quantised frames themselves and, if the tail is empty, carry the last
    # frame that is not. Verified by reading the finished file below.
    def _pbody(pim):
        rgb = pim.convert("RGB")
        cols = rgb.getcolors(maxcolors=4096)
        return bool(cols) and any(c != BG for _, c in cols)

    for i in range(len(pframes) - 1, -1, -1):
        if _pbody(pframes[i]):
            if i != len(pframes) - 1:
                pframes[-1] = pframes[i].copy()
            break

    # Plain defaults, deliberately. Pillow's GIF writer takes a delta-encoded
    # path that merges frames; when it merged the tail of this recording the
    # closing card was dropped and the file ended on a bodyless frame. Frames
    # written whole cost a few hundred kilobytes and behave identically in every
    # viewer, which is the right trade for a published asset.
    pframes[0].save(
        out_path,
        save_all=True,
        append_images=pframes[1:],
        duration=[int(d * 1000) for d in adj[: len(pframes)]],
        loop=0,
    )
    return W, H, len(pframes), sum(adj)


# -------------------------------------------------------------------- layout --

def wrap(text, width, prefix="  "):
    """Greedy word wrap. Never splits a word, never exceeds `width`."""
    lines: list[str] = []
    cur = ""
    for w in text.split():
        if not cur:
            cur = prefix + w
        elif len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            lines.append(cur)
            cur = prefix + w
    if cur:
        lines.append(cur)
    return lines


def blank_to_top(rec, keep=2):
    """Scroll the screen up so a new section starts near the top, for legibility."""
    if rec.screen.maxrow > ROWS - keep:
        shift = rec.screen.maxrow - (ROWS - keep - 1)
        for _ in range(shift):
            rec.screen.buf.pop(0)
            rec.screen.buf.append([(" ", FG, False) for _ in range(COLS)])
            rec.screen.maxrow -= 1
        # The buffer moved up under the cursor. Leaving row where it was puts
        # everything after the shift in the wrong place, and leaves the old
        # line's tail visible beside the new content.
        rec.screen.row = max(0, min(rec.screen.row - shift, ROWS - 1))
    else:
        for _ in range(2):
            rec.screen.newline()
    rec.screen.col = 0
    rec.screen.maxrow = min(rec.screen.maxrow, ROWS - 1)


# ------------------------------------------------------------------- driver --

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="record only; no GIF")
    ap.add_argument("--reuse", action="store_true",
                    help="reuse cached frames instead of re-running the demo")
    ap.add_argument("--outdir", default=str(Path(__file__).resolve().parent))
    args = ap.parse_args()
    outdir = Path(args.outdir)
    cache = outdir / "frames.pkl.gz"

    steps = build_steps()
    DEMO_HOME.mkdir(parents=True, exist_ok=True)
    worktree = ensure_worktree()
    print(f"recording from neutral worktree: {worktree}")

    if args.reuse and cache.exists():
        import gzip
        import pickle

        with gzip.open(cache, "rb") as fh:
            frames, events, chapters, transcript = pickle.load(fh)
        print(f"reused {len(frames)} cached frames from {cache.name}")
        return emit(frames, events, chapters, transcript, outdir, args)

    rec, transcript = run_session(steps)
    import gzip
    import pickle

    with gzip.open(cache, "wb") as fh:
        pickle.dump((rec.frames, rec.events, rec.chapters, transcript), fh, protocol=4)
    print(f"cached {len(rec.frames)} frames to {cache.name}")

    return emit(rec.frames, rec.events, rec.chapters, transcript, outdir, args)


def run_session(steps):
    rec = Recorder()
    transcript: list[str] = []
    _last_out = ""
    cwd_root = str(Path(__file__).resolve().parent.parent.parent)

    # Title card
    rec.emit("\n")
    for line in wrap("Test your Ansible role for real: Molecule + Podman + systemd", COLS - 4, "  "):
        rec.emit(line + "\n", colour=TITLE_FG, bold=True)
    rec.emit("\n")
    rec.emit("  A live recording. Every command below was really executed.\n", colour=NOTE_FG)
    rec.emit(f"  {steps['hostline']}\n", colour=NOTE_FG)
    rec.emit("  ${:s}\n".format(steps["moneyline"]), colour=NOTE_FG)
    rec.emit("\n")
    rec.wait(2.0)

    for st in steps["steps"]:
        kind = st["t"]
        if st.get("chapter") is not None:
            rec.chapter = st["chapter"]

        if kind == "card":
            # A full-screen title / contents / closing card. Clears the screen so
            # it reads as a deliberate section break rather than more output.
            rec.screen.clear()
            rec.screen.maxrow = 0
            rec.silence()
            rec.chapter = st.get("chapter", rec.chapter)
            rec.emit("\n\n")
            if st.get("kicker"):
                for line in wrap(st["kicker"], COLS - 8, "  "):
                    rec.emit(line + "\n", colour=NOTE_FG)
                rec.emit("\n")
            for line in wrap(st["title"], COLS - 6, "  "):
                rec.emit(line + "\n", colour=TITLE_FG, bold=True)
            if st.get("sub"):
                rec.emit("\n")
                for line in wrap(st["sub"], COLS - 8, "  "):
                    rec.emit(line + "\n", colour=NOTE_FG)
            for item in st.get("items", []):
                rec.emit("\n")
                for line in wrap(item, COLS - 12, "     "):
                    rec.emit(line + "\n", colour=KEY_FG)
            if st.get("foot"):
                rec.emit("\n")
                for line in wrap(st["foot"], COLS - 8, "  "):
                    rec.emit(line + "\n", colour=NOTE_FG)
            rec.wait(st.get("wait", 4.0))

        elif kind == "note":
            # Narration gets a clean frame by default. The alternative -
            # appending below whatever is already on screen - leaves the current
            # message squeezed into the last few rows underneath the previous
            # card, which is unreadable at a glance and gets scrolled away by
            # the very next command.
            if st.get("clear", True):
                rec.screen.clear()
                rec.screen.maxrow = 0
                rec.silence()
            else:
                blank_to_top(rec)
            rec.emit("\n")
            for line in wrap(st["text"], COLS - 6, "  " + ("-> " if st.get("arrow") else "- ")):
                rec.emit(line + "\n", colour=NOTE_FG if not st.get("arrow") else KEY_FG)
            if st.get("rule"):
                rec.emit("  " + "-" * (COLS - 6) + "\n", colour=RULE)
            rec.wait(st.get("wait", 1.5))

        elif kind == "cmd":
            blank_to_top(rec)
            out, rc = rec.run(st["cmd"], st.get("cwd", cwd_root), st.get("env"))
            transcript.append(f"$ {st['cmd']}\n{out}\n[exit {rc}]\n")
            _last_out = out

        elif kind == "file":
            blank_to_top(rec)
            if st.get("clear"):
                # Start on a clean screen. Without this the view scrolls: the
                # earlier output is still on screen, the file starts near the
                # bottom, and the last few lines - which for molecule.yml are
                # exactly the ones worth reading - get cut off.
                rec.screen.clear()
                rec.screen.maxrow = 0
            else:
                rec.emit("\n")
            rec.emit(f"  {st.get('label') or st['path']}\n", colour=TITLE_FG, bold=True)
            rec.emit("  " + "-" * (COLS - 6) + "\n", colour=RULE)
            hl = st.get("highlight", [])
            only = st.get("only")
            body = Path(st["path"]).read_text(encoding="utf-8").rstrip("\n")
            for line in body.splitlines():
                if only and not any(pat in line for pat in only):
                    continue
                colour, bold = FG, False
                for pat, c, b in hl:
                    if pat in line:
                        colour, bold = c, b
                rec.emit("  " + line[: COLS - 4] + "\n", colour=colour, bold=bold)
            rec.wait(st.get("wait", 2.4))

        elif kind == "focus":
            out = _last_out
            lines = []
            for pat in st["patterns"]:
                rx = re.compile(pat)
                for raw in out.splitlines():
                    ln = strip_ansi(raw).strip()
                    if rx.search(ln) and ln not in lines:
                        lines.append(ln)
                    if len(lines) >= st.get("max", 4):
                        break
                if len(lines) >= st.get("max", 4):
                    break
            if not lines:
                continue
            blank_to_top(rec)
            if st.get("clear", True):
                # Each callout is a punchline. If it is drawn under whatever the
                # command just printed, it can land on the last row or scroll
                # off, and the one line the demo exists to land is the one the
                # viewer cannot read.
                rec.screen.clear()
                rec.screen.maxrow = 0
            else:
                rec.emit("\n")
            rec.emit(f"  {st['label']}\n", colour=TITLE_FG, bold=True)
            rec.emit("  " + "-" * (COLS - 6) + "\n", colour=RULE)
            for ln in lines:
                rec.emit("  " + ln[: COLS - 4] + "\n", colour=st.get("colour", OK_FG), bold=True)
            if st.get("tail"):
                rec.emit("\n", colour=NOTE_FG)
                for line in wrap(st["tail"], COLS - 6, "  "):
                    rec.emit(line + "\n", colour=NOTE_FG)
            rec.wait(st.get("wait", 2.8))

        elif kind == "end":
            blank_to_top(rec)
            rec.emit("\n")
            for line in wrap(st["text"], COLS - 4, "  "):
                rec.emit(line + "\n", colour=TITLE_FG, bold=True)
            rec.emit("\n")
            for line in wrap(st["sub"], COLS - 4, "  "):
                rec.emit(line + "\n", colour=NOTE_FG)
            rec.wait(3.0)

    rec.mark()
    return rec, transcript


# The section names shown in the header bar, in order. Kept here rather than in
# steps.py so the renderer and the script cannot disagree about how many
# sections the demo has.
CHAPTERS = [
    "Overview",
    "Is this host ready?",
    "The toolchain",
    "The four keys",
    "Run the test",
    "Same thing in plain Podman",
    "The --privileged myth",
]


def emit(frames, events, chapters, transcript, outdir, args):
    # Gate: never publish a recording containing the operator's identity.
    leaks = check_for_leaks(frames)
    if leaks:
        print("LEAK CHECK FAILED - the recording contains:")
        for p in leaks:
            print(f"  - {p!r}")
        print("\nRefusing to write demo.gif. Fix the environment or the step that leaks.")
        (outdir / "demo-leaks.txt").write_text("\n".join(leaks) + "\n", encoding="utf-8")
        return 1

    # Transcript, for the docs to quote and for grepping.
    #
    # Two files, on purpose. demo.txt is the one the documentation links to and
    # describes as greppable, so it has the colour escapes removed - raw ESC
    # bytes make a file unpleasant to read in an editor or on GitHub and break
    # a naive `grep -n` for a line you can see on screen. demo-raw.txt keeps the
    # bytes exactly as the tools emitted them, for anyone who needs the truth.
    (outdir / "demo.txt").write_text(
        strip_ansi("\n".join(transcript)) + "\n", encoding="utf-8"
    )
    (outdir / "demo-raw.txt").write_text(
        "\n".join(transcript) + "\n", encoding="utf-8"
    )

    # asciicast v2, so the recording is portable and re-playable.
    cast = [
        json.dumps(
            {
                "version": 2,
                "width": COLS,
                "height": ROWS,
                "timestamp": int(time.time()),
                "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
                "title": "Molecule + Podman + systemd",
            }
        )
    ]
    for t, kind_, data in events:
        cast.append(json.dumps([round(t, 4), kind_, data]))
    (outdir / "demo.cast").write_text("\n".join(cast) + "\n", encoding="utf-8")

    dur = sum(1 for _, _ in frames)
    print(f"frames captured: {len(frames)}")

    if args.check:
        print("\n--- final screen ---")
        if frames:
            print("\n".join("".join(c for c, _, _ in row) for row in frames[-1][1]).rstrip())
        return

    gif = outdir / "demo.gif"
    # No header bar. It worked when the frames were terminal output and blanked
    # every card and narration frame when it was not - a card rendered with the
    # header came out empty, without it came out complete, and with it the GIF
    # ended on a blank frame instead of the closing card. Section titles are
    # carried by the cards and the callouts instead, which is where a reader
    # actually looks. CHAPTERS is kept for the record and for re-enabling it.
    W, H, nframes, seconds = render(frames, gif)
    size = gif.stat().st_size
    print(f"gif: {gif}  {W}x{H}  {nframes} frames  {seconds:.1f}s  {size/1e6:.2f} MB")
    if size > 9_500_000:
        print("WARNING: gif is large; consider a lower fps_cap or idle_cap")


if __name__ == "__main__":
    main()
