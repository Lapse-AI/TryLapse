# TryLapse — Product Backlog

**Last updated: 2026-07-04**
**Owner: Sparsh (CEO)**
**Status key:** `[ ]` = pending · `[x]` = shipped · `[~]` = in progress

This document is the authoritative backlog for everything not yet shipped. Each item includes **what** it is, **why** it matters, and **how** to implement it. Update the date at the top whenever this file is edited.

---

## 0. Deployment (Hard Blocker — Nothing Is Visible Without This)

### `[ ]` Railway deploy

**What:** Connect the TryLapse GitHub repo to Railway via CLI, set all required environment variables, and verify the dashboard is publicly accessible at a stable URL.

**Why:** The product currently only runs on localhost. No investor, design partner, or beta user can see it. Every other item in this backlog is invisible until this is done. This is the single highest-leverage unblocked task.

**Current state:** `Dockerfile`, `railway.json`, and `docker-entrypoint.sh` all exist and are correct. The image builds the Vite frontend, embeds it in the Python package static dir, seeds the demo artifacts volume on first boot, and starts `rehearse serve --host 0.0.0.0 --port $PORT`. The Railway CLI is installed locally (`railway 4.66.1`). **Blocked only on Railway login + `railway up`.**

**How:**
1. In terminal: `railway login` (opens browser auth)
2. `cd /Users/sparshnagpal/Desktop/projects/TryLapse && railway init` — create new Railway project named "TryLapse"
3. `railway volume add` — add a persistent volume mounted at `/data/artifacts` (run data survives redeploys)
4. Set env vars via Railway dashboard or CLI:
   ```
   REHEARSE_JWT_SECRET=<64-char hex — run: openssl rand -hex 32>
   DEEPSEEK_API_KEY=<key>
   NVIDIA_NIM_API_KEY=<key>
   REHEARSE_ADMIN_EMAILS=0sparsh2@gmail.com
   REHEARSE_EMAIL=<target site login email>
   REHEARSE_PASSWORD=<target site login password>
   REHEARSE_CORS_ORIGIN=https://<railway-domain>.up.railway.app
   ```
5. `railway up` — triggers first deploy; watch build logs
6. Verify: `curl https://<domain>/api/health` → `{"status":"ok"}`
7. Open dashboard URL → confirm demo runs are visible

**Acceptance:** Public URL returns the dashboard with at least one real completed run visible.

---

### `[ ]` Fresh demo run

**What:** Trigger a new rehearsal run against `faculty-dashboard-eight.vercel.app` (Argyle) or the enterprise config after Railway is live, so the dashboard shows evidence dated today rather than weeks ago.

**Why:** Investors and design partners look at the "last run" timestamp. A run from weeks ago reads as abandoned product, not active development.

**How:**
1. After Railway is live, POST to `/api/jobs` with the argyle config, or use the dashboard trigger UI
2. Monitor via admin dashboard → live jobs section
3. Verify run completes, scorecard has current date, evidence artifacts are accessible
4. Optionally set a Railway cron to run weekly against the demo target

---

## A. Crawler Quality

*Root problem: the crawler follows links. That is not the same as covering the app. These items close the gap between "pages visited" and "app graph covered."*

---

### `[x]` A1 — Route template deduplication

**Shipped 2026-07-04.** `route_graph.py` created — unified URL-to-template normalizer with version-segment detection (`v1`/`v2` → `{version}`) and `RouteTemplateGraph` with Jaccard-based semantic merging (threshold 0.85). Replaces the duplicated inline implementations in both `crawler.py` and `deep_crawler.py`. `_url_pattern()` in `deep_crawler.py` now delegates to `route_graph.url_to_template()`.

---

### `[ ]` A2 — State-dependent route discovery

**What:** After each journey step executes, re-scan the link/route graph. Any new routes that appear after the action that weren't present before = state-dependent routes. Add them to the crawl queue tagged with the action sequence that reveals them.

**Why:** Checkout confirmation pages, onboarding step 3, empty-state screens, post-purchase flows — these pages only exist after specific user actions. A link-following crawler never reaches them. They are exactly the pages most likely to have bugs (high-stakes, low-traffic, rarely tested).

**How:**
1. Before each step, snapshot `document.querySelectorAll('a[href]')` → set of hrefs
2. After step completes, snapshot again. Diff = new routes.
3. Tag new routes with `{ "discovered_via": [list of steps], "type": "state_dependent" }`
4. Add to crawl queue with the prerequisite step sequence stored
5. In coverage report: `"state_dependent_routes_discovered": N`

