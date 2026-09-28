# Ubuntu — install Molecule and Podman

> **You are here:** [Docs home](../index.md) → [Install](./index.md) → **Ubuntu** → [Quickstart](../quickstart.md)

**What you will be able to do:** go from a fresh Ubuntu machine to a passing pre-flight check,
and deal correctly with the one thing that breaks on Ubuntu 24.04 — a security layer called
AppArmor that can block containers outright.

**Read section 3 before you start testing containers.** It is the Ubuntu-only problem on this
site, and it presents as a confusing permission error with no obvious cause.

---

## Are you in the right place?

Two Ubuntu releases are documented here, and they are **not** equivalent.

```bash
lsb_release -rs
```

**You should see**, one of:

```
26.04
```

```
24.04
```

If `lsb_release` is not installed, this always works instead:

```bash
. /etc/os-release && echo "$NAME $VERSION_ID ($VERSION_CODENAME)"
```

**You should see**, one of `Ubuntu 26.04 (Resolute Raccoon)` or
`Ubuntu 24.04.5 LTS (Noble Numbat)`.

| Release | Name | Podman it ships | Verdict |
|---|---|---|---|
| **26.04 LTS** | Resolute Raccoon | `5.7.0` | **Recommended.** Current, and everything on this page applies. |
| 24.04 LTS | Noble Numbat | `4.9.3` ⚠ | Still supported until **31 May 2029**. Works, but Podman is from **2022**. |
| 25.10 | Questing Quokka | `5.4.2` | The interim release. Not covered here. |
| ~~25.04~~ | — | — | **This release never existed.** The interim between 24.04 and 25.10 was skipped. Plenty of blog posts still refer to it; ignore them. |

> Ubuntu 24.04's other verified baseline facts, in case you need them: Linux kernel `6.8`,
> systemd `v255.4`, Python 3.12, AppArmor `4.0.1`, and security maintenance until 31 May 2029
> (extendable with Ubuntu Pro or the Legacy add-on).

---

## Dependencies, itemised

Every package, what it is for, and where it comes from. The "24.04" column is the only place
the two releases differ apart from Podman itself.

| Package | What it is for | Native or pipx | 26.04 version | 24.04 version |
|---|---|---|---|---|
| `podman` | **The container engine.** Creates, starts and stops your test container. | **Native** — apt | `5.7.0` | `4.9.3` ⚠ 2022 |
| `podman-remote` | The **remote client** half of Podman, for talking to an engine elsewhere. Optional; install it if you prefer that route. | **Native** — apt | `5.7.0` | `4.9.3` |
| `ansible-core` | **Ansible's core engine.** Provides `ansible-config`, which Molecule calls the instant it starts. | **Native** — apt | `2.20.1` | `2.16.3` |
| `uidmap` | Installs `newuidmap` and `newgidmap`, the two helper programs a rootless container needs in order to act as many user IDs. | **Native** — apt | Recommends of `podman` | Recommends of `podman` |
| `passt` | **Rootless networking.** Lets a container with no network privileges still make connections. | **Native** — apt | `passt` | `passt` |
| `slirp4netns` | Older rootless networking. **Podman 4.9 on 24.04 may still want it**; on 26.04 it is not needed. | **Native** — apt | not needed | may be needed |
| `fuse-overlayfs` | A fallback for rootless container storage on filesystems without native overlay support. | **Native** — apt | `fuse-overlayfs` | `fuse-overlayfs` |
| `git` | Molecule's build step needs it, and you will want it for your own files. | **Native** — apt | `git` | `git` |
| `pipx` | **Installs Python programs into their own isolated folder.** How Molecule gets onto your machine. | **Native** — apt | `1.4.3-1` | `1.4.3-1` |
| `molecule` | **The test driver itself.** | **pipx** — Ubuntu has no package | `26.9.0` | `26.9.0` |
| `molecule-plugins` | **The Podman driver.** Not part of Molecule, and in no distribution's repository. | **pipx** | `26.9.28` | `26.9.28` |

**What Ubuntu does *not* have:** a `molecule` package, in any suite, in any release. A full
package search returns exactly one hit, and it is not it. And `molecule-plugins` is in no
repository anywhere. Both come from Python.

> **A Personal Package Archive (PPA) is not required and this page does not use one.** Ubuntu's
> own upstream advice for a newer Ansible is a PPA, and we are deliberately not using one: a PPA
> is a third-party repository you would be adding root-level trust to for a tool this site does
> not need. The versions in the table above are all sufficient.

---

## 1. Install the packages

```bash
sudo apt install -y podman uidmap passt slirp4netns fuse-overlayfs git pipx ansible-core
```

**You should see:** a list of newly installed packages, ending with a line like:

```
Setting up podman (5.7.0+ds2-3build1) ...
```

