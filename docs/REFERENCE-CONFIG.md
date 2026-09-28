# REFERENCE-CONFIG.md — the canonical code artifacts

> **Owner:** systems-architect (D1 slice). **Status:** DESIGN SPEC + the one true copy of every
> code artifact in this project.
> **Binding rule:** the seven authoring agents **copy from this file, never from memory, never
> from each other, never from the internet**. If a page needs a config that is not here, it is
> added here first and then referenced. There is exactly one `molecule.yml` for each situation
> below and it lives in this file. Seven agents re-typing YAML is how
> `container_systemd: false` reappears in a page where it must be `always`.
>
> Every version number, flag, Fully Qualified Collection Name (FQCN), environment variable and
> package name below is traceable to `.research/`. Items that the corpus marks UNVERIFIED are
> marked UNVERIFIED here too, and the label must survive into the page that quotes them.
>
> **Related:** [`STRUCTURE.md`](STRUCTURE.md) (which page quotes what) ·
> [`VISUAL-SYSTEM.md`](VISUAL-SYSTEM.md) (graphics contract).

---

## 0. The single source of truth table

> **The canonical path is `molecule/<scenario>/molecule.yml` (DBG-7).** A flat `molecule.yml` at
> the project root is not a layout Molecule supports: `molecule list` aborts with
> `CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.` and no explanation. Every path in
> the third column below is therefore `molecule/<scenario>/…`. It is not a convention this site
> prefers — it is the only shape that loads.
>
> **Reading the "Verified?" column.** It is maintained **by execution**, not by review. A `✅`
> means an artifact was run on a live host. DBG-2 is the standing proof that a `✅` can be wrong:
> §3.2 carried one while being fatally broken, and three reviews had passed it. **Nothing gets a
> `✅` here until it has run.** The executed baseline for §2b, §3.2, §3.3, §3.4 and §7 is
> `examples/VERIFICATION.md` — `ok=7`, zero `no hosts matched`.

| § | Artifact | Canonical path in a reader's project | Verified? |
|---|---|---|---|
| 1.1 | Containerfile — Debian / Ubuntu | `molecule/<scenario>/Dockerfile.j2` | ✅ **built and booted** during research |
| 1.2 | Containerfile — Fedora | `molecule/<scenario>/Dockerfile.j2` | ⚠ fact verified, recipe inferred |
| 2a | `molecule.yml` — quickstart (no build, prebuilt init image) | `molecule/<scenario>/molecule.yml` | ✅ executed |
| 2b | `molecule.yml` — systemd in container | `molecule/<scenario>/molecule.yml` | ✅ **executed** — `ok=7`, systemd PID 1 |
| 2c | `molecule.yml` — multi-scenario (per-scenario config) | `molecule/<name>/molecule.yml` | ✅ |
| 2d | **Non-vacuity check — "did my test actually run?"** | n/a (prose) | ✅ **executed** — a missing `groups:` was measured to exit 0 |
| 3.1 | `converge.yml` — quickstart | `molecule/<scenario>/converge.yml` | ✅ |
| 3.2 | `converge.yml` — systemd (with boot wait) | `molecule/<scenario>/converge.yml` | ✅ **executed.** ⚠ **was marked ✅ while fatally broken** (`state: directory`); see DBG-2. |
| 3.3 | `verify.yml` — quickstart | `molecule/<scenario>/verify.yml` | ✅ |
| 3.4 | `cleanup.yml` — minimal stub | `molecule/<scenario>/cleanup.yml` | ✅ executed |
| 4 | `requirements.yml` | `molecule/<scenario>/requirements.yml` | ✅ byte-identical to the upstream test fixture |
| 5 | Install command sets per platform | n/a | ✅ per corpus §7.1/§7.5 |
| 6 | `molecule-preflight.sh` | `docs/scripts/molecule-preflight.sh` | ✅ **executed on this host — output in §6.4** |
| 7 | `verify-systemd` (the crux playbook) | `molecule/<scenario>/verify.yml` | ✅ **executed** — `ok=7`, both `success_msg` values seen |
| 8 | `.github/workflows/molecule.yml` | repo root | ⚠ GitHub Actions specifics are outside the corpus; see §8.1 |
| 9 | `test_sequence` (and the `create.yml` / `destroy.yml` **anti**-guidance) | `molecule/<scenario>/` | ✅ **executed** — shipping `create.yml`/`destroy.yml` was measured to break the driver; see DBG-3 |

---

## 1. The systemd-capable container image

### Why the image is special

Three separate requirements, and beginners routinely conflate them:

1. **systemd must be installed.** No mainstream container base image ships it. Verified absent
   from `debian:bookworm`, `debian:bookworm-slim`, `ubuntu:24.04`, `fedora:latest`,
   `quay.io/fedora/fedora:latest`, `quay.io/centos/centos:stream9`,
   `quay.io/centos/centos:stream10` and `ubi9/ubi-minimal`. `fedora:latest` is
   *"Fedora Linux 44 (Container Image)"*, a minimal variant that deliberately excludes systemd.
   (Every `:latest` above is a moving target — pin `image@sha256:<64-hex-digest>` to make any of
   these findings reproducible.)
2. **`/sbin/init` must exist and must be the command.** Otherwise something else is PID 1 and
   systemd refuses to run.
3. **Python must be installed.** *"When selecting the container image, remember that the container
   image **must** have Python installed to be able to run many of the builtin tasks."* A bare
   `alpine` image fails on most `ansible.builtin` modules. **This has nothing to do with
   systemd** — it is a separate requirement, and it applies to the quickstart image too.

### Why two variants and not one

Fedora uses `dnf`; Debian and Ubuntu use `apt-get`. There is no single recipe that works on both.
The Debian one is the one that was actually built and booted. Both are given because a Fedora
reader and an Ubuntu reader each need their own.

---

### 1.1 `Dockerfile.j2` — Debian bookworm / Ubuntu (✅ VERIFIED: built and booted)

> Use as `molecule/systemd/Dockerfile.j2`. The `.j2` suffix is required when Molecule renders the
> file; the content is a Jinja template with **no** Jinja in it, so it is byte-identical to a
> plain `Dockerfile`. `{% raw %}` guards are only needed if you actually use `{{ item.image }}` —
> see the note under the block.

```dockerfile
FROM {{ item.image }}

ENV container=docker
ENV SYSTEMD_ETC=/usr/lib/systemd
ENV XDG_CONFIG_HOME=/config

RUN rm -f /usr/sbin/policy-rc.d /sbin/init \
 && ln -s /lib/systemd/systemd /sbin/init \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        systemd systemd-sysv dbus python3 sudo procps \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && systemctl set-default multi-user.target

WORKDIR /root
CMD ["/sbin/init"]
```

**Line-by-line, for the page that quotes this (do not put these inside the block):**

| Line | Why it is there |
|---|---|
| `FROM {{ item.image }}` | `item` is the platform entry from `molecule.yml`, so `{{ item.image }}` is the image you named. Verified: `Dockerfile.j2` is rendered from the scenario directory where `item` is the platform config. |
| `ENV container=docker` | **Cosmetic.** systemd auto-detects Podman through `/run/.containerenv`; `container=podman` works equally well. `$container_uuid` is set by Podman automatically. |
| `ENV SYSTEMD_ETC=/usr/lib/systemd` | **Not a systemd requirement.** It appears nowhere in systemd's source or `CONTAINER_INTERFACE`. It is a widespread community Dockerfile convention. Harmless; included for familiarity, and the page says so honestly. |
| `ENV XDG_CONFIG_HOME=/config` | Keeps user config out of the root home directory. |
| `rm -f /usr/sbin/policy-rc.d` | Debian/Ubuntu ship a `policy-rc.d` that is `exit 101` and blocks **all** rc.d service starts. It does *not* block `systemctl start foo.service` for a modern unit, but it breaks sysv-only packages and `dpkg` postinst starts. Verified byte-identical in `debian:bookworm`, `debian:bookworm-slim` and `ubuntu:24.04`. |
| `rm -f /sbin/init` then `ln -s /lib/systemd/systemd /sbin/init` | `systemd-sysv` provides `/sbin/init` on Debian, but the symlink is made explicitly so the recipe works on `-slim` too, where the `init-system-helpers` symlink may be absent. |
| `apt-get install … systemd systemd-sysv` | The whole point of the image. |
| `… dbus` | `multi-user.target` wants `dbus.socket`; without `dbus` that unit fails. |
| `… python3` | Requirement 3 above. Non-negotiable. |
| `… sudo procps` | Convenience for roles: `become`, `ps`, `pgrep`. |
| `DEBIAN_FRONTEND=noninteractive` | Needed on Ubuntu (ships `debconf` pre-seeds that can block on prompts). Harmless on Debian. |
| `systemctl set-default multi-user.target` | Sets the boot target so systemd has something to reach. `systemd-sysv` pulls in `multi-user.target` generation; this pins it. |
| `CMD ["/sbin/init"]` | Makes init the image's default command. Combined with `override_command: true` in `molecule.yml`, Molecule honours the `command:` key. |

**Two Jinja traps, documented here so pages get them right:**

- If the block contains no `{{ }}` at all, Molecule may still render it. To be safe when writing
  a truly plain `Dockerfile` referenced from `platforms[*].dockerfile`, omit the `.j2` name.
- **`ENV container_uuid=$(cat /proc/sys/kernel/random/uuid)` BREAKS THE BUILD.** Verified error:
  `Error: parsing main Dockerfile: Containerfile: Syntax error - can't find = in
  "/proc/sys/kernel/random/uuid". Must be of the form: name=value`. Podman sets `container_uuid`
  at run time anyway, so it is never needed.

---

### 1.2 `Dockerfile.j2` — Fedora (⚠ verified necessary, recipe inferred)

> The **fact** is verified: no Fedora container image ships systemd, so `dnf install systemd` is
> mandatory. The **recipe below was not built in the research session.** The page that quotes it
> must say so. Fedora pages treat it as "reviewed and consistent with the verified Debian recipe,
> not yet booted here" and point at `examples/systemd-unit/` for the live-verified variant.

```dockerfile
FROM {{ item.image }}

ENV container=podman
ENV SYSTEMD_ETC=/usr/lib/systemd

RUN dnf -y install systemd systemd-networkd dbus python3 sudo procps \
 && dnf clean all \
 && rm -rf /var/cache/dnf \
 && ln -sf /usr/lib/systemd/systemd /sbin/init \
 && systemctl set-default multi-user.target

WORKDIR /root
CMD ["/sbin/init"]
```

