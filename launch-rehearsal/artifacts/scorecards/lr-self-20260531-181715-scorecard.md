# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260531-181715` |
| **Date** | 2026-05-31 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 522s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Amber** |
| **Top blocker** | Slow step completion |
| **Top delight** | Clear navigation structure |
| **Issues** | 13 |
| **Delights** | 6 |

| **Pages crawled** | 14 |
| **Auto journeys added** | 3 |
| **Parallel seeds** | 1 |
| **Flaky steps** | 6 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Fail** | **Fail** | **Fail** |
| **j2-runs** Runs list | **Fail** | **Fail** | **Fail** |
| **j3-compare** Compare runs | **Pass** | **Partial** | **Fail** |
| **j4-init-dogfood** Init dogfood flow | **Pass** | **Partial** | **Pass** |
| **j5-runner-selftest** Runner self-test trigger | **Pass** | **Pass** | **Pass** |
| **j6-trends** Trends monitoring | **Pass** | **Pass** | **Pass** |
| **auto-j1-dashboard** Auto: Dashboard | **Pass** | **Pass** | **Pass** |
| **auto-j3-explore** Auto: Explore /recommendations | **Pass** | **Pass** | **Pass** |
| **auto-j4-explore** Auto: Explore /library | **Pass** | **Pass** | **Pass** |

---

## Site map (crawl)

# Site map

**Origin:** http://127.0.0.1:8081  
**Pages crawled:** 14  

## Hub pages (most outbound links)

- `/` — Command center — Launch Rehearsal
- `/library` — Journey library — Launch Rehearsal
- `/agents` — Agents — Launch Rehearsal
- `/alerts` — Alerts — Launch Rehearsal
- `/cli` — CLI — Launch Rehearsal
- `/config` — Workspace — Launch Rehearsal
- `/init` — Init wizard — Launch Rehearsal
- `/integrations` — Integrations — Launch Rehearsal

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/` | Command center — Launch Rehearsal | 0 | 29 | 0 | 358 |
| `/agents` | Agents — Launch Rehearsal | 1 | 16 | 0 | 469 |
| `/alerts` | Alerts — Launch Rehearsal | 1 | 16 | 0 | 151 |
| `/cli` | CLI — Launch Rehearsal | 1 | 16 | 0 | 334 |
| `/compare` |  | 1 | 0 | 0 | 0 |
| `/config` | Workspace — Launch Rehearsal | 1 | 16 | 0 | 356 |
| `/init` | Init wizard — Launch Rehearsal | 1 | 17 | 0 | 267 |
| `/integrations` | Integrations — Launch Rehearsal | 1 | 16 | 0 | 124 |
| `/library` | Journey library — Launch Rehearsal | 1 | 18 | 0 | 160 |
| `/recommendations` | Recommendations — Launch Rehearsal | 1 | 23 | 0 | 249 |
| `/runner` | Runner — Launch Rehearsal | 1 | 17 | 0 | 266 |
| `/sitemap` |  | 1 | 0 | 0 | 0 |
| `/trends` |  | 1 | 0 | 0 | 0 |
| `/workflows` |  | 1 | 0 | 0 | 0 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/config` | Workspace — Launch Rehearsal | — |
| integration | `/integrations` | Integrations — Launch Rehearsal | — |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 14 pages; 0 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: dashboard, integration |
| `journey-runner` | E2E journey execution | Executed 60 steps across 9 journeys (2 failures, 6 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 7 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | First-time evaluator finds the dashboard informative but desktop initial load ca |
| `llm-p2-operator` | LLM evaluator: Daily operator | The dashboard loads reliably on most devices but has initial load failures on de |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Admin/buyer evaluation reveals inconsistent desktop page loads and mobile errors |
| `synthesizer` | Cross-agent synthesis | Synthesized 13 issues, 6 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 4 | 97% steps pass; 2 failures |
| UI/UX | 4 | 0 unlabeled buttons; ~4795ms avg step |
| Information clarity | 3 | 2 sparse-content pages |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I6** | Crawl found error pages — Paths: /compare, /sitemap, /trends, /workflows | p3-admin | `crawl-graph` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I3** | Console errors on page — 1 console error(s): Failed to load resource: the server responded with a status of 500 (Internal Server Error) | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I4** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). Timeout 15000ms exceeded.
=========================== logs ===========================
"load" event fired
============================================================ | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I5** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). Timeout 15000ms exceeded.
=========================== logs ===========================
"load" event fired
============================================================ | p1-evaluator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I11** | Compare runs page on mobile reports errors (hypothesis) — Both mobile navigation and wait steps for the compare runs page have errors in the 'errors' array (value 'failed'), although the wait outcome is pass. This indicates potential instability on mobile for a key comparative analysis task. | p2-operator | `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` |
| **I12** | Compare page shows errors on mobile — The mobile steps for the compare journey (j3-compare) have 'failed' in their errors list, indicating a technical issue that prevents proper rendering or functionality on mobile devices. | p3-admin | `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Slow step completion — Step took 67703ms (>8s perceived delay threshold). | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I7** | Slow initial load on desktop for Command Center — The first navigation to the Command Center on desktop took 67 seconds to load, which may frustrate new users expecting quick value. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I8** | Slow initial load on desktop for Runs page — The first navigation to the Runs page on desktop took 29 seconds to load, which may discourage exploration. | p1-evaluator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I9** | Desktop initial navigation to command center fails — The first navigate step to the command center on desktop failed, though it recovered on subsequent wait. This delays the operator's entry to the core page. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I10** | Desktop initial navigation to runs fails — The first navigate step to the runs page on desktop failed, recovering on wait. This adds delay to accessing run history. | p2-operator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I13** | Desktop initial page loads fail intermittently (hypothesis) — The first navigate steps for desktop views of the command center and runs pages fail (no title or excerpt), though subsequent steps succeed. This suggests slow or inconsistent loading that may frustrate admins. | p3-admin | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 16 links and 1 headings. | p1-evaluator, p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Accessible form labels — All 2 form inputs have labels or placeholders. | p3-admin | `auto-j3-explore-p1-evaluator-s1-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 38 steps completed under 3s. | p2-operator | `j2-runs-p1-evaluator-s2-desktop-seed1-loop1` |
| **D5** | Clear value summary on Command Center mobile view — The mobile Command Center shows a concise 'Pre-launch readiness, observed. Live rollup' with readiness score, blockers, and delights, quickly communicating the product's value. | p1-evaluator | `j1-command-center-p1-evaluator-s1-mobile-seed1-loop1` |
| **D6** | Transparent mock data indicator on mobile runs — The mobile runs page clearly displays 'API offline — showing Acme mock', providing honest communication about data source, which builds trust for an admin verifying data integrity. | p3-admin | `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` |

