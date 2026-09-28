# `assets/ATTRIBUTION.md` — licence and provenance record

**Every graphic in this repository.** Source of truth for every licence and trademark claim is
[`.research/04-brand-assets.md`](../.research/04-brand-assets.md) §16 (SHIP DECISION TABLE) and
§17 (ready-to-paste lines). The design contract is [`docs/VISUAL-SYSTEM.md`](../docs/VISUAL-SYSTEM.md).
This file adds no new licence claim of its own; it records what was decided and what was refused.

Pages that display any mark from this catalogue must link here (`STRUCTURE.md` rule **R12**).

---

## 1. Original work in this tree

| Asset | Count | Author | Licence |
|---|---|---|---|
| `icons/icon-*.svg` | 20 | authored for this project | **CC0 1.0 Universal** |
| `diagrams/*.svg` (D-04, D-09, D-14) | 3 | authored for this project | **CC0 1.0 Universal** |
| `badges/badge-*.svg` | 10 | authored for this project | **CC0 1.0 Universal** |
| `assets.css` | 1 | authored for this project | **CC0 1.0 Universal** |

**These are original works, released into the public domain under CC0 1.0.** They are not derived
from any third-party artwork: no icon is a traced, recoloured, or simplified version of somebody
else's mark, and no badge contains a third-party logo. CC0 was chosen because it is the most
permissive dedication available, it puts the house style beyond the reach of any later maintainer
who wants to relicense it, and it matches the cleanest licence already in this catalogue.

Every **SVG** file in the groups above carries a `<!-- license: … -->` provenance comment on its
first line, because that is the convention the SVG format supports.

**One exemption, stated so the claim above stays true.** `assets/assets.css` is **CSS, not SVG**,
so it cannot carry an HTML comment as its first line without the file being a CSS parse error. It
carries its provenance as a `/* license: … */` block comment on lines 1–7 instead, declaring the
same **CC0 1.0 Universal** dedication as the SVGs. The intent is identical; the syntax is not,
because CSS and SVG do not share a comment syntax.

> **Do not add third-party artwork to `icons/` or `badges/`.** The house icon set is
> `currentColor`, `fill="none"`, 24-unit grid, stroke 2 — a brand mark cannot be drawn on that grid
> without being a recolour or a remix, which is exactly what the brand owners prohibit. Marks go
> in `badges/` as text, or they go in their own file with a row in §2 or §3 below.

---

## 2. Graphics cleared to ship — **none of them are in this tree yet**

These six assets are cleared by §16. **They are not present in `assets/`**, because they are
third-party files that must be fetched **verbatim** from the URLs below. Do not hand-author a
substitute and do not ask an agent to draw one — that is a lookalike, and for Molecule
(CC BY-ND 4.0) and Fedora (email-gated) it is an outright breach.

| Mark | File name if added | Exact source URL (fetch verbatim) | Licence | Conditions attached | Ready-to-paste attribution |
|---|---|---|---|---|---|
| **Markdown** | `assets/logos/markdown-mark.svg` | `https://raw.githubusercontent.com/dcurtis/markdown-mark/master/svg/markdown-mark.svg` | **CC0 1.0** (public domain) | None. Cleanest in the set. Attribution optional but included. | `Markdown Mark by Dustin Curtis, dedicated to the public domain (CC0 1.0).` + `https://github.com/dcurtis/markdown-mark` |
| **Podman** | `assets/logos/podman-logo-source.svg` | `https://raw.githubusercontent.com/containers/podman/main/logo/podman-logo-source.svg` | **Apache-2.0** (repo-included) | Retain the licence/NOTICE and state changes. **Must hyperlink to `https://podman.io`.** Must state it is a CNCF project. | `Podman is a registered trademark of The Linux Foundation.`<br>`The Podman logo is used under the Apache License 2.0.`<br>`© The Podman Authors. https://www.apache.org/licenses/LICENSE-2.0` |
| **GitHub** (Octicons `mark-github-24`) | `assets/logos/mark-github.svg` | `https://raw.githubusercontent.com/primer/octicons/main/icons/mark-github-24.svg` | **MIT** (artwork) + GitHub trademark | **Do not modify or recolour. Must be a link** to our repository. No implication of endorsement. Use the permitted logo version, not the Invertocat. | `The GitHub mark is from the Octicons set, © GitHub Inc., MIT licensed.`<br>`GITHUB®, the GITHUB® logo design, the INVERTOCAT logo design, OCTOCAT®, and the OCTOCAT® logo design are trademarks of GitHub, Inc.` |
| **Molecule** | `assets/logos/molecule-logo.png` | `https://raw.githubusercontent.com/ansible/molecule/main/docs/_static/images/logo.png` | **CC BY-ND 4.0** | 🚩 **NoDerivatives: display UNMODIFIED.** Do not crop, recolour, or remix. **It is a PNG, not an SVG.** Attribution required. Attribution is required *and* a derivative statement is required, even though there are no derivatives. | `The Molecule logo is licensed under the Creative Commons NoDerivatives 4.0 License.`<br>`https://creativecommons.org/licenses/by-nd/4.0/`<br>`This logo is displayed unmodified.` |
| **Arch Linux** | *(not added — see below)* | `https://archlinux.org/static/logos/archlinux-logo-black-scalable.svg` | Trademark (editorial use permitted) | 🚩 **™ must remain visible.** Retain proportions. No composite lockup with other marks. Not in an SEO `<title>`. Clear non-affiliation. **This site ships the text badge instead**, which removes every one of these obligations. | `The Arch Linux name and logo are recognized trademarks. Some rights reserved.`<br>`https://terms.archlinux.org/docs/trademark-policy/` |
| **Fedora** | *(BLOCKED — do not add)* | *only* the packet approved by `logo@redhat.com`; governing policy `https://fedoraproject.org/wiki/Legal/Trademark_guidelines` | Trademark of Red Hat, Inc. | 🚩 **Must request first (1–2 weeks).** One-colour **word design only — NEVER the Infinity logo.** Must hyperlink to `https://fedoraproject.org/`. Use `Fedora®` on the first instance on each page. Never modify. | `Fedora and the Infinity design logo are trademarks of Red Hat, Inc.`<br>`This site is not affiliated with or endorsed by the Fedora Project.`<br>`https://fedoraproject.org/wiki/Legal/Trademark_guidelines` |

