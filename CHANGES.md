# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (June 3, 2026 — Claude Code session)

- **L3-PRED-09 — Directional lift card** (`LiftCard` component): before/after readiness bars, Δ chip, new/resolved issue counts. Wired into experiment page. "Directional until G6 calibration" honesty label
- **L3-PRED-03 — Cohort rehearsal**: `enqueue_cohort_run()` runs same config N seeds serially, aggregates readiness (mean/min/max/spread), confidence band (high ≤5 pt spread / medium ≤15 / low), recurring issues at ≥50% of seeds. `POST /api/jobs/cohort`, `GET /api/cohort/{id}`. `CohortRehearsalPanel` in Runner. `/cohort/:jobId` report page with live seed progress bar, band visualization, recurring issues table
- **L3-PRED-07 — Step behavior signals**: `_step_behavior()` in `analysis_export.py` — abandon (fail/error), hesitate (partial or >5s interactive), continue (pass). Added to every step in bundle. Abandon/hesitate chips in Steps tab; counts in Run observability panel
- **L3-PRED-04/05 — Experiment report + chat** (PR #21): `GET /api/experiment/{id}/report` (per-persona A-vs-B grade table, readiness delta, hypothesis verdict); `GET/POST /api/experiment/{id}/chat` (LLM context = both bundles + diff + hypothesis; template fallback)
- **L2-UI-71 — Config persona editor** (PR #21): live CRUD panel on `/config`; `GET /api/configs/{id}/personas` + `POST /api/configs/personas/replace`
- **L3-PRED-06 — Variant A/B rehearsal**: `enqueue_variant_run()`, `POST /api/jobs/variant`, `GET /api/variant/{id}`, `/experiment/:jobId` page with phase bar + per-run readiness
- **Deploy — Railway/Coolify**: `Dockerfile` (dashboard-only, no Playwright), `docker-entrypoint.sh` (seeds demo artifacts on first boot), `docker-compose.yml`. Demo artifacts (enterprise×2, argyle) tracked in git for deployed seed
- **Demo polish** (PR #21): screenshots in Evidence dialog and gallery now go through `artifactUrl()` (were 404ing); Runner config dropdown filtered to canonical named configs

### Fixed (June 3, 2026)

- Screenshot Evidence dialog: `issue.screenshotPath` was used directly as `<img src>` instead of via `artifactUrl()` — all evidence screenshots showed broken image
- Runner config dropdown: 39 entries (mostly auto-generated timestamps) reduced to canonical configs + 3 most-recent snapshots
- CI lint failures on `feat/nlu-browser-parity` and post-session direct-push commits — Prettier formatting applied via `eslint --fix`

### Added (prior — Cursor session, May 31 – June 2, 2026)

- Docs: `COMPETITIVE_BLOK.md` — Blok/TechCrunch feature matrix; `L3-PRED-01`–`10` in `FEATURE_SCOPE.md` §4.12 (gated post–3 would-pay)
- **L3-PRED-02 (partial):** Experiment spec — `experiment:` in YAML, `POST /api/configs/experiment`, Config panel + run banner
- **L2-UI-68–70:** Persona studio — `POST /api/personas/draft|suggest`, Init panel, `persona_lens` / `enabled`, staged extras on generate
- Docs: `DESIGN_PARTNER_OUTREACH.md` (§0 Track A templates); `INIT_WIZARD.md` (Init flow reference)
- Delight `confidence` in analysis bundle + UI chips; run observability panel (duration, outcome, cost, named errors)
- Dimension filter helper: `Frontend_V1/src/lib/dimension-match.ts` (`relatedDimensions` cross-tag support)
- Tests: `test_experiment_dsl.py`, `test_errors_budgets.py`, `test_persona_draft.py`, dimension tagging in `test_analysis_export.py`

### Fixed

- **Dimension rollup filters:** findings were all exported as `Functionality`; UI/UX and Accessibility tabs showed “0 findings” despite low rubric scores. Export now tags findings by dimension, adds `relatedDimensions` for cross-cutting issues (e.g. unlabeled buttons → UI/UX + Accessibility), enriches unlabeled totals across steps, and adds Phase 2 rollup findings when scores flag gaps. **Existing runs:** delete `artifacts/analysis/{run-id}.json` and reload, or re-run `build_run_bundle` / backfill.

- Config YAML API: `GET /api/configs/{id}`, validate/save, append navigate journey from sitemap path
- Init wizard: prompt → journey draft (`POST /api/journeys/draft`) before recorder block
- Site map: page preview screenshot + “Add navigate journey” to selected config
- Annotations: **Pin** on automated issues; **manual finding** panel on run Annotations tab
- Docs: `DOC_CATALOG_STATUS.md` audit checklist; aligned `FEATURE_SCOPE` / compare docs
- UX handoff: shared config selection (`selected-config.ts`) across Config, Runner, Sitemap, Workflows; Runner readiness panel + config picker; Init/Config CTAs toward Runner
- Temporary test auth: product dropdown (no login required) + optional sign-in; runs/compare scoped per product — `AUTH_TEST_GROUPS.md`
- Compare visual step diff: side-by-side screenshots with focus box + label on click/fill/select steps
- Compare UI: collapsible accordion per changed step (expand for side-by-side); command-center top-right **Compare runs** link with `#visual-diff` anchor
- Workflows: **Add to config** on suggested journeys (append navigate journey via `/api/configs/append-journey`)
- Run detail observability: Web Vitals per step, console warnings, network-log / web-vitals exports, agents-run summary
- Compare diff: sitemap new/removed pages panel (L2-UI-19)
- Dimension rollup grid component on command center and run detail (clickable dimension filters with breakdown banner)
- NLU narrative disk cache (`artifacts/narratives/`) for digest, trends, and compare — LLM runs once per stable run set; `?refresh=true` to regenerate; UI 30m stale time without refetch on focus
- **NLU-1:** Run narratives (template + optional LLM), Run summary + chat on run Overview, `POST /api/runs/{runId}/chat`
- **NLU-2:** Compare narratives on `GET /api/diff` and Compare page “What changed” panel
- **NLU-3:** Trends narrative on `GET /api/trends` and Trends insight panel
- **NLU-4:** Persistent run chat in `artifacts/chats/`; reload thread on run Overview
- **NLU-5:** Command-center digest on `GET /api/digest` and home panel
- **Phase C:** DSL `explore` + `dismiss`; multi-persona browser (`execute_all_personas_in_browser`); Init journey recorder (`POST /api/recordings/compile`)
- **NLU-6:** Richer explore evidence — per-round `exploreLog`, NL `exploreSummary`, JSON artifact, run detail timeline rows
- **Browser parity Phase A:** viewports (desktop/tablet/mobile), DSL `hover`/`scroll`/`select`, intent resolution, compact ARIA artifacts, Init viewport/exclude paths
- **Browser parity Phase B:** Performance agent (Web Vitals), `network-log.json`, console warnings + `press` action
- Job queue: file lock on `jobs.json`, one rehearsal at a time, dedupe, stale-job cleanup on serve restart; `.env` loaded for background jobs
- Runner UI: LLM enrichment checkbox for job triggers
- **Test groups (dev):** mock sign-in + website persona groups in top bar; presets target URL and YAML config (`AUTH_TEST_GROUPS.md`)
- Phase 1 tail: named step error types (`errorType` on steps/issues), run `costEstimate` in analysis bundle, observability fields (`pagesCrawled`, `agentsRun`) in bundle summary
- Sprint 3 UI: init wizard writes YAML via `POST /api/configs`; Linear backlog export stub; live/offline/running command-center chip
- Sprint 3 backend: `save_config()` + `POST /api/configs` for self-serve init
- Sprint 2 UI: live command-center KPIs from `/api/trends`, workflow map from run bundle, delights from latest run, issue annotation agree/disagree/false-positive actions
- Sprint 1 UI: export artifact downloads, compare run selectors wired to `/api/diff`, evidence copy-repro and step timeline deep links
- GitHub Flow repo foundation: CI, PR checks, release workflow, issue/PR templates
- Python unit tests for DSL, preflight SSRF guards, and flaky heuristics
- `CONTRIBUTING.md`, `CODEOWNERS`, Dependabot config

### Changed

- Self-test journey `j5` no longer clicks “Run self-test” (prevents job-queue cascade)
- LLM JSON calls: brace-extraction fallback when model returns truncated JSON (narratives + compare)
- When dashboard API is live, run summaries and trends use real artifacts only (no Acme mock merge)
- Workflows and recommendations pages use live run bundle data instead of mock Acme fixtures
- `FEATURE_SCOPE.md` reorganized for SELECTIVE EXPANSION execution plan

## [0.1.0] - 2026-05-31

### Added

- Initial monorepo: `launch-rehearsal` CLI, `Frontend_V1` dashboard, product specs
- Multi-agent pipeline: crawl, journeys, personas, LLM, scorecard
- Parallel seeds + FLAKY detection; `open_link` profile fallback
- Dashboard API + artifact serving; Argyle dogfood configs

[Unreleased]: https://github.com/Lapse-AI/TryLapse/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Lapse-AI/TryLapse/releases/tag/v0.1.0
