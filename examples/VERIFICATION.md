# `examples/VERIFICATION.md` — live end-to-end verification

**Verifier:** qa-test-engineer (routed to `general`; specialist quota exhausted).
**Date:** 2026-09-28. **Result: both examples PASS (`molecule test` exit 0), and four of the
canonical artifacts do not work as written.**

## 0. Environment actually used

| Fact | Observed |
|---|---|
| OS / arch | Fedora 44 · x86_64 |
| podman | 5.8.7, **rootless**, SELinux **Enforcing**, cgroup v2 |
| molecule | 26.9.0 (`molecule_plugins` 26.9.28, ansible-core 2.21.4) |
| `containers.podman` collection | 1.20.2 (resolved by the `dependency` step from `requirements.yml`) |
| python | 3.14 |
| venv on PATH | `/tmp/opencode/molvenv/bin` — **mandatory** |

Final state after all runs: `podman ps -a` → **no containers**. `podman network ls` → scenario
network gone.

---

## 1. Headline: a documented run that silently passes without asserting anything

This is the single most important finding and it is worse than a crash.

Running `examples/systemd-unit` built **verbatim** from `REFERENCE-CONFIG.md` §2b/§3.2/§7.2:

```console
$ molecule test
INFO     [default > converge] Executing
[WARNING]: Could not match supplied host pattern, ignoring: molecule
PLAY [Converge] ****************************************************************
skipping: no hosts matched
...
INFO     [default > verify] Executing
[WARNING]: Could not match supplied host pattern, ignoring: molecule
PLAY [Verify systemd and the test service] *************************************
skipping: no hosts matched
...
SCENARIO RECAP
default                   : actions=8  successful=6  disabled=0  skipped=0  missing=1  failed=0
$ echo $?
0
```

**Exit code 0. `failed=0`. Every play skipped. Not one assertion executed.** The crux playbook
of the entire documentation site — the thing `§7` says is *"the single most important file in
the project"* — never ran a single task, and Molecule reported success. A reader following
`docs/systemd-in-containers.md` gets a green, reassuring, completely empty run.

---

## 2. Doc bugs, in severity order

### DBG-1 🔴 CRITICAL — missing `groups: [molecule]` causes a silent false pass

**Affects:** §2a, §2b, and every playbook targeting `hosts: molecule` (§3.1, §3.2, §3.3, **§7.2**).

**Symptom:** every play reports `skipping: no hosts matched`; `molecule test` exits **0**.

**Root cause** — `molecule/provisioner/ansible.py`:
```python
for platform in self._config.platforms.instances:
    for group in platform.get("groups", ["ungrouped"]):
```
There is no implicit `molecule` group. Molecule's own scaffolded `converge.yml` uses
`hosts: all`, and `molecule init scenario` scaffolds no `groups:` key. Proven directly:

```console
"msg": "GROUPS=['all', 'ungrouped']"        # before the fix
"msg": "GROUPS=['all', 'molecule', 'ungrouped']"   # after the fix
```

**Fix** — add to `platforms[0]` in both §2a and §2b:
```yaml
    groups:
      - molecule
```
Verified: with this line, `hosts: molecule` matches, both assertions run, run goes green with
zero `no hosts matched` warnings.

> The `provisioner.inventory.host_vars` block is **not** the culprit and is correct as written —
> `ansible_connection: containers.podman.podman` is applied and works
> (`"msg": "CONN=containers.podman.podman"`).

**Documentation action:** every page that shows a `molecule.yml` and every playbook that says
`hosts: molecule`. The docs should also warn explicitly that a green `molecule test` with
`skipping: no hosts matched` is a *silent failure*, not a pass.

### DBG-2 🔴 CRITICAL — `wait_for: state: directory` is a fatal error on ansible-core 2.21.4

**Affects:** §3.2 — the first task of the canonical systemd `converge.yml`.

**Symptom:**
```
TASK [Wait for systemd to finish booting] **************************************
[ERROR]: Task failed: Module failed: value of state must be one of:
         absent, drained, present, started, stopped, got: directory
Origin: molecule/default/converge.yml:8:7
fatal: [instance]: FAILED! => {"msg": "value of state must be one of: ... got: directory"}
```

**Root cause** — ansible-core 2.21.4 `ansible/modules/wait_for.py:494`:
```python
state=dict(type='str', default='started',
           choices=['absent', 'drained', 'present', 'started', 'stopped']),
```
The string `directory` appears **zero times** in the module. The `directory` / `file` / `socket`
states were removed. `§0` nevertheless marks §3.2 "✅ Verified".

**Fix** — `state: present` (`started`, the default, is the same "path exists" test):
```yaml
    - name: Wait for systemd to finish booting
      ansible.builtin.wait_for:
        path: /run/systemd/system
        state: present      # was: directory  -> fatal on ansible-core >= 2.19
        timeout: 30
```
Verified working; the documented intent ("wait for `/run/systemd/system` to appear") is preserved.

