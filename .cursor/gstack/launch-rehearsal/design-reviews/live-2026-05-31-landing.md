# Design Review — Launch Rehearsal Marketing Landing Page

**Date:** 2026-05-31  
**URL:** http://localhost:8082/ (reachable — HTTP 200)  
**Reference:** `enterprise_work_env_simulator_2026/LANDING_PAGE_PLAN.md` · dashboard review [live-2026-05-31.md](./live-2026-05-31.md)  
**Method:** Browser DevTools MCP — ARIA snapshots, viewport 1280×720 + 390×844, interaction probes, Web Vitals  
**Screenshots:** `.cursor/gstack/launch-rehearsal/design-reviews/screenshots/landing-2026-05-31/`

---

## Executive summary

**Overall: 6.5 / 10**

This is a **dedicated marketing landing page** — not `Frontend_V1` (`:8081`). It lives in a sibling Vite project at `/Users/sparshnagpal/Desktop/projects/TryLapse-Landing Page` (`npm run dev` → `:8082`). It implements ~90% of `LANDING_PAGE_PLAN.md` section IA and copy faithfully, with strong visual tokens (OKLCH indigo canvas, Instrument Serif accent) and honest integrations grid.

**Verdict:** **Not partner-shippable yet.** The primary conversion path is broken: **`main.js` is never loaded** (missing entry script in `index.html`), so form submit falls through to a native GET navigation → Vite **403 Restricted** error with PII in the query string. Even after fixing the script tag, the form is mock-only (no Formspree/Calendly backend).

**North-star fit:** Messaging (“design partner”, “Get a staging scorecard”, observe-only) aligns with concierge mode. Execution gaps undermine the trust story the page sells.

---

## What is this page?

| Attribute | Detail |
|-----------|--------|
| **Surface** | Standalone static marketing site (Vite + vanilla HTML/CSS/JS + animejs) |
| **Not** | Frontend_V1 vision mode, dashboard, or in-repo `TryLapse/` path |
| **Source** | `TryLapse-Landing Page/` — `index.html`, `src/main.js`, `src/style.css` |
| **Port** | 8082 (`vite --port 8082 --host`) |
| **Dashboard** | Separate product at `:8081` — landing mocks it with CSS wireframes |
| **Plan alignment** | Sections 0–13 from `LANDING_PAGE_PLAN.md` largely present |

---

## Pages / sections reviewed

| Section | Plan ID | Rendered | Notes |
|---------|---------|----------|-------|
| Announcement bar | 0 | ✓ | Dismissible (JS-dependent) |
| Hero | 1 | ✓ | H1 matches plan option A |
| Problem / pain cards | 2 | ✓ | |
| How it works + agent strip | 3 | ✓ | Concierge copy honest |
| Product gallery tabs | 4 | ⚠️ | CSS mockups only; tabs need JS |
| Interactive persona matrix | 5 | ⚠️ | Click → modal (JS); placeholder screenshots |
| Sample scorecard | 6 | ✓ | Cal.com + Argyle footnote |
| Compare / diff story | 7 | ⚠️ | Red→Green copy vs AMBER Tuesday badge |
| CLI + terminal | 8 | ⚠️ | Typing animation JS-dependent |
| Integrations grid | 9 | ✓ | Honest Available vs Roadmap |
| Pricing teaser | 10 | ⚠️ | “Direct Slack channel” over-promise |
| Lead form | 11 | **✗** | GET submit → 403; no backend |
| FAQ | 12 | ⚠️ | 6/12 planned questions |
| Footer | 13 | ⚠️ | Broken GitHub; alert() legal links |

---

## Dimension scores (0–10, rendered UI)

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Information architecture** | 8.0 | Full scroll narrative; anchor nav matches plan |
| **Visual hierarchy** | 7.5 | Strong H1 + dual CTA; announcement bar competes slightly |
| **Design spec fidelity** | 7.0 | Structure/copy track `LANDING_PAGE_PLAN.md`; missing tertiary “Read CLI docs” in hero |
| **Trust & evidence UX** | 5.0 | Mixed Cal.com Amber + Argyle Green + hero “0 blockers” vs matrix blocker; CSS-only “screenshots” |
| **Conversion / CTA path** | 4.0 | Form ship-blocker; placeholder Calendly; no lead capture backend |
| **Accessibility** | 5.5 | Matrix `<td>` clicks not buttons; quoted H3 breaks in AX tree; mobile +20px horizontal scroll |
| **Mobile responsiveness** | 6.5 | Stack + hamburger present; matrix table scroll; minor overflow |
| **Polish / motion** | 5.0 | Hero gauge stuck at 0%/“Analyzing…” without JS; reveal animations inert |
| **Copy accuracy / honest scope** | 6.0 | Good FAQ observe-only; pricing Slack bullet contradicts integrations honesty |
| **Performance (dev)** | 7.5 | FCP 248ms, TTFB 21ms local; Google Fonts external |

