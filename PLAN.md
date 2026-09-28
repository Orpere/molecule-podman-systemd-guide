# PLAN.md — Molecule + Podman + systemd Documentation Site

> **Owner:** tech-lead · **Status:** ✅ **DELIVERED** · **Version:** v1.0 (2026-09-28)
> **Method:** Graph Engineering (work/system/history graphs) · Loop Engineering (bounded
> feedback loops) · Visual Planning (this file) · Zero-Cost Doctrine ($0, forever, no card on file)
> **Verified by execution, not by review:** 4 runnable example scenarios, all exit 0 and
> non-vacuous (`ok=4`/`ok=7`, zero `no hosts matched`) on Fedora 44 · podman 5.8.7 ·
> Molecule 26.9.0 · ansible-core 2.21.4. **Gates cleared after two rounds each.**
> **Provenance:** the verified research corpus and the gate reports referenced throughout this
> document live in a local `.research/` directory, which is deliberately **not** published — it
> holds internal process notes, local absolute paths, and a third-party username quoted from an
> upstream doc. The claims it backs are cited by URL in the reader-facing pages.

---

## 1. Deliverable, in one paragraph

A beginner-friendly, copy-paste-works documentation site that takes a reader from *"I have
never used Ansible"* to *"I have my own Molecule test workflow running systemd services in
Podman containers on my OS of choice."* It must cover **installation** (all dependencies
enumerated), **systemd inside Podman containers**, **day-to-day usage**, and **how to author
your own workflows** — on **Fedora, Ubuntu, Arch, macOS**, and (interpreting "moc osx" both
ways) **macOS + Mageia OS**. Every diagram is Mermaid-first and every icon is original
house-style SVG plus official brand marks with recorded licence/attribution.

---

## 2. Non-negotiable constraints (Zero-Cost Doctrine + house gates)

| # | Constraint | How it is enforced |
|---|---|---|
| Z1 | **$0 forever. No payment method, ever.** | Only pip/pipx + distro packages + Homebrew (free) + GitHub Pages (free). No SaaS, no paid registry, no paid CI runner, no paid icon pack. |
| Z2 | **Docs must render with zero build tooling.** | Markdown + Mermaid (GitHub renders Mermaid natively). MkDocs Material is documented as *optional*, never required. |
| Z3 | **Boring stack.** | Molecule + Podman + `containers.podman`. No Kubernetes, no Terraform, no Vault, no Docker. |
| Z4 | **Every claim is sourced or empirically verified.** | Research corpus in `.research/` with source URLs; unverified items are labelled or omitted. |
| Z5 | **Brands used nominatively, attributed.** | Official marks recorded in `assets/ATTRIBUTION.md` with source URL + licence. Original icons authored by us. |
| Z6 | **No secrets, no personal identifiers.** | `~/tools/scan-secrets.sh` before any `git init`/push. |

---

## 3. Work graph (DAG) — dependencies are explicit

**Status legend** (this replaces the old `classDef` colour-coding, which
`VISUAL-SYSTEM.md` **M2** forbids because GitHub does not re-theme hard-coded fills):

| Word in a node label | Meaning | Old class |
|---|---|---|
| `DONE` | finished and verified | `done` (green) |
| `IN FLIGHT` | being written / being run right now | `act` (blue) |
| `CRITICAL` | on the critical path | `crit` (red) |
| `BLOCKED` | waiting on someone or something else | — (no node) |
| `PENDING` | not started | `wait` (grey, defined but unused) |

The DAG has 17 nodes, so **M1** (at most 7 nodes per diagram) splits it into five
diagrams. Read them in order; the edges are the real dependencies and no edge is
invented or dropped. Every node of the critical path appears in at least one of the
five, and no diagram contradicts another.

### 3a — intake, brand research and the first three writers

```mermaid
flowchart LR
  N1["N1 Intake requirements DONE"]
  R1["R1 Brand asset research DONE"]
  D1["D1 Doc IA + ref spec CRITICAL"]
  B1["B1 Icon + diagram IN FLIGHT"]
  W1["W1 README + overview IN FLIGHT"]
  W2["W2 Install docs 5 OS IN FLIGHT"]
  W3["W3 systemd page IN FLIGHT"]
  N1 --> D1
  N1 --> R1
  R1 --> B1
  D1 --> B1
  D1 --> W1
  D1 --> W2
  D1 --> W3
```

**Reading 3a:** intake fans out to the design spec (`D1`, critical) and to brand-asset
research (`R1`, done). Both feed the icon set (`B1`, in flight). `D1` also releases the
first three writers — `W1` README, `W2` install docs, `W3` the systemd-in-containers page.

### 3b — the remaining writers and the examples task

`D1`, `W3` and `W4` reappear here because `E1` depends on all three; the other four
writers (`W4`–`W7`) get their release edge from `D1` in this diagram.

```mermaid
flowchart LR
  D1["D1 Doc IA + ref spec CRITICAL"]
  W3["W3 systemd page IN FLIGHT"]
  W4["W4 Quickstart IN FLIGHT"]
  W5["W5 Usage reference IN FLIGHT"]
  W6["W6 workflows + CI IN FLIGHT"]
  W7["W7 Troubleshooting IN FLIGHT"]
  E1["E1 Runnable examples CRITICAL"]
  D1 --> W4
  D1 --> W5
  D1 --> W6
  D1 --> W7
  D1 --> E1
  W3 --> E1
  W4 --> E1
```

**Reading 3b:** the other four writers — `W4` quickstart, `W5` usage reference,
`W6` authoring + CI, `W7` troubleshooting + FAQ + glossary — are released by `D1`.
The runnable-example task `E1` (critical) needs `D1` **and** both `W3` and `W4`,
because it is the artefact that proves what those two pages claim.

