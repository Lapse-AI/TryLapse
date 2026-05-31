# Product Document — Synthetic Company Rehearsal Platform

**Document version:** 1.2  
**Benchmark date:** **May 28, 2026**  
**Status:** Pre-build — decisions locked at first benchmark  
**Owner:** Sparsh Nagpal  
**Working platform name:** *Synthetic Company Rehearsal* (rename TBD)

---

## 1. Benchmark snapshot (what we decided on May 28, 2026)

This section is the **source of truth** for decisions at the first benchmark. If future debates arise, defer to this unless explicitly revised with a new dated amendment.

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Two products, one core engine** | Same simulation platform; different buyers, packaging, and scorecards. |
| 2 | **Product A is primary for now** | Pre-customer validation for founders/startups — faster to build, test, and dogfood. |
| 3 | **Product B is secondary (long-term)** | Pre-POC rehearsal for SE / Solutions Eng / FDE — higher ACV after proof. |
| 4 | **The tool being evaluated (Product A)** | Always the **builder’s own product** (web app / tool / site). |
| 5 | **The tool being evaluated (Product B)** | The **vendor’s product** inside a **prospect’s synthetic stack**. |
| 6 | **Synthetic company = context** | Slack, Jira, CRM, email, roles — backdrop for realistic usage, not the main eval subject in Product A. |
| 7 | **Core value (Product A)** | Answer: *“Without real customers, how do I know it works or what breaks?”* |
| 8 | **Evaluation scope** | **End-to-end** assessment across **persona types** and **journeys** — functionality, information clarity, speed, UI/UX, adaptability, integrations, compliance **signals**, reliability, **longitudinal / heavy-use** gaps, and **documented positives** (delights, time saved, impressive moments). Not SOC2 certification. See **`EVALUATION_FRAMEWORK.md`**. |
| 9 | **MiroFish** | **Not required.** Optional reference for parallel agents only; enterprise twin via VEI-style patterns or custom mocks. |
| 10 | **v0 stack** | Browser automation + LLM personas + journey scripts → scorecard. No full enterprise twin on day one. |
| 11 | **First validation** | One URL × 3 personas × 5 journeys → readiness scorecard (can run manually before product exists). |
| 12 | **Adjacent competitors** | Veris, VEI (agent/twin gyms); UserTesting/Maze (human); Demostack (vendor demos) — see `../enterprise-work-env-simulator/`. |

**Explicitly not in scope at benchmark:**

- “Compress 5 years of usage” as a v1 promise  
- MiroFish as core dependency  
- Enterprise procurement as primary GTM  
- Replacing all user research or SOC2 audits  

---

## 2. Vision

**Vision (3-year):** Every team shipping software can **rehearse** how their product behaves in a realistic company — before real users, beta testers, or enterprise POCs — and ship with evidence, not guesswork.

**Mission (near-term):** Give builders **synthetic customers** and structured feedback when they have **no users yet**; later, give revenue teams **synthetic prospects** before live POCs.

---

