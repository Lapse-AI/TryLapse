# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260531-181747` |
| **Date** | 2026-05-31 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 439s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Red** |
| **Top blocker** | Slow step completion |
| **Top delight** | Clear navigation structure |
| **Issues** | 12 |
| **Delights** | 7 |

| **Pages crawled** | 1 |
| **Auto journeys added** | 0 |
| **Parallel seeds** | 1 |
| **Flaky steps** | 3 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Pass** | **Partial** | **Pass** |
| **j2-runs** Runs list | **Fail** | **Fail** | **Fail** |
| **j3-compare** Compare runs | **Fail** | **Fail** | **Fail** |
| **j4-init-dogfood** Init dogfood flow | **Pass** | **Partial** | **Partial** |
| **j5-runner-selftest** Runner self-test trigger | **Pass** | **Partial** | **Partial** |
| **j6-trends** Trends monitoring | **Pass** | **Partial** | **Pass** |

---

## Site map (crawl)

# Site map

**Origin:** http://127.0.0.1:8081  
**Pages crawled:** 1  

## Hub pages (most outbound links)

- `/` — 

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/` |  | 0 | 0 | 0 | 0 |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 1 pages; 0 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: none |
| `journey-runner` | E2E journey execution | Executed 51 steps across 6 journeys (4 failures, 3 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 4 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | The dashboard displays a strong readiness score on the landing page, but navigat |
| `llm-p2-operator` | LLM evaluator: Daily operator | Operator can access command center and init wizard reliably, but runs and compar |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Admin evaluation of Launch Rehearsal Dashboard on localhost reveals consistent p |
| `synthesizer` | Cross-agent synthesis | Synthesized 12 issues, 7 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 4 | 92% steps pass; 4 failures |
| UI/UX | 4 | 0 unlabeled buttons; ~7196ms avg step |
| Information clarity | 2 | 4 sparse-content pages |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I5** | Crawl found error pages — Paths: / | p3-admin | `crawl-graph` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-evaluator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I3** | Console errors on page — 1 console error(s): Failed to load resource: the server responded with a status of 500 (Internal Server Error) | p2-operator | `j5-runner-selftest-p1-evaluator-s1-desktop-seed1-loop1` |
| **I4** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). Timeout 15000ms exceeded.
=========================== logs ===========================
"load" event fired
============================================================ | p1-evaluator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I6** | Compare page fails on desktop with 'not found' error — The desktop version of the compare runs page fails to load initially and shows a 'not found' error on the wait step, preventing first-time users from exploring comparisons. | p1-evaluator | `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` |
| **I9** | Runs page navigation fails on first attempt across all devices — The /runs page returns null title and fails to load on initial navigate (desktop: 21.8s, tablet: 26.4s, mobile: 43.2s). The page eventually loads on subsequent wait, but the initial failure undermines reliable quick access for the operator. | p2-operator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I10** | Compare runs page navigation fails on desktop with 'not found' error — Navigating to /compare on desktop times out with error 'not found' after 41.9s, while tablet and mobile load successfully. This prevents desktop operators from using the compare feature reliably. | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I11** | Runs page initial navigation fails across all device types — Navigating to /runs from desktop, tablet, and mobile all result in failure on first attempt (step_id j2-runs-p1-evaluator-s1-desktop-seed1-loop1, -tablet-, -mobile-). The page loads only after a wait step, indicating a possible timeout or rendering issue. | p3-admin | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I12** | Compare page shows 'not found' error on desktop — On the Compare runs page (j3-compare-p1-evaluator-s2-desktop-seed1-loop1), an error 'not found' is present. This could indicate a missing resource or API endpoint, potentially affecting trust signals. | p3-admin | `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Slow step completion — Step took 19863ms (>8s perceived delay threshold). | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I7** | Initial navigation to Runs page fails on all devices (hypothesis) — The first navigation to the runs page returns a null title and failure outcome on all devices (desktop, tablet, mobile), which may confuse new users even though the page eventually loads. | p1-evaluator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I8** | Mobile Init wizard shows 'API offline' and mock data — The init wizard on mobile displays 'API offline — showing Acme mock' which may mislead first-time evaluators into thinking the product is not functional. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 29 links and 4 headings. | p1-evaluator, p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Accessible form labels — All 3 form inputs have labels or placeholders. | p3-admin | `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 24 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s2-desktop-seed1-loop1` |
| **D5** | Clear readiness score and green status on Command center — The landing page immediately shows a 92% readiness score with a green indicator, effectively communicating value to first-time users. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D6** | Init wizard works smoothly across all device types — The Init wizard page (j4-init-dogfood) navigates and interacts without errors on desktop, tablet, and mobile, demonstrating consistent cross-device behavior. | p3-admin | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **D7** | Self-dogfooding integration is clearly presented — The Init wizard page includes a 'Dogfood this dashboard' feature and instructions for using the dashboard to test itself, which aligns with admin interests in trust and verification. | p3-admin | `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` |

---

## Run log

| Step | Journey | Action | Outcome | URL |
|------|---------|--------|---------|-----|
| `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` | j1-command-center | navigate | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s2-desktop-seed1-loop1` | j1-command-center | wait | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s1-tablet-seed1-loop1` | j1-command-center | navigate | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s2-tablet-seed1-loop1` | j1-command-center | wait | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s1-mobile-seed1-loop1` | j1-command-center | navigate | pass | http://127.0.0.1:8081/ |
| `j1-command-center-p1-evaluator-s2-mobile-seed1-loop1` | j1-command-center | wait | pass | http://127.0.0.1:8081/ |
| `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` | j2-runs | navigate | fail | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-desktop-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s1-tablet-seed1-loop1` | j2-runs | navigate | fail | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-tablet-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` | j2-runs | navigate | fail | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-mobile-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` | j3-compare | navigate | fail | http://127.0.0.1:8081/compare |
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

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
