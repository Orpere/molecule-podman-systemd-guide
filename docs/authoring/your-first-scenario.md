# Your first scenario

> **You are here:** [Authoring](./index.md) → **Your first scenario** → [Project layout](./project-layout.md)

**What you will be able to do:** go from an empty folder to a green `molecule test` that
creates a container, applies your role to it, asserts the result, and deletes the container.

**Time:** about 10 minutes *(an unmeasured estimate, not a timed figure)*. **Cost:** $0 — every
package below is free.

---

## The shape of the thing you are building

A **role** is the reusable bundle of Ansible tasks. A **scenario** is one disposable test
environment that runs it. You are building both: `tasks/main.yml` is the product,
`molecule/default/` is the test. Molecule's own guide says so — *"The `molecule/` directory
and its scenario files are added for testing. They are not part of the role itself."*

---

## Three commands that no longer exist

Read this before your first command, because most tutorials online will tell you to type
something that fails. `molecule add`, `molecule remove`, and `molecule lint` **have been
removed** — not deprecated, gone. There is no source file for any of them.

| Removed command | What to use instead |
|---|---|
| `molecule add <name>` | `molecule init scenario <name>` |
| `molecule remove <name>` | `rm -r molecule/<name>` |
| `molecule lint` | `ansible-lint`, run standalone |

One more spelling trap: the command is **`molecule idempotence`**, with an *e*. There is no
`molecule idempotency`. Run `molecule --help` and you will see the real command list.

---

## 1. Make the project

```bash
mkdir -p my_role/tasks
cd my_role
git init
```

**You should see:** `mkdir` and `cd` print nothing. `git init` prints a short block ending
`Initialized empty Git repository in .../my_role/.git/`.

**What changed and why:** `git init` is not decoration. Molecule looks for a shared
configuration file at your **version-control root** — the top of the git repository — when
you add shared state between scenarios later. Without a repository there is no such root.

---

## 2. Write the role first

Write the role **before** the test. You cannot assert something you cannot observe.

```bash
cat > tasks/main.yml <<'EOF'
---
- name: Create a marker file
  ansible.builtin.copy:
    content: molecule role test
    dest: /tmp/molecule_role_marker
    mode: "0644"
EOF
```

**You should see:** no output. `cat tasks/main.yml` shows the five lines above.

**What changed and why:** `ansible.builtin.copy` is a *module* — a small program Ansible
ships that knows how to do one job properly. A marker file is the cheapest thing that is both
visible and assertable; testing a role whose only effect you cannot see is testing nothing.

`ansible.builtin.copy` is a **FQCN**, a **Fully Qualified Collection Name**: the collection
name, a dot, then the module. Always write it this way — a bare `copy:` is ambiguous once you
use more than one collection.

---

## 3. Generate the scenario

```bash
molecule init scenario default
```

**You should see:** Molecule reporting that it created the scenario. If it asks *What is the
scenario name?* first, type `default` and press Enter.

The precise facts — this is where beginners lose the most time:

- **`molecule init` has exactly one subcommand: `scenario`.** No `molecule init playbook`, no
  `molecule init driver`. A tutorial showing one is inventing it.
- **The scenario must live in `molecule/<name>/molecule.yml`.** That is the only layout that
  loads: Molecule hard-requires a `molecule/*/molecule.yml` glob. A flat `molecule.yml` at the
  project root is not "another valid arrangement" — `molecule list` aborts with
  `CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.` and gives you no hint why. Keep
  the `molecule/<name>/` shape that `init` creates.
- **It creates exactly 5 files.** Not more, not fewer.
- **It does *not* scaffold `requirements.yml`, `prepare.yml`, `side_effect.yml`,
  `cleanup.yml`, `inventory/`, `driver.py`, or `<scenario>/tests/`.** Every tutorial that
  says otherwise is describing a different tool.

```bash
ls molecule/default
```

