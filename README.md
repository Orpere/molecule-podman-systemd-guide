# Molecule + Podman + systemd — a beginner's guide to testing your own Ansible

**Test your Ansible roles, playbooks and collections automatically — in Podman containers, on
Fedora, Ubuntu, Arch, macOS or Mageia, for free. Written for someone who has never used
Molecule, Podman or Ansible.**

[![Ansible](assets/badges/badge-ansible.svg)](https://docs.ansible.com/)
[![systemd](assets/badges/badge-systemd.svg)](https://systemd.io/)
[![CNCF](assets/badges/badge-cncf.svg)](https://www.cncf.io/)
[![Fedora](assets/badges/badge-fedora.svg)](docs/install/fedora.md)
[![Ubuntu](assets/badges/badge-ubuntu.svg)](docs/install/ubuntu.md)
[![Arch](assets/badges/badge-arch.svg)](docs/install/arch.md)
[![macOS](assets/badges/badge-macos.svg)](docs/install/macos.md)
[![Mageia](assets/badges/badge-mageia.svg)](docs/install/mageia.md)
[![Mermaid](assets/badges/badge-mermaid.svg)](https://mermaid.js.org/)
[![Markdown](assets/badges/badge-markdown.svg)](https://commonmark.org/)

---

```mermaid
flowchart LR
  R["your Ansible role"] --> S["Molecule scenario"]
  S -->   P["container, systemd is PID 1"]
  P --> V["verify.yml asserts it works"]
  V --> D["container destroyed"]
```

**What this shows:** one `molecule test` run takes your Ansible role, puts it in a disposable
scenario, runs it inside a Podman container in which `systemd` is the first process, asserts
the result, and throws the container away.

A text description of the diagram, in reading order, for anyone who cannot see it. It starts on
the left with the thing you already have: an Ansible role, playbook or collection. That feeds
into a *Molecule scenario*, which is a folder holding your settings and your playbooks — the
unit of work you are about to build. The scenario tells Podman to start a container from an
image in which `systemd` is the very first process, so the container behaves like a real Linux
machine rather than a bare process sandbox. Inside it, your role is applied. Then `verify.yml`
runs your own assertions — is the service active, is the file there, is the port listening.
That is the step that decides pass or fail. Finally the container is destroyed, so nothing is
left behind and the next run starts from scratch.

---

## Why this guide exists

You will find a lot of Molecule tutorials on the internet. Most of them are wrong about the
things that matter, in three specific ways: they were written for a version of Molecule that
no longer exists, they assume Docker rather than Podman, and they tell you to run `systemd` in a
container with `--privileged` — which does not work, and which is a documented error in
Molecule's own Podman driver. This guide is built from primary sources and from running the
examples on real hardware, and it says out loud where the folklore is and why it is wrong.

| The claim you will read online | What is actually true |
|---|---|
| "Molecule version 6" or "Molecule 7" | Molecule uses **calendar versioning** (`CalVer`). The current release is **`26.9.0`**. There is no v6 or v7. |
| The Podman connection plugin is in `community.docker` | It is **`containers.podman.podman`**, from the `containers.podman` collection. `community.docker` has no Podman plugin. |
| Molecule ships a `podman` driver | The `podman` driver is in a **separate package**, `molecule-plugins`, which is in no distribution's repository. |
| `molecule add`, `molecule remove`, `molecule lint` | **All removed.** Use `molecule init scenario`, `rm -r`, and standalone `ansible-lint`. |
| Point Ansible at the Podman socket with `DOCKER_HOST` | The Podman connection plugin drives the **`podman` command-line tool**, not a socket. There is no `DOCKER_HOST` in this path. |
| `systemd` in a container needs `--privileged` | It does not, and it **makes things worse**: privileged mode makes three kernel mounts fail, and the container lands in `degraded` instead of `running`. Leave `privileged: false`. |
| You must `setsebool container_manage_cgroup true` and edit `policy.json` | Neither is needed on Podman 2.0 or newer. Both are Docker-era folklore. |
| Molecule's `default` driver creates your container | It creates **nothing**. It is called *default* because it is the fallback, not because it does a default thing. |

The full, evidence-backed list of eight myths is in
**[systemd in containers](docs/systemd-in-containers.md)**, and there is a
[one-paragraph summary](docs/troubleshooting.md) in the troubleshooting reference.

---

## The 60-second orientation

Four concepts. That is genuinely all you need to start.

**1. Molecule is the test harness.** You give it some Ansible content and it builds a
throwaway machine, applies your content to it, checks the result, and destroys the machine. You
do not write a test framework; you write a `verify.yml` with assertions, which is ordinary
Ansible YAML.

**2. A scenario is one disposable test environment.** It is a folder — conventionally
`molecule/default/` — holding a settings file, a `converge.yml` that applies your work, and a
`verify.yml` that asserts the outcome. One project can hold several scenarios; one is enough to
start.

**3. Podman is the container engine that builds the machine.** A container is a process, or a
few processes, that the operating system shows you as its own machine while sharing your
computer's kernel. It starts in about a second and can be thrown away instantly. Podman runs
without root privileges and needs no background daemon, which is why it is the engine this site
uses.

**4. `systemd` inside the container is the point.** `systemd` is the program that starts and
supervises services on a Linux machine. Almost no container image contains it, so a role whose
whole job is to install and start a service cannot be tested in a stock container. Getting
`systemd` running as the first process inside a container is the interesting part of this whole
subject — and the part most guides get wrong.

> **A warning worth reading twice.** There is a configuration that looks perfect, passes
> review, and reports **success while asserting nothing at all**. Molecule can exit `0` with
> every play reporting `no hosts matched`. It happened to us, and it is why
> [this page explains it](docs/concepts/how-molecule-works.md#10-verify). The one-second habit that
> catches it is in [the troubleshooting reference](docs/troubleshooting.md).

---

## Supported platforms

All five are documented with exact, copy-pasteable commands and the version each one gives you.
**$0, no payment method, ever.**

| Platform | Page | Container engine | The honest caveat |
|---|---|---|---|
| **Fedora 44** | [Install](docs/install/fedora.md) | `podman` 5.8.1 | **The cleanest path, and the one this site was live-verified on.** |
| **Ubuntu 26.04 LTS** | [Install](docs/install/ubuntu.md) | `podman` 5.7.0 | AppArmor may block user namespaces; the page shows the one-line check. |
| **Ubuntu 24.04 LTS** | [Install](docs/install/ubuntu.md) | `podman` 4.9.3 | Podman from **2022**. Works, but stale. |
| **Arch Linux** | [Install](docs/install/arch.md) | `podman` 6.1.2 | The most current platform, and the only Linux one with a native Molecule package. |
| **macOS, Apple Silicon** | [Install](docs/install/macos.md) | `podman` 6.1.2, in a virtual machine | Containers run in a Linux **VM**, not natively. Intel Macs are unsupported. |
| **Mageia 10** | [Install](docs/install/mageia.md) | `podman` 5.7.1 | The weakest platform. Three workarounds, one honestly labelled unverified. |

Also needed on every Linux platform: [rootless Podman setup](docs/install/rootless-podman.md) —
what `subuid` and `subgid` are, and how to set them. Check your machine first with the
[ten-second pre-flight script](docs/preflight.md); it is read-only and never uses `sudo`.

---

## Start here

Read these in this order. Nothing else is required.

1. **[How Molecule works](docs/concepts/how-molecule-works.md)** — the mental model, with no
   commands in it. Five minutes, and every later command makes sense.
2. **[Install your platform](docs/install/index.md)** — pick your row: [Fedora](docs/install/fedora.md) ·
   [Ubuntu](docs/install/ubuntu.md) · [Arch](docs/install/arch.md) ·
   [macOS](docs/install/macos.md) · [Mageia](docs/install/mageia.md)
3. **[Pre-flight check](docs/preflight.md)** — ten seconds, read-only, free. Tells you exactly
   which thing is missing instead of letting you find out halfway through a test.
4. **[Quickstart](docs/quickstart.md)** — your first green `molecule test`, about 15 minutes
   *(an unmeasured estimate, not a timed figure)*, four files and one command.
5. **[systemd in containers](docs/systemd-in-containers.md)** — the crux. The four keys that
   matter, the flag-by-flag verdict table, and the eight myths.
6. **[Build your own workflows](docs/authoring/index.md)** — when it is time to test *your*
   role rather than the example: [your first scenario](docs/authoring/your-first-scenario.md) ·
   [project layout](docs/authoring/project-layout.md) ·
   [writing tests](docs/authoring/writing-tests.md) ·
   [custom images](docs/authoring/custom-images.md) ·
   [multi-scenario](docs/authoring/multi-scenario.md) ·
   [CI](docs/authoring/ci.md)

Two runnable projects you can execute right now, without writing anything:
[`examples/quickstart/`](examples/quickstart/) and
[`examples/systemd-unit/`](examples/systemd-unit/).

---

## What you can build here

| Example | What it proves | Run it |
|---|---|---|
| [`examples/quickstart/`](examples/quickstart/) | The toolchain works: create a container, write a file, assert on it, destroy the container. | `cd examples/quickstart && molecule test` |
| [`examples/systemd-unit/`](examples/systemd-unit/) | `systemd` is PID 1 in a rootless Podman container, and a `.service` unit the test installed and started is **active**. | `cd examples/systemd-unit && molecule test` |

Both exit `0` with the assertions genuinely executed. The captured transcripts, and every defect
those runs found in this documentation, are in
[`examples/VERIFICATION.md`](examples/VERIFICATION.md).

---

## Status — what is verified, and what is not

We would rather tell you than let you find out.

### ✅ Verified by execution, on real hardware

The two examples in `examples/` were run end to end on **Fedora 44, x86-64, rootless Podman
5.8.7, SELinux Enforcing, cgroup v2**, against **Molecule 26.9.0** (`molecule-plugins` 26.9.28,
`ansible-core` 2.21.4, `containers.podman` 1.20.2, Python 3.14). `molecule test` exited `0`
with the assertions actually running — verified by the `ok=` count in the verify recap, not by
the exit code. That run also confirmed the cgroup v2 and SELinux claims on
[the systemd page](docs/systemd-in-containers.md), and the pre-flight script in
`docs/scripts/molecule-preflight.sh` was executed on the same host in both states.

**And that run found seven real bugs in this documentation**, which are now fixed. We are naming
them because a guide that hides its own errors is not telling you the truth about its accuracy.
The list is in [`examples/VERIFICATION.md`](examples/VERIFICATION.md). The worst of them:

- **A silent false pass.** The canonical `molecule.yml` produced `no hosts matched` for every
  play, and `molecule test` **still exited 0**. Not one assertion ran. Three independent
  reviews had already approved that file. Only execution caught it. The fix is now in every
  canonical config, and ["did my test actually run?"](docs/troubleshooting.md) is a
  first-class entry in the troubleshooting reference.
- **A documented flag that breaks the run.** Shipping `create.yml` and `destroy.yml`, as the
  reference material instructed, **overrides the driver's own create playbook** — so no
  container is ever built and converge dies with `Container 'instance' not found`. Corrected,
  and the reason is now on the page.
- **A fatal option value.** `wait_for: state: directory` is not a valid state on
  `ansible-core` 2.21.
- Plus a `command` task that could never produce the output the same page promised, a scenario
  labelled "no systemd" that set `systemd: always`, a `cleanup` step with no `cleanup.yml`, and
  a folder layout that is impossible to create.

**Two claims the execution refuted**, which we had asserted too strongly and have softened: that
`systemd: always` is strictly *required* (it is the robust choice, and it becomes genuinely
required the moment your command is not literally an init), and that `override_command: true` is
always mandatory (it is required exactly when the image's own start command is not an init).

### 📖 Documented from primary sources, not executed here

The install pages for **Ubuntu, Arch, macOS and Mageia**, and the **multi-scenario** authoring
page, were written from package-manager metadata, the drivers' own source, and the upstream
documentation. They are sourced line by line, but **nobody has run them on those four
platforms**, and we will not pretend otherwise. Every claim on those pages that the corpus could
not confirm is labelled **UNVERIFIED** in place. If you find one that is wrong, that is a
documentation bug and we want the report.

### 🧭 Deliberately out of scope

Docker, Kubernetes, Terraform, cloud instances, and testing anything that is not your own
Ansible content. Molecule supports those; this guide does not cover them.

---

## Licence and attribution

**This repository has no licence file yet.** The documentation text, and every original
graphic in `assets/` — 20 icons, 3 illustrations, 10 badges and the stylesheet — were authored
for this project and released under
**[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)** (public domain
dedication). The full per-file provenance record, with source URLs and licences for every mark,
is in [`assets/ATTRIBUTION.md`](assets/ATTRIBUTION.md). Where a licence decision is still open,
it is recorded there rather than assumed.

**No maintainer is named**, because none has been designated. If you want to be one, the
honest route is to open an issue saying so.

### Third-party marks

Ansible®, Podman, Molecule, systemd, Fedora, Ubuntu, Arch Linux, macOS, Mageia, Docker, Mermaid
and Markdown are the property of their respective owners and are used here
nominatively. All product names, logos and brands are the property of their respective owners;
their use does not imply endorsement. **This site is not affiliated with or endorsed by the
Fedora Project, the Arch Linux Project, Red Hat, Inc., Canonical Ltd., or The Linux
Foundation.** The Molecule logo, where used, is displayed unmodified under CC BY-ND 4.0. No
Apple graphic and no Fedora Infinity logo appears anywhere in this repository — see
[`assets/ATTRIBUTION.md`](assets/ATTRIBUTION.md) for the decisions and the reasons.

### Contributing

There is no contribution process yet, and inventing one would be worse than saying so. What is
true today:

- **Every page is written from a rule set**, and the rules are public: the information
  architecture in [`docs/STRUCTURE.md`](docs/STRUCTURE.md) and the graphics contract in
  [`docs/VISUAL-SYSTEM.md`](docs/VISUAL-SYSTEM.md).
- **Every code artifact has exactly one home**, [`docs/REFERENCE-CONFIG.md`](docs/REFERENCE-CONFIG.md).
  To change a `molecule.yml`, change it there first. Pages quote it; they never re-type it.
- **The highest-value contribution is an execution report.** A transcript of a run on a platform
  not in the verified list above, showing what actually happened, is worth more than a
  paragraph of prose. So is a correction with a source.
- Report anything that contradicts the folklore table above. If the internet is right and this
  guide is wrong, we want to know and fix it.

---

## Next

- **Never used Ansible before?** → [Docs home](docs/index.md), then
  [the quickstart](docs/quickstart.md).
- **Already installed?** → [Quickstart](docs/quickstart.md) — your first green test, about 15
  minutes, $0.
- **Something is broken?** → [Troubleshooting](docs/troubleshooting.md).
- **A word you do not know?** → [Glossary](docs/glossary.md).