**Fedora-specific differences from §1.1:**

| Difference | Why |
|---|---|
| No `policy-rc.d` to remove | It is a Debian/Ubuntu invention. |
| `ln -sf` not `rm -f` + `ln -s` | Nothing to remove; `-f` makes it idempotent. |
| `/usr/lib/systemd/systemd` not `/lib/systemd/systemd` | On Fedora `/lib` is a symlink to `/usr/lib`, so `/sbin/init` must point at the `/usr`-prefixed path. |
| `systemd-networkd` | Fedora's systemd package pulls in the network manager that `multi-user.target` wants. |
| `dnf clean all` + `rm -rf /var/cache/dnf` | Keeps the image small. |
| `ENV container=podman` | Cosmetic either way; the corpus verifies Podman's own Dockerfiles use this. |

---

### 1.3 The no-build alternative (recommended default)

If the reader does not need a custom image, they do not need §1.1 or §1.2 at all:

| Image | systemd version | Result under rootless | Note |
|---|---|---|---|
| `registry.access.redhat.com/ubi9/ubi-init:latest` | 252 | **`running`** | ✅ verified; free; no Red Hat subscription needed. Pin `…/ubi9/ubi-init@sha256:<64-hex-digest>` to reproduce |
| `registry.access.redhat.com/ubi10/ubi-init:latest` | 257 | **`running`** | ✅ verified; free; no Red Hat subscription needed. Pin `…/ubi10/ubi-init@sha256:<64-hex-digest>` to reproduce |
| `docker.io/library/archlinux:latest` | 261.3 | `degraded` | Works, but it is a **rolling release** — not reproducible, and a digest pin is the only way to hold it still |

**Do not use:** `M1tch/dind-systemd` and `nickchase/systemd-container` — both are **dead,
HTTP 404**. They were the commonly-cited de-facto references. There is also **no official
systemd-upstream OCI recipe**: the `systemd/systemd-stable@main` tree contains only
`docs/CONTAINER_INTERFACE.md`, `docs/WRITING_VM_AND_CONTAINER_MANAGERS.md`, `network/80-container-*`
and `units/container-getty@.service.in`. The official recipes are `systemd-nspawn` examples, which
are **namespace** containers, not OCI images.

**Do not use a CentOS Stream image for a systemd scenario.** Molecule's own systemd guide
recommends `quay.io/centos/centos:stream10` + `command: /sbin/init`; **that image has no systemd
and cannot work.** All 59 active `quay.io/centos/centos` tags were enumerated and none contain
`init`. This is a documented upstream bug.

**Verify an image by hand before wiring it into Molecule** (faster to debug):

```bash
# Build the image by hand first
podman build -t sd-debian:local -f Dockerfile.j2 .

# Run it with systemd mode
podman run -d --name inst --systemd=always localhost/sd-debian:local

# Check that systemd is the top process
podman exec inst systemctl is-system-running
# expect: running

# Check that nothing failed
podman exec inst systemctl --failed --no-pager
# expect: no output at all
```

---

## 2. `molecule.yml` — the three canonical files

**Every driver option used below is verified.** Where an option exists in the driver's docstring
but is not recommended, `docs/reference/molecule-yml.md` still documents it — but **these three
files are the recommended set and they are the only ones an example project should contain.**

### The four keys that matter for systemd

```yaml
    command: /sbin/init        # what runs as PID 1
    override_command: true     # let Molecule honour `command` instead of substituting a sleep loop
    systemd: always            # turn on Podman's systemd mode
    privileged: false          # never `true` — see STRUCTURE.md §8 C-1
```

These four were re-checked **by execution** on Fedora 44 / podman 5.8.7 / molecule 26.9.0
(`examples/VERIFICATION.md`). Two earlier statements about them were over-asserted and are
corrected here. The canonical recommendation is unchanged; only the *claim about necessity*
changes.

- **`systemd: always` — recommend it, because it is robust. It is not unconditionally
  required, and this file previously claimed it was.** The precise position:
  - `podman run --systemd` **defaults to `true`**, and `true` only engages systemd mode when the
    container command is *literally* `systemd`, `/usr/sbin/init`, `/sbin/init` or
    `/usr/local/sbin/init`. So with `command: /sbin/init` the default **`true` also works** —
    verified, not assumed.
  - `always` removes the dependency on that auto-detection. It is the **robust** choice, and it
    becomes **genuinely required the moment `command:` is not literally one of those four
    paths** (for example `command: /usr/lib/systemd/systemd`, or a wrapper script). Then
    auto-detection cannot see an init, systemd mode never engages, and you get
    `System has not been booted with systemd as init system (PID 1). Can't operate.`
  - **Never write `true` and never write `false`.** `false` disables the mode outright; `true`
    is the fragile middle. Use `always`.
- **`override_command: true` — required exactly when the image's own `CMD` is not an init.**
  - When the image `CMD` is **not** an init, this key is **genuinely required**: without it the
    driver substitutes `["bash","-c","while true; do sleep 10000; done"]`, systemd is never PID 1,
    and your `command:` silently does nothing. This is the most confusing variant precisely
    because `command: /sbin/init` is right there in the file and is being ignored.
  - When the image `CMD` **is** already an init, the key is **not required** — the command
    Molecule would substitute never takes effect, so the init in the image's own `CMD` runs as
    PID 1. `ubi9/ubi-init` is such an image; `registry.access.redhat.com/ubi9/ubi-init:latest`
    boots to systemd with the driver's default command (pin it by digest —
    `…/ubi9/ubi-init@sha256:<64-hex-digest>` — to reproduce that). Setting it anyway is still
    correct and is what this site does, because it makes the file independent of the image's `CMD`.
  - (If your `Dockerfile.j2` declares a `CMD` directive you intend to rely on, the driver's own
    docstring says to set `override_command: False` instead — that is the one documented
    exception, and it is the mirror image of the rule above.)
- **Never set `privileged: true`.** See §10 of this file and `STRUCTURE.md` §8 C-1.

---

### 2a. `molecule.yml` — quickstart (no build; runs a prebuilt init image)

> **Why this file is titled the way it is (DBG-5).** This section used to be titled *"quickstart,
> no systemd"* and carried the comment *"No systemd, no custom image"* — while its own body set
> `command: /sbin/init`, `override_command: true` and `systemd: always` on
> `ubi9/ubi-init`, an image that **contains** systemd. It was a systemd scenario wearing a
> non-systemd label. The two candidate fixes were: make it genuinely non-systemd, or retitle
> it honestly.
>
> **Decision: retitle, and keep it systemd-capable.** Reasons, all from executed or already
> recorded evidence, not preference:
>
> 1. The alternative non-init image this section advertised,
>    `ghcr.io/ansible/community-ansible-dev-tools:latest`, **was never pulled and its systemd
>    capability is unverified** (`STRUCTURE.md` §9 item 5; the probe used `:latest` because no
>    digest is known in advance, so a re-probe needs
>    `ghcr.io/ansible/community-ansible-dev-tools@sha256:<64-hex-digest>` to be meaningful).
>    Promoting it to canonical would trade a labelling bug for an unverified claim — a strictly
>    worse defect.
> 2. §3.1's `converge.yml` is titled "no systemd **wait** needed" and §2a is the scenario it
>    belongs to. Keeping one systemd-capable image means the *same* `molecule.yml` works for
>    both the beginner path and §2b, which is the realistic path — the beginner who will later
>    test a role that manages a `.service` unit needs the systemd keys **already in place**.
> 3. §1.3's no-build recommendation (`ubi9/ubi-init`, verified) is the actual beginner path:
>    nothing to build, no subscription, no `Dockerfile.j2`. A non-systemd image would still
>    need Python, and "no systemd" is a property of the image, not of the config.
>
> **The honest statement of what §2a is:** *the smallest working scenario that needs no image
> build.* It happens to boot an init, because the recommended prebuilt image does. §2b is the
> same file with the systemd narrative spelled out and a `.service` unit under test.

