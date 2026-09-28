# Arch Linux — install Molecule and Podman

> **You are here:** [Docs home](../index.md) → [Install](./index.md) → **Arch Linux** → [Quickstart](../quickstart.md)

**What you will be able to do:** go from a fresh Arch installation to a passing pre-flight check,
and learn two Arch-specific things that surprise everyone: the package is called
`python-pipx`, and there is a warning you are meant to ignore.

**Arch is the second-smoothest platform on this site after Fedora.** It has the newest versions
of everything, and it is the **only Linux distribution that ships a usable Molecule package** —
in the official `extra` repository, not the AUR.

---

## Are you in the right place?

You are on **Arch Linux**, the rolling release. Every package below is the current one as of the
research date, 2026-09-28.

```bash
cat /etc/os-release
```

**You should see**, on the `ID` line:

```
ID=arch
```

```bash
pacman -Q podman molecule ansible ansible-lint python-pipx 2>/dev/null
```

**You should see** — or, on a fresh machine, see them listed as *not installed*, which is what
step 1 fixes:

```
podman 6.1.2-1
molecule 26.9.0-1
ansible 14.4.0-1
ansible-lint 26.9.0-1
python-pipx 1.15.0-1
```

---

## Dependencies, itemised

Arch is the platform where almost everything is native, so this table is short and the "pipx"
column is nearly empty.

| Package | What it is for | Native or pipx | Version you will get |
|---|---|---|---|
| `podman` | **The container engine.** Creates, starts and stops your test container. | **Native** — pacman | `6.1.2-1` |
| `molecule` | **The test driver itself** — and the only place on Linux you can install it natively. | **Native** — pacman, official **`extra`** repo | `26.9.0-1` |
| `ansible` | The full Ansible collections bundle. | **Native** — pacman | `14.4.0-1` |
| `ansible-core` | Ansible's core engine — also available natively if you prefer the minimal set. Provides `ansible-config`. | **Native** — pacman | `2.21.4-1` |
| `ansible-lint` | Optional linter. **Not** a Molecule dependency. | **Native** — pacman | `26.9.0-1` |
| `crun` | The **OCI runtime** — the low-level program that actually runs a container. Arch's default, and faster than `runc`. | **Native** — pacman | current |
| `passt` | **Rootless networking.** Lets a container with no network privileges still make connections. | **Native** — pacman | current |
| `git` | Molecule's build step needs it. | **Native** — pacman | current |
| **`python-pipx`** | **Installs Python programs into their own isolated folder.** Used only for the driver, because `molecule` itself is native. | **Native** — pacman | `1.15.0-1` |
| `molecule-plugins` | **The Podman driver.** Not in Molecule, and in no Arch repository either. | **pipx** | `26.9.28` |

### The two names that catch people out

> **`python-pipx`, not `pipx`.** Arch prefixes Python tools with `python-`. `sudo pacman -S pipx`
> will fail with "target not found". There is no `python3-pipx` anywhere either — the name is
> exactly `python-pipx`.

> **`molecule-plugins` is not in any Arch repository.** This is the one thing Arch does *not*
> have natively, and it is not an Arch oversight — it is in **no** distribution's repository on
> any platform on this site. Its 35-entry dependency list does not include it. So even on the
> most complete platform, you run one extra pipx command.

---

## 1. Install the packages

```bash
sudo pacman -S podman molecule ansible ansible-lint python-pipx git crun passt
```

**You should see** a list of packages, and then the prompt that matters:

```
:: Proceed with installation? [Y/n]
```

Type `Y` and press Enter. If some of the packages are already installed, `pacman` will say so
and move on — that is fine, it means this step is partly done already.

```bash
podman --version
```

**You should see:**

```
podman version 6.1.2
```

> **You may see a warning here, and you are meant to ignore it.** See section 3. It is not a
> failure, and you should not try to fix it.

---

## 2. Rootless identity mapping is already done on Arch

On most Linux distributions, giving your user permission to run containers means adding a block
of user IDs to two configuration files by hand. **On Arch, this is already done for you.**

Since the `shadow` package version `4.11.1-3`, Arch's `useradd` — the command that creates a new
user — pre-populates `/etc/subuid` and `/etc/subgid` automatically. Those two files are what let
a rootless container act as many different user IDs. (`subuid` = *subordinate user IDs*,
`subgid` = *subordinate group IDs*.)

Verify rather than assume:

```bash
grep "^$USER:" /etc/subuid /etc/subgid
```

**You should see two lines, one from each file:**

```
/etc/subuid:yourname:100000:65536
/etc/subgid:yourname:100000:65536
```

That means **65,536 IDs** are reserved for your account. That is the standard block size, and it
is exactly what a container needs to run a full range of UIDs without touching anything real on
your system.

