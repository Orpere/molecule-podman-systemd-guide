# Custom images

> **You are here:** [Authoring](./index.md) → [Writing tests](./writing-tests.md) → **Custom images** → [Multi-scenario](./multi-scenario.md)

**What you will be able to do:** build your own systemd-capable container image from a
`Dockerfile.j2`, and understand the one setting whose default silently skips the build
entirely.

---

## The one requirement, before anything else

**Your container image must contain Python.**

Molecule's own documentation says it plainly: *"When selecting the container image, remember
that the container image **must** have Python installed to be able to run many of the builtin
tasks."* Ansible's built-in tasks run Python on the **target** — the machine being
configured. No Python, no tasks. Your test fails with a traceback before your first assertion
runs.

This has **nothing to do with systemd**. It is a separate requirement, and it applies to the
quickstart image too. A bare `alpine` image is the canonical counter-example: it has no
Python, it is not a systemd image either, and it will fail on most `ansible.builtin`
modules. It cannot be a Molecule scenario image.

So a usable scenario image needs **three** things, and beginners routinely conflate them:

| # | Requirement | Why |
|---|---|---|
| 1 | **Python installed** | Ansible's built-in tasks execute Python on the target. Nothing works without it. |
| 2 | **systemd installed** | No mainstream base image ships it. Verified absent from `debian:bookworm`, `debian:bookworm-slim`, `ubuntu:24.04`, `fedora:latest`, `quay.io/fedora/fedora:latest`, `quay.io/centos/centos:stream9`, `quay.io/centos/centos:stream10` and `ubi9/ubi-minimal`. |
| 3 | **`/sbin/init` exists and is the command** | Otherwise something else is process 1, and systemd refuses to run. |

Requirements 2 and 3 are what this page is about. Requirement 1 is why both recipes below
install `python3`.

---

## The two ways to give Molecule an image

| | **(a) Prebuilt image** | **(b) Build your own** |
|---|---|---|
| How | `platforms[*].image` points at an image that already exists | `pre_build_image: false` plus a `Dockerfile.j2` |
| Build time | None — just a pull | Once, then cached |
| The image value is | The whole reference: `registry.access.redhat.com/ubi9/ubi-init:latest` | The **base** image only. It becomes the `FROM` line. |
| Debugging | Nothing to debug | A broken `RUN` line. Faster to fix by hand first — see below. |
| **Use when** | A published image already has what you need. **This is the default choice.** | Your role needs a package, a user, or a build flag no published image has. |

---

## `pre_build_image: false` is mandatory

**`pre_build_image` defaults to `true`.**

The default means *"use the image as-is"*. With the default, Molecule never looks at your
`Dockerfile.j2` at all. It pulls the base image, runs the container, and your `Dockerfile`
changes have **no effect whatsoever** — with no error and no warning.

This is the number-one cause of "I edited the Dockerfile and nothing happened". Molecule's own
rootless guide states the rule: *"The `Dockerfile` templating and image building processes
are only done for scenarios with `pre_build_image = False`, which is not the default setting
in generated `molecule.yml` files."*

**Getting this backwards is silent.** There is no diagnostic. The test runs, it passes, it
just tests the *base* image instead of yours. If your test passes before you expected it to,
check this setting first.

### How the `Dockerfile.j2` templating works

When `pre_build_image: false` is set:

1. Molecule looks for `Dockerfile.j2` **in the scenario directory**. If it is not there, the
   driver falls back to its own built-in template.
2. It renders the file as a **Jinja template**, with `item` bound to the platform entry from
   your `molecule.yml`. So `{{ item.image }}` is literally the `image:` you wrote.
3. It builds the result, tagging the result `molecule_local/` + your image name.
4. The container is created from that local tag, not from the upstream one.

The image reference the driver computes is exactly:

```text
molecule_local/<your image name>
```

prefixed with `molecule_local/` when `pre_build_image` is false, and **not** prefixed when it
is true. That one expression is the whole mechanism.

`platforms[*].dockerfile` is optional. Set it only if your file has another name or lives
elsewhere; otherwise the `Dockerfile.j2` in the scenario directory is the default. If your
file contains no Jinja at all, drop the `.j2` — a plain `Dockerfile` referenced by
`platforms[*].dockerfile` is not rendered.

### The wiring, verbatim

This is the `molecule.yml` fragment for the build route — **Option B**, quoted from the
research corpus:

```yaml
platforms:
  - name: instance
    image: debian:bookworm-slim        # base; the driver prefixes molecule_local/
    pre_build_image: false             # REQUIRED, else the build is skipped
    dockerfile: Dockerfile.j2          # optional; Dockerfile.j2 in the scenario dir is the default
    command: /sbin/init
    override_command: true
    systemd: always
    # REQUIRED (DBG-1). Molecule derives its Ansible groups from platforms[*].groups
    # (default ["ungrouped"]), so there is no implicit `molecule` group. Omit it and
    # `hosts: molecule` in converge.yml/verify.yml matches nothing: every play reports
    # "skipping: no hosts matched" and `molecule test` still EXITS 0. Silent false pass.
    groups:
      - molecule
```

**What changed and why:** `image` is now a *base without systemd*, because your
`Dockerfile.j2` is what adds it. `pre_build_image: false` turns the build on. The three
systemd keys stay exactly as they are — they are about running the container, not about
building the image. And `groups: [molecule]` is added, which is the line this block was
missing and which is the reason a build route could go green without asserting anything.

---

## The Debian / Ubuntu image — ✅ verified, built and booted

**Status: this recipe was actually built and booted during the research session**, on Fedora
44, cgroup v2, SELinux Enforcing, rootless Podman 5.8.7. The result was
`systemctl is-system-running` returning `running` and `systemctl --failed` returning **no
output at all**.

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

Save it as `molecule/systemd/Dockerfile.j2`. The `.j2` suffix is required when Molecule
renders the file; the content is a Jinja template with **no** Jinja beyond `{{ item.image }}`.

### Every line, explained

| Line | Why it is there |
|---|---|
| `FROM {{ item.image }}` | `item` is the platform entry from `molecule.yml`, so this is the base image you named. `Dockerfile.j2` is rendered from the scenario directory, where `item` is the platform config. |
| `ENV container=docker` | **Cosmetic.** systemd auto-detects Podman through `/run/.containerenv`; `container=podman` works equally well. Podman sets `container_uuid` at run time anyway. |
| `ENV SYSTEMD_ETC=/usr/lib/systemd` | **Not a systemd requirement.** It appears nowhere in systemd's source or `CONTAINER_INTERFACE.md`. It is a widespread community convention. Harmless; included for consistency. |
| `ENV XDG_CONFIG_HOME=/config` | Keeps user configuration out of the root home directory. |
| `rm -f /usr/sbin/policy-rc.d` | Debian and Ubuntu ship a `policy-rc.d` that is `exit 101` and blocks **all** rc.d service starts. It does *not* block `systemctl start foo.service` for a modern unit, but it breaks sysv-only packages and `dpkg` post-install starts. Verified byte-identical in `debian:bookworm`, `debian:bookworm-slim` and `ubuntu:24.04`. |
| `rm -f /sbin/init` then `ln -s /lib/systemd/systemd /sbin/init` | `systemd-sysv` provides `/sbin/init` on Debian, but the symlink is made explicitly so the recipe also works on `-slim`, where the `init-system-helpers` symlink may be absent. |
| `apt-get install … systemd systemd-sysv` | The whole point of the image. |
| `… dbus` | `multi-user.target` wants `dbus.socket`; without `dbus` that unit fails. |
| `… python3` | The hard requirement from the top of this page. Non-negotiable. |
| `… sudo procps` | Convenience for roles: privilege escalation (`become`), `ps`, `pgrep`. |
| `DEBIAN_FRONTEND=noninteractive` | Needed on Ubuntu, which ships `debconf` pre-seeds that can block on a prompt. Harmless on Debian. |
| `systemctl set-default multi-user.target` | Sets the boot target so systemd has something to reach. `systemd-sysv` generates `multi-user.target`; this pins it. |
| `WORKDIR /root` | Where tasks run by default. |
| `CMD ["/sbin/init"]` | Makes init the image's default command. With `override_command: true` in `molecule.yml`, Molecule honours the `command:` key. |

### The Ubuntu variant — an adaptation, not a build

> **Status: NOT built during the research session.** The recipe above is a direct adaptation
> of the verified Debian one, and the differences are the two Ubuntu-specific lines already in
> it: `DEBIAN_FRONTEND=noninteractive` (Ubuntu ships blocking `debconf` pre-seeds) and the
> base image. Nothing else changes. Use it on `ubuntu:24.04` and treat it as reviewed, not
> as tested. If it fails on your machine, start from the Debian recipe and change only the
> base image.

### Two Jinja traps, so you do not hit them

- **If the block contains no `{{ }}` at all, Molecule may still render it.** To be safe when
  writing a truly plain `Dockerfile` referenced from `platforms[*].dockerfile`, do not use
  the `.j2` name.