### DBG-3 🔴 HIGH — shipping `create.yml` / `destroy.yml` breaks the podman driver

**Affects:** §9.1, which states they are scaffolded *"because Molecule's own architecture
requires them"* and that *"the driver owns the container lifecycle"*.

**Symptom** — with the scaffolded stubs present, the create step runs **only the inert local
stub** and no container is ever created:
```
INFO     [default > create] Executing
PLAY [Create] ******************************************************************
TASK [Populate instance config dict] *******************************************
skipping: [localhost]
TASK [Convert instance config dict to a list] **********************************
skipping: [localhost]
INFO     [default > create] Executed: Successful      <-- "successful", but nothing was created
...
TASK [Wait for systemd to finish booting] **************************************
[ERROR]: Task failed: Command execution failed: Container 'instance' not found
```

**Root cause:** molecule resolves the scenario's own `create.yml` *before* falling back to the
driver's. The driver's real playbook (`molecule_plugins/podman/playbooks/create.yml`) contains
`Create Dockerfiles from image names`, `Create podman network dedicated to this scenario`,
`Create molecule instance(s)`, `Wait for instance(s) creation to complete` — none of which
appear in the run. Removing the two files makes the driver's playbook run and the container
appear.

**Fix:** under the podman driver, **do not ship `create.yml` or `destroy.yml`**. Amend §9.1 to
say the opposite of what it currently says. (If a page must show them for the
*Ansible-native* route, label them clearly as that route only — and note the existing warning
about `tasks/create-fail.yml`.)

### DBG-4 🟡 MEDIUM — §7.2's diagnostics use `command` with a `;` compound, so the promised output is unreachable

**Affects:** §7.2's *"Show the systemd state and any failed units"* task and the *"Expected
output on a healthy run"* block directly beneath it.

**Symptom:**
```console
TASK [Print the diagnostics] ***************************************************
ok: [instance] => {
    "sd.stdout_lines": []
}
```
Empty. But §7.2 promises:
```
"msg": [
    "running",
    "  UNIT                        LOAD   ACTIVE SUB     DESCRIPTION",
    "0 loaded units listed."
]
```

**Root cause:** `ansible.builtin.command` does **not** invoke a shell, so
`"systemctl is-system-running; systemctl --failed --no-pager || true"` is passed as a single
`argv[0]`. No such executable exists, the exec fails, and `failed_when: false` swallows it
silently. `;` and `||` are shell syntax that `command` cannot honour.

**Fix:** use `ansible.builtin.shell`:
```yaml
    - name: Show the systemd state and any failed units (diagnostic, non-fatal)
      ansible.builtin.shell: "systemctl is-system-running; systemctl --failed --no-pager || true"
      register: sd
      changed_when: false
      failed_when: false
```
Verified: this reproduces the §7.2 sample output exactly (`running` / `0 loaded units listed`),
so the doc's promised block is achievable — it is only the module that is wrong.
(Cosmetic: the real header renders as `UNIT LOAD ACTIVE SUB DESCRIPTION`, not the
column-padded `UNIT                        LOAD   ACTIVE SUB     DESCRIPTION` shown in the doc —
tab-width dependent. Not worth "fixing" beyond a screenshot.)

### DBG-5 🟡 MEDIUM — §2a contradicts itself: "no systemd" but is a systemd scenario

**Affects:** §2a, and by reference the quickstart page.

`§2a` is titled *"quickstart, no systemd"*; its first comment says *"No systemd, no custom
image."* Its body then sets:
```yaml
    image: registry.access.redhat.com/ubi9/ubi-init:latest
    command: /sbin/init
    override_command: true
    systemd: always
```
`ubi9/ubi-init` **contains** systemd (verified: `systemctl is-system-running` → `running`,
PID 1 → `systemd`). The file also carries a comment advertising a genuinely non-systemd
alternative — `ghcr.io/ansible/community-ansible-dev-tools:latest`, *"keep `command:` as the
driver's default sleep and do NOT set `systemd:`"* — that its own configuration contradicts.

**Fix:** either retitle §2a to what it is, or ship the real non-systemd config (swap the image,
delete the three keys, keep `groups: [molecule]` per DBG-1, and use `hosts: all` or keep
`groups`). A beginner reading "no systemd" and then seeing `systemd: always` learns to distrust
the page.

### DBG-6 ⚪ MINOR — `cleanup` is in both test sequences but no `cleanup.yml` is ever shipped

**Affects:** §2a, §2b, §9.2.

