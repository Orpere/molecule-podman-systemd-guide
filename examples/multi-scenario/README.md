# `examples/multi-scenario/` — two scenarios, one role, two verdicts

A Molecule project with **two scenarios in one project**, both executed end to end on the
target host (Fedora 44 · rootless podman 5.8.7 · SELinux Enforcing · cgroup v2 · x86_64)
against molecule 26.9.0 · molecule-plugins 26.9.28 · ansible-core 2.21.4. Both runs exit
**0** with the assertions genuinely executed — zero `no hosts matched` lines, and a
`PLAY RECAP` with `ok=N` and `N > 0` in the verify play. See `../VERIFICATION.md` (DBG-1)
for why a green exit code on its own proves nothing.

> This is the tree that `docs/authoring/multi-scenario.md` links to. The files are copies
> of the two already-verified single-scenario projects (`../quickstart/` and
> `../systemd-unit/`), not re-invented: only the header comments and, in `default/`, the
> image plus the three systemd keys differ. Every explanatory comment — including the
> `groups: [molecule]` reason comment — is carried over verbatim. Do not delete those
> comments; the `groups` key is the difference between a real test and a silent false pass.

---

## 1. Layout

```text
multi-scenario/
├── README.md
└── molecule/
    ├── default/                 <- plain container, no systemd anywhere
    │   ├── molecule.yml
    │   ├── converge.yml
    │   ├── verify.yml
    │   ├── requirements.yml
    │   └── cleanup.yml
    └── systemd/                 <- systemd as PID 1
        ├── molecule.yml
        ├── converge.yml
        ├── verify.yml
        ├── requirements.yml
        └── cleanup.yml
```

Molecule hard-requires the glob `molecule/*/molecule.yml`, so each scenario is a folder with
its own complete set of files. There is no `group_vars/` anywhere in this project — that
absence is deliberate; see "The trap this tree avoids" below.

---

## 2. What the two scenarios demonstrate

| | `default/` | `systemd/` |
|---|---|---|
| Image | `ghcr.io/ansible/community-ansible-dev-tools:latest` | `registry.access.redhat.com/ubi9/ubi-init:latest` |
| `command:` / `override_command:` / `systemd:` | **absent** — the driver's default sleep loop keeps the container alive | `command: /sbin/init`, `override_command: true`, `systemd: always` |
| PID 1 in the container | whatever the image's own command is | `systemd` |
| What converge does | write a marker file, read it back | wait for the boot, install + start a `.service` unit, reload systemd |
| What verify asserts | the marker file exists and its content is right | systemd is PID 1, the unit is active, and the state is printed as a diagnostic |
| Verify recap on this host | `instance : ok=4` | `instance : ok=7` |
| `groups: [molecule]` | present | present |

**The one-sentence version:** the two scenarios differ in *image and three keys*, not in
tasks — which is exactly why `docs/authoring/multi-scenario.md` says to split when the
image or the `test_sequence` differs, and not when only the `assert` list does.

`default/` is also the answer to defect DBG-5 in `../VERIFICATION.md`: the genuinely
non-systemd path that the quickstart's own comment points at, kept as a second scenario
next to the systemd one instead of replacing it.

---

## 3. Run it

```bash
export PATH="/tmp/opencode/molvenv/bin:$PATH"   # molecule only runs if its bin/ is on PATH
cd "$(git rev-parse --show-toplevel)/examples/multi-scenario"

molecule list            # both scenarios are discovered
molecule test -s default             # or the long form: --scenario-name default
molecule test -s systemd
molecule test            # both, in series
```

`-s` belongs to the `test` subcommand: `molecule test -s default`, **not**
`molecule -s default test` (that form exits 1 with `Error: No such option '-s'` on
molecule 26.9.0).

Iterate faster with `molecule create` → `molecule converge` → `molecule verify`, and always
`molecule destroy` when finished:

```bash
cd "$(git rev-parse --show-toplevel)/examples/multi-scenario" && molecule destroy
podman ps -a   # expect: header row only
```

---

## 4. Real transcripts (trimmed from passing runs)

### `molecule test -s default`

