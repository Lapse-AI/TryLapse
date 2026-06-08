# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260531-182333` |
| **Date** | 2026-05-31 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 180s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Green** |
| **Top blocker** | Console warnings on page |
| **Top delight** | Clear navigation structure |
| **Issues** | 5 |
| **Delights** | 7 |

| **Pages crawled** | 14 |
| **Auto journeys added** | 3 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Pass** | **Pass** | **Pass** |
| **j2-runs** Runs list | **Pass** | **Pass** | **Pass** |
| **j3-compare** Compare runs | **Partial** | **Partial** | **Partial** |
| **j4-init-dogfood** Init dogfood flow | **Pass** | **Pass** | **Pass** |
| **j5-runner** Runner page (observe only — no | **Pass** | **Pass** | **Pass** |
| **j6-trends** Trends monitoring | **Pass** | **Pass** | **Pass** |
| **auto-j1-dashboard** Auto: Dashboard | **Pass** | **Pass** | **Pass** |
| **auto-j3-explore** Auto: Explore /recommendations | **Pass** | **Pass** | **Pass** |
| **auto-j5-explore** Auto: Explore /library | **Pass** | **Pass** | **Pass** |

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
| `/` | Command center — Launch Rehearsal | 0 | 29 | 0 | 345 |
| `/agents` | Agents — Launch Rehearsal | 1 | 16 | 0 | 487 |
| `/alerts` | Alerts — Launch Rehearsal | 1 | 16 | 0 | 151 |
| `/cli` | CLI — Launch Rehearsal | 1 | 16 | 0 | 334 |
| `/compare` | Compare runs — Launch Rehearsal | 1 | 18 | 0 | 195 |
| `/config` | Workspace — Launch Rehearsal | 1 | 16 | 0 | 356 |
| `/init` | Init wizard — Launch Rehearsal | 1 | 17 | 0 | 272 |
| `/integrations` | Integrations — Launch Rehearsal | 1 | 16 | 0 | 124 |
| `/library` | Journey library — Launch Rehearsal | 1 | 18 | 0 | 160 |
| `/recommendations` | Recommendations — Launch Rehearsal | 1 | 23 | 0 | 282 |
| `/runner` | Runner — Launch Rehearsal | 1 | 17 | 0 | 280 |
| `/sitemap` | Site map — Launch Rehearsal | 1 | 16 | 0 | 55 |
| `/trends` | Trends — Launch Rehearsal | 1 | 16 | 0 | 290 |
| `/workflows` | Workflows — Launch Rehearsal | 1 | 16 | 0 | 248 |

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
| `journey-runner` | E2E journey execution | Executed 57 steps across 9 journeys (0 failures, 0 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 9 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | Landing page and runs overview provide clear value, but compare page has a 'not  |
| `llm-p2-operator` | LLM evaluator: Daily operator | Dashboard navigates correctly across viewports, but mobile compare page shows 'n |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Command center and runs pages load correctly across viewports; mobile compare pa |
| `synthesizer` | Cross-agent synthesis | Synthesized 5 issues, 7 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 5 | 100% steps pass; 0 failures |
| UI/UX | 5 | 0 unlabeled buttons; ~1355ms avg step |
| Information clarity | 5 | 0 sparse-content pages |

---

## Issues (evidence-bound)

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Console noise spike across run — Captured 0 console error(s) and 8 warning(s) across canonical steps — review network-log and step artifacts. | p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I3** | Compare page shows 'not found' error on mobile viewports — On mobile, the compare page logs a 'not found' error, which may mislead a first-time evaluator into thinking the feature is broken or incomplete. Desktop and tablet viewports do not exhibit this issue. | p1-evaluator | `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` |
| **I4** | Mobile compare page displays 'not found' errors — The mobile version of the compare runs page (j3-compare) logs 'not found' errors, which may indicate broken API calls or missing data. This could prevent operators from reliably comparing runs on mobile devices. | p2-operator | `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Console warnings on page — 8 warning(s): Generated path "/runs/" for route "/runs/$runId" matched route "/runs/" instead. This can happen when multiple route tem | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I5** | Mobile compare page has 'not found' errors — On mobile viewport, the Compare runs page logs 'not found' errors, indicating missing resources (e.g., scripts, styles, or API endpoints). While the page loads, this may erode admin confidence in reliability. | p3-admin | `j3-compare-p1-evaluator-s1-mobile-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 16 links and 1 headings. | p1-evaluator, p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Accessible form labels — All 2 form inputs have labels or placeholders. | p3-admin | `auto-j3-explore-p1-evaluator-s1-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 55 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s2-desktop-seed1-loop1` |
| **D5** | Clear setup instructions in Init wizard — The Init wizard provides straightforward steps and a 'Generate self-test YAML' button, making it easy for a first-time user to understand how to configure and run rehearsals. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` |
| **D6** | Command center shows latest run summary with blockers and delights — The landing page displays a concise summary of the latest run, including blocker and delight counts, quickly communicating the product's value and status. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D7** | Responsive design works seamlessly across devices — The command center loads and functions without issues on desktop, tablet, and mobile viewports, enabling operators to complete core tasks on any device. | p2-operator | `j1-command-center-p1-evaluator-s1-mobile-seed1-loop1` |

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
| `auto-j3-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j3-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j3-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j3-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j3-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j3-explore | navigate | pass | http://127.0.0.1:8081/recommendations |
| `auto-j5-explore-p1-evaluator-s1-desktop-seed1-loop1` | auto-j5-explore | navigate | pass | http://127.0.0.1:8081/library |
| `auto-j5-explore-p1-evaluator-s1-tablet-seed1-loop1` | auto-j5-explore | navigate | pass | http://127.0.0.1:8081/library |
| `auto-j5-explore-p1-evaluator-s1-mobile-seed1-loop1` | auto-j5-explore | navigate | pass | http://127.0.0.1:8081/library |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