Every documented run emits:
```
WARNING  [default > cleanup] Executed: Missing playbook (Remove from test_sequence to suppress)
...
SCENARIO RECAP: missing=1
```
Harmless (not a failure) but it is noise on a beginner's first run and it makes the recap read
as though something is missing. **Fix:** ship a `cleanup.yml` in §2a/§2b (the scaffolded
`# Developer must implement.` stub is enough), or drop `cleanup` from the sequences. Both
examples here ship a minimal `cleanup.yml`.

### DBG-7 ⚪ MINOR — the flat example layout in the task brief cannot work

`molecule.yml` at the project root is impossible:
```console
$ molecule list
CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.
```
Both examples therefore use `examples/<name>/molecule/default/`, which is also the canonical
path in §0. Worth stating explicitly in the docs, because a reader who hand-rolls a flat layout
hits an unhelpful `CRITICAL` with no hint.

---

## 3. Claim-by-claim verdict table

| # | Claim under test | Verdict | Evidence |
|---|---|---|---|
| 1 | **C-1**: `privileged: false` is right; `privileged: true` breaks systemd | **CONFIRMED** | `--privileged` → `is-system-running=degraded`; failed units are *exactly* the three STRUCTURE.md §8 C-1 names: `sys-kernel-config.mount`, `sys-kernel-debug.mount`, `sys-kernel-tracing.mount`. `privileged: false` → `running`, 0 failed. Decision D1 is correct; the driver docstring is the wrong source. |
| 2 | `systemd: always` is genuinely required | **REFUTED** | `--systemd=true` + `command /sbin/init` → `running`, 0 failed, PID 1 = `systemd`. **No `--systemd` flag at all** + `/sbin/init` → also `running`, PID 1 = `systemd`, and `container_uuid` present. `always` is *defensive*, not required. §2b's stated failure (`State.ExitCode=255`, empty logs) never occurred. The doc's own reasoning is self-defeating: it says `true` engages systemd mode "when the command is literally `/sbin/init`" — which is precisely the `command:` the doc sets. |
| 3 | `override_command: true` is genuinely mandatory | **REFUTED** (as stated) | `override_command: false` + `ubi9/ubi-init` → PID 1 = `systemd`. Reason: the image's default CMD *is* `/sbin/init` (`podman inspect` → `CMD=[/sbin/init]`), and the driver docstring itself says *"consuming a built image which declares a `CMD` directive, then you must set `override_command: False`"*. `true` is harmless here but is not mandatory, and it would be **wrong** for the §1.1 `Dockerfile.j2` route if that image declares a `CMD`. Keep it only because it makes intent explicit and is image-independent. |
| 4 | The prebuilt `ubi9/ubi-init` image boots systemd here, no build needed | **CONFIRMED** | Fresh pull, `--systemd=always /sbin/init`: PID 1 `systemd`, `is-system-running` → `running`, `systemctl --failed` → `0 loaded units listed`, `/usr/bin/python3` present. §1.3's table is accurate. |
| 5 | `ansible-config` on PATH (PLAN.md Trace T3) bites as described | **CONFIRMED** | With the venv `bin/` off PATH: `molecule --version` → `FileNotFoundError: [Errno 2] No such file or directory: 'ansible-config'`, **exit 1**. Molecule 26.9 shells out to `ansible-config` at start-up. |
| 6 | The documented `converge.yml` systemd-boot wait works | **PARTLY REFUTED** | It is a hard **fatal error**, not merely mis-tuned — `state: directory` is rejected outright on ansible-core 2.21.4 (DBG-2). With `state: present` the wait works, and 30 s is ample on this host (systemd was ready well inside it). No evidence that 30 s is too long or too short here. |
| 7 | `requirements.yml` resolves | **CONFIRMED** | The `dependency` step installed `containers.podman 1.20.2` from `>=1.10.0`; `dependency: Executed: Successful` in every run. |
| 8 | The `containers.podman` connection plugin works as documented | **CONFIRMED** | `"msg": "CONN=containers.podman.podman"`; all tasks executed against the container (`/proc/1/comm`, `service_facts`, `systemd`). The FQCN in §2a/§2b is right and is not the `community.docker` confusion the doc warns about. |
| 9 | §7.2's expected diagnostic output is reproducible | **REFUTED as written; CONFIRMED after fix** | `command` → `sd.stdout_lines: []`. `shell` → `["running", "  UNIT LOAD ACTIVE SUB DESCRIPTION", "0 loaded units listed."]` (DBG-4). |
| 10 | `create.yml` / `destroy.yml` are safe to include | **REFUTED** | They silently prevent container creation and produce `Container 'instance' not found` (DBG-3). |
| 11 | `docker` is never required (podman-only path) | **CONFIRMED** | No `docker`/`docker-compose` invoked anywhere; `podman` 5.8.7 rootless throughout. `community.docker` correctly absent. |
| 12 | macOS claims (C-7), `podman info` SELinux field (C-4), pipx (C-5) | **UNVERIFIED** | Out of scope for this host (x86_64 Fedora). Not retested; C-4 in particular concerns a `podman info` template, not a Molecule path, and is unaffected by the four bugs above. |