---

## Run log

| Step | Journey | Action | Outcome | URL |
|------|---------|--------|---------|-----|
| `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` | j1-command-center | navigate | fail | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s2-desktop-seed1-loop1` | j1-command-center | wait | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s1-tablet-seed1-loop1` | j1-command-center | navigate | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s2-tablet-seed1-loop1` | j1-command-center | wait | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s1-mobile-seed1-loop1` | j1-command-center | navigate | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s2-mobile-seed1-loop1` | j1-command-center | wait | pass | http://127.0.0.1:8081/ |
| `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` | j2-runs | navigate | fail | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-desktop-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s1-tablet-seed1-loop1` | j2-runs | navigate | pass | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-tablet-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` | j2-runs | navigate | pass | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-mobile-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` | j3-compare | navigate | pass | http://127.0.0.1:8081/compare |
| `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` | j3-compare | wait | pass | http://127.0.0.1:8081/compare |
| `j3-compare-p1-evaluator-s1-tablet-seed1-loop1` | j3-compare | navigate | pass | http://127.0.0.1:8081/compare |
| `j3-compare-p1-evaluator-s2-tablet-seed1-loop1` | j3-compare | wait | pass | http://127.0.0.1:8081/compare |
| `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` | j3-compare | navigate | pass | http://127.0.0.1:8081/compare |
| `j3-compare-p1-evaluator-s2-mobile-seed1-loop1` | j3-compare | wait | pass | http://127.0.0.1:8081/compare |
| `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` | j4-init-dogfood | navigate | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s2-desktop-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s3-desktop-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s4-desktop-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s5-desktop-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s1-tablet-seed1-loop1` | j4-init-dogfood | navigate | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s2-tablet-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s3-tablet-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s4-tablet-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s5-tablet-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` | j4-init-dogfood | navigate | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s2-mobile-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s3-mobile-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s4-mobile-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s5-mobile-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j5-runner-selftest-p1-evaluator-s1-desktop-seed1-loop1` | j5-runner-selftest | navigate | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s2-desktop-seed1-loop1` | j5-runner-selftest | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s3-desktop-seed1-loop1` | j5-runner-selftest | click | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s4-desktop-seed1-loop1` | j5-runner-selftest | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s1-tablet-seed1-loop1` | j5-runner-selftest | navigate | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s2-tablet-seed1-loop1` | j5-runner-selftest | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s3-tablet-seed1-loop1` | j5-runner-selftest | click | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s4-tablet-seed1-loop1` | j5-runner-selftest | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s1-mobile-seed1-loop1` | j5-runner-selftest | navigate | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s2-mobile-seed1-loop1` | j5-runner-selftest | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s3-mobile-seed1-loop1` | j5-runner-selftest | click | pass | http://127.0.0.1:8081/runner |
| `j5-runner-selftest-p1-evaluator-s4-mobile-seed1-loop1` | j5-runner-selftest | wait | pass | http://127.0.0.1:8081/runner |
| `j6-trends-p1-evaluator-s1-desktop-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-desktop-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s1-tablet-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-tablet-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s1-mobile-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-mobile-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j1-dashboard-p1-evaluator-s1-tablet-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j1-dashboard-p1-evaluator-s1-mobile-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j3-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j3-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j3-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j3-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j3-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j3-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j4-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j4-explore | navigate | pass | http://127.0.0.1:8081/library |
| `auto-j4-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j4-explore | navigate | pass | http://127.0.0.1:8081/library |
| `auto-j4-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j4-explore | navigate | pass | http://127.0.0.1:8081/library |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
