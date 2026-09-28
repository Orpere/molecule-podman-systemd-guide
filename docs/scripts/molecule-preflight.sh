#!/usr/bin/env bash
# molecule-preflight.sh - prove this machine is ready for Molecule + Podman + systemd
#
# Canonical location: docs/scripts/molecule-preflight.sh
# Authoring rule: every page that needs a readiness check links to this file.
#                Never re-type this script inside a page. Quote it verbatim.
#
# Usage:  bash molecule-preflight.sh          # human output
#         bash molecule-preflight.sh --quiet  # only the summary line
#
# Exit codes:  0 = every required check passed
#              1 = at least one required check failed
#              2 = this script cannot run here (e.g. unsupported OS)
#
# Safety: read-only. It never installs a package and never asks for sudo. It
# never writes outside Podman's own storage directory - which `podman` itself
# may initialise on first use, when this script calls `podman info`. Nothing
# outside that directory is ever created, changed or deleted.

set -u

# USER is not exported by cron, by systemd units, under `env -i`, or by some CI
# runners. Dereferencing it unguarded would kill the report half way through
# with no RESULT: line at all, so resolve the login name exactly once here and
# use USER_NAME from then on.
USER_NAME="${USER:-}"
if [ -z "$USER_NAME" ]; then
  USER_NAME="$(id -un 2>/dev/null || true)"
fi
if [ -z "$USER_NAME" ]; then
  USER_NAME="$(id -u 2>/dev/null || true)"
fi
if [ -z "$USER_NAME" ]; then
  USER_NAME="unknown"
fi
USER="$USER_NAME"

QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

HARD_FAILURES=0
WARNINGS=0

# ---------------------------------------------------------------- output ----
if [ "$QUIET" -eq 1 ]; then
  say() { :; }
else
  say() { printf '%s\n' "$*"; }
fi

pass() { say "  PASS  $*"; }
fail() { say "  FAIL  $*"; HARD_FAILURES=$((HARD_FAILURES + 1)); }
warn() { say "  WARN  $*"; WARNINGS=$((WARNINGS + 1)); }
note() { say "        $*"; }
head_() { say ""; say "== $*"; }

# ------------------------------------------------------------- platform -----
UNAME_S=$(uname -s)
case "$UNAME_S" in
  Linux)  PLATFORM=linux ;;
  Darwin) PLATFORM=darwin ;;
  *)      say "molecule-preflight: unsupported operating system: $UNAME_S"; exit 2 ;;
esac

say "Molecule + Podman + systemd pre-flight check"
say "host: $UNAME_S $(uname -m)"

# ---------------------------------------------------------- 1. cgroup v2 ----
head_ "1. Control groups (cgroups)"
# systemd running as PID 1 needs the modern "cgroup v2" hierarchy.
# It is the same kernel feature that gives you "systemd slices".
if [ "$PLATFORM" = linux ]; then
  CGROUP_FS=$(stat -fc %T /sys/fs/cgroup 2>/dev/null || echo unknown)
  if [ "$CGROUP_FS" = "cgroup2fs" ]; then
    pass "cgroup v2 is in use ($CGROUP_FS)"
  elif [ "$CGROUP_FS" = "tmpfs" ]; then
    fail "cgroup v1 is in use ($CGROUP_FS). systemd-in-container needs cgroup v2."
    note "Podman 6.0 removed cgroup v1 support entirely. Reboot into a newer kernel,"
    note "or install a distribution/kernel that ships cgroup v2 (all five target OSes do)."
  else
    fail "cannot read the cgroup filesystem type (got '$CGROUP_FS')"
    note "Expected 'cgroup2fs'. Check that /sys/fs/cgroup is mounted."
  fi
else
  # macOS: the check has to happen inside the podman machine virtual machine.
  if command -v podman >/dev/null 2>&1 && podman machine list >/dev/null 2>&1; then
    pass "macOS detected - the real check runs inside the podman machine (see note)"
    note "Run: podman machine ssh 'stat -fc %T /sys/fs/cgroup'   -> expect: cgroup2fs"
  else
    warn "macOS detected but no podman machine yet"
    note "Run: podman machine init && podman machine start"
  fi
fi