**If you see nothing**, your account predates `shadow 4.11.1-3` — a long-standing box that was
upgraded in place rather than reinstalled. Follow
[rootless-podman.md](./rootless-podman.md) §"Step 2 — add the range if it is missing", and do
not forget its `podman system migrate` step. It is the single most frequently forgotten command
in this whole area.

---

## 3. A harmless warning you may see — learn to ignore it

Some Arch users see this line when they run a Podman command:

```
Failed to add pause process to systemd sandbox cgroup
```

**It is cosmetic. It is not a failure. Do not try to fix it.**

The explanation: rootless Podman starts a background "pause" process to hold your user
namespaces open between commands. On Arch, with `crun` as the default runtime, that process
cannot be added to a particular systemd sandbox control group — and Podman reports it anyway.
The container still works. Your tests still pass. Nothing downstream depends on this message.

If you see it and you are not sure whether it matters, run the proof:

```bash
podman run --rm alpine id
```

**You should see:**

```
uid=0(root) gid=0(root) groups=0(root)
```

The container ran. The warning was noise.

> **Do not add a systemd mask drop-in to silence it.** Such a drop-in appears in the Arch
> community write-ups, and it was **never executed and verified** during this project's research.
> This site does not teach it, and neither does it teach you to accept `degraded` instead of
> `running` — the containers here reach `running` without any masking. Ignore the warning;
> change nothing.

---

## 4. Add the Podman driver with pipx

Arch's `molecule` package is native and current, but the driver it needs is not in any
repository. So the driver goes in through pipx, into its own environment, and you put that
environment on your `PATH`.

First, put pipx's application folder on your `PATH` — the list of folders your shell searches
when you type a command name:

```bash
pipx ensurepath
```

**You should see:** confirmation that `/home/<yourname>/.local/bin` was added, or that it was
already present. Then **close your terminal and open a new one**, or run `source ~/.zshrc` (if
you use zsh, which most Arch users do) or `source ~/.bashrc`.

Now install the driver, and put its environment on `PATH`:

```bash
pipx install "molecule-plugins[podman]"
```

**You should see:**

```
installed package molecule-plugins 26.9.28, installed using Python 3.13
   in virtual environment pipx-venvs/molecule-plugins
```

```bash
export PATH="$HOME/.local/pipx/venvs/molecule-plugins/bin:$PATH"
```

**You should see:** nothing at all. `export` is silent when it works.

> **Make that `PATH` line permanent**, or you will lose the driver the next time you open a
> terminal. Add the same line to `~/.zshrc` (or `~/.bashrc`):
>
> ```bash
> echo 'export PATH="$HOME/.local/pipx/venvs/molecule-plugins/bin:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> ```

### About `ansible-config`, which Molecule needs

**Molecule calls `ansible-config` the instant it starts.** If that program is not on the same
`PATH` as `molecule`, the command dies with `ansible-config: not found`. Two ways to be sure
you are safe on Arch:

1. **The distro route** — `ansible` and `ansible-core` are both installed by step 1, so
   `ansible-config` is already on your system `PATH`. Arch's native `molecule` finds it
   immediately. This is why this page works.
2. **The pipx route** — if you prefer Molecule in its own environment, install all three
   together:

   ```bash
   pipx install molecule ansible-core molecule-plugins
   ```

   All three land in one environment, so `ansible-config` sits next to `molecule` by
   construction. **Never `pipx install molecule` on its own** — that produces a binary that
   cannot start.

### An alternative worth knowing about

If you would rather keep Arch's native `molecule` in charge and inject the driver into the
system Python that the `molecule` package uses — on Arch that is the system interpreter:

```bash
python3 -m pip install --user --break-system-packages "molecule-plugins[podman]"
```

> **Arch is a rolling-release distribution, and its system Python is externally managed** — that
> is why `--break-system-packages` is needed. If your Arch setup refuses it, use the pipx route
> above instead. Both give a working `molecule drivers` that lists `podman`. **The pipx route is
> the one this site documents as primary**, because it cannot break your system Python.

---

## 5. Verify — three commands, in this order

### 5a. Molecule starts at all

```bash
molecule --version
```

**You should see:**

```
molecule 26.9.0 using ansible-core 2.21.4
```

**If you instead see this, stop and fix it now:**

```
ansible-config: not found
```

That means `ansible-config` is not on your `PATH`. Check that step 1's `ansible` or
`ansible-core` really installed, and check your `PATH` in a fresh shell.

### 5b. The Podman driver is loaded

```bash
molecule drivers
```

**You should see** a list of driver names, one per line, including:

```
podman
```

**If `podman` is missing**, the `PATH` line from step 4 is not in effect. Reopen your terminal,
or re-run:

```bash
export PATH="$HOME/.local/pipx/venvs/molecule-plugins/bin:$PATH"
molecule drivers
```

### 5c. Rootless containers work

```bash
podman info --format '{{.Host.Security.Rootless}}'
```

**You should see:**

```
true
```

