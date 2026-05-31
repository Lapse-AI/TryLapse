# Synthetic Company Rehearsal Platform — NotebookLM Source Document

**Purpose:** Single consolidated source for NotebookLM (podcasts, briefings, Q&A).  
**Benchmark:** May 28, 2026  
**Owner:** Sparsh Nagpal  
**Conversation source:** Cursor agent transcript `88a9d701-ad26-40ce-8ae8-c701a71eba33`

---

## 1. What this project is (final definition)

**Synthetic Company Rehearsal** is a platform with **one shared simulation engine** and **two product lines**:

| | **Part 1 (now)** | **Part 2 (later)** |
|---|------------------|---------------------|
| **Working name** | **Launch Rehearsal** | **Deal Rehearsal** |
| **Buyer** | Founder, PM, solo builder, early eng | Solutions Engineer, Sales Engineer, FDE |
| **Pain** | “No real users yet — is my product good?” | “POC will surprise us — rehearse first” |
| **What gets evaluated** | **The builder’s own product** (web app, tool, site) | **Vendor product inside a prospect’s synthetic stack** |
| **Synthetic company** | Generic 20–100 person company using your category | Prospect-specific stack from discovery |
| **GTM** | PLG, founders, indie hackers, YC-stage | Enterprise SE teams, higher ACV |
| **When to build** | **Now** — Phase 0 through public beta | **After Part 1 proves value** — no Part 2 engineering until Part 1 PMF gate |

**One-sentence pitch (Part 1):**  
Synthetic customers try **your product** inside a fake but realistic company — before you have real users — and you get a **readiness scorecard** (journeys, UX, breaks, integration and compliance *signals*).

**Core question answered:**  
*“If I don’t have real customers, how do I know it works or what breaks?”*

**Category name ideas:** Product Rehearsal · Synthetic Beta · Pre-Customer QA

---

## 2. How we got here (conversation arc)

1. **Initial workspace name “TryLapse”** led to deep research on **macOS screen timelapse** — that path is **separate / parked** (`trylapse_screen_timelapse_mac_2026/`). It is **not** the active product.

2. **User pasted the real idea:** Enterprise agentic work environment simulator — replicate company tools/workflows, run parallel agent simulations, stress-test software like real users, compress usage patterns.

3. **Research stack run on that idea:**
   - `startup-competitors` — Veris, VEI, Demostack, MiroFish, Celonis, etc.
   - `startup-validator` — PROCEED WITH VALIDATION, wedge too broad as stated
   - `deep-research` — 10 JSON research items, full report
   - `tool-discovery` — MiroFish, VEI, LangGraph, browser automation

4. **Key research corrections:**
   - **MiroFish is NOT required** — it simulates **social/opinion dynamics**, not Slack/Jira work patterns. Use twin mocks + persona agents + browser runners instead.
   - **VEI and Veris are adjacent, not identical** — agent/twin gyms; strongest technical overlap but different positioning than “your product UX validation.”
   - Original “compress 5 years of usage” is **too broad for v1** — no engineering definition buyers trust yet.

5. **User refinement (pivot):** Pre-customer product validation is **primary**, not SE pre-POC. Easier to test: you are the ICP, any URL works, one afternoon = signal.

6. **User refinement (structure):** Two products under one platform — startups/founders first; SE/Solutions/FDE as **Part 2** long-term.

7. **User refinement (dates):** Do **not** assign calendar dates to Part 2 — label it **Part 2** and sequence it **after** Part 1 success gates only.

---

## 3. Locked benchmark decisions (May 28, 2026)

| # | Decision |
|---|----------|
| 1 | Two products, one core engine |
| 2 | **Part 1 (Launch Rehearsal) is primary** |
| 3 | **Part 2 (Deal Rehearsal) is secondary** — sequenced after Part 1, **no calendar dates** |
| 4 | Part 1 always evaluates **the builder’s own product** |
| 5 | Part 2 evaluates **vendor product in prospect’s stack** |
| 6 | Synthetic company (Slack, Jira, CRM, roles) = **context**, not the eval subject in Part 1 |
| 7 | Scope: journeys, UX/UI, functionality, integrations, compliance **signals** — not SOC2 certification |
| 8 | **MiroFish not required** |
| 9 | **v0 stack:** browser automation + LLM personas + journey scripts → scorecard |
| 10 | **First validation:** 1 URL × 3 personas × 5 journeys → readiness scorecard (manual OK) |
| 11 | **No Part 2 code** until Part 1 PMF review gate |
| 12 | Position as **rehearsal & discovery**, not “certified ready” or full PMF proof |

**Explicitly out of scope at benchmark:**

