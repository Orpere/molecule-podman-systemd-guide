# Frequently asked questions

## You are here

[Docs home](./index.md) → **FAQ**.

**What you will be able to do:** get a direct answer to a question you were about to search for,
and be sent to the one page that goes deep on it.

Every answer here is short on purpose. When the honest answer is "no" or "not that way", it says
so — and then says what to do instead. Where a thing is unverified or version-dependent, that is
stated rather than guessed. **This page introduces no new facts.** Every claim traces to a page
that carries the evidence.

---

## Choosing

### Do I need root, or `sudo`?

**No, not for Molecule or Podman.** Not once. Everything in this site runs as an ordinary user.

There are exactly two moments that need `sudo`, and both are host setup, not testing:
installing packages with your package manager, and editing `/etc/subuid` (the file that gives a
normal user a range of fake user IDs) for rootless Podman. The **pre-flight script never uses
`sudo` at all** — it is read-only by design, so you can run it before deciding anything.

See [preflight.md](./preflight.md) and [install/rootless-podman.md](./install/rootless-podman.md).

### Is this free? Does it cost anything, ever?

**$0, and it stays $0.** Every tool here — Molecule, `molecule-plugins`, `ansible-core`, pipx,
Podman, the container images used here, and this documentation — is free and open source. There
is nothing to subscribe to, no trial, and no credit card anywhere in the process.

**Molecule is MIT-licensed** (`pyproject.toml`: `license = "MIT"`). That is what "MIT" means for
you: you can use it, change it and ship it commercially, and nobody can charge you for it.