```bash
podman run --rm alpine id
```

**You should see:**

```
uid=0(root) gid=0(root) groups=0(root)
```

And if the `crun` warning from section 3 appears here, you now know to ignore it.

---

## A warning about the rolling release

This site is about **testing** your own configuration, and a test is only worth as much as its
reproducibility.

The tag `archlinux:latest` moves. Two runs a week apart can see different images, and a test
that passed on Sunday can fail on Tuesday for reasons that have nothing to do with your
configuration. `archlinux:latest` does work with `--systemd=always`, but it is **not
reproducible**, and we will not pretend otherwise.

**For real test work, use one of these instead:**

- **Build your own image** from a pinned base, so every run uses the same bytes. This is taught
  in full at [authoring/custom-images.md](../authoring/custom-images.md), and it is the answer
  if you care about reproducibility.
- **Use `ubi9/ubi-init:latest`**, the default recommended image on this site. It is a Red Hat
  Universal Base Image with an init system designed for exactly this job, and it reaches
  `running` — not `degraded` — rootless, with no masking and no extra configuration.

The details of why that image is the right default, and what Molecule's own guide gets wrong
about it, are in [systemd-in-containers.md](../systemd-in-containers.md).

---

## What the internet still gets wrong

> **"`molecule` is in the AUR on Arch."** It is not. It is in the **official `extra` repository**
> at `26.9.0-1`, last updated 2026-09-25. You do not need a helper such as `yay`, and you should
> not build a third-party package for a program your distribution already ships at the current
> version.
>
> **"The package is `pipx`."** It is `python-pipx`. Arch prefixes Python tools. `pacman -S pipx`
> fails.
>
> **"That `crun` warning means something is wrong."** It does not. See section 3.
>
> **"You need `--cgroup-manager=systemd` set explicitly."** It already is, and `crun` already
> supports the systemd cgroup mode. `crun` is *not* a requirement for systemd-in-container — the
> systemd **cgroup manager** is, and that is Podman's default. `crun` is simply Arch's default
> runtime and it is faster than `runc`.
>
> **"Set `privileged: true` to get systemd working."** No. See
> [systemd-in-containers.md](../systemd-in-containers.md) §11. The Podman driver's own docstring
> says this, and it is wrong. On a rootless container the flag buys you nothing and can push the
> container into `degraded` instead of `running`.

---

## Verify

You have verified the toolchain by hand. Now run the one script that checks the things you
cannot check by eye — cgroup v2, identity mapping, the driver, Python version.

→ **[Run the pre-flight check →](../preflight.md)**

The script is read-only: it never installs anything, never asks for `sudo`, and never writes outside
Podman's own storage directory, which `podman` itself may create on
first use. When it is green, your host is ready.

---

## Next

- **Pre-flight passed** → [Quickstart](../quickstart.md). Build your first passing test.
- **You want a reproducible test image** →
  [systemd-in-containers.md](../systemd-in-containers.md), then
  [authoring/custom-images.md](../authoring/custom-images.md).
- **Something failed, and you see the `crun` warning** → ignore the warning, then read
  [Troubleshooting](../troubleshooting.md).
- **You want to understand the identity mapping** →
  [Rootless Podman](./rootless-podman.md). On Arch it is already done; the page explains why it
  matters on the other three.

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md). Distribution and product names are
used to identify the software being discussed, not to imply endorsement. The ArchWiki and
`shadow` quotations are from their own documentation, cited in [Sources](#sources).

---

## Sources

- <https://archlinux.org/packages/extra/any/molecule/> — `molecule 26.9.0-1` in the official `extra` repo, updated 2026-09-25
- <https://archlinux.org/packages/?q=molecule> — one exact match, proving the other two hits are unrelated
- <https://archlinux.org/packages/extra/any/python-pipx/> — `python-pipx 1.15.0-1`
- <https://wiki.archlinux.org/title/Podman> — rootless, pre-populated `subuid` since `shadow 4.11.1-3`, `crun` as the new default runtime, and the `podman system migrate` requirement, quoted verbatim in sections 2 and 3
- <https://man.archlinux.org/man/extra/crun/crun.1.en> — `crun`
- <https://man.archlinux.org/man/extra/podman/podman-rootless.7.en> — rootless mode
- <https://archlinux.org/packages/?q=podman> and <https://archlinux.org/packages/?q=ansible> — `podman 6.1.2-1`, `ansible 14.4.0-1`, `ansible-core 2.21.4-1`
- <https://pypi.org/project/molecule-plugins/> — the driver, in no Arch repository
- <https://pipx.pypa.io/stable/how-to/install-pipx.html> — `pipx ensurepath` and `pipx install`
- Internal, reproducible: the package table is
  [`03-platform-install-matrix.md` §7.1](../../.research/03-platform-install-matrix.md) Tables A
  and B; the install commands are quoted from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §5.4