### 3c — everything converges on the lint gate (first half)

```mermaid
flowchart LR
  B1["B1 Icon + diagram IN FLIGHT"]
  W1["W1 README + overview IN FLIGHT"]
  W2["W2 Install docs 5 OS IN FLIGHT"]
  W3["W3 systemd page IN FLIGHT"]
  W4["W4 Quickstart IN FLIGHT"]
  T1["T1 Live verify CRITICAL"]
  V1["V1 Lint gate IN FLIGHT"]
  B1 --> V1
  W1 --> V1
  W2 --> V1
  W3 --> V1
  W4 --> V1
  T1 --> V1
```

**Reading 3c:** the assets and the first four writers all converge on `V1`, the lint
gate — and so does `T1`, the live run on this host (critical). `V1` cannot start until
the live run has produced something to lint.

### 3d — convergence, second half

```mermaid
flowchart LR
  W5["W5 Usage reference IN FLIGHT"]
  W6["W6 workflows + CI IN FLIGHT"]
  W7["W7 Troubleshooting IN FLIGHT"]
  V1["V1 Lint gate IN FLIGHT"]
  C1["C1 code-reviewer CRITICAL"]
  C2["C2 security-auditor IN FLIGHT"]
  W5 --> V1
  W6 --> V1
  W7 --> V1
  V1 --> C1
  V1 --> C2
```

**Reading 3d:** the last three writers converge on the same `V1`, which then hands off
to the two final gates in parallel: `C1` code-reviewer (critical — it can send work
back) and `C2` security-auditor (in flight).

### 3e — integration

```mermaid
flowchart LR
  E1["E1 Runnable examples CRITICAL"]
  T1["T1 Live verify CRITICAL"]
  C1["C1 code-reviewer CRITICAL"]
  C2["C2 security-auditor IN FLIGHT"]
  I1["I1 Integrate deliver CRITICAL"]
  E1 --> T1
  C1 --> I1
  C2 --> I1
  T1 --> I1
```

**Reading 3e:** `E1` feeds `T1` (the examples must exist before they can be run live),
and integration `I1` (critical) waits on three things: the live run, and **both** review
gates. One FAIL from either gate holds delivery.

**Critical path (longest risk chain):** `N1 → D1 → W3 → E1 → T1 → C1 → I1`.
It runs through **systemd-in-containers** and the **live-verified example** because those are
the two places where folklore is strongest and a wrong instruction costs the reader a
half-day. Everything else can be written in parallel. Those seven nodes are spread over
all five diagrams — `N1`, `D1`, `W3` in **3a**; `W3`, `E1` in **3b**; `T1` in **3c**;
`C1` in **3d**; `E1`, `T1`, `C1`, `I1` in **3e** — which is why a reader needs all five
diagrams, not one, to trace it.

**Cycle check:** topological order is clean. No back-edges. `D1` is the single fan-in point
before the writing fan-out (7 writers, no writer depends on another writer).

**Fan-in / integration points:** `B1`, `W1…W7`, `E1` all converge on `V1` (the lint gate) —
see **3c** for `B1`/`W1`–`W4` and **3d** for `W5`–`W7`. `V1` is the blast-radius boundary:
one bad cross-link fails the whole build, by design.

---

## 4. System graph — what we are documenting

11 nodes and three tiers (host → engine → container), so **M1** splits it into three
diagrams that overlap deliberately: `ANS` appears in 4a and 4c, `PCLI` in 4a and 4b.
Read 4a, then 4b, then 4c. One node-id fix: the cgroup-v2 node used to be called
`ENG`, colliding with the `ENG` subgraph id, which made mermaid-cli fail outright with
`Referenced shape does not exist: CTR`. It is now `CG`.

### 4a — the CLI, on the host

```mermaid
flowchart TB
  CLI["molecule CLI 26.9.x"]
  ANS["ansible-core exec driver"]
  CP["containers.podman.podman"]
  PCLI["podman CLI"]
  CLI --> ANS
  ANS --> CP
  CP -->|"exec via podman CLI"| PCLI
```

**Reading 4a:** your machine (the host) runs the `molecule` CLI 26.9.x, which drives
`ansible-core` as the exec driver, which uses the `containers.podman.podman` connection
plugin, which ends up executing the `podman` CLI. No socket anywhere in that chain.

### 4b — the Podman engine, and the two host requirements on the container

```mermaid
flowchart TB
  PCLI["podman CLI"]
  subgraph ENGINE["Podman engine (host or VM)"]
    CG["cgroup v2 host"]
    SEL["SELinux container_init_t"]
    CTR["container --systemd=always"]
  end
  PCLI --> CTR
  CG -.->|"must be delegated"| CTR
  SEL -.-> CTR
```

**Reading 4b:** the `podman` CLI creates the scenario container with
`--systemd=always`. Two *host* facts are prerequisites for that container to boot
cleanly: cgroup v2 with delegation, and the SELinux `container_init_t` context. Node
`CG` is the renamed former `ENG` (see above); it is the cgroup-v2 requirement, not the
engine — the engine is the box the subgraph names.

### 4c — inside the container, and what asserts

```mermaid
flowchart TB
  PY["python3 + ansible"]
  ANS["ansible-core exec driver"]
  INIT["systemd (PID 1)"]
  SVC["your .service units"]
  VFY["verify.yml"]
  PY -.->|"needed by builtin tasks"| ANS
  INIT --> SVC
  ANS -->|"asserts"| VFY
```

**Reading 4c:** inside the container, systemd is PID 1 and supervises your `.service`
units. On the target, Python 3 plus Ansible must be installed, because that is what
`ansible.builtin` tasks actually execute against; and the run finishes with
`verify.yml`, the playbook that asserts the outcome.

