# TryLapse — Launch Rehearsal

Enterprise-agnostic **monitoring, feedback, and testing** for web apps before launch. Observe and score only — no auto-fix, no deploy.

## Quick start

```bash
# From repo root (loads .env)
./rehearse run -c launch-rehearsal/examples/enterprise-authenticated.yaml --llm
./rehearse serve -o launch-rehearsal/artifacts

cd Frontend_V1 && npm run dev
```

## Repository layout

| Path | Purpose |
|------|---------|
| `launch-rehearsal/` | Python CLI + agents + dashboard API |
| `Frontend_V1/` | React dashboard (proxies `/api` → `:8765`) |
| `enterprise_work_env_simulator_2026/` | Product spec, CEO decisions, feature scope |
| `rehearse` | Repo-root wrapper script |

## Authority docs

- [FEATURE_SCOPE.md](enterprise_work_env_simulator_2026/FEATURE_SCOPE.md) — L1/L2/L3 inventory + active sprint order
- [DESIGN_PARTNER_CHECKLIST.md](enterprise_work_env_simulator_2026/DESIGN_PARTNER_CHECKLIST.md) — outreach + demo gates
- [CEO_DECISIONS.md](enterprise_work_env_simulator_2026/CEO_DECISIONS.md) — locked scope gates

## Organization

https://github.com/Lapse-AI
