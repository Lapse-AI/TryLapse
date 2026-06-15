# Context Checkpoint — feat/deep-analysis-wiring
**Branch:** feat/deep-analysis-wiring  
**Date:** 2026-06-13 00:08 UTC  
**Last commit:** `3ad9685` feat: persona library + workspace-scoped job filtering

---

## What was built this session

### 1. Workspace routing scoping (6 files)
All compare/diff, runs, runner links in workspace-scoped pages now use `/$workspaceSlug/...` URLs.
- `$workspaceSlug.dashboard.tsx` — Compare, All runs, View all
- `$workspaceSlug.runs.index.tsx` — Diff last two
- `$workspaceSlug.compare.tsx` — individual run links (A & B)
- `runs.$runId.tsx` — Diff button reads workspace from localStorage
- `app-sidebar.tsx` — live-job runner link
- `run-history-live-rows.tsx` — accepts `workspaceSlug` prop; run + job links

**Key nuance:** `$workspaceSlug.runs.$runId.tsx` still redirects to `/runs/$runId` (non-scoped). The Diff button in the non-scoped run detail reads `getWorkspace()?.slug` from localStorage to build a scoped compare URL. Long-term fix: make the workspace run detail render in-place instead of redirecting.

### 2. /api/jobs server-side workspace filtering
- `job_store.py`: `list_jobs()` now accepts `config_prefix` — filters via `json_extract` on the SQLite `data` column (`$.config` path and `$.runId`)
- `server.py`: derives prefix by stripping `-YYYYMMDD-HHMMSS` from config filename stem (e.g. `faculty-dashboard-eight-vercel-app`)
- Falls back to `?configPrefix=` query param, then authenticated user's workspace config, then all-jobs
- CORS headers updated to include `DELETE`

### 3. NIM 429 Retry-After-aware backoff (2 files)
- `persona_journey_discovery._call_llm`: reads `Retry-After` / `x-ratelimit-reset-requests` header; waits exactly that long (≤65s) then retries; falls back to DeepSeek if wait > 65s or all retries exhausted
- `llm._post_chat_with_fallback`: same logic with `_retry_after_seconds()` helper + exponential fallback
- Both sites: 4-5 retries per provider before giving up

### 4. Evidence save before analysis (runner.py)
- `evidence.save()` now called with `outcome='partial'` immediately after `run_journey_phase()`
- Overwrites with `outcome='complete'` after successful analysis
- Prevents 2h of browser work being lost to a crash in the analysis/LLM phase

### 5. Persona depth model — Phase 1 (5 behavioral fields)
- `dsl.Persona`: `tech_literacy`, `patience`, `trust_level`, `character`, `usage_context`
- `persona_journey_discovery.py`: `_PLAN_SYSTEM` and `_EXPAND_SYSTEM` describe behavioral disposition; both `format()` calls inject new fields
- `llm.SYSTEM_PROMPT`: grades friction relative to persona behavioral profile (novice label confusion = P2 not P3, etc.)
- `persona-editor-panel.tsx`: Behavioral profile section with 3 dropdowns + 2 text inputs
- Faculty config: 7 personas annotated with realistic behavioral profiles

### 6. Persona Library (new feature — full stack)
**Backend:**
- `persona_store.py`: flat-file store at `artifacts/personas.json`; CRUD with `threading.Lock`; `import_from_config()` for idempotent bulk import (ids namespaced by product slug)
- `persona_draft.draft_library_persona()`: extended AI generator producing full behavioral-depth persona; system prompt teaches novice/expert, patience, trust distinctions
- `server.py`: full CRUD REST surface (GET list, GET single, POST upsert, POST generate, POST import, DELETE)