**This includes CI** — see [Can I run this in CI, and does it cost money?](#can-i-run-this-in-ci-and-does-it-cost-money).

### Does it work on macOS?

**Yes, on Apple Silicon. No on Intel Macs, and there is no workaround.**

On macOS there is no Linux kernel to run containers on, so Podman runs them inside a virtual
machine (a *VM*) called the *podman machine*. That works; the whole path is documented in
[install/macos.md](./install/macos.md).

Intel Macs are **unsupported**: Podman 6.0 removed Intel Mac support outright, Homebrew moved
Intel to Tier 3 in September 2026 with no prebuilt binaries, and the podman formula is
hard-locked to Apple Silicon. **Colima is not an alternative** — it does not support Podman.

> **UNVERIFIED:** no macOS step on this site was executed. The verification host was x86_64
> Fedora. Treat the macOS page as a documented path, not a measured one.

### Why Podman and not Docker?

**Podman runs rootless, with no daemon and no service to start.** Docker normally needs a
background process running as `root` before it will do anything; Podman does not, which is why
every result on this site was produced as an ordinary user.

Docker still works with Molecule — see [Can I use Docker instead?](#can-i-use-docker-instead).
This site documents the Podman path only, because that is the one everything was verified on.

### Can I use Docker instead?

**Yes — Molecule ships a `docker` driver, and you can see it on any install:**

```console
$ molecule drivers
docker
containers
gce
azure
ec2
openstack
vagrant
podman
default
```

Switching means changing one line, `driver: { name: docker }`. **But:** this site documents and
verifies the Podman path only, so anything here about the Docker driver is **unverified**, and
this site will not claim it works. If you use Docker, treat
[`troubleshooting.md`](./troubleshooting.md) as Podman-specific and verify each fix yourself.

If you came here because a tutorial told you to install Docker, that tutorial predates
Podman's systemd support and is teaching you a harder path for no benefit.

### Can I test a role, a playbook, or a collection?

**All three.** `converge.yml` is the file that applies whatever you are testing, and it is an
ordinary Ansible playbook:

- **A role** — `ansible.builtin.include_role` with `name: your_role`. This is the scaffolded
  default and what most of this site shows.
- **A playbook** — `ansible.builtin.import_playbook`, or just write the tasks directly.
- **A collection** — include the specific role from the collection, or run its own scenario
  from a checkout of it.

The difference is only in what the first task of `converge.yml` is. The assertion, idempotence
and container mechanics are identical.

See [authoring/your-first-scenario.md](./authoring/your-first-scenario.md) and
[authoring/writing-tests.md](./authoring/writing-tests.md).

### Can I test something that is not a container?

**Yes.** Molecule is not limited to containers — its driver system has drivers for cloud
instances too, which is why `gce`, `ec2`, `azure` and `openstack` appear in the list above.

**But:** this site documents the Podman driver only, and every verified result here is a
container. For anything else, read the driver you intend to use and
[`troubleshooting.md`](./troubleshooting.md) will not cover it.

### What is the difference between a scenario and a platform?

**A platform is a container. A scenario is a whole test.**

- A **platform** is one entry in the `platforms:` list of `molecule.yml`. It names a container,
  says which image to use, and says how to start it. In the canonical configuration there is
  exactly one, called `instance`. If you wrote `platforms[0].name` and the machine called the
  container that, you have a platform.
- A **scenario** is one directory — `molecule/default/` — containing a `molecule.yml` and its
  playbooks. It is one complete, independent test: its own container, its own converge, its own
  verify. You can have several, and you pick between them with `molecule test -s <name>`.

So: a scenario *contains* platforms. A project can have many scenarios, each with its own
platforms. The multi-scenario layout is in
[authoring/multi-scenario.md](./authoring/multi-scenario.md).

### What is CalVer, and why does this site say `26.9.0`?

**Molecule versions are dates, not version numbers.** CalVer — calendar versioning — means
`26.9.0` is "the release from 2026, month 9, first release". It was released on 2026-09-22.

This matters because **any page or answer telling you Molecule is "version 6" or "version 7" is
wrong.** Those numbers do not exist. The `molecule-plugins` package is on the same scheme: the
version installed here is `26.9.28`.

### Which Ansible versions are supported?

**The honest answer is: this site has verified exactly one combination, and upstream publishes
no support matrix we quote.**

| What | Version |
|---|---|
| **Verified by running** | `ansible-core` **2.21.4**, with Molecule **26.9.0** |
| Fedora 44's package | `ansible-core` 2.20.3 |
| Ubuntu 26.04 LTS's package | `ansible-core` 2.20.1 |
| Ubuntu 24.04 LTS's package | `ansible-core` 2.16.3 — old, but the whole path works on it |

Molecule 26.9 does not pin an `ansible-core` version, so your distribution's version is what you
get unless you install one yourself. Two things to know:

- **Python 3.10 or newer** is the hard floor. Molecule declares `>=3.10`; so does
  `molecule-plugins`.
- **Some Ansible behaviour changes between versions, and it will bite you.** `wait_for`'s
  `state: directory` was **removed** in the `ansible-core` 2.19 series — a config that was
  correct for years now fails hard on 2.21.4. This is the single most useful thing to know on
  this page, and it is why
  [troubleshooting.md §3](./troubleshooting.md) exists.

Verify what you actually have with `ansible --version`, and report *that* version when
something breaks.

---

## Installing

### Why does Molecule need a second package for Podman?

**Because the container drivers were split out of Molecule into a separate package,
`molecule-plugins`.** Molecule core has no idea how to talk to Podman, Docker or Vagrant; that
knowledge lives in drivers, and the drivers live in `molecule-plugins`.

`molecule-plugins` is **in no distribution repository anywhere** — not Fedora, not Ubuntu, not
Arch, not Homebrew, not Mageia. Even Arch's `molecule 26.9.0-1` package does not depend on it.
So every platform in this site runs one extra command:

```bash
pipx inject molecule molecule-plugins
```

Its current release is `26.9.28`, and it requires `molecule>=25.1.0` and Python `>=3.10`.

There is also one upgrade trap worth knowing: the old, separate per-driver packages
(`molecule-podman`, `molecule-vagrant`) are dead. If you upgrade Molecule and things break,
remove them.

See [install/index.md](./install/index.md).

### Is `molecule-ansible` a real package? Do I need `delegator`?

**No to both.** Neither exists as a dependency.

- **`molecule-ansible` does not exist.** `pypi.org/simple/molecule-ansible/` returns **404**.
  If a page tells you to install it, that page is wrong.
- **`delegator` is not a dependency.** It is an unrelated 2014 package that implements Ruby's
  `delegate.rb`. The confusion comes from Molecule's *class* name, `molecule.driver.Delegated`.

Both mistakes are in the wild because both look plausible.

### What if `molecule --version` crashes with `FileNotFoundError` about `ansible-config`?

**`ansible-core` is not installed.** Molecule 26.9 does not declare it as a dependency, so
`pip install molecule` succeeds and leaves you with a binary that cannot start. Install all three
together:

```bash
pipx install molecule ansible-core molecule-plugins
```

There is a second, equally common cause: the virtual environment's `bin/` folder is not on your
`PATH`. Full entry, with the real traceback, is
[troubleshooting.md §2](./troubleshooting.md).

---

## Running

### How long does a test take?

**This site does not quote a time, and neither should you quote one to someone else.** There is
no number in the verification transcript, because the host it ran on is not a machine most
readers have. If you measure yours, report your own seconds.

What *is* true, and explains most of what you will see:

- **The first run is dominated by downloading the container image.** That is a network
  transfer of hundreds of megabytes. Pull it yourself once and the first run starts instantly:
  `podman pull registry.access.redhat.com/ubi9/ubi-init:latest`.
- **Every run creates a container, and every run destroys it.** That is the design, not waste —
  see [Why does every run create and destroy a container?](#why-does-every-run-create-and-destroy-a-container).
- **The `idempotence` step runs your converge playbook twice, on purpose.** That is the step
  doing its job.

### Why does every run create and destroy a container?

**That is the design, and it is the point.** A fresh container per run means every run starts
from a known state, so a test cannot pass because of something a previous run left behind. It is
also why the destroy strategy is a first-class option — `molecule test --destroy never` keeps the
container so you can poke at it when something fails.

Full command reference: [`usage.md`](./usage.md).

### Why is my test green but nothing happened?

**Because `molecule test` exiting 0 does not mean your assertions ran.** A play that matches no
hosts is not a failure. It reports `skipping: no hosts matched`, `failed=0`, and the command
exits **0**.

This was measured on this site's own scenario. Every play skipped, not one assertion executed,
`SCENARIO RECAP … failed=0`, `echo $?` → `0`. The usual cause is a missing `groups: [molecule]`
key, because Molecule's Ansible groups default to `["ungrouped"]` and **there is no implicit
`molecule` group**.

The check, in one line: your `PLAY RECAP` must show `ok=N` with `N > 0`, and there must be
**zero** `no hosts matched` lines.

See [troubleshooting.md §1](./troubleshooting.md) — it is the first entry for a reason.

### Is `degraded` a failure?

**Usually not, and you should not make your test care.** `degraded` means systemd reached its
boot target but at least one unit failed. In a rootless container the usual culprits are
services that expect a full host: `dbus-broker.service`, `dbus.socket`, `systemd-resolved`,
`systemd-homed`, `systemd-firstboot`. They are artifacts of running rootless, not problems with
your test.

**Never assert that `is-system-running` equals `running`.** Assert on **your own unit** with
`ansible.builtin.service_facts` instead — that is what the canonical `verify.yml` does.

The one case where `degraded` *is* your fault: the failed units are `sys-kernel-config.mount`,
`sys-kernel-debug.mount` and `sys-kernel-tracing.mount`, which means `privileged: true`. Remove
it — it makes things worse, and it is advice you will find in Molecule's own driver docstring.

See [systemd-in-containers.md](./systemd-in-containers.md) and
[troubleshooting.md §6](./troubleshooting.md).

### My container starts but there is nothing in `podman logs`. What now?

**Empty logs are the normal result when systemd never started** — there was no process to write
any. The silence is the information. Look at the exit code and at whether the container was even
created.

The diagnostic sequence is in [troubleshooting.md §7](./troubleshooting.md).

---

## Writing your own tests

### How do I test idempotence?

**It is already a step in the sequence — the `idempotence` step.** You do not write it. Molecule
runs your converge playbook a second time and expects nothing to change. If a task reports
`changed` on the second pass, the step fails, and you have found a task that does work every
single run.

```console
molecule idempotence
```

Two honest notes:

- The spelling is **`idempotence`**. `molecule idempotency` does not exist.
- **Removing the step does not make your role idempotent** — it removes the only automated check
  you had. Keep it.

### What if my role needs a real database?

**Put the database in the container, or point at one you already have. There is no third option
that this site has verified.**

Two honest approaches:

1. **The `prepare` step.** `molecule.yml`'s `test_sequence` can include `prepare`, and
   `prepare.yml` runs *before* converge — that is where you install the database package and
   start its service, so your role has something to connect to by the time converge runs.
   `molecule init` does **not** scaffold `prepare.yml`; you write it. The default scaffolded
   sequence does **not** include `prepare` either, so you add that line yourself. The two tasks
   you need are ordinary Ansible modules — `ansible.builtin.package` to install, and
   `ansible.builtin.systemd_service` (or `ansible.builtin.service`) to start and enable it.
2. **An external service.** If you already run the database somewhere, give the role that host
   and let converge configure it. This is the wrong shape for a *test* — the test is no longer
   self-contained, and it is not reproducible — but it is often the pragmatic one.

**What this site does not do:** there is no verified recipe here for a real database server, and
we will not invent one. If you go down this road you are past what has been tested — expect to
debug, and share what you learn.

### How do I know my assertions are any good?

**Assert on the outcome, not on the fact that a task ran.** Three habits, in order of how much
they catch:

1. **Assert on state, not on output.** `"The marker file is there."` beats
   `"the copy command succeeded."`
2. **Assert on your own unit's state**, via `service_facts` — never on `is-system-running`
   (see [Is `degraded` a failure?](#is-degraded-a-failure)).
3. **Add a deliberately failing assertion once**, and confirm the test goes red. A test you have
   never seen fail is a test you have not tested.

See [authoring/writing-tests.md](./authoring/writing-tests.md).

### Where do the canonical files live?

**In exactly one place: [`REFERENCE-CONFIG.md`](./REFERENCE-CONFIG.md).** Every `molecule.yml`,
`converge.yml`, Containerfile and install command on this site is copied from there, with the
reasoning kept inline as a comment.

That rule exists because of a real incident on this project: seven pages independently re-typed
the same `molecule.yml`, and they drifted. If you are copying a config from anywhere, copy it
from there.

---

## Images and systemd

### Can I use an existing image instead of building one?

**Yes, and that is the recommended beginner path.** You need an image that has three things:
**systemd**, **Python**, and **`/sbin/init`**. This is the one that was verified:

```yaml
    image: registry.access.redhat.com/ubi9/ubi-init:latest
    # Supply chain: `latest` is a moving tag, so two runs are not the same build and the
    # registry decides what you execute. OPTIONAL: append `@sha256:<digest>` to pin it --
    # get one with `podman image inspect --format '{{index .Digest}}' <the image above>`.
```

Nothing to build, nothing to subscribe to, and it reached `running` with 0 failed units on a
first pull.

What will **not** work: `fedora:latest`, `debian:bookworm`, `ubuntu:24.04`, `ubi-minimal`, bare
`alpine` (no Python, and it will not work), and **every `quay.io/centos/centos:stream*` tag** —
Molecule's *own* systemd guide currently recommends one of those, and it cannot work, because
none of those images contain an `init`.

If you need a base image that is not on that list, build your own — the verified Debian
Containerfile is in [authoring/custom-images.md](./authoring/custom-images.md).

### Do I need `setsebool container_manage_cgroup true`?

**No.** That is **legacy** advice, and running it unthinkingly weakens your machine's security
for nothing.

On Podman 2.0 or newer, Podman labels a systemd-mode container `container_init_t`, which may
already write the cgroup filesystem. Measured on this site's host, with **SELinux**
(**Security-Enhanced Linux**) in **Enforcing** mode and the boolean **off**, systemd still
reached `running`.

**Only run it if you are reading actual AVC denials** in the host's audit log while the
container is starting. Podman's own documentation says the same: *"Only do this on systems
running older versions of Podman."*

Also do not edit `/etc/containers/policy.json` — a stock one reaches `running` untouched. Both
pieces of advice are Docker-era folklore. See
[troubleshooting.md §11](./troubleshooting.md).

### Do I need `--privileged` for systemd in a container?

**No — and it is actively harmful.** This is the most-repeated wrong piece of advice on the
internet about this topic, and it comes from Molecule's own `molecule-plugins` driver docstring,
which shows `privileged: true` in its example.

Measured: `privileged: true` makes the container reach `degraded` instead of `running`, because
it unmask `/sys` and three kernel-filesystem mount units then fail. It cannot help anyway —
rootless containers cannot have more privileges than the user who launched them.

Set `privileged: false`, or omit it. If one unit genuinely needs more rights, add **only**
`SYS_ADMIN`. See [systemd-in-containers.md](./systemd-in-containers.md).

### Which `molecule.yml` keys are actually required?

Four, and the honest status of each was measured rather than assumed:

| Key | Value | Status |
|---|---|---|
| `command` | `/sbin/init` | what runs as PID 1 |
| `override_command` | `true` | **required** when the image's own `CMD` is not an init; harmless otherwise |
| `systemd` | `always` | the **robust** choice. Required once `command:` is not literally an init. **Never `true`, never `false`.** |
| `privileged` | `false` | never `true` |
| `groups` | `[molecule]` | **required** or your plays match nothing — silently, and green |

You will read online that `systemd: always` and `override_command: true` are both "mandatory".
On `ubi9/ubi-init` they are not — the image's own `CMD` is already `/sbin/init`, and Podman's
`--systemd` already defaults to `true`. They are kept because they make the file independent of
the image, not because anything breaks without them.

Full table: [`REFERENCE-CONFIG.md` §2](./REFERENCE-CONFIG.md).

---

## Cost and CI

### Can I run this in CI, and does it cost money?

**Yes, and it costs $0** — if you stay inside the free tier of a free platform. The
recommended path is **GitHub Actions** with a **GitHub-hosted Linux runner** (`runs-on:
ubuntu-latest`), which is free for public repositories.

Three rules keep it at $0 forever:

- **Linux runners only.** `macos-*` and `windows-*` draw on a separate, much smaller pool — and
  macOS needs a virtual machine anyway.
- **Set a hard `timeout-minutes` bound.** A hung test must not be able to burn the allowance.
  This is the single most important line in the workflow file.
- **Do not use self-hosted runners.** They cost money, and that breaks the rule.
  **Do not push to a container registry** from the pipeline — registries have storage and
  bandwidth costs. Keep the image inside the job.

**This site deliberately quotes no minutes figure and no price.** GitHub's own billing page is
the authority, and a hard-coded number here would go stale. Read it yourself:
<https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions>

The full workflow file is in [authoring/ci.md](./authoring/ci.md).

---

## Housekeeping

### Why is there no `molecule add`, `molecule remove` or `molecule lint` any more?

**They were removed.** You will still find them in tutorials and blog posts. The replacements:

| Removed | Use instead |
|---|---|
| `molecule add <name>` | `molecule init scenario <name>` |
| `molecule remove <name>` | `rm -r molecule/<name>` |
| `molecule lint` | `ansible-lint`, run on its own |

`molecule init` has **exactly one** subcommand: `scenario`. See
[`REFERENCE-CONFIG.md` §9.3](./REFERENCE-CONFIG.md).

### Is there a built-in linter?

**No.** Linting is `ansible-lint`, a separate program. The sample workflow in
[authoring/ci.md](./authoring/ci.md) runs it as its own step. If a page tells you to run
`molecule lint`, it predates the removal.

### Why do I get `Missing playbook` for `cleanup`?

**Nothing is broken — it is a warning.** The `cleanup` step is in your `test_sequence`, but
`molecule init` does not scaffold a `cleanup.yml` for it. Ship the file (an empty stub is
enough) or drop `cleanup` from the sequence.

The [troubleshooting entry](./troubleshooting.md) also explains the asymmetry that makes this
counter-intuitive: `cleanup.yml` is always safe to ship, while `create.yml` and `destroy.yml`
are the opposite.

### Can I keep the container after a failed run to look at it?

**Yes.**

```bash
molecule test --destroy never
```

Or run the steps individually and stop at `converge` — `molecule create`, `molecule converge`,
`molecule verify`, `molecule destroy`. That is the normal debugging loop, and it avoids
re-pulling and re-creating the container on every attempt. `molecule test` re-runs everything
from the top every time, which is why it is the wrong tool for iteration.

See [usage.md](./usage.md).

---

## Questions we get wrong in the docs

One entry, because it is the one that matters.

### "A green `molecule test` means my test passed."

**No. It does not. And documentation that implies otherwise is wrong — including ours, once.**

The claim that broke: a green `molecule test` is evidence that the assertions executed. It is
not. A play that matches no hosts is not a failure — it reports `skipping: no hosts matched`,
`failed=0`, and the command **exits 0**.

This is not a warning about other people's docs. It is what happened here. A `molecule.yml` on
this site — the crux example, the file the whole documentation project was built to prove —
omitted one key. Every play reported `skipping: no hosts matched`. **Zero assertions executed.**
`SCENARIO RECAP … failed=0`. `echo $?` → `0`. Three independent expert reviews had approved that
configuration, because it is syntactically perfect and semantically plausible and completely
inert. There is no error to read. **Only running it caught it.**

Two rules came out of it, and this site now holds itself to both:

1. **The `PLAY RECAP` must show `ok=N` with `N > 0`, and there must be zero
   `skipping: no hosts matched` lines.** That is the check, and it is published at
   [`REFERENCE-CONFIG.md` §2d](./REFERENCE-CONFIG.md).
2. **A claim about Ansible or Molecule behaviour is not verified until it has been executed.**
   A "verified" marker on a config file means somebody ran it. Not that it parsed.

The general lesson, which applies to every answer on this site: **reading, reviewing and
linting cannot find a defect that only exists at run time.** Where a claim here is labelled
`UNVERIFIED`, that label is doing real work.

---

## Next

- **Something is broken and you have the error message** —
  [`troubleshooting.md`](./troubleshooting.md).
- **Something is broken and you do not** — [`preflight.md`](./preflight.md), one read-only
  script.
- **A word in this answer you did not know** — [`glossary.md`](./glossary.md).
- **Background, before more questions** — [`concepts/how-molecule-works.md`](./concepts/how-molecule-works.md).
- **Ready to write your own** — [`authoring/index.md`](./authoring/index.md).
- **Ready to run it** — [`quickstart.md`](./quickstart.md).

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../assets/ATTRIBUTION.md`](../assets/ATTRIBUTION.md). Product and distribution names are used
to identify the software being discussed, not to imply endorsement.

---

## Sources

This page introduces no new facts. Each answer cites the page that carries the evidence:

- <https://pypi.org/project/molecule/> — Molecule `26.9.0`, released 2026-09-22, requires Python `>=3.10`; MIT licence
- <https://pypi.org/project/molecule-plugins/> — `molecule-plugins` `26.9.28`, requires `molecule>=25.1.0`; in no distribution repository
- <https://docs.ansible.com/projects/molecule/> — *"pip is the only supported installation method"*; the removal of `molecule add` / `remove` / `lint`
- <https://github.com/ansible/molecule> — the driver list (`docker`, `containers`, `gce`, `azure`, `ec2`, `openstack`, `vagrant`, `podman`, `default`); the `ungrouped` default in `molecule/provisioner/ansible.py`
- <https://github.com/ansible/molecule/blob/main/src/molecule/data/init-scenario.yml> — the scaffolded playbooks, the default `test_sequence`, and the fact that `cleanup.yml` is not among the five
- <https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/wait_for_module.html> — the valid `state` values, and the removal of `directory`
- <https://github.com/containers/podman/blob/main/troubleshooting.md> — §1 (volume `Permission denied`), §8 (the `container_manage_cgroup` boolean, *"Only do this on systems running older versions of Podman"*), §16 (cgroup v2 on old systemd), §26 (missing cgroup controllers)
- <https://docs.podman.io/en/latest/markdown/podman-run.1.html> — `--systemd`, the rootless-privilege note
- <https://molecule.readthedocs.io/guides/systemd-container> — Molecule's systemd guide, source of the CentOS Stream image bug and the `group_vars` trap
- <https://github.com/ansible-community/molecule-plugins/tree/main/src/molecule_plugins/podman/> — the driver whose own example sets `privileged: true`
- <https://docs.ansible.com/projects/ansible/latest/collections/containers/podman/podman_container_module.html> — the `podman_container` module the podman driver uses; its `systemd` parameter is *"Run container in systemd mode. The default is true."*
- <https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/systemd_service_module.html> · <https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/package_module.html> — the two modules a `prepare.yml` needs
- <https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions> — the authoritative Actions cost model; deliberately not quoted on this site
- The measured claims — [`../examples/VERIFICATION.md`](../examples/VERIFICATION.md), a live run on Fedora 44 with podman 5.8.7, molecule 26.9.0, `molecule_plugins` 26.9.28 and ansible-core 2.21.4
