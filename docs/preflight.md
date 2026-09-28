# Pre-flight check — is this machine ready?

> **You are here:** [Docs home](./index.md) → [Install](./install/index.md) → **Pre-flight** → [Quickstart](./quickstart.md)

**What you will be able to do:** run one read-only script that tells you — in about ten
seconds — whether this machine can run Molecule, Podman and systemd, and exactly which check
to fix if it cannot.

You do not need this page if everything already works. You need it if you are about to start
installing, or if something failed and you want to know which of the seven things is wrong.

**This page costs nothing.** The script is free and offline. It never installs a package and
never asks for `sudo`. It only reads — with one bounded exception, spelled out here rather than
buried: it calls `podman info`, and `podman` may initialise its own storage directory
(`~/.local/share/containers` by default) on first use. Nothing outside that directory is read
or changed.

---

## What this checks

The script asks eight questions, grouped into seven numbered sections. Here is each one and
*why it exists* — one plain sentence each.

| # | Check | Why it exists | Fix it on |
|---|---|---|---|
| 1 | **Control groups are version 2** | systemd, running as process 1 inside a container, must be able to write to the modern *cgroup v2* kernel hierarchy, and Podman 6.0 removed cgroup v1 support entirely. | [Install index](./install/index.md) |
| 2 | **Podman is on your `PATH`** | Podman is the container engine that will actually create your test container. `PATH` is the list of folders your shell searches when you type a command name. | [Install index](./install/index.md) |
| 3 | **Podman runs rootless** | Running as an unprivileged user, not `root`, is how container security works on a normal Linux desktop, and it is the configuration every result in this project was measured under. | [Rootless Podman](./install/rootless-podman.md) |
| 4 | **`newuidmap` and `/etc/subuid` + `/etc/subgid` exist** | A rootless container still needs to act as *many* user IDs inside itself; these three things provide that range, and without them rootless Podman cannot start. | [Rootless Podman](./install/rootless-podman.md) |
| 5 | **SELinux state** | SELinux (Security-Enhanced Linux) is a mandatory-access-control system that can block a container from doing things it should be allowed to do — this check tells you whether it is enforcing, so you can predict the symptoms. | [Troubleshooting](./troubleshooting.md) |
| 6 | **Python is 3.10 or newer** | Molecule is a Python program and declares `>=3.10` as its minimum; an older interpreter will refuse to install or fail at import time. | [Install index](./install/index.md) |
| 7 | **Molecule and the `podman` driver are present** | The `podman` *driver* is the piece that teaches Molecule how to manage containers. It is not in Molecule itself and not in your distribution's package repository. | [Install index](./install/index.md) |
| 8 | **The `containers.podman` Ansible collection is installed** | This collection holds the connection plugin Ansible uses to run commands inside the container. Molecule installs it for you, so this one only warns. | [Troubleshooting](./troubleshooting.md) |

> **On check 8 — a Fully Qualified Collection Name (FQCN).** Ansible collections are named
> `namespace.collection`, and each plugin inside them has a name too, so the full identifier
> looks like `namespace.collection.plugin`. The one you need here is
> **`containers.podman.podman`**. It comes from the **`containers.podman`** collection — *not*
> from `community.docker`, which ships only the `docker`, `docker_api` and `nsenter` plugins and
> has no Podman plugin at all.

---

## Run it

### Option A — download the file, read it, then run it (no placeholder to fill in)

**This is the option to use.** Open [`scripts/molecule-preflight.sh`](./scripts/molecule-preflight.sh),
save it as `molecule-preflight.sh` in the directory you are working in, then:

```bash
less molecule-preflight.sh    # read it first - it is short, and it only reads
bash molecule-preflight.sh
```

There is **no URL and no placeholder to substitute**: you already have the file in front of
you, because you are reading this page. Once it is saved you need no network at all.

You should see the script's banner and then seven numbered sections scroll past, ending in a
`RESULT:` line.

### Option B — fetch it over the network (pin a commit, then read it)

If you would rather not save the file by hand, download it first, read what arrived, and only
then run it:

```bash
curl -fsSL "$REPO_BASE/<COMMIT-SHA>/docs/scripts/molecule-preflight.sh" -o molecule-preflight.sh \
  && less molecule-preflight.sh \
  && bash molecule-preflight.sh
```

**Why it is written this way:** `bash <(curl ...)` hands whatever bytes the server returns
straight to an interpreter — a typo'd base URL, a mirror, or a hijacked host turns into
arbitrary code execution with no review step and no undo. Pinning `<COMMIT-SHA>` fixes the
bytes to one reviewed revision of this repository, and the download-then-read step means you
see them before they run. The script is short and read-only, so reading it costs ten seconds.

`REPO_BASE` is this site's raw-content base URL — the address that serves a file straight out
of the repository, with no web page around it. `<COMMIT-SHA>` is the commit you are reading
this page at, and is worth copying literally: a branch name such as `main` moves under you.

You should see the same banner and the same seven sections, because it is the same file.

### Option C — run it again later, quietly