**Files:** `crawler.py`, `route_graph.py`

---

### `[ ]` A3 — XHR-based route supplementation

**What:** During the crawl phase, intercept all outgoing network requests. Extract API endpoint patterns. Cross-reference with the frontend route graph. Endpoints with no corresponding frontend route = "dark paths."

**Why:** The frontend only reveals what someone intentionally linked. Backend API endpoints reveal what the app actually does. Dark paths are often admin functions, legacy flows, or partially-built features — all high-risk areas.

**How:**
1. Attach `page.on('request', ...)` handler during crawl phase
2. Collect all `fetch`/XHR requests: method, URL, status
3. After crawl, cluster API endpoints by path pattern
4. Cross-reference with discovered frontend routes — routes with no frontend equivalent are dark paths
5. Include in crawl output: `{ "api_endpoints_observed": 34, "dark_paths": 3, "dark_path_urls": [...] }`

**Files:** `crawler.py`, `evidence.py`

---

### `[ ]` A4 — Graph coverage metric

**What:** Replace "N routes visited" with a real coverage metric: `X% of reachable app graph covered`. Show which subgraphs were not reached.

**Why:** "Visited 47 routes" means nothing to an engineering team. "Covered 78% of the reachable app graph; these 3 subgraphs were not reached" is actionable and builds trust.

**How:**
1. Build a directed graph: nodes = unique route templates, edges = navigation paths between them
2. From entry point, compute all reachable nodes via BFS
3. Track which reachable nodes were actually visited
4. Coverage = `visited / reachable * 100`
5. Expose: `GET /api/runs/{id}/coverage` → `{ "coverage_pct": 78, "reachable_templates": 15, "visited_templates": 12, "uncovered": [...] }`
6. Frontend: coverage ring on run detail page

**Files:** `route_graph.py`, `analysis_export.py`, `runs.$runId.tsx`

---

### `[ ]` A5 — Soft-redirect auth detection

**What:** If the crawler navigates to a URL and the resulting page contains `<input type="password">`, mark that route as auth-gated regardless of HTTP status code.

**Why:** Many apps return HTTP 200 for unauthenticated users but serve a login page. The crawler currently classifies these as "visited" when they're actually auth-blocked.

**How:**
1. After every navigation, check: `page.query_selector('input[type="password"]') is not None`
2. If true, mark route as `auth_gated: true`
3. Do not count auth-gated routes as "covered" in the coverage metric
4. If auth credentials are configured, re-crawl those routes with auth state applied

**Files:** `crawler.py`, `route_graph.py`

---

### `[ ]` A6 — Parameterized route recognition

**What:** Detect URL patterns like `/users/:id`, `/products/:slug`. Store as route templates, not instances. When testing, use synthetic valid IDs drawn from prior crawl responses.

**Why:** Without this, 500 user profile pages create 500 entries in the route graph, each identical. We want to test the template once with a known-valid ID.

**How:**
1. After crawl, cluster URLs by structure (already done in `route_graph.py`)
2. During XHR capture (A3), harvest real IDs from API responses — valid synthetic test values
3. Store: `{ "template": "/users/{id}", "instances": [...], "synthetic_test_id": "123" }`
4. Journey runner uses `synthetic_test_id` when constructing test URLs

**Files:** `route_graph.py`, `crawler.py`

---

## A2. Flake Rate (Target ≤3% Before Any Public Launch)

---

### `[ ]` Three-run confirmation gate verification

**What:** Confirm that the existing `flake_rate` field and `_mark_flaky_steps` logic in `evidence.py`/`heuristics.py` is correctly gating: a finding is only filed if it reproduces in ≥2 of 3 seeds. Write a test that proves the gate fires correctly.

**Why:** The code was written but never explicitly end-to-end tested. If the gate is misconfigured, we either file false positives (destroy trust) or miss real bugs (miss coverage). At <3% flake rate we can claim reliability.

**How:**
1. Read `evidence.py:_mark_flaky_steps` and `heuristics.py` flake-rate check
2. Write `tests/test_flake_gate.py`: mock 3 seed runs where a step fails in 1/3, 2/3, and 3/3 cases; assert finding only filed for ≥2/3
3. Run the test; if it fails, fix the gate

**Files:** `evidence.py`, `heuristics.py`, `tests/test_flake_gate.py`

