# `molecule.yml` reference — every key the Podman driver reads

> **You are here:** [Docs home](../index.md) → [Usage](../usage.md) → [CLI reference](./cli.md) → **`molecule.yml` reference** → [Environment variables](./env-vars.md)

**What you will be able to do:** look up any key in `molecule.yml` and get its type, its
default, what it does, and — the part that saves you an afternoon — what breaks if you get it
wrong.

---

## How to use this page

One entry per key. Each one has the same four parts:

- **Type** and **Default**, from the driver's JSON schema and its own source.
- **What it does** — one sentence, then the detail.
- **Get this wrong and…** — the actual symptom, so you can match it against what you see.

Two tables run the whole page:

| | |
|---|---|
| **Recommended set** | The keys this project uses. Nothing else is required. |
| **Present but not recommended** | The key exists in the driver's docstring. It works. This site does not use it, and the row says why. |

> #### About "Default"
>
> Molecule's own documentation gives a default for very few of these keys. Where this page says
> **not documented**, that is precise: nothing in the research corpus states a default, so the
> safe move is to **omit the key entirely** rather than guess a value. The keys with a real,
> verified default are called out in their own rows.

---

## The top-level keys

A scenario's configuration is one file, `molecule/<scenario>/molecule.yml`. It has five top-level
sections that matter here, plus two more Molecule supports.

