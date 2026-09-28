# `examples/demo/` — how the demo is recorded

> **What you will be able to do:** watch the demo, play the raw recording, grep the exact
> terminal output, and re-record or re-render it yourself.

This directory holds the demo that appears at the top of [`README.md`](../../README.md) and is
walked through in [`docs/demo.md`](../../docs/demo.md). The animation is not drawn by hand and
is not a screen recording made on someone's desktop. It is a real terminal session, executed
command by command, rendered to an animated GIF by a script that lives here.

---

## The three artefacts

| File | What it is | What it is for |
|---|---|---|
| **`demo.gif`** | The animated GIF: **866 × 534 px, 248 frames, ~1 min 54 s, 2.1 MB.** | What readers see. It plays inline on GitHub as an ordinary Markdown image, so there is no build step, no JavaScript, and no external player. [`README.md`](../../README.md) embeds it with a full `alt`. |
| **`demo.cast`** | An [asciicast](https://asciinema.org/) v2 recording, **52 KB**, at 100 × 30 characters. | The portable, text-accurate original. Play it with `asciinema play examples/demo/demo.cast`. It carries every keystroke and every colour as data, so it is the artefact to trust if the GIF's pixels ever look wrong. |
| **`demo.txt`** | The terminal output of the whole session with colour escapes removed, **33 KB**. | The evidence. Grep it, quote it, link to it. Every quoted command and every quoted line in this repository's documentation comes from this file. Escapes are stripped so a `grep -n` for a line you can see on screen actually finds it. |
| **`demo-raw.txt`** | The same session with the colour bytes left exactly as the tools emitted them, **33 KB**. | The unedited truth. Use it when you need to prove what a tool really wrote rather than what it looked like. |

Plus the two files that produce them:

| File | What it is |
|---|---|
| **`record.py`** | The recorder and renderer. Runs the commands in a pty, renders the frames, and runs the leak check. |
| **`steps.py`** | The demo script: what is said, what runs, which output lines each callout card shows. Edit this to change the demo; edit `record.py` to change how it is drawn. |

`frames.pkl.gz` is a cache of the captured frames, written so that `--reuse` can re-render
without re-running anything. It is a build artefact, not a source file.

---

## How to use the three artefacts

**Watch it.** The GIF is the point; open `README.md` and it plays there, and so does
[`docs/demo.md`](../../docs/demo.md). If you have it on disk, most image viewers and every
browser will play it.

**Play the raw recording.** This is the one to use when you want to see the timing, or to step
through at your own pace, or to copy text out:

```bash
asciinema play examples/demo/demo.cast
```

`asciinema` is free and open source. If you do not have it, the `.cast` file is a text file: each
line after the header is a JSON array of `[time, "o", data]`, so you can read it with nothing
installed at all.

**Grep the output.** This is how the documentation was written, and it is how you check any claim
on the site against something real:

```bash
grep -n "ok="            examples/demo/demo.txt   # the non-vacuity check
grep -n "PID 1"          examples/demo/demo.txt   # the payoff of beat 4
grep -n "RESULT:"        examples/demo/demo.txt   # the pre-flight verdict
grep -n "no hosts matched" examples/demo/demo.txt # absent — and that absence is the point
```

Anything quoted on a documentation page should be findable here. If you cannot find it, that is a
documentation bug worth reporting.

---

## How to re-record it

```bash
python3 examples/demo/record.py            # record for real, render, write all three artefacts
python3 examples/demo/record.py --check    # record only, print the transcript, write no GIF
python3 examples/demo/record.py --reuse    # re-render from cached frames, without re-running
```

| Flag | What it does | When to use it |
|---|---|---|
| *(none)* | Runs the whole demo in a pty, caches the frames to `frames.pkl.gz`, and writes `demo.txt`, `demo.cast` and `demo.gif`. | When the *content* changed and you need fresh, honest output. |
| `--check` | Records and prints, but **writes no GIF**. The frames are still cached. | When you changed a step in `steps.py` and only want to know whether it still works. Cheap, and it is the loop to use before you commit to a render. |
| `--reuse` | Loads `frames.pkl.gz` and re-renders the GIF from it **without re-running a single command**. | The fast iteration loop. When you changed the *renderer* — colours, font size, frame rate, layout — and want to see the result in seconds instead of minutes. |

Editing the demo means editing [`steps.py`](./steps.py). The steps are a list of typed objects:
`note` for narration, `cmd` for a command that really runs, `file` to show a file from the
repository, `focus` for a callout card, and `end` for the closing card. Editing the recording or
the rendering means editing [`record.py`](./record.py).

The recorder also accepts `--outdir`, if you want the artefacts somewhere other than this
directory.

---

## Requirements

Everything here is free and open source. No account, no payment method, no paid service.

**Python 3 with [Pillow](https://pillow.readthedocs.io/).** Pillow is the only Python
dependency, and the only thing that draws the GIF.

```bash
python3 -c "import PIL; print(PIL.__version__)"   # check it is importable
```

**And a monospace TrueType font that covers the box-drawing characters.** The recorder draws
`─ │ ┌ └ ┐ ┘` and the `➜` that Molecule uses in its output; a font without those glyphs
renders the whole recording as empty boxes. The script tests the font it picks and refuses one
that cannot draw them, then tells you what to install.

### Install, per platform

| Platform | Pillow | A monospace font with box-drawing coverage |
|---|---|---|
| **Fedora** | `sudo dnf install python3-pillow` | `sudo dnf install dejavu-sans-mono-fonts liberation-mono-fonts` |
| **Ubuntu** | `sudo apt install python3-pil` | `sudo apt install fonts-dejavu-core fonts-liberation2` |
| **Arch Linux** | `sudo pacman -S python-pillow` | `sudo pacman -S ttf-dejavu` |
| **Mageia** | `sudo dnf install python3-pillow` | `sudo dnf install fonts-ttf-dejavu` |
| **macOS** | `pipx install Pillow` — or `python3 -m pip install --user Pillow` if you already manage Python that way | Ships with the system: **Menlo** and **SF Mono** are monospaced and cover box-drawing. If the script cannot find one, `brew install --cask font-dejavu` installs DejaVu Sans Mono where fontconfig will see it. |

Notes, so nobody loses an afternoon to them:

- **Debian/Ubuntu call it `python3-pil`, not `python3-pillow`.** It is the same library; the
  package kept the old name.
- **Mageia names it `fonts-ttf-dejavu`**, not the Fedora `dejavu-sans-mono-fonts`. Same font,
  different package name.
- **On macOS, `pipx` is the tidier route** because it keeps Pillow in its own environment and off
  the system Python, which recent macOS releases mark as externally managed.
- **The script asks fontconfig first** (`fc-match`), then falls back to scanning
  `/usr/share/fonts`, so it does not care where your distribution puts the file. On macOS without
  fontconfig, the DejaVu cask is the reliable answer.
- You also need the tools the demo itself exercises — Molecule, `molecule-plugins`, Podman —
  exactly as any other machine running this site's examples would. See
  [`docs/install/index.md`](../../docs/install/index.md).

---

## The leak check

A published video is permanent, and a home directory or a login name in one frame is a disclosure
that cannot be taken back. `record.py` treats that as a build failure, not a warning.

**What it protects against.** The recording runs with a neutral `HOME`
(`/tmp/molecule-demo-home`) and a placeholder `USER`, and it executes out of a `git clone` at a
neutral path rather than from the working checkout. That is belt; the leak check is braces. On
every run, the script concatenates the text of every captured frame and searches it for the real
`$HOME` and the real `$USER`. If either appears:

```
LEAK CHECK FAILED - the recording contains:
  - '/home/someone'
Refusing to write demo.gif. Fix the environment or the step that leaks.
```

**The GIF is not written.** `demo.txt` and `demo.cast` are not written either. What is written is
`demo-leaks.txt` in the output directory, listing the strings that matched, so you can see what
leaked without opening a video.

**If it fires, in practice.** It almost always means one of two things. Either a tool found your
real home directory by some route other than `$HOME` — Podman's
`$HOME/.ansible_async` paths and the pre-flight script's `subuid` lines are the two places this
happens, and they are why those commands are wrapped the way they are — or a step you added
prints an absolute path. Fix the step rather than the check; the check exists precisely so that a
future edit cannot quietly reintroduce the problem. `demo-leaks.txt` names the offending string,
which is nearly always enough to find the line. Delete it once you are done.

**The second reason the recording is a clone.** Because the commands run from
`/tmp/molecule-demo-home/proj` rather than from your checkout, the video always shows the
**committed** state of the repository. Commit first, then record. A recording made from uncommitted
work would show a video that no reader could ever reproduce — the exact drift this project is
trying to avoid.

---

## Known limitations

Stated plainly, because a limitations section that hides something is worse than no limitations
section.

**Only the Fedora/x86_64 path has actually been recorded.** The recording in this repository was
made on Fedora 44, x86-64, with rootless Podman 5.8.7, cgroup v2, Molecule 26.9.0 and
`ansible-core` 2.21.4. The Ubuntu, Arch, macOS and Mageia install pages are documented from
package metadata and upstream sources and **have not been filmed**. The other four platforms'
instructions in the table above are from the same research; they are plausible and they are what
the install pages say, but nobody has watched the demo render on them.

**The video is 100 × 30 characters, so very long lines wrap.** The recorder asks the command for
a 100-column, 30-row terminal, and lines longer than that wrap onto the next row exactly as they
would in a real narrow terminal. Molecule prints some long absolute paths, and those are the lines
that wrap. This is faithful rather than broken, but it is the first thing people notice, so it is
worth knowing before you assume the frame is broken.

**The recorder records a sample of a ~2-minute run, not every frame.** Terminal output is bursty:
a real `molecule test` takes a couple of minutes, most of it spent waiting. The recorder keeps
only the frames where the screen actually changed — 321 captured, 248 kept in the GIF — compresses
idle time to a cap, and caps the frame rate at 8 fps. The result is a ~1 min 54 s video of a
roughly two-and-a-half-minute session, with the waiting taken out. You are watching a real run
with its dead air removed — not a sped-up playback, and not a re-enactment.

**Callout cards show what matched, and may show less than you expect.** Each card greps the real
captured output for a pattern and prints the first match or two, up to a cap. That is what makes
the demo unable to lie, but it also means a card can be empty if the wording upstream ever
changes. An empty card is a signal, not a cosmetic glitch: fix the pattern in
[`steps.py`](./steps.py), do not paper over it.

**The renderer is deliberately minimal.** Pillow only, one shared palette built from the colours
the frames actually use, no anti-aliasing tricks. The file is 2.1 MB rather than several times
that, at the cost of some colour fidelity in the greys.

---

## Next

- **Watch the annotated walkthrough** → [`docs/demo.md`](../../docs/demo.md), which quotes this
  recording's transcript beat by beat.
- **See the demo in context** → [`README.md`](../../README.md), the landing page.
- **Run the scenario the demo runs** → [`examples/systemd-unit/`](../systemd-unit/).
- **Read the evidence behind every claim** → [`examples/VERIFICATION.md`](../VERIFICATION.md).
