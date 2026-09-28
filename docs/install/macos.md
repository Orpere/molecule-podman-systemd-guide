# macOS on Apple Silicon — install Molecule and Podman

> **You are here:** [Docs home](../index.md) → [Install](./index.md) → **macOS** → [Quickstart](../quickstart.md)

**What you will be able to do:** run Molecule and systemd-in-a-container on an Apple Silicon
Mac, where the container engine is a small Linux virtual machine and almost every command from
the Linux pages is replaced.

**This page is different from the other four.** On Linux, Podman runs on your machine. On macOS,
**Podman does not run on your machine at all** — it runs inside a virtual machine, and the
`podman` command on your Mac is a remote control that forwards into it. Read section 1 before
you install anything. **All of it is free:** the Podman installer and Homebrew are both free and
open source, ask for no payment method, and nothing here needs a card.

---

## Read this first: Intel Macs are not supported

> ### If you have an Intel Mac, there is no supported path. Stop here.
>
> This is not a difficult install. It is an unsupported platform, and three independent
> upstream decisions have closed the door:
>
> 1. **Podman 6.0 removed Intel Mac support outright.** From the Podman 6.0.0 release notes,
>    verbatim: *"Support for running on Intel Macs has been removed."*
> 2. **Homebrew moved macOS Intel to Tier 3 in September 2026**, with no new pre-compiled
>    bottles. Homebrew's own support-tiers documentation describes Tier 3 as supported on a
>    best-effort basis only.
> 3. **The Homebrew `podman` formula is hard-locked to Apple Silicon**, carrying
>    `depends_on arch: :arm64`. `brew install podman` is refused on an Intel Mac regardless of
>    anything else.
>
> All three would have to change. We are not going to give you an inferred recipe and call it a
> guide. **If you have an Intel Mac**, your realistic options are to run Linux on that machine,
> or to run against a remote Linux host — start at
> [rootless-podman.md](./rootless-podman.md) and [quickstart.md](../quickstart.md).

Confirm you are on Apple Silicon before going further:

```bash
uname -m
```

**You should see:**

```
arm64
```

**On an Intel Mac you will instead see:**

```
x86_64
```

If that is what you see, this page does not apply to you.

---

## What actually happens on macOS

Containers are Linux. They need the Linux kernel. macOS does not have one — it has XNU. So the
`podman` command on your Mac is a **remote client**: it opens a connection to a small Linux
virtual machine, called the *podman machine*, and asks that machine to do the real work.

```mermaid
flowchart LR
  Y["You type podman"] --> C["podman on macOS"]
  C --> S["SSH to the VM"]
  S --> E["podman inside the VM"]
  E --> K["Container + systemd"]
```

**What this shows:** a command typed on macOS becomes a remote call into a Linux virtual
machine, where the actual container and systemd run.

Read left to right. You type `podman` in your Mac's terminal. That `podman` is a remote client,
not an engine. It opens an SSH connection to a forwarded localhost port. The real `podman`
engine runs inside a small Linux virtual machine that Podman created for you. Inside that
virtual machine, your container starts and systemd runs as process 1 inside it.

**Two consequences you must internalise before reading further:** **nothing is a native macOS
process** — no container, no systemd, no cgroup belongs to your Mac, it is all inside the
virtual machine. And **there is no rootless setup on macOS**: do not read
[rootless-podman.md](./rootless-podman.md) on this platform. All `podman machine` commands are
rootless only by design, and the virtual machine handles identity mapping itself. That page is
for the four Linux platforms. **The default provider also changed in Podman 6:** the current
macOS providers are **`libkrun`** (the default) and **`applehv`**. If a guide tells you to use
`krunkit`, it is out of date — `krunkit` is the virtualisation *framework* that `libkrun` builds
on, not a provider name. One wrinkle: Homebrew's `podman` formula deliberately reverts the
default to `applehv`, because "krunkit is not yet available in homebrew-core", so
`podman machine list` shows a different `VM TYPE` depending on your installer. Both work;
override either way with `podman machine init --provider libkrun` or `--provider applehv`.

---

## Dependencies, itemised

