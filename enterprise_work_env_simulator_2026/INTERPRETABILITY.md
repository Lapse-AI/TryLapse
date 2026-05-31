# Interpretability & natural language — Launch Rehearsal

**Date:** 2026-05-31  
**Goal:** Customers understand runs without reading raw JSON, matrix cells, or Cursor transcripts.

---

## Shipped (NLU-1)

| ID | Deliverable |
|----|-------------|
| **NLU-1a** | Template narrative on every run: executive summary, founder view, engineering view, suggested review questions |
| **NLU-1b** | Optional LLM enrichment when `DEEPSEEK_API_KEY` / `REHEARSE_LLM_API_KEY` is set (`source: llm+template`) |
| **NLU-1c** | `narrative` field on `analysis/{run_id}.json` and dashboard bundle |
| **NLU-1d** | Run detail UI: **Run summary** + **Ask about this run** (chat) on Overview |
| **NLU-1e** | `POST /api/runs/{runId}/chat` — LLM Q&A with template fallback |

---

## Shipped (NLU-2)

| ID | Deliverable |
|----|-------------|
| **NLU-2** | Compare narrative on `/api/diff` — headline, founder/eng views, verdict; LLM when key set |
| **NLU-2 UI** | Compare page **What changed** panel (`DiffPanel`); badge **AI + rules** when `source: llm+template` |
| **NLU-ops** | Runner **LLM enrichment** checkbox → `POST /api/jobs` with `llm: true`; subprocess loads repo `.env` |

## Shipped (NLU-3)

| ID | Deliverable |
|----|-------------|
| **NLU-3** | Trends narrative on `GET /api/trends` + Trends page **Trends insight** panel |

## Shipped (NLU-4)

| ID | Deliverable |
|----|-------------|
| **NLU-4** | Chat threads in `artifacts/chats/{run_id}.json`; `GET` + `POST /api/runs/{id}/chat` |

## Shipped (NLU-5)

| ID | Deliverable |
|----|-------------|
| **NLU-5** | Command-center digest — `GET /api/digest?n=7` + home panel |

## Shipped (NLU-6)

| ID | Deliverable |
|----|-------------|
| **NLU-6** | Explore steps export `exploreLog`, `exploreSummary`, `explore-{step_id}.json` artifact; bundle + Steps timeline UI |

## Roadmap

| Phase | Deliverable |
|-------|-------------|
| — | (next: landing page, partner packaging — see `LANDING_PAGE_PLAN.md`) |

---

## Usage

```bash
# Full run with LLM personas + narrative
REHEARSE_LLM_API_KEY=... ./rehearse run -c config.yaml -o artifacts --llm

# Regenerate bundle + narrative for an old run
curl -X POST http://127.0.0.1:8765/api/backfill

# Compare two runs (CLI or UI /compare?a=&b=)
rehearse diff RUN_A RUN_B -o launch-rehearsal/artifacts
curl "http://127.0.0.1:8765/api/diff?a=RUN_A&b=RUN_B"
```

Chat from UI or:

```bash
curl -X POST http://127.0.0.1:8765/api/runs/lr-self-20260531-183909/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What blocked readiness?"}'
```

---

*Observe-only: narratives interpret evidence; they do not auto-fix products.*
