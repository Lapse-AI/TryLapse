# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260602-154152` |
| **Date** | 2026-06-02 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 171s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Red** |
| **Top blocker** | Console warnings on page |
| **Top delight** | Clear navigation structure |
| **Issues** | 10 |
| **Delights** | 5 |

| **Pages crawled** | 14 |
| **Auto journeys added** | 2 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Pass** | **Pass** | **Pass** |
| **j2-runs** Runs list | **Pass** | **Pass** | **Pass** |
| **j3-compare** Compare runs | **Pass** | **Pass** | **Pass** |
| **j4-init-dogfood** Init dogfood flow | **Fail** | **Fail** | **Fail** |
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
| `/` | Command center — Launch Rehearsal | 0 | 38 | 0 | 561 |
| `/agents` | Agents — Launch Rehearsal | 1 | 17 | 0 | 509 |
| `/alerts` | Alerts — Launch Rehearsal | 1 | 17 | 0 | 179 |
| `/cli` | CLI — Launch Rehearsal | 1 | 17 | 0 | 424 |
| `/compare` | Compare runs — Launch Rehearsal | 1 | 19 | 0 | 337 |
| `/config` | Workspace — Launch Rehearsal | 1 | 19 | 0 | 365 |
| `/init` |  | 1 | 0 | 0 | 0 |
| `/integrations` | Integrations — Launch Rehearsal | 1 | 17 | 0 | 152 |
| `/library` | Journey library — Launch Rehearsal | 1 | 19 | 0 | 185 |
| `/recommendations` | Recommendations — Launch Rehearsal | 1 | 23 | 0 | 239 |
| `/runner` | Runner — Launch Rehearsal | 1 | 33 | 0 | 687 |
| `/sitemap` | Site map — Launch Rehearsal | 1 | 17 | 0 | 83 |
| `/trends` | Trends — Launch Rehearsal | 1 | 17 | 0 | 535 |
| `/workflows` | Workflows — Launch Rehearsal | 1 | 17 | 0 | 310 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/config` | Workspace — Launch Rehearsal | 6 inputs |
| integration | `/integrations` | Integrations — Launch Rehearsal | — |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 14 pages; 0 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: dashboard, integration |
| `journey-runner` | E2E journey execution | Executed 54 steps across 8 journeys (3 failures, 0 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 7 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | First-time evaluator finds robust command center but encounters a critical failu |
| `llm-p2-operator` | LLM evaluator: Daily operator | The dashboard mostly works well for daily operators, but the Init wizard page ha |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | The dashboard is generally functional, but the Init wizard page fails to load on |
| `synthesizer` | Cross-agent synthesis | Synthesized 10 issues, 5 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 4 | 94% steps pass; 3 failures |
| UI/UX | 5 | 0 unlabeled buttons; ~2017ms avg step |
| Information clarity | 2 | 3 sparse-content pages |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I6** | Crawl found error pages — Paths: /init | p3-admin | `crawl-graph` |
| **I7** | Init wizard page fails to load on first navigation — On all device sizes, navigating to /init results in a 15-second timeout and blank page. The page only loads after a subsequent wait step. This blocks first-time users from exploring the setup wizard. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I3** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I4** | Form inputs missing labels — 4 of 19 inputs lack label, aria-label, or placeholder. | p1-evaluator, p3-admin | `j4-init-dogfood-p1-evaluator-s2-desktop-seed1-loop1` |
| **I5** | Console noise spike across run — Captured 0 console error(s) and 16 warning(s) across canonical steps — review network-log and step artifacts. | p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I9** | Init wizard page loads slowly or fails on initial navigation — On all form factors, navigating to /init resulted in a 15-second timeout before the page eventually loaded on subsequent wait steps. This could delay operators trying to configure a new rehearsal. | p2-operator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I10** | /init page fails to load on initial navigation — The Init wizard page fails to load on first navigation across all form factors (desktop, tablet, mobile), returning blank page for ~15 seconds before succeeding on retry. This could undermine admin confidence in access boundaries and trust signals. | p3-admin | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Console warnings on page — 16 warning(s): Generated path "/runs/" for route "/runs/$runId" matched route "/runs/" instead. This can happen when multiple route tem | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I2** | Slow step completion — Step took 15258ms (>8s perceived delay threshold). | p2-operator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I8** | Mobile command center shows duplicate header text — On mobile, the header displays 'Self-test (this UI)' twice, which may confuse new users about the current section. | p1-evaluator | `j1-command-center-p1-evaluator-s1-mobile-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 19 links and 1 headings. | p1-evaluator, p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Accessible form labels — All 6 form inputs have labels or placeholders. | p3-admin | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 51 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D5** | Live rollup provides clear value proposition — The command center explicitly describes its purpose: 'Pre-launch readiness, observed. Live rollup of every persona × journey rehearsal against 127.0.0.1:8081.' This helps first-time evaluators immediately understand the product's core value. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |

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
| `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` | j4-init-dogfood | navigate | fail | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s2-desktop-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s3-desktop-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s4-desktop-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s5-desktop-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s1-tablet-seed1-loop1` | j4-init-dogfood | navigate | fail | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s2-tablet-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s3-tablet-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s4-tablet-seed1-loop1` | j4-init-dogfood | click | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s5-tablet-seed1-loop1` | j4-init-dogfood | wait | pass | http://127.0.0.1:8081/init |
| `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` | j4-init-dogfood | navigate | fail | http://127.0.0.1:8081/init |
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