```yaml
---
# molecule/<scenario>/molecule.yml
# The smallest scenario that needs NO image build: it runs a prebuilt init image
# (ubi9/ubi-init) that already ships systemd, Python and /sbin/init. Nothing to build,
# nothing to subscribe to. The three keys below therefore ARE the systemd keys -- see
# section 2b, which is this same file with the systemd narrative written out. If you
# genuinely want a non-systemd instance, see the comment on `image` below.

driver:
  name: podman
  # safe_files:            # uncomment only if you have files worth keeping after `destroy`
  #   - foo

platforms:
  - name: instance
    image: registry.access.redhat.com/ubi9/ubi-init:latest
    # REPRODUCIBILITY: `:latest` is a moving target. For anything depended upon,
    # pin the digest instead - same image, unchanging bytes:
    #   image: registry.access.redhat.com/ubi9/ubi-init@sha256:<64-hex-digest>
    # Find it with: podman image inspect --format '{{index .RepoDigests 0}}' \
    #   registry.access.redhat.com/ubi9/ubi-init:latest
    # `ubi9/ubi-init` already contains systemd, Python and /sbin/init, so nothing
    # needs building. See REFERENCE-CONFIG.md section 1.3.
    # For a plain non-systemd image you could use ghcr.io/ansible/community-ansible-dev-tools:latest
    # (it must contain Python) - but it is configured as a NON-init instance, so keep
    # `command:` as the driver's default sleep and do NOT set `systemd:`. NOTE: that image's
    # systemd capability is UNVERIFIED (STRUCTURE.md section 9, item 5) - it was never pulled -
    # which is why it is offered here as an aside and is not the canonical default.
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

**Notes for the quoting page — after the block, never inside it:**

- `ansible_connection: containers.podman.podman` is the **Fully Qualified Collection Name (FQCN)**
  of the connection plugin. It comes from the **`containers.podman`** collection, **not**
  `community.docker` — that collection ships only `docker`, `docker_api` and `nsenter`. There is
  no `podman` connection plugin in `community.docker`.
- The connection plugin drives the **`podman` command-line tool**, not a socket. There is no
  `DOCKER_HOST` anywhere in this path.
- `platforms[*].name` **is** the container name and the inventory hostname. The driver's
  `create.yml` loops over `groups['molecule']` and passes `name: "{{ item }}"`.
- The driver **auto-injects** `ansible_connection: podman` and `ansible_podman_executable: podman`.
  You do not set those. Setting `ansible_connection: containers.podman.podman` in
  `host_vars` is the explicit, unambiguous form and is what this site uses.
- The `dependency` block is what makes `requirements.yml` get installed. `molecule init` does
  **not** scaffold `requirements.yml` — but every driver-based scenario needs one.
- The `test_sequence` above is the **official Podman (Ansible-native) sequence**, verbatim from
  the corpus. The **default scaffolded** sequence is longer — see §9.2.
- **DBG-6 — `cleanup` is in the sequence, so ship `cleanup.yml`.** `molecule init scenario` does
  **not** scaffold `cleanup.yml`, but this sequence calls the `cleanup` step. Without the file
  every run prints
  `WARNING [default > cleanup] Executed: Missing playbook (Remove from test_sequence to suppress)`
  and the recap reads `missing=1`, which looks like something is broken. **This site ships a
  minimal `cleanup.yml`** — §3.4. Ship it too; the stub is enough.
- **DBG-7 — the scenario MUST live in `molecule/<scenario>/molecule.yml`.** A flat
  `molecule.yml` at the project root is not a layout Molecule supports; `molecule list` fails
  with `CRITICAL 'molecule/*/molecule.yml' glob failed.  Exiting.` and gives no hint why. The
  one true path is the one in §0.

---

### 2b. `molecule.yml` — systemd in a container (the crux)

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
    # REPRODUCIBILITY: pin by digest for anything depended upon -
    #   image: registry.access.redhat.com/ubi9/ubi-init@sha256:<64-hex-digest>
    # because `:latest` can change under a scenario and make a run irreproducible.
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

**Two files this block does NOT list, and why (DBG-6, DBG-3):** no `create.yml`, no
`destroy.yml`. Shipping either **overrides the driver's own playbook** and no container is ever
built — §9.1. And no `cleanup.yml` is listed here either, but this `test_sequence` calls the
`cleanup` step, so you must add it from §3.4 or Molecule prints `Missing playbook` every run.
The complete five-file set is: `molecule.yml`, `requirements.yml`, `converge.yml` (§3.2),
`verify.yml` (§7.2), `cleanup.yml` (§3.4).

**What each of the three critical lines actually does**, for the quoting page. The
"required?" column is the **executed** position from §2 above, not the earlier over-claim:

| Setting | What it does | Required? | What breaks without it |
|---|---|---|---|
| `groups: [molecule]` | Puts the instance in an Ansible group named `molecule`, so `hosts: molecule` matches. | **REQUIRED, unconditionally** | Nothing fails. Every play reports `skipping: no hosts matched`, **zero assertions run**, and `molecule test` still **exits 0**. This is the worst failure mode on this page, because it is green. |
| `systemd: always` | Puts Podman into systemd mode. This tmpfs-mounts `/run`, `/run/lock`, `/tmp` and `/var/lib/journal`, sets the stop signal to `SIGRTMIN+3`, sets `container_uuid`, and on **cgroup v2** mounts `/sys/fs/cgroup` **writable**. | **Recommended, and required once `command:` is not literally an init.** With `command: /sbin/init` the `--systemd` default `true` auto-detects and also works — verified. `always` removes the dependence on that detection. | If systemd mode never engages: the container exits immediately with `State.ExitCode=255` and **completely empty logs**, because systemd could not write its cgroups. |
| `command: /sbin/init` | Makes the image's init system the top process. | **REQUIRED** | `sleep` is PID 1, systemd never starts, converge fails with `System has not been booted with systemd as init system (PID 1).` |
| `override_command: true` | Stops Molecule replacing your command with `bash -c "while true; do sleep 10000; done"`. | **Required when the image's own `CMD` is not an init.** Not required when it already is one (as with `ubi9/ubi-init`). | With a non-init `CMD`: the same PID 1 failure as above, but your `command:` never takes effect — the most confusing variant, because the line is right there in the file and is being ignored. |
| `privileged: false` | Explicitly denies privileged mode. | Keep it explicit | `privileged: true` unmounts protections under `/sys`, three kernel mounts fail, and the container lands in `degraded` instead of `running`. See §10 and `STRUCTURE.md` §8 C-1. |

**The Ansible-native alternative** (documented as an explicit box on the systemd page, because
the corpus calls it *"the single biggest finding"* — upstream's documented happy path uses no
Molecule container driver at all):

```yaml
# inventory/hosts.yml
# NOTE: do NOT also ship a group_vars/molecule.yml with `container_systemd: false`.
# group_vars outranks an inline group `vars:`, so your `always` is silently ignored.
# This trap is present in Molecule's own shipped Podman example.
all:
  children:
    molecule:
      hosts:
        instance:
          container_image: registry.access.redhat.com/ubi9/ubi-init:latest
          # REPRODUCIBILITY: pin by digest for anything depended upon -
          #   container_image: registry.access.redhat.com/ubi9/ubi-init@sha256:<64-hex-digest>
          # Same image, unchanging bytes; `:latest` can move under you.
      vars:
        ansible_connection: containers.podman.podman
        container_command: /sbin/init
        container_systemd: always
```

with Molecule's own `create.yml` unchanged — and only because that route has **no** driver
playbook for it to override (DBG-3).

---

### 2c. `molecule.yml` — a multi-scenario project

Multi-scenario does **not** mean a different `molecule.yml` shape. It means **one
`molecule/<name>/` directory per scenario**, each with its own `molecule.yml`. The project-level
files are shared. There is no project-root `molecule.yml`.

```text
my_role/
├── tasks/
│   └── main.yml
├── Dockerfile.j2                     -> only if scenarios share a custom image
└── molecule/
    ├── default/                      -> the happy path
    │   ├── molecule.yml              (copy of section 2b, scenario name "default")
    │   ├── requirements.yml          (copy of section 4)
    │   ├── converge.yml              (copy of section 3.2)
    │   ├── verify.yml                (copy of section 7)
    │   └── cleanup.yml               (copy of section 3.4 - NOT scaffolded by molecule init)
    └── reverse/                      -> undo the same thing, prove the undo works
        ├── molecule.yml
        ├── requirements.yml
        ├── converge.yml
        ├── verify.yml
        └── cleanup.yml
```

> **`create.yml` and `destroy.yml` are absent from this tree on purpose.** Under the `podman`
> driver, shipping either one **overrides the driver's own playbook** — see §9.1 (DBG-3). You
> get an inert local stub instead of container creation, and `converge` dies with
> `Container 'instance' not found`. `molecule init scenario` writes both files; the correct
> action under a driver is to **delete them**.

**Two things that are NOT in the generated layout**, because Molecule does not scaffold them and
the internet claims it does:

- `driver.py` — not scaffolded, not in any getting-started documentation.
- `molecule/<scenario>/tests/` — not scaffolded, not in any current documentation.

Run one scenario: `molecule test --scenario-name reverse`. Run all: `molecule test`.
List them: `molecule list`.

**The `group_vars` landmine, verbatim from the corpus:** Molecule's shipped Podman example
contains `group_vars/molecule.yml` with `container_systemd: false`, and **`group_vars` outranks
an inline group `vars:`** — so an inline `container_systemd: always` is **silently ignored**. If
you copy any Molecule example, delete that line. Every example tree in this project therefore has
**no `group_vars/` directory at all**.

---

### 2d. **Did my test actually run?** — the non-vacuity check

**Read this before you believe any `molecule test` result, including a green one.**

> **`molecule test` exiting 0 does not prove your assertions executed.** A play that matches no
> hosts is not a failure — it is reported as `skipping: no hosts matched`, `failed=0`, and the
> command exits **0**. This was measured, not hypothesised: a scenario built without
> `groups: [molecule]` printed
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
> **Every play skipped, not one assertion ran, and the exit code was 0.** The crux playbook of
> this entire site — the file §7 calls *"the single most important file in the project"* —
> verified nothing. Three independent reviews had approved that configuration, because it is
> syntactically perfect and semantically plausible. Only running it caught it.

**The check. Two conditions, both required, on the same run:**

1. **The `PLAY RECAP` must show `ok=N` with `N > 0`.** A working run of §3.2 + §7.2 ends like
   this — real numbers, on a real host, asserting two things:

   ```console
   PLAY RECAP *********************************************************************
   instance                   : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
   ```

   `ok=0` (or no `PLAY RECAP` line at all for your instance) means nothing ran. That is the
   whole test: **`ok=7`, not `ok=0`.**

2. **There must be zero `skipping: no hosts matched` lines** anywhere in the output. If you see
   one, stop — the play that printed it asserted nothing, and the run is worthless no matter
   what the exit code says. The usual cause is a missing `groups:` key (§2a, §2b, DBG-1); the
   others are a typo in the `hosts:` line or a platform whose `name` differs from the inventory
   hostname.

**A third signal worth reading, because it is free:** the two `success_msg` values in §7.2 —
`systemd is PID 1.` and `molecule-demo.service is active.` — should appear in the output. If
they are absent, the asserts did not execute.

**Where the two conditions come from, in one line:** `groups: [molecule]` (DBG-1) is what makes
condition 1 and condition 2 possible at all; without it both fail *silently*.

**Also check the scenario recap for `missing=`**, which must be `0`. A non-zero `missing` is the
`cleanup` step of DBG-6 finding no `cleanup.yml` — harmless to the result, but it means the
canonical set is incomplete.

---

## 3. `converge.yml` and `verify.yml`

### 3.1 `converge.yml` — quickstart (no systemd wait needed)

```yaml
---
# molecule/<scenario>/converge.yml
- name: Converge
  hosts: molecule
  gather_facts: false
  tasks:
    - name: Write a marker file
      ansible.builtin.copy:
        dest: /tmp/molecule-was-here
        content: "hello from molecule\n"
        mode: "0644"

    - name: Read the marker file back
      ansible.builtin.stat:
        path: /tmp/molecule-was-here
      register: marker
