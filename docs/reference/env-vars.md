# Environment variables

> **You are here:** [Docs home](../index.md) → [Usage](../usage.md) → [CLI reference](./cli.md) → [`molecule.yml` reference](./molecule-yml.md) → **Environment variables**

**What you will be able to do:** look up any environment variable that changes Molecule's
behaviour, set it correctly, unset it again, and recognise the one that tutorials recommend and
that does not exist.

---

## The master table

An **environment variable** is a value set outside a program, in the shell that launches it, and
readable by everything that runs. Molecule reads a handful.

| Variable | Affects | Default | Status |
|---|---|---|---|
| [`MOLECULE_PODMAN_EXECUTABLE`](#molecule_podman_executable) | Which Podman binary the `podman` driver runs | `podman` | ✅ Verified in the driver's source |
| [`MOLECULE_CONTAINERS_BACKEND`](#molecule_containers_backend) | Which engine the `containers` driver picks | `"podman,docker"` | ✅ Verified in the driver's source |
| [`MOLECULE_SCENARIO_DIRECTORY`](#molecule_scenario_directory) | The scenario's own absolute path, interpolated into your config | set by Molecule before each step | ✅ Used by the canonical `dependency:` block |
| [`MOLECULE_PROJECT_DIRECTORY`](#molecule_project_directory) | The project root, for the same reason | set by Molecule | ✅ Used in the official `roles_path` example |
| [`MOLECULE_NO_LOG`](#variables-without-a-verified-default) | Playbook `no_log` (referenced as `molecule_no_log`) | *(none documented)* | ⚠️ Listed in the driver playbooks; no documented default |
| [`MOLECULE_DEFAULT_DOCKER_BIN`](#molecule_default_docker_bin-does-not-exist) | *nothing* | — | ❌ **Does not exist.** 0 code-search hits repo-wide on GitHub |

**A note on what is deliberately absent.** The corpus's environment-variable master table also
lists `DOCKER_HOST`, `DOCKER_CERT_PATH` and `DOCKER_TLS_VERIFY`, and four
`ANSIBLE_PODMAN_*` variables. **None of them is a Molecule variable**, and the first three are
covered below because tutorials tell you to set them. The `ANSIBLE_PODMAN_*` family belongs to
the connection plugin, not to Molecule — see
[Variables that are not Molecule's](#variables-that-are-not-molecules).

---

## `MOLECULE_PODMAN_EXECUTABLE`

| | |
|---|---|
| **Purpose** | Which Podman binary the Podman driver shells out to. |
| **Default** | `podman` |
| **Affects** | The `podman` driver only. |

**Where it comes from.** The driver reads it once, at construction, and the same variable is
honoured inside the driver's own `create.yml` and `destroy.yml` playbooks — so it applies to the
whole lifecycle, not just to a connection.

**When to set it.**

| Situation | Set it to |
|---|---|
| Normal Linux desktop or server | **Don't set it.** The default is right. |
| macOS, talking to a virtual machine with the remote client | `podman-remote` |
| Your distribution names the binary differently, or you have two installed | The full path, e.g. `/usr/local/bin/podman` |

**Worked example** — the remote client, which is the case that actually comes up:

```bash
MOLECULE_PODMAN_EXECUTABLE=podman-remote molecule test
```

To set it for your shell session only, that one-liner is enough. To set it for every Molecule
run in that terminal session:

```bash
export MOLECULE_PODMAN_EXECUTABLE=podman-remote
molecule test
```

**How to unset it.**

```bash
unset MOLECULE_PODMAN_EXECUTABLE
```

Or, for a single command, an empty value falls back to the default:

```bash
MOLECULE_PODMAN_EXECUTABLE= molecule test
```

**When it is set to something wrong, the message names the variable's value.** The driver
resolves the binary against your `PATH` and exits with
`command not found in PATH <value>` — so `command not found in PATH podman-remote` means
"that binary is not installed or not on `PATH`", not "Podman is broken".

> **Do not confuse this with `MOLECULE_DEFAULT_DOCKER_BIN`.** That name appears in tutorials and
> does nothing at all. See
> [below](#molecule_default_docker_bin-does-not-exist).

---

## `MOLECULE_CONTAINERS_BACKEND`

| | |
|---|---|
| **Purpose** | The engine preference order for the **`containers`** driver. |
| **Default** | `"podman,docker"` — Podman first, then Docker |
| **Affects** | The `containers` driver **only**. |

**How it resolves.** The value is split on commas, and the driver takes the **first entry that
is found on your `PATH`**. If neither is found, it falls back to the *first* entry anyway. The
upstream source carries the comment *"Logic for picking backend is subject to change"*, so treat
the default as documented-but-not-guaranteed.

**When to set it.** Only if you use `driver: name: containers` — a different driver from the
`podman` one this project teaches. Three cases:

| Situation | Set it to |
|---|---|
| You use `driver: name: podman` | **Don't set it. It has no effect.** |
| Both Podman and Docker are installed, and you want Docker | `MOLECULE_CONTAINERS_BACKEND=docker` |
| You want to guarantee Podman even if a `docker` binary shadows it | `MOLECULE_CONTAINERS_BACKEND=podman` |

**Worked example:**

```bash
MOLECULE_CONTAINERS_BACKEND=podman molecule drivers
```

**You should see:** the `containers` driver listed, and — with `--debug` — a line reading
`Containers driver will use podman backend`.

**How to unset it.**

```bash
unset MOLECULE_CONTAINERS_BACKEND
```

**When it is set to an engine that does not exist**, the driver raises
`NotImplementedError: Driver <name> is not supported.` It is a strict enum, not a free-text
field.

---

## `MOLECULE_SCENARIO_DIRECTORY`

| | |
|---|---|
| **Purpose** | The absolute path of the scenario's own folder. Molecule sets it before each step. |
| **Default** | Set by Molecule. You do not set it yourself. |
| **Affects** | Every scenario. |

**Why you care.** This is what lets you write a path in `molecule.yml` that keeps working when
you move the project, copy the scenario to another repository, or run it from a subdirectory.
The canonical `dependency` block uses it, and so should yours:

```yaml
dependency:
  name: galaxy
  options:
    requirements-file: ${MOLECULE_SCENARIO_DIRECTORY}/requirements.yml
```

**Worked example.** To see the value for yourself, print it the same way your config does:

```bash
molecule dependency
```

**How to unset it.** **Do not.** Molecule sets it for you on every run, and a hand-set value
would be overwritten anyway. If you find yourself wanting to, the real question is whether you
meant to reference a file in the *project* rather than in the *scenario* — see the next entry.

---

## `MOLECULE_PROJECT_DIRECTORY`

| | |
|---|---|
| **Purpose** | The project root, i.e. the directory above `molecule/`. |
| **Default** | Set by Molecule. |
| **Affects** | Every scenario. |

**The official example that uses it** is an Ansible role including *itself*, which is why a
role's tests reach the role's own tasks:

```yaml
ansible:
  cfg:
    defaults:
      roles_path: ${MOLECULE_PROJECT_DIRECTORY}/../
```

**The trade-off, stated honestly.** You can point every scenario at one shared
`requirements.yml` by using `${MOLECULE_PROJECT_DIRECTORY}` instead. It is not forbidden — but
Molecule installs what that file lists on **every** scenario run, so two scenarios needing
different collection versions are forced to share one. For a per-scenario suite, keeping
`requirements.yml` inside each scenario folder is the honest default: a scenario then carries
everything it needs and can be copied out and run alone. Use the shared form when every
scenario genuinely needs the same thing.

**How to unset it.** **Do not** — same as its companion.

---

## Variables without a verified default

### `MOLECULE_NO_LOG`

| | |
|---|---|
| **Purpose** | Controls the `no_log` value the driver's playbooks pass down (referenced inside them as `molecule_no_log`). |
| **Default** | *(none documented in the corpus)* |
| **Affects** | Playbook logging. |

It is listed in the corpus's master table with the source "driver playbooks", and the driver's
`create.yml` and `destroy.yml` both carry `no_log: "{{ molecule_no_log }}"`. That is where the
value comes from. No default and no documented consumer contract were recorded, so this page
documents what is known and stops: **if you need it, set it and read the output.** It is a
logging switch, so it cannot break a scenario.

---

## `MOLECULE_DEFAULT_DOCKER_BIN` does not exist

> ### ⚠️ It is not a real variable. Stop looking for it.
>
> Tutorials, forum answers and at least one LLM-generated walkthrough recommend
> `MOLECULE_DEFAULT_DOCKER_BIN` to select the Podman binary. **It does not exist.**
> A code search for that string returns **0 results across all of GitHub** — verified through
> two independent routes. There is nothing to set, nothing to configure, and nothing that will
> ever read it.

**Use this instead:**

```bash
MOLECULE_PODMAN_EXECUTABLE=podman molecule test
```

See [`MOLECULE_PODMAN_EXECUTABLE`](#molecule_podman_executable). If you have it in a `.env` file,
a Dockerfile, a CI workflow or a wiki page, **delete it** — it is dead weight that reads as if
it should be doing something.

---

## `DOCKER_HOST` is not how you connect to Podman

You will read that you must point Ansible at the Podman socket:

```bash
export DOCKER_HOST=unix:///run/user/1000/podman/podman.sock
```

**No.** The `containers.podman.podman` connection plugin drives the **`podman` command-line
tool**, not a socket. There is no `DOCKER_HOST` anywhere in its documentation. The connection
is a **CLI-exec seam**, not a socket seam, and this is the single most common documentation
error in the wild.

| Variable | Who reads it | Should you set it? |
|---|---|---|
| `DOCKER_HOST` | The **`docker`** driver, in `molecule-plugins`, which maps it to the Docker CLI's `-H=` flag | **No**, on the Podman path. It does nothing for the `podman` driver. |

The equivalent Podman behaviour is `MOLECULE_PODMAN_EXECUTABLE`, and on macOS the remote client
is what `podman-remote` is for.

---

## The two the driver reads, and the naming oddity

The Podman driver's `create.yml` and `destroy.yml` read two **Docker-named** variables. That is
genuinely odd — they predate the rename of the engine this driver replaced — and it is worth
naming rather than pretending it makes sense.

| Variable | Purpose | Default |
|---|---|---|
| `DOCKER_CERT_PATH` | Registry certificate directory | *(none)* |
| `DOCKER_TLS_VERIFY` | Registry TLS verification | *(none)* |

**You will almost certainly never set either.** Both exist so a scenario can pull from a private
registry with a client certificate. For a public image, do nothing. The equivalent per-platform
keys are [`registry`](molecule-yml.md#the-other-platforms-keys-at-a-glance) — `cert_path` and
`tls_verify` — which are better than environment variables here, because they live in the same
file as the image they apply to.

---

## Variables that are not Molecule's

You will meet these in a log or a connection-plugin error. They belong to the
**`containers.podman` connection plugin**, which is a separate project from Molecule.

| Variable | Purpose | Default |
|---|---|---|
| `ANSIBLE_PODMAN_EXECUTABLE` | The connection plugin's Podman binary | `podman` |
| `ANSIBLE_PODMAN_HOST` | The container name or ID to connect to | the inventory hostname |
| `ANSIBLE_PODMAN_EXTRA_ARGS` | Extra command-line arguments for the plugin | `''` (empty) |
| `ANSIBLE_PODMAN_TIMEOUT` | Operation timeout; `0` means none | `0` |
| `ANSIBLE_PODMAN_MOUNT_DETECTION` | Auto-detect container mount points for file operations | `true` |

**You do not need to set these.** The Molecule driver auto-injects `ansible_connection: podman`
and `ansible_podman_executable: podman`, and the container name comes from your inventory
hostname. They are listed here so that the next time one appears in a log, you know whose it is.

---

## Environment variables do not fix an install problem

> ### ⚠️ The most common failure on this site is a **missing package**, not a missing variable.
>
> ```console
> $ molecule --version
> FileNotFoundError: [Errno 2] No such file or directory: 'ansible-config'
> ```
>
> **No environment variable fixes this, and none should.** Molecule shells out to the
> `ansible-config` program the instant it starts, and **Molecule 26.9 does not declare
> `ansible-core` as a hard dependency.** So a `pip install molecule` that reports success leaves
> a `molecule` binary that cannot run. Two independent causes, and you need to check both:
>
> | Cause | Check | Fix |
> |---|---|---|
> | **`ansible-core` is not installed at all** | `which ansible-config` — no output | Install it, in the **same** environment as `molecule` |
> | It **is** installed, but not on the same `PATH`** | `which ansible-config` finds it, but not next to `molecule` | Put both in one isolated environment — e.g. `pipx install molecule ansible-core` |
>
> **The fix is always the same shape: install `ansible-core` alongside Molecule.** Putting them
> in one `pipx` venv solves both causes at once. The full procedure, per platform, is in
> [install/index.md](../install/index.md).

**And note the diagnostic asymmetry that makes this confusing.** In the same broken
installation, **`molecule drivers` worked perfectly** — it listed every driver — while
`molecule --version` died. The driver list proves `molecule-plugins` is present; it says nothing
about `ansible-core`. **Run both commands when you verify an install.** They test different
things, and passing one is not evidence about the other.

**The general rule for this page:** environment variables change *behaviour*. They never install
software, they never put a missing program on your `PATH`, and they never fix a version
mismatch. If something is not installed, install it.

---

## Next

- **A command** — [`cli.md`](./cli.md), every `molecule` command with its prerequisites and its
  most common failure.
- **A key in `molecule.yml`** — [`molecule-yml.md`](./molecule-yml.md), with a "get this wrong
  and…" line for each.
- **An install that is not right yet** — [`../install/index.md`](../install/index.md), and the
  per-platform pages it links.
- **Something broke** — [`../troubleshooting.md`](../troubleshooting.md).
- **A word you did not know** — [`../glossary.md`](../glossary.md).

---

## Attribution

No brand marks or logos are displayed on this page. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md); product names identify the software
being discussed and imply no endorsement.

---

## Sources

- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py>
  — `MOLECULE_PODMAN_EXECUTABLE`, its default `podman`, the lazy `PATH` resolution and the
  `command not found in PATH` message
- `src/molecule_plugins/podman/playbooks/create.yml` and `destroy.yml` — the same variable read
  inside the lifecycle playbooks, plus `DOCKER_CERT_PATH` and `DOCKER_TLS_VERIFY`
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/containers/driver.py>
  — `MOLECULE_CONTAINERS_BACKEND`, its `"podman,docker"` default, the comma split, the
  `shutil.which()` resolution, the fall-back to the first entry, and the
  `NotImplementedError` for anything else
- `src/molecule_plugins/docker/driver.py` — `DOCKER_HOST` mapped to `ansible_docker_extra_args`,
  which is what makes it a Docker-driver variable and not a Podman one
- <https://docs.ansible.com/projects/ansible/latest/plugins/connection/podman.html> — the
  `ANSIBLE_PODMAN_*` family, which belongs to the connection plugin
- <https://github.com/ansible/molecule/blob/main/docs/configuration.md> —
  `MOLECULE_SCENARIO_DIRECTORY` and `MOLECULE_PROJECT_DIRECTORY`
- <https://docs.ansible.com/projects/molecule/installation/> — *"pip is the only supported
  installation method"*, and the fact that `pipx` is not named in Molecule's own documentation.
  Both positions are stated in [install/index.md](../install/index.md).
- **`MOLECULE_DEFAULT_DOCKER_BIN`:** verified by code search returning **0 results repo-wide**,
  through two independent routes, and recorded as
  [`../STRUCTURE.md`](../STRUCTURE.md) §8 and
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §10.
- **`ansible-config: not found`:** observed live during this project's research — a
  `pip install molecule` that reported success, `molecule drivers` working, and
  `molecule --version` dying. Recorded in [`../../PLAN.md`](../../PLAN.md) §6 Trace T3.
- Internal: the canonical `dependency` block that uses
  `${MOLECULE_SCENARIO_DIRECTORY}` is copied from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §2a and §2b — the single source of truth
  for every config artifact in this project.
