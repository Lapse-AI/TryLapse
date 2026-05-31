# TryLapse — Launch Rehearsal

[![CI](https://github.com/Lapse-AI/TryLapse/actions/workflows/ci.yml/badge.svg)](https://github.com/Lapse-AI/TryLapse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/Lapse-AI/TryLapse)](LICENSE)

Enterprise-agnostic **monitoring, feedback, and testing** for web apps before launch. Observe and score only — no auto-fix, no deploy.

**Org:** https://github.com/Lapse-AI · **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) · **Changelog:** [CHANGES.md](CHANGES.md)

## Quick start

```bash
# From repo root (loads .env)
./rehearse run -c launch-rehearsal/examples/enterprise-authenticated.yaml --llm
./rehearse serve -o launch-rehearsal/artifacts

cd Frontend_V1 && npm run dev   # → http://127.0.0.1:8081/
```

## Repository layout

| Path | Purpose |
|------|---------|
| `launch-rehearsal/` | Python CLI + agents + dashboard API |
| `Frontend_V1/` | React dashboard — **dev** at `:8081` (`npm run dev`) |
| `Frontend_Deliverable/` | Wrapper → same as `Frontend_V1` dev |
| `enterprise_work_env_simulator_2026/` | Product spec, CEO decisions, feature scope |
| `rehearse` | Repo-root wrapper script |

## UI modes

**Dev and Vision = same newest UI** at http://127.0.0.1:8081/. See [UI_PRODUCT_LINES.md](enterprise_work_env_simulator_2026/UI_PRODUCT_LINES.md).

```bash
./rehearse serve -o launch-rehearsal/artifacts
cd Frontend_V1 && npm run dev    # or npm run dev:vision — identical UI
```

## Authority docs

- [UI_PRODUCT_LINES.md](enterprise_work_env_simulator_2026/UI_PRODUCT_LINES.md) — **Vision vs Deliverable** (locked 2026-05-31)
- [FEATURE_SCOPE.md](enterprise_work_env_simulator_2026/FEATURE_SCOPE.md) — L1/L2/L3 inventory + active sprint order
- [DESIGN_PARTNER_CHECKLIST.md](enterprise_work_env_simulator_2026/DESIGN_PARTNER_CHECKLIST.md) — outreach + demo gates
- [CEO_DECISIONS.md](enterprise_work_env_simulator_2026/CEO_DECISIONS.md) — locked scope gates
- [INTERPRETABILITY.md](enterprise_work_env_simulator_2026/INTERPRETABILITY.md) — NLU narratives, compare, chat
- [BROWSER_CAPABILITY_PARITY.md](enterprise_work_env_simulator_2026/BROWSER_CAPABILITY_PARITY.md) — Phase A/B shipped; Phase C roadmap

## Development workflow (GitHub Flow)

1. Branch from `main`: `feat/…`, `fix/…`, or `chore/…`
2. Open a PR — CI runs Python tests + Frontend build
3. Squash merge to `main`
4. Release: bump `launch-rehearsal/pyproject.toml` version, update `CHANGES.md`, tag `v*.*.*`

See [CONTRIBUTING.md](CONTRIBUTING.md) for full conventions.

## Organization

https://github.com/Lapse-AI/TryLapse
