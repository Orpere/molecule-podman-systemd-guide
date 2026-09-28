# Mageia 10 — install Molecule and Podman

> **You are here:** [Docs home](../index.md) → [Install](./index.md) → **Mageia 10** → [Quickstart](../quickstart.md)

**What you will be able to do:** go from a fresh Mageia 10 machine to a passing pre-flight
check, using a virtual environment because your distribution does not package two of the tools
this site needs.

**Read section 1 before you start.** Mageia needs three workarounds that the other four
platforms do not, and one of them we cannot fully answer for you. We are going to be straight
about that rather than give you a recipe we have not tested.

---

## Are you in the right place?

You are on **Mageia 10**, released July 2026. Mageia 9 reached end of support in September
2026.

```bash
cat /etc/os-release
```

**You should see**, on the `ID` and `VERSION_ID` lines:

```
ID=mageia
VERSION_ID="10"
```

Mageia uses `dnf` under the hood, and its own native front-end is `urpmi`. Both work
interchangeably for everything on this page. This site uses `dnf` because it is the more
recognisable name, and `urpmi` equivalents are given where they differ.

> **One Mageia fact worth knowing up front, and it is a good one:** Mageia 10's `ansible-core`
> is `2.20.6` and its `ansible` is `13.7.0` — **both fresher than Fedora 44's** (`2.20.3` and
> `13.4.0`). Its `podman` at `5.7.1` is only one minor version behind Fedora's `5.8.1`. So the
> tools Mageia *does* ship are current. It is the two it does not ship that make this platform
> hard.

---

## Mageia is the hardest platform on this site

> ### Three things are missing or unusable on Mageia 10. Here they are, up front.
>
> | # | Problem | What it means for you |
> |---|---|---|
> | 1 | **No `pipx` package.** Zero matches across all 38,861 packages in Mageia's `core/release`. | You must install `pipx` itself with `pip`. |
> | 2 | **No `uidmap` / `newuidmap` package.** Only `shadow-utils 4.13` and the `lib64subid4` library exist. | **We cannot tell you whether the helper programs are present.** Section 4 is a live check, not a fix. |
> | 3 | **The packaged Molecule is `6.0.3`, from September 2021.** | **Unusable.** It predates `molecule-plugins`, the Podman driver as it exists today, and the `containers.podman` collection. You must install Molecule yourself. |
>
> All three were verified against Mageia's official mirror directory listing, which is
> authoritative and has no anti-bot protection. We did not guess at any of it.

**And the honest caveat on top:** whether Mageia 10 marks its `python3` as
`EXTERNALLY-MANAGED` under PEP 668 is **UNVERIFIED**. That decides whether the plain `pip`
route in section 2 works or refuses. **This page gives you a virtual environment in section 3,
which is safe either way** — that is why the ordering here is not the same as the other pages.

---

## Dependencies, itemised

| Package | What it is for | Native or pip | Version you will get |
|---|---|---|---|
| `podman` | **The container engine.** Creates, starts and stops your test container. | **Native** — dnf / urpmi | `5.7.1-1.mga10` |
| `ansible` | The full Ansible collections bundle. | **Native** — dnf / urpmi | `13.7.0-1.mga10` |
| `python3-ansible-core` | Ansible's core engine — this is the one Molecule calls. Provides `ansible-config`. | **Native** — dnf / urpmi | `2.20.6-1.mga10` |
| `git` | Molecule's build step needs it. | **Native** — dnf / urpmi | `2.52.0-2.mga10` |
| `python3-pip` | Python's package installer. **You need this because Mageia packages no `pipx` and no usable Molecule.** | **Native** — dnf / urpmi | `26.0.1-1.mga10` |
| `passt` | **Rootless networking.** Lets a container with no network privileges still make connections. | **Native** — dnf / urpmi | `0.20251223` |
| `crun` | The **OCI runtime** — the low-level program that actually runs a container. | **Native** — dnf / urpmi | `1.25.1-2.mga10` |
| `ansible-lint` | Optional linter. **Not** a Molecule dependency. | **Native** — dnf / urpmi | `26.4.0-1.mga10` |
| `fuse-overlayfs` | Fallback rootless container storage, for filesystems without native overlay support. | **Native** — dnf / urpmi | `1.15-1.mga10` |
| `pipx` | **Installs Python programs into their own isolated folder.** | **NOT PACKAGED** → `pip` | whatever pip gives |
| `molecule` | **The test driver itself.** | **NOT USABLE** — `python3-molecule` is 6.0.3 (2021) → install with `pip` | `26.9.0` |
| `molecule-plugins` | **The Podman driver.** In no distribution's repository, on any platform. | **NOT PACKAGED** → `pip` | `26.9.28` |
| `newuidmap` | Lets a rootless container act as many user IDs. | **NOT PACKAGED** ⚠ see section 4 | — |
| `passt-selinux` | SELinux policy for `passt`. Pulled in automatically. | **Native** | `0.20251223` |