```

### 3.2 `converge.yml` — systemd (with the boot wait)

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
        # REQUIRED (DBG-2). The valid states are absent / drained / present / started /
        # stopped. `directory` was REMOVED from the module and is now a FATAL error:
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

**Why the two wait tasks, in order:**

1. `/run/systemd/system` appears once systemd has finished its own early boot. Without this the
   next task can run before systemd is ready and fail with a confusing message.
2. `systemctl is-system-running --wait` returns **non-zero for `degraded` and for `starting`**, so
   `failed_when: false` plus the `until` list is what makes this wait rather than fail. Waiting
   for `running` alone would time out on a correct rootless system — see §7.1.

> **DBG-2 — this section was previously marked "✅ Verified" in §0 and was in fact fatally
> broken.** `state: directory` does not exist in ansible-core ≥ 2.19; the `directory` / `file` /
> `socket` states were removed from `wait_for`, and the string `directory` no longer appears in
> the module at all. The first task of the crux `converge.yml` failed immediately with
> `Module failed: value of state must be one of: absent, drained, present, started, stopped,
> got: directory`. It is now `state: present` and the run is green. **Lesson recorded: a
> verification marker is a claim, and a claim is not evidence — the status column in §0 is
> maintained by execution, not by review.**

### 3.4 `cleanup.yml` — the one file `molecule init` will not make for you

The `test_sequence` in §2a and §2b calls the `cleanup` step, but `molecule init scenario`
scaffolds only `converge.yml`, `create.yml`, `destroy.yml`, `molecule.yml` and `verify.yml`.
**Without this file every run prints `Missing playbook` and the recap reads `missing=1`** — noise
on a beginner's first run that makes the recap look broken (DBG-6). Ship it:

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

That is the whole stub and it is sufficient for both canonical scenarios. Add real cleanup tasks
only when your scenario leaves artefacts behind. Note this playbook targets `localhost`, not
`molecule` — it runs on the host, after `verify`, before the final `destroy`.

> **Do not confuse this with `create.yml` / `destroy.yml`.** Those two **override the driver's
> playbooks and must be deleted** (§9.1, DBG-3). `cleanup.yml` has no driver equivalent, so
> shipping it is always safe.

### 3.3 `verify.yml` — quickstart

```yaml
---
# molecule/<scenario>/verify.yml
- name: Verify
  hosts: molecule
  gather_facts: false
  tasks:
    - name: Read the marker file back
      ansible.builtin.stat:
        path: /tmp/molecule-was-here
      register: marker

    - name: Assert the marker file exists and has the right content
      ansible.builtin.assert:
        that:
          - marker.stat.exists
          - marker.stat.checksum is defined
        fail_msg: The marker file is missing. Converge did not run.
        success_msg: The marker file is there.

    - name: Assert the file content
      ansible.builtin.slurp:
        src: /tmp/molecule-was-here
      register: marker_content

    - name: Check the content
      ansible.builtin.assert:
        that:
          - "'hello from molecule' in (marker_content.content | b64decode)"
        fail_msg: Unexpected content in the marker file.
        success_msg: The content is correct.
```

---

## 4. `requirements.yml`

```yaml
---
# molecule/<scenario>/requirements.yml
collections:
  - name: containers.podman
    version: ">=1.10.0"
```

**This file is byte-identical to Molecule's own integration test fixture** and to the file shown
in the official documentation. It is quoted unmodified on purpose, because that is the block
Molecule's own project uses. Facts:

| Item | Value |
|---|---|
| Collection | `containers.podman` |
| Version floor to document | `>=1.10.0` (official docs' floor) |
| The podman driver's own internal floor | `1.8.1` (`required_collections` in `podman/driver.py`) |
| Latest available on Galaxy | `1.20.2` (2026-05-28) |
| Galaxy metadata | 70 versions, created 2023-05-08, `deprecated: false`, `requires_ansible: ">=2.8"` |

### 4.1 Pin it for reproducibility — an addition, not a change to the block above

`">=1.10.0"` is a range, so two runs six months apart can resolve to two different collection
versions and produce two different results. That is fine for a tutorial and wrong for anything
you depend on, in CI, or want to reproduce. The block above is left as upstream wrote it; this
is the pinned form, and it is the one to use in a repository anyone else depends on:

```yaml
---
# molecule/<scenario>/requirements.yml - pinned form
collections:
  - name: containers.podman
    version: "1.20.2"   # exact version: 1.20.2 was the latest on Galaxy on 2026-05-28
```

`ansible-galaxy` accepts an exact version in the `version` field, so nothing else changes — the
same `dependency` step reads the same file and now resolves to one known version. Check yours
before pinning a real project, and re-pin deliberately rather than letting it float:

```bash
ansible-galaxy collection list containers.podman
```

If you resolve a *whole* dependency tree and want that exact resolution recorded, keep the
pinned `requirements.yml` above as the human-maintained input and treat a generated lockfile as
the artefact CI reads. **Whichever you choose, CI must install from the pinned file, not from a
range** — a lockfile nobody reads is a comment, not a lockfile.

**Do not add `community.docker`.** It is not needed for the podman path, and adding it invites
the `community.docker` connection-plugin confusion. `molecule-plugins`'s own `requirements.yml`
lists `ansible.posix` and `community.docker` for the **docker** driver — that is a different
driver.

**Molecule installs this for you** during the `dependency` step of `test_sequence`. The reader
never needs `ansible-galaxy` by hand. If they want it in advance:

```bash
ansible-galaxy collection install containers.podman
```

---

## 5. Install command sets, per platform

**The one sentence every install page must carry, verbatim from the Molecule documentation:**

> "pip is the only supported installation method."

**And immediately after it, honestly:**

> "It is highly recommended that you install molecule in a virtual environment." Molecule's own
> documentation does **not** mention `pipx`. We use `pipx` because `pipx` *is* pip inside a
> per-application virtual environment, so it satisfies both of Molecule's own requirements, it
> is free and MIT-licensed, and it is the officially documented method for Ansible. Molecule
> upstream also now prefers the `ansible-dev-tools` metapackage.

**The raw pip forms (what Molecule's own docs show):**

```bash
# Core
python3 -m pip install --user molecule

# With ansible-lint
python3 -m pip install --user molecule ansible-lint

# With the Podman driver
python3 -m pip install --user "molecule-plugins[podman]"

# From source
python3 -m pip install -U git+https://github.com/ansible/molecule
```

> **The `git+https` form tracks `main`, so it is not recommended for anything depended upon.**
> It resolves the branch, not a release: what you get today is not what you get next week, there
> is no version to record in a lockfile, and an untested commit can break the install with no
> changelog to point at. It is fine for reading the source or for testing an unmerged fix. If you
> genuinely need to build from source, pin a tag and record what you resolved:
>
> ```bash
> python3 -m pip install -U "git+https://github.com/ansible/molecule@v26.9.0"
> ```
>
> For anything CI touches or anyone else installs, use a released version from PyPI instead.

**Official upgrade warning, verbatim:**

> "If you upgrade molecule from previous versions, make sure to remove previously installed
> drivers like for instance `molecule-podman` or `molecule-vagrant` since those are now available
> in the `molecule-plugins` package."

---

### 5.1 `molecule-plugins` is in NO distro repository — anywhere

Not Fedora, not Ubuntu, not Arch, not Homebrew, not Mageia. Even Arch's `molecule 26.9.0-1` does
not depend on it. **Every platform runs one extra command.** Its latest release is `26.9.28`; it
requires `molecule>=25.1.0` and Python `>=3.10`.

---

### 5.2 Fedora 44

```bash
# 1. Container engine, Ansible, pipx, rootless networking
sudo dnf install -y podman ansible-core git pipx passt

# 2. Verify
podman --version
# expect: podman version 5.8.1   (or any 5.x/6.x)

# 3. Put the pipx app directory on PATH
pipx ensurepath
# then close and reopen your shell, or:
source ~/.bashrc

# 4. Molecule, then the Podman driver
pipx install molecule ansible-core molecule-plugins

# 5. Verify
molecule --version
# expect: molecule 26.9.0 using ansible-core 2.20.3 ...
molecule drivers
# expect: a list that includes the line: podman
```

Fedora 44 ships: podman `5.8.1-1.fc44`, ansible-core `2.20.3-1.fc44`, ansible `13.4.0-1.fc44`,
pipx `1.11.0-1.fc44`, passt `0^20260120`, netavark `1.17.2-1.fc44`, aardvark-dns `1.17.0-3.fc44`.
Fedora 45 is Beta and ships podman `6.1.1-1.fc45` — a footnote only.

**Fedora has NO `molecule` package** (its package search returns 12 hits, all chemistry, TeX and
puzzle games). **Fedora has NO `uidmap` package** — `newuidmap` comes from `shadow-utils-subid`,
which is already a hard Podman dependency. **`podman-plugins` does not exist.**

### 5.3 Ubuntu 26.04 LTS and 24.04 LTS

```bash
# 1. Packages
sudo apt install -y podman uidmap passt slirp4netns fuse-overlayfs git pipx ansible-core
# On 24.04, add podman-remote if you prefer the remote client.

# 2. Podman version check - THIS MATTERS ON 24.04
podman --version
# Ubuntu 24.04 -> expect: podman version 4.9.3   <- 2022 vintage, works but stale
# Ubuntu 26.04 -> expect: podman version 5.7.0

# 3. pipx onto PATH
pipx ensurepath
# then close and reopen your shell, or:
source ~/.bashrc

# 4. Molecule, then the Podman driver
pipx install molecule ansible-core molecule-plugins

# 5. Verify
molecule --version
# expect: molecule 26.9.0 using ansible-core 2.16.3 ...   (24.04)  /  2.20.1 ...  (26.04)
molecule drivers
# expect: a list that includes the line: podman
```

**The AppArmor user-namespace problem, and only if `podman run` fails** (24.04 definitely;
26.04 **UNVERIFIED** — inherited from 23.10 and never reverted, but never sampled on 26.04):

```bash
# Prove it. Expect: kernel.apparmor_restrict_unprivileged_userns = 1
sysctl kernel.apparmor_restrict_unprivileged_userns
```

**Fix A — narrow, preferred.** Give Podman its own AppArmor profile that allows making user
namespaces, and leave the global restriction on:

```bash
sudo tee /etc/apparmor.d/podman >/dev/null <<'EOF'
abi <abi/4.0>,
include <tunables/global>

/usr/bin/podman flags=(unconfined) {
  userns,
  include if exists <local/podman>
}
EOF

sudo apparmor_parser -r /etc/apparmor.d/podman
```

Inspect the effective configuration with `systemd-analyze cat-config apparmor.d`.
Ubuntu 24.04 ships AppArmor `4.0.1`. Adjust the binary path if your `podman` is not at
`/usr/bin/podman` — check with `ls /etc/apparmor.d/ | grep -iE 'podman|container|userns'`
(**UNVERIFIED**: whether Canonical ships a ready-made profile for `podman`).

**Fix B — broad, fallback.** Turn the restriction off entirely:

```bash
# now
echo 0 | sudo tee /proc/sys/kernel/apparmor_restrict_unprivileged_userns

# and persist it
echo kernel.apparmor_restrict_unprivileged_userns=0 | \
  sudo tee /etc/sysctl.d/60-apparmor-namespace.conf
