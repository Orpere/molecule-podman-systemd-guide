"""
The content of the demo: what gets recorded, in what order, and what the viewer
is meant to take away from each part.

This file contains no rendering logic. It is the script. Edit it to change the
demo; edit `record.py` to change how it is drawn.

Every `cmd` step is executed for real. Nothing here is simulated, and there are
no expected outputs written by hand: the callouts pull matching lines out of
whatever the tool actually printed, so if a claim in this file stops being true
the callout goes empty rather than lying.

The writing aims at someone who has never used Molecule, Podman or Ansible, so
each section says what is happening and why it matters, not just which key to
press. Section names must match CHAPTERS in record.py, which drives the header
bar.

A note on the environment below
-------------------------------
The recording deliberately runs the commands with a neutral ``HOME`` and a
placeholder ``USER``, while pointing Podman back at the real storage via
``XDG_DATA_HOME``. That does exactly one thing: it stops the operator's real
home directory and login name appearing in a video that will be published.
Podman's ``$HOME/.ansible_async`` paths and the pre-flight script's subuid lines
are the only two places they leak.

None of this is something a reader has to do. It is an artefact of recording,
and ``record.py`` enforces it with a leak check that refuses to write the GIF if
the real path or username reaches the frames.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# A neutral home for the recording. Created by record.py before the run.
DEMO_HOME = Path(tempfile.gettempdir()) / "molecule-demo-home"

# The demo runs from a git clone at a neutral path, not from the real checkout.
# Two reasons, both important:
#   1. Molecule prints its absolute scenario directory. os.getcwd() resolves
#      symlinks, so a symlink would not help - the real home path would still
#      reach the frames. A real clone at a neutral path is the only way to keep
#      the operator's home directory out of a published video.
#   2. The recording then always shows the *committed* state of the repository,
#      so the video can never drift from what a reader would actually download.
WORKTREE = DEMO_HOME / "proj"


def ensure_worktree() -> Path:
    """Clone (or refresh) the repository at a neutral path. Returns the path."""
    if WORKTREE.exists():
        return WORKTREE
    WORKTREE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        # file:// rather than --local: --local hardlinks the object store, which
        # fails across filesystems, and /tmp is usually a different one.
        ["git", "clone", "--quiet", f"file://{ROOT}", str(WORKTREE)],
        check=True,
    )
    return WORKTREE


def _real(name: str, default: str) -> str:
    return os.environ.get(name) or default


def _bin_dir() -> str:
    """Directory holding the `molecule` binary, for PATH inside the recording.

    Order: an explicit VENV_BIN override, then whatever `molecule` is on the
    caller's PATH, then the usual suspects. Deriving it from the caller's PATH
    is what makes this work on someone else's machine without editing anything.
    """
    override = os.environ.get("VENV_BIN")
    if override:
        return override
    found = shutil.which("molecule")
    if found:
        return str(Path(found).resolve().parent)
    for cand in (ROOT / ".venv" / "bin", ROOT / "venv" / "bin"):
        if (cand / "molecule").exists():
            return str(cand)
    return str(ROOT / ".venv" / "bin")


def safe_env() -> dict:
    """Environment for recorded commands: real tools, neutral identity."""
    real_home = _real("HOME", str(ROOT))
    return {
        "PATH": f"{_bin_dir()}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "USER": _real("USER", "youruser"),
        "HOME": str(DEMO_HOME),
        # Keep Podman on the real image store so the demo does not re-pull.
        "XDG_DATA_HOME": f"{real_home}/.local/share",
        "XDG_CONFIG_HOME": f"{real_home}/.config",
        "XDG_RUNTIME_DIR": _real("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"),
    }


# Semantic colours for the demo. Defined here rather than imported from
# record.py, which imports this module - the import would be circular.
KEY = (255, 209, 102)    # amber: the settings that do the work
OKC = (126, 214, 160)    # green: things that passed
BADC = (255, 123, 114)   # red: things that went wrong


def build_steps():
    return {
        "hostline": (
            "Recorded live: Fedora 44, rootless Podman 5.8.7, cgroup v2, "
            "Molecule 26.9.0, ansible-core 2.21.4."
        ),
        "moneyline": "Every tool here is free. Nothing in this demo costs money.",
        "steps": [
            # ================================================== title
            {
                "t": "card",
                "chapter": "Overview",
                "kicker": "A two-minute tour",
                "title": "Test your Ansible for real",
                "sub": (
                    "Molecule builds a throwaway container, runs your Ansible "
                    "inside it, checks the result, and deletes it. Nothing here "
                    "is simulated - every command you are about to see was run "
                    "on a real machine, and the callouts are lifted from what "
                    "the tools actually printed."
                ),
                "foot": (
                    "New to Molecule, Podman or Ansible? That is the right "
                    "starting point. Each section explains what it is doing."
                ),
                "wait": 5.0,
            },
            # ================================================== contents
            {
                "t": "card",
                "chapter": "Overview",
                "kicker": "What this covers",
                "title": "Seven short sections",
                "items": [
                    "Check the host is ready before installing anything",
                    "Confirm the toolchain, and the one install mistake that breaks it",
                    "The four keys that make systemd PID 1 in a container",
                    "Run the test, and prove the assertions really ran",
                    "The same thing in plain Podman, with no Molecule at all",
                    "Why the most-copied advice on the internet makes it worse",
                ],
                "foot": "The last two sections are the ones worth remembering.",
                "wait": 5.0,
            },
            # ================================================== 1. pitch
            {
                "t": "note",
                "chapter": "Overview",
                "text": (
                    "Why bother with a container at all? Because the part of "
                    "your role most likely to be broken is the part that talks to "
                    "the init system. Molecule gives you a real one - a real "
                    "systemd, real unit files, real service lifecycle - for the "
                    "price of a container that throws itself away afterwards. So "
                    "you can test that starting a service actually works, not just "
                    "that a task reported changed."
                ),
                "wait": 4.0,
            },
            # ================================================== 2. pre-flight
            {
                "t": "note",
                "chapter": "Is this host ready?",
                "text": (
                    "Start by finding out whether this machine can do it at all. "
                    "The script only reads: it installs nothing, elevates nothing, "
                    "and touches nothing outside Podman's own storage. It is "
                    "worth running before you install anything, because two of "
                    "its checks catch problems that are very hard to diagnose "
                    "later."
                ),
                "wait": 3.6,
            },
            {
                "t": "cmd",
                # The sed is only there so the video shows a placeholder name
                # instead of the operator's login. The check itself is real.
                "cmd": 'bash docs/scripts/molecule-preflight.sh 2>&1 | sed "s/\\b$USER\\b/youruser/g"',
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            {
                "t": "focus",
                "label": "The two checks that cause real trouble",
                "patterns": [r"PASS\s+cgroup v2", r"PASS\s+podman runs rootless", r"RESULT: READY"],
                "max": 3,
                "colour": OKC,
                "tail": (
                    "Cgroup v2 is the one to internalise. Podman 6 cannot run "
                    "systemd inside a container on a cgroup v1 host at all, and "
                    "the failure looks like systemd simply hanging. Rootless is "
                    "the right default: no root daemon, no shared socket, nothing "
                    "listening for other users."
                ),
                "wait": 4.4,
            },
            # ================================================== 3. toolchain
            {
                "t": "note",
                "chapter": "The toolchain",
                "text": (
                    "Two commands, and the first one teaches the most common "
                    "installation mistake there is."
                ),
                "wait": 2.6,
            },
            {
                "t": "cmd",
                "cmd": "molecule --version; echo; molecule drivers | grep -x podman",
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            {
                "t": "focus",
                "label": "Two things worth noticing",
                "patterns": [r"^molecule 2", r"^podman$"],
                "max": 2,
                "colour": OKC,
                "tail": (
                    "Notice ansible-core in that first line. Molecule shells out "
                    "to ansible-config the moment it starts, and it does not "
                    "declare ansible-core as a dependency - so installing "
                    "Molecule on its own gives you a binary that crashes with "
                    "'ansible-config not found'. Install them together. And "
                    "'podman' in that second list is not in Molecule: it comes "
                    "from the separate molecule-plugins package."
                ),
                "wait": 4.8,
            },
            # ================================================== 4. the crux
            {
                "t": "note",
                "chapter": "The four keys",
                "text": (
                    "This is the whole configuration, and it is short on purpose. "
                    "Four keys do all the work. The three in amber are what make "
                    "systemd run as PID 1 instead of a shell."
                ),
                "wait": 3.2,
            },
            {
                "t": "file",
                "path": str(WORKTREE / "examples/systemd-unit/molecule/default/molecule.yml"),
                # Shown as a repo-relative path, not the neutral worktree path
                # the demo happens to run from.
                "label": "examples/systemd-unit/molecule/default/molecule.yml",
                "clear": True,
                "only": [
                    "driver:", "name: podman", "platforms:", "- name: instance",
                    "image:", "command:", "override_command:", "systemd:",
                    "privileged:", "groups:", "- molecule",
                ],
                "highlight": [
                    ("command: /sbin/init", KEY, True),
                    ("override_command:", KEY, True),
                    ("systemd: always", KEY, True),
                    ("groups:", OKC, True),
                    ("- molecule", OKC, True),
                ],
                "wait": 4.2,
            },
            {
                "t": "note",
                "chapter": "The four keys",
                "text": (
                    "The amber three: point the container at systemd as its entry "
                    "point, tell Molecule not to override that with its own sleep "
                    "loop, and force systemd mode on. That is all it takes - no "
                    "--privileged, no policy file edits."
                ),
                "wait": 4.0,
            },
            {
                "t": "note",
                "chapter": "The four keys",
                "text": (
                    "The green one is the line most tutorials forget, and it is "
                    "the single most useful thing in this video. Molecule builds "
                    "its Ansible groups from this 'groups' key, and the default is "
                    "'ungrouped' - there is no built-in 'molecule' group. Leave it "
                    "out and every play in your project silently skips, because "
                    "'hosts: molecule' now matches nothing, and molecule test "
                    "still exits 0. You get a green run that tested nothing at all."
                ),
                "wait": 5.2,
            },
            # ================================================== 5. run it
            {
                "t": "note",
                "chapter": "Run the test",
                "text": (
                    "Now run it. Molecule creates a container, applies the "
                    "configuration, checks the result, and destroys the container "
                    "again. It takes about half a minute, almost all of it "
                    "container start-up."
                ),
                "wait": 3.2,
            },
            {
                "t": "cmd",
                "cmd": "cd examples/systemd-unit && molecule test",
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            {
                "t": "focus",
                "label": "This is the point of the whole exercise",
                "patterns": [r"systemd is PID 1", r"molecule-demo\.service is active"],
                "max": 2,
                "colour": OKC,
                "tail": (
                    "Read those two lines carefully. Not 'the playbook ran'. Not "
                    "'changed=0'. The init system in that container really is PID "
                    "1, and the service your role installed is genuinely active. "
                    "That is the thing that is hard to be confident about without "
                    "this."
                ),
                "wait": 5.0,
            },
            {
                "t": "focus",
                "label": "And did the test really run?",
                "patterns": [r"instance\s+: ok="],
                "max": 1,
                "colour": OKC,
                "tail": (
                    "Check this before you trust any green Molecule run. If your "
                    "plays skip every host, molecule test still exits 0 and the "
                    "recap still says failed=0 - while your assertions never ran. "
                    "ok=7 with no 'no hosts matched' is the real signal, and it is "
                    "the reason the 'groups' key exists."
                ),
                "wait": 5.4,
            },
            # ================================================== 6. plain podman
            {
                "t": "note",
                "chapter": "Same thing in plain Podman",
                "text": (
                    "Everything so far has been Molecule. Here is the identical "
                    "result in three plain Podman commands, so you can see what "
                    "the automation is actually doing underneath."
                ),
                "wait": 3.2,
            },
            {
                "t": "cmd",
                "cmd": (
                    "podman run -d --name demo --systemd=always "
                    "registry.access.redhat.com/ubi9/ubi-init >/dev/null && "
                    "sleep 4 && "
                    "podman exec demo systemctl is-system-running; "
                    "podman rm -f demo >/dev/null"
                ),
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            {
                "t": "focus",
                "label": "One flag does the work",
                "patterns": [r"^running$", r"^degraded$"],
                "max": 1,
                "colour": OKC,
                "tail": (
                    "--systemd=always. That is the whole trick. No --privileged, "
                    "no /etc/containers/policy.json edits, no setsebool. You will "
                    "see all three of those recommended online; hold that thought "
                    "for the next section."
                ),
                "wait": 4.6,
            },
            # ================================================== 7. the myth
            {
                "t": "note",
                "chapter": "The --privileged myth",
                "text": (
                    "Here is the folklore, tested. The single most-copied piece of "
                    "advice about systemd in containers is 'just add "
                    "--privileged'. Watch what it does."
                ),
                "wait": 3.2,
            },
            {
                "t": "cmd",
                "cmd": (
                    "podman run -d --name demo --privileged --systemd=always "
                    "registry.access.redhat.com/ubi9/ubi-init >/dev/null && "
                    "sleep 5 && "
                    "podman exec demo systemctl is-system-running; "
                    "podman rm -f demo >/dev/null"
                ),
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            {
                "t": "focus",
                "label": "Running became degraded",
                "patterns": [r"^degraded$", r"^running$"],
                "max": 1,
                "colour": BADC,
                "tail": (
                    "Same image, same flag, plus --privileged - and systemd went "
                    "from running to degraded. --privileged unmounts /sys, so three "
                    "of systemd's own units can no longer mount. You weakened the "
                    "sandbox and broke the init system. The narrow flag from the "
                    "previous section was the whole fix."
                ),
                "wait": 5.2,
            },
            # ================================================== 8. cleanup
            {
                "t": "note",
                "chapter": "The --privileged myth",
                "text": (
                    "Finally, clean up. Molecule destroys the scenario itself, so "
                    "the point of all this is that you are left with no "
                    "containers and no state."
                ),
                "wait": 2.8,
            },
            {
                "t": "cmd",
                "cmd": "cd examples/systemd-unit && molecule destroy && podman ps -a",
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            # ================================================== closing
            {
                "t": "card",
                "kicker": "That is the whole loop",
                "title": "Make a container, prove your role, throw it away",
                "sub": (
                    "You have just seen a role that installs a systemd service "
                    "and get told, by the init system itself, that the service is "
                    "active. That is a much stronger claim than a task reporting "
                    "'changed'."
                ),
                "items": [
                    "docs/install/ - pick your platform, every step copy-pasteable",
                    "docs/systemd-in-containers.md - why those four keys, in detail",
                    "docs/authoring/ - write your own scenarios, including a CI workflow",
                    "docs/troubleshooting.md - 21 symptoms, with the real error text",
                ],
                "foot": (
                    "All of it free and open source. Nothing in this demo or in "
                    "the guide costs money."
                ),
                "wait": 6.0,
            },
        ],
    }
