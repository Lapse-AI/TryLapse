# Launch Rehearsal (Phase 1)

Enterprise-agnostic E2E **monitoring & feedback** CLI. Crawls, executes journeys, runs multi-agent analysis, emits scorecards — **does not modify the target product**.

## Setup

```bash
cd launch-rehearsal
python -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium
```

**Two terminals?** `rehearse` is only installed inside `launch-rehearsal/.venv`. Other venvs (e.g. `.venv-research` at repo root) will show `command not found`.

| Where you are | How to run |
|---------------|------------|
| `launch-rehearsal/` + `source .venv/bin/activate` | `rehearse serve -o artifacts` |
| `TryLapse/` (any venv) | `./rehearse serve` or `launch-rehearsal/.venv/bin/rehearse serve -o launch-rehearsal/artifacts` |

## Commands

```bash
# Full pipeline: crawl → workflows → journeys → persona agents → scorecard
rehearse run -c examples/cal-com-phase0.yaml -o artifacts

# Crawl only (sitemap + workflow detection)
rehearse crawl -c examples/enterprise-saas.yaml -o artifacts

# Skip crawl
rehearse run -c examples/cal-com-phase0.yaml --no-crawl

# LLM-enhanced persona analysis (optional)
export OPENAI_API_KEY=sk-...
rehearse run -c examples/cal-com-phase0.yaml --llm --no-crawl

# Authenticated
export REHEARSE_EMAIL=... REHEARSE_PASSWORD=...
rehearse run -c examples/enterprise-authenticated.yaml -o artifacts

# Local monitoring dashboard
rehearse serve -o artifacts
# → http://127.0.0.1:8765

# Compare two runs
rehearse diff cal-20260529-192901 cal-20260529-193724 -o artifacts
```

## Multi-agent pipeline

| Phase | Agent | Output |
|-------|-------|--------|
| 1 | **Crawler** | Sitemap JSON/Markdown, hub/orphan/auth-gated pages |
| 2 | **Workflow** | Pattern detection, auto-journey supplementation |
| 3 | **Journey runner** | E2E steps, screenshots, step evidence |
| 4 | **Persona agents** (×3) | Per-lens journey grades + findings |
| 4b | **LLM persona agents** (optional) | Natural-language, evidence-bound issues/delights |
| 5 | **Synthesizer** | Unified scorecard, readiness, deduped issues/delights |

## Outputs

| Path | Content |
|------|---------|
| `artifacts/scorecards/<run_id>-scorecard.md` | Full report |
| `artifacts/sitemaps/<run_id>-sitemap.md` | Crawl graph |
| `artifacts/runs/<run_id>.json` | Step evidence |
| `artifacts/artifacts/<run_id>/*.png` | Screenshots |

## Dashboard

**CLI (minimal):**

```bash
rehearse serve -o artifacts
```

**Full UI (`Frontend_V1/`):** start `rehearse serve`, then `cd Frontend_V1 && npm run dev` — proxies `/api` to port 8765. See `Frontend_V1/README.md`.

```bash
rehearse init https://your-app.com --auth -o configs/my-app.yaml
rehearse backfill -o artifacts   # rebuild analysis.json for Frontend
```

Home view: readiness per run, issue/delight counts, run history. Run detail: scorecard, step log, sitemap, screenshots, **run summary (NLU-1)**, run diff. Compare: side-by-side diff + **What changed (NLU-2)** when `DEEPSEEK_API_KEY` is set.

**Dogfood self-test:** Init → Dogfood → `lr-self.yaml`, then Runner → **Run self-test** (LLM checkbox uses repo `.env`).

## LLM analysis (optional)

Supports **DeepSeek direct API**, **NVIDIA NIM**, and any OpenAI-compatible endpoint.

**DeepSeek API** (recommended — faster than NIM free tier; loads from repo `.env`):

```bash
# .env — use api.deepseek.com model names (not NVIDIA catalog ids)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-v4-flash
# optional: DEEPSEEK_API_BASE=https://api.deepseek.com
# optional: REHEARSE_LLM_TIMEOUT_S=180  (default read timeout, was 90s)

./rehearse run -c examples/enterprise-authenticated.yaml --llm --no-crawl
```

If both `DEEPSEEK_API_KEY` and `NVIDIA_NIM_API_KEY` are set, **DeepSeek wins** (direct API).

**NVIDIA NIM** (free trial, ~40 RPM, slower reads):

```bash
NVIDIA_NIM_API_KEY=nvapi-...
NVIDIA_NIM_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=deepseek-ai/deepseek-v4-flash
```

**Generic override:** `REHEARSE_LLM_API_KEY`, `REHEARSE_LLM_BASE_URL`, `REHEARSE_LLM_MODEL`

Env precedence: `REHEARSE_LLM_*` → `DEEPSEEK_*` → `NVIDIA_*` → `OPENAI_API_KEY`. Set `REHEARSE_LLM_JSON_MODE=0` if a model rejects `response_format`. Set `REHEARSE_LLM_RETRIES=2` for timeout/429 retries.

## Config

See `examples/enterprise-saas.yaml`. Key sections: `run`, `crawl`, `auth`, `personas`, `journeys`, `budgets`.

Platform UI spec (dashboard, agents page, alerts): `../enterprise_work_env_simulator_2026/MONITORING_PLATFORM_SPEC.md`  
Interpretability (narratives, compare, chat): `../enterprise_work_env_simulator_2026/INTERPRETABILITY.md`  
Browser vs MCP parity: `../enterprise_work_env_simulator_2026/BROWSER_CAPABILITY_PARITY.md`