---

## 4. What a passing run actually looked like

```console
# systemd-unit
default > dependency: Executed: Successful
default > create:     Executed: Successful
default > converge:   Executed: Successful
default > idempotence: Executed: Successful
default > verify:     Executed: Successful
default > cleanup:    Executed: Successful
default > destroy:    Executed: Successful
SCENARIO RECAP: default : actions=8  successful=7  disabled=0  skipped=0  missing=0  failed=0
exit 0        # and: 0 occurrences of "no hosts matched"

# quickstart
SCENARIO RECAP: default : actions=8  successful=7  disabled=0  skipped=0  missing=0  failed=0
exit 0        # and: 0 occurrences of "no hosts matched"
```

Both verified non-vacuous by asserting the success messages appear in the log
(`systemd is PID 1.`, `molecule-demo.service is active.`, `The marker file is there.`,
`The content is correct.`) — never by the exit code alone, which is what let DBG-1 hide.

---

## 5. Required changes to `REFERENCE-CONFIG.md`

Ordered by blast radius. No page that quotes these files is correct until all six land.

1. **§2a, §2b** — add `groups:\n  - molecule` to `platforms[0]`. *(DBG-1 — silent false pass.)*
2. **§3.2** — `state: directory` → `state: present` in the `wait_for` task. *(DBG-2 — fatal.)*
3. **§9.1** — reverse the `create.yml` / `destroy.yml` guidance for driver-based scenarios. *(DBG-3.)*
4. **§7.2** — `ansible.builtin.command` → `ansible.builtin.shell` for the diagnostics task. *(DBG-4.)*
5. **§2a** — resolve the "no systemd" self-contradiction. *(DBG-5.)*
6. **§2a, §2b, §9.2** — ship a `cleanup.yml` or drop `cleanup` from the sequences. *(DBG-6.)*

Plus a wording correction, not a code fix: §2b's justification for `systemd: always` and
`override_command: true` should be restated as *"explicit and image-independent"* rather than
*"mandatory"* / *"only engages when the command is `/sbin/init`"*, since both were empirically
shown to be unnecessary for `ubi9/ubi-init` (claims 2 and 3).

---

## Appendix B — `examples/multi-scenario/` run record (added during final integration)

**Why this appendix exists.** `examples/README.md` and `examples/multi-scenario/README.md` both
claim this project was run to `exit 0` and point the reader at this file as the authority. Until
this appendix was added that claim was **unevidenced** — the original run had only two scenarios
recorded. A documentation project that tells readers its transcripts are real must be able to show
the real thing, including for the tree added later.

**Command form.** `molecule test -s <name>` is the valid form in Molecule 26.9.0.
`molecule -s <name> test` fails with `No such option '-s'`. Both READMEs have been corrected.

**Environment.** Fedora 44 · x86_64 · rootless `podman 5.8.7` · `cgroup2fs` · SELinux Enforcing ·
Python 3.14 · Molecule 26.9.0 · molecule-plugins 26.9.28 · ansible-core 2.21.4 · `containers.podman`
collection pinned to `1.20.2`.

### B.1 `molecule test -s default`

```
instance                   : ok=4    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Exit code `0`. Grep for `no hosts matched` across the full log: **0 occurrences**.

### B.2 `molecule test -s systemd`

```
instance                   : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Exit code `0`. Grep for `no hosts matched`: **0 occurrences**. The two load-bearing assertion
messages are identical to the standalone `systemd-unit` project:

```json
{ "changed": false, "msg": "systemd is PID 1." }
{ "changed": false, "msg": "molecule-demo.service is active." }
```

`systemctl is-system-running` → `running`, with `0 loaded units listed.`

### B.3 Non-vacuity check — all four projects, one run

This is the check that matters, because **`exit 0` and `failed=0` are also exactly what a vacuous
pass produces.** See `PLAN.md` Trace T5.

| Project | exit | `ok=N` | `N>0` | `no hosts matched` | `missing` | verdict |
|---|---|---|---|---|---|---|
| `examples/systemd-unit` | 0 | 7 | yes | 0 | 0 | **REAL** |
| `examples/quickstart` | 0 | 4 | yes | 0 | 0 | **REAL** |
| `examples/multi-scenario -s default` | 0 | 4 | yes | 0 | 0 | **REAL** |
| `examples/multi-scenario -s systemd` | 0 | 7 | yes | 0 | 0 | **REAL** |

`examples/quickstart` asserted: `The marker file is there.` / `The content is correct.`

### B.4 Cleanup

`molecule destroy` was run for every project. `podman ps -a --format '{{.Names}}' | wc -l` → **0**.
No containers, no volumes, no leftover state.
