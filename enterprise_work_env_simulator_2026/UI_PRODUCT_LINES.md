# UI product lines — Dev & Vision (same newest UI)

**Locked:** 2026-05-31 (revised)  
**Policy:** **Dev and Vision both run the full Vision-level (newest) dashboard.** There is no reduced or older dev UI.

---

## One UI tier, two npm scripts

| Script | Mode label | URL | UI |
|--------|------------|-----|-----|
| `npm run dev` | **Dev** | http://127.0.0.1:8081/ | **Newest / Vision-level** — full dashboard |
| `npm run dev:vision` | **Vision** | same port | **Same newest UI** — for reference builds |

**Identical:** every route, panel, env selector, trends recurrence, YAML editor, integrations, etc.

**Only difference:** the small badge (`Dev` vs `Vision`) — useful for screenshots or knowing which script you started.

---

## Data source (both modes)

| API state | What you see |
|-----------|--------------|
| `./rehearse serve` **running** | Live runs, bundles, KPIs, real screenshots |
| API **offline** | Acme mock fallback — **both** dev and Vision (so UI never looks empty while coding) |

**Partner demos:** always start the API and use real run IDs (`argyle-20260531-000517`). Ignore mock when API is live.

---

## Commands

```bash
./rehearse serve -o launch-rehearsal/artifacts

cd Frontend_V1 && npm run dev          # daily dev → :8081
cd Frontend_V1 && npm run dev:vision     # same UI, Vision badge

cd Frontend_Deliverable && npm run dev # alias → Frontend_V1 dev
```

---

## Adding new UI

**All new UI work lands in `Frontend_V1/src/`** — it appears in **both** dev and Vision automatically. Do not mode-gate chrome. Use `FEATURE_SCOPE.md` L1/L2/L3 only for **backend wiring** and honest partner promises, not for hiding pages.

Optional: mark future-only sections with `<VisionOnly section="…">` for documentation — it does **not** hide UI.

**Dev rehearsal personas:** top-bar **Test groups** (mock sign-in) switches target URL + YAML config presets per website persona — see `AUTH_TEST_GROUPS.md`.

---

## Backend vs UI honesty (partner calls)

The newest UI still includes some **mock / Phase 2 shells** (recurrence table, cron UI, OAuth Connect, etc.) visible in **both** modes. Do not over-promise — see `FEATURE_SCOPE.md` §1 and §3 L2 catalog.

---

## Code map

| File | Role |
|------|------|
| `src/lib/ui-mode.ts` | `getUiMode()`, `uiTierLabel()` → always "Vision UI" tier |
| `src/lib/api/hooks.ts` | Mock fallback when API down (both modes) |
| `.env.dev` / `.env.vision` | Mode badge only |

---

## Sidebar groups (authoring vs monitoring)

| Group | Routes | When to use |
|-------|--------|-------------|
| **Author & rehearse** | `/init`, `/library`, `/config`, `/runner` | Target URL, prompt → YAML draft, recorder, edit & save config, trigger run |
| **Monitor** | `/`, `/runs`, `/compare`, `/trends`, … | Scorecards, compare runs (incl. visual step diff), drift |
| **Map** | `/sitemap`, `/workflows` | Crawl output → preview page → append smoke journey |

See `JOURNEY_STRATEGY.md`, `COMPARE_SCREENSHOTS.md`, and `DOC_CATALOG_STATUS.md` for journey philosophy, compare steps, and doc consistency checklist.

---

## Related

`FEATURE_SCOPE.md` · `JOURNEY_STRATEGY.md` · `COMPARE_SCREENSHOTS.md` · `DESIGN_PARTNER_CHECKLIST.md` · `live-2026-05-31.md`
