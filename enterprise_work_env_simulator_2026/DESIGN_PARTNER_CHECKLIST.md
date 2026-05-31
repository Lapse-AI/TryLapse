# Design partner outreach — Phase 1 checklist

*Authority: `CEO_DECISIONS.md` · Target: **3 would-pay** design partners by Sep 30, 2026*  
*Last updated: 2026-05-31 · Scope: `FEATURE_SCOPE.md` · UI review: `.cursor/gstack/launch-rehearsal/design-reviews/live-2026-05-29-followup.md`*

---

## North star question

> **“Would you run this before every launch?”**

Record verbatim answers. Secondary: *“Would you pay ~$49/mo for this on every release?”*

---

## ICP (who to recruit)

- Engineering or product leader at a **B2B SaaS** team shipping weekly
- Already runs manual dogfood, UAT, or “launch rehearsal” before releases
- Pain: regressions caught late, persona-blind QA, no evidence bundle for stakeholders
- **Not yet:** enterprise SE leaders, compliance-heavy regulated buyers (Phase 3+)

---

## Offer (what they get)

- **Free** Launch Rehearsal runs on their staging URL (observe/score only — no code changes)
- Markdown scorecard + artifact bundle (screenshots, step log, crawl sitemap when enabled)
- Live dashboard walkthrough: persona × journey matrix, P1–P3 issues, delights, agent trace
- 30-minute readout with evidence drill-down (screenshot + step_id + repro notes)

**CEO guardrails to state upfront:** no auto-fix, no deploy, no code changes — observe and score only (`MONITORING_PLATFORM_SPEC.md`).

---

## Demo readiness gates (must pass before first external call)

