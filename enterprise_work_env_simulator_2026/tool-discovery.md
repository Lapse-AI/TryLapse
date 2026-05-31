# Tool Discovery: Enterprise Work Environment Simulator Stack

*Skill: tool-discovery | Generated: 2026-05-28*

## Recommendation

**VEI (enterprise twin core) + LangGraph (orchestration) + GraphRAG ingest (Microsoft GraphRAG or custom) + optional OASIS patterns for persona swarms** — not MiroFish as monolith.

## Why this wins

- **VEI** already implements stateful Slack/Jira/SFDC mocks, contracts, benchmarks, deterministic replay ([OVERVIEW](https://github.com/strangeloopcanon/vei/blob/main/docs/OVERVIEW.md)) — months of saved engineering vs greenfield.
- **LangGraph** is production-grade for multi-step agent workflows with checkpoints — fits “manual feeding + alerts + reruns.”
- **GraphRAG** matches your stated Boeing-style strength — ingest unstructured enterprise artifacts into a world spec.
- **OASIS** only where you need **many interacting persona agents**; domain APIs still come from VEI layer.

## Compared options

| Stack | Pros | Cons |
|-------|------|------|
| **VEI + LangGraph + GraphRAG** | Closest to vision; deterministic + LLM edges | OSS integration work; VEI license clarity |
| **Veris (buy)** | SOC2, scenarios, enterprise GTM | Wrong default story (your agent gym); $$$ |
| **MiroFish fork** | Stars, graph+swarm hype | Wrong sim domain; AGPL |
| **Klavis MCP sandboxes** | Real SaaS fidelity | Not full cross-tool company world |
| **Greenfield ScreenCaptureKit-style** | Full control | Absurd scope for enterprise twin |
| **Celonis/Ikigai** | Process simulation maturity | Different buyer; not SE pre-POC |

## Trade-offs / risks

- **AGPL** on MiroFish if you embed code
- **LLM cost** for large persona swarms — mitigate with deterministic backend + sparse LLM
- **Dependency on VEI roadmap** — fork and contribute missions/verticals

## Next step

1. `vei quickstart run` locally  
2. LangGraph agent that completes one “CRM migration week” mission  
3. GraphRAG spike: ingest 50 pages of public Jira+Salesforce admin docs → world YAML  
4. Compare output to manual SE test script (calibration v0)