## 3. Platform architecture (one engine, two products)

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED CORE PLATFORM                      │
│  • Synthetic org model (roles, teams, policies)              │
│  • Persona agents (goals, memory, behavior)                  │
│  • Journey runner (scripted + exploratory)                   │
│  • Browser / API interaction layer                           │
│  • E2E journey runner (full flows, not page-only checks)       │
│  • Multi-persona matrix + longitudinal / heavy-use modes       │
│  • Scoring by dimension (UX, speed, info, adaptability, …)   │
│  • Issue + gap + delight capture (negatives and positives)     │
│  • Replay, severity, export                                    │
│  • Run orchestration (parallel seeds, regression)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌──────────────────────┐       ┌──────────────────────┐
│  PRODUCT A (now)      │       │  PRODUCT B (later)    │
│  Launch Rehearsal       │       │  Deal Rehearsal       │
│  ─────────────────     │       │  ─────────────────     │
│  ICP: Founders, PMs,   │       │  ICP: SE, Solutions,  │
│  early-stage builders  │       │  FDE, sales eng       │
│  Evaluates: THEIR app  │       │  Evaluates: product in │
│  Context: generic      │       │  prospect stack        │
│  company template      │       │  Context: prospect-    │
│                        │       │  specific twin         │
└──────────────────────┘       └──────────────────────┘
```

### Product naming (working)

| Product | Working name | Tagline |
|---------|--------------|---------|
| **A** | **Launch Rehearsal** | *Synthetic customers for your product — before you have real users.* |
| **B** | **Deal Rehearsal** | *Rehearse the POC before the POC — in the prospect’s stack.* |
| **Platform** | **Synthetic Company Rehearsal** | Umbrella brand / company name TBD |

---

## 4. Product A — Launch Rehearsal (primary)

### 4.1 ICP

| Attribute | Detail |
|-----------|--------|
| **Who** | Founder, PM, design engineer, solo builder |
| **Stage** | Pre-launch → early beta (&lt;50 real users) |
| **Company type** | B2B SaaS, dev tools, workflow products |
| **Trigger** | About to launch, open beta, or post-release uncertainty |

### 4.2 Jobs to be done

1. **End-to-end:** Confirm the product works across full human journeys — not isolated screens  
2. **Multi-persona:** Replicate the same and different journeys across user types (new, power, admin, returner, heavy user)  
3. **Human-ready:** Information, speed, UI/UX, functionality — everything needed for real humans to succeed  
4. **Adaptability:** Surface confusion when users return after time away or when workflows change  
5. **Longitudinal:** Model issues and gaps that appear **after repeated use** (e.g. 10× in-session, simulated “100th use” veteran perspective)  
6. **Positives:** Capture what users would **love**, find **impressive**, and where the product **saves time** — not bugs-only reports  
7. Integrations and compliance **signals** in org context  
8. Re-run after each release (regression rehearsal)

*Full rubric: [`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md)*

### 4.3 Outputs (scorecard)

- **E2E persona × journey matrix** (pass / partial / fail + evidence)  
- **Dimension rollup** — functionality, information, speed, UI/UX, adaptability, integrations, compliance signals, reliability  
- **Issue backlog** (P0–P3) with repro  
- **Gaps & wishes** — what heavy/returning users feel is **missing**  
- **Delights & strengths** — loves, impressive moments, time saved (required section)  
- Integration break list (when mocks exist)  
- Replay links / screenshots per finding  

### 4.4 Pricing hypothesis (Product A)

| Tier | Price | Includes |
|------|-------|----------|
| Free | $0 | 1 product URL, 3 journeys, 1 persona, 1 run |
| Pro | $49–99/mo | Parallel runs, full personas, scorecard export |
| Team | $199+/mo | CI on staging, shared journeys, team workspace |

*Dates are targets; validate willingness to pay in Phase 1.*

---

## 5. Product B — Deal Rehearsal (secondary, long-term)

### 5.1 ICP

| Attribute | Detail |
|-----------|--------|
| **Who** | Solutions Engineer, Sales Engineer, FDE, SE manager |
| **Company** | B2B SaaS vendor (≈200–2000 employees) |
| **Trigger** | Large deal, complex integration POC, fear of surprise failure |

### 5.2 Jobs to be done

1. **E2E** rehearsal of vendor product inside **prospect-shaped** synthetic stack  
2. **Multi-persona** POC journeys (champion, admin, daily user, blocker personas)  
3. Same human dimensions as Product A: speed, UX, information, adaptability, heavy-use gaps  
4. Find integration and permission failures before live POC  
5. Document **positives** champions can cite (“impressive”, time saved) — not only risks  
6. Produce deal-ready evidence; shorten POC firefighting  

### 5.3 Outputs (deal scorecard)