| Package | What it is for | Where it comes from | Version |
|---|---|---|---|
| Podman | **The container engine**, running inside a virtual machine you never see. | `.pkg` installer (recommended) or `brew install podman` | `6.1.2` |
| `podman machine` | The **subcommand** that creates and manages that virtual machine. Part of Podman. | included | `6.1.2` |
| `podman-remote` | The remote client. **On Homebrew, `podman` is a symlink to `podman-remote`** — which is why `MOLECULE_PODMAN_EXECUTABLE=podman-remote` works out of the box. | included | `6.1.2` |
| `podman-mac-helper` | Forwards a **Docker-style API socket**. Only needed for Docker-compatible tools; **Molecule does not need it**. | ships inside the Homebrew formula — not a separate package | `6.1.2` |
| Ansible | **Ansible's engine.** Already installed inside the default virtual machine image. | Fedora CoreOS image, or `brew install ansible` for Route B | `14.4.0` (brew) |
| `molecule` | **The test driver itself.** Homebrew ships it natively. | `brew install molecule` | `26.9.0` |
| `molecule-plugins` | **The Podman driver.** Not part of Molecule, and **Homebrew has no formula for it** — on any platform. | Python, via `pipx` or a virtual environment | `26.9.28` |
| `pipx` | **Installs Python programs into their own isolated folder.** | `brew install pipx` | current |

**What macOS does *not* need**, unlike all four Linux pages: `uidmap`, `passt`, `crun`,
`fuse-overlayfs`, `newuidmap`, and the whole `/etc/subuid` dance. The virtual machine handles
all of that. **Do not** follow a Linux guide's dependency list on this platform.

---

## 1. Install Podman

**The recommended route is the official `.pkg` installer.** It is free, it is open source
(Apache-2.0 and GPL-3.0), and it needs no account, no payment method and no Homebrew. Go to
<https://podman.io>, download the macOS installer for Apple Silicon, open the `.pkg`, follow the
prompts, then open a **new** terminal window so the `PATH` change is picked up.

**Alternative — Homebrew, Apple Silicon only.** Homebrew is free and open source:

```bash
brew install podman

# Optional graphical interface, also free:
brew install --cask podman-desktop

# Docker-API forwarding helper. Only for Docker-compatible tools —
# Molecule does not need this:
sudo "$(brew --prefix)/bin/podman-mac-helper" install
```

> **The `podman` formula is hard-locked to `arm64`.** On an Intel Mac this command is refused by
> the formula itself, independent of the Podman 6.0 change — the second of the three blockers
> listed at the top of this page.

```bash
podman --version
```

**You should see:**

```
podman version 6.1.2
```

---

## 2. Create and start the machine

The virtual machine does not exist yet. Create it, then start it — or in one step,
`podman machine init --now`.

```bash
podman machine init
podman machine start
```

**You should see** from the `start`, a line ending in something like:

```
API forwarding listening on: /var/folders/.../podman/podman-machine-default-api.sock
```

or `API forwarding listening on: /run/user/501/podman/podman-machine-default-api.sock`. Which of
the two you get depends on your macOS version and installer; both are correct.

Check the machine:

```bash
podman machine list
podman machine info --format '{{.Host.Arch}}'
```

**You should see** from the second command:

```
arm64
```

> **Useful variants, all free:** `podman machine init --cpus=6 -m=8192 --disk-size=100` sizes the
> machine; `--provider applehv` or `--provider libkrun` picks the virtualisation backend;
> `podman machine init --playbook provision.yml` runs an Ansible playbook on first boot, which is
> the official way to pre-build this machine. `podman machine cp` moves files in and out;
> `podman machine reset` rebuilds it from scratch if it goes wrong.

---

## 3. Verify the machine can host systemd

**This is a verification, not an assumption, and the reason is specific.**

Podman 6.0 removed `--cgroup-manager` from **both** `podman machine init` and
`podman machine set`. The `containers.conf(5)` manual page says configuration "must be edited
in the virtual machine by using `podman machine ssh`". So **you cannot set the cgroup manager
from the Mac any more** — whatever the virtual machine image ships is what you get. This site
does not assert a value. It has you check.

A *cgroup* (see-group) is the Linux kernel feature that partitions resources and tracks which
process owns them. systemd needs cgroup version 2 to run properly as process 1 inside a
container. Run all four of these:

```bash
podman machine ssh 'cat /sys/fs/cgroup/cgroup.controllers'
podman machine ssh 'stat -fc %T /sys/fs/cgroup/'
podman machine ssh 'systemctl is-system-running'
podman machine ssh 'podman info --format "{{.Host.CGroupsVersion}}"'
```

**You should see, from the four commands in order:**

```
cpuset cpu io memory pids
cgroup2fs
running
v2
```

The first is the proof of cgroup v2 — Podman 6.0 removed cgroup v1 entirely, so the machine is
certainly v2, and this confirms it rather than assuming it. The third will also accept
`degraded`, which is normal: some kernel units cannot run inside a container.
[systemd-in-containers.md](../systemd-in-containers.md) explains why `degraded` is a success
case rather than a failure.

**If you find the cgroup manager is `cgroupfs` rather than `systemd`**, the fix goes *inside* the
virtual machine, per `containers.conf(5)` — the config must live in the VM, not on the Mac:

```bash
podman machine ssh
```

Then, inside the virtual machine:

```bash
sudo mkdir -p /etc/containers/containers.conf.d
sudo tee /etc/containers/containers.conf.d/99-molecule-systemd.conf <<'CONFEOF'
[containers]
cgroup_manager = "systemd"
CONFEOF
exit
podman machine stop && podman machine start
```

**You should see:** the same "API forwarding listening on" line as before.

**To undo the drop-in**, delete the file and restart the machine so the change is not re-read:

```bash
podman machine ssh
sudo rm -f /etc/containers/containers.conf.d/99-molecule-systemd.conf
exit
podman machine stop && podman machine start
```

The file is written *inside* the virtual machine, so the `rm` has to happen inside it too — and
`podman machine stop && start` is required because the guest reads that directory at boot, not
per command. Leaving the file in place does no harm, but nothing else in this guide should be
undone by accident.

> **UNVERIFIED:** whether the `libkrun` and `applehv` machines fully support what
> systemd-in-container needs — cgroup v2 delegation and `CAP_SYS_ADMIN` inside the guest. No
> upstream statement was found either way. The four commands above are how to close that gap on
> your own machine. Also worth knowing: a client and machine version mismatch is unsupported, and
> `podman info` shows both versions, so run it and compare.

---

## 4. Install Molecule and Ansible — two routes

Both routes work. **Route A is recommended**, and the reason is not a preference.

| | **Route A — inside the virtual machine** | **Route B — on macOS, remote client** |
|---|---|---|
| Where Molecule runs | Inside the Linux VM | On your Mac |
| Filesystem paths | Always visible to the engine | **The footgun** — see below |
| Recommended | **Yes** | Fallback |

### The footgun that decides it

**The Molecule Podman driver writes its build files on the *macOS* side**, into a cache
directory, and then asks the *in-VM* engine to build from those paths and bind-mount your
scenario directory. **If the in-VM engine cannot see a path, the build fails.** Your Mac's home
directory is not inside the virtual machine, so Route B spends its life fighting path
visibility. This is not in the driver's own docstring; it is a direct consequence of how the
driver works.

### Route A (recommended) — run Molecule inside the virtual machine

The default machine image is **Fedora CoreOS**, and it **already includes Ansible**. That
removes one whole step.

```bash
podman machine ssh
```

You are now inside the Linux virtual machine. Everything below runs here.

```bash
sudo dnf install -y podman pipx
pipx ensurepath && source ~/.bashrc
```

**You should see:** a list of packages installed ending with `Complete!`, then confirmation that
`/home/core/.local/bin` was added to your `PATH`. (`core` is the default user inside the
machine.)

> `pipx` may already be present. If `pipx --version` works before you install it, skip that part.

Now the toolchain — **all three packages together**, so `ansible-config` sits next to
`molecule`:

```bash
pipx install molecule ansible-core molecule-plugins
```

**You should see** three "installed package" lines — `molecule`, `ansible-core` and
`molecule-plugins` — all naming the **same** virtual environment, `pipx-venvs/molecule`:

```
installed package molecule 26.9.0, installed using Python 3.12
   in virtual environment pipx-venvs/molecule
installed package ansible-core 2.20.3, installed using Python 3.12
   in virtual environment pipx-venvs/molecule
installed package molecule-plugins 26.9.28, installed using Python 3.12
   in virtual environment pipx-venvs/molecule
```