**Mageia's equivalent one-liner, if you prefer `urpmi`:**

```bash
sudo urpmi podman ansible ansible-lint git python3-pip passt crun fuse-overlayfs
```

---

## 1. Install the packages

```bash
sudo dnf install -y podman ansible git python3-pip passt crun
```

**You should see:** a list of packages being installed and configured, ending with something
like:

```
Setting up podman ...
```

```bash
podman --version
```

**You should see:**

```
podman version 5.7.1
```

---

## 2. Install pipx from pip

There is no `pipx` package, so you install it with `python3`'s own package installer.

```bash
python3 -m pip install --user pipx
```

**You should see:**

```
Successfully installed pipx-...
```

```bash
python3 -m pipx --version
```

**You should see** something of the shape:

```
pipx 1.x.x from /home/<yourname>/.local/lib/python3.x/site-packages/pipx (python 3.x)
```

**If you see this instead:**

```
error: externally-managed-environment
```

Mageia 10 marks its `python3` as `EXTERNALLY-MANAGED` under PEP 668, which blocks installing
packages into the system interpreter. **Skip section 3's `pipx` steps entirely and go straight
to section 4, the virtual environment** — it is unaffected either way, which is exactly why it
is the recommended route.

Put pipx's application folder on your `PATH` — the list of folders your shell searches when you
type a command name:

```bash
python3 -m pipx ensurepath
```

**You should see:** confirmation that `/home/<yourname>/.local/bin` was added or is already
there. Then **close your terminal and open a new one**, or run `source ~/.bashrc` (or
`source ~/.zshrc`).

---

## 3. Ignore the packaged Molecule — prove it is unusable

Mageia ships a package called `python3-molecule`. **Do not install it.** Check what is there:

```bash
rpm -q python3-molecule
```

**You should see:**

```
python3-molecule-6.0.3-*.mga10
```

That is **September 2021**. It is unusable for this toolchain, and it is not a matter of taste:

- It is a **Python module package**, not a `molecule` console script.
- It **predates `molecule-plugins` entirely.** In 2021, drivers were separate packages like
  `molecule-podman`. Today they live inside `molecule-plugins`.
- It predates the **`containers.podman`** collection, which the modern driver requires.

**If it is already installed, remove it:**

```bash
sudo dnf remove python3-molecule
```

**You should see:** a confirmation summary, ending with `Complete!`

> **Why removing it matters even though it ships no console script.** Mageia's system Python
> directories come *before* your per-user directory in the search order. So a `molecule` module
> in the system path is found **first**, and it will shadow the copy you install yourself in
> `~/.local`. You would end up debugging a seven-year-old module while looking at a 26.9.0
> version number. This is a real failure mode on any RPM-based system that ships a Python module
> package.

---

## 4. Rootless identity mapping is UNVERIFIED on Mageia — here is how to check

**This is the one place on this site where we cannot give you a tested answer, and we are not
going to pretend otherwise.**