- Prospect stack compatibility map  
- **Persona × journey E2E matrix** (prospect roles)  
- POC risk register (P0 blockers vs nice-to-fix)  
- **Gaps after sustained POC-style use** (what admins/users would ask for in week 2–4)  
- **Champion delights** — strengths to lead with in the deal  
- Persona-based “day in the life” narrative  
- Comparison runs (config A vs B)  
- Optional: shareable summary for AE / customer champion  

### 5.4 Pricing hypothesis (Product B)

| Tier | Price | Includes |
|------|-------|----------|
| Team | $499–999/mo | SE team seats, template library |
| Enterprise | $5k–25k/yr or per-deal | Custom prospect worlds, SSO, on-prem option |

*Do not sell until Product A has calibration case studies.*

---

## 6. Goals

### 6.1 Short-term goals (May 28 – Sep 30, 2026)

| Goal | Target date | Success metric |
|------|-------------|----------------|
| **G0** Manual rehearsal on 1 URL proves value | **Jun 7, 2026** | E2E scorecard: ≥3 non-obvious issues **and** ≥1 delight or gap-from-heavy-use insight |
| **G1** Repeatable v0 pipeline (personas + journeys) | **Jul 5, 2026** | Same URL, 3 runs, comparable output |
| **G2** 5 founder design-partner conversations | **Jul 26, 2026** | ≥3 say “would use before launch” |
| **G3** Private alpha (Product A) | **Aug 30, 2026** | 10 active workspaces |
| **G4** Public beta / waitlist launch | **Sep 30, 2026** | 50 signups, 10 weekly active runs (**CEO:** secondary to **3 would-pay** design partners) |

### 6.2 Long-term goals (Oct 2026 – Dec 2027)

| Goal | Target date | Success metric |
|------|-------------|----------------|
| **G5** Product A PMF signal | **Mar 31, 2027** | 20+ paying teams OR $5k MRR |
| **G6** Calibration study published | **Jun 30, 2027** | “Sim found X% of issues seen in first 10 betas” |
| **G7** Product B private pilot | **Sep 30, 2027** | 3 SE teams, 1 paid pilot each |
| **G8** Product B GA | **Dec 31, 2027** | $25k+ ARR from Deal Rehearsal |
| **G9** Shared core: integration twin layer | **Jun 30, 2027** | Slack + Jira + CRM mocks in core |

---

## 7. Phased roadmap (with dates)

### Phase 0 — Concept validation (manual)

**Dates:** **May 28, 2026 → Jun 7, 2026** (10 days) — **COMPLETED May 28, 2026**

| Deliverable | Detail | Status |
|-------------|--------|--------|
| Pick target URL | Cal.com (practice); re-run on your URL | Done / **redo on yours** |
| Define 3 personas + 5 journeys | `journeys/phase-0.md` | Done |
| Run manual/agent-assisted rehearsal | `results/phase0-20260528-001-scorecard.md` | Done |
| Go/no-go | `PHASE0_GO_NOGO.md` — **GO** | Done |

**Exit criteria:** Met — scorecard would be worth paying for as a founder (methodology validated).

---

### Phase 1 — Product A MVP (builder-first) — **CEO-reduced scope**

**Dates:** **Jun 8, 2026 → Jul 5, 2026** (4 weeks)  
**Authority:** [`CEO_DECISIONS.md`](CEO_DECISIONS.md) — Phase 1 OUT list overrides conflicting items below.

| Week | Dates | Focus | Deliverables |
|------|-------|-------|--------------|
| 1 | Jun 8–14 | Runner + artifacts | DSL schema, browser runner, step logs, screenshots, SSRF preflight |
| 2 | Jun 15–21 | Trust layer | Evidence-bound scorecard, P0–P3, **required** delights, 3 auto dimensions |
| 3 | Jun 22–28 | Personas + parallel | Persona agents on journeys; 3 seeds; FLAKY flag; run budgets |
| 4 | Jun 29–Jul 5 | CLI + hardening | `rehearse run`, observability fields, 3× micro-repeat friction signal |

