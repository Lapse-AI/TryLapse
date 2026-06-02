# Journey strategy — Launch Rehearsal

**Authority:** `CEO_DECISIONS.md` (trust over coverage) · **UI:** `UI_PRODUCT_LINES.md`  
**Last updated:** 2026-05-31

---

## Principle

Sell **trust**, not **coverage**. Partners want named launch paths with evidence — not a spider that clicks every button and floods the scorecard.

---

## Three layers (how the product works)

| Layer | Mechanism | Role in readiness |
|-------|-----------|-------------------|
| **1. Scripted journeys** | 5+ journeys in `rehearse.yaml` (DSL steps) | **Primary gate** — persona×journey matrix, blockers, delights |
| **2. Crawl (BFS)** | Same-origin discovery, sitemap, workflow types | **Discovery** — orphans, auth walls, suggested paths; optional `supplement_journeys` adds light auto-navigate journeys |
| **3. Depth inside journeys** | `explore`, recorder, viewports, parallel seeds, **prompt → draft** | **Richer signal** on paths you already care about |

**Explicitly deferred (Phase 2+ / audit mode):** sitewide “every button” exploration, combinatorial path enumeration.

---

## Customer expectations

| They expect | We deliver |
|-------------|------------|
| “Did our **critical flows** pass?” | 5 configured journeys + matrix |
| “What did you **see** on staging?” | Crawl sitemap + screenshots per step |
| “Can we **define** what to test?” | Init wizard, YAML editor, recorder, journey library, prompt draft |
| “Every possible path?” | Honest no for Phase 1 — crawl + suggest, not full combinatorial |

---

## Personas (unchanged contract)

- **3 personas required** in YAML (evaluator / operator / admin archetypes).
- **Browser default:** first persona runs journeys; optional `execute_all_personas_in_browser`.
- **Matrix columns:** technical steps from browser; other personas = evaluation lens (PersonaAgent + heuristics + optional LLM).

### Planned — Init persona studio (L2-UI-68–71)

| Capability | Behavior |
|------------|----------|
| **Core three** | Always scaffolded: first-time evaluator, daily operator, admin/buyer (today’s `init_config.py` defaults). |
| **Describe a user** | Free-text need (e.g. “SOC2 reviewer who only cares about audit logs”) → LLM drafts `id`, `name`, `role`, `goals[]` for YAML. |
| **Product suggestions** | From target URL + product name (+ optional crawl hints): 2–4 *suggested* personas user can one-click add. |
| **Custom** | User edits draft or writes persona by hand; validate still enforces ≥3 personas for full matrix runs. |
| **Persona off** | Optional run mode: journeys execute with **no persona lens** (technical pass/fail only) or subset of personas — for smoke vs full rehearsal. |

**Init step order (target):** Target → Auth → **Personas (new panel)** → Journeys (draft/recorder) → Crawl/viewport → Review & generate YAML.

---

## UI placement (authoring vs monitoring)

| Nav group | Routes | Purpose |
|-----------|--------|---------|
| **Author & rehearse** | `/init`, `/library`, `/config`, `/runner` | Define target, draft journeys, edit YAML, trigger runs |
| **Monitor** | `/`, `/runs`, `/compare`, `/trends`, … | Read scorecards, diff runs, track drift |
| **Map** | `/sitemap`, `/workflows` | Crawl output → add journeys, preview pages |

**Flow:** Init or Config → Runner → Runs / Compare.

---

## Roadmap hooks (L2)

| ID | Feature | Status |
|----|---------|--------|
| L2-UI-18 | Compare visual step diff + focus box | ✅ Accordion per step — `COMPARE_SCREENSHOTS.md` |
| L2-UI-41–43 | Live YAML validate + save on `/config` | ✅ `ConfigYamlEditor` + API |
| L2-UI-27–32 | Sitemap preview + add journey to config | ✅ Preview + append navigate journey |
| L2-UI-13 | Annotations pin + manual finding | ✅ Pin on issues + manual finding panel |
| — | `POST /api/journeys/draft` prompt → YAML fragment | ✅ Init wizard **Describe a journey** panel |
| — | Persona studio L2-UI-68–70 | ✅ Init **Personas** panel + API |
| — | Journey `priority: critical \| smoke \| exploratory` | Documented; optional YAML field Phase 2 |

---

## Related

`FEATURE_SCOPE.md` · `DOC_CATALOG_STATUS.md` · `COMPARE_SCREENSHOTS.md` · `BROWSER_CAPABILITY_PARITY.md` · `DESIGN_PARTNER_CHECKLIST.md`
