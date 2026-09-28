# Fedora 44 — install Molecule and Podman

> **You are here:** [Docs home](../index.md) → [Install](./index.md) → **Fedora 44** → [Quickstart](../quickstart.md)

**What you will be able to do:** go from a fresh Fedora 44 workstation to a machine that passes
the pre-flight check, in about five commands.

**This is the shortest page on the site.** If you have a choice of platform, this is the one to
start on. Everything here is native: one package manager, no virtual environment gymnastics, no
compatibility warnings. The only extra tool you install comes from Python.

---

## Are you in the right place?

You are on **Fedora 44**, released 28 April 2026, the current stable release.

```bash
cat /etc/os-release
```

**You should see**, on the `ID` line:

```
ID=fedora
VERSION_ID=44
```

```bash
rpm -q podman ansible-core pipx
```

**You should see** — the versions you will be installing. If yours differ, that is fine; check
they are in the same ballpark:

```
podman-5.8.1-1.fc44.x86_64
ansible-core-2.20.3-1.fc44.x86_64
pipx-1.11.0-1.fc44.noarch
```

> **Fedora 45 note, and it is only a footnote.** Fedora 45 is currently Beta. It ships
> `podman 6.1.1`, which is a major-version jump from the 5.8.1 you are installing. Everything on
> this page still applies; nothing on this page is version-specific to 5.x.

---

## Dependencies, itemised

Every package below, what it does, and where it comes from. Nothing is hidden — this is the whole
list. Read the "What it is for" column before you install, so you know what you are about to
run.

| Package | What it is for | Native or pipx | Version you will get |
|---|---|---|---|
| `podman` | **The container engine.** Creates, starts and stops your test container. It is the program that actually runs your systemd-under-test. | **Native** — dnf | `5.8.1-1.fc44` |
| `ansible-core` | **Ansible's core engine.** Provides `ansible-playbook`, `ansible-galaxy` and — the part that matters here — `ansible-config`, which Molecule calls the instant it starts. | **Native** — dnf | `2.20.3-1.fc44` |
| `passt` | **Rootless networking.** Lets a container that has no network privileges still make network connections. | **Native** — dnf | `0^20260120` |
| `git` | Molecule's build step needs it, and you will want it for your own project files. | **Native** — dnf | `2.53.0-1.fc44` |
| `pipx` | **Installs Python programs into their own isolated folder.** This is how Molecule and its Podman driver get onto your machine. | **Native** — dnf | `1.11.0-1.fc44` |
| `molecule` | **The test driver itself.** | **pipx** — Fedora has no package | `26.9.0` |
| `molecule-plugins` | **The Podman driver.** Tells Molecule how to talk to Podman. It is *not* part of Molecule. | **pipx** — no distribution ships it, anywhere | `26.9.28` |

**Two things that are on this list because they surprise people:**

- **`molecule` has no Fedora package.** Fedora's package search for `molecule` returns twelve
  results. Every one of them is a chemistry package, a typesetting package or a puzzle game.
  This is why pipx is in the list at all.
- **`molecule-plugins` has no package on any platform, on any distribution.** Not Fedora, not
  Ubuntu, not Arch, not Homebrew, not Mageia. If you are searching for it in a package manager,
  stop. It is a Python package and nothing else.

**Also pulled in automatically, and correctly not named above:** `netavark` `1.17.2-1.fc44` and
`aardvark-dns` `1.17.0-3.fc44`, which Fedora ships as separate packages and Podman depends on.
You do not need to name them.

---

## 1. Install the container engine and the support packages

```bash
sudo dnf install -y podman ansible-core git pipx passt
```

**You should see:** a list of packages being installed and configured, ending with something like:

```
Complete!
```

Then check that Podman is really there:

```bash
podman --version
```

**You should see:**

```
podman version 5.8.1
```

> If you see a different 5.x number, that is fine. Any `5.x` or `6.x` works for this site. What
> would *not* be fine is a `4.x` — that is the old Ubuntu 24.04 situation, covered in
> [ubuntu.md](./ubuntu.md).

---

## 2. Put the pipx application folder on your PATH

`pipx` installs its programs into a folder inside your home directory. That folder has to be on
your `PATH` — the list of folders your shell searches when you type a command name — or the
`molecule` command will not be found.

```bash
pipx ensurepath
```

**You should see:**

```
/home/<yourname>/.local/bin is already in PATH.
Success! You have already added '/home/<yourname>/.local/bin' to your PATH.
```