- “Compress 5 years of usage” as v1 promise  
- MiroFish as core dependency  
- Enterprise procurement as primary GTM  
- Replacing all user research or SOC2 audits  

---

## 4. Platform architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED CORE PLATFORM                      │
│  • Synthetic org model (roles, teams, policies)              │
│  • Persona agents (goals, memory, behavior)                  │
│  • Journey runner (scripted + exploratory)                   │
│  • Browser / API interaction layer                           │
│  • Scoring, severity (P0–P3), replay, export                 │
│  • Run orchestration (parallel seeds, regression)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌──────────────────────┐       ┌──────────────────────┐
│  PART 1 — Launch       │       │  PART 2 — Deal         │
│  Rehearsal             │       │  Rehearsal             │
│  (builders, now)       │       │  (SE/FDE, later)       │
└──────────────────────┘       └──────────────────────┘
```

**Feature tagging rule:** Every feature is `core` | `part_1` | `part_2` at implementation time.

---

## 5. Part 1 — Launch Rehearsal (full product spec)

### ICP

| Attribute | Detail |
|-----------|--------|
| Who | Founder, PM, design engineer, solo builder |
| Stage | Pre-launch → early beta (<50 real users) |
| Company type | B2B SaaS, dev tools, workflow products |
| Trigger | About to launch, open beta, post-release uncertainty |

### Jobs to be done

1. Discover broken journeys before users do  
2. Get structured UX/functionality feedback without recruiting betas  
3. Test integrations/workflows in plausible org context  
4. Surface compliance-style failure modes (signals only)  
5. Re-run after each release (regression rehearsal)

### Outputs (readiness scorecard)

- Journey pass/fail matrix (persona × journey)  
- Issue backlog P0–P3 with repro steps  
- UX friction notes (heuristic)  
- Integration break list (when mocks exist)  
- Compliance signal flags (audit trail gaps, role misuse, PII placement)  
- Replay links / screenshots per finding  

### Pricing hypothesis (Part 1)

| Tier | Price | Includes |
|------|-------|----------|
| Free | $0 | 1 URL, 3 journeys, 1 persona, 1 run |
| Pro | $49–99/mo | Parallel runs, full personas, scorecard export |
| Team | $199+/mo | CI on staging, shared journeys, team workspace |

### Part 1 phased roadmap (dated — Part 1 only)

| Phase | Dates | Focus | Exit criteria |
|-------|--------|--------|---------------|
| **0 — Validation** | May 28 – Jun 7, 2026 | Manual rehearsal: 1 URL, 3 personas, 5 journeys | ≥3 non-obvious issues OR clear go/no-go |
| **1 — MVP** | Jun 8 – Jul 5, 2026 | Journey engine, P0–P3 scorecard, parallel runs, light org JSON | One-command run → scorecard <30 min |
| **2 — Alpha** | Jul 6 – Sep 30, 2026 | 10 design partners, CI spike, pricing experiment | 10 WAU, ≥5 “would miss it” |
| **3 — Growth** | Oct 2026 – Jun 2027 | Integration mocks, regression rehearsal, calibration study | Paying teams or $5k MRR path; PMF gate Mar 2027 |

### Part 1 short-term goals (dated)

| ID | Target | Success metric |
|----|--------|----------------|
| G0 | Jun 7, 2026 | Manual rehearsal finds ≥3 non-obvious issues |
| G1 | Jul 5, 2026 | Repeatable pipeline, 3 comparable runs |
| G2 | Jul 26, 2026 | 5 founder interviews; ≥3 “would use before launch” |
| G3 | Aug 30, 2026 | 10 active alpha workspaces |
| G4 | Sep 30, 2026 | 50 signups, 10 weekly active runs |

### Part 1 long-term goals (dated)

| ID | Target | Success metric |
|----|--------|----------------|
| G5 | Mar 31, 2027 | 20+ paying teams OR $5k MRR (PMF gate) |
| G6 | Jun 30, 2027 | Calibration: sim vs first 10 betas overlap % |
| G9 | Jun 30, 2027 | Slack + Jira + CRM mocks in shared core |

### MVP v0 (4 weeks, builder-first)

| Week | Deliverable |
|------|-------------|
| 1 | 3 personas × 5 journeys on one URL → markdown scorecard |
| 2 | Parallel runs (3×) + P0–P3 severity rubric |
| 3 | Optional lightweight company context (roles, Slack mock JSON) |
| 4 | 5 founder interviews: “Would you run this before launch?” |

**v0 tech:** Playwright / Browser DevTools MCP + LLM personas + journey scripts (LangGraph optional).  
**v1 add:** VEI-style integration mocks if builders need “works with Jira” stories.

### Phase 0 test protocol (no platform build required)

1. Pick one URL (your product or practice SaaS)  
2. Define 3 personas: power user, confused IC, admin  
3. Define 5 journeys: signup, core action, settings, invite teammate, edge case  
4. Run automated browser passes → issue backlog with screenshots  
5. Compare to your gut — did it find non-obvious breaks?  

**Go/no-go:** Output would have been worth paying for as a founder.

---

## 6. Part 2 — Deal Rehearsal (sequenced, no calendar dates)

**Rule:** Part 2 is a **sequencing label**, not a dated roadmap. It starts only after Part 1 PMF gate (G5).

### ICP

| Attribute | Detail |
|-----------|--------|
| Who | Solutions Engineer, Sales Engineer, FDE, SE manager |
| Company | B2B SaaS vendor (~200–2000 employees) |
| Trigger | Large deal, complex integration POC, fear of surprise failure |

### Jobs to be done

1. Rehearse vendor product inside **prospect-shaped** synthetic stack  
2. Find integration and permission failures before live POC  
3. Produce deal-ready evidence for internal champions  
4. Shorten POC cycle / reduce SE firefighting  

### Outputs (deal scorecard)

- Prospect stack compatibility map  
- POC risk register (P0 blockers vs nice-to-fix)  
- Persona “day in the life” narrative for buyer  
- Comparison runs (config A vs B)  
- Optional shareable summary for AE / champion  

### Pricing hypothesis (Part 2)

| Tier | Price | Includes |
|------|-------|----------|
| Team | $499–999/mo | SE seats, template library |
| Enterprise | $5k–25k/yr or per-deal | Custom prospect worlds, SSO, on-prem |

**Do not sell Part 2 until Part 1 has calibration case studies.**

### Part 2 build sequence (order only — no dates)

1. **Gate:** Part 1 PMF signal (paying builders + calibration data)  
2. Prospect stack ingest spec (discovery notes → world YAML)  
3. SE scorecard + vertical templates (RevOps, ITSM, DevTools)  
4. Private pilot with 3 SE teams (services-assisted onboarding)  
5. Part 2 GA — separate pricing page and case studies  

**Depends on:** Part 1 credibility; optional VEI fork/partnership for deterministic twins.

**Exit criteria:** ≥1 paid SE team; ≥1 “POC would have failed without rehearsal” story.

### Part 2 long-term goals (gated, not dated)

| ID | Gate | Success metric |
|----|------|----------------|
| G7 | After Part 1 PMF | 3 SE teams in private pilot, 1 paid each |
| G8 | After G7 | $25k+ ARR from Deal Rehearsal |

---

## 7. Who is “the tool”? (critical product decision)

| | Part 1 | Part 2 |
|---|--------|--------|
| **Evaluated artifact** | Builder’s SaaS / tool / website | Vendor’s product in prospect stack |
| **Synthetic stack role** | Context (Slack, Jira noise, roles) | Primary fidelity target |
| **Buyer question** | “Is this launch-ready?” | “Will this POC fail?” |

The synthetic company is **not** the product being scored in Part 1 — it is the believable backdrop so personas use **your** UI the way a real team would.

---

## 8. What we do NOT claim

- Replacement for all user research or human taste  
- SOC2 certification or full compliance audit  
- Proof of product-market fit (only product **readiness**)  
- Production load testing or pen-test replacement  
- Guaranteed prediction of enterprise rollout failure (until calibration data exists)

---

## 9. Competitive landscape

### Part 1 alternatives (primary ICP)

| Alternative | Gap we fill |
|-------------|-------------|
| Manual dogfooding | No scale, blind spots |
| UserTesting / Maze | Real humans, slow, not full stack context |
| Playwright / CI tests | Scripted only, no persona judgment |
| Veris / VEI | Agent **training** gym, not **your product** UX validation story |
| Friends & Twitter beta | Biased, incomplete journeys |

### Adjacent / Part 2 relevant

| Player | Role | Threat |
|--------|------|--------|
| **Veris AI** | Stateful mock enterprise + persona users; $8.5M; SOC2 | High — commercial agent gym |
| **VEI** | OSS deterministic enterprise twin; Slack/Jira/CRM mocks | High — closest twin tech |
| **Demostack / MagicDemo** | Vendor demo sandboxes | Medium — POC acceleration, not full stack |
| **Celonis + Ikigai** | Process digital twins | Medium — different buyer (process intelligence) |
| **MiroFish** | Social swarm prediction (OASIS) | Low for core — architecture reference only |
| **Klavis Sandbox** | Real SaaS via MCP for agent eval | Medium — different fidelity model |

### Strategic opportunities

1. **Calibration layer** — publish sim vs beta / sim vs POC error bars  
2. **Vertical journey packs** — RevOps, ITSM, DevTools templates  
3. **Own category name** — “Product Rehearsal” / “Synthetic Beta”  
4. **Founder-first GTM** — avoid enterprise procurement until Part 2  

### Strategic risks

1. Veris/VEI commoditize simulation core without UX scorecard differentiation  
2. Scope creep into Part 2 before Part 1 proof  
3. Synthetic feedback ≠ real users (mitigate with calibration)  
4. LLM cost at scale (mitigate: deterministic steps, cache journeys)  
5. Celonis/Microsoft/SAP bundle simulation into suites  

---

## 10. Research verdicts (synthesis)

### Startup validator

- **Recommendation:** PROCEED WITH VALIDATION (not “build the platform” yet)  
- **Problem:** Strong — POC pain, agent pre-prod testing  
- **MVP framing:** Too broad as originally stated  
- **MiroFish:** Misclassified — social sim, not enterprise work twin  

### Startup competitors

- Market is **fragmented** at startup layer; **consolidating** at platform layer  
- **Winning move:** Sharp wedge, not “simulate everything”  
- **SE prospect-stack twin** and **calibration layer** are differentiation paths  

### Deep research wedge (updated)

- **PRIMARY:** Pre-customer product validation — builders evaluate **their own** product  
- **SECONDARY:** B2B SaaS SE pre-POC rehearsal  
- **MVP v0:** Browser + 3 personas + 5 flows + scorecard; no MiroFish; no full twin day one  

---

## 11. Technology choices

| Layer | v0 | v1+ |
|-------|----|-----|
| UI exercise | Playwright / Browser DevTools MCP | Same + CI integration |
| Personas | LLM agents with journey scripts | LangGraph orchestration (optional) |
| Company context | Light JSON org template | Slack/Jira webhook stubs |
| Enterprise twin | Not required | VEI-style mocks or fork |
| Parallelism | Job queue + multiple seeds | Full parallel run grid |
| MiroFish | **Do not use as core** | Optional reference only |

---

## 12. Positioning copy (ready to use)

**Headline:** Synthetic customers for your product — before you have real users.

**Positioning statement:**  
For teams shipping B2B software before they have enough real users, [Product] runs synthetic customers through your app in a fake but realistic company — and returns a readiness scorecard (UX, flows, breaks, compliance signals) without waiting for beta users.

**Part 2 headline (later):** Rehearse the POC before the POC — in the prospect’s stack.

---

## 13. Open questions

| Question | Resolve when |
|----------|----------------|
| Final platform + product names | End of Part 1 MVP |
| First dogfood URL | Phase 0 |
| Open-source core vs closed? | Part 1 alpha |
| VEI fork vs build mocks | Part 1 growth phase |
| Part 2 first vertical (RevOps vs ITSM) | First Part 2 pilots |

---

## 14. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Synthetic ≠ real users | Calibration studies; “rehearsal” framing |
| Two products too early | No Part 2 code until Part 1 PMF gate |
| Veris/VEI headline competition | Founder GTM + UX scorecard + vertical packs |
| LLM cost | Deterministic steps; journey caching |
| Wrong name | Decide by end of Part 1 MVP |

---

## 15. Repository artifact index

Upload **this file** plus any of these for deeper NotebookLM context:

| Path | Contents |
|------|----------|
| `enterprise_work_env_simulator_2026/NOTEBOOKLM_SOURCE.md` | **This document** |
| `enterprise_work_env_simulator_2026/PRODUCT.md` | Full product doc, goals, phases |
| `enterprise_work_env_simulator_2026/report.md` | Research executive summary |
| `enterprise_work_env_simulator_2026/POSITIONING.md` | One-pager |
| `enterprise_work_env_simulator_2026/results/Recommended_wedge_and_MVP_scope.json` | Machine-readable wedge |
| `enterprise-work-env-simulator/competitors-report.md` | Battle cards, pricing landscape |
| `enterprise-work-env-simulator/validation-report.md` | Market validation |
| `enterprise-work-env-simulator/intake.md` | Product intake |
| `enterprise-work-env-simulator/battle-cards/` | Veris, VEI, MiroFish |
| `trylapse_screen_timelapse_mac_2026/` | **Separate** — macOS timelapse research only |

---

## 16. Immediate next action

**Phase 0 (by Jun 7, 2026):** Provide one staging or public URL + one-sentence product description → run 3 personas × 5 journeys → readiness scorecard. If it surfaces unknown failures, proceed to Part 1 MVP build.

---

## 17. Amendment log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | May 28, 2026 | NotebookLM source created from transcript + repo artifacts |
| | | Part 2 = sequenced only, no calendar dates per user instruction |
