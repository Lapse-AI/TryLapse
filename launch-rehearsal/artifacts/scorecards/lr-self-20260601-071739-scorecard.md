# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260601-071739` |
| **Date** | 2026-06-01 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 97s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Green** |
| **Top blocker** | Console warnings on page |
| **Top delight** | Clear navigation structure |
| **Issues** | 2 |
| **Delights** | 7 |

| **Pages crawled** | 14 |
| **Auto journeys added** | 2 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Pass** | **Pass** | **Pass** |
| **j2-runs** Runs list | **Pass** | **Pass** | **Pass** |
| **j3-compare** Compare runs | **Pass** | **Pass** | **Pass** |
| **j4-init-dogfood** Init dogfood flow | **Pass** | **Pass** | **Pass** |
| **j5-runner** Runner page (observe only — no | **Pass** | **Pass** | **Pass** |
| **j6-trends** Trends monitoring | **Pass** | **Pass** | **Pass** |
| **auto-j1-dashboard** Auto: Dashboard | **Pass** | **Pass** | **Pass** |
| **auto-j4-explore** Auto: Explore /recommendations | **Pass** | **Pass** | **Pass** |

---

## Site map (crawl)

# Site map

**Origin:** http://127.0.0.1:8081  
**Pages crawled:** 14  

## Hub pages (most outbound links)

- `/runner` — Runner — Launch Rehearsal
- `/` — Command center — Launch Rehearsal
- `/compare` — Compare runs — Launch Rehearsal
- `/library` — Journey library — Launch Rehearsal
- `/agents` — Agents — Launch Rehearsal
- `/alerts` — Alerts — Launch Rehearsal
- `/cli` — CLI — Launch Rehearsal
- `/config` — Workspace — Launch Rehearsal

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/` | Command center — Launch Rehearsal | 0 | 36 | 0 | 546 |
| `/agents` | Agents — Launch Rehearsal | 1 | 16 | 0 | 511 |
| `/alerts` | Alerts — Launch Rehearsal | 1 | 16 | 0 | 168 |
| `/cli` | CLI — Launch Rehearsal | 1 | 16 | 0 | 413 |
| `/compare` | Compare runs — Launch Rehearsal | 1 | 18 | 0 | 350 |
| `/config` | Workspace — Launch Rehearsal | 1 | 18 | 0 | 315 |
| `/init` | Init wizard — Launch Rehearsal | 1 | 18 | 0 | 351 |
| `/integrations` | Integrations — Launch Rehearsal | 1 | 16 | 0 | 141 |
| `/library` | Journey library — Launch Rehearsal | 1 | 18 | 0 | 174 |
| `/recommendations` | Recommendations — Launch Rehearsal | 1 | 23 | 0 | 256 |
| `/runner` | Runner — Launch Rehearsal | 1 | 29 | 0 | 660 |
| `/sitemap` | Site map — Launch Rehearsal | 1 | 16 | 0 | 72 |
| `/trends` | Trends — Launch Rehearsal | 1 | 16 | 0 | 475 |
| `/workflows` | Workflows — Launch Rehearsal | 1 | 16 | 0 | 297 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/config` | Workspace — Launch Rehearsal | 3 inputs |
| integration | `/integrations` | Integrations — Launch Rehearsal | — |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 14 pages; 0 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: dashboard, integration |
| `journey-runner` | E2E journey execution | Executed 54 steps across 8 journeys (0 failures, 0 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 8 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | The dashboard is fully functional and clearly presents rehearsal results, enabli |
| `llm-p2-operator` | LLM evaluator: Daily operator | All core journeys (command center, runs, compare, init wizard, runner) completed |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | All journeys pass with no errors; readiness dashboard provides clear trust signa |
| `synthesizer` | Cross-agent synthesis | Synthesized 2 issues, 7 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 5 | 100% steps pass; 0 failures |
| UI/UX | 5 | 0 unlabeled buttons; ~1196ms avg step |
| Information clarity | 5 | 0 sparse-content pages |

---

## Issues (evidence-bound)

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Console noise spike across run — Captured 0 console error(s) and 16 warning(s) across canonical steps — review network-log and step artifacts. | p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Console warnings on page — 16 warning(s): Generated path "/runs/" for route "/runs/$runId" matched route "/runs/" instead. This can happen when multiple route tem | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 18 links and 1 headings. | p1-evaluator, p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Accessible form labels — All 3 form inputs have labels or placeholders. | p3-admin | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 54 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D5** | Clear at-a-glance readiness score — The command center displays a prominent green readiness score (94) and latest run summary, instantly communicating the product's health and value. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D6** | Consistent performance across devices — All journeys passed on desktop, tablet, and mobile with sub-2-second page loads and no errors, enabling reliable daily operations. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D7** | Clear readiness score and blocker count — The command center and runs pages prominently display a readiness score of 94 (Green) and zero blockers, giving the admin immediate trust in the current state. | p3-admin | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |

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
| `j5-runner-p1-evaluator-s1-desktop-seed1-loop1` | j5-runner | navigate | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s2-desktop-seed1-loop1` | j5-runner | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s3-desktop-seed1-loop1` | j5-runner | assert_url_contains | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s1-tablet-seed1-loop1` | j5-runner | navigate | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s2-tablet-seed1-loop1` | j5-runner | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s3-tablet-seed1-loop1` | j5-runner | assert_url_contains | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s1-mobile-seed1-loop1` | j5-runner | navigate | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s2-mobile-seed1-loop1` | j5-runner | wait | pass | http://127.0.0.1:8081/runner |
| `j5-runner-p1-evaluator-s3-mobile-seed1-loop1` | j5-runner | assert_url_contains | pass | http://127.0.0.1:8081/runner |
| `j6-trends-p1-evaluator-s1-desktop-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-desktop-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s1-tablet-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-tablet-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s1-mobile-seed1-loop1` | j6-trends | navigate | pass | http://127.0.0.1:8081/trends |
| `j6-trends-p1-evaluator-s2-mobile-seed1-loop1` | j6-trends | wait | pass | http://127.0.0.1:8081/trends |
| `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j1-dashboard-p1-evaluator-s1-tablet-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j1-dashboard-p1-evaluator-s1-mobile-seed1-loop1` | auto-j1-dashboard | navigate | pass | http://127.0.0.1:8081/config |
| `auto-j4-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j4-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j4-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j4-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j4-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j4-explore | navigate | pass | http://127.0.0.1:8081/recommendations |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