(The exact wording varies. What you are looking for is confirmation that the path was added or
is already present.)

If the first `molecule` command later fails, it is almost always because this step was not
picked up. Either **close your terminal window and open a new one**, or, in your current
window:

```bash
source ~/.bashrc
```

---

## 3. Install the toolchain — all three packages, together

This is the step most guides get wrong. **Install `ansible-core` in the same command as
`molecule`.** Molecule calls `ansible-config` on start-up; if that program is not in the same
environment, the `molecule` command is broken no matter what else you did.

```bash
pipx install molecule ansible-core molecule-plugins
```

**You should see**, roughly:

```
installed package molecule 26.9.0, installed using Python 3.14.2
   in virtual environment pipx-venvs/molecule
installed package ansible-core 2.20.3, installed using Python 3.14.2
   in virtual environment pipx-venvs/molecule
installed package molecule-plugins 26.9.28, installed using Python 3.14.2
   in virtual environment pipx-venvs/molecule
```

All three land in **one** virtual environment named `pipx-venvs/molecule`. That single fact is
what makes the next command work.

> **Prefer to add the driver as a second step?** This is equivalent, and is the form the
> canonical reference file records:
>
> ```bash
> pipx install molecule ansible-core
> pipx inject molecule molecule-plugins
> ```
>
> `pipx inject` adds a package into an environment that already exists. Both routes end in the
> same place: `molecule`, `ansible-config` and the driver in one isolated folder.

---

## 4. Verify — three commands, in this order

### 4a. Molecule starts at all

```bash
molecule --version
```

**You should see:**

```
molecule 26.9.0 using ansible-core 2.20.3
```

**If you instead see this, stop and fix it now:**

```
ansible-config: not found
```

That means `ansible-core` is not in Molecule's environment. You are on step 3, so this should
not happen — but if it does, the repair is one command:

```bash
pipx inject molecule ansible-core
molecule --version
```

Do not carry on until this prints the version line. Everything after this point depends on it.

### 4b. The Podman driver is loaded

```bash
molecule drivers
```

**You should see** a list of driver names, one per line, which includes:

```
podman
```

If `podman` is missing, the `molecule-plugins` install did not land. Re-run step 3.

### 4c. Rootless containers work

```bash
podman info --format '{{.Host.Security.Rootless}}'
```

**You should see:**

```
true
```

`true` means Podman is running without root, which is the correct and secure configuration. See
[rootless-podman.md](./rootless-podman.md) for what that means and why it is the default.

One quick container, to prove the engine works end to end:

```bash
podman run --rm alpine id
```

**You should see:**

```
uid=0(root) gid=0(root) groups=0(root)
```

**Do not be alarmed by that `root`.** Read [rootless-podman.md](./rootless-podman.md) §"Prove
it" — that `root` exists only *inside* the container. On your Fedora machine you are still an
ordinary unprivileged user, and that container is gone now that the command finished.

---

## What we did *not* install, and why

Three things a reader reasonably expects to see, and the honest reason each is absent.

| You might expect | Why it is not here |
|---|---|
| A `setsebool` command | **Not needed, and do not add it.** SELinux (Security-Enhanced Linux) is Fedora's mandatory-access-control system. With SELinux in its default `Enforcing` state, rootless Podman works — **this is the configuration every result in this project was measured under.** No extra boolean needs flipping. Adding one is a common blog workaround for a problem you do not have. |
| A `uidmap` package | **There is no `uidmap` package on Fedora.** The page 404s. The `newuidmap` and `newgidmap` helper programs come from `shadow-utils-subid`, which is already a hard dependency of `podman` — so step 1 installed it for you. Check with `rpm -q shadow-utils-subid`. |
| A `podman-plugins` package | **It does not exist on any of the five platforms on this site.** It is a Red Hat Enterprise Linux / CentOS habit. If you are following a guide that tells you to install it, that guide is wrong. |

---

## Platform-specific gotchas

Good news: **Fedora has no platform-specific gotcha.** It is the reason we suggest starting here.

Two small things worth knowing, neither of which is a problem:

- **SELinux `Enforcing` is the well-tested case, not an obstacle.** If you have ever had a
  container mysteriously unable to see a file, SELinux is the usual suspect — and the fix is
  almost always a volume label, not a `setsebool`. See
  [systemd-in-containers.md](../systemd-in-containers.md) and
  [troubleshooting.md](../troubleshooting.md).
