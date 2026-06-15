# Impeccable /audit — Launch Rehearsal Dashboard
**Date:** 2026-06-03  
**Scope:** `Frontend_V1/src/`  
**Register:** product  
**`npx impeccable detect src/` result:** 1 anti-pattern (overused font: Inter)

---

## Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | 2/4 | 29 instances of text-[10px]; only 36 aria attrs across 66+ interactive elements |
| 2 | Performance | 3/4 | Mostly clean; Sparkline SVG recalculates on every render |
| 3 | Theming | 3/4 | Excellent oklch token system; error-page.ts and chart.tsx use hard-coded hex values |
| 4 | Responsive | 2/4 | Sidebar hidden on mobile with no hamburger; several fixed-width table cells |
| 5 | Anti-Patterns | 3/4 | Overused font (Inter — acceptable for product register); 29× sub-11px text; no glassmorphism/gradient-text |
| **Total** | | **13/20** | **Acceptable — significant work in a11y + responsive** |

---

## Anti-Patterns Verdict

**Does this look AI-generated?** Mostly no — 2 mild tells:

1. **Sub-11px text everywhere** (`text-[10px]` in 29 places) — classic AI slop pattern: metadata gets compressed into illegibly small labels to fit "everything on screen." Impeccable flags this as a readability anti-pattern.
2. **Overused font (Inter)** — flagged by `detect`. Per the product register, Inter is explicitly allowed for product dashboards ("system fonts and familiar sans defaults are permitted"). The real fix is locking the *scale*, not changing the font.

What's clean: no gradient text, no glassmorphism, no bounce animations, status colors are semantic, dimension cards don't nest, no decorative gradients.

---

## Executive Summary

- **Audit Health Score:** 13/20 (Acceptable)  
- **P0:** 0 issues  
- **P1:** 4 issues (2× a11y, 1× responsive, 1× tiny text systemic)  
- **P2:** 5 issues  
- **P3:** 3 issues  

**Top issues:**
1. 36 aria attributes for 66+ interactive elements — coverage gap on buttons/links
2. 29 instances of sub-11px text (`text-[10px]`) — fails WCAG at body copy usage
3. No mobile sidebar fallback — hamburger hidden, no drawer
4. Hard-coded hex values in `error-page.ts` and `chart.tsx` — breaks theming

---

## Detailed Findings by Severity

### P1 — Major

**[P1] Sub-11px text used for meaningful content**  
- **Location:** 29 files; common in `rehearse-top-bar.tsx`, `persona-editor-panel.tsx`, `job-queue-status.tsx`, `dimension-rollup.tsx`, `run-history-live-rows.tsx`  
- **Category:** Accessibility  
- **Impact:** Text below 11px on a standard monitor fails WCAG 1.4.4 (resize text). `text-[10px]` labels in form editors and sidebar chips are unreadable at the default zoom level for users with moderate visual impairment.  
- **WCAG:** 1.4.4 Resize Text (AA)  
- **Recommendation:** Enforce a 5-step type scale: 11 / 13 / 15 / 18 / 24. Rename `text-[10px]` occurrences → `text-[11px]` across all files. Create a Tailwind alias `text-label` = 11px so it's systematic.  
- **Suggested command:** `/impeccable typeset`

**[P1] Interactive element aria coverage gap**  
- **Location:** 36 aria attributes for 66+ `<button>` and `<a>` tags across `src/`  
- **Category:** Accessibility  
- **Impact:** ~45% of interactive elements lack explicit aria labels. Users on screen readers can't identify icon-only buttons (compare swap, evidence toggle, env selector arrow).  
- **WCAG:** 4.1.2 Name, Role, Value (AA)  
- **Recommendation:** Audit icon-only buttons and add `aria-label`. The compare page already had this fixed per prior session — same pattern needed in rehearse-top-bar (env selector), dimension cards (clear filter button), run detail evidence toggle.  
- **Suggested command:** `/impeccable harden`