- **`ENV container_uuid=$(cat /proc/sys/kernel/random/uuid)` BREAKS THE BUILD.** Verified
  error, reproduced:

  ```text
  Error: parsing main Dockerfile: Containerfile: Syntax error - can't find = in
  "/proc/sys/kernel/random/uuid". Must be of the form: name=value
  ```

  Podman sets `container_uuid` at run time anyway, so it is never needed.

---

## The Fedora image — ⚠ verified necessary, recipe inferred

**Status, stated precisely:**

- The **fact** is verified: no Fedora container image ships systemd, so `dnf install systemd`
  is mandatory. `fedora:latest` is *"Fedora Linux 44 (Container Image)"*, a minimal variant
  that deliberately excludes systemd.
- The **recipe below was not built during the research session.** It is reviewed and
  consistent with the verified Debian recipe, and it is **not yet booted here**. Treat it as
  a necessary, carefully-reasoned starting point — not as a tested artifact. The
  live-verified path for a Fedora reader is the Debian recipe with a Debian base, or the
  prebuilt image in the next section.

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

### How it differs from the Debian recipe, and why

| Difference | Why |
|---|---|
| No `policy-rc.d` to remove | It is a Debian/Ubuntu invention. Fedora has no such file. |
| `ln -sf` instead of `rm -f` + `ln -s` | Nothing to remove, and `-f` makes the command idempotent — which matters here, because this runs inside a `RUN`. |
| `/usr/lib/systemd/systemd`, not `/lib/systemd/systemd` | On Fedora `/lib` is a symlink to `/usr/lib`, so `/sbin/init` must point at the `/usr`-prefixed path. |
| `systemd-networkd` | Fedora's systemd package does not pull in the network unit that `multi-user.target` wants. |
| `dnf clean all` + `rm -rf /var/cache/dnf` | Keeps the image small. The Debian equivalent is `apt-get clean` + removing the lists. |
| `ENV container=podman` | Cosmetic either way; Podman's own Dockerfiles use this value. |

Everything else is identical on purpose: Python, `dbus`, `set-default`, `WORKDIR`, `CMD`.

---

## The prebuilt-image alternative — the recommended default

**Read this section before you build anything.** If a published image already has what your
role needs, you do not need either recipe above.

| Image | systemd version | Result under rootless | Note |
|---|---|---|---|
| `registry.access.redhat.com/ubi9/ubi-init:latest` | 252 | **`running`** | ✅ verified; free; no Red Hat subscription needed |
| `registry.access.redhat.com/ubi10/ubi-init:latest` | 257 | **`running`** | ✅ verified; free; no Red Hat subscription needed |
| `docker.io/library/archlinux:latest` | 261.3 | `degraded` | Works, but it is a **rolling release** — not reproducible |

All three contain systemd, `/sbin/init` and Python. `ubi9/ubi-init` reached the *best* state
of anything tested: `running`, with zero failed units. Nothing to build, nothing to debug, and
nothing to pin. **This is what the canonical `molecule.yml` uses.**

### Do not use

| Image | Why not |
|---|---|
| `M1tch/dind-systemd` | **Dead. HTTP 404.** |
| `nickchase/systemd-container` | **Dead. HTTP 404.** |

Both were the commonly-cited de-facto references for this problem. Both are gone. This is
worth knowing because a 2019-era tutorial will send you straight to one of them.

**Do not use a CentOS Stream image for a systemd scenario.** Molecule's own systemd guide
recommends `quay.io/centos/centos:stream10` with `command: /sbin/init` — and that image has
no systemd and cannot work. All 59 active `quay.io/centos/centos` tags were enumerated and
none contain `init`. This is a documented upstream bug. If you copied a config from that
guide, the reason it never worked is here.

**There is no official systemd-upstream OCI recipe.** The `systemd/systemd-stable@main` tree
contains only `docs/CONTAINER_INTERFACE.md`,
`docs/WRITING_VM_AND_CONTAINER_MANAGERS.md`, `network/80-container-*` and
`units/container-getty@.service.in`. The official recipes are `systemd-nspawn` examples,
which are **namespace** containers, not **OCI** images — where **OCI** means *Open Container
Initiative*, the standard image format Podman and every other modern engine use. Do not wait
for upstream to hand you one.

### Why build your own anyway

Even if you ship the prebuilt image, learn this. Three reasons:

1. **You will need it eventually.** The first time your role needs a package, a user, or a
   kernel setting that no published image has, you need this page.