> **Never `pipx install molecule` on its own.** Molecule calls `ansible-config` the instant it
> starts, and without `ansible-core` in the same environment the command exits with
> `ansible-config: not found`. The equivalent two-step form is `pipx install molecule
> ansible-core` followed by `pipx inject molecule molecule-plugins`.

Verify, still inside the virtual machine, then leave it:

```bash
molecule --version
molecule drivers
exit
```

**You should see** the version line `molecule 26.9.0 using ansible-core 2.20.3`, and a list of
driver names that includes `podman`.

> **Where does your work live now?** Put your Molecule project **inside the virtual machine** —
> under `/home/core`, for example — so the engine can always see it. Use
> `podman machine cp ./my-project core@localhost:/home/core/` to move a directory in, and the
> same command in reverse to get it back out.

### Route B — run Molecule on macOS, talk to the VM

This puts Molecule on your Mac and points it at the virtual machine through the remote client.

```bash
python3 -m venv ~/.venvs/molecule
source ~/.venvs/molecule/bin/activate
python3 -m pip install --upgrade pip
pip install molecule ansible-core "molecule-plugins[podman]"
```

**You should see:** `Successfully installed molecule-26.9.0 ...` and similar lines for the
other two packages.

The driver reads one environment variable, `MOLECULE_PODMAN_EXECUTABLE`, and threads it through
to both the Ansible connection plugin and the create playbook. Set it to `podman-remote`:

```bash
export MOLECULE_PODMAN_EXECUTABLE=podman-remote
podman system connection list
```

**You should see** nothing from the `export` — it is silent when it works — and then a row from
the `list` like:

```
Name                    URI                                                     Identity
podman-machine-default  ssh://core@127.0.0.1:53298/run/user/501/podman/podman.sock  /Users/you/.local/share/containers/podman/machine/machine
```

That is a **remote client SSHing to a forwarded localhost port**, speaking the Podman HTTP API
to a socket inside the virtual machine. The identity key is generated automatically by
`podman machine init`. **No SSH inventory, no hand-written `ssh://` inventory stanza, no
`podman system connection` fiddling required.**

Verify, and set the same thing in `ansible.cfg` instead of the environment if you prefer a file:

```bash
molecule --version
molecule drivers
```

**You should see:** the version line, and `podman` in the driver list.

```bash
# ansible.cfg
[defaults]
podman_executable = podman-remote
```

> On Homebrew, `podman` is *already* a symlink to `podman-remote`, so the default value works
> without setting anything. Being explicit is still recommended — and becomes necessary if you
> also use a local Linux `podman` in the same shell.

---

## Colima is not an alternative, and neither is Docker Desktop

You will find Colima suggested. **Do not use it.** From its own documentation, verbatim: *"Colima
is a higher level usage of Lima. It utilises Lima to provide Docker, Containerd, Kubernetes, and
Incus runtimes."* Podman is not among those runtimes and there is no way to make it one. It is
free, MIT-licensed and genuinely good — for Docker. **Docker Desktop is not a substitute
either:** its "free" tier is $0 but requires an account, and it is not Podman.

**Moving files in and out** is one command, and it definitely works:

```bash
podman machine cp ./my-project core@localhost:/home/core/
```

**You should see:** no output. Silence is success. The reverse direction is identical.

> **UNVERIFIED:** whether `podman machine init -v /Users:/Users` — mounting your whole home
> directory into the machine — still works with the `libkrun` and `applehv` providers in Podman
> 6.1.2. It is documented in older man pages; the Podman 6.0 release notes only mention host
> volume mounting for the **Linux** provider. Check with `podman machine init --help` on your
> machine. `podman machine cp` is the reliable fallback.

---

## What the internet still gets wrong

> **"Install Podman with `brew install podman`."** True on Apple Silicon, false on Intel — the
> formula is hard-locked to `arm64`. The official site recommends the `.pkg` for a reason: it is
> the supported path. Homebrew is a fine alternative; both are free.
>
> **"Use `--provider krunkit`."** Not a provider value. The macOS providers are `libkrun`
> (default) and `applehv`. `krunkit` is the virtualisation framework `libkrun` builds on.
>
> **"Run `podman machine init --cgroup-manager systemd`."** The option was **removed** in Podman
> 6.0 from both `init` and `set`. Section 3 verifies the value instead of setting it — the same
> conclusion the reference configuration reaches.
>
> **"Set `privileged: true` to get systemd working."** No — and on a rootless container it
> cannot work anyway, because a container in a user namespace "cannot have more privileges than
> the user that launched them". See [systemd-in-containers.md](../systemd-in-containers.md) §11.