**[P1] No mobile sidebar fallback**  
- **Location:** `app-sidebar.tsx:73` — `className="hidden md:flex"`; no hamburger drawer  
- **Category:** Responsive  
- **Impact:** On mobile/tablet, the entire navigation disappears with no alternative. Users land on a blank left edge.  
- **WCAG:** 1.3.4 Orientation, 2.4.1 Bypass Blocks  
- **Recommendation:** Add a Sheet/Drawer component triggered by a hamburger button in the top bar for `<md` viewports. Prior session mentioned a dialog sheet was added to the landing page — same pattern needed in Frontend_V1.  
- **Suggested command:** `/impeccable adapt`

**[P1] Fixed-width table cells break at narrow viewports**  
- **Location:** `job-queue-status.tsx:106` — `max-w-[280px]`; also several `w-[N]` patterns  
- **Category:** Responsive  
- **Impact:** Tables in the runs list and job queue overflow horizontally on viewports < 1024px.  
- **Recommendation:** Replace fixed widths with `min-w-0 truncate` on string cells; use `w-full` + priority column hiding on mobile.  
- **Suggested command:** `/impeccable adapt`

---

### P2 — Minor

**[P2] Hard-coded hex colors in error-page.ts**  
- **Location:** `src/lib/error-page.ts:9-16` — `#fafafa`, `#111`, `#4b5563`, `#d1d5db`  
- **Category:** Theming  
- **Impact:** The error boundary page won't respect the oklch token palette. If background or text color changes in a future theme, error pages stay wrong.  
- **Recommendation:** Inline CSS variables: `background: var(--background)`, `color: var(--foreground)`, etc. OK to keep inline style (it's a fallback page), but use the tokens.  
- **Suggested command:** `/impeccable harden`

**[P2] Recharts chart.tsx uses `#ccc` for grid strokes**  
- **Location:** `src/components/ui/chart.tsx:51`  
- **Category:** Theming  
- **Impact:** Chart grid lines use a hard-coded gray that won't adapt. In a dark mode or future theme variant they'll look wrong.  
- **Recommendation:** Replace `[stroke='#ccc']` selectors with `var(--border)` or `var(--grid-line)` (the `--grid-line` token already exists in styles.css for this purpose).  
- **Suggested command:** `/impeccable harden`

**[P2] `rgba()` in annotated-screenshot.tsx breaks theming**  
- **Location:** `src/components/annotated-screenshot.tsx:57` — `shadow-[0_0_0_1px_rgba(255,255,255,0.6)]`  
- **Category:** Theming  
- **Impact:** Hard-coded white shadow will be invisible against a white background in a light theme variant.  
- **Recommendation:** Replace with `shadow-[0_0_0_1px_color-mix(in_oklab,var(--background)_60%,transparent)]`  
- **Suggested command:** `/impeccable harden`

**[P2] Sparkline SVG recalculates on every render**  
- **Location:** `src/components/ui-bits.tsx` — Sparkline component  
- **Impact:** Minor: no `useMemo` on the point path calculation. With many runs loaded, the trend sparkline in the command center recomputes the SVG path string on every parent render.  
- **Recommendation:** Wrap the `points` and `d` path string in `useMemo`.  
- **Suggested command:** `/impeccable optimize`

**[P2] Missing `text-wrap: balance` on headings**  
- **Location:** `styles.css:134-140` — heading reset block  
- **Category:** Anti-Pattern  
- **Impact:** Long section titles (e.g. "Evaluation rubric", "Agent control center") can orphan a single word on the last line. `text-wrap: balance` is now supported in all modern browsers.  
- **Recommendation:** Add `text-wrap: balance` to the `h1, h2, h3, h4` block in styles.css.  
- **Suggested command:** `/impeccable typeset`

---

### P3 — Polish

**[P3] Instrument Serif loaded but used minimally**  
- **Location:** `styles.css:1`, `styles.css:19` — Google Font import + `--font-serif` token  
- **Impact:** Extra network request for a font used only in 1–2 places. Slight performance hit on first paint.  
- **Recommendation:** Either use it intentionally (e.g. as a display voice in the readiness verdict) or remove it from the import and `--font-serif` definition.  
- **Suggested command:** `/impeccable typeset`

**[P3] `box-shadow: none` on `panel-quiet` may miss intent**  
- **Location:** `styles.css:185-190`  
- **Impact:** Low. The `panel-quiet` utility intentionally removes shadow, but it also removes the border opacity reduction at a slightly different rate than expected. Not visually broken, just slightly inconsistent with the opacity cascade.  
- **Suggested command:** `/impeccable polish`

**[P3] Status pulse animation fires on `ready` (green) state**  
- **Location:** `styles.css:192-204` — `@keyframes pulse-ready` / `@utility pulse-dot`  
- **Impact:** The pulse animation is wired for the "ready" (healthy) state. In 2026 calm design conventions, healthy state should be *silent* — pulse/glow is reserved for Amber/Red (needs attention). Pulsing green creates low-level anxiety.  
- **Recommendation:** Either remove the pulse on `ready`, or repurpose `pulse-dot` as the `warn`/`danger` animation only.  
- **Suggested command:** `/impeccable quieter`

---

## Patterns & Systemic Issues

1. **Sub-11px text is a systemic problem** — appears in 29 files. This is a type scale problem, not a component problem. The solution is a locked 5-step scale enforced once in styles.css + consistent class naming, not 29 individual fixes.

2. **Aria coverage is reactive, not systematic** — aria-labels were added to the compare page after a prior review, but the pattern didn't propagate. The fix is to audit `icon-only` button pattern once and add it as a Tailwind variant or a shared `IconButton` component wrapper.

3. **Hard-coded values in 3 files** — isolated, not pervasive. The oklch token system is otherwise excellent. These 3 files need a one-time cleanup.

---

## Positive Findings

- **Excellent oklch token system** — the full semantic palette in `styles.css` with `--ready/warn/danger/info/violet` is best-practice. No random hex values in component files (except the 3 flagged above).
- **`panel` + `panel-quiet` utility design** — the two-tier surface system is the right approach and well-implemented.
- **Semantic status chips** — `Chip` with tone variants, `SeverityChip`, `StatusDot` are clean and consistent. Status meaning is the same everywhere.
- **No glassmorphism, no gradient text, no bounce animations** — the codebase avoids the most common AI slop tells.
- **JetBrains Mono for IDs/code** — exactly right for an operator console. Step IDs, run IDs, and config values are clearly differentiated.
- **`text-wrap: balance` is missing on headings** but the `-0.02em` letter-spacing and `font-weight: 600` heading baseline are solid.

---

## Recommended Actions (Priority Order)

1. **[P1] `/impeccable typeset`** — Lock 5-step type scale (11/13/15/18/24), replace all `text-[10px]` occurrences, add `text-wrap: balance` to heading reset, remove or use Instrument Serif intentionally
2. **[P1] `/impeccable harden`** — Fix aria coverage on icon-only buttons, replace hard-coded hex in error-page.ts + chart.tsx + annotated-screenshot.tsx
3. **[P1] `/impeccable adapt`** — Add mobile sidebar drawer/hamburger, fix fixed-width table cells
4. **[P2] `/impeccable quieter`** — Remove pulse animation from healthy/green state (reserve for warn/danger), reduce border noise with graduated opacity  
5. **[P2] `/impeccable optimize`** — Memoize Sparkline SVG path calculation
6. **[P3] `/impeccable polish`** — Final consistency pass (panel-quiet border, Instrument Serif removal)

> You can ask me to run these one at a time, all at once, or in any order you prefer.
>
> Re-run `/impeccable audit` after fixes to see your score improve.