# ------------------------------------------------------------- 2. podman ----
head_ "2. Podman (the container engine)"
if command -v podman >/dev/null 2>&1; then
  PODMAN_VERSION=$(podman --version 2>/dev/null || echo unknown)
  pass "podman found: $PODMAN_VERSION"
  PODMAN_MAJOR=$(printf '%s' "$PODMAN_VERSION" | sed -n 's/.*version \([0-9][0-9]*\)\..*/\1/p')
  case "$PODMAN_MAJOR" in
    ''|*[!0-9]*) note "could not parse the podman major version" ;;
    *) if [ "$PODMAN_MAJOR" -lt 5 ]; then
         warn "podman $PODMAN_VERSION is older than 5. The Molecule podman driver expects a modern podman."
         note "Ubuntu 24.04 ships podman 4.9.3. Consider Ubuntu 26.04."
       else
         note "major version $PODMAN_MAJOR is supported"
       fi ;;
  esac
  if ROOTLESS=$(podman info --format '{{.Host.Security.Rootless}}' 2>/dev/null); then
    if [ "$ROOTLESS" = "true" ]; then
      pass "podman runs rootless (recommended)"
    else
      note "podman is running as root (rootful). Rootless is recommended but not required."
    fi
  else
    fail "podman is installed but 'podman info' failed - the engine is not working"
    note "Try: podman run --rm alpine echo ok"
  fi
else
  fail "podman is not on your PATH"
  note "Fedora:  sudo dnf install podman"
  note "Ubuntu:  sudo apt install podman"
  note "Arch:    sudo pacman -S podman"
  note "Mageia:  sudo dnf install podman"
  note "macOS:   download the .pkg from https://podman.io (Apple Silicon only)"
fi

# ------------------------------------------- 3. rootless user-id mapping ----
head_ "3. Rootless user-id mapping (newuidmap / subuid / subgid)"
if [ "$PLATFORM" = darwin ]; then
  pass "not applicable on macOS - the virtual machine handles this for you"
else
  if command -v newuidmap >/dev/null 2>&1; then
    pass "newuidmap found: $(command -v newuidmap)"
  else
    fail "newuidmap is missing - rootless podman cannot map user ids"
    note "Fedora: installed by shadow-utils-subid (a podman dependency)"
    note "Ubuntu: sudo apt install uidmap"
    note "Arch:   provided by the shadow package"
    note "Mageia: NOT PACKAGED - check with: rpm -ql shadow-utils"
  fi
  # Match field 1 exactly. A prefix match is wrong: a user called `orpadmin`
  # would otherwise be reported as mapped by an entry for `orpad`.
  if [ -r /etc/subuid ] && awk -F: -v u="$USER_NAME" '$1==u {found=1} END {exit !found}' /etc/subuid; then
    pass "/etc/subuid has an entry for $USER_NAME"
  else
    fail "/etc/subuid has no entry for $USER_NAME"
    note "sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 \"$USER_NAME\""
    note "then log out and back in, then run: podman system migrate"
  fi
  if [ -r /etc/subgid ] && awk -F: -v u="$USER_NAME" '$1==u {found=1} END {exit !found}' /etc/subgid; then
    pass "/etc/subgid has an entry for $USER_NAME"
  else
    fail "/etc/subgid has no entry for $USER_NAME"
    note "sudo usermod --add-subgids 100000-165535 \"$USER_NAME\""
    note "then log out and back in, then run: podman system migrate"
  fi
fi

# ------------------------------------------------------------- 4. SELinux ----
head_ "4. SELinux (Linux only)"
if [ "$PLATFORM" = darwin ]; then
  pass "not applicable on macOS"
elif command -v getenforce >/dev/null 2>&1; then
  SELINUX_STATE=$(getenforce 2>/dev/null || echo unknown)
  case "$SELINUX_STATE" in
    Enforcing)  pass "SELinux is $SELINUX_STATE - this is the well-tested case" ;;
    Permissive) warn "SELinux is Permissive - no protection. systemd-in-container still works." ;;
    Disabled)   warn "SELinux is Disabled - fine for testing, weaker isolation" ;;
    *)          warn "could not read the SELinux state (got '$SELINUX_STATE')" ;;
  esac
  note "You do NOT need: setsebool container_manage_cgroup, /etc/containers/policy.json edits,"
  note "or --security-opt label=disable. Podman labels systemd containers container_init_t."
else
  pass "SELinux tools are not installed (this distribution has no SELinux)"
fi