| Key | Required? | What it is for |
|---|---|---|
| [`driver`](#driver) | **Yes.** The only required top-level key. | Which driver creates and destroys your containers. |
| [`platforms`](#platforms) | In practice, yes for a driver-based scenario. | The list of instances: one container per entry. |
| [`provisioner`](#provisioner) | No, but you want it. | The Ansible connection — including where `containers.podman.podman` goes. |
| [`dependency`](#dependency) | No, but every driver scenario needs it. | Points at `requirements.yml` so the collection gets installed. |
| [`scenario`](#scenario) | No; has a default. | The scenario's name and its `test_sequence`. |
| [`ansible`](#ansible) | No. | Pass-through settings for `ansible-playbook` and `ansible.cfg`. |
| [`verifier`](#verifier) | No. | Which verifier runs `verify.yml`. Almost always `ansible`. |

> **`inventory` is not a top-level key in this configuration.** The inventory is configured
> **under [`provisioner.inventory`](#provisioner)** — that is where the
> `ansible_connection: containers.podman.podman` line lives. If a tutorial puts `inventory:` at
> the top level of `molecule.yml`, it is showing you the Ansible-native layout, which has no
> driver block at all. This site teaches the driver layout.

---

## `driver`

Only two keys are read here, and one of them you will never need.

| Key | Type | Default | What it does |
|---|---|---|---|
| `name` | string — **`podman`** or **`containers`**, nothing else | *(required)* | Selects the driver. The schema's `enum` is exactly `["podman", "containers"]`. |
| `safe_files` | list of strings | the scenario's ephemeral `Dockerfile` | Files, relative to the scenario's ephemeral directory, preserved after any `destroy`. |

```yaml
driver:
  name: podman
  # safe_files:            # uncomment only if you have files worth keeping after `destroy`
  #   - foo
```

- **Get `name` wrong and…** `name: default` is a *different driver* — the one built into core
  Molecule, a pure shim that provisions nothing and connects to whatever the inventory says. It
  will not read your `platforms:` and will not create a container. `name: podman` requires
  `molecule-plugins`; if you get *"the `podman` driver is missing"*, run
  [`molecule drivers`](cli.md#molecule-drivers).
- **Get `safe_files` wrong and…** nothing dramatic; you just lose whatever you asked to keep, or
  accumulate a stale file. You do not need this key unless you deliberately want an artefact to
  survive teardown.

### Where the driver comes from

`driver: name: podman` needs the separate **`molecule-plugins`** package. It is not in any
distribution repository — not Fedora's, not Arch's, not Ubuntu's, not Mageia's. It is not part
of `molecule` either. This is the single most common first-run failure, and
[`molecule drivers`](cli.md#molecule-drivers) is how you diagnose it.

---

## `platforms`

The list of instances. **The driver iterates it in `create` and `destroy`, creating one container
per entry**, and then Ansible runs your converge and verify against all of them. Two entries is a
matrix: the same test, two images, one verdict per instance.

`name` is the only key in this list that is required.

### `name`

| | |
|---|---|
| **Type** | string |
| **Default** | *(required — there is none)* |
| **What it does** | The container's name, and the hostname your playbooks see. Your playbooks' `hosts: molecule` does **not** name it; the `groups` key does that. See [`groups`](#groups). |

- **Get this wrong and…** the most confusing case on the whole page: it still works, and your
  playbooks still cannot find it. `name: instance` makes `hosts: instance` match. If your
  playbook says `hosts: molecule`, only the [`groups`](#groups) key makes that true. Set both.
- `hostname` is a separate key and defaults to this one.

### `image`

| | |
|---|---|
| **Type** | string |
| **Default** | *(not documented — set it)* |
| **What it does** | The container image to run. It becomes the `FROM` line when you also set [`pre_build_image: false`](#pre_build_image). |

**The image needs three things, and beginners routinely conflate them:**

1. **systemd installed** — no mainstream base image ships it. Verified absent from
   `debian:bookworm`, `ubuntu:24.04`, `fedora:latest`,
   `quay.io/centos/centos:stream9`, `quay.io/centos/centos:stream10` and `ubi9/ubi-minimal`.
2. **`/sbin/init` present** — see [`command`](#command).
3. **Python installed** — *"the container image **must** have Python installed to be able to run
   many of the builtin tasks."* This has nothing to do with systemd. A bare `alpine` image fails
   on most `ansible.builtin` modules, and so does this scenario with a systemd image missing
   Python.

- **Get this wrong and…** three different failures, one per missing ingredient. No systemd →
  the container exits with `State.ExitCode=255` and **empty logs**. No Python → the first
  `ansible.builtin` task fails with a Python error, or your `verify` reports a file you never
  created.
- **The recommended no-build image** is `registry.access.redhat.com/ubi9/ubi-init:latest`
  (systemd 252) or `ubi10/ubi-init:latest` (systemd 257). Both verified to reach `running`
  under rootless, both free, **no Red Hat subscription needed**. Both are `:latest` shaped, so
  they are a **moving target** — fine for the examples here, and for anything you depend on
  append `@sha256:<digest>`. See [pin your base image](../authoring/custom-images.md#pin-your-base-image).
- **Do not use a CentOS Stream image for a systemd scenario.** Molecule's own systemd guide
  recommends `quay.io/centos/centos:stream10` plus `command: /sbin/init`. **That image has no
  systemd and cannot work.** All 59 active `quay.io/centos/centos` tags were enumerated; none
  contain `init`. This is a documented upstream bug.

### `command`

| | |
|---|---|
| **Type** | string, or a list of strings |
| **Default** | `["bash", "-c", "while true; do sleep 10000; done"]` — a sleep loop that keeps the container alive between steps |
| **What it does** | What runs as **process 1 (PID 1)** inside the container. The first process in a container is the init. |

```yaml
    command: /sbin/init
```

- **Get this wrong and…** `converge` dies with
  `System has not been booted with systemd as init system (PID 1). Can't operate.` `sleep` is
  PID 1, `systemd` never starts, and every `systemctl` call fails.
- **Only useful together with [`override_command`](#override_command)**, or it is silently
  replaced by that default sleep loop.
- This key also decides whether [`systemd`](#systemd) needs the literal `always` — see that row.

### `override_command`

| | |
|---|---|
| **Type** | boolean |
| **Default** | *(not documented — set it)* |
| **What it does** | Stops the driver replacing your [`command`](#command) with `bash -c "while true; do sleep 10000; done"`. That substitution is what keeps a container alive between steps when you have not asked for an init. |

```yaml
    override_command: true
```

> **The precise rule, because it is not unconditionally required.** Earlier revisions of this
> page called it *mandatory* alongside `command:`. That was an over-claim, corrected by
> execution:
>
> - **When the image's own `CMD` is not an init, this key is genuinely required.** Without it
>   the driver substitutes the sleep loop, systemd is never PID 1, and your `command:` **does
>   nothing**. This is the most confusing variant precisely because `command: /sbin/init` is
>   right there in the file, visibly being ignored.
> - **When the image's own `CMD` already is an init, the key is not required** — the substituted
>   sleep loop never takes effect, and the image's own `CMD` boots as PID 1.
>   `registry.access.redhat.com/ubi9/ubi-init:latest` is exactly such an image.
>
> **This site sets it anyway**, so the file does not depend on the image's `CMD`.
>
> *The one documented exception, from the driver's own docstring:* if your `Dockerfile.j2`
> declares a `CMD` you intend to rely on, set `override_command: false` instead. That is the
> mirror image of the rule above, not a contradiction of it.

- **Get this wrong and…** the same PID 1 failure as a bad `command:`, but with a misleading
  file. Check this key *before* you start debugging the image.

### `systemd`

| | |
|---|---|
| **Type** | **string** in the driver's schema, rendered `true\|false\|always` in its docstring. ⚠️ A real typing oddity in the driver, not a typo here. |
| **Default** | *(not documented — set it)* |
| **What it does** | Turns on Podman's systemd mode. This is what tmpfs-mounts `/run`, `/run/lock`, `/tmp` and `/var/lib/journal`, sets the stop signal to `SIGRTMIN+3`, sets `container_uuid`, and — on **cgroup v2** — mounts `/sys/fs/cgroup` **writable**. Without it `systemd` cannot write its own cgroups and dies before it can log. |

```yaml
    systemd: always
```

> **The precise rule, because it is not unconditionally required.** Earlier revisions of this
> page said `always` was required and that setting `command:` forced it. Both claims were
> over-assertions, corrected by execution:
>
> - `podman run --systemd` **defaults to `true`**, and `true` only engages systemd mode when
>   the container command is *literally* `systemd`, `/usr/sbin/init`, `/sbin/init` or
>   `/usr/local/sbin/init`. So with `command: /sbin/init`, the default `true` **also works** —
>   verified by running it, not assumed.
> - `always` is the **robust** choice because it removes the dependence on that auto-detection.
> - It becomes **genuinely required the moment `command:` is not literally an init** —
>   `command: /usr/lib/systemd/systemd`, or a wrapper script. Then auto-detection cannot see an
>   init, systemd mode never engages, and you get
>   `System has not been booted with systemd as init system (PID 1). Can't operate.`
> - **Never write `true` and never write `false`.** `false` disables the mode outright; `true`
>   is the fragile middle. Write `always`.

- **Get this wrong and…** `false` (or a `true` that fails to auto-detect) and the container
  **exits immediately with a completely empty log and `State.ExitCode=255`**. The silence is
  the signature: there is no `systemd` to write the log.

### `privileged`

| | |
|---|---|
| **Type** | boolean |
| **Default** | *(not documented — set it to `false` explicitly)* |
| **What it does** | Runs the container with elevated privileges. |

```yaml
    privileged: false
```

> ### ⚠️ Never set `privileged: true`
>
> **1 · What the upstream driver docstring says — quoted verbatim, not our advice:**
>
> > *"When attempting to utilize a container image with `systemd` as your init system inside the
> > container … make sure to set the `privileged`, `command`, and `environment` values."*
> > — the `molecule-plugins` podman driver docstring. Its own example sets
> > `privileged: true`, `command: "/usr/sbin/init"`, `tty: True`.
>
> **2 · What this project measured — our finding, and it contradicts the quote above:**
>
> Privileged mode unmasks `/sys`, so `sys-kernel-config.mount`, `sys-kernel-debug.mount` and
> `sys-kernel-tracing.mount` **fail**, and the container reaches **`degraded` instead of
> `running`**. `podman-run(1)` also notes: *"Containers running in a user namespace (e.g.,
> rootless containers) cannot have more privileges than the user that launched them."*
>
> So `privileged` is not merely unnecessary — it is **harmful**, and it degrades the exact thing
> you are trying to test. It is listed here as **not recommended** for that reason.
> **The docstring in 1 is a documentation bug in `molecule-plugins` and should be reported
> upstream** — the finding, not the quote, is what this site is asserting.

- **Get this wrong and…** a `degraded` system, a `systemctl --failed` list full of
  `sys-kernel-*` mounts, and a test that appears to pass while the system is in a state no real
  machine would be in.

### `groups`

| | |
|---|---|
| **Type** | list of strings |
| **Default** | `["ungrouped"]` — **verified in Molecule's own source** |
| **What it does** | The Ansible groups your instance belongs to. Molecule derives them from this key and nothing else. |

```yaml
    # ---------------------------------------------------------------------------
    # REQUIRED. Molecule builds its Ansible groups from this key, defaulting
    # to ["ungrouped"] -- so there is NO implicit `molecule` group. Omit this line and
    # `hosts: molecule` in converge.yml/verify.yml matches nothing: every play reports
    # "skipping: no hosts matched" and `molecule test` still EXITS 0. Silent false pass.
    groups:
      - molecule
    # ---------------------------------------------------------------------------
```

> ### ⚠️ This is the most dangerous key on the page, because it fails **green**
>
> In Molecule's provisioner, the groups come from exactly this expression:
> `for group in platform.get("groups", ["ungrouped"]):`
>
> **There is no implicit `molecule` group.** So the near-universal
> `hosts: molecule` in a `converge.yml` or `verify.yml` matches **nothing** unless you set this
> key.
>
> **What that looks like, measured on this project's own examples before they were fixed:**
>
> ```console
> PLAY [Verify systemd and the test service] *************************************
> skipping: no hosts matched
> ...
> SCENARIO RECAP
> default                   : actions=8  successful=6  disabled=0  skipped=0  missing=1  failed=0
> $ echo $?
> 0
> ```
>
> **Every play skipped. Not one assertion ran. The exit code was 0.**
>
> Three independent specialist reviews had approved that configuration, because it is
> syntactically perfect and semantically plausible. **Only executing it caught the defect.**
>
> **It also passes `molecule init`'s own scaffolded `converge.yml`,** because that file uses
> `hosts: all` — which is exactly why nobody notices.
>
> **The fix is one line: `groups: [molecule]`.** Then prove the run was non-vacuous — the
> `PLAY RECAP` must show `ok=N` with `N > 0`, and there must be **zero** `no hosts matched`
> lines. The full check, with real output, is in
> [Did my test actually run?](../systemd-in-containers.md#4-and-inside-molecule).
>
> **The rule this produced, and the one to carry forward:** a claim about Ansible or Molecule
> behaviour is not verified until it has been executed, and **a green `molecule test` is not a
> claim that the test ran.**

- **Get this wrong and…** a passing pipeline that tests nothing, permanently and silently.

### `pre_build_image`

| | |
|---|---|
| **Type** | boolean |
| **Default** | **`true`** — use the image as-is |
| **What it does** | Chooses between *building* an image from a Containerfile and *using* the named image. Only when it is `false` does the driver look at your `Dockerfile.j2` at all. |

```yaml
    # pre_build_image: false          # MANDATORY: the default is `true`, which silently
    #                                 # skips the build. `item.image` above is the FROM line.
```

The image reference the driver computes is exactly `molecule_local/<your image name>`, prefixed
when this is `false` and **not** prefixed when it is `true`. That one expression is the whole
mechanism. Molecule's own rootless guide states the rule: *"The `Dockerfile` templating and
image building processes are only done for scenarios with `pre_build_image = False`, which is
not the default setting in generated `molecule.yml` files."*

> **The default reads backwards, and that is the trap.** The natural assumption is "`false` means
> don't build", so people leave it alone. **Leaving it alone is exactly what stops the build.**

- **Get this wrong and…** you edit `Dockerfile.j2`, rerun, and **nothing changes** — no error, no
  warning. The test runs, it passes, it just tests the *base* image instead of yours. This is
  the number-one cause of "I edited the Dockerfile and nothing happened", and the number-one
  cause of "my test passes before I expected it to".
- **You only need this key at all if you are building a custom image.** The recommended
  prebuilt images need nothing here.

### `dockerfile`

| | |
|---|---|
| **Type** | string |
| **Default** | `Dockerfile.j2` in the scenario directory — if it is not there, the driver falls back to its own built-in template |
| **What it does** | Names the Containerfile template to render. Only read when [`pre_build_image`](#pre_build_image) is `false`. |

- **Get this wrong and…** you get the driver's own generic template instead of yours, and your
  package installs and `COPY` lines silently do not happen. If your file has a different name or
  lives elsewhere, set this key.
- **The `.j2` suffix is required when Molecule renders the file.** The content is a Jinja
  template with `item` bound to your `platforms:` entry. If your file contains no Jinja at all,
  drop the `.j2`.

### The other `platforms` keys, at a glance

These are real. None of them is needed for a systemd scenario, and several are actively
**not recommended** — the driver docstring lists them, and repeating its advice is how projects
inherit its mistakes.

| Key | Type | Default | What it does | Verdict |
|---|---|---|---|---|
| `hostname` | string | the value of `name` | The container's hostname, if you want it different from the name. | Optional |
| `pull` | boolean | *(not documented)* | Whether to pull the image rather than reuse a local one. | Optional |
| `registry` | object → `url`, `credentials` → `username`, `password` | *(none)* | Pull from a private registry. | Optional — see the credential note below |
| `tty` | boolean | *(not documented; the docstring's example sets `True`)* | Allocates a pseudo-terminal. | **Not recommended** — it is part of the docstring's `privileged: true` example, which is [wrong](#privileged) |
| `detach` | boolean | *(not documented)* | Run detached. | Optional |
| `pid_mode` | string | *(not documented; docstring example `host`)* | Share the host PID namespace. | **Not recommended** — it exposes every host process to the container; nothing in a systemd scenario needs it |
| `rootless` | boolean | **`true`** | Run rootless. | **Recommended**, and the default. The driver playbooks set `become: "{{ not (item.rootless \| default(true)) }}"`, so `false` asks for root — which is neither the default nor the path this site documents |
| `capabilities` | array of strings | *(not documented)* | Adds Linux capabilities, e.g. `SYS_ADMIN`. | **Optional, and only when a unit needs it** — see below |
| `volumes` | array | *(not documented)* | Bind mounts, e.g. `/sys/fs/cgroup:/sys/fs/cgroup:ro`. | **Not recommended** — systemd mode already mounts `/sys/fs/cgroup` writable on cgroup v2; a read-only bind over it fights the driver |
| `tmpfs` | array *(schema)* / dict *(the `containers.podman.podman_container` module documents it as a dict)* | *(not documented)* | In-memory mounts. | **Not needed** — systemd mode already tmpfs-mounts `/run`, `/run/lock`, `/tmp` and `/var/lib/journal`. ⚠️ The schema/module disagreement is a real, open inconsistency in the driver |
| `devices` | array | *(not documented)* | Pass host devices through. | **Not recommended** — it grants host device access a test never needs |
| `security_opts` | array | *(not documented; docstring example `seccomp=unconfined`)* | Security options. | **Not recommended** — `seccomp=unconfined` removes a protection for no benefit here |
| `exposed_ports` | array | *(not documented)* | Ports exposed inside the container. | Optional |
| `published_ports` | array | *(not documented)* | Ports published to the host, e.g. `127.0.0.1:2080:80`. | Optional |
| `dns_servers` | array | *(not documented; docstring example `8.8.8.8`)* | DNS servers. | Optional |
| `network` | string | *(not documented; docstring example `host`)* | Container network. A dedicated per-scenario network is created when the name is not one of `bridge`, `none`, `host`, `ns`, `private`, `slirp4netns`. | Optional. **Not `host`** — it is the docstring's example, and it is not what a test wants |
| `etc_hosts` | object (pattern `^.*` → string) | *(not documented)* | Extra `/etc/hosts` entries. | Optional |
| `ulimits` | array | *(not documented; docstring example `nofile=1024:1028`)* | Resource limits. | Optional |
| `cert_path` | string | *(not documented)* | Registry certificate. | Optional — also read from `DOCKER_CERT_PATH` |
| `tls_verify` | boolean | *(not documented)* | Verify the registry's TLS certificate. | Optional — also read from `DOCKER_TLS_VERIFY` |
| `env` | object | *(not documented)* | Environment variables inside the container. | Optional. ⚠️ **This is a `platforms:` key.** `options: { env }` under `driver:` is a different thing and does not exist |
| `restart_policy` | string | *(not documented; docstring example `on-failure`)* | Container restart policy. | **Not needed** — Molecule owns the container's lifetime and destroys it itself |
| `restart_retries` | integer | *(not documented)* | Retries for the restart policy. | **Not needed** — same reason |
| `buildargs` | object | *(not documented)* | Build-time arguments for the Containerfile. | Only with [`pre_build_image: false`](#pre_build_image) |
| `cgroup_manager` | string | *(not documented; docstring example `cgroupfs`)* | `cgroupfs` or `systemd`. | **Not recommended — the premise is inverted.** `cgroupfs` was the cgroup-v1-era workaround. The default, `systemd`, is what you want, because `systemd.io/CONTAINER_INTERFACE` prescribes a `*.scope` unit with `Delegate=yes` |
| `storage_opt` | object | *(not documented; docstring example `overlay.mount_program=/usr/bin/fuse-overlayfs`)* | Storage options. | **Not needed** — a host-level storage tuning decision, not a test one |
| `storage_driver` | string | *(not documented; docstring example `overlay`)* | Storage driver. | **Not needed** — same reason |
| `extra_opts` | array | *(not documented; docstring example `--memory=128m`)* | Raw extra flags appended to the container run. | Last resort. The driver itself derives more flags from the keys above; reach for this only when a flag has no key of its own |
| `ip` | string | *(not documented)* | Static IP for the instance. | **Not recommended** — it is a schema key with no counterpart in the driver's docstring, and nothing in the documented scenario path needs it |

#### Three notes on the not-recommended rows

**`registry.credentials` — never hard-code them.** The driver's own docstring says: *"**Hard-coded
credentials in `molecule.yml` should be avoided**, instead use variable substitution."*

**`capabilities` — add only the one you need, and only if you need one.** A `.service` unit
using `PrivateTmp=`, `ProtectSystem=`, `ProtectHome=`, `PrivateNetwork=`,
`ReadWriteDirectories=` or `InaccessibleDirectories=` needs `SYS_ADMIN`. systemd's own
documentation says **do not** drop `CAP_SYS_ADMIN` or `CAP_MKNOD` broadly; Podman's defaults
include neither, so add only the single one:

```yaml
    capabilities:
      - SYS_ADMIN
```

**Everything in the second half of that table is a docstring example, not a recommendation.**
The `podman` driver's docstring is a list of every key it accepts. Several of its examples —
`privileged: true`, `tty: True`, `pid_mode: host`, `cgroup_manager: cgroupfs`,
`volumes: /sys/fs/cgroup:...`, `security_opts: seccomp=unconfined` — are the *folklore* this
project exists to correct. Their full evidence is on
[systemd in containers](../systemd-in-containers.md#myths-that-will-waste-your-time).

---

## `provisioner`

| Key | Type | Default | What it does |
|---|---|---|---|
| `name` | string — `ansible` | `ansible` | Selects the provisioner. |
| `inventory.host_vars.<hostname>` | object | — | Per-host variables. **This is where the connection plugin goes.** |
| `inventory` | object | — | The inventory structure itself. |
| `options` | object | — | Extra options passed to the provisioner. |

```yaml
provisioner:
  name: ansible
  inventory:
    host_vars:
      instance:
        ansible_connection: containers.podman.podman
```

- **`ansible_connection: containers.podman.podman` is the Fully Qualified Collection Name
  (FQCN) of the connection plugin, and it is the one line that makes the whole thing work.** It
  comes from the **`containers.podman`** collection — **not** `community.docker`, which ships
  only `docker`, `docker_api` and `nsenter` and contains no `podman` connection plugin at all.
- **The key is the host key under `host_vars`**, and it must match the platform's
  [`name`](#name) — `instance` in the canonical file.
- **The connection plugin drives the `podman` command-line tool, not a socket.** There is no
  `DOCKER_HOST` in this path.
- **Get it wrong and…** every playbook task fails to connect, and the message names a missing
  collection (`containers.podman`) rather than a typo — which is the more likely truth.
- **You can omit this block.** The driver auto-injects `ansible_connection: podman` and
  `ansible_podman_executable: podman` for you. This site writes it explicitly because the
  FQCN form is unambiguous, and a reader should be able to see which plugin is in play.

---

## `dependency`

| Key | Type | Default | What it does |
|---|---|---|---|
| `name` | string — `galaxy` | `galaxy` | Installs from Ansible Galaxy. |
| `options.requirements-file` | string | *(none)* | Path to the requirements file. |
| `options.role-file` | string | `requirements.yml` | Alias, present in the generated template. |
| `options.ignore-certs` | boolean | `false` | Present in the generated template. |
| `options.ignore-errors` | boolean | `false` | Present in the generated template. |

```yaml
dependency:
  name: galaxy
  options:
    requirements-file: ${MOLECULE_SCENARIO_DIRECTORY}/requirements.yml
```

- **`${MOLECULE_SCENARIO_DIRECTORY}` is the scenario's own absolute path**, set by Molecule
  before each step. It is what lets the same `molecule.yml` work wherever you moved the
  project. See [`MOLECULE_SCENARIO_DIRECTORY`](env-vars.md#molecule_scenario_directory).
- **Get it wrong and…** the `dependency` step runs, installs nothing, and the later steps
  cannot find `containers.podman.podman`. Because `requirements.yml` is **not** scaffolded by
  `molecule init`, this block points at a file you have to create yourself.
- **This block is why `molecule dependency` does anything at all.** Without it, the step has
  nothing to act on.

---

## `scenario`

| Key | Type | Default | What it does |
|---|---|---|---|
| `name` | string | the directory name | The scenario's name. Also the value `-s` matches. |
| `test_sequence` | list of strings | the sequence [`molecule init` scaffolds](cli.md#molecule-init-scenario) | The ordered actions `molecule test` runs. |

### `scenario.test_sequence`

There is no hard-coded order. `molecule test` runs exactly this list, and `molecule matrix`
prints it.

**The default that `molecule init scenario` scaffolds** — longer, because it includes steps a
beginner has not written yet:

```yaml
    test_sequence:
      - dependency
      - cleanup
      - destroy
      - syntax
      - create
      - prepare
      - converge
      - idempotence
      - side_effect
      - verify
      - cleanup
      - destroy
```

**The official Podman sequence** — what this project uses, shorter, and matched to a
driver-based configuration:

```yaml
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

| Step | What it does | Beginner note |
|---|---|---|
| `dependency` | Installs roles and collections from `requirements.yml`. | Runs first so everything after it has what it needs. |
| `cleanup` | Removes artefacts from a previous run. | Appears at the start *and* the end. **Needs `cleanup.yml` to exist** or Molecule prints `Missing playbook` on every run and the recap reads `missing=1`. |
| `destroy` | Deletes the containers. | Both ends, so a crashed run cannot poison the next one. |
| `syntax` | Checks the playbooks parse. Does not run them. | Catches a typo in seconds. |
| `create` | Creates the containers. | Under a driver, `molecule.yml` **is** the create configuration. |
| `prepare` | Installs fixtures before converge. | Not scaffolded; you write it. |
| `converge` | **Applies** your role. | The step that does the work. |
| `idempotence` | Converge a second time; assert nothing changed. | Catches tasks that act on every run. |
| `side_effect` | Makes a change, to be undone in a second scenario. | Not scaffolded. |
| `verify` | **Asserts** the outcome. | The step that decides pass or fail. |

- **Get this wrong and…** naming a step whose playbook you have not written gives
  `Missing playbook` on every run. Removing a step you did not want removes the guarantee with
  it — dropping `idempotence` drops the only check that your tasks are re-runnable.
- **`cleanup` is the asymmetry worth knowing:** `cleanup.yml` has **no** driver playbook, so
  shipping one is always safe. `create.yml` and `destroy.yml` **do** have one, and shipping your
  own shadows it.

---

## `ansible`

Optional. This is how you set things for `ansible-playbook` that you do not want to type every
time.

| Key | Type | Default | What it does |
|---|---|---|---|
| `cfg.defaults.deprecation_warnings` | boolean | Ansible's own | `ansible.cfg` → `[defaults]` → `deprecation_warnings`. |
| `cfg.defaults.roles_path` | string | Ansible's own | Where to look for roles. The documented example is `${MOLECULE_PROJECT_DIRECTORY}/../` — the directory above your project, so a role can include itself. |
| `cfg.defaults.host_key_checking` | boolean | `false` in the generated template | `ansible.cfg` → `[defaults]`. |
| `cfg.defaults.verbosity` | integer | `1` in the generated template | `ansible.cfg` → `[defaults]`. |
| `cfg.ssh_connection.pipelining` | boolean | `true` in the generated template | `ansible.cfg` → `[ssh_connection]`. |
| `env` | object | — | Environment variables exported to the playbooks. The generated template sets `ANSIBLE_FORCE_COLOR` and `ANSIBLE_LOAD_CALLBACK_PLUGINS`. |
| `executor.backend` | string | `ansible-playbook` | The executable. `ansible_navigator` is also shipped. |
| `executor.args.ansible_playbook` | list of strings | `--diff`, `--force-handlers`, `--inventory=…` | Arguments appended to every `ansible-playbook` call. |
| `playbooks.<action>` | string | `create.yml`, `converge.yml`, `destroy.yml`, `cleanup.yml`, `prepare.yml`, `side_effect.yml`, `verify.yml` | The playbook filename for each action. |

```yaml
ansible:
  executor:
    args:
      ansible_playbook:
        - --diff
        - --inventory=inventory/
```

- **`executor.args` is the persistent version of `--`.** The `--` form
  (`molecule converge -- -vvv --tags foo,bar`) hands the rest of one command line to
  `ansible-playbook`; this key does the same for every step. Molecule's documentation is
  explicit that input after `--` is neither sanitised nor validated, and that it **overrides**
  what this section set.
- **Get it wrong and…** a duplicated flag. `--inventory` here *and* in `host_vars` can produce
  an inventory error that looks like a Molecule problem.

---

## `verifier`

| Key | Type | Default | What it does |
|---|---|---|---|
| `name` | string | `ansible` | Which verifier runs `verify.yml`. |

In practice this is always `ansible`, and the canonical files omit it. It appears in the
Podman driver's own test fixture. Set it only if you are deliberately using a different
verifier, and note that a non-`ansible` verifier changes what `verify.yml` may contain.

---

## Options that are **not** real

Three things appear in forum posts and generated examples that the `podman` driver does not
read. All of them are under `driver:`, which is where they are most confusing.

| You will see | Verdict | Use instead |
|---|---|---|
| `driver: { options: { provided_modules } }` | ❌ **Does not exist.** Zero occurrences in current driver code. | Nothing. It is a fossil of a much older driver generation, or of the retired `molecule-docker` package. |
| `driver: { options: { env } }` | ❌ **Does not exist as a driver option.** | `platforms[*].env` — the *container's* environment variables, a different thing entirely. |
| `driver: { options: { ansible_connection_options } }` | ❌ **Not a podman-driver option.** | Read only by the **`default`** driver, and only when it is unmanaged. The podman driver hardcodes its own. |

The two that *are* real are [`safe_files`](#driver) and `login_cmd_template` — and the login
template is not something you set by hand, because [`molecule login`](cli.md#molecule-login)
already has a working one.

---

## A complete annotated `molecule.yml`

**This is the canonical systemd file**, copied verbatim from
[`REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §2b — the single source of truth for every
config in this project. The uncommented keys are the **recommended set**; every other real key
is shown, commented, with the reason next to it. **Keep the comments.** They are the reason a
future author does not "tidy" a critical key away.

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
    # REQUIRED. Molecule builds its Ansible groups from this key, defaulting
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

### The five files that belong with it

Under the `podman` driver the complete set is exactly this. Note what is **not** in it.

| File | Source | Ship it? |
|---|---|---|
| `molecule.yml` | the block above | ✅ |
| `requirements.yml` | [`REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §4 | ✅ — `molecule init` does not create it |
| `converge.yml` | [§3.2](../REFERENCE-CONFIG.md) | ✅ |
| `verify.yml` | [§7](../REFERENCE-CONFIG.md) — the crux playbook | ✅ |
| `cleanup.yml` | [§3.4](../REFERENCE-CONFIG.md) | ✅ — `molecule init` does not create it, and the sequence above calls `cleanup` |
| `create.yml` | scaffolded by `molecule init` | ❌ **Delete it.** It resolves *before* the driver's playbook, so the `create` step runs an inert local stub, **no container is ever built**, and `converge` dies with `Container 'instance' not found`. The step still reports `Executed: Successful`. |
| `destroy.yml` | scaffolded by `molecule init` | ❌ **Delete it**, for the mirror-image reason. |
| `prepare.yml`, `side_effect.yml` | not scaffolded | Only if your `test_sequence` calls them. |
| `inventory/`, `driver.py`, `<scenario>/tests/` | not scaffolded, not in current documentation | ❌ No. |

**Under a driver, `molecule.yml` *is* the create and destroy configuration.** Ship a
`create.yml` only if you deliberately want to own the entire container lifecycle — and then you
own all of it, including shipping `tasks/create-fail.yml`.

**The directory layout is not a preference either.** The one true path is
`molecule/<scenario>/molecule.yml`. A flat `molecule.yml` at the project root cannot load, and
says so only as `CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.`

---

## Next

- **A command, not a key** — [`cli.md`](./cli.md) covers every `molecule` command, including
  the three that no longer exist.
- **A variable** — [`env-vars.md`](./env-vars.md), including the one tutorials recommend and
  that does not exist.
- **What each key does to the container** — [`../systemd-in-containers.md`](../systemd-in-containers.md)
  is the crux page: what `--systemd=always` sets up, and the folklore table with evidence for
  every "not recommended" row above.
- **Build your own image** — [`../authoring/custom-images.md`](../authoring/custom-images.md) has
  the verified Debian Containerfile and the Fedora and Ubuntu ones, marked as inferred.
- **Where files go** — [`../authoring/project-layout.md`](../authoring/project-layout.md) covers
  every file Molecule understands, and the one that breaks the others.

---

## Attribution

No brand marks or logos are displayed on this page. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md); product names identify the software
being discussed and imply no endorsement.

---

## Sources

- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py>
  — the driver. Its class docstring is the authoritative list of `platforms` options (the source
  of the "not recommended" table), the `privileged: true` advice, the `override_command: False`
  exception for a `Dockerfile.j2` `CMD`, and the registry-credentials guidance
- `src/molecule_plugins/podman/schema/driver.json` — the JSON schema: `driver.name` is an enum of
  `["podman", "containers"]`, `name` is the only required platform key, and the types of every
  key (including `systemd` as `string` and the `tmpfs` array/dict disagreement)
- `src/molecule_plugins/podman/playbooks/create.yml` and `destroy.yml` — the default container
  command, `hostname` defaulting to `name`, the `molecule_local/` image prefix, the
  `rootless | default(true)` expression, and `DOCKER_CERT_PATH` / `DOCKER_TLS_VERIFY`
- <https://github.com/ansible/molecule/blob/main/src/molecule/driver/delegated.py> — the
  `default` driver, confirming `options.ansible_connection_options` belongs to it and not to
  `podman`
- <https://github.com/ansible/molecule/tree/main/src/molecule/data/templates/scenario> — the
  generated `molecule.yml.j2`, the source of the `ansible:` keys and the default
  `test_sequence`
- <https://github.com/ansible/molecule/blob/main/docs/getting-started-roles.md> — the
  `roles_path` example and the `--inventory=inventory/` executor argument
- <https://github.com/ansible/molecule/blob/main/docs/guides/systemd-container.md> — Molecule's
  systemd guide, the source of the CentOS Stream image bug
- <https://molecule.readthedocs.io/> and <https://docs.ansible.com/projects/molecule/> — the
  general usage and configuration documentation
- Internal, reproducible: the canonical `molecule.yml` above is copied verbatim from
  [`REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §2b, which is the single source of truth for
  every config artifact in this project. The `groups:` root cause is verified in Molecule's own
  source at `molecule/provisioner/ansible.py:261` and recorded as
  [`STRUCTURE.md`](../STRUCTURE.md) §8 C-8, with the executed evidence in
  [`../../examples/VERIFICATION.md`](../../examples/VERIFICATION.md). No page in this project re-types
  a config file.
