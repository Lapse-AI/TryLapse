# TODOS — Launch Rehearsal

*CEO authority: `enterprise_work_env_simulator_2026/CEO_DECISIONS.md` · Last updated: June 18, 2026*

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
- [x] Run budgets + named errors (`RunBudgetExceeded`, `BrowserStepTimeout`, etc.)
- [x] Persona agents + LLM layer (DeepSeek direct API)
- [x] 3 parallel seeds + FLAKY flag (`journey_agent.py`, `heuristics.py`, yaml budgets)
- [x] 3× micro-repeat friction signal (`repeat_micro_loop` in DSL; default 1, raise in yaml when needed)
- [x] Profile `open_link` href fallback (`browser.py`, j3 in `enterprise-authenticated.yaml`)
- [x] CLI: `rehearse run` | `serve` | `diff` | `init` | `backfill` | `crawl`
- [x] Dashboard API + Frontend_V1 wired (`/api/*`, `/files/*`, analysis bundle export)
- [x] Backfill analysis bundles for existing runs
- [x] Observability: duration, cost estimate, outcome per run (bundle + run detail panel)
- [x] Confidence labels: `high` vs `hypothesis` on issues and delights (heuristics + UI chips)

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
- [ ] List 10 warm targets + send 5 intros — see `DESIGN_PARTNER_OUTREACH.md`

## Engineering — next up (June 2026)

### Deploy
- [ ] **Railway** — connect TryLapse repo, set env vars, verify demo dashboard live (try off-peak: after 8 PM PT)
- [ ] **Fresh demo run** — re-run argyle or enterprise config so dashboard shows current-date evidence

### Scoring quality (dimension scores)
- [x] **Onboarding score** — auth outcome + first-journey pass rate + onboarding-path detection + error-free first journey (`analysis_export.py:_expand_dimensions`)
- [x] **Recovery score** — error_steps + net_failures + error_phrases + HTTP 4xx/5xx + retry-success reward (`analysis_export.py:_expand_dimensions`)
- [x] **Information score** — avg body length + heading density + link density + sparse-page count; orphan-path penalty (`heuristics.py:_score_dimensions`)
- [x] **Accessibility score** — unlabeled buttons + unlabeled inputs + missing alt text + low-contrast estimate (`analysis_export.py:_expand_dimensions`)
- [x] **UI label honesty** — all dimensions set `automated=True`; frontend shows "Automated from step evidence" for real signals, "Estimated — signal pending" for fallback (`dimension-rollup.tsx:35`)