**You should see** exactly these five names, one per line: `converge.yml`, `create.yml`,
`destroy.yml`, `molecule.yml`, `verify.yml`.

> **Molecule refuses to write into a non-empty folder**: *"Refused to expand templates as
> destination folder … as it already has content in it."* It protects a scenario you have been
> editing. If you hit it, you are in the wrong directory, or you ran this twice.

---

## 4. Add the one file Molecule will not create for you

Every driver-based scenario needs `requirements.yml`, and `molecule init scenario` will not
make it:

```bash
cat > molecule/default/requirements.yml <<'EOF'
---
# molecule/<scenario>/requirements.yml
collections:
  - name: containers.podman
    version: ">=1.10.0"
EOF
```

**You should see:** no output. `ls molecule/default` now shows six files.

**What changed and why:** this is the file that gets `containers.podman` installed. You never
run `ansible-galaxy` by hand — Molecule installs it during the `dependency` step, which is
why the `molecule.yml` in the next step names this path.

**Do not add `community.docker`.** It is not needed for the Podman path, and it invites a
specific confusion: `community.docker` ships only `docker`, `docker_api` and `nsenter` — it
contains **no** `podman` connection plugin at all. Yours is `containers.podman.podman`.

---

## 5. Wire it to the Podman driver

Replace the scaffolded `molecule.yml` with this, verbatim:

```yaml
---
# molecule/<scenario>/molecule.yml
# A scenario whose container runs systemd as PID 1.

driver:
  name: podman

platforms:
  - name: instance
    # ---- Option A: use a prebuilt init image (recommended, nothing to build) ----
    image: registry.access.redhat.com/ubi9/ubi-init:latest
    # Supply chain: `latest` is a moving tag, so two runs are not the same build and the
    # registry decides what you execute. OPTIONAL: append `@sha256:<digest>` to pin it --
    # get one with `podman image inspect --format '{{index .Digest}}' <the image above>`.
    # ---- Option B: build your own (uncomment the three lines below, and set
    #      `image` to a base WITHOUT systemd, e.g. debian:bookworm-slim) ----
    # pre_build_image: false          # MANDATORY: the default is `true`, which silently
    #                                 # skips the build. `item.image` above is the FROM line.
    # dockerfile: Dockerfile.j2       # optional; Dockerfile.j2 in the scenario dir is the default
    command: /sbin/init
    override_command: true
    systemd: always
    privileged: false
    # ---------------------------------------------------------------------------
    # REQUIRED (DBG-1). Molecule builds its Ansible groups from this key, defaulting
    # to ["ungrouped"] -- so there is NO implicit `molecule` group. Omit this line and
    # `hosts: molecule` in converge.yml/verify.yml matches nothing: every play reports
    # "skipping: no hosts matched" and `molecule test` still EXITS 0. Silent false pass.
    groups:
      - molecule
    # ---------------------------------------------------------------------------
    # Only uncomment when a unit genuinely needs it (PrivateTmp=, ProtectSystem=,
    # ProtectHome=, PrivateNetwork=, ReadWriteDirectories=, InaccessibleDirectories=).
    # systemd's own docs say do NOT drop CAP_SYS_ADMIN or CAP_MKNOD; Podman's defaults
    # include neither, so add only the one you need.
    # capabilities:
    #   - SYS_ADMIN

provisioner:
  name: ansible
  inventory:
    host_vars:
      instance:
        ansible_connection: containers.podman.podman

dependency:
  name: galaxy
  options:
    requirements-file: ${MOLECULE_SCENARIO_DIRECTORY}/requirements.yml

scenario:
  test_sequence:
    - dependency
    - destroy
    - create
    - converge
    - idempotence
    - verify
    - cleanup
    - destroy
```

**What changed and why — the lines that matter:**