> On 24.04, add `podman-remote` to that list if you would rather use the remote client.

Then check which Podman you actually got. **This step matters, because 24.04 and 26.04 differ:**

```bash
podman --version
```

**You should see on 26.04:**

```
podman version 5.7.0
```

**You should see on 24.04:**

```
podman version 4.9.3
```

---

## 2. Podman on Ubuntu 24.04 is old, and here is what that means

Ubuntu 24.04 ships `podman 4.9.3` — a **2022** release, and its source package is still
Debian's inherited `libpod`. Ubuntu 26.04 re-based onto its own `podman` source package at
`5.7.0`.

This is not a warning we invented. It is a real compatibility boundary. The Molecule Podman
driver expects modern Podman behaviour: `pasta` networking, cgroup v2 and `netavark` container
networking. On 24.04 it is talking to a 2022 codebase, and the networking backend is still the
older CNI-era tooling rather than `netavark`.

| Aspect | 24.04 LTS | 26.04 LTS |
|---|---|---|
| `podman` | `4.9.3` (2022) | `5.7.0` |
| Networking backend | containernetworking-plugins (CNI era) | `netavark` (a hard dependency of `podman`) |
| Rootless network default | `slirp4netns`-era | `pasta` |
| `ansible-core` | `2.16.3` | `2.20.1` |
| Verdict | works, but stale | **recommended** |

**Both are documented here and both are supported.** 24.04 is in standard security maintenance
until May 2029. If you have a choice, upgrade to 26.04. If you are on 24.04 and it works for
you, carry on reading.

---

## 3. Ubuntu's user-namespace restriction — read this before you blame Podman

This is the Ubuntu-specific failure on this site, and it is worth understanding rather than
copy-pasting past.

**AppArmor** is Ubuntu's security layer. It decides, per program, what that program is allowed
to do. Since Ubuntu 23.10, AppArmor has enforced a new rule: **an ordinary program may only
create a *user namespace* if it is confined and its AppArmor profile contains the `userns,`
rule.** A user namespace is a Linux feature that lets a process appear to be `root` *inside a
sandbox* while still being your ordinary user on the host. Rootless Podman is built on exactly
this feature — so if AppArmor blocks it, Podman stops.

The rule, verbatim from Ubuntu's announcement:

> "Unprivileged processes will only be able to create user namespaces if they are confined and
> have the `userns,` rule in their AppArmor profile (or if they have `CAP_SYS_ADMIN`)."

Unconfined processes with no such rule are **denied**.

### 3a. Check whether you are affected

Two commands tell you the whole story:

```bash
sysctl kernel.apparmor_restrict_unprivileged_userns
podman run --rm alpine sh -c 'echo userns-ok'
```

**If you are *not* affected, you should see:**

```
kernel.apparmor_restrict_unprivileged_userns = 0
userns-ok
```

**If the first line is `= 1`, the restriction is active.** If the second command fails with a
permission error instead of printing `userns-ok`, the kernel log will name the reason — this is
the fingerprint to look for:

```bash
sudo journalctl -k --since "5 min ago" | grep -E 'userns_create|apparmor="DENIED"'
```

**You should see a line containing:**

```
apparmor="DENIED" operation="userns_create" ... error=-13
```

Either way, go to 3c for the fix.

> **UNVERIFIED — whether this restriction is active on Ubuntu 26.04.** The mechanism was
> introduced in 23.10 and has never been reverted, so 26.04 almost certainly inherits it — but
> the research session never captured a 26.04 denial directly, and it never confirmed the status
> on 25.10 either. **So check, do not assume.** The `sysctl` command above is the one-line live
> check, and it takes two seconds. Run it on whichever release you have.

### 3b. Do not confuse the two similar settings

There are two kernel settings with confusingly similar names. Only one of them is the 24.04
problem.

| Setting | What it is | Is it your problem? |
|---|---|---|
| `kernel.apparmor_restrict_unprivileged_userns` | Ubuntu's per-program AppArmor restriction. **This is the one.** | **Yes.** |
| `kernel.unprivileged_userns_clone` | The **legacy**, all-or-nothing switch that disables user namespaces for the *entire* system. | **No.** Turning it off is not the fix, and disabling it wholesale is exactly what Fix B below warns against. |

### 3c. Fix A — narrow, and the one to use

Give Podman **its own** AppArmor profile that permits making user namespaces, and leave the
global restriction switched on. This is the approach Ubuntu 24.04 shipped a new profile flag
(`flags=(unconfined)`) to enable.

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

**You should see:** no output, and your prompt back. Silence is success here.

To inspect the effective AppArmor configuration at any time:

```bash
systemd-analyze cat-config apparmor.d
```