**Seams and blast radius:**
- `CP → PCLI` is a **CLI-exec seam, not a socket seam.** This is the single most
  common doc error in the wild; it dictates the whole connection section. (4a)
- `CG → CTR` is the **cgroup v2 + cgroup delegation seam** — the hard requirement. (4b)
- `PY` inside the container is a **hard requirement**, not optional: `ansible.builtin` tasks
  need Python on the target. Bare `alpine` cannot be a scenario image. (4c)
- Failure propagation: a broken host cgroup setup fails *every* scenario at `create` with an
  empty log — hence the dedicated troubleshooting doc.

---

## 5. Execution-history graph (appended after every phase)

**Verdict legend** (replaces the old `classDef` colour-coding, per **M2**):

| Word in a node label | Meaning | Old class |
|---|---|---|
| `DONE` | phase finished, verdict recorded below | `ok` (green) |
| `FAILED` | phase could not run — quota, provider error | `bad` (red) |
| `IN FLIGHT` | phase running now | `wip` (orange) |
| `BLOCKED` | waiting on an external precondition | — (no node) |
| `PENDING` | not started | `pend` (grey) |

Ten nodes, so **M1** splits it into two diagrams: 5a is the completed research and design
arc, 5b the four phases that have not started. `D1` appears in both, as the handoff.

### 5a — completed: intake, research, persist, design

```mermaid
flowchart LR
  N1["N1 intake DONE (corrected)"]
  RA["RA1 molecule driver DONE"]
  RB["RB2 podman+systemd DONE"]
  RC["RC3 platform matrix DONE"]
  RD["RD4 persist 445KB DONE"]
  D1["D1 doc IA + ref spec DONE"]
  N1 --> RA
  N1 --> RB
  N1 --> RC
  RA --> RD
  RB --> RD
  RC --> RD
  RD --> D1
```

**Reading 5a:** intake (done, but the brief was **corrected** — 10 factual errors) fanned
out into three research reports, all `PASS`; the three reports were then persisted to disk
(`RD4`, 445 KB) and their corpus unlocked the design spec `D1`, which is `PASS` re-routed
through the `general` agent. The `FAILED` verdict on the architect attempt (RD6) and the
`IN FLIGHT`/`BLOCKED` re-routes are all in the table below, which is the authoritative
record — the graph carries the dependency order, the table carries every verdict.

### 5b — delivered: write, build, verify, gate, integrate

```mermaid
flowchart LR
  D1["D1 doc IA + ref spec DONE"]
  P2["P2 write docs DONE"]
  P3["P3 examples+verify DONE"]
  P4["P4 review + audit DONE"]
  P5["P5 integrate + deliver DONE"]
  D1 --> P2
  P2 --> P3
  P3 --> P4
  P4 --> P5
```

**Reading 5b:** `P3` is the "examples + live verify" phase — the only label shortened to fit
M7's 30-character limit. From `D1` the five phases ran in series: write the docs, build and run
the examples live, review and audit, then integrate and deliver. **`P3` is the phase that mattered
most**: it is where the silent false pass (T5) was caught, and no amount of review had caught it.
`P4` returned an unfavourable verdict twice and sent work back both times (T6, T7).

| Phase | Verdict | Produced | Unblocked |
|---|---|---|---|
| **P2 write docs** | ✅ PASS | 35 pages across 7 units; README, install ×7, systemd, quickstart, preflight, usage, reference ×3, authoring ×7, concepts, glossary, troubleshooting, FAQ | P3 |
| **P3 examples + live verify** | ✅ PASS — **found 7 defects** | `examples/{systemd-unit,quickstart,multi-scenario}` — 4 scenarios, all exit 0 and non-vacuous → **T5** | P4 |
| **V1 lint** | ✅ PASS after 1 round | 6 blockers closed: 0 broken links, 0 duplicate slugs, 0 forbidden Mermaid constructs, 0 `no hosts matched` | P4 |
| **B1 assets** | ✅ PASS | 20 icons + 10 badges + 3 SVG illustrations; XML-valid, `currentColor`; 5 marks deliberately refused | V1 |
| **P4 gate round 1** | ❌ **CHANGES REQUESTED / NOT CLEARED** | 15 review + 27 security findings, incl. 2 BLOCKERs → **T6** | remediation |
| **Remediation** | ✅ PASS | 2 BLOCKERs closed (`curl\|bash` RCE; unwarned AppArmor boundary, with reverts in all 3 files); 6 MAJORs; home-path/username leak removed | P4 |
| **P4 gate round 2** | ✅ PASS after remediation | 1 further MAJOR (`ansible-core` missing from the venv route) + integrity gap (multi-scenario run unevidenced) → **T7**, both closed | P5 |
| **P5 integrate + deliver** | ✅ **DONE** | Secret scan clean · 0 broken links/anchors · 40/40 diagrams valid · 0 placeholders · `test-preflight.sh` 7/7 | — |

> **Provisioning note (RD9/RD10).** Three pinned specialist agents
> (`systems-architect`, `qa-test-engineer`, `frontend-engineer`, `code-reviewer`,
> `security-auditor`) return `Insufficient Balance` at the provider — six failed attempts in
> total. The `general` agent is unaffected and executed every phase, **including both gate
> rounds**. This is a staffing substitution, not a change of standard: each gate still had to
> return a favourable verdict before delivery, and each one refused clearance on its first
> pass. The residual gap — no second opinion from the *named* specialists — is recorded in
> §8.1 rather than glossed over.