| Setting | What it does |
|---|---|
| `ansible_connection: containers.podman.podman` | The **FQCN** of the connection plugin that drives the containers. It runs the `podman` **command-line tool**; there is no socket and no `DOCKER_HOST` in this path. |
| `groups: [molecule]` | Puts `instance` in an Ansible group named `molecule`, which is what `converge.yml` and `verify.yml` target with `hosts: molecule`. Molecule derives its groups from this key, defaulting to `["ungrouped"]` — **there is no implicit `molecule` group**. Omit it and every play prints `skipping: no hosts matched`, **zero** tasks run, and `molecule test` **exits 0**. Measured, not assumed. |
| `requirements-file: ${MOLECULE_SCENARIO_DIRECTORY}/requirements.yml` | `MOLECULE_SCENARIO_DIRECTORY` is the absolute path of this scenario's own folder. It is what makes the same `molecule.yml` work wherever you moved the project. |
| `test_sequence:` | The order the steps run in. `destroy` appears **twice** — start and end — so a crashed run cannot poison the next one. `idempotence` re-runs converge and fails if anything changed. |

> **Two files from step 3 that you now delete, and one you now add.**
>
> - **Delete `create.yml` and `destroy.yml`.** They are scaffolded because the *default* driver
>   needs them. Under the `podman` driver they are harmful: a scenario's own `create.yml` is
>   resolved *before* the driver's, so it **overrides** the driver's own playbook. The `create`
>   step then runs only the inert local stub, reports `Executed: Successful`, **builds no
>   container**, and step 6 dies with
>   `Command execution failed: Container 'instance' not found`. Under `podman`, `molecule.yml`
>   **is** the create/destroy configuration.
> - **Add `cleanup.yml`** (step 6b). `molecule init` does not scaffold it, but `test_sequence`
>   above calls the `cleanup` step; without it every run prints `Missing playbook` and the recap
>   reads `missing=1`.

Four more are the crux of this whole site:

- **`systemd: always` — recommend it, and know precisely why.** `true` only turns systemd mode on
  when the command is *literally* `systemd`, `/usr/sbin/init`, `/sbin/init` or
  `/usr/local/sbin/init`. **So is `always` strictly required? No** — with `command: /sbin/init`
  the `--systemd` default `true` auto-detects and also works, which was checked by running it.
  `always` is the **robust** choice because it removes the dependence on that detection, and it
  becomes **genuinely required the moment `command:` is not literally an init** (e.g.
  `/usr/lib/systemd/systemd`, or a wrapper). Then you get
  `System has not been booted with systemd as init system (PID 1). Can't operate.` Never write
  `true` (fragile) or `false` (mode off); write `always`.
- **`override_command: true` — required when the image's own `CMD` is not an init.** Without it
  the driver replaces your command with `bash -c "while true; do sleep 10000; done"` and systemd
  is never **PID 1** — the process ID of the first process in a Linux container, the one every
  other process descends from. Your `command:` then silently does nothing. If the image's `CMD`
  *is* already an init, the substitution never takes effect and the key is not required —
  `ubi9/ubi-init` is such an image. Set it anyway, so the file does not depend on the image's
  `CMD`.
- **`privileged: false` is written out on purpose.** You will read online that
  `--privileged` is required for systemd in a container. It is not required and it makes
  things worse — see [`../systemd-in-containers.md`](../systemd-in-containers.md).

**You should see:** no output. `molecule list` shows scenario `default` with the instance and
its image named.

---

## 6. Converge — apply your role

Replace the scaffolded `converge.yml`:

```yaml
---
# molecule/<scenario>/converge.yml
- name: Converge
  hosts: molecule
  gather_facts: false
  tasks:
    - name: Wait for systemd to finish booting
      ansible.builtin.wait_for:
        path: /run/systemd/system
        # REQUIRED (DBG-2). Valid states: absent / drained / present / started / stopped.
        # `directory` was REMOVED from the module and is now a FATAL error:
        #   value of state must be one of: absent, drained, present, started, stopped,
        #   got: directory
        # `present` is the "the path exists" test and preserves the documented intent.
        state: present
        timeout: 30

    - name: Wait for systemd to settle (running or degraded)
      ansible.builtin.command: systemctl is-system-running --wait
      register: sysstate
      retries: 10
      delay: 3
      until: sysstate.stdout in ['running', 'degraded']
      changed_when: false
      failed_when: false   # 'degraded' returns rc 1; do not hard-fail here

    - name: Install the test service under test
      ansible.builtin.copy:
        dest: /etc/systemd/system/molecule-demo.service
        mode: "0644"
        content: |
          [Unit]
          Description=Molecule demo service
          After=network.target

          [Service]
          Type=simple
          ExecStart=/bin/sh -c 'while true; do sleep 5; done'
          Restart=on-failure

          [Install]
          WantedBy=multi-user.target

    - name: Reload systemd so it sees the new unit
      ansible.builtin.systemd:
        daemon_reload: true

    - name: Start and enable the test service
      ansible.builtin.systemd:
        name: molecule-demo.service
        state: started
        enabled: true
```

**You should see:** `molecule converge` creates the container and reports `changed` on the
tasks that install the unit, then `ok` on the settle check.

**What changed and why:** the two wait tasks come first. `/run/systemd/system` appearing
proves systemd finished its own early boot. Then `systemctl is-system-running --wait` returns
a **non-zero exit code for `degraded`**, so `failed_when: false` plus the `until` list makes
this *wait* rather than *fail* — `degraded` is the normal, correct outcome for a rootless
container, and waiting for `running` alone would time out on a good system. The last three
tasks write a unit file, tell systemd to re-read its configuration, and start the unit.

**To test your own role instead of the demo service**, replace the last three tasks with:

```yaml
    - name: Apply the role under test
      ansible.builtin.include_role:
        name: my_role
```

`ansible.builtin.include_role` runs `tasks/main.yml` inside the scenario.

---

## 7. Verify — assert the result

Replace the scaffolded `verify.yml`:

```yaml
---
# molecule/<scenario>/verify.yml
# Proves: (1) systemd is PID 1, (2) the test service is active.
- name: Verify systemd and the test service
  hosts: molecule
  gather_facts: false
  tasks:
    - name: Read what PID 1 is
      ansible.builtin.command: cat /proc/1/comm
      register: pid1
      changed_when: false

    - name: Confirm systemd is the top process
      ansible.builtin.assert:
        that:
          - pid1.stdout | trim == 'systemd' or pid1.stdout | trim == 'init'
        fail_msg: >-
          PID 1 is '{{ pid1.stdout | trim }}', not systemd.
          Check that `command: /sbin/init`, `override_command: true` and
          `systemd: always` are all set in molecule.yml.
        success_msg: systemd is PID 1.

    - name: Read the container UUID that Podman sets in systemd mode
      ansible.builtin.command: cat /proc/1/environ
      register: pid1_environ
      changed_when: false
      failed_when: false

    - name: Collect the instance's service facts
      ansible.builtin.service_facts:

    - name: Confirm systemd is running the managed service
      ansible.builtin.assert:
        that:
          - "'molecule-demo.service' in ansible_facts.services"
          - "ansible_facts.services['molecule-demo.service'].state == 'running'"
        fail_msg: molecule-demo.service is not running inside the container.
        success_msg: molecule-demo.service is active.

    - name: Show the systemd state and any failed units (diagnostic, non-fatal)
      # REQUIRED (DBG-4). This must be `shell`, not `command`. `ansible.builtin.command` does
      # NOT invoke a shell, so a `;`-joined compound is passed as a single argv[0], the exec
      # fails, and `failed_when: false` swallows it silently -- leaving `sd.stdout_lines: []`.
      # `shell` is the module that can honour `;` and `||`.
      ansible.builtin.shell: "systemctl is-system-running; systemctl --failed --no-pager || true"
      register: sd
      changed_when: false
      failed_when: false

    - name: Print the diagnostics
      ansible.builtin.debug:
        var: sd.stdout_lines
```

**You should see** on a healthy run:

```console
TASK [Confirm systemd is the top process] *****************************************
ok: [instance] => {
    "changed": false,
    "msg": "systemd is PID 1."
}

TASK [Confirm systemd is running the managed service] *******************************
ok: [instance] => {
    "changed": false,
    "msg": "molecule-demo.service is active."
}
```

Those two `msg` lines are your `success_msg` values — how you know the assertions ran rather
than being skipped.

**What changed and why:** two assertions and one deliberate non-assertion.
`ansible.builtin.service_facts` asks systemd what it is actually running, and the assertion
checks **your** unit. It does **not** check that `systemctl is-system-running` says `running`,
because a correct rootless container reports `degraded` — asserting `running` fails a working
system. The last two tasks only *print* the state; they cannot fail the test.

> **`degraded` is not a failure.** A rootless container usually also shows unrelated units in
> `systemctl --failed` — `dbus-broker.service`, `systemd-resolved.service`,
> `systemd-homed.service`. Those are rootless-container artefacts, not problems with your test.

### 6b. Add `cleanup.yml`

`molecule init` scaffolds five files and this is not one of them, but the `test_sequence` in step
5 calls the `cleanup` step. Create `molecule/default/cleanup.yml`:

```yaml
---
# molecule/<scenario>/cleanup.yml
- name: Cleanup
  hosts: localhost
  connection: local
  gather_facts: false
  # no_log: "{{ molecule_no_log }}"
  tasks:
    # Developer must implement. Usually: remove files/directories created during the run.

    - name: Remove the instance config file
      ansible.builtin.file:
        path: "{{ molecule_instance_config }}"
        state: absent
```

**Why it matters:** without it every run prints
`WARNING [default > cleanup] Executed: Missing playbook (Remove from test_sequence to suppress)`
and the recap reads `missing=1`, which reads like a failure on a first run. The stub is enough.
Note it targets `localhost`, not `molecule` — it runs on your host, after `verify`, before the
final `destroy`. Unlike `create.yml` / `destroy.yml` (which you **delete**), shipping this file
is always safe: there is no driver playbook for it to override.

---

## 8. Run it

```bash
molecule test
```

**You should see** the eight steps announced as `==> Starting \`<name>\`` in order —
`dependency`, `destroy`, `create`, `converge`, `idempotence`, `verify`, `cleanup`, `destroy` —
and a final `Verifier  SUCCESS`. `Verifier SUCCESS` and an **exit code of 0** are the pass.
The exit code is what a CI system reads, so check it with `echo $?` — **you should see** `0`.

> #### Did my test actually run? — exit 0 does not prove it did
>
> **This is the check that separates a real pass from a fake one.** An Ansible play that matches
> no hosts is **not** a failure: it reports `skipping: no hosts matched`, `failed=0`, and
> `molecule test` **exits 0**. So `Verifier SUCCESS` and "the assertions executed" are different
> claims, and the exit code only supports the first.
>
> Measured, not hypothetical: this exact scenario, with the `groups: [molecule]` line missing
> from step 5, produced `skipping: no hosts matched` for **every** play, ran **zero** assertions,
> and still exited `0` — while three separate reviews had approved the configuration, because it
> is syntactically perfect and semantically plausible. Only running it caught the problem.
>
> **Two conditions, both required, on your run:**
>
> 1. **The `PLAY RECAP` shows `ok=N` with `N > 0`.** A healthy run of these five files ends:
>
>    ```console
>    PLAY RECAP *********************************************************************
>    instance                   : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
>    ```
>
>    `ok=0` — or no `PLAY RECAP` line for `instance` at all — means nothing ran.
> 2. **There are zero `skipping: no hosts matched` lines** in the whole output. One appearing
>    anywhere means that play asserted nothing and the run is worthless, whatever the exit code.
>
> Third, free signal: the two `success_msg` values from step 7 — `systemd is PID 1.` and
> `molecule-demo.service is active.` — should appear in the output. Absent means the asserts did
> not execute. And the scenario recap should read `missing=0`; non-zero means the step-6b
> `cleanup.yml` is absent.
>
> **The one line that decides all of it:** `groups: [molecule]` in `molecule.yml`, step 5.