**Weighted overall: 6.5 / 10**

---

## What works well

1. **Positioning copy** — H1 “Pre-launch readiness, observed.” and concierge subhead match plan and dashboard headline continuity.
2. **CTA hierarchy** — Primary “Get a staging scorecard” repeated in nav, hero, pricing, form; secondary “See sample scorecard” present.
3. **Honest integrations section** — Available now vs Roadmap (Q3/Q4) grid matches `FEATURE_SCOPE.md` / CEO gates.
4. **Sample scorecard block** — Real Cal.com Phase 0 language + Argyle dogfood stat line; markdown download works (`/src/assets/sample-scorecard.md` → 200).
5. **Design tokens** — OKLCH palette, Instrument Serif accent, JetBrains Mono in CLI block align with plan §8 visual direction.
6. **Form UX design** — Field set, validation rules, privacy guard copy, and success-state layout are partner-ready *once wired*.

---

## Critical issues (ship blockers)

### DR-LP-01 — `main.js` never loaded (P0)

**Observed:** Served HTML injects `@vite/client` only — **no** `<script type="module" src="/src/main.js">`.  
**Impact:** No animations, tab switching, matrix modals, form `preventDefault`, mobile menu, or terminal simulator. Hero readiness gauge frozen at **0% / “Analyzing…”**.  
**Fix:** Add before `</body>`:

```html
<script type="module" src="/src/main.js"></script>
```

### DR-LP-02 — Form submit → GET navigation → Vite 403 (P0)

**Observed:** Filling form and clicking “Request partner slot” navigates to:

`/?email=partner%40test.com&url=https%3A%2F%2Fstaging.example.com&role=eng-lead&...`

→ **403 Restricted** (Vite fs allow list). PII exposed in URL.  
**Root cause:** DR-LP-01 — submit handler never attached.  
**Fix:** DR-LP-01 + `method="post"` + `action="#"` on form; wire Formspree/Netlify/Calendly per plan §8.5.

### DR-LP-03 — No real lead capture backend (P0 for public launch)

**Observed:** Success state is client-side mock; Calendly href is `https://calendly.com/placeholder-demo`.  
**Fix:** Formspree or partner table + real Calendly embed per `LANDING_PAGE_PLAN.md` §8.5 / §9.1.

---

## High-priority issues (beyond product photos / name)

| ID | Issue | Why it matters |
|----|-------|----------------|
| DR-LP-04 | **Readiness narrative inconsistency** — Hero mockup: 0 blockers + `run_argyle_latest`; matrix shows Admin J4 **Blocker**; sample scorecard is **Amber** (Cal.com); dogfood footnote **Green** (Argyle); compare prose **Red→Green** but Tuesday badge **AMBER 68%** | Skeptical eng lead sees contradictory evidence on one page |
| DR-LP-05 | **GitHub footer link 404** — `https://github.com/launch-rehearsal/rehearse` | Broken trust signal for “CLI for engineers” |
| DR-LP-06 | **Pricing teaser: “Direct Slack channel”** | Contradicts integrations grid (Slack = Roadmap Q3) and `CEO_DECISIONS.md` do-not-claim |
| DR-LP-07 | **Evidence modal shows “Staging UI Screenshot Mockup”** placeholder | Undermines “evidence-bound” pillar; label the mock honestly or use real `:8081` captures |
| DR-LP-08 | **Matrix cells are `<td>` not `<button>`** | Not keyboard-focusable; fails WCAG operable pattern; screen readers announce “cell” not “button” |
| DR-LP-09 | **Mobile horizontal overflow** — `scrollWidth 410` vs `clientWidth 390` | Subtle sideways scroll on 390px viewport |
| DR-LP-10 | **Legal links use `alert()` placeholders** | Credential Handling / ToS feel unfinished for partner calls |
| DR-LP-11 | **Footer “Sample evidence” → `#product-story`** not `#sample-scorecard` | Wrong destination vs nav label |
| DR-LP-12 | **FAQ truncated** — 6 items vs 12 in plan §2.5 | Missing pricing, CI/GitHub Action, user research, SOC2 questions |
| DR-LP-13 | **Hero missing plan subhead clause** — “Evidence-bound. No auto-fix.” not in hero body (only in trust chips partially) | Plan §4.1 pairs H1 with explicit no-auto-fix sentence |
| DR-LP-14 | **Compare NLU quote shown before scroll** — default text is “after” state while Tuesday badge visible | Minor motion/story sync issue when JS loads |

---

## Accessibility quick check

| Check | Result |
|-------|--------|
| Heading hierarchy | Single H1 ✓; H2 section titles ✓ |
| H3 with embedded quotes | AX tree truncates “Evidence-Free \"Looks Good\"" — verify visible text OK |
| Focus / keyboard | Matrix interactive cells ✗; tabs are real `<button role=tab>` ✓ |
| Form labels | Associated labels + `aria-live` on errors ✓ |
| Contrast | Indigo on white CTAs OK; `--ink-muted` body may be borderline on warm canvas — spot-check |
| Touch targets | Mobile CTAs full-width ✓; hamburger ~44px ✓ |
| Reduced motion | CSS `@media (prefers-reduced-motion)` + JS branch present ✓ (when JS loads) |

