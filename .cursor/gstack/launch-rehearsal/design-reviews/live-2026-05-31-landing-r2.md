# Design Review R2 — Launch Rehearsal Marketing Landing Page

**Date:** 2026-05-31  
**URL:** http://localhost:8082/ (HTTP 200)  
**Prior review:** [live-2026-05-31-landing.md](./live-2026-05-31-landing.md) (6.5 / 10)  
**Reference:** `enterprise_work_env_simulator_2026/LANDING_PAGE_PLAN.md`  
**Method:** Browser DevTools MCP — ARIA snapshots, 1280×720 + 390×844, form/matrix/legal probes, Web Vitals  
**Screenshots:** `.cursor/gstack/launch-rehearsal/design-reviews/screenshots/landing-2026-05-31-r2/`

---

## Executive summary

**Overall: 7.8 / 10** (+1.3 vs R1)

User updates addressed the **P0 interactivity blockers** from R1. `main.js` loads; the hero gauge animates to **92% Green**; product gallery tabs switch; matrix cells open evidence modals; the lead form validates and shows a success state **without** the Vite 403 GET failure. FAQ expanded to **12 items**; pricing copy no longer promises Slack; footer and hero copy align better with `LANDING_PAGE_PLAN.md`.

**Verdict:** **Suitable for live partner calls with a human on the call** — walk hero → sample scorecard → `:8081` live demo. **Not yet suitable as an unsupervised public URL** until Formspree actually receives submissions, Calendly is real, and GitHub link resolves.

**North-star fit:** Stronger. Messaging, concierge framing, and honest integrations grid remain solid; execution now matches the trust story in most interactive paths.

---

## Delta vs prior review (R1 → R2)

| ID | Issue (R1) | R2 status | Evidence |
|----|------------|-----------|----------|
| **DR-LP-01** | `main.js` never loaded | **Fixed** | `<script type="module" src="/src/main.js">` in served HTML; hero shows 92% Green (not 0% / “Analyzing…”) |
| **DR-LP-02** | Form GET → Vite 403 + PII in URL | **Fixed** | `preventDefault` on submit; URL stays `#request-form`; success UI renders |
| **DR-LP-03** | No real lead capture backend | **Still open** | HTML has `method="POST" action="https://formspree.io/f/mqkrbpne"` but JS **simulates** success via `setTimeout` — no network POST observed |
| **DR-LP-04** | Readiness narrative inconsistency | **Mostly fixed** | Compare badges: TUESDAY **68% RED • 3 Blockers** → LATEST **92% GREEN • 0 Blockers**; matrix Admin J4 = “Pass (Blocker resolved)”. Cal.com Amber sample vs Argyle Green hero still dual-source but **labeled** (Phase 0 vs dogfood footnote) |
| **DR-LP-05** | GitHub footer 404 | **Still open** | `https://github.com/launch-rehearsal` → HTTP **404** (was `/rehearse` subpath; org URL also missing) |
| **DR-LP-06** | Pricing “Direct Slack channel” | **Fixed** | Bullet now reads **“Dedicated email channel”** |
| **DR-LP-07** | Evidence modal placeholder text | **Partial** | Modal opens with structured finding + CSS wireframe panel labeled **“Staging UI Screenshot”** — improved UX, still not real `:8081` captures |
| **DR-LP-08** | Matrix `<td>` not keyboard-focusable | **Fixed** | Interactive cells are `<button>` with descriptive `aria-label`; AX tree announces “button” |
| **DR-LP-09** | Mobile horizontal overflow | **Still open** | `scrollWidth 410` vs `clientWidth 390` at 390px viewport (+20px) |
| **DR-LP-10** | Legal links `alert()` placeholders | **Fixed** | `<dialog>` modal with Credential Handling / ToS copy + Acknowledge button |
| **DR-LP-11** | Footer “Sample evidence” wrong anchor | **Fixed** | Links to `#sample-scorecard` |
| **DR-LP-12** | FAQ 6/12 | **Fixed** | 12 `<details>` groups rendered (pricing, CI/PR, SOC2, scope, etc.) |
| **DR-LP-13** | Hero missing “No auto-fix” clause | **Fixed** | Hero body ends with **“Evidence-bound. No auto-fix.”**; tertiary **“Read CLI docs →”** present |
| **DR-LP-14** | Compare NLU / terminal sync | **Fixed** | CLI terminal shows typed run output; compare badges match Red→Green story |

### Product photos / naming (user-flagged — note only)

| Item | Status |
|------|--------|
| Product gallery tabs | Still **CSS wireframe mockups**, not screenshots from `:8081` |
| Matrix evidence modal | **Styled wireframes** per finding type (pricing matrix, signup, etc.) — functional demo, not production captures |
| Brand / product name | “Launch Rehearsal” consistent; no regressions observed |