**Tech:** Playwright or Browser DevTools MCP + LLM personas (week 3+). LangGraph optional.  
**Exit criteria:** `rehearse run` on staging URL → evidence-backed scorecard in &lt;30 min.

**Phase 1 OUT (CEO):** PLG signup, billing, GitHub CI Action, org/Slack twin, 100×/return-gap modes, full 8-dimension automation.

---

### Phase 2 — Product A alpha & design partners

**Dates:** **Jul 6, 2026 → Sep 30, 2026** (12 weeks)

| Milestone | Date | Detail |
|-----------|------|--------|
| Design partner outreach | Jul 6–20 | 10 pre-launch founders targeted |
| Alpha invites | Aug 1 | 10 workspaces |
| CI integration spike | Aug 15 | GitHub Action: run on staging deploy *(CEO: not Phase 1)* |
| Pricing experiment | Sep 1 | Pro tier to 3 design partners |
| Public beta | **Sep 30, 2026** | Landing page + waitlist |

**Exit criteria:** 10 weekly active runs; NPS or qualitative “would miss it” from ≥5 users.

---

### Phase 3 — Product A growth + core hardening

**Dates:** **Oct 1, 2026 → Jun 30, 2027** (9 months)

| Milestone | Date | Detail |
|-----------|------|--------|
| Integration mock layer (v1) | **Dec 31, 2026** | Slack/Jira webhook stubs for context |
| Heavy-use / return journeys | **Jan 31, 2027** | 10× loops + “return after 3 days” flows |
| Regression rehearsal | **Feb 28, 2027** | Compare run N vs N-1 on same journeys |
| Veteran (100×) simulation mode | **Jun 30, 2027** | Chronic gaps + delight rubric in core |
| Calibration blog / case study | **Jun 30, 2027** | Sim vs real beta findings |
| PMF review gate | **Mar 31, 2027** | Continue, pivot, or double down on B |

**Exit criteria:** Paying customers OR clear path to $5k MRR; calibration data for sales story.

---

### Phase 4 — Product B (Deal Rehearsal) build & pilot

**Dates:** **Jul 1, 2027 → Dec 31, 2027** (6 months)

| Milestone | Date | Detail |
|-----------|------|--------|
| Prospect stack ingest spec | **Jul 31, 2027** | Discovery notes → world YAML |
| SE scorecard + templates | **Aug 31, 2027** | 3 vertical packs (RevOps, ITSM, DevTools) |
| Private pilot (3 SE teams) | **Sep 30, 2027** | Services-assisted onboarding |
| Product B GA | **Dec 31, 2027** | Separate pricing page, case studies |

**Depends on:** Product A credibility + optional VEI fork/partnership for deterministic twins.

**Exit criteria:** ≥1 paid SE team; ≥1 “POC would have failed without rehearsal” story.

---

### Phase 5 — Platform scale (2028+)

**Dates:** **Jan 2028 onward** (directional)

- On-prem / VPC for regulated customers  
- Marketplace of journey packs (community + paid)  
- API for CI/CD and internal QA platforms  
- Optional: evaluate third-party tools in synthetic company (procurement module)  

---

## 8. Feature ownership matrix

Tag every feature at implementation time: `core` | `product_a` | `product_b`.

| Capability | Core | Product A | Product B |
|------------|:----:|:---------:|:---------:|
| Persona agent runtime | ✓ | | |
| Journey definition DSL | ✓ | | |
| Browser/UI runner | ✓ | | |
| E2E journey orchestration (full flows) | ✓ | | |
| Multi-persona journey matrix | ✓ | | |
| Dimension scoring (UX, speed, info, adaptability, …) | ✓ | | |
| Delight / gap / impressive capture | ✓ | | |
| Heavy-use & return-visit journey modes | ✓ | ✓ | ✓ |
| Severity + scorecard engine | ✓ | | |
| Replay / artifacts | ✓ | | |
| Generic company template (20–100 ppl) | | ✓ | |
| Launch readiness report | | ✓ | |
| PLG signup + self-serve | | ✓ | |
| Prospect stack ingest | | | ✓ |
| Deal / POC risk report | | | ✓ |
| SE team seats + templates | | | ✓ |
| Slack/Jira/SFDC twin (deep) | ✓ | share | ✓ |
| Compliance scenario packs | ✓ | ✓ | ✓ |
| Parallel run grid | ✓ | ✓ | ✓ |