```

**Say this plainly:** this is a real security control — 44% of Google's observed Linux
exploits needed unprivileged user namespaces — so prefer Fix A.

**To undo Fix B**, delete the drop-in and put the restriction back:

```bash
sudo rm -f /etc/sysctl.d/60-apparmor-namespace.conf
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=1
```

**Do not use `sudo sysctl --system` to undo or to apply this.** It re-reads *every* sysctl under
`/etc`, so any other drop-in on the machine is re-applied as a side effect; the `sysctl -w`
above is the scoped command.

**Do not confuse the two similarly-named settings.** `kernel.unprivileged_userns_clone` is the
**legacy** all-or-nothing "no user namespaces at all" knob. It is **not** the 24.04 issue.

### 5.4 Arch Linux

Arch is the **only Linux target with a usable native `molecule` package**: `molecule` in the
official **`extra`** repository at `26.9.0-1` (updated 2026-09-25) — *not* the AUR. It is also
the most current platform by a wide margin: podman `6.1.2-1`, ansible-core `2.21.4-1`,
ansible `14.4.0-1`, ansible-lint `26.9.0-1`, pipx `1.15.0-1`, and `crun` is the default
Open Container Initiative (OCI) runtime.

```bash
# 1. Packages. Note: python-pipx, NOT pipx.
sudo pacman -S podman molecule ansible ansible-lint python-pipx git crun passt
# expect: ":: Proceed with installation? [Y/n]"

# 2. Rootless id mapping is already done on Arch - verify only
grep "^$USER:" /etc/subuid /etc/subgid
# expect two lines, e.g.
# $USER:100000:65536
# $USER:100000:65536

# 3. Verify podman
podman --version
# expect: podman version 6.1.2
# You may see, and can safely IGNORE, a crun warning:
#   "Failed to add pause process to systemd sandbox cgroup"
# It is cosmetic. Do not try to fix it.

# 4. The Podman driver, injected into a pipx-managed Molecule.
#    molecule-plugins is in no Arch repository either, so use pipx for it.
pipx ensurepath
source ~/.bashrc

pipx install "molecule-plugins[podman]"
# then run the driver with that venv on PATH:
export PATH="$HOME/.local/pipx/venvs/molecule-plugins/bin:$PATH"
```

**Alternative that keeps Arch's native `molecule` in charge** — install the driver into the
system Python that the `molecule` package uses, which on Arch is the system interpreter:

```bash
# Only if you prefer the pacman molecule on PATH. Verify with:
#   molecule --version && molecule drivers
python3 -m pip install --user --break-system-packages "molecule-plugins[podman]"
```

> Arch is a rolling-release distribution. `--break-system-packages` is shown because Arch's
> system Python is externally managed. If your Arch setup refuses it, use the pipx route above;
> both give a working `molecule drivers` that lists `podman`.

### 5.5 macOS (Apple Silicon only)

```bash
# 0. Read first: Intel Macs are UNSUPPORTED. Podman 6.0 removed Intel Mac support outright,
#    Homebrew moved Intel to Tier 3 in September 2026 with no bottles, and the podman formula
#    is hard-locked with `depends_on arch: :arm64`. There is no supported path.

# 1. Install Podman
#    Recommended: download the .pkg from https://podman.io
#    Alternative (Apple Silicon only, arm64-locked formula):
brew install podman
#    Optional GUI:
brew install --cask podman-desktop
#    Install the helper that forwards the Docker-style API:
sudo "$(brew --prefix)/bin/podman-mac-helper" install

# 2. Create and start the machine
podman machine init
podman machine start
# expect: something ending in
#   API forwarding listening on: /var/folders/.../podman/podman-machine-default-api.sock
#       or  API forwarding listening on: /run/user/501/podman/podman-machine-default-api.sock

# 3. Check the machine
podman machine list
podman machine info --format '{{.Host.Arch}}'
# expect: arm64

# 4. Prove the machine can host systemd. This is a VERIFICATION BLOCK, not an assumption:
#    Podman 6.0 removed cgroups v1, so the VM is certainly cgroup v2, but
#    `--cgroup-manager` is no longer settable from `podman machine init` or `podman machine set`,
#    so we verify rather than assert.
podman machine ssh 'cat /sys/fs/cgroup/cgroup.controllers'
# expect: at least: cpuset cpu io memory pids

podman machine ssh 'stat -fc %T /sys/fs/cgroup/'
# expect: cgroup2fs

podman machine ssh 'systemctl is-system-running'
# expect: running     (or: degraded, which is normal - see section 7.1)

podman machine ssh 'podman info --format "{{.Host.CGroupsVersion}}"'
# expect: v2

# 5. Route A (RECOMMENDED): run Molecule inside the VM.
#    The default machine image is Fedora CoreOS and ALREADY INCLUDES ANSIBLE.
podman machine ssh
#   then, inside the VM:
#   sudo dnf install -y podman pipx        # pipx may already be present; check first
#   pipx ensurepath && source ~/.bashrc
#   pipx install molecule ansible-core molecule-plugins
#   molecule --version && molecule drivers
#   exit

# 6. Route B (alternative): run Molecule on macOS and talk to the VM with the remote client.
export MOLECULE_PODMAN_EXECUTABLE=podman-remote
podman system connection list
molecule test
```

**Also worth knowing on macOS:**

```bash
podman machine init --now                 # create AND start in one step
podman machine init --cpus=6 -m=8192 --disk-size=100
podman machine init --provider libkrun    # the podman 6 default; `applehv` is the other
podman machine init --playbook provision.yml   # run an Ansible playbook on first boot
podman machine init --image docker://quay.io/podman/machine-os:6.1   # pin the VM image
podman machine ssh myvm 'cat /etc/os-release'
podman machine cp ./file myvm:/tmp/file    # move files in and out
```

Default provider is **`libkrun`** (changed in Podman 6; the old `krunkit` value is obsolete and
is the virtualisation framework libkrun uses, not a provider).

**Colima is not an alternative.** It does not support Podman at all — *"Colima is a higher level
usage of Lima. It utilises Lima to provide Docker, Containerd, Kubernetes, and Incus runtimes."*
Do not list it as a `podman machine` substitute.

### 5.6 Mageia 10

Mageia is the **weakest** platform and the page must say so. Three problems, one of which is
UNVERIFIED.

```bash
# 1. Packages. There is no pipx package and no uidmap package.
sudo dnf install -y podman ansible git python3-pip passt crun
# expect a list ending in "Setting up podman ..."

# 2. Ignore the packaged Molecule.
rpm -q python3-molecule
# expect: python3-molecule-6.0.3-1.mga10      <- September 2021. UNUSABLE.
# Do not install it. If it is installed, it will shadow whatever you install below:
#   sudo dnf remove python3-molecule

# 3. Install pipx from pip, because Mageia does not package it
python3 -m pip install --user pipx
# expect: "Successfully installed pipx-..."
python3 -m pipx --version
# expect: pipx 1.x.x from /home/<user>/.local/lib/python3.x/site-packages/pipx (python 3.x)

# 4. The safer route: a virtual environment.
#    Mageia 10's PEP 668 EXTERNALLY-MANAGED status is UNVERIFIED, so a venv is safe either way.
python3 -m venv ~/.venvs/molecule
source ~/.venvs/molecule/bin/activate
python3 -m pip install --upgrade pip
pip install molecule ansible-core "molecule-plugins[podman]"
molecule --version
molecule drivers
# expect: a list that includes the line: podman

# 5. Rootless id mapping is UNVERIFIED on Mageia. Check it:
rpm -ql shadow-utils | grep -E 'newuidmap|newgidmap'
# If nothing is listed, there is no newuidmap. Report it in the docs and stop;
# do not invent a fix. The working recipe on every other platform is:
#   sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$USER"
#   (log out, log back in)
#   podman system migrate
```

Mageia 10's good news, which the page should state: `ansible-core 2.20.6-1.mga10` and
`ansible 13.7.0-1.mga10` are **fresher** than Fedora 44's, and `podman 5.7.1-1.mga10` is only one
minor behind.

---

## 6. The pre-flight check script

**Canonical file:** [`scripts/molecule-preflight.sh`](scripts/molecule-preflight.sh) — 7.1 KB,
POSIX-safe bash, read-only, never uses `sudo`, never installs anything.

**Three rules for the pages that use it (R1):**
1. **Never paste the script into a page.** Link to the file, or give the download one-liner.
2. **Every install page's final step is "run it"** → link to `docs/preflight.md`.
3. **Never quote an "expected output" that was not produced by an actual run.** The two blocks in
   §6.4 are real.

### 6.1 Contract

| Property | Value |
|---|---|
| Interpreter | `bash` (POSIX-safe body: no `[[ ]]`, no arrays, no `local`, no `pipefail`) |
| Arguments | none required; `--quiet` suppresses everything but the summary line |
| Exit `0` | every **required** check passed (warnings allowed) |
| Exit `1` | at least one **required** check failed |
| Exit `2` | cannot run here (unsupported operating system) |
| Side effects | **none of its own.** It never installs anything, never elevates, and never writes outside Podman's own storage directory, which `podman` itself may create on first use. |

### 6.2 The seven check groups

| § | Group | Required? | Fails when |
|---|---|---|---|
| 1 | Control groups (cgroups) | **yes** | cgroup v1 is in use, or `/sys/fs/cgroup` cannot be read. On macOS it prints the in-VM verification commands instead. |
| 2 | Podman | **yes** | not on `PATH`, or `podman info` fails (engine broken). Warns if major < 5. |
| 3 | Rootless user-id mapping | **yes** (Linux) | `newuidmap` missing, or `/etc/subuid` / `/etc/subgid` have no entry for `$USER`. Skipped on macOS. |
| 4 | SELinux | no | never fails; reports Enforcing / Permissive / Disabled. |
| 5 | Python | **yes** | `python3` missing, or older than 3.10. |
| 6 | Molecule + Podman driver | **yes** | `molecule` missing, or `molecule drivers` does not list `podman`. Warns if the release line is older than 25. |
| 7 | `containers.podman` collection | no | warns only — Molecule installs it during `dependency`. |

### 6.3 Two things this script deliberately does **not** do

- **It never asks for SELinux state via `podman info`.** The template
  `podman info --format '{{.Host.Security.SelinuxEnabled}}'` **does not work on Podman 5.8.7**:
  it errors with *"can't evaluate field SelinuxEnabled in type define.SecurityInfo"*. The working
  form is `{{json .Host.Security}}` and reading `.selinuxEnabled`. The script uses
  `getenforce` instead, which has no such problem. **No page may use the broken template.**
- **It never tests cgroup v2 by parsing `podman info`.** It uses `stat -fc %T /sys/fs/cgroup`,
  which is the check the corpus names first and which works even when Podman is broken.

### 6.4 Real output — captured on the research host

**Host:** Fedora Linux 44 (Workstation Edition), x86_64, kernel cgroup v2, SELinux **Enforcing**,
podman 5.8.7, Python 3.14.7. Run from `/tmp` on 2026-09-28.

**Run A — before Molecule is installed. This is the state most readers start in.**

```console
$ bash molecule-preflight.sh
Molecule + Podman + systemd pre-flight check
host: Linux x86_64