Rootless Podman needs two helper programs, `newuidmap` and `newgidmap`. They let a container
act as a range of user IDs without being `root` on your machine. On Fedora they come from
`shadow-utils-subid`. On Ubuntu from `uidmap`. On Arch from `shadow`. **On Mageia, there is no
`uidmap` package at all** — zero matches for `uidmap`, `newuid` and `newgid` across all 38,861
packages. Only `shadow-utils 4.13` and the `lib64subid4` library are present.

On modern Fedora the binaries were split into a `shadow-utils-subid` subpackage. **Whether Mageia
put them back into its single `shadow-utils` package, or left them out, is UNVERIFIED.** We
could not read Mageia's package contents listing, and its own web interfaces are behind
JavaScript and cookie protection.

**So check your own machine. This is a read-only command:**

```bash
rpm -ql shadow-utils | grep -E 'newuidmap|newgidmap'
```

**If you see both paths, you are fine** — the binaries are there and you can skip to the
standard steps:

```bash
grep "^$USER:" /etc/subuid /etc/subgid
```

**You should see two lines:**

```
/etc/subuid:yourname:100000:65536
/etc/subgid:yourname:100000:65536
```

That is 65,536 reserved IDs, which is the standard block. Then follow
[rootless-podman.md](./rootless-podman.md) to prove rootless works.

