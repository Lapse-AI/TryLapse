# Competitive lens — Blok (joinblok.co)

**Last updated:** 2026-06-01  
**Sources:** [Blok homepage](https://www.joinblok.co/), [behavioral fidelity methodology](https://www.joinblok.co/insights/fidelity-methodology), [TechCrunch Jul 9, 2025](https://techcrunch.com/2025/07/09/blok-is-using-ai-persons-to-simulate-real-world-app-usage/)

**Roadmap IDs:** `FEATURE_SCOPE.md` §4.12 (`L3-PRED-*`) · **Do not block** current execution (§0 sprints, design partners).

---

## 1. What Blok sells

| Capability | Blok (marketed) |
|------------|-----------------|
| **Input** | Product analytics export (Amplitude, Mixpanel, Segment); Figma + experiment hypothesis |
| **Core loop** | Model personas from real behavior → run many agent simulations → report friction, drop-off, lift |
| **Output** | Experiment report, persona-wise breakdown, recommendations, experiment chat |
| **Claim** | Predict behavior **before** wide release; up to **87% behavioral fidelity** (step-level decision distributions, backtested) |
| **Position** | “Predictive layer” ahead of Optimizely/Amplitude (reactive tools) — MaC VC quote in TechCrunch |
| **ICP skew** | Teams with event data; finance/healthcare early (low tolerance for bad live experiments) |

---

## 2. Should Launch Rehearsal offer “everything Blok offers”?

**Yes on outcomes that help our ICP — no on cloning their GTM or unvalidated metrics.**

| Principle | Rule |
|-----------|------|
| **Wedge first** | Pre-launch / early-beta founders still win on **evidence-bound E2E rehearsal** (persona × journey, delights, compare). |
| **Cherry-pick Blok** | Only features that (a) partners ask for, (b) reuse our runner/scorecard, (c) don’t require analytics maturity on day one. |
| **Honesty** | No “87% fidelity” or “predicted lift” in marketing until **G6 calibration** (`PRODUCT.md`) or held-out backtests exist. |
| **Gate** | All `L3-PRED-*` items: **after 3 would-pay** or explicit partner pull — same as §1 in `FEATURE_SCOPE.md`. |

**We are not trying to be Optimizely + Amplitude + Blok on day one.** We are building a path so a mature customer can get Blok-like **experiment pre-qualification** without abandoning our trust story.

---

## 3. Feature matrix — adopt / have / defer / skip

| Blok capability | Us today | Roadmap | Verdict |
|-----------------|----------|---------|---------|
| AI personas exercise the product | ✅ LLM + browser personas | Deepen Init/Runner | **Have** — keep building |
| Simulate before live users | ✅ Staging rehearsal | — | **Have** — core positioning |
| Friction insights | ✅ Issues + step evidence | L3-PERF-09 deep friction | **Have** → deepen |
| Persona-wise report | ✅ Persona × journey matrix | L3-PRED-04 experiment rollup UI | **Partial** |
| Compare control vs variant | ✅ Compare run A vs B (post-run) | L3-PRED-06 variant job (pre-merge) | **Partial** → **add** |
| Experiment hypothesis + goal in UI | ❌ | L3-PRED-02 | **Add** (lightweight metadata) |
| Many runs per experiment (cohort) | ✅ `parallel_seeds` | L3-PRED-03 scale + stats | **Partial** → **add** |
| Funnel drop-off / abandon rates | ❌ | L3-JRN-05, L3-PRED-07 | **Add** |
| Predicted lift (numeric) | ❌ | L3-PRED-06 + calibration | **Add** (gated) |
| Chat about results | ✅ Run chat (`L1-NLU-02`) | L3-PRED-05 experiment-scoped chat | **Partial** |
| Recommendations summary | ✅ Narratives / digest | L3-PRED-04 | **Partial** |
| Ingest Amplitude / Mixpanel / Segment | ❌ | L3-PRED-01 | **Add** (2027 — data moat) |
| Figma prototype as target | ❌ | L3-DES-08 (shared) | **Defer** — staging URL first |
| Behavioral fidelity % published | ❌ | G6 + L3-PRED-10 | **Add** (calibration, not copied 87%) |
| Replace user research / A/B tools | They disclaim partially | `POSITIONING.md` | **Skip** — same honesty |
| Waitlist-only enterprise GTM | — | — | **Skip** — our partner-led motion |

---

## 4. Roadmap — `L3-PRED-*` (Blok-adjacent, relevant only)

Registered in `FEATURE_SCOPE.md` §4.12. Suggested build order:

### Wave 1 — Reuses shipped engine (2027 Q1, after PMF signal)

| ID | Feature | Why |
|----|---------|-----|
| **L3-PRED-02** | Experiment spec on config/run: `hypothesis`, `user_goal`, `variant_label` | TechCrunch: teams submit hypothesis + goal with each test |
| **L3-PRED-06** | Variant rehearsal job: run config **A** and **B** on same URL; compare readiness + issue delta | Blok control/variant; extends compare |
| **L3-PRED-04** | Experiment report page: overall + per-persona rollup (pass/fail, top friction, delights) | Persona-wise report |
| **L3-PRED-05** | Chat scoped to experiment (both runs + diff context) | Extends `L1-NLU-02` |

### Wave 2 — Quantitative story (2027 H1, ties G6)

| ID | Feature | Why |
|----|---------|-----|
| **L3-PRED-07** | Step-level continue / hesitate / abandon counts per persona | Fidelity methodology: distributions, not single outcome |
| **L3-JRN-05** | Funnel drop-off across journeys | Blok “drop-off” headline |
| **L3-PRED-03** | Cohort mode: N parallel seeds with aggregate confidence band | TechCrunch: “simulation many times” |
| **L3-PRED-09** | Directional “lift” card: readiness Δ, issues resolved/new (label `hypothesis` until G6) | Blok “lift” without false precision |

### Wave 3 — Data-informed personas (2027 H2)

| ID | Feature | Why |
|----|---------|-----|
| **L3-PRED-01** | Import event export (Segment/Mixpanel/Amplitude JSON) → persona priors | TechCrunch onboarding flow |
| **L3-PRED-08** | Optional Figma URL / prototype link on experiment (browse via staging proxy) | Nice-to-have; not before staging URL path solid |
| **L3-PRED-10** | Calibration dashboard: sim vs beta issue overlap %; optional step-fidelity if backtest data | Answer “how close to real users?” without copying 87% |

### Explicitly out of scope (unless partner-funded)

- Full analytics warehouse / CDP replacement  
- Autonomous “ship this variant” recommendations without human review  
- Competing on MaC’s “before a single line of code” — we stay **before production traffic**, typically **staging + YAML**

---

## 5. Messaging when Blok comes up

| They say | We say |
|----------|--------|
| Predict before you ship | **Rehearse on staging with evidence** — every finding has `run_id` + step replay |
| 87% fidelity | We publish **calibration against your beta** when ready (G6), not a borrowed benchmark |
| Upload Segment data | On roadmap (L3-PRED-01); today you define personas in YAML + we dogfood on your URL |
| Figma experiments | Staging-first; Figma later (L3-DES-08) |
| Delights + launch readiness | **Our differentiator** — Blok is experiment-centric; we are **launch-readiness + positives** |

---

## 6. What to build **now** (unchanged)

Continue **§0 Active execution plan** in `FEATURE_SCOPE.md`:

- Design partner outreach + concierge demos  
- Author & rehearse UX (Init → Config → Runner → Runs/Compare)  
- Trust: evidence, annotations, live jobs, test groups for multi-product demos  

Do **not** start L3-PRED until Wave 1 gate clears unless a design partner blocks a deal on a specific ID (document in `CHANGES.md`).

---

## 7. Related docs

| Doc | Role |
|-----|------|
| `FEATURE_SCOPE.md` §4.12 | ID registry |
| `PRODUCT.md` G6, Phase 3 | Calibration milestone |
| `POSITIONING.md` | What we do / do not claim |
| `enterprise-work-env-simulator/competitors-report.md` | Veris, VEI, Demostack (different axis) |
