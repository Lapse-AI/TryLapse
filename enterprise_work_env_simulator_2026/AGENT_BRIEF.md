# Agent brief — Launch Rehearsal (partner-ready)

**Last updated:** 2026-05-31  
**Use this file:** `@enterprise_work_env_simulator_2026/AGENT_BRIEF.md` at the start of any design, partner-prep, or `/design-review` agent session.

---

## Status in one sentence

**Concierge + self-serve partner demos are ready** on `main` (Sprints 1–3 + Phase 1 tail merged); **marketing/PLG is not** until **3 would-pay** design partners (Sep 30, 2026).

---

## What is DONE (do not re-plan)

| Area | Evidence |
|------|----------|
| **Sprint 1** — export, compare, evidence repro | PR [#13](https://github.com/Lapse-AI/TryLapse/pull/13) |
| **Sprint 2** — live KPIs, workflows, annotations, delights | PR [#13](https://github.com/Lapse-AI/TryLapse/pull/13) |
| **Sprint 3** — init writes YAML, retire Acme when API live, Linear export stub | PR [#14](https://github.com/Lapse-AI/TryLapse/pull/14) |
| **Phase 1 tail** — named errors, `costEstimate`, observability in bundle | PR [#15](https://github.com/Lapse-AI/TryLapse/pull/15) |
| **Design review (live stack)** | **8.2 / 10** — see design review doc below |
| **Post-review UI fixes (Batch A+B)** | `main` @ `7a940f0` — readiness explainer, compare JSON collapsed, init URL default, flaky alignment, cost labels, Lovable badge hidden |
| **Partner gates G1–G13** | All ✅ in checklist below |

---

## Authority order (when docs disagree)

1. **`DESIGN_PARTNER_CHECKLIST.md`** — gates, demo flow, outreach, what not to show  
2. **`.cursor/gstack/launch-rehearsal/design-reviews/live-2026-05-31.md`** — rendered UI truth (scores, routes, partner script)  
3. **`FEATURE_SCOPE.md` §0 + §1** — what shipped vs **deferred later**  
4. **`CEO_DECISIONS.md`** — observe-only, pricing gate, expansions adopted  
5. **`MONITORING_PLATFORM_SPEC.md`** — product principles and Phase boundaries  
6. **`BROWSER_CAPABILITY_PARITY.md`** — what browser powers must live in Rehearsal (not Cursor MCP) for customers  
7. **`MONITORING_PLATFORM_DESIGN.md`** — IA / command-center spec (target layout)  
8. **`CHANGES.md`** (repo root) — engineering changelog only  

---

## Must-read doc index

| Role | Path |
|------|------|
| **Partner calls (primary)** | `DESIGN_PARTNER_CHECKLIST.md` |
| **Design review result** | `.cursor/gstack/launch-rehearsal/design-reviews/live-2026-05-31.md` |
| **Sprint / L2 inventory** | `FEATURE_SCOPE.md` |
| **CEO guardrails** | `CEO_DECISIONS.md` |
| **Observe-only spec** | `MONITORING_PLATFORM_SPEC.md` |
| **Browser parity (vs MCP)** | `BROWSER_CAPABILITY_PARITY.md` |
| **UI / IA spec** | `MONITORING_PLATFORM_DESIGN.md` |
| **Positioning** | `PRODUCT.md` |
| **Dev vs Vision UI lines** | `UI_PRODUCT_LINES.md` |
| **Prior review (superseded)** | `.cursor/gstack/launch-rehearsal/design-reviews/live-2026-05-29.md` |

---

## North star (record on every partner call)

> **“Would you run this before every launch?”**

Secondary: *“Would you pay ~$49/mo for this on every release?”* — yes / no / maybe.

---

## Live demo stack

```bash
# Terminal 1 — API + artifacts
./rehearse serve -o launch-rehearsal/artifacts

# Terminal 2 — Dashboard (proxies /api, /files → :8765)
cd Frontend_V1 && npm run dev
# → http://localhost:8081
```

**Canonical demo runs (API live):**

- `argyle-20260531-000517` — Argyle faculty, Green, crawl + matrix (preferred hero)  
- `enterprise-20260530-234231` — enterprise example scorecard  

**Never use when API is up:** mock `run_8s7d2` (404 / breaks trust).

**If UI shows Acme mock data:** restart `./rehearse serve` — API was down.

---

## 20-minute demo flow (design partner)

1. `/` — Command center (live KPIs, latest run)  
2. `/runs/argyle-20260531-000517` — Matrix → issue → **Evidence** → Agree/Disagree  
3. `/compare?a=argyle-20260530-235656&b=argyle-20260531-000517` — Red → Green, new/resolved issues  
4. `/recommendations` — Export to Linear (markdown download)  
5. `/init` — Generate & write YAML (self-serve onboarding)  
6. `/agents` — Agent trace; Compliance/Performance **idle** (honest Phase 2)  

Say **Phase 2** for: trends recurrence/calendar mock, full Linear OAuth, cron, SSO, PLG.

---

## `/design-review` skill workflow

1. Read `MONITORING_PLATFORM_DESIGN.md` and this brief.  
2. Open **http://localhost:8081** with stack above (Browser DevTools MCP only).  
3. Score rendered UI 0–10; compare to `live-2026-05-31.md`.  
4. Save new reports: `.cursor/gstack/launch-rehearsal/design-reviews/live-{YYYY-MM-DD}.md`  
5. Do **not** treat Lovable preview URLs or `run_8s7d2` as current truth.

---

## Do NOT promise (FEATURE_SCOPE §1)

PLG signup, billing, usage metering, Slack/Jira OAuth integrations, scheduled cron, SSO, journey marketplace, GitHub CI product, Product B — until **3 would-pay** partners unless CEO explicitly pulls forward.

---

## Human-only track (not an agent task)

Fill **“Next 10 outreach targets”** in `DESIGN_PARTNER_CHECKLIST.md` and run the outreach sequence there. Engineering readiness does not replace intros.

---

## Copy-paste agent system prompt

```text
You are preparing or reviewing Launch Rehearsal for B2B design partner calls.

Read @enterprise_work_env_simulator_2026/AGENT_BRIEF.md first, then DESIGN_PARTNER_CHECKLIST.md and live-2026-05-31 design review.

Assume Sprints 1–3 and Phase 1 tail are DONE on main. Do not reopen finished L2 items unless the user reports a regression.

Stay observe-only (CEO_DECISIONS). Defer FEATURE_SCOPE §1 items.

For UI work: verify on localhost:8081 with rehearse serve, demo runs argyle-20260531-000517 or enterprise-20260530-234231.
```

---

## Repo

https://github.com/Lapse-AI/TryLapse (private) · default branch `main`