| Gate | Status | Notes |
|------|--------|-------|
| **G1** Trust loop: evidence opens with screenshot + step_id | ✅ | Design review DR-01–03 fixed; real screenshots via `/files/` when API live |
| **G2** Readiness band consistent with P0/P1 count | ✅ | Backend heuristics + bundle export; avoid Acme mock when API up |
| **G3** Real runs in dashboard (not mock-only) | ✅ | 13+ enterprise runs backfilled; `./rehearse serve` + Frontend_V1 |
| **G4** Run detail matrix interactive | ✅ | Cells open journey dialog |
| **G5** CLI produces repeatable scorecard in &lt;30 min | ✅ | Phase 1 pipeline shipped |
| **G6** Dogfood scorecard attachable | ✅ | Argyle + enterprise scorecards in `launch-rehearsal/artifacts/scorecards/` |
| **G7** Mobile nav usable | ✅ | Hamburger sheet (DR-07) |
| **G8** Honest Phase 2 scope (Compliance/Performance idle) | ✅ | Agents page shows idle placeholders |
| **G9** Export / Diff / Compare fully functional | ✅ | Sprint 1 shipped in PR #13 — export, compare, evidence repro |
| **G10** Command-center KPIs from live data | ✅ | Sprint 2 — home KPIs wired from live run/bundle data (PR #13) |
| **G11** Init wizard writes config from UI | ✅ | Sprint 3 merged (PR #14) — `POST /api/configs` + Init wizard button |
| **G12** Lovable badge removed in production build | ✅ | CSS hides dev tagger; verify on share |
| **G13** Design review pass (live stack) | ✅ | `.cursor/gstack/launch-rehearsal/design-reviews/live-2026-05-31.md` — 8.2/10 partner-ready |

**Verdict (2026-05-31):** **Concierge + self-serve onboarding ready** (export, compare, KPIs, init wizard, Linear backlog download). **Marketing/PLG** still gated per `CEO_DECISIONS.md` (3 would-pay partners first).

---

## L2 gaps to close before self-serve (optional for concierge)

Priority order from `FEATURE_SCOPE.md`:

| ID | Item | Why it matters for partners |
|----|------|----------------------------|
| L2-UI-12 | Annotation agree/disagree UI ✅ | False-positive feedback loop |
| L2-UI-17 | Compare run selectors wired ✅ | “What changed since last release?” |
| L2-UI-08–09 | Export artifact download ✅ | Async handoff after call |
| L2-UI-50 | Export to Linear ✅ | Markdown download stub (full OAuth later) |
| L2-UI-29–30 | Workflows from live bundle ✅ | Credibility on crawl-derived coverage |
| L2-UI-52 | Delights from latest run ✅ | Home page delight parity |
| L2-UI-01–04 | Command-center KPIs from API ✅ | Trust in aggregate metrics |
| L2-UI-63 | Init wizard writes YAML ✅ | Partner self-onboarding (PR #14) |

---

## Live demo stack (use this on calls)

```bash
# Terminal 1 — API + artifact serving
./rehearse serve -o launch-rehearsal/artifacts

# Terminal 2 — Frontend (proxies /api and /files → :8765)
cd Frontend_V1 && npm run dev
# → http://localhost:8081
```

**Demo flow (20 min):**

1. **Command center** (`/`) — latest run readiness, blockers, top delight
2. **Run detail** (`/runs/enterprise-20260530-234231`) — matrix → click fail cell → issues → **Evidence** dialog
3. **Agents** (`/agents`) — collaboration trace, persona agents, idle Phase 2 agents
4. **Site map** (`/sitemap?run=…`) — hub/leaf/orphan taxonomy
5. **Trends** (`/trends`) — readiness over time (note: recurrence/calendar still mock — say “Phase 2”)
6. **Runner** (`/runner`) — trigger run live if partner shares staging URL on call

**Do not demo:** Acme mock run `run_8s7d2` when API is live (404). Pick a real `enterprise-*` or `argyle-*` run_id from `/runs`.

**Fallback:** If API down, UI falls back to mock Acme data — restart `./rehearse serve` before any call.

---

## Outreach sequence

1. **Warm intro** (YC network, former colleagues, design-partner Slack) — **10 names**
2. **Email / DM template** (personalize first line):
   - Problem: “We score your staging app like three personas would, with evidence, in ~10 minutes.”
   - Ask: staging URL + test credentials + one critical journey (login → core workflow)
   - CTA: 30-min call + async run before the call
3. **Preflight** — `./rehearse run --dry-run -c <their-config.yaml>` or POST `/api/preflight`
4. **Run** — `./rehearse run -c <their-config.yaml> --llm` (concierge; you operate)
5. **Deliver** — scorecard markdown + dashboard link (local or deployed) + optional GraphML sitemap
6. **Close loop** — north star question + would-pay at ~$49/mo (record yes/no/maybe)

### Email snippet

```
Subject: Pre-launch scorecard for [Product] staging — 30 min?

We run your staging URL through three persona lenses (admin / operator / evaluator),
capture screenshots + step evidence, and produce a readiness scorecard in ~10 minutes.
No code changes — observe and score only.

If you can share staging URL + test login + one critical journey, I'll run it async
before a 30-min walkthrough of findings.

Worth a look before your next release?
```

---

## Qualification (would-pay bar)

| Signal | Pass |
|--------|------|
| Shares staging creds without heavy legal delay | ✓ |
| Names a **release blocker** from the scorecard | ✓ |
| Asks for **weekly** or **per-PR** runs | ✓ |
| Introduces second stakeholder (EM or PM) | ✓ |
| Replays evidence dialog unprompted (“show me that screenshot again”) | ✓ |

**Scoring:** Strong yes = 3+ signals. Maybe = 1–2. No = no staging access or “nice demo, not our workflow.”

---

## Artifacts to attach (pre-call or follow-up)

| Artifact | Path |
|----------|------|
| Latest Argyle dogfood scorecard | `launch-rehearsal/artifacts/scorecards/argyle-20260531-000517-scorecard.md` |
| Enterprise example scorecard | `launch-rehearsal/artifacts/scorecards/enterprise-20260530-234231-scorecard.md` |
| Product positioning | `PRODUCT.md` |
| CEO scope guard | `MONITORING_PLATFORM_SPEC.md` |
| Feature scope (internal) | `FEATURE_SCOPE.md` |

---


## Next 10 outreach targets

| Company | Contact | Status | Next action |
|---------|---------|--------|-------------|
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

## Partner tracking (target: 5 conversations → 3 would-pay)

| # | Company | Contact | Role | Intro sent | Call booked | Run ID | North star | Would-pay? | Notes |
|---|---------|---------|------|------------|-------------|--------|------------|------------|-------|
| 1 | | | | | | | | | |
| 2 | | | | | | | | | |
| 3 | | | | | | | | | |
| 4 | | | | | | | | | |
| 5 | | | | | | | | | |

**Funnel targets (Sep 30, 2026):**

| Stage | Target |
|-------|--------|
| Warm list | 10 |
| Intros sent | 5 |
| Calls booked | 3 |
| Runs completed | 3 |
| Would-pay (verbal) | **3** |

---

## Pre-outreach checklist (this week)

- [ ] Confirm demo stack: `./rehearse serve` + Frontend_V1 on `localhost:8081`
- [ ] Walk demo flow once end-to-end (matrix → evidence → agents)
- [ ] Attach Argyle + enterprise scorecards to outreach template
- [ ] List **10 warm targets** (name, company, mutual connection)
- [ ] Send **5 personalized intros**
- [ ] Book **2 calls** with staging-access commitment
- [ ] Prepare partner config template from `./rehearse init <url> --auth` output
- [ ] Dismiss Lovable badge / use production build for screen share

---

## Post-call capture

For each partner, log in tracking table + optional note file `results/design-partner-{company}-{date}.md`:

- Staging URL (redact in git — local only)
- Run ID produced
- Top blocker they reacted to (quote if possible)
- Top delight they reacted to
- North star answer (verbatim)
- Would-pay answer
- Objections (security, false positives, coverage, price)
- Follow-up action (second run, intro to EM, wait until G9 export)

---

## Related docs

| Doc | Purpose |
|-----|---------|
| `CEO_DECISIONS.md` | Authority, gates, would-pay metric |
| `FEATURE_SCOPE.md` | L1/L2/L3 — what’s real vs mock |
| `PRODUCT.md` | Positioning, timeline |
| `MONITORING_PLATFORM_SPEC.md` | Phase boundaries |
| `TODOS.md` | Engineering gates vs partner gates |
| `design-reviews/live-2026-05-29-followup.md` | UI trust-loop verification |
