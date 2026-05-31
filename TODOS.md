# TODOS — Launch Rehearsal

*CEO authority: `enterprise_work_env_simulator_2026/CEO_DECISIONS.md` · Last updated: May 31, 2026*

## Hard gates

- [x] **Phase 0 complete** — May 28, 2026 (`phase0-20260528-001`) — **GO**
- [x] Phase 0 pass: ≥1 non-obvious issue + ≥1 evidence-backed delight
- [x] Re-run Phase 0 on **your** product — Argyle faculty dashboard (`phase0-argyle-20260529-001`)
- [x] Argyle extended run (`phase0-argyle-20260529-003`) — scorecards only, no target-app changes
- [x] Phase 1 scaffold started (gate cleared May 28)

## Phase 1 must-ship (by Jul 5, 2026) — CEO order

- [x] URL preflight + SSRF guardrails (`launch-rehearsal/src/rehearse/preflight.py`)
- [x] Journey DSL (URL, 3 personas, 5 E2E journeys) (`dsl.py` + `examples/`)
- [x] Browser runner + per-step logs + screenshots (`browser.py`, Playwright)
- [x] Scorecard: matrix, P0–P3 issues, **required** delights (`heuristics.py`, `scorecard.py`)
- [x] 3 auto dimensions: Functionality, UI/UX, Information clarity (heuristics)
- [x] CLI: `rehearse run` + `rehearse scorecard`
- [ ] Run budgets + named errors (`RunBudgetExceeded`, `BrowserStepTimeout`, etc.)
- [x] Persona agents + LLM layer (DeepSeek direct API)
- [x] 3 parallel seeds + FLAKY flag (`journey_agent.py`, `heuristics.py`, yaml budgets)
- [x] 3× micro-repeat friction signal (`repeat_micro_loop` in DSL; default 1, raise in yaml when needed)
- [x] Profile `open_link` href fallback (`browser.py`, j3 in `enterprise-authenticated.yaml`)
- [x] CLI: `rehearse run` | `serve` | `diff` | `init` | `backfill` | `crawl`
- [x] Dashboard API + Frontend_V1 wired (`/api/*`, `/files/*`, analysis bundle export)
- [x] Backfill analysis bundles for existing runs
- [ ] Observability: duration, cost estimate, outcome per run (partial in bundle)
- [ ] Confidence labels: `high` vs `hypothesis` on voice-of-user text (partial in heuristics)

## Explicitly OUT of Phase 1 (CEO NO)

- [ ] ~~PLG signup / billing~~ → Phase 2
- [ ] ~~GitHub Action CI~~ → Aug 2026
- [ ] ~~100× / return-after-gap~~ → 2027
- [ ] ~~Slack/Jira twin~~ → Dec 2026
- [ ] ~~Product B~~ → Mar 2027 gate
- [ ] ~~Full 8-dimension automation~~ → Phase 2 partial

## Design partner demo readiness (May 31, 2026)

*Checklist: `DESIGN_PARTNER_CHECKLIST.md` · Scope: `FEATURE_SCOPE.md` · UI: `UI_PRODUCT_LINES.md`*

- [x] Concierge + self-serve demo stack (Sprints 1–3, PRs #13–#15)
- [x] G1–G13 design partner gates ✅ (`live-2026-05-31.md`)
- [x] Dual UI modes: **Dev** (`:8081`, `npm run dev`) + **Vision reference** (`npm run dev:vision`) — `UI_PRODUCT_LINES.md`
- [ ] List 10 warm targets + send 5 intros (`DESIGN_PARTNER_CHECKLIST.md`)

## Phase 2+ (unchanged targets)

- [ ] 5 founder design partners — **3 would-pay** by Sep 30, 2026 (`DESIGN_PARTNER_CHECKLIST.md`)
- [ ] Public beta / waitlist — Sep 30, 2026
- [ ] Open-source decision — Aug 1, 2026 (default **closed** until then)
- [ ] VEI fork vs mocks — Dec 31, 2026
- [ ] Calibration study (G6) — Jun 30, 2027
- [ ] Product B — no work before Mar 31, 2027

## This week (CEO calendar)

- [x] Write `journeys/phase-0.md`
- [x] Run Phase 0 manual rehearsal + scorecard
- [x] Go/no-go — **GO** (`PHASE0_GO_NOGO.md`)
- [x] Pick **your** dogfood URL — Argyle faculty dashboard (`enterprise-authenticated.yaml`)
- [x] Phase 1 scaffold (`launch-rehearsal/`) — preflight + DSL + CLI `rehearse run --dry-run`
- [x] Wire Frontend_V1 to live API + backfill analysis bundles
- [x] Publish `FEATURE_SCOPE.md` (L1/L2/L3)
- [x] Update `DESIGN_PARTNER_CHECKLIST.md` with demo gates + live stack
- [x] Document Vision vs Deliverable UI (`UI_PRODUCT_LINES.md`)
- [ ] Design partner outreach: 10 targets, 5 intros, 2 booked calls