---

## A5-synth. Synthesizer Quality

*The synthesizer is currently the weakest link: LLM calls where deterministic code should live, no full semantic deduplication, no calibration loop.*

---

### `[ ]` Embedding-based deduplication

**What:** Replace current string-matching finding dedup with sentence-transformer embeddings. Two findings with cosine similarity > 0.85 are treated as the same bug. LLM only writes the merged description after dedup.

**Why:** The same bug surfaced by 3 personas creates 3 duplicate findings. Users see noise. And if dedup uses an LLM, running the synthesizer twice on the same findings produces different dedup decisions — unacceptable for a testing tool.

**Note:** `TFIDFEmbedder` in `embeddings.py` exists and handles finding dedup with Jaccard + TF-IDF cosine. This item upgrades to full sentence-transformer embeddings (`all-MiniLM-L6-v2`) for higher accuracy, or confirms TF-IDF is sufficient.

**How:**
1. Evaluate whether `TFIDFEmbedder` false-positive/negative rate is acceptable by running on real run data
2. If not: `pip install sentence-transformers`, embed with `all-MiniLM-L6-v2`, compute cosine similarity matrix
3. Group findings where similarity > 0.85 into clusters
4. For each cluster, take the finding with most evidence as canonical; LLM writes merged description
5. Store `merged_from: [finding_id_1, finding_id_2]` on the canonical finding

**Files:** `synthesizer.py`, `embeddings.py`

---

### `[ ]` Deterministic severity scoring

**What:** Replace LLM-determined severity (P0/P1/P2/P3) with a pure deterministic function. LLM only writes the human-readable explanation for *why* the severity was assigned.

**Why:** Same evidence → different severity on different runs is a fundamental correctness failure. If a developer sees a finding flip from P0 to P1 between runs without any code change, they stop trusting the tool immediately.

**Decision tree:**
```
P0 = journey-blocking failure with step evidence (step failed, no recovery)
P1 = journey completes but a significant defect observed with evidence
P2 = non-blocking observation with evidence
P3 = observation without direct evidence (hypothesis)
```

**How:**
1. Create `severity.py` with `classify_severity(finding: dict) -> str` pure function
2. Inputs: `finding_type`, `evidence_count`, `journey_impact` (blocked/degraded/completed), `reproduction_count` (out of 3 seeds)
3. Map to P0/P1/P2/P3 deterministically via if/elif tree
4. LLM call: given severity + evidence, write `severity_explanation` (one sentence)
5. Replace all LLM-determined severity in `synthesizer.py` with `classify_severity()`

**Files:** `severity.py` (new), `synthesizer.py`

---

### `[x]` Statistical baseline scoring

**Shipped 2026-07-04.** `baseline_store.py` created — computes rolling 90-run z-scores for `readiness`, `flakeRate`, `blockerCount`, `issueCount`, `stepCount`, `durationSec`, `pagesCrawled`, plus per-dimension scores. Wired into `analysis_export.py`; result stored as `summary.baseline` in the bundle JSON.

---

### `[ ]` Cross-run delta view (primary view for returning users)

**What:** For every run after the first, the primary dashboard view shows: new findings, resolved findings, score delta per axis, new P0s since last run. The full scorecard is secondary.

**Why:** Returning users are not asking "what is the state?" They are asking "what changed since Tuesday?" Showing a static scorecard every time trains users to ignore it.

**Note:** `_cross_run_delta()` exists in `analysis_export.py`. The backend computation may be partially done. Frontend panel is missing entirely.

**How:**
1. Verify `_cross_run_delta()` output shape in `analysis_export.py` — confirm it's wired into the bundle `summary`
2. If not wired: call it and store as `summary.delta`
3. Frontend: if `bundle.summary.delta` exists, show delta panel above the full scorecard:
   - "2 blockers resolved ✓" (green)
   - "1 new P1 since last run" (amber)
   - Score delta per dimension sparkline
4. Full scorecard stays below, collapsed by default when delta panel is shown

**Files:** `analysis_export.py`, `runs.$runId.tsx`

---

### `[x]` Severity calibration feedback loop

**Shipped (pre-existing).** `finding_outcome_store.py` + `PUT /api/runs/{run_id}/findings/{id}/outcome` endpoint + `FindingOutcomeButtons` frontend component all exist. Finding outcomes are stored in `artifacts/feedback/{slug}.jsonl`.