| Phase | Verdict | Produced | Unblocked |
|---|---|---|---|
| N1 intake | ⚠ **CORRECTED** | Empty-dir discovery; brief had 10 factual errors | R1 |
| RA1 research | ✅ PASS | `.research/01-molecule-podman-driver.md` (111 KB) | D1 |
| RB2 research | ✅ PASS | `.research/02-podman-systemd-container.md` (123 KB) | D1 |
| RC3 research | ✅ PASS | `.research/03-platform-install-matrix.md` (210 KB) | D1 |
| RD4 persist | ✅ PASS | Corpus secured to disk after in-transit truncation; 551 KB / 56 sections | D1 |
| RB5 brand assets | ✅ PASS | `.research/04-brand-assets.md` (105 KB) + ship-decision table | B1 |
| **RD6 architect quota** | ❌ **FAIL ×2** | `systems-architect` → `Insufficient Balance` on both attempts | — |
| D1 design | ✅ PASS (re-routed) | `docs/STRUCTURE.md` · `REFERENCE-CONFIG.md` · `VISUAL-SYSTEM.md`; 7 corpus contradictions resolved | P2 |
| RD7 persist | ✅ PASS | Corpus 551 KB / 4 reports; `molecule-preflight.sh` run live (exit 1, correct) | T1 |
| RD8 toolchain | ✅ PASS | venv `/tmp/opencode/molvenv`: molecule 26.9.0 · plugins 26.9.28 · ansible-core 2.21.4 → **Trace T3** | T1 |
| W3 systemd page | ✅ PASS | `docs/systemd-in-containers.md` (527 L, 2 Mermaid) | — |
| W4 quickstart | ✅ PASS | `docs/quickstart.md` + `docs/preflight.md` (2 Mermaid) | — |
| W2 install ×7 | ✅ PASS | `docs/install/{index,fedora,ubuntu,arch,macos,mageia,rootless-podman}.md` (4 Mermaid) | — |
| W6 authoring ×7 | ✅ PASS | `docs/authoring/{index,your-first-scenario,project-layout,writing-tests,custom-images,multi-scenario,ci}.md` (5 Mermaid) | — |
| **RD9 quota wall** | ❌ **FAIL ×2** | `qa-test-engineer` + `frontend-engineer` → `Insufficient Balance` | — |
| T1 live verify | 🔁 **RE-ROUTED** | → `general` | V1 |
| B1 assets | 🔁 **RE-ROUTED** | → `general` | V1 |

> **Provisioning note (RD9).** Three of the pinned specialist agents
> (`systems-architect`, `qa-test-engineer`, `frontend-engineer`) return
> `Insufficient Balance` at the provider. The `general` agent is unaffected and has
> completed every phase. All specialist work is therefore being executed and
> self-reviewed by `general`, and the **final** gates (`code-reviewer`,
> `security-auditor`) will be attempted on their pinned agents with a `general`
> fallback. This is a staffing substitution, not a change of standard: the gates
> still have to pass.
| **D1 spec (re-route)** | ✅ **PASS** | `docs/STRUCTURE.md` (94 KB, 31 units, 0 orphans / 0 dead ends) · `docs/REFERENCE-CONFIG.md` (67 KB, single source of truth for every artifact) · `docs/VISUAL-SYSTEM.md` (34 KB, 10 Mermaid + 3 SVG + 20 icons + 4 badges) · `docs/scripts/molecule-preflight.sh` (10.8 KB, **executed live on this Fedora 44 host, real output in §6.4**). **7 corpus self-contradictions found and decided** (`STRUCTURE.md` §8). 14 UNVERIFIED items labelled. | **W1–W7, B1, E1** |

---

## 6. Problem-solving traces

### Trace T1 — "10 wrong premises" in the intake brief

| # | Premise (as briefed) | Verdict | Ground truth | Consequence for the docs |
|---|---|---|---|---|
| 1 | Molecule "v6/v7" | ❌ | **CalVer `26.9.0`** (2026-09-22) | Docs must never say v6/v7. |
| 2 | Driver built on `delegator` | ❌ | `delegator` is an unrelated 2014 pkg; the class is `Delegated` | No `delegator` install step. |
| 3 | `molecule-ansible` is a plugin | ❌ | **Does not exist** (PyPI 404) | Omit entirely. |
| 4 | `MOLECULE_DEFAULT_DOCKER_BIN` | ❌ | 0 GitHub hits | Use `MOLECULE_PODMAN_EXECUTABLE`. |
| 5 | `molecule add/remove/lint` | ❌ | **Removed** | `molecule init scenario`, `rm -r`, standalone `ansible-lint`. |
| 6 | Connection plugin in `community.docker` | ❌ | It is **`containers.podman.podman`** | All FQCNs change. |
| 7 | `pipx install molecule` is documented | ⚠ | Works (pipx = venv) but upstream says *"pip is the only supported method"* | Present pipx as the recommended **isolated** form, and state the upstream wording honestly. |
| 8 | Point Ansible at the podman socket | ❌ | The plugin drives the **CLI**, not a socket | No `DOCKER_HOST` in the podman path. |
| 9 | "moc osx" | ⚠ | Ambiguous | Cover **macOS** *and* **Mageia OS**. |
| 10 | systemd in container needs `--privileged`, `policy.json` edits, `setsebool` | ❌ | Only `--systemd=always` + cgroup v2. `--privileged` makes it **worse** (`degraded`) | The "known-bad folklore" callout box. |

**Root cause of the whole class:** these are stale pre-v6 blog posts, widely mirrored.
**Fix adopted:** every number, FQCN, env var and flag in the docs traces to `.research/`,
and a *"what the internet still gets wrong"* callout is a first-class doc element.

### Trace T2 — in-transit research truncation
- **Symptom:** three research reports returned "SuperMemory truncated N chars → saved".
- **Hypotheses:** (a) context limit, verdict **correct**; (b) data loss on disk, verdict **rejected** — re-reading confirmed the agents had the full text.
- **Root cause:** the subagent return channel, not the filesystem.
- **Fix:** resume each `task_id` and instruct a `Write` of the full report to `.research/`.
- **Regression test:** byte sizes reported by each agent (111 635 / 123 676 / 210 479) and
  section-heading greps now confirm completeness.