---

## 9. Success metrics (by phase)

| Phase | North star | Supporting metrics |
|-------|------------|-------------------|
| 0 | **Insight quality** | # unknown issues found |
| 1 | **Repeatability** | Run success rate, time to scorecard |
| 2 | **Activation** | WAU, runs per workspace, D7 retention |
| 3 | **Revenue + calibration** | MRR, sim→beta issue overlap % |
| 4 | **SE pilot conversion** | Pilots → paid, deal cycle impact (qual) |

---

## 10. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Synthetic feedback ≠ real users | Calibration studies; label as *rehearsal* not *proof* |
| Scope creep (two products too early) | **No Product B code until Mar 2027 gate** |
| Veris/VEI commoditize core | Vertical packs + UX scorecard + founder GTM |
| LLM cost at scale | Deterministic steps where possible; cache journeys |
| Wrong product name | Pick name by end of Phase 1 |

---

## 11. Open questions (resolve by date)

| Question | Owner | Resolve by |
|----------|-------|------------|
| Final platform + product names | Sparsh | **Jul 5, 2026** |
| First dogfood URL | Sparsh | **Jun 7, 2026** |
| Open-source core vs closed? | Sparsh | **Aug 1, 2026** |
| VEI fork vs build mocks | Eng | **Dec 31, 2026** |
| Product B first vertical (RevOps vs ITSM) | Sparsh + pilots | **Jul 31, 2027** |

---

## 12. Related documents

| File | Purpose |
|------|---------|
| **`EVALUATION_FRAMEWORK.md`** | **E2E rubric: personas, dimensions, 100× use, delights** |
| `POSITIONING.md` | One-page positioning (Product A focus) |
| `report.md` | Research summary |
| `../enterprise-work-env-simulator/validation-report.md` | Market validation |
| `../enterprise-work-env-simulator/competitors-report.md` | Competitive landscape |
| `results/Recommended_wedge_and_MVP_scope.json` | Machine-readable wedge |
| **`CEO_DECISIONS.md`** | **Locked executive calls (May 28, 2026)** |

---

## 13. Amendment log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | **May 28, 2026** | Initial benchmark: two products, Product A primary, phased roadmap with dates |
| 1.1 | **May 28, 2026** | E2E + multi-persona + longitudinal/heavy-use + delights required; `EVALUATION_FRAMEWORK.md` added |
| 1.2 | **May 28, 2026** | CEO decisions: HOLD vision, REDUCE Phase 1, hard gates, build order; `CEO_DECISIONS.md` |
| 1.3 | **May 28, 2026** | Phase 0 **GO** — `phase0-20260528-001`, scorecard + `PHASE0_GO_NOGO.md` |
| 1.5 | **May 29, 2026** | Crawler + sitemap + multi-agent pipeline + `MONITORING_PLATFORM_SPEC.md` |

*To amend: add row above; do not silently edit Section 1 decisions without noting in amendment log.*

---

## CEO REVIEW REPORT

| Review | Status | Findings |
|--------|--------|----------|
| CEO Review (2026-05-28) | **clean** | Pro CEO decisions locked in `CEO_DECISIONS.md`. Approach **B**. HOLD vision + **Phase 1 REDUCTION**. |

**VERDICT:** **GO** — Phase 0 by Jun 7, then Phase 1 per CEO-reduced scope. No code before Phase 0 pass. Full framework remains north star; Jul 5 ships trust loop only.