---

### `[ ]` Causal clustering

**What:** Group findings by likely root cause. Three symptoms of a broken checkout flow should be presented as one P0, not three separate findings.

**Why:** "Fix before you launch" with 7 items is overwhelming. The human-facing rule: never more than 3 items in the top bucket. If there are more P0s, they're symptoms of fewer root causes.

**How:**
1. After deduplication, cluster remaining findings by: same page URL, same journey, same step range (within 2 steps), correlated appearance/disappearance across runs
2. Within each cluster, elect the highest-severity finding as the cluster representative
3. Store: `{ "cluster_id": "checkout-flow-3", "root_finding": {...}, "related_findings": [...] }`
4. "Fix before you launch" shows cluster representatives, not individual findings
5. Clicking a cluster expands to show all related findings

**Files:** `synthesizer.py`, `clustering.py` (new), `run-detail.tsx`

---

### `[x]` Streaming synthesis (frontend polling)

**Shipped 2026-07-04.** Backend `_write_partial_bundle()` already existed. Added: `refetchInterval` to `useRunBundle` (polls every 5s when `summary.partial === true`, stops when run finalizes) + "Analysis in progress — N of M personas complete" banner in `runs.$runId.tsx`. `RunSummary` type extended with `partial`, `personasComplete`, `personasTotal`.

---

### `[x]` SEO health signals

**Shipped 2026-07-04.** `seo.py` created — checks missing meta description, duplicate titles, noindex on non-admin pages, images missing alt, broken canonical. Called from `analysis_export.py` via `run_seo_checks(seo_snapshots)`. SEO snapshots collected during crawl in `deep_crawler.py` via `SEO_EXTRACTION_SCRIPT`.

---

### `[x]` Cookie consent compliance detection

**Shipped 2026-07-04.** `check_and_dismiss_consent_banner()` added to `browser.py` — detects fixed/sticky overlays covering ≥15% viewport with consent keywords, attempts auto-dismiss via 14 selectors. Result stamped on `snap.note` as `[consent-banner:dismissed]` or `[consent-banner:blocked]`. Heuristic in `heuristics.py` raises P1 if blocked, notes delight if dismissed.

---

## B. Architecture (Carmack Audit)

*Root concern: partial states must be impossible. State isolation must be complete. LLM calls must be confined to the right boundary.*

---

### `[x]` B1 — Pre-run cleanup

**Shipped (pre-existing).** `_cleanup_stale_artifacts()` exists in `runner.py` at line ~99. Scans for `*.tmp*` files before run start and removes them.

---

### `[ ]` B2 — Context-per-persona enforcement

**What:** Verify in code (and add a test) that every persona always gets a fresh `browser.new_context()` call. Make it structurally impossible to reuse a context between personas.

**Why:** Context reuse is the primary source of state bleed. Cookies, localStorage, service workers, cached responses from persona 1 leak into persona 2. This produces findings that are artifacts of test ordering rather than real bugs.

**How:**
1. Read `browser.py:BrowserSession` and `_ThreadSession` — verify context is created fresh per persona
2. Write `tests/test_context_isolation.py`: run two personas sequentially, verify localStorage from persona 1 is empty in persona 2's context
3. Add a log line at context creation: `logger.info("New context for persona %s", persona_id)`

**Files:** `browser.py`, `journey_agent.py`, `tests/test_context_isolation.py`

---

### `[ ]` B3 — Context destruction verification

**What:** After `context.close()`, assert that no pages from that context are still attached. Log context lifetime.

**Why:** A context that closes with attached pages is a resource leak. Over a multi-persona run, leaked pages accumulate and cause memory growth.

**How:**
1. In `BrowserSession.__exit__`: log `context closed: created_at={t0}, closed_at={t1}, pages_opened={n}`
2. Store in phase timings: `evidence.phase_timings["context_lifetime_ms"]`

**Files:** `browser.py`, `evidence.py`

---

### `[ ]` B4 — Network request completion guard

**What:** Before closing a browser context, wait for all in-flight network requests to complete (or timeout at 5s).

**Why:** A slow POST from persona 1 (e.g., a form submission that takes 3s) can resolve its response handler after persona 2's context has started. Shared state touched in that handler = contaminated persona 2 results.

**How:**
1. Before `context.close()`, call `page.wait_for_load_state("networkidle", timeout=5000)` on all open pages
2. Catch `TimeoutError` and log: `"Context close: network idle wait timed out after 5s for persona {id}"`
3. Proceed with close regardless