---

## Performance (localhost dev)

| Metric | Value | Rating |
|--------|-------|--------|
| TTFB | 21ms | good |
| FCP | 248ms | good |
| LCP / CLS / INP | n/a in automation session | — |

Plan target LCP < 2.5s on 4G — likely met when built/static; verify with production build + real fonts.

---

## Comparison to `LANDING_PAGE_PLAN.md`

| Plan requirement | Status |
|------------------|--------|
| Design partner CTA (not PLG) | ✓ |
| No public pricing tiers | ✓ |
| Sample scorecard embed | ✓ (inline, not PDF) |
| Real `:8081` screenshots | ✗ (CSS wireframes) |
| Form + Calendly | ✗ (mock / placeholder) |
| 12 FAQ items | ✗ (6) |
| Tertiary “Read CLI docs” in hero | ✗ (Docs nav → `#cli-docs` only) |
| Customer logos / quotes | ✓ correctly omitted (blocked) |

---

## Partner conversation readiness

**Do not send this URL to partners until DR-LP-01–03 are fixed.**

When fixed, walk:

1. Hero → trust chips → “observe only”
2. Sample scorecard section (methodology)
3. Integrations honesty grid
4. Live `:8081` demo on call (landing mockups are not the product)

Record: *“Would you run this before every launch?”*

---

## Screenshots captured

| File | Description |
|------|-------------|
| `01-hero-desktop-20260531-155909.png` | Desktop hero (1280×720) — gauge at 0% without JS |
| `02-product-matrix-tab-20260531-155927.png` | Product gallery area |
| `03-sample-scorecard-20260531-155957.png` | Sample scorecard section |
| `04-lead-form-desktop-20260531-155959.png` | Lead capture form block |
| `05-matrix-modal-20260531-160001.png` | Persona matrix (modal not visible — JS absent) |
| `06-hero-mobile-390-20260531-160031.png` | Mobile hero 390×844 |
| `07-mobile-menu-open-20260531-160054.png` | Mobile viewport (menu state) |
| `08-form-success-20260531-160107.png` | **Vite 403** after form GET submit (failure capture) |
| `09-full-page-desktop-20260531-160107.png` | Full page (post-form-break state) |

Base path: `.cursor/gstack/launch-rehearsal/design-reviews/screenshots/landing-2026-05-31/`

---

## Top 10 prioritized improvements (excluding product photos / product name)

1. **Add `main.js` script entry** — unblocks all interactivity (DR-LP-01).
2. **Wire form to real backend + fix submit** — Formspree/Calendly; never GET-with-querystring (DR-LP-02, DR-LP-03).
3. **Reconcile readiness story** — Pick one demo run narrative per section or label sources explicitly (Cal.com vs Argyle vs compare runs) (DR-LP-04).
4. **Fix GitHub + Calendly + legal URLs** — No 404s, no placeholders, no `alert()` (DR-LP-05, DR-LP-10).
5. **Remove “Direct Slack channel” from pricing bullets** — Replace with “Email/async handoff” (DR-LP-06).
6. **Matrix a11y** — `<button type="button">` per cell, `aria-label`, focus trap in `<dialog>` (DR-LP-08).
7. **Fix mobile horizontal overflow** — Audit wide elements (matrix, agent strip, announcement) (DR-LP-09).
8. **Expand FAQ to plan’s 12 questions** — Especially pricing hypothesis, CI/Action, SOC2 (DR-LP-12).
9. **Footer/nav link accuracy** — Sample evidence → `#sample-scorecard`; Docs → GitHub README or `/docs` (DR-LP-11).
10. **Hero initial state without JS** — SSR/build-time static 92% Green + visible matrix dots for no-JS/first paint (DR-LP-01 mitigation).

---

## Regression vs dashboard review (live-2026-05-31.md @ :8081)

| Dashboard strength | Landing gap |
|--------------------|-------------|
| Real run data, evidence dialog | CSS mockups + placeholder modal screenshots |
| 8.6 partner-ready | Landing 6.5 — conversion path broken |
| Compare Red→Green live | Marketing compare badges internally inconsistent |

Landing should **link to live demo** (`:8081` on partner calls) rather than imply mockups are the product.

---

## Recommended next engineering

1. One-line script tag + `vite build` smoke test (form, tabs, gauge).
2. Capture 4 real screenshots from `argyle-20260531-000517` on `:8081` for gallery tabs.
3. Formspree + Calendly in success state.
4. Move landing repo into `TryLapse/` monorepo or document sibling dependency for CI.

---

*Review method: Browser DevTools MCP only · Desktop 1280×720 · Mobile 390×844 · localhost:8082 reachable*