---

## Source location & likely changed files

| Attribute | Detail |
|-----------|--------|
| **Project path** | `/Users/sparshnagpal/Desktop/projects/TryLapse-Landing Page/` (sibling to `TryLapse/` — **not** in monorepo git) |
| **Stack** | Vite + vanilla HTML/CSS/JS + animejs |
| **Port** | 8082 |
| **Git** | No git repo in landing project — changes inferred from file mtimes (~16:06–16:07 local) |

**Files touched since R1 (by inspection + mtimes):**

| File | Likely changes |
|------|----------------|
| `index.html` | Added `main.js` script tag; Formspree `action`; expanded FAQ (12); hero subhead + “Read CLI docs”; matrix `<button>` cells; pricing email bullet; footer GitHub URL + sample evidence anchor |
| `src/main.js` | Full interactivity: gauge animation, tabs, matrix modals, form validation/success, legal `<dialog>`, mobile menu, terminal typing |
| `src/style.css` | Modal, matrix button, mobile, animation styles |
| `dist/` | Production build artifact (`index-DVJlew7Q.js`) — 16:07 |

---

## Blocker re-test results

| Test | R1 | R2 |
|------|----|----|
| JS loading (gauge, tabs, form) | ✗ frozen at 0% | ✓ 92% Green; Persona Matrix tab selects; form handler attached |
| Form submit | ✗ GET → 403 Restricted | ✓ Client success state; no navigation; Calendly still `placeholder-demo` |
| Readiness narrative | ✗ contradictory badges/cells | ✓ Argyle thread coherent; Cal.com Amber isolated in methodology section |
| GitHub link | ✗ 404 `/rehearse` | ✗ 404 org URL |
| Pricing Slack bullet | ✗ over-promise | ✓ email channel |
| Matrix a11y | ✗ `<td>` clicks | ✓ focusable `<button>` + labels |
| Mobile overflow | ✗ 410/390 | ✗ unchanged 410/390 |
| Legal footer | ✗ `alert()` | ✓ `<dialog>` with real copy |
| FAQ count | 6 | 12 |
| Hero copy | missing no-auto-fix / CLI CTA | ✓ both present |

---

## Dimension scores (0–10, rendered UI)

| Dimension | R1 | R2 | Notes |
|-----------|----|----|-------|
| **Information architecture** | 8.0 | 8.0 | Full scroll narrative; 12 FAQ completes plan §2.5 |
| **Visual hierarchy** | 7.5 | 8.0 | Animated hero gauge; clearer evidence modal hierarchy |
| **Design spec fidelity** | 7.0 | 8.5 | Hero subhead, tertiary CLI CTA, FAQ count, pricing honesty |
| **Trust & evidence UX** | 5.0 | 6.5 | Argyle/compare story aligned; gallery/modals still wireframes |
| **Conversion / CTA path** | 4.0 | 6.5 | Form UX partner-ready; backend + Calendly still mock |
| **Accessibility** | 5.5 | 7.5 | Matrix buttons + legal dialog; H3 quoted-title AX truncation persists; mobile overflow |
| **Mobile responsiveness** | 6.5 | 6.5 | Hamburger + full-width CTAs ✓; +20px horizontal scroll ✗ |
| **Polish / motion** | 5.0 | 8.0 | animejs scope live: gauge, reveals, form transition, terminal |
| **Copy accuracy / honest scope** | 6.0 | 7.5 | Slack bullet fixed; dual run sources now labeled |
| **Performance (dev)** | 7.5 | 8.0 | TTFB 38ms, FCP 84ms (local) |

**Weighted overall: 7.8 / 10** (was 6.5)

---

## What works well (new or reinforced)

1. **End-to-end interactivity** — Announcement dismiss, tabs, matrix modals, mobile menu, form validation/success all functional.
2. **Conversion form UX** — Inline validation, spinner, animated success state; no PII leak via query string.
3. **Narrative coherence on Argyle thread** — Hero 92% Green / 0 blockers matches compare LATEST badge and resolved Admin J4 cell.
4. **Plan completeness** — 12 FAQ items cover pricing hypothesis, CI/Action, SOC2, scope boundaries.
5. **Accessibility wins** — Matrix operable pattern; legal content in accessible dialog (not alert).
6. **Honest pricing teaser** — Email async handoff aligns with integrations grid and CEO gates.

---

## Remaining issues (prioritized)

### P0 — before unsupervised public URL

