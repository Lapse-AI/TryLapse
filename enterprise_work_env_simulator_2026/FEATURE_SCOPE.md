# Launch Rehearsal — Feature Scope

**Last updated:** 2026-06-02  
**Planning mode:** **SELECTIVE EXPANSION** (CEO review)  
**Authority:** `CEO_DECISIONS.md` · `MONITORING_PLATFORM_SPEC.md` · `DESIGN_PARTNER_CHECKLIST.md`

---

## How to read this document

| Section | Purpose |
|---------|---------|
| [§0 Active plan](#0-active-execution-plan-selective-expansion) | What to build **now** and in what order |
| [§1 Deferred later](#1-deferred-later--do-not-block-current-work) | Explicit **not now** bucket (CEO NO + post-PMF) |
| [§2 L1 Shipped](#2-l1--backend-shipped) | Full inventory of working backend/API |
| [§3 L2 UI backlog](#3-l2--ui-present-backend-missing-or-partial) | UI gaps, **prioritized** then catalogued by area |
| [§4 L3 Future](#4-l3--not-present-future--spec) | Spec’d future work (mostly later) |
| [§5 Indexes](#5-indexes--cross-refs) | Concern map, demo readiness, file paths |
| [UI product lines](UI_PRODUCT_LINES.md) | **Vision vs Deliverable** — locked dual-UI policy |

### Level legend

| Level | Definition |
|-------|------------|
| **L1** | Shipped in **backend** (`launch-rehearsal/`) — CLI, agents, heuristics, artifacts, or dashboard API. Includes static/template API routes where the server implements the handler but not external delivery (e.g. integration catalog). |
| **L2** | Present in **Frontend_V1** (or built-in HTML dashboard) but **not fully backed** — mock data, placeholders, cosmetic controls, or partial wiring. |
| **L3** | **Not present** as functional capability — spec’d, discussed, or industry-expected; future work. |

**Principles (always L1):** Observe-only · evidence-bound (`run_id`, `step_id`, artifacts) · persona × journey matrix · enterprise-agnostic config · **no auto-fix / no deploy**.

### North star (unchanged)

> **“Would you run this before every launch?”**  
> Measured by **3 would-pay** design partners (Sep 30, 2026), not feature count.

---

## 0. Active execution plan (SELECTIVE EXPANSION)

**CEO 2026-05-31:** Ship PR #13; parallel Sprint 3 + outreach Track A.

**Baseline scope: HOLD.** Phase 1 engine is largely shipped. **Cherry-pick** only L2 items that unlock partner trust or post-call async.

### Parallel tracks (do not serialize outreach behind UI)

```text
Track A (critical path)     Track B (engineering)
─────────────────────       ─────────────────────────
Design partner outreach  →  L2 Sprint 1 (P0 async)
Demo dry-run             →  L2 Sprint 2 (P1 credibility)
Partner runs + capture     →  Phase 1 tail (budgets, cost)
```

### Engineering sprint order

| Sprint | When | L2 / eng IDs | Outcome |
|--------|------|--------------|---------|
| **Sprint 1** | Now | L2-UI-08–11, L2-UI-17 | Post-call async: export, compare, repro |
| **Sprint 2** | After 1+ partner call | L2-UI-12, L2-UI-29–30, L2-UI-52, L2-UI-01–04 | ✅ Live data on home/workflows; annotations |
| **Sprint 3** | Before self-serve marketing | L2-UI-63, L2-MCK-01, L2-UI-50 | ✅ Init writes YAML; retire Acme; Linear export |
| **Phase 1 tail** | Parallel / low urgency | Run budgets + named errors; cost estimate in bundle | CEO Phase 1 #11–13 |
| **Init persona studio** | After experiment spec · before §0 outreach | L2-UI-68–71 | AI + suggested personas; optional persona-off runs |

### Concierge vs self-serve

| Mode | Status | Blocker |
|------|--------|---------|
| **Concierge demo** (you run CLI + walk UI) | ✅ Ready | None — start outreach |
| **Self-serve** (partner operates UI alone) | ✅ | Sprint 1–3 shipped (PRs #13–#14); G12 badge only |
| **Marketing / PLG** | ❌ Later | §1 Deferred + 3 verbal would-pay |

**Demo runs (API live):** `argyle-20260531-000517`, `enterprise-20260530-234231` — not mock `run_8s7d2`.

### UI product lines — see [UI_PRODUCT_LINES.md](UI_PRODUCT_LINES.md)

**Dev and Vision = same newest UI** at `:8081`. No reduced dev chrome.

| Script | Label |
|--------|-------|
| `npm run dev` | Dev |
| `npm run dev:vision` | Vision (identical UI) |

Mock fallback when API down in **both**. Partner demos: API live + real run IDs.

---

## 1. Deferred later — do not block current work

> **CEO rule:** These are real roadmap items but **later priority**. Do not promise on design partner calls. Do not schedule before **3 would-pay** unless a partner explicitly pulls one forward.

### 1.1 Explicit CEO “NO” until gate cleared

| Theme | Target phase / gate | Related IDs (see §4) |
|-------|---------------------|----------------------|
| **PLG signup / billing / usage metering** | After 3 would-pay | L3-OPS-06 |
| **Public pricing page** | After 3 verbal pay commits | `CEO_DECISIONS.md` §3 |
| **GitHub Action CI / PR checks** | Aug 2026 | L3-INT-05, L3-INT-12 |
| **Product B — Deal Rehearsal** | Mar 31, 2027 PMF gate | L3-PRD-01 |
| **Journey marketplace** | Post-PMF | (future catalog) |
| **Open-source release** | Decide Aug 1, 2026 (default closed) | `CEO_DECISIONS.md` |
| **100× / return-after-gap veteran modes** | 2027 | L3-JRN-02 |
| **Slack / Jira / CRM twins** | Dec 2026 | L3-INT-01–07, L2-UI-50–51, L2-UI-59–60 |

### 1.2 Platform & integrations (later)

| Theme | Notes | Related IDs |
|-------|-------|-------------|
| **Deep security audit** (OWASP, pen test, SOC2 story) | L1 has SSRF + auth heuristics only | L3-SEC-01–11 |
| **Slack / email / webhook alert delivery** | Catalog + mock UI today | L3-INT-01–03, L2-UI-56–58 |
| **Scheduled cron runs** | Mock `scheduledRuns` in UI | L3-INT-11, L2-UI-23, L2-MCK-08 |
| **SSO dashboard (OIDC/SAML)** | Catalog entry only | L3-SEC-12 |
| **Dashboard RBAC** | Admin / viewer / run-only | L3-SEC-13 |
| **Multi-workspace / portfolio** | UI chrome only | L2-UI-06, L2-UI-49, L3-OPS-05 |
| **OAuth flows** (GitHub, Slack, SSO) | Inert Connect buttons | L2-UI-60, L3-SEC-12 |

### 1.3 Deep quality agents (optional post-PMF)

| Theme | Related IDs |
|-------|-------------|
| Full WCAG / axe-core | L3-A11Y-01–07 |
| Web Vitals / Lighthouse / HAR | L3-PERF-01–08 |
| Functional compliance agent | L3-SEC-09 (L1 placeholder today) |
| Functional performance agent | L3-PERF-03 (L1 placeholder today) |
| Visual regression / Figma compare | L3-DES-08–09 |
| Every-button sitewide crawl | L3-DES-11 |
| Competitor benchmark | L3-CMP-01–04, L2-UI-53 |
| **Predictive rehearsal (Blok-adjacent)** | After 3 would-pay · **G6** for fidelity claims | `L3-PRED-01`–`10` · `COMPETITIVE_BLOK.md` |

### 1.4 Promoted to L1 (remove from “blocked” mental model)

| Was spec’d as L3 / stale L2 | Now L1 |
|-----------------------------|--------|
| Parallel journey seeds + FLAKY flag | L1-BRW-18–20, L1-HEU-23, L1-DSL-14–16 |
| Repeat micro-loop | L1-DSL-16 (`repeat_micro_loop` in budgets) |
| Profile link navigation fallback | L1-BRW-18 (`open_link`) |

---

## 2. L1 — Backend (shipped)

### L1.1 CLI & lifecycle

| ID | Feature | Notes |
|----|---------|-------|
| L1-CLI-01 | `rehearse run` — full pipeline | Crawl (optional) → journeys → multi-agent → scorecard → analysis bundle |
| L1-CLI-02 | `rehearse run --dry-run` | DSL validation + skipped step evidence, no browser |
| L1-CLI-03 | `rehearse run --no-crawl` | Skip crawl phase |
| L1-CLI-04 | `rehearse run --llm` | Enable LLM persona agents |
| L1-CLI-05 | `rehearse crawl` | Crawl-only + sitemap + workflow detection |
| L1-CLI-06 | `rehearse scorecard` | Regenerate markdown from saved evidence |
| L1-CLI-07 | `rehearse diff <run_a> <run_b>` | CLI run comparison |
| L1-CLI-08 | `rehearse serve` | Local dashboard HTTP server (:8765, port fallback) |
| L1-CLI-09 | `rehearse backfill` | Rebuild missing `analysis/{run_id}.json` |
| L1-CLI-10 | `rehearse init <url>` | Scaffold 3-persona / 5-journey YAML (`init_config.py`) |
| L1-CLI-11 | Global `.env` loading | Walks up dirs; NVIDIA/OpenAI/DeepSeek keys |
| L1-CLI-12 | JSON stdout summary on run | run_id, readiness, paths |

### L1.2 Config DSL & validation

| ID | Feature | Notes |
|----|---------|-------|
| L1-DSL-01 | Required 3 personas, 5 journeys | `dsl.py` validation |
| L1-DSL-02 | Persona fields: id, name, role, goals[] | |
| L1-DSL-03 | Journey steps: navigate, click, fill, wait, assert_url_contains, **open_link** | |
| L1-DSL-04 | Step locators: CSS selector + intent (role/label/text) | |
| L1-DSL-05 | `${ENV_VAR}` interpolation in step values | Secrets via env only |
| L1-DSL-06 | `{target_url}` templating in URLs | |
| L1-DSL-07 | Auth block: login_path, email_env, password_env, labels | |
| L1-DSL-08 | Crawl block: enabled, max_depth, max_pages, same_origin_only | |
| L1-DSL-09 | Crawl: supplement_journeys (auto-add from crawl) | |
| L1-DSL-10 | Crawl: strict_enterprise flag | Triggers workflow agent checks |
| L1-DSL-11 | Budgets: max_steps_per_journey, max_run_seconds, step_timeout_ms | |
| L1-DSL-12 | Example configs | enterprise-authenticated, enterprise-saas, cal-com-phase0 |
| L1-DSL-13 | Init scaffold: `--auth`, `--no-crawl`, `--name`, `--prefix` | |
| L1-DSL-14 | Budget: `parallel_seeds` | Default 1; Argyle dogfood uses 3 |
| L1-DSL-15 | Budget: `repeat_micro_loop` | Default 1; CEO friction signal when raised |
| L1-DSL-16 | Step `open_link` + profile path fallback value | href / new-tab / first profile link |

### L1.3 Preflight & safety

| ID | Feature | Notes |
|----|---------|-------|
| L1-PRE-01 | SSRF-safe URL allowlist | Blocks private IPs, localhost, metadata endpoints |
| L1-PRE-02 | DNS resolution check before fetch | |
| L1-PRE-03 | HEAD preflight with GET fallback | `preflight_head()` |
| L1-PRE-04 | POST `/api/preflight` | Dashboard wrapper |

### L1.4 Crawl & site discovery

| ID | Feature | Notes |
|----|---------|-------|
| L1-CRL-01 | Same-origin BFS crawler (Playwright) | |
| L1-CRL-02 | Per-page metrics: links, forms, inputs, buttons, words, depth | |
| L1-CRL-03 | Hub path detection (most outbound links) | |
| L1-CRL-04 | Orphan path detection (no inbound from crawl) | |
| L1-CRL-05 | Auth-gated path detection (redirect to login) | |
| L1-CRL-06 | Error path detection (HTTP ≥400, error phrases) | |
| L1-CRL-07 | Sitemap JSON export | `sitemaps/{run_id}-sitemap.json` |
| L1-CRL-08 | Sitemap Markdown export | |
| L1-CRL-09 | Sitemap load/rebuild from JSON | `SiteMap.from_json_dict()` |
| L1-CRL-10 | GraphML export | `GET /api/sitemap/{run_id}/graphml` |
| L1-CRL-11 | Crawl budget / max_pages enforcement | |

### L1.5 Workflow detection

| ID | Feature | Notes |
|----|---------|-------|
| L1-WF-01 | Pattern classification: auth, signup, pricing, search, admin, dashboard, docs, integration | Regex on paths/titles |
| L1-WF-02 | Workflow confidence + signals per page | |
| L1-WF-03 | Suggested journeys from crawl graph | Up to 5 navigate-only journeys |
| L1-WF-04 | Auto-journey supplementation into config | `supplement_journeys()` |
| L1-WF-05 | Workflow agent findings | Auth-gated without login surface; missing enterprise paths |

### L1.6 Browser journey execution

| ID | Feature | Notes |
|----|---------|-------|
| L1-BRW-01 | Headless Chromium 1280×900 | |
| L1-BRW-02 | Auth flow with env credentials | Multi-strategy fill, 3 retries, session detection |
| L1-BRW-03 | Auth outcomes tracked on RunEvidence | success, failed_still_on_login, etc. |
| L1-BRW-04 | Step actions: navigate, click, fill, wait, assert_url_contains, **open_link** | |
| L1-BRW-05 | Per-step: final URL, title, HTTP status, duration | |
| L1-BRW-06 | Per-step body text excerpt (2000 chars) | |
| L1-BRW-07 | Per-step full-page PNG screenshot | |
| L1-BRW-08 | Per-step `.txt` body snapshot | |
| L1-BRW-09 | Error screenshot on step failure | |
| L1-BRW-10 | Console error capture (type error) | |
| L1-BRW-11 | Network failure capture (HTTP ≥400) | |
| L1-BRW-12 | Basic a11y counts: unlabeled buttons, labeled vs total inputs | In-page JS |
| L1-BRW-13 | Link count, heading count on page | |
| L1-BRW-14 | Error phrase detection in body | error, not found, unauthorized, forbidden |
| L1-BRW-15 | Step grading: pass / partial / fail | Auth redirect, loading state, 401/403 |
| L1-BRW-16 | Run budget enforcement | `RunBudgetExceeded`, step timeout |
| L1-BRW-17 | Journey agent: all config journeys, primary persona executes | Matrix replicated per persona |
| L1-BRW-18 | `open_link` with href / new-tab / profile fallback | Fixes View Profile no-op |
| L1-BRW-19 | Parallel seeds per journey (`parallel_seeds` budget) | Re-run + compare outcomes |
| L1-BRW-20 | `flaky` + `seed_index` on StepSnapshot | Cross-seed disagreement → FLAKY |

### L1.7 Heuristics & analysis (automated)

| ID | Feature | Notes |
|----|---------|-------|
| L1-HEU-01 | Persona × journey matrix | pass / partial / fail per cell |
| L1-HEU-02 | Issue: HTTP ≥400 → P1 | |
| L1-HEU-03 | Issue: auth wall on deep link → P2 | |
| L1-HEU-04 | Issue: unlabeled buttons → P2 | |
| L1-HEU-05 | Issue: form inputs missing labels → P2 | |
| L1-HEU-06 | Issue: slow step >8s → P3 | |
| L1-HEU-07 | Issue: sparse page content (<80 chars) → P2 | |
| L1-HEU-08 | Issue: stuck loading (initializing/loading…) → P1 | |
| L1-HEU-09 | Issue: duplicate CTAs (≥4) → P3 hypothesis | |
| L1-HEU-10 | Issue: auth setup failed → P1 | |
| L1-HEU-11 | Issue: crawl error pages → P1 | |
| L1-HEU-12 | Issue: deep navigation (depth ≥3) → P3 hypothesis | |
| L1-HEU-13 | Delight: visible error feedback after click | |
| L1-HEU-14 | Delight: clear navigation (links + headings) | |
| L1-HEU-15 | Delight: accessible form labels | |
| L1-HEU-16 | Delight: informative landing content | |
| L1-HEU-17 | Delight: interactive forms discovered (crawl) | |
| L1-HEU-18 | Automated dimensions (1–5): Functionality, UI/UX, Information clarity | |
| L1-HEU-19 | Readiness band: Green / Amber / Red | P1 count + matrix pass ratio |
| L1-HEU-20 | Persona keyword routing for findings | evaluator / operator / admin |
| L1-HEU-21 | Confidence labels: high / hypothesis | |
| L1-HEU-22 | Top blocker / top delight selection | |
| L1-HEU-23 | Flaky step findings (parallel seeds) | P2 when seeds disagree |

### L1.8 Multi-agent pipeline

| ID | Feature | Notes |
|----|---------|-------|
| L1-AGT-01 | CrawlAgent | Crawl + sitemap save + orphan findings |
| L1-AGT-02 | WorkflowAgent | Pattern detection + journey supplement |
| L1-AGT-03 | JourneyAgent | Browser E2E execution |
| L1-AGT-04 | PersonaAgent ×3 | Per-persona re-grade (admin/operator/evaluator lenses) |
| L1-AGT-05 | LLMPersonaAgent ×3 (optional) | Evidence-bound JSON findings |
| L1-AGT-06 | SynthesizerAgent | Dedupe, merge matrix, renumber IDs, readiness rollup |
| L1-AGT-07 | Agent reports in scorecard | Collaboration table |
| L1-AGT-08 | Agent handoff metadata | Page counts, step counts, merge stats |
| L1-AGT-09 | Orchestrator phase ordering | crawl → workflow → journey → persona → synthesis |
| L1-AGT-10 | Compliance agent placeholder in export | status idle |
| L1-AGT-11 | Performance agent placeholder in export | status idle |

### L1.9 LLM integration

| ID | Feature | Notes |
|----|---------|-------|
| L1-LLM-01 | Provider auto-detect | DeepSeek, NVIDIA NIM, OpenAI-compatible |
| L1-LLM-02 | Evidence bundle to model | Steps, sitemap summary, workflows (≤40 steps) |
| L1-LLM-03 | JSON-only response contract | issues, delights, journey_grades |
| L1-LLM-04 | Retry / timeout / JSON extraction fallback | |
| L1-LLM-05 | `llm_to_findings()` merge into synthesis | |
| L1-LLM-06 | Run + compare narrative LLM enrichment | ✅ `narrative.py`, `llm.py`; JSON brace fallback |

### L1.9b Interpretability (NLU) — shipped 2026-05-31

| ID | Feature | Notes |
|----|---------|-------|
| L1-NLU-01 | Run narrative (executive / founder / engineering) | ✅ `analysis/{run_id}.json` + bundle; `source: llm+template` |
| L1-NLU-02 | Run chat Q&A | ✅ `POST /api/runs/{runId}/chat`; Overview panel |
| L1-NLU-03 | Compare narrative on diff | ✅ `GET /api/diff`; Compare **What changed** panel |
| L1-NLU-04 | Jobs pass `llm` + load repo `.env` | ✅ Runner checkbox; serialized job queue |

| L1-NLU-05 | Trends narrative | ✅ `GET /api/trends` |
| L1-NLU-06 | Command digest | ✅ `GET /api/digest` |
| L1-NLU-07 | Persistent chat | ✅ `artifacts/chats/{run_id}.json` |
| L1-BRW-C01 | `explore` / `dismiss` actions | ✅ Phase C |
| L1-BRW-C02 | Journey recorder API | ✅ `POST /api/recordings/compile` |
| L1-BRW-C03 | Multi-persona browser | ✅ `execute_all_personas_in_browser` |

| L1-NLU-08 | Explore evidence export | ✅ `exploreLog`, `exploreSummary`, artifact JSON |

### L1.10 Scorecard & artifacts

| ID | Feature | Notes |
|----|---------|-------|
| L1-ART-01 | Run evidence JSON | `runs/{run_id}.json` |
| L1-ART-02 | Scorecard markdown | Executive summary, matrix, agents, dimensions, issues, delights, run log |
| L1-ART-03 | Analysis bundle JSON | Frontend_V1 contract |
| L1-ART-04 | Config snapshot per run | `configs/{run_id}.yaml` |
| L1-ART-05 | Step screenshots + text artifacts | `artifacts/{run_id}/*.png`, `.txt` |
| L1-ART-06 | Run ID format `{prefix}-{YYYYMMDD-HHMMSS}` | |
| L1-ART-07 | Rebuild bundle from artifacts (no browser) | `rebuild_bundle_from_artifacts()` |

### L1.11 Analysis export (bundle enrichment)

| ID | Feature | Notes |
|----|---------|-------|
| L1-EXP-01 | Numeric readiness score | Green=85, Amber=72, Red=38 + matrix adjustment |
| L1-EXP-02 | P0 severity upgrade | Auth failures, auth-wall patterns |
| L1-EXP-03 | Flake detection heuristic | Console errors, outcome variance, duration spikes + `step.flaky` |
| L1-EXP-04 | Owner heuristic | frontend / backend / content / security |
| L1-EXP-05 | Extended dimensions (Phase 2 heuristic) | Performance, Accessibility, Trust, Onboarding, Recovery |
| L1-EXP-06 | Sitemap pages/edges serialization | hub/leaf/orphan/auth types |
| L1-EXP-07 | Screenshots index in bundle | |
| L1-EXP-08 | Personas + journeys in bundle | |
| L1-EXP-09 | Workflows + suggested journeys in bundle | |
| L1-EXP-10 | Matrix cells in bundle | |

### L1.12 Dashboard API

| ID | Feature | Notes |
|----|---------|-------|
| L1-API-01 | GET `/api/health` | |
| L1-API-02 | GET `/api/summaries` | Run summary cards |
| L1-API-03 | GET `/api/bundle/{run_id}` | Full analysis bundle |
| L1-API-04 | GET `/api/runs`, GET `/api/runs/{id}` | Legacy detail format |
| L1-API-05 | GET `/api/diff?a=&b=` | Readiness, issues, pages, steps, new/resolved issues, **compare narrative** |
| L1-API-06 | GET `/api/trends` | Readiness, pages, flake rate time series |
| L1-API-07 | GET `/api/search?q=` | Runs, issues, pages |
| L1-API-08 | GET/PUT/POST `/api/workspace` | workspace.json persistence |
| L1-API-09 | GET `/api/configs` | Saved + example YAMLs |
| L1-API-10 | GET `/api/library` | Templates + suggested journeys |
| L1-API-11 | GET `/api/init` | Wizard steps + defaults metadata |
| L1-API-12 | GET/POST `/api/jobs` | Background run/crawl queue |
| L1-API-13 | GET/POST `/api/annotations/{run_id}` | Read + append annotations |
| L1-API-14 | POST `/api/backfill` | Trigger analysis rebuild |
| L1-API-15 | GET `/api/backlog` | P0/P1 from latest run |
| L1-API-16 | GET `/api/integrations` | Static catalog |
| L1-API-17 | GET `/api/alerts` | Static rule definitions |
| L1-API-18 | GET `/files/{path}` | Artifact file serving (path traversal guarded) |
| L1-API-19 | CORS headers | For Frontend_V1 dev proxy |
| L1-API-20 | Auto-backfill on serve startup | |
| L1-API-21 | Built-in static HTML dashboard | `dashboard/static/index.html` |

### L1.13 Background jobs

| ID | Feature | Notes |
|----|---------|-------|
| L1-JOB-01 | Enqueue run or crawl via subprocess | |
| L1-JOB-02 | Job status: queued / running / done / failed | |
| L1-JOB-03 | Parse run_id from CLI JSON stdout | |
| L1-JOB-04 | jobs.json persistence (last 50) | |
| L1-JOB-05 | 1-hour subprocess timeout | |

### L1.14 Phase 1 tail (partial — not partner-blocking)

| ID | Feature | Notes |
|----|---------|-------|
| L1-TAIL-01 | Named errors complete set | ✅ `BrowserStepTimeout`, etc. — CEO #11 |
| L1-TAIL-02 | Run cost estimate in bundle/logs | ✅ CEO #13 — `costEstimate` + `agentCost` |
| L1-TAIL-03 | Structured observability export | ✅ duration, outcome, pagesCrawled, agentsRun, configHash |

---

## 3. L2 — UI present, backend missing or partial

> Includes mock data when API is down, placeholders when API is up, and controls that do not persist or trigger real behavior.

### 3.1 Active L2 backlog (SELECTIVE EXPANSION)

#### Sprint 1 — P0 post-call async ✅ (2026-05-31)

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-08 | Export menu — artifact download buttons | ✅ `run-export.ts` + `/files/` downloads |
| L2-UI-09 | Export “Download all” | ✅ Sequential download of md/json/png |
| L2-UI-10 | Evidence dialog “Copy repro” | ✅ Clipboard + toast |
| L2-UI-11 | Evidence dialog “Open in step timeline” | ✅ Deep link `?tab=steps&step=` |
| L2-UI-17 | Compare page run A/B `<select>` | ✅ URL search `a`/`b` refetches diff |

#### Sprint 2 — P1 credibility & partner workflow ✅

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-12 | Annotations tab — add agree/disagree/false positive | ✅ `IssueAnnotationActions` + POST `/api/annotations/{run_id}` |
| L2-UI-29 | Workflows page coverage cards | ✅ `buildWorkflowCoverage()` from live bundle |
| L2-UI-30 | Workflows active journeys list | ✅ `bundle.journeys` from latest run |
| L2-UI-52 | Delights to protect section | ✅ `bundle.delights` on recommendations page |
| L2-UI-01 | “live” chip tied to API health + jobs | ✅ Command center |
| L2-UI-02 | Stat: “Time to first scorecard 11m 42s” | ✅ `formatDuration(latest.durationSec)` |
| L2-UI-03 | Stat: “Flake rate (7d) 3.1%” | ✅ `/api/trends` flakeRate + prior-run delta |
| L2-UI-04 | Stat: “Recurring blockers 2” | ✅ `issues.filter(recurring > 1).length` |

#### Sprint 3 — P2 onboarding & handoff

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-63 | Init wizard “Generate & write YAML” end step | ✅ Calls `POST /api/configs` from `/init` |
| L2-UI-68 | Init: describe user need → AI draft persona | ✅ `POST /api/personas/draft` + PersonaStudioPanel |
| L2-UI-69 | Init: core 3 + product-suggested extra personas | ✅ `POST /api/personas/suggest` |
| L2-UI-70 | Init: custom persona + toggle personas on/off | ✅ `personaEnabled`, `persona_lens`, staged extras on generate |
| L2-UI-71 | Config persona editor (add/edit/remove live) | **Partial** — append via `/api/configs/append-persona`; full editor later |
| L2-MCK-01 | Acme demo run `run_8s7d2` | Retire when API live — causes 404 on screen share |
| L2-UI-50 | “Export to Linear” button | ✅ Markdown/JSON download — OAuth delivery **later** §1 |

### 3.2 L2 catalog — mock data & fallback

| ID | Feature | Notes |
|----|---------|-------|
| L2-MCK-01 | Acme demo run `run_8s7d2` | Full rich mock bundle (not in artifacts unless backfilled) |
| L2-MCK-02 | Historical Acme runs (run_8s6q1, run_8s5l9, run_8s1k4) | Mock-only summaries |
| L2-MCK-03 | 4-persona Acme catalog (Prospect, Operator, Admin, Skeptic) | Not always matching live config |
| L2-MCK-04 | Acme journey catalog (6 marketing journeys) | vs enterprise/cal journey sets |
| L2-MCK-05 | `workflowCoverage` percentages (6 categories) | Not computed from live crawl |
| L2-MCK-06 | `suggestedJourneys` mock entries | |
| L2-MCK-07 | `issueRecurrence` table data | |
| L2-MCK-08 | `scheduledRuns` cron list | **Later** — §1 scheduled cron |
| L2-MCK-09 | `auditLog` entries | |
| L2-MCK-10 | `agentConfigDefaults` (LLM model, crawl sliders, agent toggles) | Not read/written to backend |
| L2-MCK-11 | `backlogItems` full mock set | API backlog only from latest run P0/P1 |
| L2-MCK-12 | Mock `integrations` card details beyond API catalog | Connect state fictional |
| L2-MCK-13 | Mock `alertChannels` beyond API template rules | |

### 3.3 L2 catalog — command center & global chrome

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-01 | “live” chip always shown | Sprint 2 |
| L2-UI-02 | Stat: “Time to first scorecard 11m 42s” | Sprint 2 |
| L2-UI-03 | Stat: “Flake rate (7d) 3.1%” | Sprint 2 |
| L2-UI-04 | Stat: “Recurring blockers 2” | Sprint 2 |
| L2-UI-05 | Environment selector (prod-canary / staging / demo) | Local React state; does not filter runs |
| L2-UI-06 | Workspace switcher button | **Later** — multi-workspace §1 |
| L2-UI-07 | Breadcrumb “acme” slug when workspace loading | Fallback label |

### 3.4 L2 catalog — run detail & evidence UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-08 | Export menu — artifact download buttons | Sprint 1 |
| L2-UI-09 | Export “Download all” | Sprint 1 |
| L2-UI-10 | Evidence dialog “Copy repro” | Sprint 1 |
| L2-UI-11 | Evidence dialog “Open in step timeline” | Sprint 1 |
| L2-UI-12 | Annotations tab — add agree/disagree/false positive | Sprint 2 |
| L2-UI-13 | Annotations — pin / manual finding | ✅ Pin on issues + `ManualAnnotationPanel` |
| L2-UI-14 | Severity reason / persona impact rich fields | Shown when in bundle; not always populated |
| L2-UI-15 | Similar issue IDs cross-linking | Mock Acme only |
| L2-UI-16 | Marketing-ready / regression-risk on delights | Partially in bundle; inconsistent |

### 3.5 L2 catalog — compare & diff UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-17 | Compare page run A/B `<select>` | ✅ Sprint 1 |
| L2-UI-17b | Compare **What changed** narrative panel | ✅ NLU-2; `AI + rules` badge |
| L2-UI-18 | Side-by-side step screenshot diff | ✅ `CompareVisualDiffPanel` + focus regions — `COMPARE_SCREENSHOTS.md` |
| L2-UI-19 | Visual sitemap diff highlight | ✅ Compare page sitemap new/removed panel |

### 3.6 L2 catalog — trends & monitoring UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-20 | Per-dimension trend sparklines | Seeded from mock math, not historical dimension API |
| L2-UI-21 | Stats: readiness avg (7d), issues opened/resolved | Hardcoded |
| L2-UI-22 | Issue recurrence table | Mock `issueRecurrence` |
| L2-UI-23 | Scheduled runs list | Mock — **later** §1 |
| L2-UI-24 | 14-day calendar heatmap | Static pattern |
| L2-UI-25 | “New issue / resolved issue” dedicated timeline | Partially in diff API; no trends UI |

### 3.7 L2 catalog — site map & workflows UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-26 | Sitemap graph layout | Client grid positions, not force-directed |
| L2-UI-27 | Sitemap “Preview screenshot” per page | ✅ Page list + graph click → preview |
| L2-UI-28 | Sitemap “Diff sitemap” | Links to compare; no sitemap-specific diff view |
| L2-UI-29 | Workflows page coverage cards | Sprint 2 |
| L2-UI-30 | Workflows active journeys list | Sprint 2 |
| L2-UI-31 | “Add to config” on suggested journey | ✅ Wired on `/workflows` + `/sitemap` via `POST /api/configs/append-journey` |
| L2-UI-32 | Click page → preview from last crawl | ✅ Wired on `/sitemap` |

### 3.8 L2 catalog — agents UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-33 | Agent configuration panel | Mock `agentConfigDefaults` |
| L2-UI-34 | Enable/disable agents per run toggles | Display only |
| L2-UI-35 | Crawl budget sliders | Display only |
| L2-UI-36 | LLM model picker | Display only |
| L2-UI-37 | Strict enterprise mode toggle in agents page | Display only |
| L2-UI-38 | Replay single agent | Button inert |
| L2-UI-39 | Expandable findings per agent (interactive) | Partially shown; no expand drill-down |
| L2-UI-40 | Live agent status stream (running → done) | Post-hoc bundle only; no SSE — **later** L3-OPS-11 |

### 3.9 L2 catalog — config & workspace UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-41 | YAML editor with live config | ✅ `GET /api/configs/{id}` + `ConfigYamlEditor` |
| L2-UI-42 | YAML validate button | ✅ `POST /api/configs/validate` |
| L2-UI-43 | YAML save to backend | ✅ `POST /api/configs/save` |
| L2-UI-44 | Personas editor (add/edit/remove) | Display mock personas only |
| L2-UI-45 | REHEARSE_* secrets manager UI | Shows “set” labels; no vault |
| L2-UI-46 | Git config version link | Display only |
| L2-UI-47 | Retention days enforcement | Display only; no purge job |
| L2-UI-48 | Strict enterprise mode toggle on config page | Display only |
| L2-UI-49 | Multi-product portfolio switcher | **Later** §1 |

### 3.10 L2 catalog — recommendations & backlog UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-50 | “Export to Linear” button | Sprint 3 stub / **later** delivery §1 |
| L2-UI-51 | Export to Jira / GitHub Issues | Inert — **later** §1 |
| L2-UI-52 | Delights to protect section | Sprint 2 |
| L2-UI-53 | Competitive benchmark URL input | Disabled — **later** L3-CMP |
| L2-UI-54 | Gap / wish list backlog | Mock items beyond API backlog |
| L2-UI-55 | Rubric alignment tags on backlog | Not implemented |

### 3.11 L2 catalog — alerts & integrations UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-56 | Recent alerts feed | Hardcoded 4 events |
| L2-UI-57 | “+ Add channel” button | Inert |
| L2-UI-58 | Toggle alert channel enabled (persist) | Display only |
| L2-UI-59 | Integration Connect / Manage buttons | Inert — **later** §1 |
| L2-UI-60 | OAuth flows (GitHub, Slack, SSO) | **Later** §1 |
| L2-UI-61 | Datadog / Sentry linked dashboards | Catalog only |

### 3.12 L2 catalog — init & library UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-62 | Init wizard PII checkbox | ✅ Saved via `POST /api/configs` (`piiRedaction`) |
| L2-UI-63 | Init wizard “Generate & write YAML” end step | ✅ Calls `POST /api/configs` from `/init` |
| L2-UI-64 | Library “parallel seeds / flaky config” badges | **Misleading UI** — engine runs seeds (L1-BRW-19); badge copy only |

### 3.13 L2 catalog — runner UI

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-65 | Job config picker | ✅ Runner config selector + shared `selected-config` persistence |
| L2-UI-66 | `--llm` toggle in runner UI | Not exposed in all job POST paths |
| L2-UI-67 | Live log stream during job | Poll only; no stdout stream |

### 3.14 L2 catalog — legacy HTML dashboard

| ID | Feature | Notes |
|----|---------|-------|
| L2-UI-68 | Separate static dashboard at `/` on :8765 | Simpler than Frontend_V1; not feature-parity |

---

## 4. L3 — Not present (future / spec)

> Default posture: **later priority** unless pulled forward by a paying design partner. Grouped for roadmap planning; all items retained from prior scope.

### 4.1 Security & trust (deep) — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-SEC-01 | OWASP-style vulnerability scan | |
| L3-SEC-02 | Cookie flags / Secure / HttpOnly / SameSite audit | |
| L3-SEC-03 | CSP / HSTS header analysis | |
| L3-SEC-04 | Secrets or API keys in DOM/network leak scan | |
| L3-SEC-05 | Session fixation / CSRF surface checks | |
| L3-SEC-06 | Auth fuzzing / brute-force detection | |
| L3-SEC-07 | Dependency / supply-chain scan | |
| L3-SEC-08 | Penetration test agent | |
| L3-SEC-09 | Compliance agent (functional) | L1 placeholder idle |
| L3-SEC-10 | SOC2-ready storage / encryption at rest story | |
| L3-SEC-11 | Customer-managed encryption keys | |
| L3-SEC-12 | Dashboard SSO (OIDC/SAML) | **Later** §1 |
| L3-SEC-13 | Dashboard RBAC (admin / viewer / run-only) | **Later** §1 |

### 4.2 Accessibility (deep) — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-A11Y-01 | axe-core / WCAG 2.x automated audit | L1 = unlabeled counts only |
| L3-A11Y-02 | Color contrast checking | |
| L3-A11Y-03 | Keyboard-only navigation traversal | |
| L3-A11Y-04 | Focus trap / skip link detection | |
| L3-A11Y-05 | Screen reader path simulation | |
| L3-A11Y-06 | ARIA roles/landmarks completeness | |
| L3-A11Y-07 | Motion / reduced-motion preference | |

### 4.3 Performance & reliability (deep) — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-PERF-01 | Web Vitals (LCP, INP, CLS) capture | |
| L3-PERF-02 | Lighthouse performance score | |
| L3-PERF-03 | Performance agent (functional) | L1 placeholder idle |
| L3-PERF-04 | Network waterfall / HAR analysis | |
| L3-PERF-05 | API response time percentile tracking | L1 has per-step duration |
| L3-PERF-06 | Rate limiting / 429 detection | |
| L3-PERF-07 | CDN / cache header analysis | |
| L3-PERF-08 | Load testing / concurrency simulation | |
| L3-PERF-09 | Repeat micro-loop friction (deep analytics) | **Partial L1** — `repeat_micro_loop` in DSL |
| L3-PERF-10 | Parallel seeds at scale / statistical flake scoring | **Partial L1** — `parallel_seeds` + FLAKY |
| L3-PERF-11 | Mobile / tablet viewport profiles | Init wizard defaults only |
| L3-PERF-12 | API+UI hybrid journey steps | Spec’d |

### 4.4 Visual / UX / design quality (deep) — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-DES-01 | Layout / positioning / overlap detection | |
| L3-DES-02 | Responsive breakpoint testing | |
| L3-DES-03 | Design system / token consistency | |
| L3-DES-04 | Typography hierarchy critique | |
| L3-DES-05 | Spacing / alignment grid analysis | |
| L3-DES-06 | Native-ness / platform HIG conformance | |
| L3-DES-07 | Dark mode / theme consistency | |
| L3-DES-08 | Figma or design-file comparison | |
| L3-DES-09 | Visual regression (screenshot diff between runs) | |
| L3-DES-10 | Brand / styling critique with design knowledge | LLM hints only |
| L3-DES-11 | Every button/control sitewide interaction test | L1 = configured journeys only |
| L3-DES-12 | Hover / tooltip / micro-interaction coverage | |

### 4.5 Journey, product & behavioral analytics — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-JRN-01 | Agentic NPS / qualitative satisfaction score | |
| L3-JRN-02 | Stickiness / return-visit simulation | **Later** §1 100× modes |
| L3-JRN-03 | User adaptability / learning curve measurement | |
| L3-JRN-04 | Time-to-value metric | |
| L3-JRN-05 | Funnel drop-off analytics across journeys | |
| L3-JRN-06 | Session replay integration (Hotjar-style) | |
| L3-JRN-07 | Discoverability / information scent scoring (deep) | |
| L3-JRN-08 | Onboarding completion rate | Partial dimension heuristic |
| L3-JRN-09 | Empty state / error recovery UX scoring (deep) | Partial heuristic |
| L3-JRN-10 | Cross-persona hinderance report (narrative) | Partial via LLM |

### 4.6 Content, freshness & SEO — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-CNT-01 | Footer / copyright freshness (systematic) | |
| L3-CNT-02 | Stale content detection across site | |
| L3-CNT-03 | Broken external link checker | |
| L3-CNT-04 | SEO meta / OG tag audit | |
| L3-CNT-05 | i18n / locale / RTL layout testing | |
| L3-CNT-06 | Copy tone / reading level analysis | |
| L3-CNT-07 | Legal page completeness (privacy, terms) | |

### 4.7 Crawl & discovery (advanced) — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-CRL-01 | Subdomain / multi-tenant URL sets | |
| L3-CRL-02 | Import OpenAPI as journey seed | |
| L3-CRL-03 | Import sitemap.xml as crawl seed | |
| L3-CRL-04 | Authenticated crawl at scale (SSO test tenant) | Basic auth only today |
| L3-CRL-05 | Robots.txt respect (optional flag spec’d) | |
| L3-CRL-06 | Cookie consent banner handling | |
| L3-CRL-07 | Cross-run sitemap diff UI | API partial |

### 4.8 Analysis, export & workflow integration — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-INT-01 | Real Slack alert delivery | **Later** §1 |
| L3-INT-02 | Real email alert delivery | **Later** §1 |
| L3-INT-03 | Webhook alert delivery | **Later** §1 |
| L3-INT-04 | Weekly digest scorecard email | |
| L3-INT-05 | GitHub Actions PR / deploy trigger | **Later** §1 Aug 2026 |
| L3-INT-06 | Vercel / Netlify post-deploy hook | |
| L3-INT-07 | Linear / Jira / GitHub Issues export (functional) | **Later** §1 |
| L3-INT-08 | Datadog / Sentry correlation with run_id | |
| L3-INT-09 | PDF scorecard export | |
| L3-INT-10 | ZIP export of all artifacts | |
| L3-INT-11 | `rehearse schedule` cron command | **Later** §1 |
| L3-INT-12 | CI status badge / GitHub check run | **Later** §1 |

### 4.9 Competitive & market intelligence — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-CMP-01 | Competitor URL benchmark run | |
| L3-CMP-02 | Side-by-side readiness vs competitor | |
| L3-CMP-03 | Feature parity matrix vs competitor | |
| L3-CMP-04 | Pricing / positioning comparison | |

### 4.10 Governance, ops & platform — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-OPS-01 | Evidence retention purge job (30/90/365) | Policy field exists |
| L3-OPS-02 | PII redaction in screenshots/text (functional) | Toggle exists; no pipeline |
| L3-OPS-03 | Audit log (functional) | Mock only |
| L3-OPS-04 | False positive rate analytics from annotations | |
| L3-OPS-05 | Multi-workspace / multi-product portfolio | **Later** §1 |
| L3-OPS-06 | Billing / usage metering | **Later** §1 PLG |
| L3-OPS-07 | Design partner workspace isolation | |
| L3-OPS-08 | Agent cost accounting (real $ from API usage) | Partial metadata |
| L3-OPS-09 | Human manual finding + evidence upload | |
| L3-OPS-10 | Agent replay from mid-pipeline stage | |
| L3-OPS-11 | Live SSE agent event stream | |
| L3-OPS-12 | Success metrics dashboard (time-to-first-scorecard SLA) | |

### 4.11 Product line extensions — **later**

| ID | Feature | Notes |
|----|---------|-------|
| L3-PRD-01 | Product B — Deal Rehearsal (synthetic org context) | **Later** Mar 2027 gate §1 |
| L3-PRD-02 | Phase 3 — trend alerting at scale | |
| L3-PRD-03 | Numeric readiness as SLA gate in CI | Ties to GitHub Action CI §1 |

### 4.12 Predictive rehearsal (Blok-adjacent) — **later**

> **Cherry-pick only.** Full matrix: `COMPETITIVE_BLOK.md`. Do not promise on partner calls until Wave 1 ships. No public fidelity % until **G6** (`PRODUCT.md`).

| ID | Feature | Wave | Notes |
|----|---------|------|-------|
| L3-PRED-01 | Import analytics export (Segment / Mixpanel / Amplitude JSON) → persona priors | 3 | TechCrunch onboarding; optional for founders without data |
| L3-PRED-02 | Experiment spec: `hypothesis`, `user_goal`, `variant_label` on config or run | 1 | ✅ DSL + API + Config UI + run banner |
| L3-PRED-03 | Cohort mode: N seeds + aggregate pass/fail and confidence band | 2 | ✅ `enqueue_cohort_run()`, `/api/jobs/cohort`, `/cohort/:jobId` (PR #22) |
| L3-PRED-04 | Experiment report UI: overall + per-persona rollup | 1 | ✅ `/api/experiment/{id}/report`, per-persona grade table, verdict chip (PR #21) |
| L3-PRED-05 | Chat scoped to experiment (multi-run + diff context) | 1 | ✅ `/api/experiment/{id}/chat`, `chat_about_experiment()` in `llm.py` (PR #21) |
| L3-PRED-06 | Variant rehearsal job: config A vs B, single report + readiness delta | 1 | ✅ `enqueue_variant_run()`, `/api/jobs/variant`, `/experiment/:jobId` (PR #22) |
| L3-PRED-07 | Step-level continue / hesitate / abandon distribution | 2 | ✅ `_step_behavior()` in export, chips in Steps tab, counts in observability (PR #22) |
| L3-PRED-07b | Funnel drop-off: aggregate abandon rates across journeys (step-level → flow view) | 2 | Depends on L3-JRN-05; next after L3-PRED-07 |
| L3-PRED-08 | Optional Figma / prototype link on experiment | 3 | Shares `L3-DES-08`; staging URL remains primary |
| L3-PRED-09 | Directional lift card (readiness Δ, issues new/resolved; `hypothesis` label) | 2 | ✅ `LiftCard` component on experiment page, "Directional until G6" label (PR #22) |
| L3-PRED-10 | Calibration dashboard (sim vs beta overlap; optional step backtest) | 3 | **G6** Jun 30, 2027 |

**Overlaps (do not duplicate work):** funnel drop-off → `L3-JRN-05`; Figma compare → `L3-DES-08`; fidelity narrative → `G6` + `EVALUATION_FRAMEWORK.md` §8.

---

## 5. Indexes & cross-refs

### 5.1 User-discussed concerns → level

| Concern | Level | Active vs later |
|---------|-------|-----------------|
| Security (deep) | L3 | **Later** §1 |
| Sites breaking | L1 | Active |
| Loading times (basic) | L1 | Active |
| Loading times (Web Vitals) | L3 | **Later** |
| Accessibility (basic labeling) | L1 | Active |
| Accessibility (full WCAG) | L3 | **Later** |
| Every single button | L3 | **Later** |
| Positioning / layout / native-ness | L3 | **Later** |
| API fails / network errors | L1 | Active |
| Customer journeys & hinderances | L1 + LLM | Active |
| Discoverability (deep) | L3 | **Later** |
| Stickiness / 100× modes | L3 | **Later** §1 |
| Agentic NPS | L3 | **Later** |
| Response time | L1 step duration | Active |
| UI/UX styling critique | L1 heuristics | Active; deep = **Later** |
| Compliance (functional) | L3 | **Later** |
| Freshness / SEO | L3 | **Later** |
| Competitor analysis | L3 | **Later** |
| Slack/Jira/Linear delivery | L3 + L2 stubs | **Later** §1 |
| PLG / billing | L3 | **Later** §1 |
| SSO / RBAC dashboard | L3 | **Later** §1 |
| Scheduled cron | L3 + L2 mock | **Later** §1 |
| GitHub CI integration | L3 | **Later** §1 |
| Product B | L3 | **Later** §1 |
| Journey marketplace | — | **Later** §1 |
| Parallel seeds / FLAKY | L1 | Active (shipped) |
| Predicted drop-off / lift (Blok-style) | L3-PRED + L3-JRN-05 | **Later** · `COMPETITIVE_BLOK.md` |
| Analytics-informed personas | L3-PRED-01 | **Later** Wave 3 |
| Behavioral fidelity % (published) | L3-PRED-10, G6 | **Later** 2027 |

### 5.2 Design partner demo readiness

See full gates: `DESIGN_PARTNER_CHECKLIST.md`.

| Mode | Verdict |
|------|---------|
| Concierge | ✅ Ready — G1–G13 (2026-05-31) |
| Self-serve | ✅ Sprint 1–3 shipped |
| UI for partner calls | **Dev** at `:8081` — `npm run dev` + `./rehearse serve` |
| Do not promise | §1 Deferred later |

### 5.3 File references

| Area | Path |
|------|------|
| CLI | `launch-rehearsal/src/rehearse/cli.py` |
| Heuristics | `launch-rehearsal/src/rehearse/heuristics.py` |
| Agents | `launch-rehearsal/src/rehearse/agents/` |
| API | `launch-rehearsal/src/rehearse/dashboard/server.py`, `store.py` |
| Bundle export | `launch-rehearsal/src/rehearse/analysis_export.py` |
| Frontend routes | `Frontend_V1/src/routes/` |
| Mock fallback | `Frontend_V1/src/lib/mock-data/store.ts` |
| API hooks | `Frontend_V1/src/lib/api/hooks.ts` |
| Spec north star | `enterprise_work_env_simulator_2026/MONITORING_PLATFORM_SPEC.md` |
| Design partner outreach | `enterprise_work_env_simulator_2026/DESIGN_PARTNER_CHECKLIST.md` |
| UI Vision vs Deliverable | `enterprise_work_env_simulator_2026/UI_PRODUCT_LINES.md` |
| CEO decisions | `enterprise_work_env_simulator_2026/CEO_DECISIONS.md` |
| GitHub org | https://github.com/orgs/Lapse-AI/repositories |

### 5.4 Inventory counts

| Level | Count (approx.) |
|-------|-----------------|
| L1 | ~125 (+ tail + seeds/open_link) |
| L2 | ~68 |
| L3 | ~95 |
| **Total scoped pointers** | **~288** |

---

## CEO REVIEW REPORT

| Review | Status | Findings |
|--------|--------|----------|
| CEO Review (SELECTIVE EXPANSION) | clean | Reorganized doc; §1 deferred bucket; §0 active sprints; L1 promotions for seeds/open_link; outreach not blocked by L2 |

**VERDICT:** Ready for implementation planning on **Sprint 1 L2** while **Track A outreach** runs in parallel.
