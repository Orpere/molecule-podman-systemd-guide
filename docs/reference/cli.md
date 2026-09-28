# CLI reference — every `molecule` command

> **You are here:** [Docs home](../index.md) → [Usage](../usage.md) → **CLI reference** → [`molecule.yml` reference](./molecule-yml.md)

**What you will be able to do:** look up any real `molecule` command and get its synopsis, its
prerequisites, a worked example and its most common failure — and recognise the commands that
no longer exist before you waste an afternoon on them.

---

## How to use this page

Molecule has two classes of command, and the sections below are in two lists:

- **[Special commands](#special-commands)** — one standalone job each. Not part of a test run.
  `drivers`, `init`, `list`, `login`, `matrix`, `reset`.
- **[Actions](#actions)** — the named steps inside a [test sequence](molecule-yml.md#scenariotest_sequence).
  `check`, `cleanup`, `converge`, `create`, `dependency`, `destroy`, `idempotence`, `prepare`,
  `side-effect`, `syntax`, `test`, `verify`.

That is **eighteen commands in total**, and the list is exhaustive. Every section below has the
same five parts, in the same order, so you can jump straight to the part you need.

| Command | One line | Section |
|---|---|---|
| `molecule check` | Sanity check of the scenario and its parameters. | [`#molecule-check`](#molecule-check) |
| `molecule cleanup` | Runs `cleanup.yml` to remove leftover artefacts. | [`#molecule-cleanup`](#molecule-cleanup) |
| `molecule converge` | Runs `converge.yml` — **applies** your role. | [`#molecule-converge`](#molecule-converge) |
| `molecule create` | Starts the container. | [`#molecule-create`](#molecule-create) |
| `molecule dependency` | Installs what `requirements.yml` lists. | [`#molecule-dependency`](#molecule-dependency) |
| `molecule destroy` | Deletes the container. | [`#molecule-destroy`](#molecule-destroy) |
| `molecule drivers` | Lists the drivers Molecule can see. | [`#molecule-drivers`](#molecule-drivers) |
| `molecule idempotence` | Converge a second time; assert nothing changed. | [`#molecule-idempotence`](#molecule-idempotence) |
| `molecule init scenario` | Creates a new scenario directory and 5 files. | [`#molecule-init-scenario`](#molecule-init-scenario) |
| `molecule list` | One row per scenario. | [`#molecule-list`](#molecule-list) |
| `molecule login` | Interactive shell inside the running container. | [`#molecule-login`](#molecule-login) |
| `molecule matrix` | Prints the ordered action list. | [`#molecule-matrix`](#molecule-matrix) |
| `molecule prepare` | Runs `prepare.yml` — fixtures before converge. | [`#molecule-prepare`](#molecule-prepare) |
| `molecule reset` | Removes every container labelled `owner=molecule`. | [`#molecule-reset`](#molecule-reset) |
| `molecule side-effect` | Runs `side_effect.yml` — a change to be undone. | [`#molecule-side-effect`](#molecule-side-effect) |
| `molecule syntax` | Parses the playbooks without running them. | [`#molecule-syntax`](#molecule-syntax) |
| `molecule test` | Runs the whole test sequence. | [`#molecule-test`](#molecule-test) |
| `molecule verify` | Runs `verify.yml` — **asserts** the outcome. | [`#molecule-verify`](#molecule-verify) |

---

## Special commands

Six commands. Each does one standalone job and is **not** part of a test run:
`drivers`, `init`, `list`, `login`, `matrix`, `reset`.

### `molecule drivers`

**Synopsis**

```bash
molecule drivers
molecule drivers --format plain
```

**Purpose.** Lists every driver Molecule can see, and where each one came from. **This is the
diagnostic to run when a driver is missing** — and `podman` is the one that will be missing,
because the Podman driver does not ship with Molecule. It lives in a separate package,
`molecule-plugins`.

**Prerequisites.** Nothing. It reads installed entry points; it does not need a container, a
network, or even a scenario.

**Worked example.**

```bash
$ molecule drivers
```

**You should see:** a table whose rows include a line whose driver name is exactly `podman`.
With `--format plain` the same list is printed one per line without the table formatting.

**Most common failure.** `podman` is **absent** from the list. Almost always one of two things:

| Symptom | Cause | Fix |
|---|---|---|
| `podman` missing, Molecule and the driver in different environments | `molecule-plugins` was installed somewhere `molecule` cannot see — commonly a distro `molecule` on the `PATH` shadowing a `pipx` one | Install the driver into the *same* environment: `pipx inject molecule molecule-plugins`, then re-run `molecule --version && molecule drivers` |
| `podman` missing entirely | `molecule-plugins` was never installed | Install it: see [install/index.md](../install/index.md) |

> **`molecule drivers` working is not proof your install is healthy.** During this project's
> own research, a `pip install` that reported success produced a `molecule` whose
> `molecule --version` died with `ansible-config: not found` while `molecule drivers` listed
> every driver perfectly. **Run `molecule --version` too.** The two together are the real check;
> see [`molecule --version` in the install index](../install/index.md).

---

### `molecule init scenario`

**Synopsis**

```bash
molecule init scenario <name>
molecule init scenario          # prompts for the name; defaults to "default"
```

**Purpose.** Creates `molecule/<name>/` and writes the scenario template files into it. This
is the **only** subcommand of `molecule init` — `molecule init` registers exactly one.

**Prerequisites.** A `molecule/` directory path the command can create, i.e. you run it from
your project root. No scenario needs to exist.

**Worked example.**

```bash
$ molecule init scenario default
```

**You should see:** the `molecule/default/` directory created, containing **five** files:

| File | What it is |
|---|---|
| `molecule.yml` | The scenario configuration. You edit this. |
| `converge.yml` | Applies the role under test. You edit this. |
| `verify.yml` | Asserts the outcome. You edit this. |
| `create.yml` | A **stub you are meant to delete** under a driver — see below. |
| `destroy.yml` | A **stub you are meant to delete** under a driver — see below. |

> #### ⚠️ Exactly five files, and two of them you must delete
>
> `molecule init scenario` scaffolds **five** files. It does **not** scaffold
> `requirements.yml`, `prepare.yml`, `side_effect.yml`, `cleanup.yml`, an `inventory/`
> directory, a `driver.py`, or a `<scenario>/tests/` directory. The internet frequently claims
> otherwise; none of those are generated.
>
> **`create.yml` and `destroy.yml` must be deleted** once you name a driver. Molecule resolves a
> scenario's own `create.yml` *before* the driver's, so keeping the stub replaces container
> creation with an inert local file-write. The `create` step still reports
> `Executed: Successful`, **no container is ever built**, and `converge` then dies with
> `Command execution failed: Container 'instance' not found`. Under a driver, `molecule.yml`
> *is* the create/destroy configuration.
>
> **Most common failure.** `Refused to expand templates as destination folder '<path>' as it
> already has content in it.` You ran `init` twice into the same folder, or the folder is not
> empty. Molecule refuses on purpose rather than overwrite your work. Start from a new empty
> folder, or remove the old one.

---

### `molecule list`

**Synopsis**

```bash
molecule list
```

**Purpose.** *"List command shows information about current scenarios."* One row per scenario,
showing its name, the actions in its `test_sequence`, and the driver it uses. It is how you
discover the names you pass to `-s`.

**Prerequisites.** At least one scenario directory under `molecule/`.

**Worked example.**

```bash
$ molecule list
```

**You should see:** one row per scenario directory. With a single scenario named `default`,
one row.

**Most common failure.** `CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.` — and
nothing else. **This means there is no `molecule/<scenario>/molecule.yml` anywhere.** A
scenario must be a **directory** under `molecule/`, with the file inside it. A flat
`molecule.yml` at your project root is not a layout Molecule supports, and this one-line
`CRITICAL` is the only explanation you get. The one true path is
`molecule/<scenario>/molecule.yml`.

---

### `molecule login`

**Synopsis**

```bash
molecule login
```

**Purpose.** Opens an interactive shell inside the running container, so you can look at the
result of a converge. With the `podman` driver this is a `podman exec` into the instance. For
other resource types it is SSH, `curl`, `psql`/`mysql`/`mongosh`, or `oc`/`kubectl`/`odo`; it
also supports `ansible adhoc` and `ansible-console`.

**Prerequisites.** **`create` must have run.** The container has to exist.

**Worked example.**

```bash
$ molecule converge
$ molecule login
```

**You should see:** a shell prompt inside the container, typically with the hostname set to
the platform's `name` — `instance` in the canonical scenario.

From inside, the two commands worth knowing:

```bash
systemctl --failed --no-pager    # anything that failed to start
cat /proc/1/comm                # the top process: must be systemd or init
```

**Most common failure.** `molecule login` cannot find a container to enter, because you never
ran `create` — or because a previous `molecule test` ended in `destroy`. The container is
deliberately disposable: nothing you do in a test is meant to outlive it.

---

### `molecule matrix`

**Synopsis**

```bash
molecule matrix
```

**Purpose.** *"Matrix will display the subcommand's ordered list of actions, which can be
changed in scenario configuration."* It answers the question *"what would `molecule test`
actually do here?"* without doing any of it.

**Prerequisites.** Nothing beyond a readable `molecule.yml`.

**Worked example.**

```bash
$ molecule matrix
```

**You should see:** the action names from your `scenario.test_sequence`, one per line, in
order — for the canonical project, `dependency`, `destroy`, `create`, `converge`,
`idempotence`, `verify`, `cleanup`, `destroy`.

**Most common failure.** Very little. If the list is not what you expect, your
[`test_sequence`](molecule-yml.md#scenariotest_sequence) is not what you think it is — this is
the fastest way to find out.

---

### `molecule reset`

**Synopsis**

```bash
molecule reset
```

**Purpose.** Resets scenario state. Under the Podman driver this runs
`podman rm --force --filter=label=owner=molecule` — it removes **every** Molecule container on
the machine, across **all** scenarios.

> **⚠️ Big blast radius, and no confirmation prompt.** `molecule reset` will **not** ask before
> deleting. It takes no scenario name, so it cannot be narrowed from the command line, and it
> reaches **every** Molecule container on the host — including projects you are working on in
> another terminal, and containers holding state you have not committed. There is no undo. **Reach
> for it only when you are deliberately clearing the machine**, and know that
> `molecule destroy -s <name>` (or `molecule destroy` inside a project) is almost always the
> command you actually wanted: same effect for one scenario, and it stops at that scenario's
> boundary. If you only want to reclaim disk from a finished run,
> [`molecule destroy`](#molecule-destroy) is the right tool; `reset` is the blunt one.

**Prerequisites.** Nothing — which is part of the problem above.

**Worked example.**

```bash
$ molecule reset
```

**You should see:** the containers disappear from `podman ps`.

**Most common failure.** A warning, not an error: `Reset called, but <binary> could not be
found on the system. Skipping reset step`. The driver handles a missing Podman binary
deliberately, so this is informational.

> **Read the scope before you run it.** `reset` is not per-scenario. It is the "clear
> everything" button — useful when a crashed run has left containers behind and you want a
> clean machine. If you only want to remove one scenario's container, use
> [`molecule destroy`](#molecule-destroy) with `-s <name>` instead.

---

## Actions

Twelve commands. These are the named steps inside a [test
sequence](molecule-yml.md#scenariotest_sequence). You can run one on its own, or let
`molecule test` run them in order. Sections are alphabetical: `check`, `cleanup`, `converge`,
`create`, `dependency`, `destroy`, `idempotence`, `prepare`, `side-effect`, `syntax`, `test`,
`verify`.

### `molecule check`

**Synopsis**

```bash
molecule check
```

**Purpose.** A sanity check of the scenario. Molecule's own one-line description is a *"syntax /
paramiko sanity check on the scenario"* — the SSH library is only relevant to remote drivers,
and with the Podman driver this is effectively a configuration check. It is the cheapest thing
Molecule can do that still reads your configuration.

**Prerequisites.** Nothing. Run it before you have ever started a container.

**Worked example.**

```bash
$ molecule check
```

**Most common failure.** Very little fails here, which is the point of it. If it does complain
about the scenario, the cause is in `molecule.yml` — check
[`platforms[*].name`](molecule-yml.md#name) and the `driver:` block.

---

### `molecule cleanup`

**Synopsis**

```bash
molecule cleanup
```

**Purpose.** Runs `cleanup.yml`, which removes files and directories your scenario created
outside the container. Under the canonical sequence it runs after `verify` and before the
final `destroy`, and it targets `localhost` — the **host**, not the container.

**Prerequisites.** A `cleanup.yml` in the scenario directory. Molecule does not scaffold one.

**Worked example.** The minimal stub that is enough for a scenario which leaves nothing
behind:

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

**Most common failure.** `WARNING [default > cleanup] Executed: Missing playbook (Remove from
test_sequence to suppress)` on **every** run, and `missing=1` in the scenario recap. The
`cleanup` action exists and the sequence calls it, but the file does not — and
`molecule init` does not create one. It is harmless to the result and very confusing to look
at, so ship the stub above.

> **Do not confuse this with `create.yml` / `destroy.yml`.** Those two **override the driver's
> playbooks and must be deleted**. `cleanup.yml` has no driver equivalent, so shipping it is
> always safe. The asymmetry is deliberate.

---

### `molecule converge`

**Synopsis**

```bash
molecule converge
molecule converge -- -vvv --tags foo,bar
```

**Purpose.** Runs `converge.yml`. **This is the step that applies your role** — the work, as
opposed to the checking.

**Prerequisites.** **`create` must have run.** There has to be a container to converge.

**Worked example.**

```bash
$ molecule converge
```

**You should see:** a `CONVERGE` banner, then your tasks, then a `PLAY RECAP` for the instance.
`changed: [instance]` means the task did something; `ok: [instance]` with `changed: false`
means it did not need to.

**Most common failure.** Two, and they are worth telling apart:

| Message | Cause |
|---|---|
| `Command execution failed: Container 'instance' not found` | **No container exists.** Either you never ran `create`, or a `create.yml` stub is present and shadowed the driver's playbook so no container was ever built. |
| `System has not been booted with systemd as init system (PID 1). Can't operate.` | The container booted something other than its init, so `systemd` is not running. See [`command` and `systemd`](molecule-yml.md#command). |

---

### `molecule create`

**Synopsis**

```bash
molecule create
```

**Purpose.** Creates the container, from the image named in `platforms:`, honouring the
systemd keys. Under a driver this is entirely driven by `molecule.yml`.

**Prerequisites.** Nothing. A `molecule.yml` with a `platforms:` entry is enough.

**Worked example.**

```bash
$ molecule create
```

**You should see:** a `CREATE` banner, then `podman ps` shows one row whose `NAMES` column
contains `instance`, status `Up`.

**Most common failure.** The container exits immediately with **completely empty logs** and
`State.ExitCode=255`. That silence is the signature of **systemd mode never engaging** — without
it `systemd` cannot write its own cgroups, so it dies before it can log anything. Check
[`systemd`](molecule-yml.md#systemd) and [`command`](molecule-yml.md#command) in `molecule.yml`.
The full symptom list is in [troubleshooting](../troubleshooting.md).

---

### `molecule dependency`

**Synopsis**

```bash
molecule dependency
```

**Purpose.** Installs the roles and collections listed in the scenario's `requirements.yml`.
This is what makes the `containers.podman` collection — and therefore the connection plugin —
available.

**Prerequisites.** A `requirements.yml` in the scenario directory, and a `dependency:` block in
`molecule.yml` that points at it:

```yaml
dependency:
  name: galaxy
  options:
    requirements-file: ${MOLECULE_SCENARIO_DIRECTORY}/requirements.yml
```

**Worked example.**

```bash
$ molecule dependency
```

**You should see:** Ansible Galaxy output as it installs, ending with the collection in place.

**Most common failure.** The `dependency` step runs, installs nothing, and the later steps
cannot find `containers.podman.podman`. The `requirements.yml` is missing or the `dependency:`
block is not pointing at it. `molecule init` does **not** scaffold `requirements.yml`, so this
is a gap in every fresh project — see
[the one file Molecule will not create for you](../authoring/your-first-scenario.md#4-add-the-one-file-molecule-will-not-create-for-you).

---

### `molecule destroy`

**Synopsis**

```bash
molecule destroy
```

**Purpose.** Deletes the container. It is the only per-scenario teardown, and it appears **at
both ends** of the canonical test sequence so that a crashed run cannot poison the next one.

**Prerequisites.** Nothing. It is safe to run when no container exists.

**Worked example.**

```bash
$ molecule destroy
```

**You should see:** a `DESTROY` banner, after which `podman ps` shows no rows.

**Most common failure.** You expect it to read a `destroy.yml`, and there is none — and there
should not be. Under the `podman` driver, `molecule.yml` *is* the destroy configuration. A
`destroy.yml` you kept from scaffolding resolves *before* the driver's and replaces teardown
with an inert stub. Delete both `create.yml` and `destroy.yml`; see
[`molecule init scenario`](#molecule-init-scenario).

---

### `molecule idempotence`

**Synopsis**

```bash
molecule idempotence
```

**Purpose.** Runs `converge.yml` a **second** time and fails if anything changed. It is what
catches a task that acts on every run instead of only when it needs to.

**Prerequisites.** **`converge` must have run and succeeded.** Idempotence is a claim about
converge, so it needs a first converge to compare against.

**Worked example.**

```bash
$ molecule converge
$ molecule idempotence
```

**You should see:** the tasks run again with `ok=` and `changed: false`, and the step succeeds.

**Most common failure.** `changed: [instance]` on the second run. Something in `converge.yml`
is not idempotent — the usual culprits are a template task without a `changed_when` guard, a
`command` or `shell` task without one, or a package install that always re-runs. That is the
step working: it found a real problem.

> **Spelling.** The command is `idempotence`, with an *e*. `molecule idempotency` does not
> exist.

---

### `molecule prepare`

**Synopsis**

```bash
molecule prepare
```

**Purpose.** Runs `prepare.yml` — installing fixtures, before converge. The right place for
"the test needs this package, this user, or this file to already exist".

**Prerequisites.** `create` must have run. A `prepare.yml` must exist.

**Worked example.**

```yaml
---
# molecule/<scenario>/prepare.yml
- name: Prepare
  hosts: molecule
  gather_facts: false
  tasks:
    - name: Install a package the role under test expects
      ansible.builtin.package:
        name: bash-completion
        state: present
```

**Most common failure.** `Missing playbook` — because `molecule init` does not scaffold
`prepare.yml`, and the default `test_sequence` includes `prepare` regardless. Either create
the file or remove the step from your `test_sequence`.

---

### `molecule side-effect`

**Synopsis**

```bash
molecule side-effect
```

**Purpose.** Runs `side_effect.yml` — makes a change, for the purpose of **undoing** it in a
second scenario. It is how you test that something can be reverted.

**Prerequisites.** `create` must have run. A `side_effect.yml` must exist.

**Worked example.** Paired with a `reverse` scenario, the pair means: the `default` scenario
creates the resource, the `reverse` scenario removes it and asserts it is gone.

**Most common failure.** `Missing playbook`, for the same reason as `prepare` — the default
`test_sequence` lists `side_effect` and `molecule init` creates no `side_effect.yml`. The
canonical Podman sequence this project uses leaves the step out entirely; do the same unless
you have a real use for it.

---

### `molecule syntax`

**Synopsis**

```bash
molecule syntax
```

**Purpose.** `ansible-playbook --syntax-check` across the scenario's playbooks. It parses and
does not run.

**Prerequisites.** Nothing. No container is created.

**Worked example.**

```bash
$ molecule syntax
```

**You should see:** a short check per playbook, ending successfully.

**Most common failure.** A YAML error with a line number — which is the entire point of running
this first. It turns a five-minute container cycle into a two-second answer. It is the best
value-per-second command in the set when you are editing YAML.

---

### `molecule test`

**Synopsis**

```bash
molecule test
molecule test -s <scenario>
molecule test --parallel
molecule test --all
molecule --debug test
```

**Purpose.** *"Test command will execute the sequence necessary to test the instances."* It runs
the `test_sequence` from your `molecule.yml`, in order, for the scenarios you selected. In the
canonical sequence it ends in `destroy`, so **the container is gone when it finishes**.

**Prerequisites.** Nothing, beyond a valid scenario. It is the command that runs everything
else, including `create`.

**Worked example.**

```bash
$ molecule test
```

**You should see:** eight step banners in order — `DEPENDENCY`, `DESTROY`, `CREATE`, `CONVERGE`,
`IDEMPOTENCE`, `VERIFY`, `CLEANUP`, `DESTROY` — and then the machine is clean.

### Flags

| Flag | What it does |
|---|---|
| `-s <name>` | Target one scenario. Long form `--scenario-name <name>`. |
| `-s <group>/<name>` | Target a nested scenario, `/` as the separator. |
| `-s "<group>/*"` | Target a whole group of nested scenarios. |
| `--all` | Run every scenario, explicitly. |
| `--parallel` / `--no-parallel` | Run the scenarios concurrently, or not. |
| `-- -vvv --tags foo,bar` | Hand the rest of the line to `ansible-playbook`. Molecule does not validate it. |
| `--debug` | Molecule's own verbose mode. **Before** the subcommand. |

**Most common failure — and the one that matters most:**

> #### ⚠️ `molecule test` exits **0** having asserted nothing
>
> A play that matches no hosts is **not a failure**. It reports `skipping: no hosts matched`,
> `failed=0`, and the command **exits 0**. This was measured on this project's own examples
> before they were fixed: every play skipped, zero assertions ran, exit code `0`.
>
> **On the same run, check both:**
>
> 1. **`PLAY RECAP` shows `ok=N` with `N > 0`.** A real run ends like
>    `instance : ok=7 changed=0 unreachable=0 failed=0 skipped=0 rescued=0`. `ok=0` means
>    nothing ran.
> 2. **There are zero `skipping: no hosts matched` lines** anywhere in the output.
>
> The cause is almost always a missing `groups:` key under `platforms[0]` — **Molecule builds
> its Ansible groups from that key, and there is no implicit `molecule` group.** The fix is one
> line; see [`groups`](molecule-yml.md#groups). The full check is in
> [Did my test actually run?](../systemd-in-containers.md#4-and-inside-molecule).

Other common failures:

| Message | Cause |
|---|---|
| `CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.` | No `molecule/<scenario>/molecule.yml`. A flat file at the project root is not a supported layout. |
| `Command execution failed: Container 'instance' not found` | A `create.yml` stub is shadowing the driver's playbook, so no container was built. Delete it. |
| `Module failed: value of state must be one of: absent, drained, present, started, stopped, got: directory` | `state: directory` in a `wait_for` task. That state was removed; use `state: present`. |
| `molecule: command not found`, or a crash with `ansible-config: not found` | An install problem, not a test problem. See [install/index.md](../install/index.md). |

---

### `molecule verify`

**Synopsis**

```bash
molecule verify
```

**Purpose.** Runs `verify.yml`. **This is the step that decides pass or fail.** Everything else
is setup; this is the verdict.

**Prerequisites.** **`converge` must have run.** Verifying without converging asserts the state
of a container you have not touched.

**Worked example.**

```bash
$ molecule converge
$ molecule verify
```

**You should see:** a `VERIFY` banner and your `ok: [instance]` assertions, each printing its
`success_msg`. The canonical playbook prints `systemd is PID 1.` and
`molecule-demo.service is active.`

**Most common failure.** `The marker file is missing. Converge did not run.` — either converge
really did not run, or the image has no Python so Ansible's built-in tasks could not execute.
Those are two different problems with the same message; check the converge output first.

**The deeper failure is the quiet one:** a `verify.yml` whose play targets a group that does not
exist asserts nothing and passes. Check the `ok=` count, not the exit code — the callout under
[`molecule test`](#molecule-test) applies to every step that runs a playbook, including this
one.

---

## The full `test_sequence`

`molecule test` has no hard-coded order. It runs what `molecule.yml` lists. Both canonical
values, and what each step does, are on the [usage page](../usage.md#the-test-sequence), with
`molecule matrix` showing you which one your project has.

---

## Commands that were removed

> ### ⚠️ These do not exist. Most tutorials are wrong about this.
>
> `molecule add`, `molecule remove` and `molecule lint` **have been removed** — not deprecated,
> gone. There is no source file for any of them in Molecule's command package, and no mention of
> them in its current documentation. The internet is full of tutorials that tell you to type
> them.

| Removed | Use instead | Notes |
|---|---|---|
| `molecule add <name>` | `molecule init scenario <name>` | The exact form matters: `molecule init` has **exactly one** subcommand, `scenario`. `molecule init` on its own prompts for the name and defaults it to `default`. |
| `molecule remove <name>` | `rm -r molecule/<name>` | There is no Molecule command. Deleting the directory is the whole procedure. |
| `molecule lint` | `ansible-lint`, standalone | Molecule never wrapped it. Run the linter yourself. |
| `molecule idempotency` | `molecule idempotence` | Not a removal — a spelling trap. The real command ends in *-e*. |

`molecule --help` is the authority on any machine you are standing in front of.

---

## Environment variables

Four Molecule variables affect these commands, and one that tutorials recommend does not exist:

- [`MOLECULE_PODMAN_EXECUTABLE`](env-vars.md#molecule_podman_executable) — which Podman binary
  the driver runs.
- [`MOLECULE_CONTAINERS_BACKEND`](env-vars.md#molecule_containers_backend) — which engine the
  `containers` driver picks.
- [`MOLECULE_SCENARIO_DIRECTORY`](env-vars.md#molecule_scenario_directory) — the scenario's
  own absolute path, which is what the canonical `dependency:` block interpolates.
- [`MOLECULE_DEFAULT_DOCKER_BIN` does not exist](env-vars.md#molecule_default_docker_bin-does-not-exist)
  — zero hits repo-wide on GitHub. Use `MOLECULE_PODMAN_EXECUTABLE`.

---

## Next

- **Every key in `molecule.yml`** — [`reference/molecule-yml.md`](molecule-yml.md), with the
  type, the default and a "get this wrong and…" line for each.
- **Every environment variable** — [`reference/env-vars.md`](env-vars.md).
- **The commands in context** — [`../usage.md`](../usage.md) is the day-to-day page: the
  everyday loop, when to skip a step, and how to drive this from a Makefile.
- **Something broke** — [`../troubleshooting.md`](../troubleshooting.md), ordered by how often
  each failure bites.

---

## Attribution

No brand marks or logos are displayed on this page. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md); product names identify the
software being discussed and imply no endorsement.

---

## Sources

- <https://docs.ansible.com/projects/molecule/> — the command list (six special commands and
  the actions), the per-command descriptions quoted above, the `--` pass-through form, and the
  note that `--debug` is useful when Molecule reports errors
- <https://github.com/ansible/molecule/blob/main/src/molecule/command/__init__.py> — the
  registered commands. **The absence of `add.py`, `remove.py` and `lint.py` in this file is how
  the removals were verified**; there is also a verified directory listing of
  `src/molecule/command/` with no such entries
- <https://github.com/ansible/molecule/blob/main/src/molecule/command/init/init.py> and
  `.../init/scenario.py` — `init` registering exactly one subcommand, and the `scenario-name`
  argument with its `default` behaviour
- <https://github.com/ansible/molecule/blob/main/src/molecule/data/init-scenario.yml> — the
  scaffolding playbook, including the refusal when the destination folder has content, and
  `molecule/default` as the default name
- <https://github.com/ansible/molecule/tree/main/src/molecule/data/templates/scenario> — the
  five scaffold templates, verified individually
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py> —
  `reset()` and its `label=owner=molecule` filter, and its tolerance for a missing binary
- Internal, reproducible: the `cleanup.yml` stub is copied verbatim from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §3.4; the two `test_sequence` values and
  the step table from §9.2; the `dependency:` block from §2a; the non-vacuity check from §2d.
  No page in this project re-types a config file.