2. **It is the biggest speed lever available.** Every `dnf install` in `converge.yml` runs on
   every test. The same install in a `Dockerfile.j2` runs **once**. A test that took 90
   seconds can take 15 — ⚠️ an **illustrative estimate, not a measurement**; the ratio depends
   entirely on what the install is.
3. **You learn what your scenario is really running.** After writing the image, you know
   exactly what is inside it — which is exactly the knowledge that makes a test failure
   diagnosable.

The honest summary: **start with `ubi9/ubi-init`. Build an image the day a published one
stops being enough.**

---

## Build it by hand first

Faster to debug. If the build fails inside `molecule test`, you are reading a Molecule log, an
Ansible log, and a container log at the same time. Prove the image works on its own first:

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

**You should see:** the build finishing without error, and `podman exec` printing either
`running` **or** `degraded` — both are acceptable. `running` with no failed units is the best
case; `degraded` with a handful of rootless-container units is normal and correct. A
container that exits immediately with `State.ExitCode=255` and completely empty logs means
systemd could not write its cgroups, and `systemd: always` is missing.

If it works by hand, wire it into `molecule.yml` with `pre_build_image: false`. If it does
not, you have a container problem, not a Molecule problem — and you will know which.

Clean up afterwards: `podman rm -f inst`.

---

## Pin your base image

`:latest` is not reproducible. It changes under you, with no commit and no diff, and your
test breaks on someone else's machine.

| Base reference | Reproducible? | Use it for |
|---|---|---|
| `debian:bookworm-slim` | ❌ moves | Local development only |
| `debian:bookworm-slim@sha256:abc123…` | ✅ yes | Anything you commit |
| `debian:12.11-slim` | mostly — a named version | A good middle ground |

The same applies to the prebuilt route: `ubi9/ubi-init:latest` is convenient and
`.latest`-shaped. If you want a byte-identical test everywhere, pin it.

> **UNVERIFIED:** this site does not quote a specific `debian:bookworm-slim` digest, because
> a digest is only correct until the next rebuild. Take the digest from your own
> `podman build` output, or from `podman image inspect`, and pin that.

---

## Next

- **[Multi-scenario](./multi-scenario.md)** — several scenarios, and one shared image across
  all of them.
- **[systemd in containers](../systemd-in-containers.md)** — what `systemd: always` sets up
  inside the container, and the `degraded` lesson in full.
- **[Troubleshooting](../troubleshooting.md)** — when the build or the container fails.
- **Runnable example:** [`../../examples/systemd-unit/`](../../examples/systemd-unit/)

---

## Attribution

No brand marks or logos are displayed on this page. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md); product names identify the
software being discussed and imply no endorsement.

---

## Sources

- <https://docs.ansible.com/projects/molecule/getting-started-roles/> — *"When selecting the container image, remember that the container image **must** have Python installed to be able to run many of the builtin tasks."*
- <https://github.com/ansible/molecule/blob/main/docs/guides/docker-rootless.md> — *"The `Dockerfile` templating and image building processes are only done for scenarios with `pre_build_image = False`, which is not the default setting in generated `molecule.yml` files."*
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py> — the `pre_build_image` default of `true`, and the `molecule_local/` tag prefix
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/playbooks/Dockerfile.j2> — the driver's own image template, used only when `pre_build_image: false`
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/playbooks/create.yml> — the image reference expression `{{ item.pre_build_image | default(false) | ternary('', 'molecule_local/') }}{{ item.image }}`
- <https://github.com/ansible/molecule/blob/main/docs/examples/podman.md> — the Molecule guide that recommends `quay.io/centos/centos:stream10`, which has no systemd (documented bug)
- <https://docs.podman.io/en/latest/markdown/podman-run.1.html> — `--systemd=always`, and `/run/.containerenv` as the container-detection mechanism
- <https://github.com/systemd/systemd-stable/blob/main/docs/CONTAINER_INTERFACE.md> — the `container` and `container_uuid` environment variables systemd reads
- <https://catalog.redhat.com/software/containers/ubi9-init/60790c752390a9cc4b2a5c1e> — `ubi9/ubi-init`, free to pull, no subscription required
- Internal, reproducible: the two Containerfiles and the prebuilt-image table are copied verbatim from [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §1.1, §1.2 and §1.3; the hand-build block is §1.3. The Debian recipe was **built and booted** during the research session (`.research/02` §2.5.1); the Fedora recipe is `.research/02` §2.5.3 and the Ubuntu variant is `.research/02` §2.5.2, neither of which was built.