# ------------------------------------------------------------ 5. Python -----
head_ "5. Python (Molecule needs Python 3.10 or newer)"
if command -v python3 >/dev/null 2>&1; then
  PY_VERSION=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo 0.0)
  PY_MAJOR=${PY_VERSION%%.*}
  PY_MINOR=${PY_VERSION##*.}
  pass "python3 found: $PY_VERSION"
  if [ "$PY_MAJOR" -eq 3 ] 2>/dev/null && [ "$PY_MINOR" -ge 10 ] 2>/dev/null; then
    pass "python3 is new enough (need >= 3.10)"
  else
    fail "python3 $PY_VERSION is too old - Molecule needs >= 3.10"
    note "Arch and macOS users: install a newer python3 from your package manager or Homebrew."
  fi
else
  fail "python3 is not on your PATH"
  note "Fedora:  sudo dnf install python3"
  note "Ubuntu:  sudo apt install python3"
  note "Arch:    sudo pacman -S python"
fi

# ---------------------------------------------------------- 6. Molecule -----
head_ "6. Molecule and the Podman driver"
if command -v molecule >/dev/null 2>&1; then
  # Real output: "molecule 26.9.0 using ansible-core 2.20.3 python version 3.14.7 ..."
  # The version is always field 2 of line 1. Never regex the whole line: it also
  # contains the ansible-core version, which would be misread as the molecule version.
  MOLECULE_VERSION=$(molecule --version 2>/dev/null | awk 'NR==1 { print "molecule " $2 }')
  if [ -z "$MOLECULE_VERSION" ] || [ "$MOLECULE_VERSION" = "molecule " ]; then
    pass "molecule found (version string not recognised)"
  else
    pass "$MOLECULE_VERSION"
  fi
  MOLECULE_NUM=$(printf '%s' "$MOLECULE_VERSION" | awk '{ print $2 }')
  case "$MOLECULE_NUM" in
    [0-9]*) ;;
    *)     MOLECULE_NUM="" ;;
  esac
  if [ -n "$MOLECULE_NUM" ]; then
    MOLECULE_MAJOR=${MOLECULE_NUM%%.*}
    if [ "$MOLECULE_MAJOR" -lt 25 ] 2>/dev/null; then
      warn "molecule $MOLECULE_NUM is older than the current 26.9.x line"
      note "pipx upgrade molecule    /    pipx install molecule ansible-core molecule-plugins"
    else
      note "molecule $MOLECULE_NUM is on a supported release line"
    fi
  fi
  if molecule drivers 2>/dev/null | grep -q '^podman'; then
    pass "the 'podman' driver is available (from molecule-plugins)"
  else
    fail "the 'podman' driver is missing"
    note "pipx inject molecule molecule-plugins"
    note "or: python3 -m pip install --user \"molecule-plugins[podman]\""
  fi
else
  fail "molecule is not on your PATH"
  note "pipx install molecule ansible-core molecule-plugins"
  note "Mageia (no pipx package): python3 -m pip install --user pipx && pipx install molecule ansible-core molecule-plugins"
fi

# ------------------------------------------------ 7. containers.podman ------
head_ "7. The containers.podman Ansible collection"
if command -v ansible-galaxy >/dev/null 2>&1; then
  if ansible-galaxy collection list containers.podman 2>/dev/null | grep -q 'containers.podman'; then
    COLLECTION_VERSION=$(ansible-galaxy collection list containers.podman 2>/dev/null | sed -n 's/.*containers\.podman *\([0-9][0-9.]*\).*/\1/p')
    pass "containers.podman collection is installed${COLLECTION_VERSION:+ (version $COLLECTION_VERSION)}"
  else
    warn "containers.podman is not installed yet"
    note "You do not need it installed up front. 'molecule test' installs it from"
    note "requirements.yml during the 'dependency' step. Run 'ansible-galaxy collection"
    note "install containers.podman' if you want it now."
  fi
else
  warn "ansible-galaxy is not on your PATH, so the collection cannot be checked"
  note "This is only informational - Molecule installs collections on demand."
fi

# ------------------------------------------------------------ 8. summary ----
# The RESULT line is the exit-code contract, so it is written with printf
# directly and is never suppressed by --quiet. --quiet silences the report
# body, not the verdict.
if [ "$HARD_FAILURES" -gt 0 ]; then
  RESULT="RESULT: NOT READY - $HARD_FAILURES required check(s) failed, $WARNINGS warning(s)"
elif [ "$WARNINGS" -gt 0 ]; then
  RESULT="RESULT: READY WITH WARNINGS - $WARNINGS warning(s), no hard failures"
else
  RESULT="RESULT: READY - every check passed"
fi

say ""
say "----------------------------------------"
printf '%s\n' "$RESULT"
if [ "$HARD_FAILURES" -gt 0 ]; then
  say "Fix every FAIL line above, then run this script again."
elif [ "$WARNINGS" -gt 0 ]; then
  say "You can continue. Read each WARN line before you start."
fi

if [ "$HARD_FAILURES" -gt 0 ]; then
  exit 1
fi
exit 0