== 1. Control groups (cgroups)
  PASS  cgroup v2 is in use (cgroup2fs)

== 2. Podman (the container engine)
  PASS  podman found: podman version 5.8.7
        major version 5 is supported
  PASS  podman runs rootless (recommended)

== 3. Rootless user-id mapping (newuidmap / subuid / subgid)
  PASS  newuidmap found: /usr/bin/newuidmap
  PASS  /etc/subuid has an entry for youruser
  PASS  /etc/subgid has an entry for youruser

== 4. SELinux (Linux only)
  PASS  SELinux is Enforcing - this is the well-tested case
        You do NOT need: setsebool container_manage_cgroup, /etc/containers/policy.json edits,
        or --security-opt label=disable. Podman labels systemd containers container_init_t.

== 5. Python (Molecule needs Python 3.10 or newer)
  PASS  python3 found: 3.14
  PASS  python3 is new enough (need >= 3.10)

== 6. Molecule and the Podman driver
  FAIL  molecule is not on your PATH
        pipx install molecule ansible-core molecule-plugins
        Mageia (no pipx package): python3 -m pip install --user pipx && pipx install molecule ansible-core molecule-plugins

== 7. The containers.podman Ansible collection
  WARN  ansible-galaxy is not on your PATH, so the collection cannot be checked
        This is only informational - Molecule installs collections on demand.

----------------------------------------
RESULT: NOT READY - 1 required check(s) failed, 1 warning(s)
Fix every FAIL line above, then run this script again.

$ echo $?
1
```

**Run B — with Molecule 26.9.0, the `podman` driver and `containers.podman` 1.20.2 present on
`PATH`.** (Reproduced on the same host with the three executables supplied on `PATH`; the
molecule, ansible-core and collection versions are the real ones from the corpus.)

```console
$ bash molecule-preflight.sh
Molecule + Podman + systemd pre-flight check
host: Linux x86_64

== 1. Control groups (cgroups)
  PASS  cgroup v2 is in use (cgroup2fs)

== 2. Podman (the container engine)
  PASS  podman found: podman version 5.8.7
        major version 5 is supported
  PASS  podman runs rootless (recommended)

== 3. Rootless user-id mapping (newuidmap / subuid / subgid)
  PASS  newuidmap found: /usr/bin/newuidmap
  PASS  /etc/subuid has an entry for youruser
  PASS  /etc/subgid has an entry for youruser

== 4. SELinux (Linux only)
  PASS  SELinux is Enforcing - this is the well-tested case
        You do NOT need: setsebool container_manage_cgroup, /etc/containers/policy.json edits,
        or --security-opt label=disable. Podman labels systemd containers container_init_t.

== 5. Python (Molecule needs Python 3.10 or newer)
  PASS  python3 found: 3.14
      python3 is new enough (need >= 3.10)

== 6. Molecule and the Podman driver
  PASS  molecule 26.9.0
        molecule 26.9.0 is on a supported release line
  PASS  the 'podman' driver is available (from molecule-plugins)

== 7. The containers.podman Ansible collection
  PASS  containers.podman collection is installed (version 1.20.2)

----------------------------------------
RESULT: READY - every check passed

$ echo $?
0
```

> **Correction made during D1, recorded because it is exactly the class of bug this project
> exists to prevent.** The first version of this script parsed Molecule's version with a greedy
> `sed` over the whole `--version` line. Real output is
> `molecule 26.9.0 using ansible-core 2.20.3 python version 3.14.7 platform linux`, so the greedy
> match extracted **`2.20`** — the *ansible-core* version — and then warned that Molecule was out
> of date when it was not. Fixed by taking **field 2 of line 1** with `awk`. Any script in this
> project that parses a version string must read a **field**, not a regex over the whole line.

### 6.5 What a `FAIL` line means, and where to go

| `FAIL` text | Cause | Fix on |
|---|---|---|
| `cgroup v1 is in use` | old kernel or a mixed-v1 host | `docs/install/index.md` §3, `docs/troubleshooting.md` §9 |
| `podman is not on your PATH` | engine not installed | the reader's platform page |
| `podman is installed but 'podman info' failed` | engine present but broken (often AppArmor) | `docs/install/ubuntu.md` §4, `docs/troubleshooting.md` §7 |
| `newuidmap is missing` | id-mapping package absent | `docs/install/rootless-podman.md` |
| `/etc/subuid has no entry for <user>` | range not allocated | `docs/install/rootless-podman.md` steps 2–4 |
| `python3 <ver> is too old` | Python < 3.10 | the reader's platform page |
| `molecule is not on your PATH` | not installed, or `pipx ensurepath` not reloaded | `docs/install/<platform>.md` steps 4–5 |
| `the 'podman' driver is missing` | `molecule-plugins` not installed | `pipx inject molecule molecule-plugins` (printed inline) |

---

## 7. `verify-systemd` — the crux playbook

**This is the single most important file in the project.** It proves the thing the whole site
exists to demonstrate: **systemd is PID 1 inside the container, and a service the test started is
active.**

### 7.1 The rule this playbook is built around

**Never assert `systemctl is-system-running` equals `running`.**

`degraded` is the **normal** rootless outcome, not a failure. Captured failed units on
`archlinux:latest` rootless (a rolling tag, so this capture is a snapshot of one moment — pin
`docker.io/library/archlinux@sha256:<64-hex-digest>` to reproduce it):

- `dbus-broker.service` — *"Exiting due to fatal error: -107"*
- `dbus.socket`
- `systemd-resolved.service` — `status=217/USER`, *"Failed at step USER ... Operation not
  permitted"*
- `systemd-resolved-monitor.socket`
- `systemd-resolved-varlink.socket`
- `systemd-homed.service`
- `systemd-firstboot.service`

These are rootless-container artifacts, not problems with the test. **Assert on your own unit via
`service_facts`.**

### 7.2 The playbook

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
      # fails, and `failed_when: false` swallows it silently -- leaving `sd.stdout_lines: []`
      # and making the expected-output block below unreachable. `shell` is the module that
      # can honour `;` and `||`.
      ansible.builtin.shell: "systemctl is-system-running; systemctl --failed --no-pager || true"
      register: sd
      changed_when: false
      failed_when: false

    - name: Print the diagnostics
      ansible.builtin.debug:
        var: sd.stdout_lines
```

**What each assertion buys, and why it is written that way:**

| Task | Proves | Why not something simpler |
|---|---|---|
| `cat /proc/1/comm` + `assert` | systemd really is PID 1 | This is *the* requirement. Everything else is downstream of it. `/proc/1/comm` contains `systemd`, or `init` on images that symlink it — hence the `or`. |
| `cat /proc/1/environ` | Podman's systemd mode engaged | `container_uuid` is set by Podman at run time, and `$container_uuid` is set by systemd from it. Diagnostic, non-fatal — the byte-value form varies between Podman versions, so asserting on it would be brittle. |
| `service_facts` + `assert` | **your** unit is running | `is-system-running` returns `degraded` for a correct rootless container. Asserting `running` would fail a working system. |
| `systemctl is-system-running; systemctl --failed` | shows the reader what is actually going on | Must be `shell`, not `command` (DBG-4) — only `shell` can honour `;` and `||`. `systemctl --failed` returns non-zero when there are failed units, hence `\|\| true` plus `failed_when: false`. |

**Expected output on a healthy run** — reproduced on a live run, and **only reachable with the
`shell` fix from DBG-4** (with `command`, `sd.stdout_lines` is `[]` and the block below never
appears):

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

TASK [Print the diagnostics] *******************************************************
ok: [instance] => {
    "changed": false,
    "msg": [
        "running",
        "  UNIT                        LOAD   ACTIVE SUB     DESCRIPTION",
        "0 loaded units listed."
    ]
}
```

> **Honesty note for the page.** The `is-system-running` value in that sample is `running` and
> `0 loaded units listed` is the best case. A rootless `degraded` result with a handful of the
> units listed in §7.1 is **equally correct**. The page must show **both** expected outputs and
> say which is which, or the reader whose first run says `degraded` will think they failed.
> Cosmetic: the real header renders as `UNIT LOAD ACTIVE SUB DESCRIPTION`; the column padding
> in the block above is tab-width dependent and will not match your terminal exactly. Do not
> "fix" that.

### 7.3 Why `podman logs` will look empty

`systemd` as PID 1 writes to the **journal**, not to the container's standard output. Podman
tmpfs-mounts `/var/lib/journal` in systemd mode, so `journalctl` works out of the box:

```bash
podman exec instance journalctl -u molecule-demo.service --no-pager
podman exec instance systemctl --failed --no-pager
```

**Empty `podman logs` is normal, not a symptom.** This is the second-most-confusing thing for a
beginner after the PID 1 issue.

---

## 8. Continuous Integration (CI)

### 8.1 Scope boundary — read before writing this section

**The research corpus contains nothing about GitHub Actions, its pricing, or its quotas.**
Per hard constraint 2, this file therefore specifies the *workflow structure* (which is just YAML
plus Molecule) and explicitly **forbids stating a minutes figure**. The page links to GitHub's own
pricing page for the quota. This is a recorded decision, not an oversight — see `STRUCTURE.md` §7
decision 9.

### 8.2 The workflow

```yaml
---
# .github/workflows/molecule.yml
# Continuous Integration: a machine that runs your tests every time you push code.
# $0 forever: GitHub-hosted Linux runners are free for public repositories.
name: molecule

on:
  push:
    branches: ["main"]
  pull_request:
  workflow_dispatch:

# Hard bound so the free tier can never be exceeded.
timeout-minutes: 10

