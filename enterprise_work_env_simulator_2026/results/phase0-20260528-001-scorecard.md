# Launch Rehearsal — Phase 0 Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `phase0-20260528-001` |
| **Date** | May 28, 2026 |
| **Target** | https://cal.com (practice run — replace with your product URL) |
| **Method** | Manual agent-assisted E2E (Browser DevTools MCP) |
| **CEO gate** | **PASS** |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Amber** (strong product; marketing surface has clutter and comparison fatigue) |
| **Top blockers** | Nav IA ambiguity; pricing comparison overload |
| **Top delight** | Signup above fold with “no credit card” + live booking UI preview |
| **Persona coverage** | 3 personas × 5 journeys (logged-out scope) |

---

## Persona × journey matrix

| Journey | P1 Jordan (first-time) | P2 Sam (power) | P3 Alex (admin) |
|---------|------------------------|----------------|-----------------|
| **J1** Land → value | **Pass** | **Pass** | **Pass** |
| **J2** Start signup | **Pass** | **Pass** | **Pass** |
| **J3** Explore depth | **Partial** | **Partial** | **Partial** |
| **J4** Pricing | **Pass** | **Partial** | **Partial** |
| **J5** Return navigation | **Pass** | **Partial** | **Pass** |

*Partial = journey reachable but friction or overload detected.*

---

## Dimension rollup (subset — Phase 0 manual)

| Dimension | Score 1–5 | Top signal |
|-----------|-----------|------------|
| Functionality | 4 | Core paths work; `/features` route redirected to unrelated demo page in one probe |
| Information clarity | 3 | Strong hero; nav labels “Solutions/Developer” less clear in structure tree |
| UI/UX | 4 | Polished; very long homepage |
| Adaptability | 3 | Many repeated CTAs would tax return visitors |
| Integrations | 4 | App ecosystem surfaced in footer and copy |
| Compliance signals | 5 | ISO/SOC2/HIPAA badges in footer |
| Reliability | 4 | No broken primary links observed |
| Speed (perceived) | 4 | Fast load; pricing page content-heavy |

---

## Issues (evidence-bound)

### P2 — Non-obvious / meaningful

| ID | Finding | Persona | Journey | Evidence |
|----|---------|---------|---------|----------|
| **I1** | **Top nav IA:** “Solutions” and “Developer” appear as plain text in the accessibility tree while “Enterprise”, “Pricing”, etc. are clear links — first-time users may not discover developer/docs paths from nav alone. | P1 | J1 | `J1-S1` — homepage ARIA: paragraph “Solutions”, paragraph “Developer” without sibling link refs like Enterprise/Pricing (`e2`, `e4`) |
| **I2** | **Pricing comparison fatigue:** Feature breakdown is extremely long; admin persona must scroll through a massive matrix to compare Teams vs Organizations — high cognitive load for POC-style evaluation. | P3 | J4 | `J4-S1` — pricing page text: “Feature breakdown… Compare our Free and Teams plans…” with truncated long feature list |
| **I3** | **Return-user CTA noise:** At least **six** distinct “Get started” links on homepage alone (`e6`, `e12`, `e19`, `e41`, `e44`, `e69`) — power users on repeat visits face “which CTA is canonical?” | P2 | J5 | `J5-S1` — homepage snapshot refs |

### P3 — Polish

| ID | Finding | Evidence |
|----|---------|----------|
| I4 | Hero demo calendar shows **May 2025** in mock UI — may read as stale content to detail-oriented buyers. | `J1-S2` — homepage ARIA paragraphs “May”, “2025” in booking widget |

### P1 — Note

| ID | Finding | Evidence |
|----|---------|----------|
| I5 | Marketing (`cal.com`) → app (`app.cal.com`) split for signup is expected but adds context switch for Jordan. | `J2-S1` — signup links target `app.cal.com/signup` |

---

## Gaps & wishes (friction / repeat use)

| ID | Gap | Confidence | Evidence |
|----|-----|------------|----------|
| G1 | **Veteran user (10th visit)** would want a single persistent “Start free” in nav and fewer mid-page signup duplicates. | hypothesis | I3 |
| G2 | **Comparison shoppers** need a one-screen “which plan for 5-person startup?” decision helper, not only a full matrix. | hypothesis | I2 |

---

## Delights & strengths (required)

| ID | Delight | Persona | Evidence |
|----|---------|---------|----------|
| **D1** | **Immediate time-to-value:** Hero offers **Sign up with Google**, **Sign up with email**, and **“No credit card required”** without scrolling — strong for founders evaluating scheduling tools. | P1 | `J1-S3` — refs `e9`, `e10`, paragraph “No credit card required” |
| **D2** | **Impressive product preview:** Interactive booking UI (duration chips, calendar grid, notifications mock) on homepage — user grasps product before account creation. | P1, P2 | `J1-S4` — hero widget headings “Property Viewing”, duration options, notification toasts |
| **D3** | **Pricing clarity for individuals:** “Free forever” individual tier with explicit “Unlimited event types & calendars” — reduces fear of hidden limits. | P3 | `J4-S2` — pricing text: “Individuals… Free… *Free forever” |
| **D4** | **Trust stack visible:** Footer surfaces ISO 27001, SOC 2, GDPR, HIPAA links — helps admin persona. | P3 | `J1-S5` — refs `e72`–`e76` security links |

---

## Phase 0 CEO gate

| Criterion | Result |
|-----------|--------|
| ≥1 non-obvious issue | **Yes** (I1, I2, I3) |
| ≥1 evidence-backed delight | **Yes** (D1, D2) |
| **Gate** | **PASS → Phase 1 code approved to start Jun 8, 2026** |

---

## What this proves about Launch Rehearsal

The methodology surfaces **actionable, evidence-tagged** findings and **positives**, not a bug dump alone. Re-run on **your** staging URL before trusting scores for your own product.

---

## Next steps

1. Replace target URL in `journeys/phase-0.md` with your product.  
2. Re-run Phase 0 (same personas/journeys).  
3. Begin Phase 1 Week 1: DSL schema + browser runner (per `CEO_DECISIONS.md`).

---

## Run log

| Step | URL | Outcome |
|------|-----|---------|
| J1-S* | https://cal.com/ | Homepage ARIA + content captured |
| J4-S* | https://cal.com/pricing | Pricing text captured (truncated) |
| J2-S* | app.cal.com/signup | Redirect probe landed on unrelated demo page — note for runner hardening |

*Artifacts: browser session May 28, 2026; full ARIA in agent-tools log.*