**Frontend:**
- `LibraryPersona` type in `types.ts` — mirrors Python schema exactly
- 6 API client methods in `client.ts` with full TypeScript signatures
- 5 React Query hooks in `hooks.ts` — `usePersonaLibrary`, `useSavePersonaLibrary`, `useGeneratePersona`, `useImportPersonasFromConfig`, `useDeletePersonaLibrary`
- `$workspaceSlug.personas.tsx`: full persona library page at `/$workspaceSlug/personas`
  - AI generate panel (prompt → preview → save or copy YAML)
  - Manual editor drawer (all fields including behavioral profile)
  - Persona card grid (hover for edit/delete/copy/add-to-config)
  - Import from config dropdown (idempotent)
  - Search + tag filter bar
  - Empty state with guided CTAs
- `app-sidebar.tsx`: "Personas" nav item under Build group
- `persona-editor-panel.tsx`: "Library" button opens inline picker for personas not yet in current config

### 7. Bug fixes shipped this session
| Fix | File | Commit |
|-----|------|--------|
| `_guess_config_path` uses jobs DB → persona count → workspace.json | `analysis_export.py` | 14113bf |
| Double `JSONDecodeError` in `llm.py` crash on malformed LLM JSON | `llm.py` | 987b7cc |
| Evidence save before analysis (prevents data loss on analysis crash) | `runner.py` | 010cbce |
| NIM 429 Retry-After backoff | `llm.py`, `persona_journey_discovery.py` | 2425199 |
| LLM provider logging `[llm] nim/... 67s status=200` | `persona_journey_discovery.py` | ab4555a |
| Workspace routing scoping (compare, runs, runner, Diff button) | 6 frontend files | 67bb6d4 |
| Budget propagation floor (max_run_seconds ≥ 28800, steps ≥ 20) | `store.py` | 50eafa2 |
| Partial run salvage `_try_salvage_partial_run` | `jobs.py`, `analysis_export.py` | 50eafa2 |
| Hydration mismatch on latest run link in sidebar | `app-sidebar.tsx` | earlier |
| Subprocess timeout 3600→32400s | `jobs.py` | earlier |

---

## Files touched (this session only)

### Backend (Python)
```
launch-rehearsal/src/rehearse/dashboard/job_store.py        — config_prefix filter
launch-rehearsal/src/rehearse/dashboard/jobs.py             — propagate config_prefix
launch-rehearsal/src/rehearse/dashboard/server.py           — workspace filter + persona library API
launch-rehearsal/src/rehearse/dashboard/persona_store.py    — NEW: persona library store
launch-rehearsal/src/rehearse/dashboard/persona_draft.py    — draft_library_persona() + _LIBRARY_PERSONA_SYSTEM
launch-rehearsal/src/rehearse/dsl.py                        — Persona behavioral fields
launch-rehearsal/src/rehearse/persona_journey_discovery.py  — prompt injection + NIM retry + logging
launch-rehearsal/src/rehearse/llm.py                        — JSON crash fix + NIM retry + behavioral grading
launch-rehearsal/src/rehearse/runner.py                     — early evidence save + configId injection
launch-rehearsal/src/rehearse/analysis_export.py            — _guess_config_path improvements
```

### Frontend (TypeScript/React)
```
Frontend_V1/src/lib/mock-data/types.ts               — LibraryPersona type + RunSummary.configId
Frontend_V1/src/lib/api/client.ts                    — 6 persona library API methods
Frontend_V1/src/lib/api/hooks.ts                     — 5 persona library hooks
Frontend_V1/src/routes/$workspaceSlug.personas.tsx   — NEW: persona library page
Frontend_V1/src/routes/$workspaceSlug.dashboard.tsx  — workspace-scoped compare/runs links
Frontend_V1/src/routes/$workspaceSlug.runs.index.tsx — workspace-scoped diff link + workspaceSlug prop
Frontend_V1/src/routes/$workspaceSlug.compare.tsx    — workspace-scoped run detail links
Frontend_V1/src/routes/runs.$runId.tsx               — workspace-aware Diff button + Re-run button
Frontend_V1/src/components/app-sidebar.tsx           — Personas nav + workspace-scoped runner link
Frontend_V1/src/components/persona-editor-panel.tsx  — Library picker + behavioral profile fields
Frontend_V1/src/components/run-history-live-rows.tsx — workspaceSlug prop + scoped links
Frontend_V1/src/routeTree.gen.ts                     — auto-registered $workspaceSlug.personas
```

