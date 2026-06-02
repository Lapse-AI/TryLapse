# Init wizard — what it does

**Route:** `/init` · **API:** `GET /api/init`, `POST /api/configs` · **Backend:** `init_config.py`, `dashboard/store.py`

**Last updated:** 2026-06-02

---

## Purpose

The Init wizard is the **fastest path from “we have a staging URL” to a runnable `rehearse.yaml`**. It mirrors `rehearse init` on the CLI: scaffold config, write to `launch-rehearsal/artifacts/configs/{slug}.yaml`, then open **Runner** to rehearse.

It does **not** run a full rehearsal by itself — it **authors** config.

---

## What happens end-to-end

```text
You enter target URL (+ options)
        ↓
Optional: Preflight HEAD (SSRF-safe reachability check)
        ↓
POST /api/configs → build_config() or build_self_dashboard_config()
        ↓
YAML written under artifacts/configs/
        ↓
Selected config id stored (localStorage) → Runner / Config / Sitemap use same file
```

---

## UI sections (current)

| Section | What it does |
|---------|----------------|
| **Test group preset** | If signed in via test groups: fills URL, auth flags, product from top-bar group. |
| **Dogfood this dashboard** | One-click `http://127.0.0.1:8081` + **Generate self-test YAML** (`lr-self` journeys for /, /runs, /compare, /init, /runner, /trends). |
| **Target & options** | URL, product name, preflight, self-test, localhost allowlist, auth block, PII toggle, execute-all-personas-in-browser, crawl excludes, viewports. |
| **Describe a journey** | `JourneyDraftPanel` — natural language → `POST /api/journeys/draft` → YAML fragment to paste into config. |
| **Personas (L2-UI-68–70)** | `PersonaStudioPanel` — core 3 toggles, product suggestions, AI draft → staged extras on generate; `persona_lens` for technical-only |
| **Journey recorder** | JSON steps → `POST /api/recordings/compile` → YAML journey fragment. |
| **Wizard steps (read-only list)** | Mirrors API `steps[]` — conceptual checklist, not a multi-page wizard yet. |
| **Generate & write YAML** | `POST /api/configs` — main deliverable. |

---

## What gets generated (default product config)

From `build_config()`:

| Block | Content |
|-------|---------|
| **run** | `target_url`, `run_id_prefix` (from host slug), `product_name`, `viewports` |
| **crawl** | Enabled, depth 2, max 30 pages, `supplement_journeys: true`, optional exclude prefixes |
| **personas** | **3 fixed archetypes:** first-time evaluator, daily operator, admin/buyer (ids `p1-evaluator`, `p2-operator`, `p3-admin`) |
| **journeys** | **5 starter journeys:** land, core workflow, secondary, search/discovery, admin/settings (mostly navigate + wait — you edit for real flows) |
| **budgets** | 12 steps/journey, 20 min run cap, 45s step timeout |
| **auth** | Optional block if “Include auth” — login path + `REHEARSE_EMAIL` / `REHEARSE_PASSWORD` env vars |

**Self-test variant** (`build_self_dashboard_config`): same base + `allow_localhost`, dashboard-specific journeys, no auth, higher step budget.

---

## Options explained

| Checkbox / field | Effect |
|------------------|--------|
| **Preflight HEAD** | Calls `/api/preflight` — checks URL reachable; blocks private IPs unless localhost allowed. |
| **Self-test config** | Writes dogfood YAML for this UI at `:8081`. |
| **Allow localhost** | SSRF guard allows 127.0.0.1 / localhost targets. |
| **Include auth** | Adds `auth:` + login-oriented first journey steps. |
| **PII redaction** | Stored on workspace metadata (Phase 2 enforcement). |
| **Execute all personas in browser** | Sets `execute_all_personas_in_browser: true` — slower, each persona runs browser steps. |
| **Crawl exclude prefixes** | Skips paths during BFS (e.g. `/api/`). |
| **Viewports** | desktop / tablet / mobile replay profiles. |

---

## After Init

1. **Config (YAML)** — validate/save, experiment spec, edit journeys.  
2. **Runner** — queue `rehearse run` against selected config.  
3. **Runs / Compare** — read scorecard, diff releases.

---

## Planned (not built yet)

See `JOURNEY_STRATEGY.md` **Init persona studio** (L2-UI-68–71):

- Describe user need → AI persona draft  
- Suggested personas from product context  
- Add/remove personas; optional “run without persona lens”

---

## Related

`JOURNEY_STRATEGY.md` · `FEATURE_SCOPE.md` L2-UI-63 · `AUTH_TEST_GROUPS.md` · `COMPETITIVE_BLOK.md` (experiment spec on Config, not Init)