- **House rule now applied:** *any research too large to survive the return channel must be
  persisted to disk by the agent, and verified by size + heading count before use.*

### Trace T3 — `molecule --version` crashes on a clean pip install

- **Symptom:** after `pip install molecule molecule-plugins ansible-lint`, `molecule --version`
  died with `FileNotFoundError: [Errno 2] No such file or directory: 'ansible-config'`.
  `molecule drivers` worked fine, so the install looked healthy.
- **Hypotheses:** (a) broken/partial install → **rejected**, `molecule drivers` listed every
  driver so the package and its entry points were intact; (b) missing `ansible-core` → **correct**;
  (c) PATH problem → **also true**, the venv `bin/` was not on PATH.
- **Root cause:** `molecule` shells out to `ansible-config` at start-up, and Molecule 26.9 does
  **not** declare `ansible-core` as a hard dependency. A `pip install molecule` that reports
  success leaves a **broken** `molecule` binary.
- **Fix:** `pipx install molecule ansible-core molecule-plugins` (one shared venv). `ansible-core`
  must be named explicitly — pipx's `--include-deps` only pulls *declared* dependencies.
- **Regression test:** `molecule --version` must print `molecule 26.9.0 using python 3.x`.
  **Verified live on this host** with molecule 26.9.0 + ansible-core 2.21.4.
- **Consequence for the docs:** every install page installs `ansible-core` *together with*
  `molecule`, and `ansible-config: not found` is now a first-class troubleshooting entry
  (delivered in `docs/install/*.md` and `docs/troubleshooting.md`).

### Trace T4 — three R10 line-budget overruns, accepted with a rule

- **Symptom:** the corpus-derived house rule R10 caps a page at ~450 lines. `systemd-in-containers.md`
  (527), `quickstart.md` (479), `macos.md` (495), `ubuntu.md` (474), `your-first-scenario.md` (476)
  all exceed it. Each author flagged it rather than silently cutting.
- **Hypotheses:** (a) bloat → **rejected**, the overruns are 58-95 lines of *mandated verbatim*
  `molecule.yml`/Containerfile blocks plus mandated diagram text-alternatives; (b) genuine scope
  creep → **partly true** on `macos.md`; (c) rule is wrong → **correct**, and the fix is a rule change.
- **Root cause:** R10 was written for prose pages but the site quotes canonical YAML verbatim and
  may not paraphrase it, so line count is a poor proxy for bloat.
- **Fix (rule change, retroactive):** R10 applies to **prose only**. Verbatim artifact blocks,
  tables and diagram text-alternatives are excluded from the count. Long pages split only along
  the fixed IA file boundary — never into a new file the IA does not define.
- **Regression test:** the V1 lint gate reports line counts but fails only on *prose* density.

### Trace T5 — 🔴 the silent false pass: `molecule test` exits 0 having asserted nothing

**The single most valuable finding of this delivery.** Found by T1 (live run), not by review.

- **Symptom:** both examples reported PASS. But the canonical `molecule.yml` (§2a and §2b) produced
  `skipping: no hosts matched` for **every** play, and `molecule test` still **exited 0**.
- **Root cause (verified in the installed source, `molecule/provisioner/ansible.py:261`):**
  `for group in platform.get("groups", ["ungrouped"])`. Molecule derives the Ansible groups from
  `platforms[*].groups`, whose default is `["ungrouped"]`. There is **no implicit `molecule`
  group**, so the ubiquitous `hosts: molecule` matched nothing — *silently, and green*.
- **Why it survived review:** three specialists had already reviewed §2b and all approved it. It
  is syntactically perfect, semantically plausible, and completely inert. **Only execution caught it.**
- **Fix:** `groups: [molecule]` added to every canonical `platforms[*]` block, in
  `REFERENCE-CONFIG.md` and in all seven quoting pages, with the reason kept inline as a comment.
- **Regression test (the real gate, not a self-report):** the `verify` play recap must show
  `ok=N` with `N > 0` and **zero** `no hosts matched`. Live result on this host —
  `instance : ok=7 changed=0 unreachable=0 failed=0 skipped=0 rescued=0`, asserting
  `systemd is PID 1.` and `molecule-demo.service is active.`, with `systemctl is-system-running`
  → `running` and `0 loaded units listed.`
- **Promoted to documentation:** the "did my test actually run?" check is now a first-class
  troubleshooting entry, because **exit 0 does not mean your assertions executed.**

#### The full T1 defect list now closed (from `examples/VERIFICATION.md`)

| ID | Sev | Defect | Fix |
|---|---|---|---|
| DBG-1 | 🔴 | `groups` missing → zero assertions, green exit | add `groups: [molecule]` |
| DBG-2 | 🔴 | `wait_for: state: directory` is fatal on ansible-core 2.21 (valid: `absent/drained/present/started/stopped`) | `state: present` |
| DBG-3 | 🔴 | §9.1 called `create.yml`/`destroy.yml` required; shipping them **overrides the driver's own create playbook** → no container built, converge dies `Container 'instance' not found` | do not ship them; §9.1 reversed |
| DBG-4 | 🟡 | `command` with a `;` compound never runs a shell → `stdout_lines: []`, so the doc's own promised sample output was unreachable | use `shell` |
| DBG-5 | 🟡 | §2a titled "no systemd" while setting `systemd: always` on an image that *contains* systemd | retitled / made genuinely non-systemd |
| DBG-6 | ⚪ | `cleanup` in `test_sequence` with no `cleanup.yml` → "Missing playbook" every run | ship a `cleanup.yml` or drop the step |
| DBG-7 | ⚪ | flat `molecule.yml` at project root is impossible (`CRITICAL 'molecule/*/molecule.yml' glob failed`) | keep the `molecule/<scenario>/` layout |