---

## Architecture decisions

### Persona library storage
- **Decision:** flat `artifacts/personas.json` (not a new SQLite table)
- **Why:** human-readable, git-diffable, no migration needed, consistent with other artifact files
- **Trade-off:** not suitable for >10k personas, but irrelevant at current scale

### Workspace job filtering
- **Decision:** push filter into SQLite `json_extract` rather than client-side filtering
- **Why:** client was returning all jobs from all products; breaking isolation as product list grows
- **Nuance:** prefix = full product slug (e.g. `faculty-dashboard-eight-vercel-app`) not just first word — avoids collisions when two products share a first word

### NIM 429 handling
- **Decision:** respect `Retry-After` header; fall back to DeepSeek if wait > 65s
- **Why:** NIM free tier resets per-minute; blindly sleeping 2-4s was too short; sleeping > 65s is unacceptable in parallel journey execution context
- **Nuance:** `x-ratelimit-reset-requests` header also checked (NIM uses both)

### Evidence save timing
- **Decision:** `evidence.save(outcome='partial')` immediately after `run_journey_phase()`
- **Why:** 2h run was lost because `evidence.save()` came after `run_analysis_phase()` which crashed on malformed LLM JSON. Steps only lived in memory.
- **Nuance:** `finished_at` and `duration_ms` are set twice — once for the partial save (accurate execution time), once overwritten for the final save. The analysis time is included in the final `duration_ms`.

---

## Remaining work (open issues on GitHub)

| Issue | Title | Status |
|-------|-------|--------|
| #38 Phase 2 | Adaptive Step Memory — generate→execute→observe loop | Not started |
| #41 | Per-journey video recordings (rename UUID.webm → journey_id.webm) | Not started |
| #42 | User consent modal before recording | Not started |
| #43 | OS push notifications (Web Notifications API) | Not started |

### Lower priority (flagged in audit but deferred)
- JWT in localStorage: acceptable for local-first tool on localhost; note for when deployed
- `$workspaceSlug.runs.$runId.tsx` redirect → should render in-place (currently redirects to `/runs/$runId` losing workspace scope in URL bar)
- API server-side workspace filter for `/api/summaries` is already implemented via `config_prefix`; `/api/configs` still returns all configs (no filter needed yet)

---

## Failed / discarded approaches

- **Nemotron nano 8b**: tested for journey planning, returned garbage JSON. Kept DeepSeek v4-flash as default, NIM as primary (same model via different endpoint).
- **`rebuild_bundle_from_artifacts` for run 200414**: failed first attempt because `runs/{id}.json` didn't exist (crash happened before `evidence.save()`). Fixed by writing a synthetic run JSON from screenshot filenames, then running the rebuild. Real fix was the early save in `runner.py`.
- **`_guess_config_path` by mtime**: was picking `140923.yaml` (newer mtime due to my edits) instead of `052339.yaml` (the one actually used for the run). Fixed to check jobs DB first (most authoritative), then persona count, then workspace.json.

---

## Environment notes

- **Server must be restarted** after any backend Python change — the server doesn't hot-reload
- **Active config**: `artifacts/configs/faculty-dashboard-eight-vercel-app-20260611-052339.yaml` (7 personas, 28800s budget, parallel_journeys: 2)
- **workspace.json** points to `052339.yaml`
- **REHEARSE_LLM_PRIMARY=nim** in `.env` → NIM first, DeepSeek fallback
- **LLM logging**: `[llm] nim/deepseek-v4-flash 67.3s status=200` visible in server stdout after restart

## Next recommended skill
`/code-review high` on the persona library page and `runner.py` changes before merging to main.