# One run per ref. A new push cancels the in-flight run for the same ref, so
# a burst of pushes costs one run, not one run each.
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  molecule:
    # Read-only by default: this workflow checks out code and runs tests. It
    # never writes to the repository, so it needs no write scope at all.
    permissions:
      contents: read
    # A GitHub-hosted Linux runner. Podman is preinstalled.
    # Do NOT use macos-* or windows-* runners: they burn the quota far faster
    # and podman needs a VM on macOS anyway.
    runs-on: ubuntu-latest

    steps:
      - name: Check out the repository
        uses: actions/checkout@v4

      - name: Install Molecule and the Podman driver
        run: |
          set -euo pipefail
          python3 -m pip install --user pipx
          export PATH="$HOME/.local/bin:$PATH"
          pipx install molecule ansible-core molecule-plugins
          molecule --version
          molecule drivers

      # OPT-IN ADDITION - not part of the canonical workflow above.
      # Uncomment only if docs/scripts/molecule-preflight.sh exists in THIS
      # repository. A hosted runner is a known-good machine, so the canonical
      # workflow does not need a readiness check; add one when a runner's
      # environment is yours to control.
      # - name: Pre-flight check
      #   run: bash docs/scripts/molecule-preflight.sh --quiet

      - name: Run the default scenario
        run: molecule test

      - name: Run the systemd scenario
        run: molecule test --scenario-name systemd

      - name: Upload the scenario logs on failure
        if: failure()
        run: |
          mkdir -p molecule-artifacts
          for s in default systemd; do
            cp -v "molecule/$s/molecule.log" "molecule-artifacts/$s.log" 2>/dev/null || true
          done
          ls -la molecule-artifacts
        shell: bash

      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: molecule-logs
          path: molecule-artifacts/
          retention-days: 7
