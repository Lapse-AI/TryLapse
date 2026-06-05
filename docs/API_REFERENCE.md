# API Reference

Base URL: `http://<host>:<port>` (default `:8080` in production, `:8765` in local dev)

All API routes return JSON. Errors follow `{ "error": "<message>" }`.

---

## Authentication

### POST /auth/signup

Create a new user account.

**Request body**
```json
{ "email": "you@company.com", "password": "s3cr3t", "name": "Jane" }
```

**Response `201`**
```json
{
  "token": "<jwt>",
  "user": { "id": "<uuid>", "email": "you@company.com", "name": "Jane" }
}
```

**Error `409`** — email already in use.

---

### POST /auth/login

Authenticate an existing user.

**Request body**
```json
{ "email": "you@company.com", "password": "s3cr3t" }
```

**Response `200`**
```json
{
  "token": "<jwt>",
  "user": { "id": "<uuid>", "email": "you@company.com", "name": "Jane" }
}
```

**Error `401`** — invalid email or password.

---

### GET /auth/me

Return the currently authenticated user (requires a valid JWT in `Authorization: Bearer <token>`).

**Response `200`**
```json
{ "id": "<uuid>", "email": "you@company.com", "name": "Jane" }
```

**Error `401`** — not authenticated.

---

### Protected routes

When `REHEARSE_API_TOKEN` is set, all `/api/*` routes require one of:

- `Authorization: Bearer <token>` — static API token **or** a valid user JWT
- `?token=<token>` — query param (static token only)

Public paths that never require auth: `/`, `/api/health`, `/auth/*`, `/static/*`.

---

## Runs

### GET /api/runs

List all runs.

| Query param | Type | Description |
|-------------|------|-------------|
| `format`    | `summary` | Return lighter summary objects |

**Response** — array of run objects.

---

### GET /api/summaries

Alias for `GET /api/runs?format=summary`.

---

### GET /api/runs/:runId

Fetch full run evidence (steps, screenshots, web-vitals).

**Error `404`** — run not found.

---

### GET /api/runs/:runId/chat

Fetch the chat thread for a run.

### POST /api/runs/:runId/chat

Send a message about a run.

**Request body**
```json
{ "message": "Why did this step fail?" }
```

**Response**
```json
{ "runId": "...", "reply": "...", "source": "llm|template" }
```

---

## Analysis bundles

### GET /api/bundle/:runId

Return the synthesised analysis bundle for a run (summary, issues, delights, persona grades).

**Error `404`** — bundle not found.

---

## Trends & digest

### GET /api/trends

Historical readiness, page count, flake rate, and recurring issue data across all runs.

| Query param | Type | Description |
|-------------|------|-------------|
| `refresh`   | `1\|true` | Force recompute |

---

### GET /api/digest

Summary digest for the last N days.

| Query param | Default | Description |
|-------------|---------|-------------|
| `n`         | `7`     | Number of days |
| `refresh`   | `false` | Force recompute |

---

## Search

### GET /api/search

Full-text search across runs and issues.

| Query param | Description |
|-------------|-------------|
| `q`         | Search query |

---

## Diff

### GET /api/diff

Compare two runs side-by-side.

| Query param | Description |
|-------------|-------------|
| `a`         | Run ID A |
| `b`         | Run ID B |
| `refresh`   | `1\|true` to force recompute |

---

## Jobs (background runs)

### GET /api/jobs

List all background jobs.

### POST /api/jobs

Enqueue a new run.

**Request body**
```json
{
  "configPath": "launch-rehearsal/artifacts/configs/lr-self.yaml",
  "mode": "run",
  "llm": true,
  "noCrawl": false
}
```

**Response `202`** — `{ "id": "<jobId>", "status": "queued" }`

Rate-limited: max 5 requests per 60 s per IP.

---

### POST /api/jobs/cohort

Enqueue a multi-seed reliability run.

