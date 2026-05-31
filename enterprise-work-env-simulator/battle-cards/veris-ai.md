# Battle Card: Veris AI

*Skill: startup-competitors | Generated: 2026-05-28*

## Who they are

Commercial **agent simulation gym**: stateful mocks of Slack, Jira, email, DBs; probabilistic users; CI/CD gating; SOC2; GCP Marketplace ([veris.ai](https://veris.ai/), [$8.5M raise](https://thenewstack.io/veris-ai-is-a-training-gym-for-ai-agents/)).

## Strengths

- Production narrative: train **before** customers hit prod
- Thousands of scenarios + adversarial users
- Enterprise security story (hosted + customer K8s)
- Framework-agnostic (LangGraph, etc.)

## Weaknesses

- Focused on **agents you build**, not **third-party SaaS evaluation**
- Pricing opaque; likely long enterprise cycle
- Less emphasis on **deterministic replay** than VEI

## How to win

- Position on **“simulate customer environment to evaluate vendor X”** not “tune your agent”
- Offer **deterministic regression** contracts for procurement benchmarks
- **Complement** not replace: “Veris tests your agent; we test whether Salesforce replacement survives Acme Corp’s workflows”

## When they win

- Buyer is **ML platform team** shipping internal agents
- Needs **SOC2 + marketplace procurement** now
- Wants **RL / auto-optimization loop** out of the box

## Objections

| Objection | Response |
|-----------|----------|
| “Veris already simulates enterprise tools” | “For **your** agent’s training. We simulate **the buyer’s** heterogeneous stack to **compare vendors**.” |
| “We need SOC2 day one” | Roadmap on-prem + partner; start with vendor-side synthetic data only |

## Vulnerability

Third-party **tool selection / POC** use case is not their homepage story — own that narrative.

## Churn signals

**[Assumption]** Teams that only needed pre-launch checklist may churn after agents stabilize; you need ongoing **regression on vendor upgrades**.
