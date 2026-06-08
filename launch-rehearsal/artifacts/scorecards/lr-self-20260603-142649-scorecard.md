# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260603-142649` |
| **Date** | 2026-06-03 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 243s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Amber** |
| **Top blocker** | Form inputs missing labels |
| **Top delight** | Clear navigation structure |
| **Issues** | 11 |
| **Delights** | 8 |

| **Pages crawled** | 14 |
| **Auto journeys added** | 2 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin | P4 Competitive |
|---------|--------|--------|--------|--------|
| **j1-command-center** Command center | **Pass** | **Pass** | **Pass** | **Pass** |
| **j2-runs** Runs list | **Pass** | **Pass** | **Pass** | **Pass** |
| **j3-compare** Compare runs | **Pass** | **Pass** | **Pass** | **Pass** |
| **j4-init-dogfood** Init dogfood flow | **Fail** | **Fail** | **Fail** | **Fail** |
| **j5-runner** Runner page (observe only — no | **Pass** | **Pass** | **Pass** | **Pass** |
| **j6-trends** Trends monitoring | **Pass** | **Pass** | **Pass** | **Pass** |
| **auto-j1-dashboard** Auto: Dashboard | **Pass** | **Pass** | **Pass** | **Pass** |
| **auto-j4-explore** Auto: Explore /recommendations | **Pass** | **Pass** | **Pass** | **Pass** |

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
| `/` | Command center — Launch Rehearsal | 0 | 38 | 0 | 592 |
| `/agents` | Agents — Launch Rehearsal | 1 | 17 | 0 | 524 |
| `/alerts` | Alerts — Launch Rehearsal | 1 | 17 | 0 | 179 |
| `/cli` | CLI — Launch Rehearsal | 1 | 17 | 0 | 424 |
| `/compare` | Compare runs — Launch Rehearsal | 1 | 19 | 0 | 449 |
| `/config` | Workspace — Launch Rehearsal | 1 | 19 | 0 | 317 |
| `/init` |  | 1 | 0 | 0 | 0 |
| `/integrations` | Integrations — Launch Rehearsal | 1 | 17 | 0 | 152 |
| `/library` | Journey library — Launch Rehearsal | 1 | 19 | 0 | 185 |
| `/recommendations` | Recommendations — Launch Rehearsal | 1 | 22 | 0 | 259 |
| `/runner` | Runner — Launch Rehearsal | 1 | 34 | 0 | 694 |
| `/sitemap` | Site map — Launch Rehearsal | 1 | 17 | 0 | 83 |
| `/trends` | Trends — Launch Rehearsal | 1 | 17 | 0 | 539 |
| `/workflows` | Workflows — Launch Rehearsal | 1 | 17 | 0 | 311 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/config` | Workspace — Launch Rehearsal | 11 inputs |
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
| `persona-p4-competitor-analyst` | Evaluator: Competitive Analyst (Competitor evaluating feature parity and gaps) | Analysis from Competitor evaluating feature parity and gaps perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | First-time evaluator sees live rehearsal status and run history, but initial nav |
| `llm-p2-operator` | LLM evaluator: Daily operator | The dashboard is largely functional and responsive, but the Init wizard journey  |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Admin can access all core pages but the Init wizard fails on first load across d |
| `llm-p4-competitor-analyst` | LLM evaluator: Competitive Analyst | The Launch Rehearsal Dashboard shows a rich feature set for competitive analysis |
| `synthesizer` | Cross-agent synthesis | Synthesized 11 issues, 8 delights from 12 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 4 | 94% steps pass; 3 failures |
| UI/UX | 5 | 0 unlabeled buttons; ~2673ms avg step |
| Information clarity | 2 | 3 sparse-content pages |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I6** | Crawl found error pages — Paths: /init | p3-admin | `crawl-graph` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Form inputs missing labels — 5 of 11 inputs lack label, aria-label, or placeholder. | p1-evaluator, p3-admin, p4-competitor-analyst | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I4** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I5** | Console noise spike across run — Captured 0 console error(s) and 16 warning(s) across canonical steps — review network-log and step artifacts. | p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **I7** | Init wizard page fails to load on first navigation attempt — On all device types, navigating to /init results in a timeout or blank page (outcome: fail) before eventually loading after a wait. This confuses new users who may think the page is broken. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I8** | Init wizard initial page load fails on first attempt — On all device sizes (desktop, tablet, mobile), the first navigation to /init fails (empty title, long duration ~15-17s) before subsequent steps succeed, indicating a timeout or rendering issue that slows down the operator. | p2-operator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I9** | Init wizard page consistently fails on first navigation — On desktop, tablet, and mobile, the first navigation to /init fails (no title, long duration ~15-17s) before succeeding on retry. This unreliability undermines trust for an admin verifying access boundaries. | p3-admin | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I10** | Init wizard page times out on first load across devices — The /init page failed to load on first navigation (timeout >15s) on desktop, tablet, and mobile, though it succeeded on retry. This could indicate a server-side bottleneck or heavy initialization that may frustrate users and suggests reliability concerns. | p4-competitor-analyst | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Console warnings on page — 16 warning(s): Generated path "/runs/" for route "/runs/$runId" matched route "/runs/" instead. This can happen when multiple route tem | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I3** | Slow step completion — Step took 15488ms (>8s perceived delay threshold). | p2-operator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I11** | Mobile command center may be missing navigation items (hypothesis) — The mobile command center excerpt shows fewer navigation links (e.g., no 'Monitor', 'Runs', 'Compare runs') compared to desktop. While this could be due to truncation or a responsive menu, it may limit feature discoverability on mobile, a potential gap for competitive parity. | p4-competitor-analyst | `j1-command-center-p1-evaluator-s1-mobile-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 19 links and 1 headings. | p1-evaluator, p2-operator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `auto-j1-dashboard-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Accessible form labels — All 2 form inputs have labels or placeholders. | p3-admin, p4-competitor-analyst | `auto-j4-explore-p1-evaluator-s1-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 48 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D5** | Live rehearsal status displayed prominently on command center — The command center shows a live rehearsal job with status 'running', giving immediate visibility into ongoing activity. | p1-evaluator | `j1-command-center-p1-evaluator-s2-desktop-seed1-loop1` |
| **D6** | Run history with clear summary of completed and live runs — The Runs page shows a concise summary of 1 live and 31 completed runs, making it easy to understand system activity at a glance. | p1-evaluator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **D7** | Run comparison with 'Diff last two' button — The Runs page includes a 'Diff last two' button that enables quick side-by-side comparison of recent runs, a powerful feature for competitive analysts tracking changes over time. | p4-competitor-analyst | `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` |
| **D8** | Dogfood self-test capability — The Init wizard provides a 'Dogfood this dashboard' feature that allows users to test the dashboard itself, showcasing a unique differentiator and a strong selling point for competitive advantage. | p4-competitor-analyst | `j4-init-dogfood-p1-evaluator-s2-mobile-seed1-loop1` |

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
