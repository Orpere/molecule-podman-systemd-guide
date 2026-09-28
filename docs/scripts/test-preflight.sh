#!/usr/bin/env bash
# Acceptance tests for molecule-preflight.sh.
#
# These exist because the script once had a defect that three content reviews
# missed: it ran under `set -u` but dereferenced ${USER} unguarded, so in cron,
# in a systemd unit, under `env -i`, or in some CI runners it died mid-report
# with no RESULT: line at all. A reader told to "fix every FAIL line" would be
# fixing a problem that was never reported. See PLAN.md Trace T3 and the
# regression rule at the end of Trace T5.
#
# Free and offline: only bash, coreutils, awk, grep. Nothing to install.
# Run:  bash docs/scripts/test-preflight.sh

set -uo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SCRIPT="$HERE/molecule-preflight.sh"
pass=0; fail=0
ok()   { printf '  PASS  %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

echo "Acceptance tests for molecule-preflight.sh"

# 1. Must be syntactically valid.
if bash -n "$SCRIPT" 2>/dev/null; then ok "bash -n: script parses"; else bad "bash -n: script does not parse"; fi

# 2. Must reach the RESULT: verdict line with USER unset (the T3 regression).
out=$(env -u USER bash "$SCRIPT" 2>&1); rc=$?
if printf '%s' "$out" | grep -q '^RESULT:'; then
  ok "env -u USER: still reaches the RESULT: verdict line"
else
  bad "env -u USER: died before RESULT: (this is Trace T3 regressing)"
  printf '%s\n' "$out" | tail -3 | sed 's/^/        /'
fi
[ "$rc" -eq 0 ] || [ "$rc" -eq 1 ] && ok "env -u USER: exit code is 0 or 1 (got $rc)" \
  || bad "env -u USER: unexpected exit code $rc (expected 0 or 1)"

# 3. Same with a fully empty environment.
out=$(env -i PATH="$PATH" HOME="$HOME" bash "$SCRIPT" 2>&1)
printf '%s' "$out" | grep -q '^RESULT:' \
  && ok "env -i: still reaches the RESULT: verdict line" \
  || bad "env -i: died before RESULT:"

# 4. --quiet must still emit the verdict and preserve the exit-code contract.
#    NOTE: do not test this with a pipeline. `set -o pipefail` is on above, and the
#    pre-flight script deliberately exits 1 when a check fails, which would mask a
#    successful grep. Capture the output first, then test it.
qout=$(bash "$SCRIPT" --quiet 2>/dev/null); qrc=$?
qlines=$(printf '%s\n' "$qout" | wc -l)
if [ "$qlines" -eq 1 ] && [ "${qout#RESULT:}" != "$qout" ]; then
  ok "--quiet: emits exactly one line, and it is the verdict"
else
  bad "--quiet: expected exactly 1 line starting RESULT:, got $qlines"
fi
if [ "$qrc" -eq 0 ] || [ "$qrc" -eq 1 ]; then
  ok "--quiet: exit code is 0 or 1, so CI can still gate on it (got $qrc)"
else
  bad "--quiet: unexpected exit code $qrc"
fi

# 5. Read-only in the sense the docs actually claim.
#    The claim is: the script writes nothing EXCEPT the storage Podman itself
#    initialises on first use (its XDG roots). So assert exactly that - not a
#    stricter fiction the documentation would then be wrong about.
tmpd=$(mktemp -d)
HOME="$tmpd" bash "$SCRIPT" >/dev/null 2>&1
# Anything created must live under one of Podman's XDG roots.
stray=$(find "$tmpd" -mindepth 1 -maxdepth 1 2>/dev/null \
        | grep -vE "/\.(local|config|cache|run|var/tmp)$" | wc -l)
podman_dirs=$(find "$tmpd" -mindepth 1 -maxdepth 1 2>/dev/null \
        | grep -cE "/\.(local|config|cache)$" || true)
rm -rf "$tmpd"
if [ "$stray" -eq 0 ]; then
  ok "read-only: created nothing outside Podman's XDG storage ($podman_dirs storage dir(s), 0 stray)"
else
  bad "read-only: created $stray entries outside Podman's XDG storage"
fi

printf '\n%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