### Wave 2 Track B — remaining
- [x] ~~L3-PRED-09 — Directional lift card on experiment page~~ (PR #22)
- [x] ~~L3-PRED-03 — Cohort rehearsal (N seeds, confidence band)~~ (PR #22)
- [x] ~~L3-PRED-07 — Step behavior signals (abandon/hesitate/continue)~~ (PR #22)
- [x] **L3-PRED-07 funnel** — `FunnelPanel` component in `run-detail.tsx` groups steps by journey, computes pass/partial/fail rates per step position, integrates behavioralJourneys friction scores; placed in `runs.$runId.tsx`
- [x] **L3-PRED-09 lift card on Compare page** — guard changed from `scoreA > 0 && scoreB > 0` to `summaryA ?? summaryB`; LiftCard shows whenever either run has a summary
- [x] **Cohort sidebar link** — cohort-mode jobs in Run history link to `/cohort/$jobId` with orange "cohort" chip badge (`run-history-live-rows.tsx`)

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

---

## Engineering Excellence — Board Mandates

*Source: Full board session with Andrej Karpathy, John Carmack, Steve Jobs, Paul Graham — June 17, 2026.*
*Standard: every task below must be reviewed by the designated reviewer before merge. No exceptions.*
*Reviewers: Karpathy = AI/ML correctness · Carmack = architecture/code quality · Jobs = product experience · Graham = customer validation*

---

### A. Karpathy Audit — Five Subsystems

#### A1. Crawler — Route Coverage, Not Just Route Visiting

**Problem:** The crawler follows links. That is not the same as covering the app. Parameterised routes (`/users/:id`, `/products/:slug`) are discovered as one instance; the template is what matters. State-dependent routes — pages that only appear after a specific action sequence (post-purchase confirmation, onboarding step 3, empty-state zero-data screens) — are never reached from the homepage. JS-only navigation (`router.push('/checkout')` inside a click handler) leaves no `<a href>` for the crawler to find. Soft auth redirects (200 + login page instead of 401) cause auth detection to misclassify entire route subtrees. XHR interception is absent — the network calls reveal what the backend actually does, which is different from what frontend links expose.

**Required work:**
- [ ] **Route template deduplication** — embed page content (headings, landmark structure, form fields) with a sentence-transformer. Routes with cosine similarity > 0.85 are the same template. Only test one instance. Report: "tested 12 unique templates across 47 discovered routes."
- [ ] **State-dependent route discovery** — after each journey step, re-scan the route graph. New routes that appeared = state-dependent. Add them to the crawl queue with the action sequence that reveals them.
- [ ] **XHR-based route supplementation** — intercept all network requests during crawl. Extract API endpoints. Cross-reference with route graph. Endpoints with no frontend route are dark paths worth testing.
- [ ] **Graph coverage metric** — replace "N routes visited" with "X% of reachable app graph covered." Show the uncovered subgraphs explicitly. This is the metric Karpathy actually cares about.
- [ ] **Soft-redirect auth detection** — if a navigation lands on a page containing a login form (detected by `<form>` with password field), mark the route as auth-gated regardless of HTTP status code.
- [ ] **Parameterized route recognition** — detect `:id`, `:slug`, `[param]` patterns in discovered URLs. Store as template, not instance. Test with synthetic valid IDs drawn from prior crawl responses.

**Reviewer:** Karpathy — must confirm coverage metric is real, not cosmetic.
**Files:** `launch-rehearsal/src/rehearse/crawler.py`, new `route_graph.py`

---

#### A2. Flake Rate — From 17.6% to Under 3%

**Problem:** 17.6% flake rate makes findings untrustworthy. The root causes, in order of contribution: (1) fixed `waitForTimeout` calls instead of condition-based waits — element exists in DOM but is not yet interactive; (2) external dependencies — analytics, CDN fonts, third-party chat widgets — are non-deterministic and timeout unpredictably; (3) CSS animation/transition interference — click fires while element is mid-transition, lands on wrong target; (4) state pollution — browser context not fully isolated between persona runs, cookies and localStorage from persona 1 leak into persona 2; (5) network variability from real external APIs (Stripe, Auth0) in the test environment.

**Required work:**
- [x] **Animation freeze injection** — `_ANIMATION_FREEZE_CSS` injected via `add_init_script` on every page (`setup_page_for_run`) + `add_style_tag` after every navigate (`_inject_animation_freeze`). Kills transitions/animations/scroll-behavior. (`browser.py:22-115`)
- [x] **Third-party request interception** — `_ANALYTICS_BLOCK_PATTERNS` (16 origins: segment, intercom, hotjar, fullstory, GTM, GA, mixpanel, amplitude, heap, clarity, sentry, datadog, logrocket) aborted via `context.route` in `_block_analytics_routes`. Called on every context creation. (`browser.py:35-90`)
- [x] **Full context isolation** — `BrowserSession.reset_context_for_persona()` destroys and recreates context between personas in sequential mode. Parallel mode already had per-worker contexts. (`browser.py`, `journey_agent.py:execute`)
- [x] **Replace all fixed waits** — audited `browser.py`: the only `wait_for_timeout` at line 738 is a DSL `sleep` action (user-configured intentional wait). All event-driven waits use `wait_for_load_state`/`wait_for_selector`. No arbitrary fixed waits in journey runner.
- [x] **Three-run confirmation gate** — `flake_rate` field added to `StepSnapshot`. `_mark_flaky_steps` computes fail fraction per seed position. `add_issue` skips findings with `flake_rate < 2/3` (non-reproducible noise); downgrades severity for reproducible flakes (≥2/3). (`evidence.py`, `journey_agent.py`, `heuristics.py`)
- [x] **Per-finding-type flake telemetry** — `flakeBreakdown` dict added to run bundle summary in `analysis_export.py`. Keyed by dimension (auth, checkout, forms, navigation), each entry has `{count, rate}` relative to total flaky steps. (`analysis_export.py:1161-1170`, `summary.flakeBreakdown`)
- [x] **Flake rate dashboard metric** — `get_trends()` in `dashboard/store.py` computes real `flakeRate` from run bundles. Dashboard shows 7-day trailing flake % with tone gates (≤2%=ready, ≤5%=warn, >5%=danger). Trends page shows sparkline. All real data, no mock fallback needed. (`dashboard/store.py:469`, `$workspaceSlug.dashboard.tsx:110`, `$workspaceSlug.trends.tsx:19`)

**Target:** ≤3% flake rate before any public launch. No exceptions.
**Reviewer:** Carmack — verify state isolation is complete, no shared mutable context.
**Files:** `launch-rehearsal/src/rehearse/browser.py`, `journey_agent.py`

---

#### A3. Persona Agents — Five New Personas + Behavioral Fidelity Ceiling

**Problem:** Current personas are system prompts. "You are an iOS Safari user on slow 3G with thumb navigation" describes a user; it does not simulate one. A prompted LLM navigates like a developer pretending to be a user. It finds bugs that are obvious to any observer. It misses the bugs that real confused users find — the misunderstood IA, the form field everyone abandons at the same step, the navigation path a new user takes that no developer anticipated.

**Ceiling of prompt personas (documented):** They catch ~60% of surface-level UX bugs. They structurally miss: rage-click patterns after failed actions, cognitive model mismatches (user expects save button top-right, it's bottom-left), form abandonment at specific fields, the exact navigation path a lost new user takes.

**Required new personas:**
- [x] **Keyboard-only user** — `keyboard_only: bool` on Persona. Click actions use `focus()+Enter` instead of mouse. Focus-visible JS check fires after focus; P1 filed (structural, WCAG 2.4.7) if outline/box-shadow is `0px`/`none`. (`browser.py:799`, `heuristics.py:keyboard-only: focus not visible`)
- [x] **Frustrated/rage user** — `rage_mode: bool` field on `Persona` dataclass and YAML config. After a click step fails with error phrases in DOM, `_rage_retry()` fires 3× rapid retries (100ms gap). P0 filed if duplicate-submission language detected; P2 filed if no loading state prevented re-submission. (`dsl.py:80`, `browser.py:_rage_retry`, `heuristics.py:322-341`)
- [x] **Intermittent connection user** — `network_throttle: "offline_intermittent"` on Persona. After each `fill` step, `_offline_blip()` calls `context.set_offline(True)` for 1.5s then reconnects. Checks for offline indicator in DOM; P2 filed if absent. Locale support also wired: `reset_context_for_persona` accepts `persona_locale`, propagated from journey agent on persona switch. (`browser.py:_offline_blip`, `heuristics.py:322`, `journey_agent.py:534`)
- [x] **Screen reader user** — `screen_reader: bool` on Persona. Click/fill use `_resolve_locator_by_aria()` (get_by_label → get_by_role → get_by_text → fallback). P1 (structural) filed when ARIA resolution fails; P2 filed for no-accessible-name match. ARIA live region check fires P2 when error phrases present but no `role=alert/status/log` in tree. (`browser.py:_resolve_locator_by_aria`, `heuristics.py:_aria_has_live_region`)
- [x] **International user** — `locale` field on Persona now fully wired: `reset_context_for_persona(persona_locale=...)` sets `context.locale` + `Accept-Language` header. Journey agent resets context when locale changes (including first persona with non-default locale). RTL heuristic fires P2 (hypothesis) if locale is Arabic/Hebrew/Farsi and page has LTR direction hints. (`browser.py:reset_context_for_persona`, `journey_agent.py:523`, `heuristics.py:RTL_LOCALES`)

**Future direction (12-18 months):** Fine-tune behavioral navigation models on real user session recordings (FullStory/LogRocket exports labeled by persona type). Train on sequences of `(DOM_state, user_action)` pairs. This produces behavioral fidelity that prompt personas cannot achieve. Build the data collection infrastructure now even if the model comes later.

**Reviewer:** Karpathy — verify each persona produces qualitatively different navigation paths from the base personas.
**Files:** `launch-rehearsal/src/rehearse/personas/`, new persona yaml configs

---

#### A4. Journey Runner — Complete Evidence Chain

**Problem:** The current evidence chain (screenshots, DOM snapshots, network events, Web Vitals) misses the signals that reveal the most bugs. JavaScript console errors are the first symptom of broken components — uncaught exceptions and promise rejections appear before any visual failure. Video recording is absent, meaning findings are described with static screenshots instead of showing exactly what the user saw. The accessibility tree is never captured, so a11y bugs are invisible. DOM state between steps is never diffed, so regressions are described in text rather than shown as structural changes.

**Required additions to evidence chain:**
- [x] **JavaScript console error capture** — `page.on('console')` + `page.on('pageerror')` handlers; `console_errors` field on `StepSnapshot`; heuristic fires P2 on uncaught JS errors (`browser.py`, `evidence.py`, `heuristics.py`)
- [ ] **Full Playwright trace per run** — enable `context.tracing.start(screenshots=True, snapshots=True, sources=True)`. Stop and export at run end. The trace file is the ground-truth artifact: timeline of every action, every network request, every DOM snapshot. Screenshots become a summary derived from the trace, not the primary artifact.
- [x] **Video recording per journey** — `record_video=True` on `BrowserSession`; `record_video_dir` on context creation; video path stored in `evidence.video_paths`; attached to P0/P1 findings via narrative layer
- [x] **Accessibility tree snapshot per step** — `_compact_aria_tree()` already captured to artifact file per step. Now also stored in `StepSnapshot.aria_snapshot` (in-memory dict) for heuristic access. Used by screen-reader persona and live-region check. (`browser.py:927`, `evidence.py:aria_snapshot`)
- [x] **DOM diff between steps** — MD5 fingerprint via `StepSnapshot.dom_hash`; `_analyze_dom_stagnation` fires P2 when interactive action leaves DOM hash unchanged. (`browser.py:_dom_fingerprint`, `heuristics.py:_analyze_dom_stagnation`)
- [x] **Storage state capture per step** — `_capture_storage_keys()` captures localStorage+sessionStorage key names after navigate/click/fill/select. Stored in `StepSnapshot.storage_keys`. `_analyze_storage_continuity` fires P0 (hypothesis) when auth-pattern keys vanish mid-journey. (`browser.py:_capture_storage_keys`, `heuristics.py:_analyze_storage_continuity`)
- [x] **Network response body capture** — POST/PUT/PATCH responses with 2xx status captured (≤10KB); `silent_api_failures` field on `StepSnapshot`; silent-failure heuristic fires P1 when success=false body detected (`browser.py`, `evidence.py`, `heuristics.py`)
- [x] **Resource timing breakdown** — `_collect_resource_timing()` calls `performance.getEntriesByType('resource')` after navigate steps; top 10 slowest stored in `StepSnapshot.resource_timing`. P2 filed when any resource >2s. (`browser.py:_collect_resource_timing`, `heuristics.py:resource_timing`)

**Reviewer:** Karpathy — verify evidence chain is complete; Carmack — verify no I/O performance cliff from simultaneous capture streams.
**Files:** `launch-rehearsal/src/rehearse/browser.py`, `evidence.py` (new)

---

#### A5. Synthesizer — Deterministic Where Possible, Learning Where Necessary

**Problem:** The synthesizer uses an LLM for work that should be deterministic (severity scoring, deduplication) and doesn't use a learning loop for work that requires it (severity calibration from real outcomes). Same inputs produce different outputs on different runs — unacceptable for a testing tool. The 8 axes are a hypothesis, not empirically derived. There is no cross-run memory. There is no statistical baseline.

**Required work:**
- [ ] **Embedding-based deduplication** — replace LLM-based dedup with sentence-transformer embeddings. Embed every finding. Cosine similarity > 0.85 = same bug. Deterministic, fast, reproducible. LLM is used only to write the merged description after dedup. Recommended model: `all-MiniLM-L6-v2` (fast, good quality, 384-dim).
- [ ] **Deterministic severity scoring** — severity assignment (P0/P1/P2/P3) should be deterministic code, not LLM judgment. Define a severity decision tree: P0 = journey-blocking failure with evidence; P1 = journey completes with significant defect; P2 = non-blocking with evidence; P3 = observation. LLM writes the severity explanation; it does not determine the severity.
- [ ] **Statistical baseline scoring** — each product's metric history is the baseline. "LCP is 4.2s" is uninformative. "LCP is 3.2 standard deviations above your 90-day average" is actionable. Implement z-score comparison for all numeric metrics. First run: no baseline, report absolute values. Subsequent runs: report delta from historical mean.
- [ ] **Cross-run delta computation** — given run N and run N-1, compute: new findings (appeared this run), resolved findings (gone this run), score delta per axis, new P0s. Surface this as the primary view for returning users. The question they're asking is "what changed?" not "what is the current state?"
- [ ] **Severity calibration feedback loop** — add a `finding_outcome` field to the data model: `acted_on | dismissed | false_positive | deferred`. Build a UI affordance for developers to label findings. This is training data for future severity calibration. Instrument from day one even if the model comes in 6 months.
- [ ] **Causal clustering** — group findings by likely root cause. "Checkout form fails on submit" + "Payment confirmation page never loads" + "Order ID missing from confirmation email" are three symptoms of one root cause. Cluster by: same page, same journey step range, correlated appearance/disappearance across runs.
- [ ] **Streaming synthesis** — begin synthesizing persona 1's findings as soon as persona 1 completes. Do not wait for all 4 personas. Users see partial results in ~2 minutes instead of waiting 4m42s. Use a streaming API pattern: emit findings as they're produced, update the readiness band as new findings arrive.

**Missing from synthesizer entirely:**
- [x] **Passive security surface scan** — `security.py` runs after crawl phase; checks CSP, mixed content, exposed globals (`window.__ENV__` etc.), cookie flags; results flow into synthesizer via `AgentReport` mechanism (`security.py`, `orchestrator.py`)
- [ ] **SEO health signals** — missing `<meta description>`, duplicate `<title>` tags, broken canonical links, `noindex` on pages that should be indexed, missing `alt` on images. File as P2 findings.
- [ ] **Cookie consent compliance detection** — if a GDPR/CCPA consent banner blocks the journey runner from proceeding, that is itself a compliance signal worth filing as a P1 (blocks user journeys).

**Reviewer:** Karpathy — verify dedup embedding approach; Carmack — verify deterministic/LLM boundary is clean.
**Files:** `launch-rehearsal/src/rehearse/synthesizer.py`, new `embeddings.py`, `delta.py`

---

### B. Carmack Audit — Architecture and Code Quality

#### B1. Run Transaction Model — Atomic State or Nothing

**Problem (Carmack's diagnosis):** A large fraction of software flaws come from not fully understanding all possible states the code executes in. TryLapse's state space is enormous: browser state × application state × network state × LLM response state × filesystem state. Every subsystem touches shared state. The crawler writes to disk. The journey runner reads what the crawler wrote. The synthesizer reads what the journey runner wrote. When the journey runner fails halfway through, what is the state? There is almost certainly no transaction model — files are written partially, runs are half-complete with no recovery path, and the synthesizer processes whatever it finds on disk, producing corrupt output that looks like a valid result.

**Required work:**
- [x] **Phase sub-states surfaced in jobs API** *(partial B1)* — `dashboard/server.py` enriches running jobs with `phase`, `completed_journeys`, `total_journeys`, `total_personas` from progress JSON files; frontend now shows live phase during runs
- [x] **Explicit run state machine** — `RunStateMachine` in `run_manager.py`: QUEUED→CRAWLING→RUNNING→SYNTHESIZING→COMPLETE, any →FAILED. Transitions validated, logged with timestamps to `runs/{run_id}-state.json` via atomic write. Context manager auto-fails on exception. Wired into `runner.py` at each phase boundary. 7 tests in `test_run_manager.py` (106 total passing). (`run_manager.py`, `runner.py`)
- [x] **Atomic run writes** — `RunEvidence.save()` writes `.tmp.json` then `tmp.replace(out)` (atomic POSIX rename). State file uses `_atomic_write()` with `os.replace`. (`evidence.py:83-84`, `run_manager.py:_atomic_write`)
- [x] **Run state persistence** — `runs/{run_id}-state.json` written at each transition. `recover_stale()` marks non-terminal runs as FAILED on server restart; called in `serve_dashboard()`. (`run_manager.py:recover_stale`, `dashboard/server.py:1789`)
- [x] **State machine owner** — `RunStateMachine` is the single owner of `*-state.json`. No other module writes run state. (`run_manager.py`)
- [ ] **Pre-run cleanup** — before starting a run, verify no temp artifacts exist from a prior failed run. If they do, clean them up atomically before starting.

**Reviewer:** Carmack — verify state machine is complete and no partial states are observable externally.
**Files:** `launch-rehearsal/src/rehearse/run_manager.py` (new), `state_machine.py` (new)

---

#### B2. State Isolation — Destroy, Not Clear

**Problem:** Browser context is shared or improperly reset between persona runs. Cookies, localStorage, cached API responses, and service worker state from persona 1 bleed into persona 2. This is not a corner case — it is the primary source of the 17.6% flake rate and of findings that are artifacts of test ordering rather than real bugs.

**Required work:**
- [ ] **Context-per-persona rule** — each persona gets a fresh `browser.new_context()`. Never reuse a context between personas. Never call `clear_cookies()` as a substitute for context recreation.
- [x] **Service worker isolation** — `"service_workers": "block"` added to context_opts in both `BrowserSession.__enter__` and `_ThreadSession` parallel workers (`browser.py`, `journey_agent.py`)
- [ ] **Context destruction verification** — after `context.close()`, assert that no pages from that context are still attached. Log context lifetime (created_at, closed_at, pages_opened).
- [ ] **Network request completion guard** — before closing a context, wait for all in-flight network requests to complete or timeout. In-flight requests from persona N completing during persona N+1 context init causes state bleed.

**Reviewer:** Carmack — verify zero shared mutable state between persona runs.
**Files:** `browser.py`, `context_manager.py` (new)

---

#### B3. Deterministic Synthesizer — The LLM Boundary

**Problem (Carmack's principle):** The overriding purpose of software is to be useful, not correct — but a testing tool that produces different results for the same inputs on different runs is neither. Running the synthesizer twice on the same findings must produce the same score, the same severity assignments, the same deduplication. LLMs are in the loop for deterministic calculations, making them probabilistic. This is wrong.

**The correct LLM boundary:**

| Should be deterministic code | Should use LLM |
|---|---|
| Severity score calculation | Human-readable finding description |
| 8-axis score computation | Situation report narrative |
| P0 → Amber/Red band assignment | Plain-English explanation of why P0 |
| Deduplication (embedding similarity) | Merged description after dedup |
| Regression detection (run delta) | Trend narrative for non-technical users |

- [ ] **Audit every LLM call in synthesizer.py** — for each call, ask: "Would it be embarrassing if this returned a different answer on a second run?" If yes, replace with deterministic code.
- [ ] **Deterministic severity decision tree** — implement as a pure function: `classify_severity(finding: Finding) -> Severity`. Given finding type, evidence count, journey impact, reproduction count → deterministic severity. No LLM.
- [x] **Reproducible run output** — `tests/test_determinism.py` added; 3 tests: identical output across two calls, stability with flaky steps, unique issue titles; 99 tests total passing (`heuristics.py` is the deterministic path under test)

**Reviewer:** Carmack — run the reproducibility test. Verify it passes.
**Files:** `synthesizer.py`, `severity.py` (new)

---

#### B4. Performance Cliffs — Fix Before They Hit

**Problem:** Five hidden performance cliffs will become production incidents as run volume grows. All are predictable from the current architecture.

- [x] **LLM call tracking** *(observability prerequisite)* — thread-safe counter in `llm.py` (`_llm_lock`, `_llm_call_count`); `reset_llm_call_count()` called at run start; final count stored in `evidence.phase_timings["llm_calls"]` (`llm.py`, `runner.py`)
- [ ] **LLM serial latency** — currently: 4 personas × 10 steps × 1 LLM call per step = 40 serial LLM calls at ~2s each = 80s minimum LLM wait, not counting browser time. Fix: collect all step observations per persona, make one synthesis call per persona at journey end. Target: ≤4 LLM calls per run regardless of journey length.
- [ ] **Screenshot disk I/O** — 4 personas × 10 steps × 1 PNG each = 40+ screenshots at ~1.5MB each = ~60MB per run. On runs with many steps, this is the actual bottleneck. Fix: capture as WebP (4× smaller), write async via `asyncio.to_thread`, never block the browser on disk I/O.
- [ ] **Browser process memory leak** — long-running Playwright browser processes accumulate memory from V8 heap snapshots, cached frames, and unreleased page objects. Fix: restart browser process between personas (not just context). Add memory usage assertion: browser process RSS must be < 500MB at persona start.
- [ ] **O(n²) deduplication** — if finding dedup is pairwise LLM comparison, 100 findings = 4,950 comparisons. Acceptable at current scale; catastrophic at 10×. Fix: embedding-based dedup (see A5) is O(n) embed + O(n²) matrix multiply, which numpy does in milliseconds for n < 1000.
- [ ] **Synthesizer blocking on full run** — synthesizer waits for all 4 personas to complete before starting. First result visible at 4m42s. Fix: streaming synthesis. As each persona completes, emit findings immediately. Readiness band updates live as findings arrive.

**Reviewer:** Carmack — measure actual runtime breakdown before and after each fix. No fix is accepted without before/after timing data.
**Files:** `journey_agent.py`, `synthesizer.py`, `browser.py`

---

### C. Missing Angles — Uncovered by Current Architecture

*These are not future features. They are gaps in the current product that make it less complete than it should be at launch.*

- [x] **C1: JavaScript console error capture** — `page.on('console')` + `page.on('pageerror')` in `BrowserSession`; stored in `StepSnapshot.console_errors`; P2 heuristic fires on uncaught JS errors
- [x] **C2: Video recording per journey** — `record_video=True` flag on `BrowserSession`; clips stored in `evidence.video_paths`; attached to findings via narrative layer
- [x] **C3: Passive security surface scan** — `rehearse/security.py`; 4 checks (CSP, mixed content, exposed globals, cookie flags); runs post-crawl via `AgentReport` in `orchestrator.py`
- [x] **C4: DOM diff between steps** — MD5 fingerprint of element counts + title + ARIA role count stored in `StepSnapshot.dom_hash`; stagnation heuristic fires P2 when interaction action leaves DOM hash unchanged (`browser.py`, `heuristics.py`)
- [x] **C5: Cross-run regression detection** — `_detect_regressions()` in `synthesizer.py`; compares P0/P1 findings against most recent prior bundle using `_is_duplicate()` semantic dedup; prepends `[Regression]` annotation and stores count in `ctx.metadata`
- [ ] **C6: Keyboard-only navigation persona** — see A3. Tab order, focus management, modal traps. Catches a11y blockers.
- [ ] **C7: Offline/reconnect persona** — see A3. State recovery, form persistence, error handling under network loss.
- [x] **C8: API response body capture** — POST/PUT/PATCH 2xx responses body-captured (≤10KB) in `_on_response()`; stored in `StepSnapshot.silent_api_failures`; P1 heuristic fires on `"success":false` pattern (`browser.py`, `heuristics.py`)
- [ ] **C9: Streaming synthesis** — see A5. First findings visible in ~2 minutes, not after full run completes.
- [ ] **C10: Three-run confirmation** — see A2. Required to achieve <3% flake rate.

---

### D. Non-Technical Verdict UX — Design Mandates

*Source: Steve Jobs board session. Standard: a non-technical founder must understand the verdict in under 3 seconds. A PM must be able to forward findings to a developer without translation. Every layer below is required, not optional.*

#### D1: Layer 1 — The Verdict

**Design requirement:** The top of every report is a single sentence in 48px+ font with a colour-coded indicator. No score. No percentage. A sentence.

```
🔴  Don't launch yet.
    One thing will cost you real users tonight.
```
```
🟡  Almost ready.
    Fix these two things first, then you're clear.
```
```
🟢  You're clear to launch.
    Two minor things for next sprint.
```

**Rules:**
- If any P0 finding exists: verdict is always "Don't launch yet." regardless of composite score. Non-negotiable.
- If P1 findings exist and no P0: "Almost ready." with the count of P1s.
- If only P2/P3: "You're clear." with the count of lower-priority observations.
- The verdict sentence is human-written by the synthesizer's LLM call — not templated. It should read like a senior engineer wrote it.
- No score visible on this layer. Score lives behind a "see full scorecard" disclosure.

**Implementation tasks:**
- [x] Verdict component at top of run detail page (`VerdictBanner` in `run-detail.tsx`, shown in `runs.$runId.tsx`)
- [x] Verdict logic: P0 presence → always red, regardless of axis scores (in `narrative.py` `build_template_narrative`)
- [x] LLM-generated verdict sentence (template baseline; LLM overlay via `generate_run_narrative_llm`)
- [ ] Verdict visible in email/Slack notification without clicking through

**Reviewer:** Steve Jobs — does a non-technical founder understand this without explanation?

---

#### D2: Layer 2 — The Story

**Design requirement:** Every P0 finding is presented as a user story, not a technical report entry. The story format is:

> *"We sent someone like [persona description] through [journey name]. [What they did]. [What happened]. [What they experienced as a consequence]."*

Example P0:
> *"We sent a first-time customer on an iPhone through checkout. She spent 4 minutes filling in her details, chose her shipping option, and hit Pay. The button greyed out. Nothing happened. No error. No confirmation. She tried again. Same result. She left."*

Below the story: the 20-second video clip (autoplay, muted, looped). This is the single most important evidence artifact.

Below the video: one technical line for the developer: `POST /api/checkout returns 500 on mobile Safari when card field contains trailing space.`

**Rules:**
- Story is LLM-generated from evidence. Prompt must constrain: no technical jargon, first-person user perspective, concrete actions and concrete consequences.
- Video is mandatory for P0. P1 findings get video if available.
- Technical line is a separate collapsed section for developers. Not visible by default to non-technical users.
- Persona description is human: "a first-time customer on an iPhone" not "mobile-user persona."

**Implementation tasks:**
- [x] Story generation prompt in synthesizer — `layer2Story` built in `narrative.py`; persona human labels in `personaLabel()` (`run-detail.tsx`)
- [x] Video player component embedded in finding card (`FindingStoryCard` with `<video autoPlay muted loop controls>`)
- [x] Technical details section collapsed by default (`<details>` in `FindingStoryCard`)
- [x] Persona descriptions mapped to human-readable labels (`personaLabel()` in `run-detail.tsx`)

**Reviewer:** Steve Jobs — read the generated story out loud. Would a non-technical founder feel the urgency?

---

#### D3: Layer 3 — The Fix Hierarchy

**Design requirement:** Three sections only, with exactly these labels. No P0/P1/P2/P3 labels visible to non-technical users.

```
Fix before you launch    (1–3 items max)
Fix this week            (up to 10 items)
On the radar             (collapsed by default, everything else)
```

**Rules:**
- P0 findings → "Fix before you launch"
- P1 findings → "Fix this week"
- P2/P3 findings → "On the radar" (collapsed)
- If "Fix before you launch" has more than 3 items: group related items and count them as one. A checkout flow with 4 P0 symptoms is one P0 problem.
- Developer view (togglable): shows P0/P1/P2/P3 labels, technical evidence, DOM paths.
- Non-technical view (default): shows story format, video, plain-English description.

**Implementation tasks:**
- [x] Three-section layout for findings in run detail (`FixHierarchyPanel` in `run-detail.tsx`, replaces flat filtered list in `runs.$runId.tsx`)
- [ ] Grouping logic: cluster findings by causal proximity (same journey, same page, same step range) for "Fix before you launch" section
- [x] View toggle: "Founder view" / "Developer view" — persisted in localStorage
- [x] "On the radar" section collapsed by default, count visible (e.g. "12 lower-priority observations")

**Reviewer:** Steve Jobs — can a PM read this report and immediately know what to ask a developer to fix?

---

#### D4: Layer 4 — The Forward

**Design requirement:** Every report has a "Share with team" action that generates a pre-written message a founder or PM can send via Slack, email, or linear without editing it.

Generated message format:
```
Subject: TryLapse found [N] things before launch — [verdict]

[Verdict sentence from Layer 1]

Critical (fix before launch):
• [P0 finding 1 — one sentence, human language]
  → [20-second video link]

Fix this week:
• [P1 finding 1 — one sentence]
• [P1 finding 2 — one sentence]

Full report: [link to run]
Run by TryLapse on [date] — [run duration] · [persona count] personas tested
```

**Rules:**
- Message is LLM-generated from run findings. One prompt per run. Review before send.
- Video links are direct CDN links — always work without login for P0 findings (public video, private everything else).
- Message should read like a senior QA engineer wrote it, not like a tool generated it.
- Slack format, email format, and Linear issue body format are three separate templates.

**Implementation tasks:**
- [x] "Share report" button on run detail page (`ShareReportDialog` in `run-detail.tsx`; button shown alongside VerdictBanner)
- [x] Format selector: Slack / Email (template-generated from `layer1Verdict` + P0/P1 issues + `layer4Forward`)
- [ ] LLM-generated message per format (one additional LLM call per run)
- [ ] P0 video links are publicly accessible without auth (time-limited signed URL, 7 days)
- [x] Copy to clipboard button

**Reviewer:** Steve Jobs — would a founder forward this without editing it?

---

#### D5: Layer 5 — The Trend

**Design requirement:** For returning users (any run after the first), the primary view is not the current state — it's the delta. Progress is more motivating and more informative than absolute score.

```
Last 7 runs         ● ● ● ● ● ● ●  (dots coloured by band)
Score today         78 → 84   (+6 from Tuesday)
Blockers            2 → 0     (resolved ✓)
New observations    +3         (appeared this run)
```

**Rules:**
- Delta view is default for run N+1 and beyond. Absolute score view is accessible via "see full scorecard."
- Positive delta: green. Negative delta: red. Neutral: grey.
- "Resolved since last run" findings are shown in a separate section with ✓ marks — this is the dopamine hit. Closing a P0 should feel good.
- Trend sparkline covers last 15 runs. Axis: readiness score 0-100. Coloured bands (green/amber/red) visible as background.
- If score has been stable for 5+ runs at Green: "Consistently green — you've built a reliable release process." This is the product's best outcome.

**Implementation tasks:**
- [x] Run delta computation — `scoreDelta` in `analysis_export.py`; `blockerCount` diff in `TrendSparkline`
- [x] Delta view as default for returning users — `TrendSparkline` shows when ≥2 runs for same product (`runs.$runId.tsx`)
- [x] Resolved blocker count with ✓ indicator (in `TrendSparkline`)
- [x] 15-run trend sparkline with band colouring — coloured bars by `readinessBand` (green/amber/red)
- [x] Stability message after 5 consecutive green runs ("Consistently green — you've built a reliable release process.")

**Reviewer:** Steve Jobs — does a founder feel progress when they look at this? Does fixing a P0 feel rewarding?

---

### E. MCP Integration — Developer Mode

**Concept:** TryLapse exposes its run data as an MCP server. Any MCP-compatible client — Claude Code, Cursor, Cline, Continue, ChatGPT with MCP — can query findings, trigger runs, and get readiness status without opening a browser. TryLapse findings become conversational in the developer's AI coding environment.

**Why this matters:** No other testing tool does this. Datadog has a REST API. Nobody makes their findings queryable from inside Claude Code. A developer who types "what's blocking my launch?" in Claude Code gets the answer immediately, in context, with the evidence attached.

**MCP server architecture:**

```
TryLapse Backend (REST API)
         ↓
TryLapse MCP Server (thin protocol adapter, ~200 lines)
         ↓ MCP protocol (stdio or SSE)
┌────────────────┬──────────────┬─────────────────┐
│  Claude Code   │  Cursor/Cline │  ChatGPT + MCP  │
└────────────────┴──────────────┴─────────────────┘
```

**Tools to expose:**

```python
# Tool definitions (MCP schema)

get_readiness_score(project_id: str | None) → {
    score: int,
    band: "green" | "amber" | "red",
    verdict: str,           # the Layer 1 sentence
    trend: int,             # delta from last run
    last_run_at: datetime
}

get_blockers(run_id: str | None) → [{
    id: str,
    title: str,
    story: str,             # the Layer 2 human story
    severity: "P0" | "P1",
    video_url: str | None,
    technical_detail: str,
    persona: str,
    journey: str
}]

list_runs(project_id: str | None, limit: int = 10) → [{
    run_id, status, score, band, started_at, duration, blocker_count
}]

compare_runs(run_id_a: str, run_id_b: str) → {
    new_findings: [...],
    resolved_findings: [...],
    score_delta: int,
    band_change: str | None
}

trigger_run(project_url: str, config: dict | None) → {
    run_id: str,
    status: "queued",
    eta_seconds: int
}

get_run_status(run_id: str) → {
    status, progress_percent, current_phase, eta_seconds
}

explain_finding(finding_id: str) → {
    story: str,
    technical_detail: str,
    reproduction_steps: [str],
    suggested_fix: str       # LLM-generated, one paragraph
}
```

**Example developer interactions enabled:**

In Claude Code:
- `"What's blocking my launch?"` → `get_blockers()` → natural language answer with finding stories
- `"Fix the P0 in checkout"` → `explain_finding(finding_id)` → Claude Code sees DOM path + reproduction steps + suggested fix → opens editor to the relevant file
- `"How has my score changed this week?"` → `compare_runs()` → Claude Code generates delta summary
- `"Run a rehearsal and tell me what you find"` → `trigger_run()` → polls `get_run_status()` → when complete, `get_blockers()` → reports findings

In CI/CD (GitHub Actions):
```yaml
- name: TryLapse rehearsal gate
  uses: trylapse/action@v1
  with:
    api_key: ${{ secrets.TRYLAPSE_API_KEY }}
    fail_on: amber  # or: red_only
```
Implementation: action calls `trigger_run`, polls `get_run_status`, fails pipeline if band is amber/red.

In standup prep:
- PM opens ChatGPT: `"Summarize the TryLapse report from this morning for my standup"` → ChatGPT queries MCP → generates 3-bullet standup summary

**Implementation tasks:**
- [ ] **MCP server scaffold** — Python package `trylapse-mcp`. Implements MCP stdio protocol. Reads `TRYLAPSE_API_KEY` from env. ~200 lines of protocol adapter code.
- [ ] **Tool implementations** — each tool above is a function that calls the TryLapse REST API and formats the response for MCP. Keep thin: no business logic in the MCP layer.
- [ ] **`explain_finding` LLM call** — one additional LLM call: given finding evidence, generate reproduction steps and suggested fix. This is the highest-value MCP tool for developers.
- [ ] **Claude Code integration docs** — `~/.claude/mcp.json` config snippet. Tested end-to-end with Claude Code on a real run.
- [ ] **GitHub Actions action** — `trylapse/action` wrapper around `trigger_run` + poll + verdict check. Published to GitHub Actions Marketplace.
- [ ] **Run trigger via MCP** — `trigger_run` tool starts a run asynchronously. `get_run_status` polls it. The MCP client can poll on an interval. Design for async: don't block the MCP connection.
- [ ] **Public video URLs** — P0 finding video URLs served via time-limited signed URLs (7-day expiry). MCP clients can embed or share these without requiring auth.

**Reviewer:** Carmack — verify MCP server is a pure thin adapter with no business logic. Karpathy — verify tool output is structured correctly for LLM consumption (clean JSON, no ambiguous fields).

### F. MCP Landing Page Documentation

Full end-to-end MCP section on the landing page (`TryLapse-Landing Page/index.html`).

- [x] **MCP section HTML** — new `#mcp` section between integrations and lead-form sections. Setup steps, simulated chat conversation, tool reference grid (7 tools), GitHub Actions CI/CD block. (`index.html`)
- [x] **Nav links** — desktop + mobile nav updated with MCP link.
- [x] **CSS** — `.mcp-section`, `.mcp-setup-layout`, `.mcp-chat-body`, `.mcp-tool-grid`, `.mcp-tool-card`, `.mcp-ci-block`, all responsive. (`src/style.css`)
