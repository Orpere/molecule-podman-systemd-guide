# `examples/` — runnable, verified examples

Three real, on-disk Molecule projects (`systemd-unit/`, `quickstart/`, and the two-scenario
`multi-scenario/`), plus `demo/` — the recording pipeline that produced the video at the top of
[`README.md`](../README.md). All were executed end to end on the target host
(Fedora 44 · rootless podman 5.8.7 · SELinux Enforcing · cgroup v2 · x86_64) against
molecule 26.9.0 · molecule-plugins 26.9.28 · ansible-core 2.21.4. Every `molecule test`
run exits **0** with the assertions genuinely executed (not a vacuous pass — see
`VERIFICATION.md`, DBG-1).

> **The transcripts in this file and in `VERIFICATION.md` are real captured output from those
> runs, trimmed. Nothing is reconstructed.** Read `VERIFICATION.md` before quoting any of the
> documentation elsewhere: four of these canonical files do not work as written.

## What is in here

| Path | What it is | Start here |
|---|---|---|
| [`demo/`](./demo/) | The demo recording pipeline: `demo.gif` (866 × 534 px, 248 frames, ~1 min 54 s, 2.1 MB), `demo.cast` (asciicast v2), `demo.txt` (the exact 26 KB transcript), and the two scripts that produce them. | [`demo/README.md`](./demo/README.md), and the [annotated walkthrough](../docs/demo.md) |
| [`systemd-unit/`](./systemd-unit/) | Proves `systemd` is PID 1 in a rootless container and a test-installed unit is active. | §2 below |
| [`quickstart/`](./quickstart/) | The minimal copy / write / assert scenario. | §3 below |
| [`multi-scenario/`](./multi-scenario/) | One project, two scenarios, and the `group_vars` trap it avoids. | §4 below, and [`multi-scenario/README.md`](./multi-scenario/README.md) |
| [`VERIFICATION.md`](./VERIFICATION.md) | Every claim tested, every defect found in these docs, and the fix for each. | Read **DBG-1** first — it is the silent false pass. Then the [verdict table](./VERIFICATION.md#3-claim-by-claim-verdict-table). |

The GIF plays inline on GitHub with plain Markdown — an ordinary Markdown image, nothing more — so
there is no build step, no JavaScript and no external viewer. `demo.txt` is the evidence: any line
quoted anywhere in this repository can be grepped out of it.

---

## 1. Layout (and one non-obvious constraint)

Molecule hard-requires the glob `molecule/*/molecule.yml`. A flat
`examples/systemd-unit/molecule.yml` fails immediately:

```console
$ molecule list
CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.
```

So each example is a Molecule *project root* containing a `molecule/default/` scenario —
which is exactly the canonical path in `REFERENCE-CONFIG.md` §0.

```text
examples/
├── README.md
├── VERIFICATION.md          <- findings: every claim tested, every doc bug + fix
├── demo/                    <- the demo recording pipeline
│   ├── README.md            <- what the three artefacts are, how to re-record, limitations
│   ├── demo.gif             <- 866x534, 248 frames, ~1 min 54 s, 2.1 MB
│   ├── demo.cast            <- asciicast v2, 52 KB; asciinema play demo.cast
│   ├── demo.txt             <- the exact terminal output, 26 KB; greppable, quotable
│   ├── record.py            <- the recorder and renderer (Pillow only)
│   └── steps.py             <- the demo script: what is said, what runs
├── systemd-unit/            <- proves systemd is PID 1 in a container
│   └── molecule/default/
│       ├── molecule.yml     <- REFERENCE-CONFIG §2b
│       ├── converge.yml     <- §3.2
│       ├── verify.yml       <- §7.2   <- the crux playbook
│       ├── requirements.yml <- §4
│       └── cleanup.yml      <- (doc gap; see DBG-6)
├── quickstart/              <- minimal copy/write/assert scenario
│   └── molecule/default/
│       ├── molecule.yml     <- §2a
│       ├── converge.yml     <- §3.1
│       ├── verify.yml       <- §3.3
│       ├── requirements.yml <- §4
│       └── cleanup.yml      <- (doc gap; see DBG-6)
└── multi-scenario/          <- one project, two scenarios (default + systemd)
    ├── README.md            <- what the two scenarios demonstrate
    └── molecule/
        ├── default/         <- plain container, no systemd anywhere
        └── systemd/         <- systemd as PID 1
```

**`create.yml` and `destroy.yml` are deliberately absent.** `REFERENCE-CONFIG.md` §9.1 says
they are scaffolded "because Molecule's own architecture requires them". On the podman driver
that is false, and shipping them **breaks the run** — they override the driver's own create
playbook, so no container is ever created. See DBG-3 in `VERIFICATION.md`.

---

## 2. `systemd-unit/` — what it proves

Proves the flagship claim: **systemd is PID 1 inside a rootless Podman container, and a unit
the test installed and started is active.** Uses the prebuilt
`registry.access.redhat.com/ubi9/ubi-init:latest` image — no `Dockerfile.j2`, no build step.

### Run `systemd-unit/`

```bash
export PATH="/tmp/opencode/molvenv/bin:$PATH"   # molecule only runs if its bin/ is on PATH
cd "$(git rev-parse --show-toplevel)/examples/systemd-unit"
molecule test
```

Iterate faster with `molecule create` → `molecule converge` → `molecule verify`, and always
`molecule destroy` when finished.

### `systemd-unit/` transcript (trimmed from a passing run)

```console
$ molecule test
INFO     [default > dependency] Executing
INFO     [default > dependency] Executed: Successful
INFO     [default > create] Executing
TASK [Create Dockerfiles from image names] *************************************
changed: [localhost] => (item="Dockerfile: None specified; Image: registry.access.redhat.com/ubi9/ubi-init:latest")
TASK [Create molecule instance(s)] *********************************************
ok: [localhost] => (item=instance)
INFO     [default > create] Executed: Successful
INFO     [default > converge] Executing

PLAY [Converge] ****************************************************************
TASK [Wait for systemd to finish booting] **************************************
ok: [instance]
TASK [Wait for systemd to settle (running or degraded)] ************************
ok: [instance]
TASK [Install the test service under test] *************************************
changed: [instance]
TASK [Reload systemd so it sees the new unit] **********************************
ok: [instance]
TASK [Start and enable the test service] ***************************************
changed: [instance]
INFO     [default > converge] Executed: Successful
INFO     [default > idempotence] Executed: Successful
INFO     [default > verify] Executing

PLAY [Verify systemd and the test service] *************************************
TASK [Read what PID 1 is] ******************************************************
ok: [instance]
TASK [Confirm systemd is the top process] **************************************
ok: [instance] => {
    "changed": false,
    "msg": "systemd is PID 1."
}
TASK [Read the container UUID that Podman sets in systemd mode] ****************
ok: [instance]
TASK [Collect the instance's service facts] ************************************
ok: [instance]
TASK [Confirm systemd is running the managed service] **************************
ok: [instance] => {
    "changed": false,
    "msg": "molecule-demo.service is active."
}
TASK [Show the systemd state and any failed units (diagnostic, non-fatal)] *****
ok: [instance]
TASK [Print the diagnostics] ***************************************************
ok: [instance] => {
    "sd.stdout_lines": [
        "running",
        "  UNIT LOAD ACTIVE SUB DESCRIPTION",
        "0 loaded units listed."
    ]
}
INFO     [default > verify] Executed: Successful
INFO     [default > cleanup] Executed: Successful
INFO     [default > destroy] Executed: Successful

SCENARIO RECAP
default                   : actions=8  successful=7  disabled=0  skipped=0  missing=0  failed=0
$ echo $?
0
```

> **The check, on your own run — two conditions, both required:**
>
> 1. **The `PLAY RECAP` shows `ok=N` with `N > 0`.** For this scenario a healthy run looks like
>    `instance : ok=7 changed=0 unreachable=0 failed=0 skipped=0 rescued=0`. `ok=0`, or no
>    `PLAY RECAP` line for `instance` at all, means nothing ran.
> 2. **There are zero `skipping: no hosts matched` lines** anywhere in the output. One appearing
>    anywhere means that play asserted nothing, whatever the exit code.
>
> Also check the scenario recap reads **`missing=0`** — a non-zero `missing` means the
> `cleanup.yml` this example ships is absent. And the third, free signal: the two `msg` strings
> above, `systemd is PID 1.` and `molecule-demo.service is active.`, should be visible. Absent means
> the asserts did not execute.
>
> **`failed=0` and `echo $? → 0` on their own prove nothing** — that is exactly the shape a vacuous
> run takes. One line in `molecule.yml` decides all of this: `groups: [molecule]`.
> Full diagnosis: [`docs/troubleshooting.md` §1](../docs/troubleshooting.md).

Note `Print the diagnostics` is the **only** place the real systemd state appears, and it is
empty unless the `command` → `shell` fix (DBG-4) is applied. It reports
`is-system-running = running` and **0 failed units** on this host — the best case, not the
guaranteed one. §7.1 of `REFERENCE-CONFIG.md` is right that `degraded` is also a correct
rootless outcome.

---

## 3. `quickstart/` — what it proves

The minimal path: converge writes a marker file, verify asserts it exists and has the right
content. `REFERENCE-CONFIG.md` §2a/§3.1/§3.3.

> **Read DBG-5 first.** §2a is titled *"quickstart, no systemd"* and its own first comment says
> *"No systemd, no custom image"* — but it sets `command: /sbin/init`, `override_command: true`
> and `systemd: always` against `ubi9/ubi-init`, an image that *contains* systemd. As shipped it
> is a systemd scenario wearing a "no systemd" label. This example reproduces §2a verbatim (plus
> the required `groups:` fix) so it is a faithful, runnable proof of what the doc actually
> produces; the fix is described in `VERIFICATION.md`.

### Run `quickstart/`

```bash
export PATH="/tmp/opencode/molvenv/bin:$PATH"
cd "$(git rev-parse --show-toplevel)/examples/quickstart"
molecule test
```

### `quickstart/` transcript (trimmed from a passing run)

```console
$ molecule test
INFO     [default > dependency] Executed: Successful
INFO     [default > create] Executed: Successful
INFO     [default > converge] Executing

PLAY [Converge] ****************************************************************
TASK [Write a marker file] *****************************************************
changed: [instance]
TASK [Read the marker file back] ***********************************************
ok: [instance]
INFO     [default > converge] Executed: Successful
INFO     [default > idempotence] Executed: Successful
INFO     [default > verify] Executing

PLAY [Verify] ******************************************************************
TASK [Read the marker file back] ***********************************************
ok: [instance]
TASK [Assert the marker file exists and has the right content] ****************
ok: [instance] => {
    "changed": false,
    "msg": "The marker file is there."
}
TASK [Assert the file content] *************************************************
ok: [instance]
TASK [Check the content] *******************************************************
ok: [instance] => {
    "changed": false,
    "msg": "The content is correct."
}
INFO     [default > verify] Executed: Successful
INFO     [default > cleanup] Executed: Successful
INFO     [default > destroy] Executed: Successful

SCENARIO RECAP
default                   : actions=8  successful=7  disabled=0  skipped=0  missing=0  failed=0
$ echo $?
0
```

> **The check, on your own run — two conditions, both required:**
>
> 1. **The `PLAY RECAP` shows `ok=N` with `N > 0`.** For this scenario a healthy run looks like
>    `instance : ok=4 changed=0 unreachable=0 failed=0 skipped=0 rescued=0`. `ok=0`, or no
>    `PLAY RECAP` line for `instance` at all, means nothing ran.
> 2. **There are zero `skipping: no hosts matched` lines** anywhere in the output. One appearing
>    anywhere means that play asserted nothing, whatever the exit code.
>
> Also check the scenario recap reads **`missing=0`**, and that the two `msg` strings above —
> `The marker file is there.` and `The content is correct.` — are visible. Absent means the asserts
> did not execute.
>
> **`failed=0` and `echo $? → 0` on their own prove nothing** — that is exactly the shape a vacuous
> run takes. One line in `molecule.yml` decides all of this: `groups: [molecule]`.
> Full diagnosis: [`docs/troubleshooting.md` §1](../docs/troubleshooting.md).

Idempotence passes, so `converge` is genuinely idempotent (`changed: [instance]` on run 1 only).

---

## 4. `multi-scenario/` — two scenarios in one project

`multi-scenario/` holds those same two scenarios as sibling folders — `molecule/default/`
(plain container, no systemd) and `molecule/systemd/` (systemd as PID 1) — so
`molecule test -s default` and `molecule test -s systemd` are two independent verdicts in
one project. Both were run to `exit 0`, with `ok=4` and `ok=7` in the verify recap and zero
`no hosts matched` lines. What the pair demonstrates, and the `group_vars` trap it avoids,
is in [`multi-scenario/README.md`](multi-scenario/README.md).

---

## 5. `demo/` — the demo recording pipeline

![Animated terminal recording of this project's demo on Fedora 44: a real `molecule test` run with rootless Podman 5.8.7 and Molecule 26.9.0. It shows the pre-flight check passing every check, `molecule --version` and the driver list including `podman`, the four keys in `molecule.yml` that make systemd PID 1, the verify recap reporting `ok=7` alongside `systemd is PID 1.` and `molecule-demo.service is active.`, a plain `podman run --systemd=always` container reporting `running`, the same container re-run with `--privileged` reporting `degraded`, and cleanup leaving no containers behind.](./demo/demo.gif)

The video is not hand-animated. `demo/record.py` runs every command for real in a pseudo-terminal,
and the callout cards pull their lines out of the captured output — so a claim that stops being
true makes a card go empty rather than lie. It records from a `git clone` at a neutral path
(`/tmp/molecule-demo-home/proj`) rather than from a checkout, and a leak check **refuses to write
the GIF** if the recording machine's home directory or username reaches the frames; because it
runs from a clone, the video always shows the committed state. The renderer is Pillow alone — no
asciinema, no ffmpeg, no headless browser, no network.

```bash
asciinema play examples/demo/demo.cast     # the raw recording, re-playable
grep -n "ok=" examples/demo/demo.txt       # grep the transcript; the docs were written this way
python3 examples/demo/record.py --check    # record without rendering
python3 examples/demo/record.py --reuse    # re-render from cached frames, without re-running
```

`demo/README.md` has the full pipeline, the per-platform install commands for Pillow and a
box-drawing-capable monospace font, how to work with the leak check, and an honest
known-limitations section — including the fact that **only the Fedora/x86_64 path has actually
been recorded**. The beat-by-beat walkthrough, with the transcript quoted, is
[`docs/demo.md`](../docs/demo.md).

---

## 6. Cleanup

```bash
REPO="$(git rev-parse --show-toplevel)"
for scenario in systemd-unit quickstart multi-scenario; do
  (cd "$REPO/examples/$scenario" && molecule destroy)
done
podman ps -a   # expect: header row only
```

Verified after the final runs: `podman ps -a` lists **no containers**, and the scenario network
is removed from `podman network ls`. The demo recording leaves nothing behind either — its last
beat is the same `molecule destroy` followed by `podman ps -a`.