**Why the six are absent.** The Zero-Cost Doctrine requires licence-verified assets, and CC BY-ND /
email-gated trademarks cannot be produced by an agent with a paint tool. Shipping a text badge is
both safer and honest. Adding any of them is a one-file, one-row change for a maintainer with a
browser and a licence check.

---

## 3. Text-only marks — we ship a **typographic badge**, never a graphic

Each row below is a badge in `badges/`: a rounded rectangle in **our** frame containing **only the
word**. There is no third-party artwork in any of them.

| Mark | Badge | Governing source | Licence status | Conditions attached | Required acknowledgement line (print on the page) |
|---|---|---|---|---|---|
| **CNCF** | `badge-cncf.svg` | `https://www.linuxfoundation.org/legal/trademark-usage` | Trademark of The Linux Foundation | The **landscape logo is not a permitted decorative icon.** Expand to "Cloud Native Computing Foundation (CNCF)" on first reference. | `CNCF® is a registered trademark of The Linux Foundation.` |
| **Ansible** | `badge-ansible.svg` | `https://docs.ansible.com/projects/ansible/9/dev_guide/style_guide/trademarks.html` | Trademark of Red Hat, Inc. — **no open redistribution grant** for the raster logo | The 3,993-byte white PNG is **not openly licensed**, and "never alter a trademark" means it cannot be recoloured. Red Hat endorsement must not be implied. | `Ansible® is a registered trademark of Red Hat, Inc. in the United States and other countries.` |
| **Ubuntu** | `badge-ubuntu.svg` | `https://ubuntu.com/legal/intellectual-property-policy` | Registered trademark of Canonical Ltd. | 🚩 **Do NOT append ® or ™.** Canonical's IPR policy forbids trademark symbols on product documentation distributed outside the United States. Logo use needs Canonical's **written** permission. | `Ubuntu and Canonical are registered trademarks of Canonical Ltd.` |
| **systemd** | `badge-systemd.svg` | `https://systemd.io/` | ❓ **UNVERIFIED** — no licence, no brand policy, no logo page | The upstream SVG exists (`https://systemd.io/assets/systemd-logo.svg`, HTTP 200) but **no licence covers it**; the LGPL covers "all code" only. Text only. | *(none — there is no mark to attribute)* |
| **Mageia** | `badge-mageia.svg` | `https://www.mageia.org/en/about/` | ❓ **UNVERIFIED** — no licence or policy retrievable | No first-party asset; absent from Simple Icons **and** Devicon; the wiki logo page is behind a browser-verification gate. Text only. | *(none — there is no mark to attribute)* |
| **Mermaid** | `badge-mermaid.svg` | `https://github.com/mermaid-js/mermaid` (code, MIT) | Code **MIT**; graphic ❓ **UNVERIFIED** | No official logo asset — every probe 404s. The repo README's MIT covers software only. Text only. | *(none — there is no mark to attribute)* |
| **macOS** | `badge-macos.svg` | `https://www.apple.com/legal/intellectual-property/guidelinesfor3rdparties.html` | ❌ **PROHIBITED** — see §4 | A plain text label in our own frame is a **textual acknowledgement**, which is the permitted form. | `macOS is a trademark of Apple Inc.` |

Two further badges exist for marks that are *not* in the ship table's text-only list but are
handled the same way: `badge-fedora.svg` and `badge-arch.svg` (both described in §2) and
`badge-markdown.svg` (CC0 — the text badge is the default; the mark may be added later per §2).

---

## 4. 🚩 REFUSED — do not "fix" these

A maintainer reading this file will notice a missing logo and be tempted to add one. **Do not.**
Each refusal below is a deliberate, sourced decision.