**Files:** `browser.py`

---

### `[ ]` B5 — LLM call audit in synthesizer.py

**What:** Read every LLM call in `synthesizer.py`. For each one: if it can be replaced with deterministic code, replace it. If not, add `temperature=0` and document why LLM is appropriate.

**Why:** A testing tool that produces different scores for the same inputs on different days is not a testing tool — it's a random number generator with an expensive API.

**How:**
1. List every `_call_llm()` invocation in `synthesizer.py`
2. Classify: `deterministic_replacement_possible` (severity, deduplication, score calculation) vs. `llm_appropriate` (narrative writing, explanations)
3. Replace all deterministic cases with code (feeds into `severity.py` item above)
4. Add `temperature=0` on all remaining LLM calls
5. Write `tests/test_determinism.py`: run synthesizer twice on identical inputs; assert outputs are byte-identical (except timestamps)

**Files:** `synthesizer.py`, `tests/test_determinism.py`

---

### `[ ]` B6 — LLM serial latency fix

**What:** Reduce from ~40 serial LLM calls per run (4 personas × ~10 steps × 1 call/step) to ≤4 calls per run (one synthesis call per persona at journey end).

**Why:** 40 serial LLM calls at ~2s each = 80s of pure LLM wait, not counting browser time. This is unnecessary. The per-step calls are making micro-decisions that should be deterministic code.

**How:**
1. Remove per-step LLM calls from `journey_agent.py` step execution loop
2. After all steps for a persona complete, pass the full `[StepSnapshot]` list to one LLM call
3. LLM prompt: "Given these N steps of evidence, write findings in structured format"
4. All deterministic analysis (severity, dedup, scoring) runs on LLM output as post-processing
5. Measure before/after: `evidence.phase_timings["llm_total_ms"]`

**Files:** `journey_agent.py`, `synthesizer.py`

---

### `[ ]` B7 — Screenshot WebP + async writes

**What:** Change all screenshot captures from PNG to WebP format. Write screenshot files asynchronously so the browser thread never blocks on disk I/O.

**Why:** 40 screenshots at ~1.5MB PNG each = ~60MB per run. WebP reduces this ~4× to ~15MB. On a slow disk or high-concurrency run, synchronous PNG writes block the Playwright page object — introducing artificial delays and inflating timing measurements.

**How:**
1. In `browser.py`, change all `page.screenshot()` calls: add `type="webp"`, `quality=85`
2. Change file extensions from `.png` to `.webp`
3. Wrap screenshot write in `asyncio.to_thread` or threaded write to avoid blocking the browser
4. Update any frontend `<img>` tags that hardcode `.png` extension

**Files:** `browser.py`, frontend components referencing screenshot URLs

---

### `[ ]` B8 — Browser process memory leak prevention

**What:** Restart the browser process (not just context) between personas. Assert browser process RSS is under 500MB at the start of each persona.

**Why:** Long-running Playwright browser processes accumulate V8 heap snapshots, cached frames, and unreleased page objects. On Railway's constrained containers, this triggers OOM kills on long runs with large pages.

**How:**
1. In `BrowserSession`, after each persona's context is closed, call `browser.close()` and reopen a new `playwright.chromium.launch()`
2. Before launching new browser, check process RSS: `import resource; rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`
3. Log warning if RSS > 500MB
4. Test: run a 4-persona rehearsal on Railway and monitor memory across the run

**Files:** `browser.py`, `journey_agent.py`

---

## D. Non-Technical Verdict UX (Jobs Audit)

*Standard: a non-technical founder must understand the verdict in 3 seconds.*

---

### `[ ]` D1 — Verdict in email/Slack notification

**What:** When a run completes, the notification (email or Slack) includes the full Layer 1 verdict sentence, the readiness band color, and the count of P0 findings — without requiring the user to click through to the dashboard.

**Why:** If a founder has to open the dashboard to know whether to delay launch, the notification is useless. The verdict must travel to wherever the founder is looking.

**How:**
1. In `server.py`, after a run transitions to COMPLETE, check for `REHEARSE_NOTIFY_EMAIL` or `REHEARSE_SLACK_WEBHOOK` env vars
2. Compose: `f"[{band.upper()}] {verdict_sentence}\n\nBlockers: {p0_count} · Fix this week: {p1_count}\n\nFull report: {run_url}"`
3. Email: use `smtplib` or `sendgrid` SDK; Slack: POST to webhook URL