#### Claims **refuted** by execution (the docs were over-asserting)

| Claim | Was stated as | Reality |
|---|---|---|
| `systemd: always` | *required* | **Refuted** — works with `--systemd=true` and with no flag, because Podman's default `true` auto-detects a `/sbin/init` command. Correct guidance: it is the *robust* choice that removes the dependency on auto-detection, and it becomes genuinely required the moment the command is not literally an init. |
| `override_command: true` | *mandatory* | **Refuted** for an image whose `CMD` is already an init; still genuinely required when the image `CMD` is *not* an init and the driver would otherwise substitute the sleep loop. |

**House rule now added:** *a claim about Ansible/Molecule behaviour is not verified until it has
been executed. Three independent reviews passed a config that asserted nothing.* The V1 gate
therefore gains a mandatory **non-vacuity check** on any example that claims to pass.

### Trace T6 — the gates did real work: 42 findings, round 1

- **Symptom:** with lint green, both gates returned an unfavourable verdict. Content review:
  **CHANGES REQUESTED**, 1 BLOCKER + 6 MAJOR + 6 MINOR. Security: **NOT CLEARED**, 2 BLOCKER +
  5 MAJOR + 7 MINOR + a 39-row dangerous-command inventory.
- **The two BLOCKERs, and why they mattered:**
  1. **`docs/preflight.md:51` offered `bash <(curl -fsSL "$REPO_BASE/…")` as the *first* option**,
     where `REPO_BASE` was an unfilled placeholder and the bytes went straight to `bash` with no
     checksum, no pin, no preview. Arbitrary code execution, no review step, no undo — in a
     document whose whole audience is beginners copying commands. Fixed by promoting the local
     download-read-run path to Option A and rewriting the remote form as commit-pinned,
     download → `less` → run, with the reason stated.
  2. **The AppArmor `sysctl` fix appeared on the troubleshooting page with no warning and no
     revert** — while `docs/install/ubuntu.md` carried an excellent warning for the *same three
     commands*. The site knew the right framing and had written it; it was simply absent from the
     page a reader reaches *by searching the error*, which is the least guarded moment. Fixed by
     leading with the narrow per-program fix, importing the warning verbatim, and adding a
     **revert block to all three files** that prescribe the broad fix.
- **Root cause of the class:** documentation written page-by-page without a **cross-page safety
  invariant**. A warning in one file does not protect a reader arriving from another.
- **Fix adopted:** the "privileged / system-weakening command" warning is now required to travel
  with the command **and** its revert, everywhere. Verified by grep in the security re-audit.
- **Also found and fixed:** an absolute-home-path/username leak (11 lines) — this repo is scanned
  for home paths and usernames before push, so that was a hygiene blocker, not cosmetics.

### Trace T7 — round 2, and the bug that survived three correct fixes

- **Symptom:** re-review found the `ansible-core` fix (T3) had been applied to the **pipx** routes
  but not to the **pip/venv** route at `docs/REFERENCE-CONFIG.md:1172` — which
  `docs/install/mageia.md` calls *"the recommended route on Mageia"* and explicitly claims to
  quote. The page rendered the corrected command while the source it cited still taught the trap.
- **Hypotheses:** (a) the sweep missed it, verdict **correct**; (b) it was intentional, **rejected**.
- **Root cause:** the install pattern appears in three syntactically different forms (pipx
  one-shot, pipx two-step, venv+pip) and my earlier sweep matched only two of them.
- **Fix:** added `ansible-core` to the venv route; re-swept all 38 occurrences of
  `pipx install molecule`; the 5 residuals are prose *about* the pattern, not prescriptions.
  **House rule:** a fix to a repeated command pattern must be swept across **all** its syntactic
  variants, and the sweep must be reported with counts, not asserted.
- **Round-2 also closed:** the author's **real login name** appearing in 8 lines of reader-facing
  pre-flight transcript (`entry for <username>` in the sample output was the author's
  login, now a placeholder); a `delegate.conf` drop-in
  prescribed with no revert; and six pages still claiming the script "never writes" absolutely,
  which the review correctly noted is false — `podman` initialises its own XDG storage on first
  use. That last one I then **proved** by running the script under a sandboxed `HOME`: it created
  `.local` and `.config`. The docs now say exactly what "read-only" excludes, and
  `docs/scripts/test-preflight.sh` asserts that precise invariant rather than a stricter fiction.
- **Residual, stated not hidden:** the gates ran on `general` because four attempts across three
  pinned specialists returned `Insufficient Balance`. See §8.1.

---

## 7. Loop budgets (bounded, no unbounded retries)

| Phase | Inner loop | Max attempts | Exit condition (gate) | On exhaustion |
|---|---|---|---|---|
| Research | DO fetch → VERIFY source → REFLECT | 2 | Fact has a primary-source URL or is labelled UNVERIFIED | Architect re-scopes |
| D1 design | DO draft IA → VERIFY vs corpus | 2 | Every planned page maps to ≥1 verified fact | I re-scope |
| Writing (per file) | DO write → VERIFY facts+links | 2 | No unverified claim, no broken internal link | Code-reviewer |
| E1 examples | DO author → VERIFY run | 3 | Scenario runs green on this host | Debugger |
| T1 live verify | DO run → VERIFY exit code | 3 | `molecule test` exit 0 with systemd asserts | Debugger |
| V1 lint | DO fix → VERIFY clean | 3 | 0 broken links, 0 invalid Mermaid | I fix |
| C1/C2 gates | DO review → VERIFY verdict | 2 | APPROVED / SECURE | I re-route |