### 4.1 Apple / macOS — **PROHIBITED, no exceptions**

> *"You may not use the Apple Logo or any other Apple-owned graphic symbol, logo, or icon on or in
> connection with web sites, products, packaging, manuals…"*
> — Apple's Copyright and Trademark Guidelines for Third Parties,
> <https://www.apple.com/legal/intellectual-property/guidelinesfor3rdparties.html>

**Refused: the Apple logo, the Apple silhouette, the bitten-apple shape, a stylised Mac, a laptop
outline, a Finder-style window face, and a lookalike of any of them — in any size, in any file in
this repository.**

- **CC0 or MIT does not help.** The Simple Icons and Devicon copies are CC0/MIT *as files*; the
  *mark* is still Apple's, and CC0 cannot license what you do not own. The research file records
  this explicitly.
- **What we do instead:** the word `macOS` in our own typeface inside our own rounded frame
  (`badge-macos.svg`), and in `diagrams/macos-machine.svg` a **plain rounded rectangle** carrying
  the label `macOS`. A textual acknowledgement is the permitted form; a drawing is not.
- **If you are about to add one because a page "looks empty" without it:** that is the point. The
  absence is the compliance.

### 4.2 Fedora **Infinity** logo — **BLOCKED until `logo@redhat.com` approves a packet**

The word *Fedora* in a plain frame is fine. The Infinity device mark is not, and is not shipped
even if a packet arrives — the packet covers a **one-colour word design only**.

### 4.3 Ansible, systemd, Mageia, Mermaid, CNCF, Ubuntu — **text only**

See §3. For `systemd`, `Mageia` and `Mermaid` the reason is that **no licence covers the graphic**,
so there is nothing to rely on even in good faith. For `Ansible`, `CNCF` and `Ubuntu` the graphic
is trademarked and either not openly licensed or not permitted as a decorative icon.

### 4.4 A Molecule mascot, a "cloud" icon, a payment icon, or a gear-cluster variant

Not licence problems — **house-style** problems, rejected in `VISUAL-SYSTEM.md` §2.3. The
Zero-Cost Doctrine forbids hosted services, so a cloud icon would be a false claim; `$0` is set in
text, never in an icon. If you want one, change the spec first, not the icon.

---

## 5. Per-page footer

Any page that displays a graphic from §2 or names a mark from §3 carries:

```text
This site is not affiliated with or endorsed by the Fedora Project,
the Arch Linux Project, Red Hat, Inc., Canonical Ltd., or The Linux Foundation.
All product names, logos, and brands are property of their respective owners.
Their use does not imply endorsement.
```

---

## 6. Notes on this tree (deliberate deviations)

Recorded so a later reviewer does not mistake a decision for an oversight.

1. **Ten badges, not four.** `VISUAL-SYSTEM.md` §5.3 lists four (Fedora, Ubuntu, Arch, Mageia) and
   says the remaining marks get "no badge at all". The owner instruction for this build was to
   emit a badge for every mark §16 marks text-only, on the grounds that a badge containing only a
   word **is** the text-only treatment and reads as one family. Both are honoured: every badge is
   text-only, and §3 records that the underlying decision is still "no graphic". Dropping a badge
   is a one-file deletion if a maintainer prefers the smaller set.
2. **`<title>` is present inside the icons and badges**, alongside `role="img"` + `aria-label`.
   `VISUAL-SYSTEM.md` §2.1 and §9 decision 10 ask for *neither*, on the grounds that an
   `<img src>`-loaded SVG's internals are not reliably exposed to assistive technology. That reason
   still holds, and it is why the **full** text alternative still lives in the Markdown
   (`VISUAL-SYSTEM.md` §6.1) — the illustrations also carry a ready-to-lift version in an HTML
   comment at the top of each file. The `<title>` is an additive fallback, not a replacement.
3. **Type is set with `<text>` in the badges and the illustrations.** The "no `text` elements"
   rule applies to the **house icons**, where a glyph would break `currentColor` inheritance and
   the font stack; all 20 icons are pure stroke paths. A diagram with no labels cannot communicate,
   and both files use a `system-ui` stack with **no external font file**, no `@font-face`, and no
   network reference, so they render identically in GitHub and in a browser.
4. **Colour hex values in the diagrams live in the `<style>` block, in both the base rules and the
   `@media (prefers-color-scheme: dark)` block** — never on a `stroke=` or `fill=` attribute. This
   is `VISUAL-SYSTEM.md` §3.2's rule and it is deliberate: an SVG loaded through `<img src>` is a
   separate document and does **not** inherit the parent page's custom properties, so
   `var(--fg)` would resolve to nothing. Strokes still use `currentColor`; the root sets `color`
   once, in the stylesheet, for each theme.
5. **A note for anyone editing these SVGs:** a CSS class rule **overrides** a `fill="none"`
   presentation attribute. When you add a new filled panel, paint it *before* anything that sits
   on top of it. This bug shipped for one build cycle in `macos-machine.svg` and is now fixed.