**Request body**
```json
{
  "configPath": "...",
  "nSeeds": 7,
  "hypothesis": "Homepage loads under 3 s for all personas",
  "llm": true
}
```

### GET /api/cohort/:jobId

Get cohort job status and aggregate stats (readiness mean/min/max, recurring issues).

---

### POST /api/jobs/variant

Enqueue an A/B test between two configs.

**Request body**
```json
{
  "configAPath": "...",
  "configBPath": "...",
  "hypothesis": "New onboarding increases evaluator readiness",
  "userGoal": "Complete signup in < 2 minutes"
}
```

### GET /api/variant/:jobId

Get variant job status and diff narrative.

---

## Configs

### GET /api/configs

List saved test configs.

### POST /api/configs

Create a new config from a structured body.

| Field | Type | Description |
|-------|------|-------------|
| `targetUrl` | string | **Required** |
| `productName` | string | Display name |
| `withAuth` | boolean | Include auth steps |
| `piiRedaction` | boolean | Redact PII from screenshots |
| `viewports` | string[] | e.g. `["desktop","mobile"]` |

### GET /api/configs/:configId

Return config YAML + parsed experiment spec.

### POST /api/configs/validate

Validate raw YAML.

**Request body** `{ "yaml": "..." }`

**Response** `{ "valid": true, "errors": [], "summary": { "journeyCount": 3 } }`

### POST /api/configs/save

Save or update YAML directly.

**Request body** `{ "yaml": "...", "configId": "optional-id-to-overwrite" }`

### POST /api/configs/experiment

Attach a hypothesis/userGoal to a config.

### POST /api/configs/append-journey

Append a navigate journey step.

### GET /api/configs/:configId/personas

List personas defined in a config.

### POST /api/configs/personas

Enable/disable personas or toggle persona-lens mode.

### POST /api/configs/personas/replace

Bulk-replace all personas in a config.

### POST /api/configs/append-persona

Append a single persona to a config.

---

## Personas & journeys

### POST /api/personas/draft

Generate a persona from a natural-language prompt.

**Request body** `{ "prompt": "...", "targetUrl": "...", "productName": "..." }`

### POST /api/personas/suggest

Suggest core personas for a product URL.

### POST /api/journeys/draft

Generate a journey from a prompt.

**Request body** `{ "prompt": "...", "targetUrl": "..." }`

---

## Library

### GET /api/library

Return journey/persona templates and metadata.

---

## Experiments

### GET /api/experiment/:jobId/chat

Fetch experiment chat thread.

### POST /api/experiment/:jobId/chat

Send a message about an experiment.

### GET /api/experiment/:jobId/report

Return variant comparison report (readiness delta, persona grades, hypothesis verdict).

---

## Workspace

### GET /api/workspace

Return workspace metadata (name, slug, env, retention days, PII settings).

### PUT /api/workspace

Update workspace metadata.

---

## Integrations & alerts

### GET /api/integrations

Return configured Slack / Linear / Jira webhooks.

### GET /api/alerts

Return alert channel configurations.

---

## Annotations

### GET /api/annotations/:runId

Fetch user annotations on a run.

### POST /api/annotations/:runId

Add an annotation.

**Request body** `{ "text": "...", "stepId": "optional" }`

---

## Backlog

### GET /api/backlog

Return unresolved issues/findings across all runs.

---

## Misc

### GET /api/health

Liveness check. Always public.

**Response** `{ "ok": true, "artifacts": "/data/artifacts" }`

### POST /api/preflight

Check whether a URL is reachable before starting a run.

**Request body** `{ "url": "https://example.com", "allowLocalhost": false }`

### POST /api/recordings/compile

Convert a manually-recorded journey (step list) into YAML.

### GET /api/init

Return scaffolding wizard defaults and available configs.

### GET /api/sitemap/:runId/graphml

Download a crawl graph in GraphML format (renderable in Gephi).

### POST /api/backfill

Regenerate missing `analysis.json` files for existing runs.