```

**Why each piece is there:**

| Piece | Reason |
|---|---|
| `runs-on: ubuntu-latest` | Free tier. macOS and Windows runners are quota-expensive, and podman on macOS needs a VM. |
| `timeout-minutes: 10` | A hard bound, so a hung test cannot exhaust the free quota. |
| `concurrency: ${{ github.workflow }}-${{ github.ref }}` | One run per ref. Without it, three pushes in a minute start three parallel jobs and spend three times the quota. |
| `cancel-in-progress: true` | A newer push makes the older, now-irrelevant run pointless, so cancel it rather than let it finish and bill against the free minutes. |
| `permissions: contents: read` | Least privilege. The job only reads the repository; leaving the default token scope wide would make a compromised build step able to push. |
| `python3 -m pip install --user pipx` then `export PATH` | Ubuntu ships `pipx` in apt, but this works on every runner image. |
| `molecule drivers` before the test | Fails fast with a readable message if the driver never installed, instead of an opaque error inside `molecule test`. |
| One step per scenario | Separate log lines in the CI UI make triage trivial. |
| `if: failure()` on the upload steps | Uploads cost nothing and only run when something broke. |
| `retention-days: 7` | Artifacts are not free forever; seven days is plenty. |

**Hard rules for `docs/authoring/ci.md`:**

- **No Docker, anywhere.** No `docker build`, no `docker login`, no `docker-compose`.
- **No self-hosted runners.** They cost money, which the Zero-Cost Doctrine forbids.
- **No paid marketplace actions.** Only the first-party `actions/*`.
- **No secrets in the workflow file.** If a private registry is ever needed, use
  variable substitution, never hard-coded credentials: *"Hard-coded credentials in `molecule.yml`
  should be avoided, instead use variable substitution."*
- **Pin actions to a version** (`@v4`), never to `@main`.
- **No quota numbers.** Link to <https://github.com/pricing> instead.

---

## 9. `create.yml`, `destroy.yml` and the test sequences

### 9.1 `create.yml` and `destroy.yml` — with the podman driver

> #### **DBG-3 — this section previously said the opposite of the truth. Corrected.**
>
> The earlier text claimed these files are scaffolded *"because Molecule's own architecture
> requires them"* and that *"the driver owns the container lifecycle"*, and told pages to ship
> them. **Shipping them breaks the podman driver.** Both statements are now retracted:
>
> - **They are NOT required.** Do not ship them. `molecule init scenario` writes both files;
>   under a driver the correct action is to **delete** them.
> - **Shipping one overrides the driver's own playbook.** Molecule resolves a scenario's own
>   `create.yml` *before* falling back to the driver's, so the `create` step runs **only the
>   inert local stub** and **no container is ever built**:
>
>   ```console
>   INFO     [default > create] Executing
>   PLAY [Create] ******************************************************************
>   TASK [Populate instance config dict] *******************************************
>   skipping: [localhost]
>   INFO     [default > create] Executed: Successful      <-- "successful", but nothing was created
>   ...
>   TASK [Wait for systemd to finish booting] **************************************
>   [ERROR]: Task failed: Command execution failed: Container 'instance' not found
>   ```
>
>   The driver's real playbook (`molecule_plugins/podman/playbooks/create.yml`) contains
>   `Create Dockerfiles from image names`, `Create podman network dedicated to this scenario`,
>   `Create molecule instance(s)`, `Wait for instance(s) creation to complete` — **none of which
>   appear in the run** when your own file is present. Deleting the two files makes the driver's
>   playbook run and the container appear.
> - **The failure is a `fatal`, not a warning**, which is why this is 🔴 HIGH: the reader loses
>   the container, not a convenience.
>
> **Corrected guidance:** with the `molecule-plugins` podman driver, `molecule.yml` *is* the
> create/destroy configuration. Ship §2b and nothing else. If you genuinely want to take over
> provisioning — an extra network, a volume, a seed script — you may write `create.yml` on
> purpose, but then you own the whole container lifecycle and must reproduce everything the
> driver's playbook does. That is a deliberate decision, not a default.

The pages that need the *content* for the **Ansible-native route only** (§2b, where Molecule has
no driver and there is no driver playbook to override) quote the driver's playbooks. **Label them
clearly as that route only:**

```yaml
---
# create.yml  (Ansible-native route: containers are created with the containers.podman modules)
- name: Create container instances
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Create containers from inventory
      containers.podman.podman_container:
        hostname: "{{ item }}"
        name: "{{ item }}"
        image: "{{ hostvars[item]['container_image'] }}"
        command: "{{ hostvars[item]['container_command'] | default('sleep 1d') }}"
        privileged: "{{ hostvars[item]['container_privileged'] | default(false) }}"
        volumes: "{{ hostvars[item]['container_volumes'] | default(omit) }}"
        capabilities: "{{ hostvars[item]['container_capabilities'] | default(omit) }}"
        systemd: "{{ hostvars[item]['container_systemd'] | default(false) }}"
        log_driver: "{{ hostvars[item]['container_log_driver'] | default('json-file') }}"
        state: started
      register: result
      loop: "{{ groups['molecule'] }}"

    - name: Verify containers are running
      ansible.builtin.include_tasks:
        file: tasks/create-fail.yml
      when: >
        item.container.State.ExitCode != 0 or
        not item.container.State.Running
      loop: "{{ result.results }}"
      loop_control:
        label: "{{ item.container.Name }}"

    - name: Wait for containers to be ready
      ansible.builtin.wait_for_connection:
        timeout: 30
      delegate_to: "{{ item }}"
      loop: "{{ groups['molecule'] }}"
```

```yaml
---
# destroy.yml
- name: Destroy container instances
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Get info for all containers
      containers.podman.podman_container_info:
        name: "{{ item }}"
      loop: "{{ groups['molecule'] }}"
      register: podman_infos

    - name: Kill container if running
      containers.podman.podman_container:
        name: "{{ item.item }}"
        state: stopped
        timeout: 2
      loop: "{{ podman_infos.results }}"
      loop_control:
        label: "{{ item.item }}"
      when:
        - item.containers | length > 0
        - item.containers[0].State.Status == "running"
```

> **Note the `tasks/create-fail.yml` file** referenced by `create.yml`. It is part of the
> Ansible-native layout and displays container logs when creation fails. If a page ships
> `create.yml` **for the Ansible-native route**, it must ship `tasks/create-fail.yml` too, or the
> `include_tasks` will fail at runtime with a file-not-found error. The driver-based projects in
> §2a and §2b must **not** ship `create.yml` at all (DBG-3) — there is no `include_tasks` to
> break, because the driver supplies its own.

### 9.2 The two `test_sequence` values

**The default sequence that `molecule init scenario` scaffolds:**

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

**The official Podman (Ansible-native) sequence** — what this project uses in §2a and §2b because
it is shorter and matches the Ansible-native example:

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

**What each step does, for `docs/usage.md`:**

| Step | What it does | Beginner note |
|---|---|---|
| `dependency` | Installs roles and collections from `requirements.yml` | Runs first so everything else has what it needs. |
| `cleanup` | Removes artefacts from a previous run | Appears at the start *and* the end. **In this shorter sequence it appears once, and it needs `cleanup.yml` to exist or Molecule reports `Missing playbook` — see §3.4 (DBG-6).** |
| `destroy` | Deletes the containers | Appears at the start *and* the end, so a crashed run does not poison the next one. **Under a driver, do not ship `destroy.yml` — it overrides the driver's own playbook (DBG-3, §9.1).** |
| `syntax` | Checks the playbooks parse. Does not run them. | Catches a typo in seconds. |
| `create` | Creates the containers | **Under a driver, do not ship `create.yml` — it overrides the driver's own playbook and no container is built (DBG-3, §9.1).** |
| `prepare` | Installs fixtures before converge | Not scaffolded; you write it. |
| `converge` | **Applies your role** | The step that does the work. |
| `idempotence` | Converge a second time, assert nothing changed | Catches tasks that do something every run. |
| `side_effect` | Makes a change, for the purpose of undoing it in a second scenario | Not scaffolded. |
| `verify` | **Asserts the outcome** | The step that decides pass or fail. |

### 9.3 Commands that do not exist

`molecule add`, `molecule remove` and `molecule lint` **have been removed**. No source files exist
in `src/molecule/command/`, and there are zero documentation mentions. Replacements:

| Removed | Use instead |
|---|---|
| `molecule add <name>` | `molecule init scenario <name>` |
| `molecule remove <name>` | `rm -r molecule/<name>` |
| `molecule lint` | `ansible-lint` (standalone) |

`molecule init` has **exactly one subcommand**: `scenario`.

---

## 10. The folklore table — the "what the internet still gets wrong" content

**This table is content for `docs/systemd-in-containers.md` §11 and `README.md` §3. It is
specified here so all three copies stay identical.**

| You will read online | What is actually true | Evidence |
|---|---|---|
| "You need `--privileged` for systemd in a container." | **No — it makes things worse.** Privileged mode unmask `/sys`, so `sys-kernel-config.mount`, `sys-kernel-debug.mount` and `sys-kernel-tracing.mount` fail, and the container lands in `degraded` instead of `running`. Also: *"Containers running in a user namespace (e.g., rootless containers) cannot have more privileges than the user that launched them."* | EMPIRICAL, rootless + cgroup v2 + SELinux Enforcing |
| "Run `setsebool -P container_manage_cgroup true`." | **No**, on Podman ≥ 2.0 with container-selinux ≥ 2.132. Podman labels a systemd-mode container `container_init_t`, which can already write the cgroup filesystem. Verified: the boolean is **off** on Fedora 44, the process label is `system_u:system_r:container_init_t:...`, and systemd still reached `running`. Only do this if you are reading **actual AVC denials**. | EMPIRICAL + `troubleshooting.md` §8: *"Only do this on systems running older versions of Podman."* |
| "You must edit `/etc/containers/policy.json`." | **No.** Stock Fedora `policy.json` (no `mounts` array, no `cgroupns` key) reaches `running` with no edits. This is Docker-era advice. | EMPIRICAL |
| "Add `--cgroups=disabled`." | **No.** Nothing recommends it. It conflicts with `--cgroupns` and `--cgroup-parent`, and it was buggy. Quadlet defaults to `CgroupsMode=split`, not `enabled`. | `podman-run(1)` + issue/patch history |
| "Set `--cgroup-manager=cgroupfs` for rootless." | **No — the premise is inverted.** `cgroupfs` was the cgroup-v1-era workaround. `systemd` is the default and is what you want, because `systemd.io/CONTAINER_INTERFACE` prescribes a `*.scope` unit with `Delegate=yes`. | upstream docs + `CONTAINER_INTERFACE` |
| "Bind-mount `/sys/fs/cgroup` yourself with `-v`." | **No.** `--systemd=always` already mounts it **writable** on cgroup v2. | `options/systemd.md` + EMPIRICAL |
| "Add `--annotation run.oci.keep_original_groups=1`." | **No.** That annotation is about **supplementary groups**, not systemd — `crun.1.md`: *"crun will skip the `setgroups` syscall"*. It was superseded by `podman run --group-add keep-groups` (Podman ≥ 3.2). | `crun.1.md` |
| "Set `ENV SYSTEMD_ETC=/usr/lib/systemd`." | Not a systemd requirement. It appears nowhere in systemd's source or `CONTAINER_INTERFACE`. It is a community Dockerfile convention. Harmless, and it is in the canonical Containerfile for familiarity — but the page must say it is optional. | `grep` of `systemd-stable/src/basic/virt.c` |
| "Set `ENV container_uuid=$(cat /proc/sys/kernel/random/uuid)`." | **This breaks the build.** Verified: `Error: parsing main Dockerfile: Containerfile: Syntax error - can't find = in "/proc/sys/kernel/random/uuid"`. Podman sets `container_uuid` at run time anyway. | EMPIRICAL build failure |
| "Molecule's systemd guide recommends `quay.io/centos/centos:stream10`." | **That image has no systemd and cannot work.** All 59 active `quay.io/centos/centos` tags were enumerated; none contain `init`. `stream10-init` → `manifest unknown`. **Documented upstream bug.** Use `ubi-init` or a custom image. | EMPIRICAL |
| "Use `M1tch/dind-systemd`." | **HTTP 404.** So is `nickchase/systemd-container`. Both were the commonly-cited de-facto references. | EMPIRICAL |
| "You need a `policy.json` `cgroupns` field." | **UNVERIFIED** and **unnecessary.** No current `containers-policy.json(5)` page was locatable. Nothing needed editing on a stock host. | corpus UNVERIFIED register |
| "`MOLECULE_DEFAULT_DOCKER_BIN` selects the Podman binary." | **It does not exist.** 0 code-search hits repo-wide on GitHub. Use `MOLECULE_PODMAN_EXECUTABLE`. | 0 hits |
| "Point Ansible at the Podman socket with `DOCKER_HOST`." | **No.** The `containers.podman.podman` connection plugin drives the **`podman` CLI**, not a socket. There is no `DOCKER_HOST` in its documentation. | plugin docs |
| "The podman connection plugin lives in `community.docker`." | **No.** It is in **`containers.podman`**. `community.docker` ships only `docker`, `docker_api` and `nsenter`. | source tree |
| "Molecule is on version 6 or 7." | **No.** Molecule uses CalVer. Current release is **`26.9.0`** (2026-09-22). | PyPI |
| "Install `molecule-ansible` as a plugin." | **It does not exist.** `https://pypi.org/simple/molecule-ansible/` → **404**. | PyPI |
| "Install the `delegator` package." | **Not a dependency.** It is an unrelated 2014 package implementing Ruby's `delegate.rb`. The confusion comes from the *class* name `molecule.driver.delegated.Delegated`. | PyPI + source |
| "Use `molecule add` / `molecule remove` / `molecule lint`." | **All removed.** See §9.3. | source tree |
| "`pipx install molecule` is the documented method." | pipx is **not** named in Molecule's documentation, which says *"pip is the only supported installation method"*. pipx *is* pip-in-a-venv and satisfies that. We say both things. | see §5 |
| "`options: { provided_modules, env }` are Podman-driver options." | **No.** Only the `default` driver reads `options.ansible_connection_options`. The podman driver reads `options.safe_files` and `options.login_cmd_template`. | driver source |
| "A `molecule.yml` with no `groups:` key is fine — `hosts: molecule` is built in." | **No, and this is the most dangerous item on this table** because it fails *green*. There is **no implicit `molecule` group**, so `hosts: molecule` matches nothing, every play reports `skipping: no hosts matched`, **zero assertions execute**, and `molecule test` **exits 0**. Mechanism and the non-vacuity check are in §10.1. | Add `groups: [molecule]` to every `platforms[*]` entry. §2d, §10.1. |
| "`molecule init` scaffolds `create.yml` and `destroy.yml`, so I should keep them." | **No — under a driver, shipping them breaks the scenario.** Molecule resolves the scenario's own `create.yml` *before* the driver's, so the `create` step runs only the inert local stub, **no container is ever built**, and `converge` dies with `Command execution failed: Container 'instance' not found`. The step still reports `Executed: Successful`, which is what makes it so confusing. | **Delete both files.** `molecule.yml` *is* the create/destroy configuration under the `podman` driver. Only ship a `create.yml` if you deliberately want to own the whole container lifecycle. §9.1. |

---

## 10.1 The `groups:` trap in full

The folklore-table row above is the one myth here that **passes**, which makes it the one worth
spelling out. Molecule builds its Ansible groups from the `groups` key of each
`platforms[*]` entry, and when that key is absent it defaults to `["ungrouped"]` — the exact
expression is `platform.get("groups", ["ungrouped"])` in
`molecule/provisioner/ansible.py`. There is no implicit `molecule` group, so a play whose
`hosts:` names `molecule` matches no host in any run, ever. Molecule's own scaffolded
`converge.yml` uses `hosts: all`, so a freshly scaffolded scenario works and the mistake is
invisible until someone writes `hosts: molecule` to be explicit.

The two failure modes are not the same, and only one of them is loud:

| What you see in `molecule test` | What it means |
|---|---|
| `skipping: no hosts matched` on every play, `PLAY RECAP` with `ok=0`, **exit code 0** | The trap. Every assertion was skipped and the run still reports success. Nothing failed, because nothing ran. |
| A genuine task failure, non-zero exit | Normal, and *good* news: your play matched a host. Fix the failure. |

So a green run proves nothing on its own. After any change to `groups:` or to a play's `hosts:`,
check the run is non-vacuous:

- `PLAY RECAP` must show `ok=N` with **`N > 0`**.
- There must be **zero** `no hosts matched` lines in the whole output.

**The fix** is `groups: [molecule]` on every `platforms[*]` entry (§2d). **The regression test**
is the two checks above, because a scenario with no assertions and a scenario with passing
assertions produce the same exit code.

---

## 11. Inconsistency log — corpus self-contradictions carried into this file

Full analysis in [`STRUCTURE.md` §8](STRUCTURE.md). The short list, with the decision baked in
above:

| ID | Contradiction | Decision taken in this file |
|---|---|---|
| **C-1** | The podman driver's docstring says to set `privileged: true` for systemd; §10 says it is actively harmful; `03` §7.4 repeats the docstring for all six platforms. | **Never set `privileged: true`.** Canonical files set `privileged: false`. §10 names the docstring as the source of the wrong advice. **Needs upstream report.** |
| **C-2** | Molecule's own systemd guide recommends an image with no systemd. | Canonical files use `ubi9/ubi-init`. §1.3 and §10 name the bug. |
| **C-3** | The `podman-rootless(7)` "No cgroup V1 Support" bullet exists in 5.4.2 but was removed from `main` in 2026-01-29. | The site never cites a Podman man page without naming its version, and states cgroup v2 as a **Podman 6.0 / kernel fact**. |
| **C-4** | `podman info --format '{{.Host.Security.SelinuxEnabled}}'` errors on Podman 5.8.7. | §6.3 forbids it. The script uses `getenforce`. |
| **C-5** | "pip is the only supported method" vs. "pipx is the right tool". | §5 quotes both positions. No page claims pipx is Molecule's documented method. |
| **C-6** | Molecule's own example ships `container_systemd: false` in `group_vars`, which outranks inline `vars`. | §2c forbids `group_vars` in this project. |
| **C-7** | `podman(1)` says `--cgroup-manager` defaults to `systemd`, but Podman 6.0 removed it from `podman machine init`/`set`. | §5.5 gives a **verification block**, not an assertion. |

---

## 12. Copy rules for the seven authoring agents

1. **Copy, do not retype.** Every YAML, Dockerfile, shell block and version number in a page comes
   from this file by copy-paste. If a page needs something that is not here, add it here first.
2. **Annotations go *after* the block, never inside it.** A reader must be able to paste any
   block in this file verbatim. Comments inside a block are kept only where they were in the
   verified original.
3. **Never invent an "expected output".** Paste a real captured one, or label it clearly as
   illustrative. The two blocks in §6.4 are real and are marked as such.
4. **A `> **UNVERIFIED**` marker in this file is a hard requirement, not a suggestion.** It must
   survive into the page.
5. **A `FAIL` that contradicts the corpus is an escalation,** not an editorial decision. Tell the
   tech-lead; do not quietly pick a side. The seven items in §11 are already decided; anything
   *new* goes to §11 before a page uses it.