```bash
bash molecule-preflight.sh --quiet
```

`--quiet` silences the report body — the banner, the seven sections, the `PASS`/`WARN`/`FAIL`
lines and the separator. It does **not** silence the verdict, because the summary line and the
exit code are the same contract a CI job or a wrapper script reads. You should get exactly one
line, for example:

```console
RESULT: READY - every check passed
```

### Optional — run the pre-flight in CI

**This is an opt-in addition, not part of the canonical workflow.** The workflow in
[`REFERENCE-CONFIG.md` §8.2](./REFERENCE-CONFIG.md) is deliberately minimal: a hosted runner is a
known-good machine, so there is nothing for a readiness check to discover. Add this step only
when you want a misconfigured self-hosted-equivalent runner to fail loudly instead of failing
confusingly — and note it only works if `docs/scripts/molecule-preflight.sh` exists in *your*
repository, which it does not if you copied that workflow into a fresh project:

```yaml
      - name: Pre-flight check (opt-in addition, not in the canonical workflow)
        run: bash docs/scripts/molecule-preflight.sh --quiet
```

`--quiet` is the right mode here: the exit code is what the job needs, and a full eight-section
report would bury the real failure in the CI log.

---

## How to read the output

Every check prints one of three words. Nothing else matters.

| Word | Meaning | Does it stop you? |
|---|---|---|
| `PASS` | This check succeeded. | No. |
| `WARN` | It is not ideal, but you can continue and probably will never notice. | No. |
| `FAIL` | Something required is missing or broken. | **Yes.** Fix it before going further. |

The script also reports its result through an *exit code* — the number a program hands back to
your shell to say how it went. `0` means ready. `1` means at least one `FAIL`. `2` means the
script cannot run on this operating system at all.

Two things the script will never do, so you do not have to wonder: it will never print a
`FAIL` for SELinux, and it will never print a `WARN` you have to act on for the
`containers.podman` collection.

---

## What a healthy run looks like on your platform

> **Honesty note about this table.** Only the Fedora 44 row is a machine that actually ran the
> script — the full captured output is in the next section. The other four rows are the result
> you should expect, assembled from your distribution's own package versions and from the
> script's own logic. Treat them as targets, not as transcripts.

| Platform | Podman version you should see | What the SELinux section says | Watch for |
|---|---|---|---|
| [**Fedora 44**](./install/fedora.md) | 5.8.1 or newer | `PASS  SELinux is Enforcing` | Nothing. This is the configuration every result in this project was measured on. |
| [**Ubuntu 26.04 LTS**](./install/ubuntu.md) | 5.7.0 | `PASS  SELinux is Disabled` — Ubuntu uses AppArmor, not SELinux | Nothing unusual. |
| [**Ubuntu 24.04 LTS**](./install/ubuntu.md) | 4.9.3 | `PASS  SELinux is Disabled` | Two `WARN`s are normal: podman older than 5, and possibly a Python or Molecule warning. 24.04 also has an AppArmor restriction that can break `podman run` — see [the Ubuntu page](./install/ubuntu.md). |
| [**Arch Linux**](./install/arch.md) | 6.1.2 | `PASS  SELinux is Disabled` | A cosmetic `Failed to add pause process to systemd sandbox cgroup` warning from `crun` can appear. It is harmless — do not try to fix it. Rootless ID mapping is already done for you, so groups 3 should be three `PASS` lines with no action. |
| [**macOS (Apple Silicon)**](./install/macos.md) | 5.x or 6.x | `PASS  not applicable on macOS` | Group 1 will not really test anything on macOS — it only tells you to run the check *inside* the Podman virtual machine. Groups 3 and 4 report `not applicable`. See [the macOS page](./install/macos.md). |
| [**Mageia 10**](./install/mageia.md) | 5.7.1 | `PASS  SELinux is Enforcing` | Mageia has no `pipx` package and no `uidmap` package, so a `FAIL` on `newuidmap` is a real possibility. The rootless ID mapping is marked **UNVERIFIED** on Mageia. See [the Mageia page](./install/mageia.md). |

---

## Real output from a Fedora 44 host

A genuine run, captured on Fedora Linux 44, kernel cgroup v2, SELinux **Enforcing**, podman
5.8.7, Python 3.14.7. Compare it to your own output — the shape should be identical.

### Run A — before Molecule is installed (the state most readers start in)

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

That `FAIL` is the expected result if you skipped the Molecule install step. It is not a
problem with your machine. Install Molecule, then run the script again.

### Run B — the same host, with Molecule 26.9.0, the `podman` driver and `containers.podman` 1.20.2 on `PATH`

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

**This is what you are aiming for:** `RESULT: READY` and exit code `0`.

---

## A trap to avoid while you are here

There is a command floating around blogs and forum answers that will break on Podman 5.8.7:

```text
podman info --format '{{.Host.Security.SelinuxEnabled}}'
```

**Do not run it.** On Podman 5.8.7 that field does not exist and the command fails with
*"can't evaluate field SelinuxEnabled in type define.SecurityInfo"*. The form that does work is
`{{json .Host.Security}}`, reading `.selinuxEnabled`.