---

## Verify

You have verified the toolchain by hand. Now run the one script that checks the things you
cannot check by eye — cgroup v2, identity mapping, the security state, the driver and the Python
version, all of which belong to the machine rather than to your Mac.

→ **[Run the pre-flight check →](../preflight.md)**

**Important:** if you chose Route A, run it **inside the virtual machine**, which is where
Molecule and the engine live:

```bash
podman machine ssh
```

then follow the [pre-flight instructions](../preflight.md) from there.

---

## Next

- **Pre-flight passed** → [Quickstart](../quickstart.md). Build your first passing test.
- **You skipped the rootless page on purpose** → that was correct. It is for Linux only.
- **Something failed** → [Troubleshooting](../troubleshooting.md), organised by error message
  rather than by platform.
- **You want to understand systemd inside the container** →
  [systemd-in-containers.md](../systemd-in-containers.md). This is where the Mac platform
  really starts to resemble the Linux pages.

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md). Distribution and product names are
used to identify the software being discussed, not to imply endorsement. The Podman, Colima and
Ubuntu quotations are from their own documentation, cited in [Sources](#sources).

---

## Sources

- <https://podman.io/docs/installation> — the macOS section, including the `.pkg` as the recommended route
- <https://github.com/podman-container-tools/podman/releases/tag/v6.0.0> — "Support for running on Intel Macs has been removed", the cgroup v1 removal, and the config-mounting change
- <https://github.com/podman-container-tools/podman/blob/main/contrib/design-docs/podman6hld.md> — the Podman 6 design document, including the `libkrun` default
- <https://docs.podman.io/en/latest/markdown/podman-machine.1.html> — the provider table: `libkrun` (default) and `applehv` for macOS
- <https://docs.podman.io/en/latest/markdown/podman-machine-init.1.html> and <https://docs.podman.io/en/latest/markdown/podman-machine-set.1.html> — `init` and `set`; the `set` option list no longer contains `--cgroup-manager`
- <https://docs.podman.io/en/latest/markdown/podman-machine-start.1.html> and <https://docs.podman.io/en/latest/markdown/podman-machine-ssh.1.html> — the "API forwarding listening on" output and the in-VM verification commands in section 3
- <https://docs.podman.io/en/latest/markdown/podman-system-connection-list.1.html> — the real `ssh://core@127.0.0.1:...` connection output quoted in Route B
- <https://docs.podman.io/en/latest/markdown/podman.1.html> — the `--cgroup-manager` default
- <https://github.com/containers/common/blob/main/docs/containers.conf.5.md> — "edit config in the VM via `podman machine ssh`"
- <https://brew.sh/2026/06/11/homebrew-6.0.0/> and <https://docs.brew.sh/Support-Tiers> — macOS Intel moved to Tier 3, no new bottles
- <https://raw.githubusercontent.com/Homebrew/homebrew-core/HEAD/Formula/p/podman.rb> — the `depends_on arch: :arm64` lock, the `applehv` revert, and the `podman` → `podman-remote` symlink
- <https://formulae.brew.sh/formula/molecule> and <https://formulae.brew.sh/formula/ansible> — `molecule 26.9.0`, `ansible 14.4.0`
- <https://github.com/ansible-community/molecule-plugins/blob/main/src/molecule_plugins/podman/driver.py> — the `MOLECULE_PODMAN_EXECUTABLE` source, quoted in Route B
- <https://docs.ansible.com/projects/ansible/latest/collections/containers/podman/podman_connection.html> — `podman_executable` and the `ANSIBLE_PODMAN_EXECUTABLE` variable
- <https://colima.run/docs/faq/> — the Colima quote proving no Podman support
- Internal, reproducible: the verification block is quoted from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §5.5; the route analysis is
  [`03-platform-install-matrix.md` §4.6–4.8](../../.research/03-platform-install-matrix.md)