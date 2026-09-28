"""
The content of the demo: what gets recorded, in what order, and what the viewer
is meant to take away from each part.

This file contains no rendering logic. It is the script. Edit it to change the
demo; edit `record.py` to change how it is drawn.

Every `cmd` step is executed for real. Nothing here is simulated, and there are
no expected outputs written by hand: the callouts pull matching lines out of
whatever the tool actually printed, so if a claim in this file stops being true
the callout goes empty rather than lying.

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
            # ---------------------------------------------------------- pitch
            {
                "t": "note",
                "text": (
                    "Molecule builds a throwaway container, runs your Ansible "
                    "content inside it, and throws it away. The part that makes "
                    "it useful is that the container runs a real init system, so "
                    "you can test that your role actually starts a service."
                ),
                "rule": True,
                "wait": 2.2,
            },
            # ------------------------------------------------------ pre-flight
            {
                "t": "note",
                "text": "Step 0 - is this machine ready? There is a script, and it only reads.",
                "arrow": True,
                "wait": 1.4,
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
                "label": "Everything the host must already be doing right",
                "patterns": [r"PASS\s+cgroup v2", r"PASS\s+podman runs rootless", r"RESULT: READY"],
                "max": 3,
                "colour": OKC,
                "tail": (
                    "cgroup v2 is the one that bites people. Podman 6 cannot run "
                    "systemd in a container on a cgroup v1 host at all."
                ),
                "wait": 3.0,
            },
            # ------------------------------------------------------- toolchain
            {
                "t": "note",
                "text": "Step 1 - the toolchain.",
                "arrow": True,
                "wait": 1.2,
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
                    "The Podman driver is not in Molecule itself. It comes from the "
                    "separate molecule-plugins package, so 'podman' has to appear in "
                    "that second list or nothing will work."
                ),
                "wait": 3.0,
            },
            # ------------------------------------------------------------ crux
            {
                "t": "note",
                "text": (
                    "Step 2 - the crux. Four keys in molecule.yml turn an ordinary "
                    "container into one that runs systemd as PID 1."
                ),
                "arrow": True,
                "wait": 1.6,
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
                    "ansible_connection:",
                ],
                "highlight": [
                    ("command: /sbin/init", KEY, True),
                    ("override_command:", KEY, True),
                    ("systemd: always", KEY, True),
                    ("groups:", OKC, True),
                    ("- molecule", OKC, True),
                ],
                "wait": 3.4,
            },
            {
                "t": "note",
                "text": (
                    "The three amber lines make systemd run. The green one is the "
                    "line almost every tutorial forgets."
                ),
                "wait": 2.0,
            },
            # ------------------------------------------------------------- run
            {
                "t": "note",
                "text": "Step 3 - run the whole scenario. Create, converge, verify, destroy.",
                "arrow": True,
                "wait": 1.4,
            },
            {
                "t": "cmd",
                "cmd": "cd examples/systemd-unit && molecule test",
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            # ---------------------------------------------------------- payoff
            {
                "t": "focus",
                "label": "This is the whole point of the exercise",
                "patterns": [r"systemd is PID 1", r"molecule-demo\.service is active"],
                "max": 2,
                "colour": OKC,
                "tail": (
                    "Not 'the playbook ran'. Not 'changed=0'. The init system is "
                    "PID 1, and the service your role installed is active."
                ),
                "wait": 3.4,
            },
            {
                "t": "focus",
                "label": "But did the test really run?",
                "patterns": [r"instance\s+: ok="],
                "max": 1,
                "colour": OKC,
                "tail": (
                    "Check this before you trust any green Molecule run. If the "
                    "playbook skipped every host, molecule test still exits 0 and "
                    "the recap shows failed=0 - while your assertions never ran at "
                    "all. ok=7 with no 'no hosts matched' is the real signal."
                ),
                "wait": 3.6,
            },
            # ------------------------------------------------------ by hand
            {
                "t": "note",
                "text": (
                    "Step 4 - here is the same thing in plain Podman. This is what "
                    "Molecule is automating for you."
                ),
                "arrow": True,
                "wait": 1.6,
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
                    "--systemd=always. No --privileged, no policy.json edits, no "
                    "setsebool. That advice is everywhere on the internet and most "
                    "of it is folklore."
                ),
                "wait": 3.0,
            },
            # --------------------------------------------------------- the myth
            {
                "t": "note",
                "text": (
                    "And the folklore is actively harmful. The most-copied advice is "
                    "to add --privileged. Watch what it does:"
                ),
                "wait": 1.8,
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
                    "--privileged unmounts /sys, so three of systemd's own units can "
                    "no longer mount. You weakened the sandbox and broke the init "
                    "system. The real fix was the narrower --systemd=always."
                ),
                "wait": 3.4,
            },
            # --------------------------------------------------------- cleanup
            {
                "t": "note",
                "text": "Step 5 - clean up. Molecule destroys the scenario; nothing is left behind.",
                "arrow": True,
                "wait": 1.4,
            },
            {
                "t": "cmd",
                "cmd": "cd examples/systemd-unit && molecule destroy && podman ps -a",
                "cwd": str(WORKTREE),
                "env": safe_env(),
            },
            {
                "t": "end",
                "text": "That is the whole loop: make a container, prove your role works, throw it away.",
                "sub": (
                    "Full install guides for Fedora, Ubuntu, Arch, macOS and Mageia, "
                    "plus how to write your own scenarios, are in the repository."
                ),
            },
        ],
    }