```console
$ molecule test -s default
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
TASK [Assert the marker file exists and has the right content] ****************
ok: [instance] => {
    "changed": false,
    "msg": "The marker file is there."
}
TASK [Check the content] *******************************************************
ok: [instance] => {
    "changed": false,
    "msg": "The content is correct."
}
PLAY RECAP *********************************************************************
instance                   : ok=4    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

INFO     [default > cleanup] Executed: Successful
INFO     [default > destroy] Executed: Successful

SCENARIO RECAP
default                   : actions=8  successful=7  disabled=0  skipped=0  missing=0  failed=0
$ echo $?
0
```

### `molecule test -s systemd`

```console
$ molecule test -s systemd
INFO     [systemd > dependency] Executed: Successful
INFO     [systemd > create] Executed: Successful
INFO     [systemd > converge] Executing

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
INFO     [systemd > converge] Executed: Successful
INFO     [systemd > idempotence] Executed: Successful
INFO     [systemd > verify] Executing

PLAY [Verify systemd and the test service] *************************************
TASK [Confirm systemd is the top process] **************************************
ok: [instance] => {
    "changed": false,
    "msg": "systemd is PID 1."
}
TASK [Confirm systemd is running the managed service] **************************
ok: [instance] => {
    "changed": false,
    "msg": "molecule-demo.service is active."
}
TASK [Print the diagnostics] ***************************************************
ok: [instance] => {
    "sd.stdout_lines": [
        "running",
        "  UNIT LOAD ACTIVE SUB DESCRIPTION",
        "0 loaded units listed."
    ]
}
PLAY RECAP *********************************************************************
instance                   : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

INFO     [systemd > cleanup] Executed: Successful
INFO     [systemd > destroy] Executed: Successful

SCENARIO RECAP
systemd                   : actions=8  successful=7  disabled=0  skipped=0  missing=0  failed=0
$ echo $?
0
```

Both runs: `grep -c 'no hosts matched'` over the full log returns **0**. That check is the
one that matters — an exit code of 0 with `skipping: no hosts matched` on every play is the
silent false pass this project exists to prevent.

---

## 5. The trap this tree avoids

Molecule's own shipped Podman example contains a `group_vars/molecule.yml` with
`container_systemd: false`. In Ansible, `group_vars` outranks an inline group `vars:`, so
such a file would silently override the inline `always` — no warning, no error, and the
container does not run systemd. There is **no `group_vars/` directory in this project**, and
both scenarios carry `groups: [molecule]` on their platform entry, which is the other half
of the same trap: without it there is no `molecule` group at all and `hosts: molecule`
matches nothing (DBG-1).

See `../VERIFICATION.md` for every claim tested and every documentation bug found.

---

## 6. Troubleshooting

| Symptom | Entry in [`../../docs/troubleshooting.md`](../../docs/troubleshooting.md) |
|---|---|
| `skipping: no hosts matched` on every play, exit 0 | entry 1 — the silent false pass (DBG-1) |
| `Container 'instance' not found` | entry 4 |
| `System has not been booted with systemd` | entry 5 — what a *missing* `systemd:` key looks like in the `systemd` scenario |
| `No module named systemd` / no Python in the image | entry 9 |
| `Missing playbook` for `cleanup` | entry 14 |
| `CRITICAL 'molecule/*/molecule.yml' glob failed` | entry 15 |

---

## 7. One declared variant

`STRUCTURE.md` §2 asks that every YAML file in an example tree be byte-identical to a
canonical block in `REFERENCE-CONFIG.md`, and that a variant be added to
`REFERENCE-CONFIG.md` first. `molecule/default/molecule.yml` is the one file here that is a
**declared variant** rather than a copy: §2a is the "init image with `systemd: always`"
shape, and this scenario is the deliberately non-systemd one. The requirement it satisfies —
an image that contains Python, with no init to run — is the requirement stated in
`docs/authoring/custom-images.md`. It is called out here and in the file's own header
comment rather than left silent. Every other file in this tree is a copy, and the
`groups: [molecule]` fix is applied exactly as documented.

---

## 8. Attribution

No brand marks or logos are displayed in this directory. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md); product names identify the
software being discussed and imply no endorsement.
