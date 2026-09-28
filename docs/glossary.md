# Glossary

> **You are here:** [Docs home](./index.md) → **Glossary** → [How Molecule works](./concepts/how-molecule-works.md)

**What you will be able to do:** look up any word this site uses, in one or two sentences, in
plain language, without having to read a page to find out what it meant.

Every term below is spelled out in full on first use, and expanded on first use everywhere in
this site. This page is the authority. If a definition here and a definition on another page
ever disagree, this page is wrong and should be fixed.

---

## A

### Ansible

The open-source automation tool that applies your configuration to machines. It reads YAML
files, connects to the machines you listed, and runs the tasks in them. Ansible is free
software from Red Hat, and its full documentation is free at
[docs.ansible.com](https://docs.ansible.com/).

### Ansible Core

The engine itself, without any pre-packaged content. It is what `ansible-core` installs, and it
is what Molecule calls. Anything you want beyond the engine — a module for a database, a role
for a web server — comes from a **collection** (see *collection*).

### Ansible collection

A downloadable bundle of Ansible content: modules, roles, playbooks and tests, published
under one name and version. This site uses one, `containers.podman`, and installs it with the
`dependency` step of a test run.

### Ansible Galaxy

The free public registry where Ansible collections and roles are published and downloaded. It
is to Ansible what a package repository is to your Linux distribution. Scenarios in this site
list what they need in a file called `requirements.yml`, and the `dependency` step fetches it
from there.

### AppArmor

A mandatory access-control system, the security mechanism Ubuntu and Debian use by default. It
can be configured to stop a program from creating the user namespaces that rootless containers
need, and it is the reason the [Ubuntu install page](./install/ubuntu.md) has a one-line check
in it. Fedora's equivalent is **SELinux**.

### ARM64 / x86-64

The two processor architectures this site is tested on and written for. **x86-64** is the
architecture of most Intel and AMD computers. **ARM64** (also written `aarch64`) is the
architecture of Apple Silicon Macs and a growing share of servers. Some Ansible modules behave
differently on the two, so a test that passes on one is not automatically proven on the other.

### assertion

A statement in your `verify.yml` that says what must be true, and fails the run if it is not.
Ansible's is `ansible.builtin.assert`. Molecule does not decide pass or fail on its own — your
assertions do.

### automation

Anything you wrote that changes a machine without you sitting in front of it. A role that
installs a web server is automation. The reason to test it is that automation runs at three in
the morning, repeatedly, and often to more machines than you expected.

---

## B

### bind mount

A folder from the host made visible inside a container at a path you choose. Podman writes them
`-v /host/path:/container/path`. Molecule's `safe_files:` option uses this to keep a file
available after the container is destroyed, which is useful for debugging a failed run.

---

## C

### CalVer

"Calendar versioning" — version numbers built from the date, so `26.9.0` means the year 2026,
month 9, release 0. **Molecule uses CalVer, so there is no Molecule "version 6" or "version
7"**, and any tutorial claiming otherwise predates the current release. The current release is
`26.9.0`.

### cgroup

A Linux *control group*: a kernel feature that collects processes together so the system can
limit and account for their CPU time, memory, and number of processes. `systemd` does not
merely use cgroups — it **manages itself through them**, which is why it cannot start without
them.

### cgroup v1

The original, split control-group design, where every resource type had its own hierarchy and
its own set of mount points. It is old, it is awkward, and it is effectively gone: **Podman 6.0
removed support for it entirely.** If you are reading a guide that assumes cgroup v1, it is old.

### cgroup v2

The unified control-group design, where every resource type shares one hierarchy. It is the
default on current Linux distributions. **Running `systemd` inside a container requires a host
on cgroup v2.** The [pre-flight check](./preflight.md) tests for it in about a second.

### cgroup delegation

Handing a container its own slice of the control-group tree, so that processes inside it can
create and manage their own groups instead of only reading the host's. This happens automatically
once systemd mode engages. Setting `systemd: always` guarantees it engages without depending on
Podman auto-detection — see [`systemd`](./reference/molecule-yml.md#systemd) for the measured rule
and [systemd in containers](./systemd-in-containers.md) for the full picture.

### collection

Short for **Ansible collection**. Also, in the container world, a bundle of images sharing a
name. Both meanings appear in this site; where it matters, the page says which.

### cleanup

A test step that removes artefacts a previous run left behind. It appears **twice** in the
standard sequence — once near the start so a crashed run cannot poison the next one, and once
at the end. It reads a file called `cleanup.yml`, which Molecule does not create for you.

### Converge

The act of *applying* your work. The file `converge.yml` is where you put it, and the
`converge` step is the one that runs. This is the step that does the actual work of a test.

**See also:** idempotence, verify.

### converge.yml

The file that applies your role, playbook or collection to the platforms. You edit this. It is
the first of the two files that carry your test's meaning; the second is `verify.yml`.

### `container_systemd`

The Podman option that decides how the container is told to behave when it is being used to run
a service. In `molecule.yml` you set `systemd: always` — **never `true` and never `false`.**
`always` is the **robust** choice: it removes the dependence on Podman's auto-detection, which only
engages systemd mode when the container command is literally `systemd`, `/usr/sbin/init`,
`/sbin/init` or `/usr/local/sbin/init`. It becomes **genuinely required** the moment `command:` is
not literally an init. Full rule: [`systemd`](./reference/molecule-yml.md#systemd). See also
[systemd in containers](./systemd-in-containers.md).

### container

A process, or a small set of processes, that the operating system shows you as if it were its
own machine — but which shares the host's kernel. Containers start in about a second and can
be thrown away instantly, which is exactly what makes them useful for tests.

**See also:** container image, container runtime, cgroup v2.

### container engine

The program that creates and runs containers. This site uses **Podman**, never Docker, and the
difference is not cosmetic: Podman runs rootless by default, needs no daemon, and needs no
root privileges at all.

### container image

A frozen filesystem plus a start command — the thing you pull down and run. An image must
contain **Python** for Ansible's built-in tasks to work inside it, which is why a bare `alpine`
image fails and a `ubi9/ubi-init` image works.

### container runtime

The lower-level program a container engine calls to actually start a container. On Linux this
is usually `crun` or `runc`. You do not install or configure one yourself.

### Containerfile / Dockerfile

A text file describing how to *build* a container image: what to start from, what to install,
what to run. Podman and `docker build` read `Containerfile`; `Dockerfile` is the older name and
both tools read it too. **You do not need one for this site** — the recommended image is
prebuilt — but [custom images](./authoring/custom-images.md) covers writing one if you want
your own.

### Continuous Integration (CI)

The practice of running your tests automatically every time you push code, on a machine you do
not sit at. "CI" is the abbreviation; expand it the first time in any document. Molecule has no
idea CI exists — [the CI page](./authoring/ci.md) shows how to run it *inside* one.

### `crun`

The low-level program that starts containers on Linux. You do not install it yourself, but you
will see its name in an error message one day. The other common one is `runc`.

---

## D

### daemon

A background program that runs continuously and answers requests. Historically a Unix
init system's own process was called a daemon, and a lot of vocabulary grew around it. This
site uses the word **once**, in this entry, and then prefers *service* and *init* instead.

### delegation

Handing a task to something else to do it: another machine, a container, a remote process. In
the Molecule vocabulary the closely related term is the **`default` driver**, whose internal
class is named `Delegated` — meaning it hands the work of creating machines to you, the reader,
rather than doing it. A frequently repeated error is that Molecule depends on a Python library
called `delegator`; it does not, and that library has nothing to do with Molecule.

### dependency

A test step that installs the collections and roles listed in `requirements.yml`, before
anything else runs. It runs first in the standard sequence so every later step has what it
needs. The first time a scenario runs, this is where `containers.podman` arrives.

### Docker

A container engine, and the one most Molecule tutorials on the internet assume you are using.
This site deliberately does not use it, and several of the corrections in
[systemd in containers](./systemd-in-containers.md) only exist because the advice was written
for Docker and was never true for Podman.

### driver

The part of Molecule that knows how to **create and destroy** the machines your test needs.
This site uses the `podman` driver, which comes from the separate **`molecule-plugins`**
package. Check yours is installed with `molecule drivers`, which should print a list including
`podman`.

**See also:** provisioner, `default` driver.

### `default` driver

Molecule's built-in driver, used when you name no driver at all. It **creates no containers and
destroys no containers** — its own description says the user is expected to manage test
resources. If you see a tutorial that runs Molecule with no driver and no containers, that is
this driver, working as designed, testing nothing.

### destroy

A test step that deletes the platforms. It runs **twice** in the standard sequence — at the
start and at the end — so a run that crashed halfway cannot leave a container that the next run
tries to reuse.

---

## E

### environment variable

A value set outside a program, in the shell that launches it, and readable by everything that
runs. Molecule uses several to change its behaviour: `MOLECULE_PODMAN_EXECUTABLE` chooses
which Podman binary to run, and `MOLECULE_SCENARIO_DIRECTORY` tells a scenario where it is.
Full list: [environment variables](./reference/env-vars.md).

### exit code

The number a program hands back to the shell when it finishes: `0` means success, anything
else means failure. **One warning that matters here:** `molecule test` can exit `0` having
asserted nothing at all. See [the silent false pass](./concepts/how-molecule-works.md#10-verify).
The number to actually read is the `ok=` count in the verify summary.

---

## F

### `fqcn`

**Fully Qualified Collection Name** — the Ansible convention for naming a module or plugin
unambiguously by writing the collection name, then the plugin name, separated by a dot. The
one this site cares about is `containers.podman.podman`, the Podman connection plugin. Writing
it in full means Ansible can never mistake it for a same-named plugin in another collection.

### Fully Qualified Collection Name

See *fqcn*, above.

### Fedora

A Red Hat–backed Linux distribution and the platform this site was **live-verified on**. It
ships Podman, `ansible-core`, SELinux and cgroup v2 in current versions, which makes it the
smoothest of the five supported platforms. Instructions: [install on Fedora](./install/fedora.md).

---

## H

### host_vars

A folder in an Ansible inventory holding settings for one machine rather than for a group. The
`molecule.yml` in this site puts the container's connection setting in `host_vars` for
`instance`.

### host_vars / group_vars

The two ways Ansible inventory attaches settings to things: `host_vars` for a single machine,
`group_vars` for every machine in a group. **A trap specific to this project:** a value in
`group_vars` outranks an inline `vars:` on the same group, so a stray `group_vars/molecule.yml`
can silently override what you wrote in `molecule.yml`. Explained in
[systemd in containers](./systemd-in-containers.md).

---

## I

### idempotence

The property that applying the same change twice leaves exactly the same result. A convergent
role is idempotent. Molecule tests this for you automatically: the `idempotence` step runs
`converge.yml` a second time and fails the run if anything changed. It is the step beginners
most often forget exists, and the one that most improves real code — a non-idempotent role
will fight any tool that runs it later.

### image

Short for **container image**. See the full entry above.

### init

The first process to start in a system, and the one that starts everything else. Traditionally
called a *daemon*; see that entry for why this site avoids the word. In a container, the
process you start first becomes the container's **init**.

### init system

The program that starts and supervises the services on a machine. `systemd` is the init system
this site is about, and it **refuses to run unless it is the very first process in its
container** — which is why a container that does not start it prints `System has not been
booted with systemd as init system (PID 1)`.

### inventory

The list of machines Ansible is allowed to touch, with their addresses and settings. In a
Molecule scenario you do not write it by hand: Molecule generates it from the `platforms:` list
in your `molecule.yml`.

### iproute2

A standard Linux package holding the `ip` command. It is not part of the base installation on
every distribution, and without it a container has no way to configure its own networking —
which is a common cause of "my test hangs at the first task". On Fedora and Arch it comes with
the base system; on Ubuntu and Mageia you install it explicitly.

---

## J

### journal / journald

The system-wide log written by `systemd`. Inside a container, this is where your service's
output goes — which is why `podman logs` can be empty while the service is running perfectly.
Read it with `journalctl` instead. Explained in
[systemd in containers](./systemd-in-containers.md).

### journalctl

The command that reads the systemd journal. Inside a container, `journalctl -u <name>.service`
is how you see why a unit failed, and it works when `podman logs` shows you nothing.

### JSON

A plain-text format for structured data, written in curly brackets. Ansible's output is YAML;
the two Molecule actually reads are YAML. You meet JSON mostly in error messages and API
responses.

---

## L

### libkrun / applehv

The two hypervisor *providers* available to `podman machine` on macOS. They differ mainly in
how efficiently they translate macOS instructions into Linux ones. On an Apple Silicon Mac the
default is usually `applehv`. See [install on macOS](./install/macos.md).

### Linux

The operating system Podman and Ansible run on. On a Mac, Podman runs your containers inside a
Linux **virtual machine** rather than natively, because macOS has no Linux kernel.

---

## M

### Mageia

A community-maintained Linux distribution descended from Mandriva. It is one of this site's
five supported platforms, and the least comfortable: it has no `pipx` package, no `uidmap`
package, and a packaged Molecule old enough to be unusable — so the install needs a virtual
environment. Instructions: [install on Mageia](./install/mageia.md).

### Mac / macOS

The two names for Apple's desktop operating system. Containers cannot run natively on it,
because it has no Linux kernel; Podman runs them inside a small Linux **virtual machine**
instead. Only Apple Silicon Macs are supported — Intel Mac support was removed in Podman 6.0.
See [install on macOS](./install/macos.md).

### Molecule

The test harness this whole site is about: it builds a throwaway environment, applies your
Ansible content to it, checks the result, and throws the environment away. Current release
`26.9.0`, versioned by **CalVer**.

### `molecule-plugins`

The separate Python distribution that provides the **`podman` driver**, along with drivers for
Docker and several clouds. It is **not** Molecule, and it is **not in any Linux distribution's
package repository** — which is why the install pages on this site use `pipx` or `pip` for it.
Check that you have it with `molecule drivers`.

### `molecule.yml`

The settings file at the heart of a scenario. It names the driver, lists the platforms (which
become containers), names the provisioner, and lists the test steps in order. It must live at
`molecule/<scenario>/molecule.yml` — a flat file at the project root does not work, and the
error it produces does not explain why. The canonical versions are in
[`REFERENCE-CONFIG.md`](./REFERENCE-CONFIG.md); every page in this site links there rather
than re-typing the file.

### Molecule's `default` driver

See *`default` driver*.

---

## N

### namespace

A named, isolated view of system resources. The kind that matters here is a **user namespace**:
it lets an unprivileged process appear to be `root` inside a boundary, with the ability to map
a range of host user IDs to a range of IDs inside. This is the mechanism that makes rootless
containers possible without any privileges at all.

### `newuidmap`

A small helper program that lets an ordinary user map a *range* of user IDs into a user
namespace. Without it, rootless containers can only use a single ID and much less is possible.
It ships in the `uidmap` package on most distributions.

---

## O

### OCI

**Open Container Initiative** — the industry group whose specification Podman implements, so
Podman can talk to images and containers produced by other tools. "OCI image" and "OCI runtime"
in an error message almost always mean "something built to that shared standard, probably fine,
look at the next line of the message".

### OCI runtime

The low-level program that actually creates and starts a container, per the OCI standard. On
Linux this is `crun` or `runc`. Podman is the *engine*; the OCI runtime is the thing under it.

---

## P

### PATH

The list of folders your shell searches, in order, when you type a command name. It is the
cause of this site's most common install failure: Molecule runs `ansible-config` at start-up,
so if that program is not on the same `PATH` as `molecule`, the command dies with
`ansible-config: not found`. It is a `PATH` problem *and* a missing-package problem, and both
have the same fix: install `molecule`, `ansible-core` and `molecule-plugins` **together**, in
one environment.

### PID

**Process identifier** — the number the operating system gives each running process. Linux
always has one process numbered 1, and everything else descends from it.

### PID 1

The number of the very first process in any system or container. **`systemd` will only run as
PID 1**; started as anything else, it checks, finds something else in first place, and prints
`System has not been booted with systemd as init system (PID 1)`. That one check causes most of
the beginner failures in this whole subject, which is why
[the systemd page](./systemd-in-containers.md) leads with it.

### platform

One machine your test needs. In a container-based scenario, each entry in the `platforms:`
list becomes one container, and the `name:` you give it is both the container's name and its
hostname in Ansible's inventory.

### playbook

A YAML file containing one or more **plays** — a list of tasks to run against a group of
machines. `converge.yml` and `verify.yml` are both playbooks. A role is what a playbook
usually uses; a playbook is what runs it.

### podman

The container engine this site uses. It runs **rootless** by default, needs no background
daemon, and — the detail that trips up most tutorials — is driven through its **command-line
tool**, not through a socket. Free and open source, from the Linux Foundation's Cloud Native
Computing Foundation (CNCF).

### `podman machine`

On macOS, a small Linux virtual machine that Podman manages and runs containers inside. Created
with `podman machine init` and started with `podman machine start`. It is why macOS commands
in this site have an extra step: you run them *inside* the machine.

### prepare

A test step that applies changes to the platforms *before* your own work runs — installing
fixtures, typically. Molecule does not create a `prepare.yml` for you; you write it, or you
remove the step from the sequence.

### privilege

The ability to do something you would otherwise not be allowed to. Containers run with a small
set of capabilities by default, and `SYS_ADMIN` is the one most often needed by a systemd unit
using `PrivateTmp=` or similar. **`privileged: true` is not needed for systemd and makes it
worse** — see [the myths table](./systemd-in-containers.md).

### process

A running program, as the operating system sees it. Every container starts as exactly one
process, and whatever that process is becomes PID 1 inside.

### provisioner

The part of Molecule that knows how to *do Ansible work*, as opposed to the driver that creates
machines. In every scenario on this site it is `ansible`, and it is the reason the project is
called a Molecule **Ansible** project at all.

---

## R

### `ready_files`

The counterpart to `safe_files`: files copied *out* of the container before it is destroyed, so
you can inspect them after a failed run. Set it in the driver's options in `molecule.yml`.

### registry

A server that stores container images. `registry.access.redhat.com` and `ghcr.io` are the two
used in this site, and both are free. Images are pulled by name and **tag** — the part after
the colon, where `:latest` means "whatever the newest build is".

### role

An Ansible packaging convention: a directory of tasks, templates, defaults and handlers that
does one job, named the same way everywhere so it can be reused. Roles are the most common
thing people test with Molecule. A role you install on a real machine *should not* be tested on
your laptop without a scenario — that is the whole point of this site.

### rootful

Running a container as the real `root` user on the host, with a daemon. Docker's default
model. Podman supports it, and this site never needs it.

### rootless

Running containers as an ordinary, unprivileged user — with no daemon and no `sudo`. A
rootless container cannot do more than the user who launched it, which is a feature: it means
your test cannot damage your machine. Podman's default, and the mode in which almost all CI runs
Molecule. It needs **user namespaces** and a range of IDs reserved for your account.

### `runc`

The low-level program that starts containers on Linux. `crun` is the newer alternative. Neither
is something you install by hand.

---

## S

### scenario

One whole disposable test environment: its own folder, its own `molecule.yml`, its own
playbooks, its own settings. `default` is the conventional name for the first one. A Molecule
project can hold several scenarios, and
[the multi-scenario page](./authoring/multi-scenario.md) covers when that is worth doing.

### SELinux

**Security-Enhanced Linux** — the mandatory access-control system Fedora ships by default, and
usually leaves in **Enforcing** mode. It decides which files a process is allowed to touch. The
good news, and a fact verified by execution: a systemd container works with SELinux enforcing
and no configuration changes at all. Ubuntu's equivalent is **AppArmor**.

### service

A long-running program managed by the init system — a web server, a database, a queue worker.
The practical definition for this site: a thing your role installs, and that `systemctl` can
report as `active`.

### service unit

The file that tells `systemd` how to run one service: where the program is, what arguments it
takes, when to start it, and what counts as healthy. It is the file your role writes, and the
thing your `verify.yml` asserts about. See [systemd in containers](./systemd-in-containers.md).

### shell

The program that reads what you type and runs it. On a Mac or Linux it is usually `bash` or
`zsh`. `PATH` is a shell setting, and `$USER` is a shell variable.

### side effect

A deliberate change made by a test, for the purpose of undoing it. The `side_effect` step lets
one scenario leave a resource behind so a second scenario can prove it cleans it up. See
[multi-scenario](./authoring/multi-scenario.md).

### socket

A file that programs use to talk to each other over a network, without a port number. You will
meet the phrase in this site's corrections: the Podman connection plugin **does not use one**,
it runs the `podman` command instead, which is why there is no `DOCKER_HOST` to set here.

### `subuid` / `subgid`

Two files, `/etc/subuid` and `/etc/subgid`, listing blocks of user and group IDs reserved for
ordinary users. A container running as your account needs a *range* of IDs, not one, to behave
like a real machine. If these are empty for your user, rootless containers cannot start. The
[pre-flight check](./preflight.md) reports this; the fix is on the
[rootless Podman page](./install/rootless-podman.md).

### subuid / subgid — the cross-reference

See `subuid` / `subgid`, above.

### syntax check

The `syntax` step: it checks that your playbooks can be parsed, without running them or
connecting to anything. It costs seconds and points at the exact line, which makes it the
cheapest failure you can have.

### systemd

The init system that starts and supervises services on a Linux machine, and the reason this
site exists. It manages itself through **cgroups**, it insists on being **PID 1**, and it will
not run in a container at all unless you ask Podman to prepare one properly. The whole of
[systemd in containers](./systemd-in-containers.md) is about that.

### systemd mode

What `--systemd=always` switches on in Podman. It does **not** start systemd for you — it
prepares the container so systemd *can* start: memory-only filesystems for `/run`, `/run/lock`,
`/tmp` and `/var/lib/journal`, a clean stop signal, and — the part that matters — the cgroup
filesystem mounted writable. Your image must still contain systemd, and your command must still
be an init.

### `systemctl`

The command you use to ask systemd questions: `systemctl is-system-running`,
`systemctl start`, `systemctl status`. Your `verify.yml` will use it over the
connection plugin.

### system image

A base filesystem with no application software installed, used as the starting point for
building your own. The recommended image on this site,
`registry.access.redhat.com/ubi9/ubi-init`, goes further: it already contains systemd and
Python, so there is nothing to build.

---

## T

### tag

The part of an image name after the colon. `ubi-init:latest` means "the newest published build
of this image." A tag is a *pointer*, not a fixed thing — it can be repointed — which is one
reason a test that passed last month can fail today.

### task

One step in a playbook: a name, a module, and its arguments. The `ok=` count in a Molecule
summary is the number of tasks that ran successfully, and it is the number that proves your
test did anything at all.

### terminal

The window you type into. On macOS and Linux the program providing it is called a **terminal
emulator**; on Windows, a terminal is a feature you usually add. Molecule runs in whatever
shell your terminal provides, which is why one of its troubleshooting entries is about `PATH`.

### test sequence

The ordered list of steps that `molecule test` runs, written in your own `molecule.yml` under
`scenario: test_sequence:`. You can shorten it, lengthen it or reorder it. Both standard values
are in [`REFERENCE-CONFIG.md`](./REFERENCE-CONFIG.md) §9, and every step is explained in
[how Molecule works](./concepts/how-molecule-works.md).

### TTY

**TeleType** — historically a physical terminal; today, an interactive shell session as opposed
to a script or a pipeline. Ansible's output looks different when it has one, which is why some
warnings appear in a terminal and not in CI logs.

---

## U

### unit

A file telling `systemd` about one thing it manages: a service, a mount point, a socket, a
target. A **`.service` unit** is the kind that matters here. Your role writes them; your
`verify.yml` asserts they are working.

### unit file

The file on disk that a `systemd` unit is defined in. Usually under
`/etc/systemd/system/`, `/usr/lib/systemd/system/` or `/lib/systemd/system/`. Inside a
container running systemd, the first of those is the one your role writes to.

### user namespace

See *namespace*, above.

---

## V

### verify

The act of **asserting** the outcome, in `verify.yml`. It is the only step in a Molecule run
that decides pass or fail, and the step most worth writing carefully — see
[writing tests](./authoring/writing-tests.md).

**See also:** convergence, assertion, the [silent false pass](./concepts/how-molecule-works.md#10-verify).

### `verify.yml`

The file that decides pass or fail. You edit this. A `verify.yml` that asserts nothing is worse
than no `verify.yml`, because Molecule will report success either way.

### virtual machine (VM)

A machine that runs its own operating system kernel, isolated from the host. Containers are
cheaper and faster but share the host's kernel; virtual machines do not. Podman uses one
underneath macOS, and Molecule can be pointed at one if your test needs a different kernel.

---

## W

### `wait_for`

An Ansible task that pauses until a condition holds — a port is open, a file exists, a service
is active. It is the usual way to survive a slow service start, and its `state:` value must be
one of `absent`, `drained`, `present`, `started` or `stopped`. A value outside that list is a
hard error on current `ansible-core` — one of the real defects found by running this site's
examples; see [`examples/VERIFICATION.md`](../examples/VERIFICATION.md).

### workspace

In CI, the machine a run happens on. In a Molecule scenario, the folder containing
`molecule/` — a *project root*, as Molecule calls it.

---

## Y

### YAML

**YAML Ain't Markup Language** — the indentation-based plain-text format Ansible playbooks,
`molecule.yml` and every config file in this site are written in. Two space rules matter more
than anything else: never use tabs, and never mix tab and space indentation. A YAML error is
what the `syntax` step exists to catch before anything runs.

### YAML Ain't Markup Language

See *YAML*, above.

---

## Terms this site deliberately avoids

A short list, so you know when a page is being precise on purpose.

- **"daemon"** — defined once, in the *daemon* entry above, and not used again. *Service* and
  *init* say what is meant.
- **"privileged"** — defined, and then discouraged. It is not the word to reach for when a
  systemd unit fails inside a container; `SYS_ADMIN` is the narrow, correct answer.
- **"Molecule 6" or "Molecule 7"** — there is no such version. Molecule uses **CalVer**, and
  the current release is `26.9.0`.
- **"pointing Ansible at the Podman socket"** — the connection plugin runs the `podman`
  **command**, not a socket. There is no `DOCKER_HOST` in this path.
- **"privileged mode for systemd"** — folklore, and it is actively harmful. See
  [the myths table](./systemd-in-containers.md).

---

## Next

- **New to all of this?** → [Docs home](./index.md), then the [quickstart](./quickstart.md).
- **Want the mental model behind these words?** → [How Molecule works](./concepts/how-molecule-works.md).
- **Want the commands?** → [Install](./install/index.md) → [Pre-flight](./preflight.md) →
  [Quickstart](./quickstart.md).
- **Something broke?** → [Troubleshooting](./troubleshooting.md).
- **Want a one-paragraph answer?** → [FAQ](./faq.md).

---

## Attribution

This page names Ansible®, Podman, Molecule, Fedora, Ubuntu, Arch Linux, macOS, systemd and
Mageia. All product names, logos and brands are the property of their respective owners; their
use here does not imply endorsement. This site is not affiliated with or endorsed by the Fedora
Project, the Arch Linux Project, Red Hat, Inc., Canonical Ltd., or The Linux Foundation. Full
licence and provenance record: [`assets/ATTRIBUTION.md`](../assets/ATTRIBUTION.md).
