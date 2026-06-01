# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
