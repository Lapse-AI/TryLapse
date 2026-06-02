# Doc & catalog status — Launch Rehearsal

**Last updated:** 2026-06-02  
**Purpose:** Single checklist for doc/catalog consistency. Update when L2 items ship or UI behavior changes.

---

## Canonical docs

| Doc | Role |
|-----|------|
| `FEATURE_SCOPE.md` | L1/L2/L3 inventory + sprint order |
| `JOURNEY_STRATEGY.md` | Journey philosophy + UI placement |
| `UI_PRODUCT_LINES.md` | Dev/Vision policy + sidebar groups |
| `COMPARE_SCREENSHOTS.md` | How to see visual step diff |
| `INIT_WIZARD.md` | What `/init` does step-by-step |
| `CHANGES.md` | Shipped changelog |
| `DESIGN_PARTNER_CHECKLIST.md` | Partner demo readiness |
| `COMPETITIVE_BLOK.md` | Blok-adjacent features: adopt / defer / skip + `L3-PRED-*` waves |

---

## Recently aligned (2026-05-31)

| Item | Status | Where documented |
|------|--------|------------------|
| Compare visual step diff + focus box | ✅ | `COMPARE_SCREENSHOTS.md`, L2-UI-18 |
| Compare accordion (one row per changed step) | ✅ | `COMPARE_SCREENSHOTS.md`, `CHANGES.md` |
| Command center top-right Compare link + `#visual-diff` | ✅ | `UI_PRODUCT_LINES.md`, `CHANGES.md` |
| Config YAML live editor (validate/save) | ✅ | L2-UI-41–43, `JOURNEY_STRATEGY.md` |
| Init prompt → journey draft | ✅ | `JOURNEY_STRATEGY.md`, `CHANGES.md` |
| Init generate & write YAML | ✅ | L2-UI-63, `POST /api/configs` |
| Init PII checkbox persisted | ✅ | L2-UI-62 |
| Sitemap preview + add journey | ✅ | L2-UI-27–32 |
| Workflows add to config | ✅ | L2-UI-31 |
| Annotations pin + manual finding | ✅ | L2-UI-13 |
| Author & rehearse sidebar group | ✅ | `UI_PRODUCT_LINES.md`, `JOURNEY_STRATEGY.md` |
| Dimension rollup → findings filter | ✅ | `analysis_export.py`, `dimension-match.ts`, `CHANGES.md` §Fixed |
| Persona studio (Init) | ✅ | `INIT_WIZARD.md`, L2-UI-68–70 |
| Experiment spec (partial) | ✅ | L3-PRED-02, Config + run banner |

---

## Known remaining inconsistencies (watch list)

| Item | Issue | Action |
|------|-------|--------|
| L2-UI-65 job config picker | Was “default only” | ✅ Runner config selector + `selected-config.ts` |
| L2-UI-28 sitemap diff view | Links to compare; no dedicated graph diff | Keep as partial |
| L2-UI-05 env selector | Cosmetic; does not filter runs | Document as display-only |
| Acme mock fallback | Both dev/Vision when API offline | `L2-MCK-01` — retire on partner demos |
| Test auth / user groups | Temporary dev feature | ✅ `AUTH_TEST_GROUPS.md`, top-bar **Test groups** |
| Experiment spec (L3-PRED-02 partial) | Config panel + run banner | ✅ `experiment` in YAML; `POST /api/configs/experiment` |
| Phase 1 tail observability | Run detail panel | ✅ duration, outcome, cost, named errors |
| Stale `analysis.json` after export fix | Old bundles keep wrong dimension tags | Delete `artifacts/analysis/{run-id}.json` and reload run detail |

---

## Terminology (locked)

| Use | Avoid |
|-----|-------|
| **Config (YAML)** | “Workspace” for YAML editor |
| **Author & rehearse** | Scattering init/recorder under Monitor |
| **Compare runs** | “Diff page” in user-facing copy |
| **Visual step diff** | “Screenshot diff” without step context |
| **Run A (baseline) / Run B (current)** | Unlabeled A/B only |

---

## Verification assumptions (compare)

1. `./rehearse serve` on `:8765`, UI on `:8081`
2. Two runs from the **same** config (step IDs align)
3. Interactive steps (`click`, `fill`, …) for focus boxes
4. Runs must differ on at least one step for accordion rows to appear
5. Enterprise or click-heavy configs show visual diff more reliably than navigate-only `lr-self`

---

## Related

`FEATURE_SCOPE.md` · `JOURNEY_STRATEGY.md` · `UI_PRODUCT_LINES.md` · `COMPARE_SCREENSHOTS.md`
