# Launch Rehearsal — Architecture

## System overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Partner's browser / your browser                                    │
│  http://localhost:8081  (dev)  or  https://*.railway.app (deployed) │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP (Vite proxy locally /
                               │ direct fetch on deployed)
┌──────────────────────────────▼──────────────────────────────────────┐
│  Frontend_V1  (React + TanStack Router + Vite)                       │
│  • Routes: /  /runs/:id  /compare  /runner  /init  /config  …       │
│  • Mock fallback when API is down (Acme data)                        │
│  • Auth: VITE_REHEARSE_API_TOKEN → Authorization: Bearer header      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST JSON  :8765
┌──────────────────────────────▼──────────────────────────────────────┐
│  rehearse serve  (Python stdlib HTTPServer)                          │
│  launch-rehearsal/src/rehearse/dashboard/server.py                   │
│                                                                      │
│  Auth:  REHEARSE_API_TOKEN (optional Bearer check)                   │
│  CORS:  REHEARSE_CORS_ORIGIN (defaults to localhost:8081)            │
│  Rate:  5 job requests / 60s / IP  (rate_limit.py)                  │
│                                                                      │
│  Key routes:                                                         │
│    GET  /api/summaries           list run summaries                  │
│    GET  /api/bundle/:id          full analysis bundle                │
│    GET  /api/diff?a=&b=          compare two runs                    │
│    GET  /api/digest              command-center NLU digest           │
│    GET  /api/trends              readiness trend series              │
│    POST /api/jobs                trigger rehearsal run               │
│    POST /api/jobs/variant        A/B variant rehearsal               │
│    POST /api/jobs/cohort         N-seed cohort rehearsal             │
│    GET  /api/experiment/:id/report  per-persona experiment rollup    │
│    POST /api/experiment/:id/chat    experiment-scoped LLM chat       │
│    POST /api/runs/:id/chat          run-scoped LLM chat              │
│    GET  /api/configs             list saved configs                  │
│    POST /api/configs/save        write YAML config                   │
│    GET  /files/*                 serve artifact files (screenshots)  │
└──────────────────┬────────────────────────────────────────────────────┘
                   │ spawns subprocess
┌──────────────────▼─────────────────────────────────────────────────┐
│  rehearse run  (CLI — separate process per job)                      │
│  launch-rehearsal/src/rehearse/                                      │
│                                                                      │
│  Pipeline:                                                           │
│  1. Preflight + SSRF check (preflight.py)                            │
│  2. CrawlAgent — BFS sitemap, workflow classification                │
│  3. JourneyAgent — Playwright browser, 3 personas × 5 journeys      │
│  4. PersonaAgent ×3 — re-grade evidence per persona lens             │
│  5. LLMPersonaAgent (optional, DEEPSEEK_API_KEY)                     │
│  6. SynthesizerAgent — merge matrix, dedupe, readiness band          │
│  7. analysis_export.py → analysis/{run_id}.json (bundle)            │
│  8. scorecard.py → scorecards/{run_id}-scorecard.md                  │
└──────────────────┬─────────────────────────────────────────────────┘
                   │ writes
┌──────────────────▼─────────────────────────────────────────────────┐
│  Artifacts  (local disk / Docker volume /data/artifacts)            │
│                                                                      │
│  jobs.db                        SQLite job queue (WAL mode)         │
│  runs/{run_id}.json             raw RunEvidence                     │
│  analysis/{run_id}.json         computed bundle (issues, matrix…)   │
│  artifacts/{run_id}/*.png       step screenshots                     │
│  configs/{config_id}.yaml       rehearsal configs                   │
│  scorecards/{run_id}-*.md       markdown reports                    │
│  sitemaps/{run_id}-sitemap.json crawl sitemap graph                 │
│  chats/{run_id}.json            persistent chat threads             │
│  narratives/{hash}.json         cached LLM narrative blobs          │
│  workspace.json                 workspace settings                  │
└────────────────────────────────────────────────────────────────────┘
```

## Data flow for a single rehearsal

```
User → Init wizard → POST /api/configs → config.yaml saved
     → Runner → POST /api/jobs → job queued in jobs.db
              → background thread → rehearse run subprocess
                                  → Playwright browser
                                  → per-step screenshots + logs
                                  → heuristics + LLM agents
                                  → analysis/{run_id}.json written
              → job status: done, runId set
     → Runs list (polling) → shows new run
     → Run detail → GET /api/bundle/:id → matrix, issues, narrative
```

## Scoring model

| Score | How computed | File |
|-------|-------------|------|
| **Readiness band** (Green/Amber/Red) | P1 count + matrix pass ratio | `heuristics.py:_overall_readiness()` |
| **Readiness number** (e.g. 92) | Band base (85/72/38) ± matrix adjustment | `analysis_export.py:_readiness_score()` |
| **Functionality** (0–100) | Step pass rate + fail count → score 2–5 × 20 | `heuristics.py:_score_dimensions()` |
| **UI/UX** (0–100) | Unlabeled button count + avg step duration → 2–5 × 20 | same |
| **Information** (0–100) | Sparse-content pages (body < 80 chars) → 2–5 × 20 | same |
| **Performance** (0–100) | Tier-1 average ± Web Vitals/duration bump | `analysis_export.py:_expand_dimensions()` |
| **Accessibility** (0–100) | Tier-1 average − 15 if >5 unlabeled buttons | same |
| **Trust** (0–100) | Tier-1 average − 20 if auth failed | same |
| **Onboarding** (0–100) | Tier-1 average + 0 (**no unique signal yet** — see issue #23) | same |
| **Recovery** (0–100) | Tier-1 average + 0 (**no unique signal yet** — see issue #23) | same |

## Security model

| Layer | Mechanism |
|-------|-----------|
| SSRF | `preflight.py` blocks private IPs, metadata endpoints |
| API auth | Optional `REHEARSE_API_TOKEN` Bearer check (server.py) |
| CORS | Locked to `REHEARSE_CORS_ORIGIN` (defaults: localhost) |
| Rate limiting | 5 job POSTs / 60s / IP; 30 config / 120 other (rate_limit.py) |
| Path traversal | `/files/` resolved path checked against `artifacts_root` |
| Request size | 10 MB hard cap on JSON body reads |
| Secrets | `.env` values never returned in API responses |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REHEARSE_API_TOKEN` | _(unset)_ | Bearer token required on all `/api/*` requests when set |
| `REHEARSE_CORS_ORIGIN` | `http://localhost:8081,http://127.0.0.1:8081` | Allowed CORS origins (comma-separated) |
| `REHEARSE_PORT` | `8080` | Dashboard server port (Railway injects `PORT`) |
| `DEEPSEEK_API_KEY` | _(unset)_ | Enables LLM persona agents + NLU narratives |
| `REHEARSE_LLM_API_KEY` | _(unset)_ | Alternative LLM key |
| `REHEARSE_EMAIL` | _(unset)_ | Staging login for configs using `${REHEARSE_EMAIL}` |
| `REHEARSE_PASSWORD` | _(unset)_ | Staging password |
| `VITE_REHEARSE_API` | _(unset)_ | Frontend: override API base URL (e.g. Railway domain) |
| `VITE_REHEARSE_API_TOKEN` | _(unset)_ | Frontend: Bearer token to send with every request |

---

## Deep Analysis Engine (Phase 1–6)

### Architecture overview

```
Deep Discovery Bot (deep_crawler.py)
  → InteractionMap: every button, form, modal, API call, chatbot, filter

Product Intelligence (product_intelligence.py)
  → ProductModel: purpose, type, features, workflows, IA concerns, quality concerns
  → Stored in artifacts/product_model.json — user-editable via PUT /api/product/update

Per-Persona Journey Discovery (persona_journey_discovery.py)
  → Each persona reads ProductModel + its goals
  → LLM generates 10–100 journeys with frequency, sub-flows, failure signals
  → POST /api/journeys/discover → parallel discovery for all personas

Behavioral Judge (behavioral_judge.py)
  → LLM evaluates every step: "Did this serve the persona's goal?"
  → Not just technical pass/fail — chatbot quality, navigation friction, IA gaps
  → judge_step(): per-step behavioral verdict + friction signals
  → judge_journey(): synthesised UX improvements + journey length assessment
```

### New API endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/product` | Load stored product model |
| `POST /api/product/analyze` | Run LLM analysis from crawl data → store ProductModel |
| `POST /api/product/update` | Partial update to ProductModel (user edits) |
| `POST /api/journeys/discover` | Discover journeys for all personas in parallel |
| `POST /api/journeys/discover/persona` | Discover journeys for one persona |

### Two-lens analysis model

**Lens A — Technical Inspector**: API failures, console errors, broken flows, form errors, performance
**Lens B — Behavioral Analyst**: goal completion, navigation friction, chatbot quality, information architecture, journey length vs access frequency