Two things to check. **Is your `podman` binary at `/usr/bin/podman`?** If not, change the path in
the profile above — find out with `which podman`. And **does Ubuntu already ship a profile for
you?** 24.04 ships AppArmor `4.0.1`, which is new enough to support the `unconfined` flag above:

```bash
ls /etc/apparmor.d/ | grep -iE 'podman|container|userns'
```

**You should see:** no matching profile, or one that does not cover `podman`.

> **UNVERIFIED — whether Canonical ships a ready-made profile for `podman`.** Only the Chromium
> example is publicly documented. That is why the check is here: run it, and if Ubuntu has
> already provided something, use theirs instead of writing one.

Then confirm the fix took:

```bash
podman run --rm alpine sh -c 'echo userns-ok'
```

**You should see:**

```
userns-ok
```

### 3d. Fix B — broad, and the fallback

If Fix A does not resolve it, the documented fallback turns the restriction off for the whole
system. Chromium's developers documented exactly these two commands. **Now:**

```bash
echo 0 | sudo tee /proc/sys/kernel/apparmor_restrict_unprivileged_userns
```

**And to make it survive a reboot:**

```bash
echo kernel.apparmor_restrict_unprivileged_userns=0 | \
  sudo tee /etc/sysctl.d/60-apparmor-namespace.conf
```

> **Say this plainly: Fix B switches off a real security control.** 44% of Google's observed
> Linux exploits needed unprivileged user namespaces. Turning the restriction off is not
> cosmetic — it is a trade of real security for convenience, across your whole system, for every
> program. **Prefer Fix A.** Reach for Fix B only when Fix A does not work, and know what you are
> giving up.

**And to undo Fix B** — delete the drop-in, then put the restriction back:

```bash
sudo rm -f /etc/sysctl.d/60-apparmor-namespace.conf
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=1
```

The first command removes the persistence; the second takes effect immediately without it. Do
not reach for `sudo sysctl --system` here either — it re-reads *every* sysctl under `/etc`, not
just this knob, so any other drop-in on the machine is re-applied as a side effect.

---

## 4. Install pipx, Molecule, and the driver

First put pipx's application folder on your `PATH` — the list of folders your shell searches
when you type a command name:

```bash
pipx ensurepath
```

**You should see:** confirmation that `/home/<yourname>/.local/bin` was added, or that it was
already there. Then **close your terminal and open a new one**, or run `source ~/.bashrc`.

Now the toolchain. **Install `ansible-core` in the same command as `molecule`** — Molecule calls
`ansible-config` the instant it starts, and if that program is not in the same environment, the
`molecule` command is dead on arrival.

```bash
pipx install molecule ansible-core molecule-plugins
```

**You should see** three "installed package" lines, all in the same virtual environment:

```
installed package molecule 26.9.0, installed using Python 3.12
   in virtual environment pipx-venvs/molecule
installed package ansible-core 2.20.6, installed using Python 3.12
   in virtual environment pipx-venvs/molecule
installed package molecule-plugins 26.9.28, installed using Python 3.12
   in virtual environment pipx-venvs/molecule
```

> **The equivalent two-step route**, as recorded in the canonical reference file:
>
> ```bash
> pipx install molecule ansible-core
> pipx inject molecule molecule-plugins
> ```
>
> `pipx inject` adds a package to an environment that already exists. Both end identically.

---

## 5. Verify — four commands, in this order

### 5a. Molecule starts at all

```bash
molecule --version
```

**You should see:**

```
molecule 26.9.0 using ansible-core 2.20.6
```

**If you instead see this, stop and fix it now:**

```
ansible-config: not found
```

That means `ansible-core` is missing from Molecule's environment. Repair it without starting
over — `pipx inject molecule ansible-core` — and re-run `molecule --version`. Do not carry on
until the version line prints.

### 5b. The Podman driver is loaded

```bash
molecule drivers
```

**You should see** a list of driver names, one per line, including:

```
podman
```

### 5c. Rootless containers actually run

This is the Ubuntu-specific check, and it is where a missed AppArmor fix shows up.

```bash
podman run --rm alpine sh -c 'echo userns-ok'
podman info --format '{{.Host.Security.Rootless}}'
```

**You should see**, from the two commands in order:

```
userns-ok
true
```

**If you see a permission error naming `userns_create`, go back to section 3.** Do not go
looking for a Podman bug. This is AppArmor, and it has a documented fix.

### 5d. Check the SELinux analogue — with `getenforce`, never with `podman info`

Ubuntu does not ship SELinux (Security-Enhanced Linux) — it ships AppArmor instead — but the
`podman` package is shared across distributions, so it is worth knowing the trap:

> **Do not run `podman info --format '{{.Host.Security.SelinuxEnabled}}'`.** On Podman 5.8.7
> that template **errors**: `can't evaluate field SelinuxEnabled in type define.SecurityInfo`.
> The field does not exist. If you want the security block, use
> `podman info --format '{{json .Host.Security}}'`.
>
> The field that *does* work is `{{.Host.Security.Rootless}}`, used in 5c above. Only the SELinux
> field is broken.
>
> On a machine that does run SELinux — Fedora, Mageia, RHEL — use `getenforce` to read its state.
> It is a small separate program and it always works.

---

## What the internet still gets wrong

> **"Ubuntu 24.04 has no `molecule` package, so you need a PPA."** No. Ubuntu has no `molecule`
> package in *any* suite, and a PPA is not required for anything on this page. The versions in
> the table above work. A PPA adds root-level trust to a third-party repository to solve a
> problem that does not exist.
>
> **"The fix is to disable user namespaces."** That is Fix B, and it is the *fallback*, not the
> fix. The narrow per-program AppArmor profile in Fix A exists, Ubuntu shipped a new profile flag
> specifically to enable it, and it leaves the global restriction on. Use Fix A.
>
> **"You need to set `kernel.unprivileged_userns_clone=1` on Ubuntu."** That is the legacy
> all-or-nothing switch and it is not the 24.04 issue. Setting it does not fix anything here.
>
> **"24.04 is fine, Podman is Podman."** 24.04's Podman is `4.9.3` from 2022 and predates
> `pasta` and `netavark`. It works, but it is a "works, but stale" tier and you should know you
> are on it.

---

## Verify

You have verified the toolchain by hand. Now run the one script that checks the things you
cannot check by eye — including the cgroup v2 requirement, which 24.04's older Podman interacts
with differently.

→ **[Run the pre-flight check →](../preflight.md)**

The script is read-only: it never installs anything, never asks for `sudo`, and never writes outside
Podman's own storage directory, which `podman` itself may create on
first use. When it is green, your host is ready.

---

## Next

- **Pre-flight passed** → [Quickstart](../quickstart.md). Build your first passing test.
- **AppArmor still blocking you** → section 3 above, then
  [Troubleshooting](../troubleshooting.md).
- **You want to understand the identity mapping** →
  [Rootless Podman](./rootless-podman.md), the one chore shared by all four Linux platforms.
- **You are on 24.04 and everything feels fragile** → the honest advice is to move to 26.04
  LTS. Start again from [Are you in the right place?](#are-you-in-the-right-place).

---

## Attribution

This page displays no brand marks or logos. Brand and licence records live in
[`../../assets/ATTRIBUTION.md`](../../assets/ATTRIBUTION.md). Distribution and product names are
used to identify the software being discussed, not to imply endorsement. The Ubuntu and
Chromium quotations are from their own documentation, cited in [Sources](#sources).

---

## Sources

- <https://releases.ubuntu.com/> — 26.04.1 is the current LTS; 24.04.5 is in standard support; 25.04 never existed
- <https://packages.ubuntu.com/noble/podman> and <https://packages.ubuntu.com/resolute/podman> — 24.04 `podman 4.9.3+ds1-1ubuntu0.1`, 26.04 `podman 5.7.0+ds2-3build1`
- <https://packages.ubuntu.com/noble/ansible-core> and <https://packages.ubuntu.com/resolute/ansible-core> — 24.04 `ansible-core 2.16.3-0ubuntu2`, 26.04 `ansible-core 2.20.1-1`
- <https://packages.ubuntu.com/noble/pipx> — `pipx 1.4.3-1`
- <https://packages.ubuntu.com/search?keywords=molecule&searchon=names&suite=all&section=all> — proves Ubuntu has no `molecule` package in any suite
- <https://ubuntu.com/blog/ubuntu-23-10-restricted-unprivileged-user-namespaces> — the restriction, quoted verbatim in section 3
- <https://documentation.ubuntu.com/release-notes/24.04/> — the AppArmor `unconfined` profile flag
- <https://documentation.ubuntu.com/security/security-features/privilege-restriction/apparmor> — 24.04 ships AppArmor `4.0.1`
- <https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md> — the exact Fix B sysctl commands, and the 44% figure
- <https://discourse.ubuntu.com/t/ubuntu-24-04-lts-noble-numbat-release-notes/39890> — kernel 6.8, systemd v255.4, Python 3.12, support until 31 May 2029
- <https://pypi.org/project/molecule/> and <https://pypi.org/project/molecule-plugins/> — the two Python packages
- <https://pipx.pypa.io/stable/how-to/install-pipx.html> — `pipx ensurepath`
- Internal, reproducible: the package table is
  [`03-platform-install-matrix.md` §7.1](../../.research/03-platform-install-matrix.md) Tables A
  and B; the install and AppArmor commands are quoted from
  [`../REFERENCE-CONFIG.md`](../REFERENCE-CONFIG.md) §5.3