**Files:** `dashboard/server.py`, `notify.py` (new)

---

### `[ ]` D3 — Finding grouping for "Fix before you launch"

**What:** When "Fix before you launch" has more than 3 items, group related P0 findings by causal proximity and present as one item with a count: "Checkout is broken (3 signals)."

**Why:** "Fix before you launch" with 7 items is overwhelming and loses the priority signal. The human-facing rule: never more than 3 items in the top bucket.

**How:**
1. After causal clustering (see A5-Causal clustering), use cluster structure to group P0s
2. If a cluster has ≥2 findings: `"[Checkout flow] 3 issues found"` with expand/collapse
3. If ≤3 clusters/individuals in P0 bucket: show all. If >3: show top 3, collapse rest into "and N more critical issues"

**Files:** `run-detail.tsx`, `clustering.py`

---

### `[x]` D4a — LLM-generated share message

**Shipped (pre-existing).** `share.py` exists with `build_share_payload()` — LLM-polished share message generation. Stored as `narrative.layer4Forward` in the bundle.

---

### `[x]` D4b — Public signed video URLs

**Shipped (pre-existing).** `signing.py` exists with `sign_path()`, `verify_signature()`, `build_signed_file_url()` — HMAC-signed URLs with expiry. Used in `share.py` for P0 finding video clips.

---

## E. MCP Integration

*TryLapse's distribution moat. When built, the developer's AI assistant becomes the primary UI.*

---

### `[x]` E1 — MCP server scaffold

**Shipped (pre-existing).** `mcp_server.py` exists — full JSON-RPC stdio adapter, 7 tools. `.claude/mcp.json` created 2026-07-04 pointing at the venv Python + local artifacts dir.

---

### `[x]` E2 — MCP tool implementations

**Shipped (pre-existing).** All 7 tools implemented in `mcp_server.py`: `get_readiness_score`, `get_blockers`, `list_runs`, `compare_runs`, `trigger_run`, `get_run_status`, `explain_finding`.

---

### `[ ]` E3 — explain_finding LLM call (backend endpoint)

**What:** A backend endpoint `POST /api/findings/{finding_id}/explain` that takes a finding's evidence and generates: numbered reproduction steps and a suggested fix paragraph.

**Why:** This is the highest-value MCP tool. When Claude Code calls `explain_finding`, it gets specific reproduction steps and a suggested fix — the developer can then say "fix it" and Claude Code opens the relevant file. This closes the loop from "TryLapse found a bug" to "Claude Code fixed the bug."

**How:**
1. Add `POST /api/findings/{finding_id}/explain` to `server.py`
2. Load finding evidence from the run bundle
3. LLM prompt: "Given this finding evidence, write: (1) numbered reproduction steps, (2) one paragraph describing the likely root cause and suggested fix. Be specific about file paths and function names if evident."
4. Return: `{ "reproduction_steps": ["Step 1: ...", ...], "suggested_fix": "..." }`
5. Cache the result — expensive, should not be recomputed per request

**Files:** `dashboard/server.py`, `synthesizer.py`

---

### `[ ]` E4 — Claude Code integration docs (end-to-end tested)

**What:** A tested, working configuration snippet for `~/.claude/mcp.json` that connects Claude Code to a Railway-hosted TryLapse instance. Tested end-to-end against a real run.

**Why:** Documentation that hasn't been tested end-to-end is not documentation — it's aspirational writing.

**How:**
1. After Railway is live, test the full flow: install MCP config → open Claude Code → ask "what's blocking my launch?" → get a real answer
2. Write `trylapse-mcp/README.md` with the exact config snippet using the Railway URL
3. Add to landing page MCP section

**Files:** `.claude/mcp.json`, `trylapse-mcp/README.md`

---

### `[ ]` E5 — GitHub Actions action

**What:** A GitHub Actions action `trylapse/action@v1` that triggers a TryLapse run, polls until complete, and fails CI if the readiness band is amber or red.

**Why:** The CI integration is the enterprise sales hook. "Our CI pipeline won't merge to main if TryLapse finds a blocker" is a purchasing conversation, not an evaluation conversation.

**How:**
1. Create `trylapse/action` GitHub repo with `action.yml`:
   ```yaml
   inputs:
     api_key: required
     project_url: required
     fail_on: { default: "amber" }
   ```
