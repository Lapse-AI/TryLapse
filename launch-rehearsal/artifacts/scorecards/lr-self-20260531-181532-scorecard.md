# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260531-181532` |
| **Date** | 2026-05-31 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 444s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Amber** |
| **Top blocker** | Slow step completion |
| **Top delight** | Clear navigation structure |
| **Issues** | 8 |
| **Delights** | 7 |

| **Pages crawled** | 14 |
| **Auto journeys added** | 3 |
| **Parallel seeds** | 1 |
| **Flaky steps** | 6 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Partial** | **Partial** | **Pass** |
| **j2-runs** Runs list | **Partial** | **Pass** | **Pass** |
| **j3-compare** Compare runs | **Pass** | **Pass** | **Partial** |
| **j4-init-dogfood** Init dogfood flow | **Pass** | **Pass** | **Pass** |
| **j5-runner-selftest** Runner self-test trigger | **Pass** | **Partial** | **Pass** |
| **j6-trends** Trends monitoring | **Fail** | **Fail** | **Fail** |
| **auto-j1-dashboard** Auto: Dashboard | **Fail** | **Fail** | **Fail** |
| **auto-j3-explore** Auto: Explore /recommendations | **Fail** | **Fail** | **Fail** |
| **auto-j5-explore** Auto: Explore /library | **Pass** | **Partial** | **Pass** |

---

## Site map (crawl)

# Site map

**Origin:** http://127.0.0.1:8081  
**Pages crawled:** 14  

## Hub pages (most outbound links)

- `/` — Command center — Launch Rehearsal
- `/compare` — Compare runs — Launch Rehearsal
- `/library` — Journey library — Launch Rehearsal
- `/agents` — Agents — Launch Rehearsal
- `/alerts` — Alerts — Launch Rehearsal
- `/cli` — CLI — Launch Rehearsal
- `/config` — Workspace — Launch Rehearsal
- `/init` — Init wizard — Launch Rehearsal

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/` | Command center — Launch Rehearsal | 0 | 29 | 0 | 372 |
| `/agents` | Agents — Launch Rehearsal | 1 | 16 | 0 | 450 |
| `/alerts` | Alerts — Launch Rehearsal | 1 | 16 | 0 | 151 |
| `/cli` | CLI — Launch Rehearsal | 1 | 16 | 0 | 334 |
| `/compare` | Compare runs — Launch Rehearsal | 1 | 18 | 0 | 261 |
| `/config` | Workspace — Launch Rehearsal | 1 | 16 | 0 | 356 |
| `/init` | Init wizard — Launch Rehearsal | 1 | 17 | 0 | 266 |
| `/integrations` | Integrations — Launch Rehearsal | 1 | 16 | 0 | 124 |
| `/library` | Journey library — Launch Rehearsal | 1 | 18 | 0 | 152 |
| `/recommendations` | Recommendations — Launch Rehearsal | 1 | 21 | 0 | 199 |
| `/runner` | Runner — Launch Rehearsal | 1 | 17 | 0 | 196 |
| `/sitemap` | Site map — Launch Rehearsal | 1 | 16 | 0 | 55 |
| `/trends` | Trends — Launch Rehearsal | 1 | 16 | 0 | 308 |
| `/workflows` | Workflows — Launch Rehearsal | 1 | 16 | 0 | 240 |

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
| `journey-runner` | E2E journey execution | Executed 60 steps across 9 journeys (5 failures, 6 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 8 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | The dashboard is functional but the desktop layout may obscure core content behi |
| `llm-p2-operator` | LLM evaluator: Daily operator | The dashboard provides a reliable and efficient experience for daily operators,  |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Admin/buyer evaluation finds a mobile compare page error that undermines trust s |
| `synthesizer` | Cross-agent synthesis | Synthesized 8 issues, 7 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 4 | 92% steps pass; 5 failures |
| UI/UX | 4 | 0 unlabeled buttons; ~6103ms avg step |
| Information clarity | 2 | 5 sparse-content pages |

---

## Issues (evidence-bound)

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-evaluator | `auto-j3-explore-p1-evaluator-s1-desktop-seed1-loop1` |
| **I4** | Console noise spike across run — Captured 0 console error(s) and 8 warning(s) across canonical steps — review network-log and step artifacts. | p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I5** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I6** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). | p1-evaluator | `j6-trends-p1-evaluator-s1-desktop-seed1-loop1` |
| **I7** | Desktop view may hide main content behind navigation sidebar (hypothesis) — On desktop, the excerpts for the command center, runs, and other pages show only the navigation sidebar, suggesting the primary dashboard content (readiness score, run history) might not be visible above the fold or in the initial viewport. This could hinder a first-time user from immediately understanding the product's value. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I8** | Mobile compare page shows unexplained 'failed' error — On the compare page (mobile), the errors array contains 'failed' even though the step outcome is 'pass'. This is confusing and reduces trust in the dashboard's reliability for an admin verifying access boundaries. | p3-admin | `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Slow step completion — Step took 12874ms (>8s perceived delay threshold). | p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I3** | Console warnings on page — 8 warning(s): Generated path "/runs/" for route "/runs/$runId" matched route "/runs/" instead. This can happen when multiple route tem | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 16 links and 1 headings. | p1-evaluator, p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Accessible form labels — All 3 form inputs have labels or placeholders. | p3-admin | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 43 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D5** | Init wizard provides clear onboarding with self-test YAML generation — The init wizard offers an intuitive, step-by-step guide and a button to generate a self-test YAML configuration, making it easy for new users to start dogfooding the dashboard. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` |
| **D6** | Concise readiness snapshot on command center — The command center shows a clean at-a-glance summary with readiness score, blocker count, and delight count, enabling quick status assessment. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D7** | Clear readiness score display across device sizes — The command center and runs pages consistently show the readiness score (e.g., 74 Amber, 92 Green), providing quick visibility into overall product health. | p3-admin | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |

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
| `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` | j2-runs | navigate | pass | http://127.0.0.1:8081/runs |
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
| `j6-trends-p1-evaluator-s1-tablet-seed1-loop1` | j6-trends | navigate | fail | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-tablet-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s1-mobile-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-mobile-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j1-dashboard-p1-evaluator-s1-tablet-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j1-dashboard-p1-evaluator-s1-mobile-seed1-loop1` | auto-j1-dashboard | navigate | fail | http://127.0.0.1:8081/config |
| `auto-j3-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j3-explore | navigate | fail | http://127.0.0.1:8081/recommendations |
| `auto-j3-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j3-explore | navigate | fail | http://127.0.0.1:8081/recommendations |
| `auto-j3-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j3-explore | navigate | fail | http://127.0.0.1:8081/recommendations |
| `auto-j5-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j5-explore | navigate | pass | http://127.0.0.1:8081/library |
| `auto-j5-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j5-explore | navigate | pass | http://127.0.0.1:8081/library |
| `auto-j5-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j5-explore | navigate | pass | http://127.0.0.1:8081/library |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
