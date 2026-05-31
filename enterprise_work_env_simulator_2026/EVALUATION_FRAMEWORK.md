# Evaluation Framework — End-to-End Human Experience Assessment

**Applies to:** Product A (Launch Rehearsal) and Product B (Deal Rehearsal)  
**Benchmark:** May 28, 2026 (amended)  
**Principle:** Every run is **end-to-end** — not a page checklist. Personas complete real goals; the system judges **whether everything a human needs is in order**, including what only shows up after repeated use.

---

## 1. What “end-to-end” means here

A rehearsal run is **E2E** when it includes:

1. **Entry** — discovery, signup, login, invite, permissions  
2. **Core value** — the jobs users actually bought the product for  
3. **Ongoing use** — return visits, settings, search, notifications, errors, recovery  
4. **Edge & stress** — bad input, empty states, role changes, integration failures  
5. **Exit / handoff** — export, billing, downgrade, support path (if applicable)

Each step is exercised **in the browser (or API+UI)** the way a human would — not isolated component tests.

---

## 2. Persona × journey matrix (required)

Every assessment **must** replicate journeys across **multiple user types**. No single “happy path” counts as a full run.

### Default persona set (minimum 3; recommend 5–7)

| Persona | What they stress |
|---------|------------------|
| **First-time user** | Clarity, onboarding, fear of breaking things |
| **Daily power user** | Speed, shortcuts, density, muscle memory |
| **Occasional returner** | “I forgot how this works” — adaptability, wayfinding |
| **Admin / owner** | Permissions, billing, team, security settings |
| **Skeptical buyer** | Trust, missing info, “where’s the proof?” |
| **Stressed user** | Errors, timeouts, partial failures, support need |
| **Heavy user (100×)** | See §4 — chronic fatigue, gaps, delights |

### Journey types (minimum 5 per product; expand per vertical)

| Journey | E2E intent |
|---------|------------|
| First success | Zero → first value in one session |
| Team expand | Invite + collaborate |
| Configure | Settings that affect daily use |
| Recover | Mistake → fix without support |
| Integrate | Connect external tool (when mocks exist) |
| Return after gap | Simulated “3 days later” session |
| Power loop | Same task 10× in one run (micro repetition) |

**Output:** Persona × journey **pass / partial / fail** matrix with evidence.

---

## 3. Assessment dimensions (everything humans care about)

Each finding is tagged with one or more dimensions. Scorecards summarize per dimension.

### 3.1 Functionality & correctness

- Features work as implied by UI copy and docs  
- Data persists; actions are reversible where expected  
- Error messages match actual failure  
- Integrations sync and fail gracefully  

### 3.2 Information & clarity

- Users always know **where they are**, **what happened**, and **what to do next**  
- Labels, empty states, and help text sufficient for persona  
- No “information holes” (missing status, ambiguous permissions)  

### 3.3 Speed & performance (perceived)

- Time-to-first-value  
- Interaction latency (clicks, saves, search)  
- Perceived slowness on heavy flows — **not** lab benchmarks only; persona **complains** if too slow  

### 3.4 UI / UX

- Layout, hierarchy, consistency  
- Click cost / steps to complete jobs  
- Mobile or narrow viewport (if relevant)  
- Accessibility **signals** (focus order, contrast flags — not full WCAG audit in v1)  

### 3.5 Adaptability & learnability

- Can a user return after a week and succeed?  
- Does the product **teach** or **punish** forgetting?  
- Settings discoverability; consistent patterns across modules  
- “Migration” within product (old UI vs new, feature flags)  

### 3.6 Integrations & workflow fit

- Works in context of synthetic company (Slack ping → action in app, etc. when modeled)  
- Handoffs between tools feel coherent  

### 3.7 Compliance & trust **signals**

- Role misuse scenarios; audit trail presence  
- PII handling UX; consent flows  
- **Not** a SOC2 report — “would an admin worry here?”  

### 3.8 Reliability over a session