This is exactly why the pre-flight script asks SELinux a different question. It runs
`getenforce` instead, which reads the state from the operating system and has no such
problem. **Trust the script's SELinux line; ignore every blog that shows the `podman info`
version.** See [Troubleshooting](./troubleshooting.md).

---

## If a check failed

| The `FAIL` line says… | What it means | Go to |
|---|---|---|
| `cgroup v1 is in use` | The kernel is using the old control-group hierarchy, which systemd-in-container cannot use. | [Install index](./install/index.md), then [Troubleshooting](./troubleshooting.md) |
| `podman is not on your PATH` | The container engine is not installed. | [Install index](./install/index.md) |
| `podman is installed but 'podman info' failed` | Podman is there but the engine is not working — on Ubuntu this is usually AppArmor. | [Ubuntu](./install/ubuntu.md), then [Troubleshooting](./troubleshooting.md) |
| `newuidmap is missing` | The package that provides user-ID mapping is absent. | [Rootless Podman](./install/rootless-podman.md) |
| `/etc/subuid has no entry for <user>` | Your user has no subordinate user-ID range allocated. | [Rootless Podman](./install/rootless-podman.md) |
| `/etc/subgid has no entry for <user>` | Same problem for group IDs. | [Rootless Podman](./install/rootless-podman.md) |
| `python3 <version> is too old` | Python is older than 3.10. | [Install index](./install/index.md) |
| `molecule is not on your PATH` | Molecule is not installed, or you have not reloaded your shell since `pipx ensurepath`. | [Install index](./install/index.md) |
| `the 'podman' driver is missing` | `molecule-plugins` is not installed. The script prints the exact command. | [Install index](./install/index.md) |
| `molecule-preflight: unsupported operating system` | The script only runs on Linux and macOS. | [Install index](./install/index.md) |

If a term in one of these messages is unfamiliar, [the glossary](./glossary.md) expands it.

---

## Re-run it

Run it as often as you like; it is read-only, so it cannot break anything. Once now, to see the
shape of the output. Once after installing, to confirm every `FAIL` is gone. And any time
something breaks later, to prove the host is still healthy and the problem is somewhere else.

---

## Next

- **Every check passed** → [Quickstart](./quickstart.md). It is a fifteen-minute first run, and
  it ends with a green `molecule test`.
- **Still failing** → [Install index](./install/index.md) to pick your platform, or
  [Rootless Podman](./install/rootless-podman.md) if the failures are in group 3.
- **You want to understand the tool before running it** →
  [How Molecule works](./concepts/how-molecule-works.md).

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../assets/ATTRIBUTION.md`](../assets/ATTRIBUTION.md). Distribution and product names are used
to identify the software being discussed, not to imply endorsement.

---

## Sources

- <https://docs.ansible.com/projects/molecule/> — Molecule documentation home
- <https://pypi.org/project/molecule/> — Molecule on PyPI: `26.9.0`, released 2026-09-22, requires Python `>=3.10`
- <https://pypi.org/project/molecule-plugins/> — the Podman driver package; no distribution ships it
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py> — the podman driver source
- <https://github.com/ansible/molecule/blob/main/src/molecule/data/init-scenario.yml> — the scaffolding playbook
- <https://docs.ansible.com/projects/ansible/latest/plugins/connection/podman.html> — the `containers.podman.podman` connection plugin
- <https://galaxy.ansible.com/collection/containers/podman> — the `containers.podman` collection
- <https://docs.podman.io/en/latest/markdown/podman-run.1.html> — `podman run`, including `--systemd`
- <https://docs.podman.io/en/latest/markdown/podman-machine-ssh.1.html> — the in-VM checks used on macOS
- Internal, reproducible: the captured output above is quoted from
  [`REFERENCE-CONFIG.md` §6.4](./REFERENCE-CONFIG.md); the script itself is
  [`scripts/molecule-preflight.sh`](./scripts/molecule-preflight.sh)

---

## Does the script still behave? A self-test you can run

The pre-flight script is the one piece of executable code in this guide, so it has its own
acceptance test — free, offline, and needing nothing but `bash`:

```bash
bash docs/scripts/test-preflight.sh
```

It checks the things that have actually broken during authoring:

| It asserts | Because |
|---|---|
| the script parses | a syntax error would make every run fail |
| it still reaches its `RESULT:` verdict when `$USER` is unset | it once died mid-report under `set -u`, silently truncating before the checks that matter (see `PLAN.md` Trace T3) |
| it still reaches `RESULT:` with an empty environment (`env -i`) | cron, systemd units and some CI runners look like this |
| `--quiet` still prints exactly one line — the verdict — and still exits `0` or `1` | CI gates on that exit code, so the verdict must survive the quiet flag |
| it creates nothing outside Podman's own XDG storage directories | it is documented as read-only, and the docs now say precisely what "read-only" excludes |

Expected result on a healthy host: every line `PASS`, then `7 passed, 0 failed`.