| ID | Issue | Fix |
|----|-------|-----|
| DR-LP-03 | Formspree not wired in JS | Replace mock `setTimeout` with `fetch(form.action, { method:'POST', body: FormData })` or allow native POST; verify Formspree inbox |
| DR-LP-03b | Calendly placeholder | Replace `calendly.com/placeholder-demo` with real design-partner calendar |
| DR-LP-05 | GitHub 404 | Point to real repo/README (e.g. monorepo `launch-rehearsal/` path) or remove until Aug 2026 OSS decision |

### P1 — polish & trust

| ID | Issue | Fix |
|----|-------|-----|
| DR-LP-07 | Gallery + modal still CSS wireframes | Capture 4 real `:8081` screenshots from `argyle-20260531-000517`; label any remaining mocks |
| DR-LP-09 | Mobile +20px overflow | Audit announcement bar, agent strip, matrix table min-width; add `overflow-x: clip` on body if needed |
| DR-LP-04 (minor) | Cal.com Amber vs Argyle Green on same page | Add one-line source chip on hero mock (“Argyle dogfood”) vs sample block (“Cal.com Phase 0 methodology”) |

### P2 — nice to have

- H3 “Evidence-Free \"Looks Good\"" — AX tree truncates at quote; verify visible text (renders OK visually).
- Legal links still `href="#"` — consider `/legal/credentials` static pages for SEO/partner diligence.
- Move landing into `TryLapse/` monorepo for CI + shared review artifacts.

---

## Accessibility quick check

| Check | R2 result |
|-------|-----------|
| Heading hierarchy | Single H1 ✓ |
| Matrix keyboard | `<button>` cells with aria-label ✓ |
| Form labels | Associated + validation messages ✓ |
| Legal | `<dialog>` + close + Acknowledge ✓ |
| Mobile overflow | ✗ scrollWidth 410 > 390 |
| Reduced motion | CSS + JS branch present ✓ |

---

## Performance (localhost dev)

| Metric | R1 | R2 |
|--------|----|----|
| TTFB | 21ms | 38ms |
| FCP | 248ms | 84ms |
| LCP / CLS / INP | n/a | n/a (automation session) |

---

## Partner conversation readiness

**R2:** OK to use landing as **scroll companion on a live call** while demoing `:8081`.

**Do not** send URL for async self-serve partner signup until DR-LP-03 + DR-LP-05 fixed.

Recommended call flow:

1. Landing hero → trust chips → “observe only”
2. Sample scorecard (Cal.com methodology)
3. **Switch to live `:8081`** for real matrix/evidence (landing mockups are illustrative)
4. Form capture on call or follow-up email

---

## Screenshots captured (R2)

| File | Description |
|------|-------------|
| `01-hero-desktop-20260531-r2-20260531-161041.png` | Desktop hero 1280×720 — gauge at 92% Green |
| `02-product-gallery-20260531-r2-20260531-161053.png` | Product gallery with Persona Matrix tab selected |
| `03-lead-form-desktop-20260531-r2-20260531-161056.png` | Lead capture form block |
| `04-form-success-20260531-r2-20260531-161101.png` | Form success state (no 403) |
| `05-matrix-modal-20260531-r2-20260531-161142.png` | Matrix evidence modal — Admin J4 resolved |
| `06-hero-mobile-390-20260531-r2-20260531-161155.png` | Mobile hero 390×844 |
| `07-mobile-menu-open-20260531-r2-20260531-161224.png` | Mobile hamburger menu open |
| `08-full-page-desktop-20260531-r2-20260531-161232.png` | Full page desktop scroll capture |

Base path: `.cursor/gstack/launch-rehearsal/design-reviews/screenshots/landing-2026-05-31-r2/`

---

## Top remaining improvements (prioritized)

1. **Wire Formspree POST in JS** — stop mock-only success; confirm email delivery (DR-LP-03).
2. **Real Calendly URL** in success state (DR-LP-03b).
3. **Fix or remove GitHub footer link** until repo is public (DR-LP-05).
4. **Replace CSS wireframes** with 4 real `:8081` captures for gallery + matrix modal (DR-LP-07).
5. **Fix mobile horizontal overflow** — 410px scrollWidth on 390px viewport (DR-LP-09).
6. **Add run-source labels** on hero vs sample scorecard sections (DR-LP-04 minor).
7. **Static legal pages** instead of `#` hrefs (P2).
8. **Monorepo / CI** — bring `TryLapse-Landing Page` into `TryLapse/` for regression gates.

---

## Regression vs dashboard review (`:8081`)

| Dashboard strength | Landing R2 gap |
|--------------------|----------------|
| Real run data, evidence dialog | Marketing still uses CSS wireframes — **link to live demo on calls** |
| 8.6 partner-ready | Landing 7.8 — conversion backend incomplete |

---

*Review method: Browser DevTools MCP only · Desktop 1280×720 · Mobile 390×844 · localhost:8082 · 2026-05-31*
