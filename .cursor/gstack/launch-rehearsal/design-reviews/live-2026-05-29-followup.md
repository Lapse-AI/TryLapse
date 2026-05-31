# Design Review Follow-up — Launch Rehearsal (Lovable)

**Date:** 2026-05-29 (re-check)  
**URL:** [Lovable preview](https://id-preview--684972b7-df8d-423b-81e4-d9fc744da026.lovable.app/)  
**Prior review:** `live-2026-05-29.md` (7.0/10)

---

## Overall: **8.4 / 10** (+1.4)

Batch A/B/C fixes from the prior review are largely implemented. The prototype now passes the **trust loop** — the core CEO gate for Launch Rehearsal.

---

## Score delta

| Dimension | Before | After | Δ |
|-----------|--------|-------|---|
| Trust & evidence UX | 5.0 | **9.0** | +4.0 |
| Interaction completeness | 5.5 | **8.5** | +3.0 |
| Accessibility | 6.0 | **7.5** | +1.5 |
| Mobile responsiveness | 4.0 | **7.5** | +3.5 |
| Data clarity | 6.5 | **8.5** | +2.0 |
| Polish / anti-slop | 6.5 | **8.0** | +1.5 |
| **Overall** | **7.0** | **8.4** | **+1.4** |

---

## Fixed since last review

| ID | Issue | Verification |
|----|-------|--------------|
| **DR-01** | Green + P0 contradiction | Home: `82 Readiness · /100 **Red**`; run detail: `Band: Red` |
| **DR-02** | Blocker count mismatch | Home + table: **Blockers 4**; run detail: `P0 + P1` |
| **DR-03** | Evidence no-op | **Evidence** opens dialog: screenshot · step j2.s4 · Copy repro · Open in step timeline |
| **DR-04** | Matrix not interactive | Cells are **buttons** with full aria labels; click opens journey dialog with steps/issues |
| **DR-05** | Severity filters broken | Toggle chips `P0 · 1` etc.; filtering to P0-only shows **"1 of 8 findings"** |
| **DR-06** | `EVALUATION_FRAMEWORK.md` in UI | Now **"Evaluation rubric"** |
| **DR-07** | Mobile sidebar crush | **Open navigation** → `dialog "Navigation"` with Close button |
| **DR-08** | Env not selectable | **`prod-canary`** is a button in header breadcrumb |
| **DR-09** | Lowercase CTAs | **Crawl only**, **Diff**, **Export**, **Evidence** capitalized |
| **DR-18** | warn vs partial | Matrix uses **pass / partial / fail** (scorecard-aligned) |

---

## Still open (non-blocking for design partner demo)

| ID | Issue | Severity |
|----|-------|----------|
| DR-11 | Site map graph still static `img` | P2 |
| DR-12 | Skeptic Sam in matrix but no 4th persona agent | P2 |
| DR-14 | No `aria-current="page"` on active nav link | P3 |
| DR-15 | ⌘K search hint removed (good) but command palette not verified | P3 |
| DR-16 | Lovable badge still present | P3 |
| DR-17 | Numeric 82 + Red band — clearer but could use tooltip | P3 |
| DR-20 | Diff / Export buttons — menus not verified | P2 |

---

## Highlight: evidence dialog (trust loop)

Clicking **Evidence** on P0 SSO issue opens:

```
dialog "SSO callback drops session on Safari 17"
  - screenshot · step j2.s4 · 1280×720
  - Network: 302 → / with no Set-Cookie. Repro 5/5.
  - Owner heuristic backend · Recurrence ×3 runs
  - [Copy repro] [Open in step timeline] [Close]
```

This matches `MONITORING_PLATFORM_DESIGN.md` §8.3.4 and CEO evidence-binding requirements.

---

## Highlight: matrix drill-down

Clicking matrix cell `Prospect Priya, Land → Pricing → Signup: fail` opens:

```
dialog "Prospect Priya · Land → Pricing → Signup"
  - fail · pricing · 7 steps
  - Related issues: P1 CTA mismatch (j1.s3), P3 footer year (j1.s1)
```

---

## Verdict

**Ready for design partner demos** after dismissing the Lovable badge. The UI now sells *believable scorecards* — the actual moat.

Next polish pass: static sitemap graph, Export/Diff menus, Skeptic Sam agent parity, aria-current on nav.

---

## Addendum — 2026-05-30 (Frontend_V1 + live API)

| Change | Impact on demo readiness |
|--------|--------------------------|
| Frontend_V1 proxied to `./rehearse serve` on `:8765` | Command center, runs, agents, sitemap, trends show **real** enterprise/argyle runs |
| Analysis bundle export + backfill | 13+ runs with screenshots served from `/files/` |
| `/runner`, `/library`, `/init` routes | Trigger runs and browse configs from UI |
| Mock Acme (`run_8s7d2`) | Fallback only when API down — **do not demo** when live |

**Updated verdict:** Concierge design partner demos **GO** — see `enterprise_work_env_simulator_2026/DESIGN_PARTNER_CHECKLIST.md` for demo script and remaining L2 gaps (export, compare selectors, hardcoded KPIs).

**Still open from prior review:** DR-11 (static sitemap graph), DR-20 (Export/Diff menus), DR-12 (4th persona agent), DR-14 (aria-current).