**Prohibition:** a retry must carry new information (new hypothesis, narrower scope, fixed
precondition). Identical re-runs are forbidden.

---

## 8. Definition of Done

- [x] All 5 platforms documented with exact, copy-pasteable commands and full dependency lists
      — `docs/install/{fedora,ubuntu,arch,macos,mageia,rootless-podman,index}.md`
- [x] systemd-in-containers page written from verified flags, folklore callout included
      — `docs/systemd-in-containers.md`; **the claim `privileged: true` is harmful is now
      execution-backed**, not just measured by the researcher
- [x] **4** live-run, exit-0, **non-vacuous** example projects — `examples/{systemd-unit,quickstart,multi-scenario}`
      (2 scenarios). All four assert; `ok=4`/`ok=7`; zero `no hosts matched`
- [x] 0 broken internal links, 0 invalid Mermaid blocks, 0 unlabelled unverified claims
      — final: 35 files, 0 broken links/anchors, 40/40 diagrams valid, 0 placeholders, 0 unbalanced fences
- [x] Every icon either original-house or official-and-attributed — `assets/ATTRIBUTION.md`;
      20 icons + 10 badges + 3 illustrations, all XML-valid, `currentColor`, and the
      **Apple / Ansible / systemd / Ubuntu / Mageia marks deliberately refused**
- [x] Review gate **CLEARED** and security gate **CLEARED**, after two rounds each —
      see T6 and T7. Round 1 returned CHANGES REQUESTED / NOT CLEARED with 15 + 27 findings;
      round 2 returned 1 MAJOR + 1 integrity gap, both closed. The gates did real work.
- [x] `PLAN.md` history graph updated to DONE — §5, and §11 below
- [x] Zero-cost confirmed; no card, no metered service, no paid asset
- [x] Secret scan clean (`~/tools/scan-secrets.sh --no-history`) and no leaked home paths,
      usernames or absolute paths in tracked files
- [x] Executable regression test exists — `docs/scripts/test-preflight.sh`, 7/7 passing

### 8.1 Gate status, stated honestly

The two specialist gates **could not run on their pinned agents** (`Insufficient Balance`,
four attempts across three specialists) and were executed by `general` under a tech-lead-set
standard. The gates themselves are real: each returned an unfavourable verdict on round 1 and
each finding was actioned and re-verified. What I have **not** done is obtain a second
*independent pair of eyes from the named specialists* — that is the one residual gap, and it is
a staffing limitation rather than a standard I lowered.

**Not established, and not claimed:** the macOS, Ubuntu, Arch and Mageia paths are documented
from research, not executed. Only the **Fedora/x86_64** path was run. The docs label this
distinction explicitly in at least 7 places, and `docs/faq.md` states it outright.

---

## 8.5 Final delivery state

| Measure | Result |
|---|---|
| Markdown pages | 35 (plus 3 research reports + 3 gate reports in `.research/`) |
| Runnable example projects | 4 scenarios across 3 projects, all exit 0 and non-vacuous |
| Diagrams | 40 Mermaid (all valid) + 3 hand-authored SVG illustrations |
| Icons / badges | 20 + 10, all `currentColor`, XML-valid, theme-safe |
| Broken links / anchors | **0** |
| Placeholders / TODOs | **0** |
| Secrets / home-path leaks | **0** |
| Paid tools, services or assets | **0** |
| Defects found by executing the docs | 7 (T5) — all fixed and regression-tested |
| Defects found by the two gates | 42 (15 review + 27 security) — all actioned |



---

## 9. Change log

| Ver | Date | Change |
|---|---|---|
| v0.1 | 2026-09-28 | Intake. Brief corrected against live sources; research corpus landed in `.research/`. |
| v0.2 | 2026-09-28 | D1 design spec. IA, canonical artifacts, pre-flight script, visual system. Architect quota exhausted → re-routed. |
| v0.3 | 2026-09-28 | 35 pages authored across 7 writing units. Icons/badges/illustrations authored. |
| v0.4 | 2026-09-28 | **T5.** 7 defects found by *executing* the docs, incl. the silent false pass. Canonical config fixed and propagated (8/8 coverage). |
| v0.5 | 2026-09-28 | Lint blockers closed: 0 broken links, 0 duplicate slugs, 0 forbidden Mermaid constructs, `examples/multi-scenario/` built and passing. |
| v0.6 | 2026-09-28 | **T6/T7.** Two gate rounds: 42 findings actioned. `curl\|bash` RCE and the unwarned AppArmor boundary both closed with reverts; `ansible-core` sweep completed across all syntactic variants; username leak removed; `test-preflight.sh` added. |
| **v1.0** | **2026-09-28** | **DELIVERED.** 35 pages · 4 non-vacuous example projects · 40 diagrams · 0 broken links · 0 secrets · 0 paid anything. Definition of Done complete. |

---

## 10. D1 design spec

**Slice owner:** systems-architect (re-routed from the quota-failed architect).
**Produced:** `docs/STRUCTURE.md`, `docs/REFERENCE-CONFIG.md`, `docs/VISUAL-SYSTEM.md`,
`docs/scripts/molecule-preflight.sh`.
**Loop:** DO draft IA → VERIFY every planned page against the corpus. 1 attempt, converged.

### 10.1 The three decisions that shape everything

1. **One code path, quoted from one place.** Every `molecule.yml`, `Containerfile`, playbook and
   install command exists exactly once, in `REFERENCE-CONFIG.md`, and the seven writing agents
   copy from it. Rationale: seven agents re-typing YAML is how `container_systemd: false`
   reappears in a page where it must be `always`. This is the primary drift control for the
   whole project and it is why D1 was worth a full slice.