**If the command prints nothing, there is no `newuidmap` on this system.** In that case
rootless Podman can only fall back to a **single-ID mapping**, which means most images will fail
to run as the users they expect. That failure mode is documented in
[Podman issue #21422](https://github.com/podman-container-tools/podman/issues/21422).

The recipe that works on every other platform — and that you can try here, because it is the
only thing available to try — is:

```bash
sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$USER"
```

Then **log out and log back in**, and then — do not skip this, it is the most forgotten command
in this whole area:

```bash
podman system migrate
```

**You should see:** the command returns to your prompt with no error. Check it:

```bash
echo $?
```

**You should see:**

```
0
```

> **If it still does not work, that is a real answer, not a failure on your part.** Mageia is
> the weakest platform on this site and this is the specific weak point. Tell us — the honest
> thing to do with an unverified path is to report what you find, not to invent a fix. Fedora,
> Ubuntu and Arch are all recommended over Mageia for exactly this reason.

---

## 5. Install Molecule in a virtual environment — the recommended route

**This is the recommended route on Mageia, and it is recommended because it is safe whether or
not Mageia's Python is `EXTERNALLY-MANAGED`.** The `pipx` route in section 2 may or may not
work; this route works either way.

```bash
python3 -m venv ~/.venvs/molecule
```

**You should see:** no output. Silence is success.

```bash
source ~/.venvs/molecule/bin/activate
```

**You should see:** your prompt now begins with `(.venvs/molecule)`. From here, `python3` and
`pip` point at the virtual environment, not at the system.

```bash
python3 -m pip install --upgrade pip
pip install molecule ansible-core "molecule-plugins[podman]"
```

**You should see** three `Successfully installed` lines, of the shape:

```
Successfully installed molecule-26.9.0 ...
Successfully installed ansible-core-2.20.6 ...
Successfully installed molecule-plugins-26.9.28 ...
```

**Note that `ansible-core` is in that same command, and that is not optional.** Molecule calls
`ansible-config` the instant it starts. If that program is not in the same environment as
`molecule`, the command exits with `ansible-config: not found` and a
`pip install molecule` on its own leaves you exactly there. Installing all three together means
the problem cannot occur.

> **If you prefer pipx and section 2 worked**, the equivalent is one command:
>
> ```bash
> pipx install molecule ansible-core molecule-plugins
> ```
>
> Both routes end in the same place: `molecule`, `ansible-config` and the driver in one
> isolated environment.

Verify:

```bash
molecule --version
```

**You should see:**

```
molecule 26.9.0 using ansible-core 2.20.6
```

**If you see this instead, stop and fix it now:**

```
ansible-config: not found
```

The fix is to reinstall into the same environment with `ansible-core` included:

```bash
pip install molecule ansible-core "molecule-plugins[podman]"
molecule --version
```

```bash
molecule drivers
```

**You should see** a list of driver names, one per line, including:

```
podman
```

Finally, prove the container engine works:

```bash
podman run --rm alpine id
```

**You should see:**

```
uid=0(root) gid=0(root) groups=0(root)
```

**Remember to leave the virtual environment activated** in any terminal where you want to run
Molecule, or re-activate it with `source ~/.venvs/molecule/bin/activate` each time.

---

## What the internet still gets wrong

> **"`sudo dnf install molecule` on Mageia."** There is no `molecule` package. There is
> `python3-molecule`, which is `6.0.3` from **September 2021** and cannot run this toolchain.
> Installing it is worse than not installing it, because it shadows your own install — see
> section 3.
>
> **"Mageia has pipx."** It does not. Zero matches across all 38,861 packages in `core/release`,
> and none in `tainted` either.
>
> **"Just add the `uidmap` package."** There is no `uidmap` package on Mageia 10. That is why
> section 4 is a check rather than a fix, and why it is marked UNVERIFIED rather than
> presented as solved.
>
> **"Skip the virtual environment, `pip install --user` is fine."** It may not be: Mageia 10's
> PEP 668 `EXTERNALLY-MANAGED` status is unverified. The virtual environment works either way,
> which is why it is what this page recommends.
>
> **"Set `privileged: true` to get systemd working."** No. See
> [systemd-in-containers.md](../systemd-in-containers.md) §11.

---

## Verify

You have verified the toolchain by hand. Now run the one script that checks the things you
cannot check by eye — including cgroup v2, which is **UNVERIFIED on Mageia** (its kernel is
`6.18.35`, which suggests yes, but it was never measured).

→ **[Run the pre-flight check →](../preflight.md)**

The script is read-only: it never installs anything, never asks for `sudo`, and never writes outside
Podman's own storage directory, which `podman` itself may create on
first use. When it is green, your host is ready — and on Mageia, that is a genuinely earned
result.

---

## Next

- **Pre-flight passed** → [Quickstart](../quickstart.md). Build your first passing test.
- **Section 4 printed nothing** → read that section again; it is the specific Mageia weak point,
  and [Troubleshooting](../troubleshooting.md) may have more.
- **You want to understand the identity mapping** →
  [Rootless Podman](./rootless-podman.md), the one chore shared by all four Linux platforms.
- **You are considering switching** → [Fedora](./fedora.md) is the shortest path and has none of
  these three problems. [Ubuntu 26.04](./ubuntu.md) is the current LTS and its only complication
  is a documented one with a documented fix.

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md). Distribution and product names are
used to identify the software being discussed, not to imply endorsement. The Podman quotation is
from its own issue tracker, cited in [Sources](#sources).

---

## Sources

- <https://mirrors.kernel.org/mageia/distrib/10/x86_64/media/core/release/> — the authoritative
  38,861-package listing behind every version and every "NOT PRESENT" claim on this page
- <https://www.mageia.org/en/10/> — Mageia 10, released July 2026
- <https://blog.mageia.org/en/2026/09/25/end-of-support-for-mageia-9/> — Mageia 9 end of support
- <https://github.com/podman-container-tools/podman/issues/21422> — the single-ID-mapping
  failure mode when `newuidmap` is absent, referenced in section 4
- <https://pypi.org/project/molecule/>, <https://pypi.org/project/molecule-plugins/> and
  <https://pypi.org/project/ansible-core/> — the three Python packages
- <https://docs.ansible.com/projects/molecule/installation/> — Molecule's installation guidance
- <https://pipx.pypa.io/stable/> — pipx, MIT-licensed
- Internal, reproducible: the package table is
  [`03-platform-install-matrix.md` §5.3–5.4](../../.research/03-platform-install-matrix.md);
  the install commands are quoted from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §5.6