- **Check the SELinux state with `getenforce`, not with `podman info`.**

  ```bash
  getenforce
  ```

  **You should see:**

  ```
  Enforcing
  ```

  `Enforcing` is the normal, correct Fedora default. `Permissive` logs and allows;
  `Disabled` is off entirely.

  > **Do not run `podman info --format '{{.Host.Security.SelinuxEnabled}}'`.** It errors on
  > Podman 5.8.7 with `can't evaluate field SelinuxEnabled in type define.SecurityInfo` — the
  > field does not exist. `getenforce` is the right tool and it always works. If you want the
  > whole block, `podman info --format '{{json .Host.Security}}'` is valid.

---

## What the internet still gets wrong

> **`privileged: true` does not help, and on Fedora it actively hurts.** The Molecule Podman
> driver's own docstring says to set `privileged: true`, `command` and `environment` when you
> want systemd inside a container. Its own example sets it. **Do not follow it.** Measured on
> Fedora 44, rootless, with SELinux `Enforcing`: `--privileged` unmasks `/sys`, which makes three
> kernel units fail, and the container lands in `degraded` instead of `running`. A rootless
> container cannot have more privileges than the user who launched it, so the flag buys you
> nothing. This site never sets it. [systemd-in-containers.md](../systemd-in-containers.md)
> carries the full folklore table.
>
> **`molecule --version` failing with `ansible-config: not found` is not a corrupt install.**
> It means `ansible-core` is missing from Molecule's environment. `pipx install molecule
> ansible-core molecule-plugins` fixes it, as step 3 does.

---

## Verify

You have verified the toolchain by hand. Now run the one script that checks the things you
cannot check by eye.

→ **[Run the pre-flight check →](../preflight.md)**

The script is read-only. It never installs anything, never asks for `sudo`, and never writes outside
Podman's own storage directory, which `podman` itself may create on
first use. It checks cgroup v2, your `PATH`, rootless mode, the identity-mapping files, SELinux
state, your Python version, and that both Molecule and the Podman driver are present. When it
is green, your host is ready.

---

## Next

- **Pre-flight passed** → [Quickstart](../quickstart.md). Build your first passing test.
- **Something failed** → [Troubleshooting](../troubleshooting.md) first — it is organised by
  error message, not by platform, and it is faster to search than re-reading this page.
- **You want to understand what just happened** →
  [Rootless Podman](./rootless-podman.md) explains the identity mapping that step 1 quietly
  set up for you.
- **You want to add a linter** → `sudo dnf install -y ansible-lint`. It is optional and
  Molecule does not require it.

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md). Distribution and product names are
used to identify the software being discussed, not to imply endorsement.

---

## Sources

- <https://fedoraproject.org/server/download> — Fedora 44, released 2026-04-28
- <https://packages.fedoraproject.org/pkgs/podman/podman/fedora-44.html> — `podman 5.8.1-1.fc44`
- <https://packages.fedoraproject.org/pkgs/ansible-core/ansible-core/fedora-44.html> — `ansible-core 2.20.3-1.fc44`
- <https://packages.fedoraproject.org/pkgs/pipx/pipx/fedora-44.html> — `pipx 1.11.0-1.fc44`
- <https://packages.fedoraproject.org/pkgs/passt/passt/fedora-44.html> — `passt 0^20260120`
- <https://packages.fedoraproject.org/pkgs/netavark/netavark/fedora-44.html> and
  <https://packages.fedoraproject.org/pkgs/aardvark-dns/aardvark-dns/fedora-44.html> — the two networking components Fedora ships separately
- <https://packages.fedoraproject.org/search?query=molecule> — proves Fedora has no `molecule` package
- <https://packages.fedoraproject.org/pkgs/uidmap/> — 404, proving no `uidmap` package exists
- <https://pypi.org/project/molecule/> and <https://pypi.org/project/molecule-plugins/> — the two Python packages
- <https://docs.ansible.com/projects/molecule/installation/> — Molecule's installation guidance
- <https://pipx.pypa.io/stable/how-to/install-pipx.html> — `pipx ensurepath`
- <https://docs.podman.io/en/latest/markdown/podman-run.1.html> — the `podman run` behaviour
  behind `{{.Host.Security.Rootless}}`
- Internal, reproducible: the package table is
  [`03-platform-install-matrix.md` §7.1](../../.research/03-platform-install-matrix.md) Tables A
  and B; the install commands are quoted verbatim from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §5.2