- Flakes, double submits, stale UI, lost work  
- Recovery after refresh or back button  

---

## 4. Longitudinal layer — “after 100 uses”

First-session bugs are not enough. The platform simulates **sustained use** so chronic issues and delights surface.

### Simulation modes

| Mode | What it models | When |
|------|----------------|------|
| **Day 1** | Onboarding + first wins | Every run (baseline) |
| **Week 1** | Return visits, mild habituation | Phase 1+ |
| **Heavy session** | Same workflows repeated 10–20× in one run | Phase 1+ |
| **Simulated tenure** | Agent memory: “I’ve done this 100 times” + rubric for veteran complaints | Phase 3+ |
| **Regression** | Same journeys after release N vs N-1 | Phase 3+ |

### What “100× user” feedback captures

**Issues (chronic):**

- Repetitive friction (“every time I export I need 4 clicks”)  
- Missing bulk / batch / automation  
- Notification fatigue or silence  
- Search/find breaks at scale  
- Features they **expected** by now and still lack  
- Workarounds they invented in-session (sign of product gap)  

**Positives (delight):**

- “This saved me a lot of time” — **with evidence** (steps before/after)  
- Moments that feel **impressive** (speed, clarity, clever defaults)  
- Features they **love** and would defend  
- Would recommend to colleague in synthetic org  

Persona agents emit structured **Voice-of-user** snippets (quotes grounded in replay steps), tagged `issue` | `gap` | `delight` | `impressive`.

---

## 5. Scorecard structure (both products)

Every run produces:

### A. Executive summary

- Overall readiness: Red / Amber / Green (per product rubric)  
- Top 3 blockers · Top 3 delights  
- Persona coverage: % journeys attempted × passed  

### B. Persona × journey matrix

(see §2)

### C. Dimension rollup

| Dimension | Score 1–5 | Top finding |
|-----------|-----------|-------------|
| Functionality | | |
| Information | | |
| Speed | | |
| UI/UX | | |
| Adaptability | | |
| Integrations | | |
| Compliance signals | | |
| Reliability | | |

### D. Issue backlog

- P0–P3 with repro, persona, journey, dimension  

### E. Gaps & wishes (chronic / veteran user)

- “After heavy use, users would wish for…”  
- Prioritized by frequency across personas  

### F. Delights & strengths

- **Must include positives** — not only bugs  
- “Users would love…” · “Impressive because…” · “Saves time when…”  

### G. Evidence

- Replay links, screenshots, step logs per finding  

---

## 6. Product-specific emphasis

| Dimension | Product A (Launch) | Product B (Deal) |
|-----------|-------------------|------------------|
| E2E scope | Full product journeys | Product **inside prospect stack** |
| Personas | Builder’s target users | Prospect org roles (IT, ops, champion) |
| Delights | Launch messaging, PLG conversion | POC confidence, champion quotes |
| 100× layer | Retention & expansion features | Admin + daily ops during POC window |
| Success | Ship-ready without betas | POC won’t embarrass SE |

---

## 7. Phase rollout (what ships when)

| Capability | Phase 0 (Jun 7) | Phase 1 (Jul 5) | Phase 3 (2027) |
|------------|-----------------|-----------------|----------------|
| E2E journeys | Manual | Automated | Automated |
| 3+ personas | ✓ | ✓ | 5–7 |
| Dimension tags | Ad hoc | Rubric v1 | Full rollup |
| Delight / gap sections | Manual | Structured | Structured |
| Heavy / repeat session | Manual | 10× loop | 100× tenure mode |
| Return-after-gap journey | Optional | ✓ | ✓ |

---

## 8. Honesty bounds

- Synthetic users **approximate** human judgment; calibrate against real users over time.  
- “Users would love” is **hypothesis** until validated — label confidence.  
- Speed scores mix observed timing + persona narrative.  
- Positives are **first-class** — a report with only bugs is incomplete.

---

*Parent doc: `PRODUCT.md` · Amendment 1.1 (May 28, 2026)*