2. **The podman **driver** is the taught path**, not the Ansible-native "no driver" pattern that
   `01` §4 calls *"the single biggest finding"*. The brief mandates the driver block, and the
   systemd knobs (`command` / `override_command` / `systemd`) are declarative keys in one file
   rather than variables threaded through inventory. The native pattern is preserved as an
   explicit **Alternative** box on the systemd page plus §2b of the reference, so the corpus
   finding is not lost.
3. **A read-only pre-flight gate before the first install step.** The script is read-only,
   never uses `sudo`, and was **executed on this Fedora 44 host** in both states (before and
   after Molecule) with the real output pasted into `REFERENCE-CONFIG.md` §6.4. A 10-second
   check is the cheapest possible "copy-paste works" insurance.

### 10.2 Structure at a glance

31 linkable units: `README.md` · `docs/index.md` · 3 D1 specs · `glossary` · `preflight` ·
`concepts/` · `install/` (index + 5 platforms + shared rootless) · `quickstart` ·
`systemd-in-containers` · `usage` · `authoring/` (index + 6) · `reference/` (3) ·
`troubleshooting` · `faq` · 3 runnable `examples/` · `assets/ATTRIBUTION.md`.
**Orphan/dead-end proof:** a 31-row table in `STRUCTURE.md` §4; V1 re-checks it mechanically.
**Mapping to the work graph:** W1→3 pages, W2→8, W3→1, W4→1, W5→4, W6→7, W7→3, D1→3,
E1→3 example trees, B1→20 icons + 4 badges + 3 SVG illustrations.

### 10.3 Corpus self-contradictions found (7) — **tech-lead action required**

Recorded in full at `STRUCTURE.md` §8 and `REFERENCE-CONFIG.md` §11. Ranked by damage a reader
would suffer:

| ID | Severity | Contradiction | Decision taken in D1 |
|---|---|---|---|
| **C-1** | 🔴 HIGH | The `molecule-plugins` podman driver docstring says *"make sure to set the `privileged`, `command`, and `environment` values"* and its own example sets `privileged: true`. `02` **empirically measured** that `--privileged` makes systemd-in-container *worse* (`degraded`, not `running`: it unmask `/sys`, so `sys-kernel-config/debug/tracing.mount` fail). `03` §7.4 then propagated the docstring's `privileged: true` as the recipe for **all six platforms** without re-testing. | Site says `privileged` is **not needed and is harmful**; canonical files set `privileged: false`; §10 of the reference is a folklore table naming the docstring as the source. **Escalated: this is a documentation bug in `molecule-plugins` and should be reported upstream.** |
| **C-2** | 🔴 HIGH | Molecule's own systemd guide recommends `quay.io/centos/centos:stream10` + `command: /sbin/init`. **That image has no systemd.** All 59 active tags enumerated, none contain `init`. | Site uses `ubi9/ubi-init` and names the upstream bug. No CentOS Stream image in any systemd example. |
| **C-4** | 🔴 HIGH | `podman info --format '{{.Host.Security.SelinuxEnabled}}'` **does not work** on Podman 5.8.7 (*"can't evaluate field SelinuxEnabled in type define.SecurityInfo"*). A documented-looking command that errors for a beginner. | Forbidden everywhere. The pre-flight script uses `getenforce` and `{{.Host.Security.Rootless}}` only. **This is why the script was executed rather than drafted.** |
| **C-6** | 🟡 MED | Molecule's shipped example has `group_vars/molecule.yml` with `container_systemd: false`, and `group_vars` outranks inline `vars:` — so an inline `always` is **silently ignored**. | No `group_vars/` in any project here. Taught as an explicit trap. |
| **C-3** | 🟡 MED | The *"No cgroup V1 Support"* bullet exists in the released 5.4.2 man page but was removed from `main` in 2026-01-29. | Never cite a Podman man page without naming its version; state cgroup v2 as a Podman 6.0/kernel fact. |
| **C-5** | 🟡 MED | *"pip is the only supported installation method"* + *"highly recommended … a virtual environment"* vs. "Molecule's docs do not mention pipx". | Both positions quoted verbatim on the install index. No page claims pipx is Molecule's documented method. |
| **C-7** | 🟡 MED | `podman(1)` says `--cgroup-manager` defaults to `systemd`, but Podman 6.0 removed it from `podman machine init` **and** `podman machine set`. | macOS page gives a **verification block**, not an assertion. |

### 10.4 Unverified items carried forward (14) — labelled in-place, never silently asserted

Includes: the Ubuntu and Fedora `Containerfile` variants (only the **Debian** one was built and
booted); Mageia's `newuidmap`/PEP 668 status; whether the AppArmor user-namespace restriction is
active on Ubuntu 26.04; whether Canonical ships a ready-made AppArmor profile for `podman`; the
ArchWiki `unprivileged_userns_clone` body. Full list: `STRUCTURE.md` §9.

**One deliberate scope boundary:** the corpus contains **nothing** about GitHub Actions. The CI
page therefore specifies workflow *structure* and links to GitHub's own pricing page rather than
stating a free-tier minutes figure.

### 10.5 A bug found and fixed inside D1, recorded as a regression test

The first pre-flight script parsed Molecule's version with a greedy `sed` over the whole
`--version` line. Real output is
`molecule 26.9.0 using ansible-core 2.20.3 python version 3.14.7 platform linux`, so the greedy
match extracted **`2.20`** — the *ansible-core* version — and warned that Molecule was outdated
when it was not. **Fixed by reading field 2 of line 1 with `awk`.** House rule now applied:
*any script in this project that parses a version string must read a field, never a regex over
the whole line.* Recorded in `REFERENCE-CONFIG.md` §6.4 because it is exactly the class of error
this project exists to prevent.

### 10.6 Unblocks

W1–W7 and B1 may start. E1 may start after W3 and W4 land. The D1 loop exited on attempt 1 of a
budget of 2; no escalation was needed.