If the run fails, three outputs matter, in this order:

1. `molecule --debug test` — the full log, including the exact `ansible-playbook` invocation.
   Start here.
2. The failing task's `fail_msg` — what the test expected and what it found. It is written
   for you; read it first.
3. `molecule login` — an interactive shell inside the container. It must still exist, so on a
   failing run use `molecule converge` then `molecule login`.

A very common first failure:

```text
fatal: [instance]: FAILED! => {"msg": "molecule-demo.service is not running inside the container."}
```

Two usual causes: the three systemd keys in step 5 are not all set, or the container image has
no **Python** in it — Ansible's built-in tasks run Python on the target machine, so an image
without Python fails on most of them. That is a requirement separate from systemd, and it
applies to every scenario. More in [Troubleshooting](../troubleshooting.md).

---

## Recreate the whole thing from scratch

To start over in a clean folder: three commands, then the five files from steps 1–7. The same
content is a runnable tree in [`../../examples/quickstart/`](../../examples/quickstart/).
Every YAML block on this page is copied **verbatim** from
[`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) — the single source of truth for every code
artifact in this project.

```bash
mkdir -p my_role/tasks
cd my_role
git init
molecule init scenario default
# then write the five files from steps 1-7
molecule test
```

Canonical sources, in order: `tasks/main.yml` from `.research/01` §4.2 (verbatim from
Molecule's guide); `requirements.yml` from `REFERENCE-CONFIG.md` §4; `molecule.yml` from §2b;
`converge.yml` from §3.2; `verify.yml` from §7.2.

No page here re-types a config file.

---

## Next

- **[Project layout](./project-layout.md)** — what every file is for, and which ones Molecule creates for you.
- **[Writing tests](./writing-tests.md)** — a `verify.yml` worth trusting, and an idempotent `converge`.
- **[systemd in containers](../systemd-in-containers.md)** — why `degraded` is correct, and what `systemd: always` sets up.
- **[Troubleshooting](../troubleshooting.md)** — when the run fails, ordered by frequency.

---

## Attribution

No brand marks or logos are displayed on this page. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md); product names identify the
software being discussed and imply no endorsement.

---

## Sources

- <https://docs.ansible.com/projects/molecule/getting-started-roles/> — the setup commands, the `tasks/main.yml` shape, the `include_role` converge, and the run
- <https://github.com/ansible/molecule/blob/main/docs/getting-started-roles.md> — *"The `molecule/` directory and its scenario files are added for testing. They are not part of the role itself."*
- <https://github.com/ansible/molecule/blob/main/src/molecule/command/init/init.py> — `molecule init` registers only the `scenario` subcommand
- <https://github.com/ansible/molecule/blob/main/src/molecule/command/init/scenario.py> — the `scenario` subcommand signature; the `--role-name` in its docstring is stale and is not registered
- <https://github.com/ansible/molecule/blob/main/src/molecule/data/init-scenario.yml> — the scaffolding playbook and the non-empty-folder refusal
- <https://github.com/ansible/molecule/tree/main/src/molecule/data/templates/scenario> — the five scaffold templates, verified by directory listing
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py> — the driver options used above
- <https://docs.ansible.com/projects/ansible/latest/plugins/connection/podman.html> — the `containers.podman.podman` connection plugin, and the requirement that the image contain Python
- <https://docs.podman.io/en/latest/markdown/podman-run.1.html> — `podman run --systemd=always` and what it sets up
- <https://github.com/ansible/molecule/blob/main/docs/usage.md> — `molecule --debug`, `molecule login`, `molecule list`
- Internal, reproducible: every YAML block above is copied verbatim from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §2b, §3.2, §4 and §7.2. No page in this
  project re-types a config file.