2. `trylapse-ci` binary: trigger run, poll `get_run_status` every 30s, exit 1 if band is amber/red
3. Publish to GitHub Actions Marketplace
4. Add usage example to landing page

---

### `[ ]` E6 — Public signed video URLs for MCP

**What:** P0 finding video URLs returned by MCP tools must be publicly accessible without auth (using signed URLs). MCP clients can share these without requiring the recipient to log into TryLapse.

**Why:** If Claude Code calls `get_blockers()` and the video URL requires auth, the LLM can't surface the video — it prints a URL that errors for the user.

**How:** Reuse the existing `signing.py` implementation. MCP tools automatically use signed URLs for any `video_url` field in responses. Wire in `mcp_server.py:get_blockers()`.

**Files:** `mcp_server.py`, `dashboard/server.py`

---

## F. Go-to-Market (Non-Engineering)

---

### `[ ]` Design partner outreach

**What:** Contact 10 warm targets; get 5 intros sent; book 2 calls.

**Why:** All engineering hardening in sections A-E is meaningless without validation that real users would pay for this. Three "would-pay" design partners by Sep 30 is the gate for Phase 2. Without starting outreach now, that gate cannot be met.

**How:**
1. Read `DESIGN_PARTNER_OUTREACH.md` for the warm targets list
2. Personalize each message: "I saw you shipped [recent feature] — we built a tool that would have caught [specific type of issue] before you launched"
3. Lead with the video evidence, not the product description
4. Ask for 20 minutes, not a demo — lower friction
5. Track: contacted / replied / call booked / would-pay verdict

**Deadline:** Calls booked by Jul 15, 2026.

---

### `[ ]` 5 founder design partners — 3 would-pay

**What:** Convert design partner outreach into 5 active users and 3 explicit "yes I would pay for this" responses.

**Why:** This is the Phase 2 gate. Without it, no public beta, no pricing page. "Would-pay" means they said it unprompted or in response to a direct pricing question.

**Target:** Sep 30, 2026

---

### `[ ]` Public beta / waitlist

**What:** A waitlist page (or form on the landing page) that captures emails from people who want access. Public announcement on Twitter/LinkedIn.

**Why:** Building a waitlist before the public beta costs nothing and creates momentum. Even 50 signups provides social proof for design partner conversations.

**Target:** Sep 30, 2026

---

### `[ ]` Open-source decision

**What:** Decide whether to open-source the `launch-rehearsal/` core.

**Why:** Open-sourcing creates distribution (GitHub stars, HN posts, developer trust) but removes a potential moat. The decision depends on whether 3 would-pay partners have been found.

**Target:** Aug 1, 2026

---

## Priority Order (as of 2026-07-04)

| Priority | Item | Reason |
|----------|------|--------|
| 1 | **Railway deploy** | Nothing is visible without this. Config exists — blocked only on `railway login` + `railway up` |
| 2 | **Fresh demo run** | Investors and partners look at the timestamp |
| 3 | **Design partner outreach** | Only validation that matters. Deadline: Jul 15 |
| 4 | **Deterministic severity** (`severity.py`) | Reproducibility is a trust prerequisite |
| 5 | **LLM call audit** (`B5`) | Feeds #4; identifies all non-deterministic synthesis |
| 6 | **LLM serial latency fix** (`B6`) | 80s → 10s LLM wait; changes the product feel |
| 7 | **Cross-run delta view** | Makes returning users sticky; backend may already have this |
| 8 | **Context isolation test** (`B2`) | Correctness; flake rate root cause |
| 9 | **Network drain guard** (`B4`) | Correctness; subtle state bleed vector |
| 10 | **Browser memory restart** (`B8`) | OOM prevention on Railway |
| 11 | **Three-run flake gate test** | Confirms the ≥2/3 gate actually fires |
| 12 | **State-dependent route discovery** (`A2`) | Coverage numbers become real |
| 13 | **explain_finding endpoint** (`E3`) | Highest-value MCP tool |
| 14 | **Verdict notification** (`D1`) | Verdict travels to founder, not vice versa |
| 15 | **GitHub Actions action** (`E5`) | Enterprise sales hook |
| — | B3, B7, A3, A4, A5, A6 | Important but not blocking trust or deploy |
| — | Causal clustering, D3 | Polish layer, high-value but after trust items |

---

*Next review: update this doc and the date at the top whenever a `[ ]` item ships or priority changes.*
