# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `lr-self-20260531-181742` |
| **Date** | 2026-05-31 |
| **Target** | http://127.0.0.1:8081 |
| **Product** | Launch Rehearsal Dashboard |
| **Outcome** | complete |
| **Duration** | 442s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Red** |
| **Top blocker** | Slow step completion |
| **Top delight** | Clear navigation structure |
| **Issues** | 18 |
| **Delights** | 9 |

| **Pages crawled** | 1 |
| **Auto journeys added** | 0 |
| **Parallel seeds** | 1 |
| **Flaky steps** | 9 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-command-center** Command center | **Pass** | **Partial** | **Pass** |
| **j2-runs** Runs list | **Fail** | **Fail** | **Fail** |
| **j3-compare** Compare runs | **Fail** | **Fail** | **Fail** |
| **j4-init-dogfood** Init dogfood flow | **Fail** | **Fail** | **Fail** |
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
| `journey-runner` | E2E journey execution | Executed 51 steps across 6 journeys (3 failures, 9 flaky steps, seeds=1, viewpor |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 4 journey(s); no threshold breaches |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | First-time evaluator sees a responsive dashboard with readiness scores, but expe |
| `llm-p2-operator` | LLM evaluator: Daily operator | Dashboard generally functional but has partial failures on runs, compare, and in |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Dashboard mostly functional but intermittent navigation failures on mobile and d |
| `synthesizer` | Cross-agent synthesis | Synthesized 18 issues, 9 delights from 10 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 4 | 94% steps pass; 3 failures |
| UI/UX | 4 | 0 unlabeled buttons; ~7118ms avg step |
| Information clarity | 2 | 3 sparse-content pages |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I9** | Crawl found error pages — Paths: / | p3-admin | `crawl-graph` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-evaluator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I3** | Console errors on page — 1 console error(s): A tree hydrated but some attributes of the server rendered HTML didn't match the client properties. This won't be patche | p2-operator | `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` |
| **I5** | Console noise spike across run — Captured 2 console error(s) and 8 warning(s) across canonical steps — review network-log and step artifacts. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I6** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). | p1-evaluator | `j2-runs-p1-evaluator-s1-desktop-seed1-loop1` |
| **I7** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). Timeout 15000ms exceeded.
=========================== logs ===========================
"load" event fired
============================================================ | p1-evaluator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I8** | Flaky step (navigate) — FLAKY: outcomes differ across seeds (fail, pass). Timeout 15000ms exceeded.
=========================== logs ===========================
"load" event fired
============================================================ | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I10** | Intermittent page load failure on mobile for Runs page — The initial navigation to /runs on mobile resulted in a blank page with null title. The page loaded successfully on a subsequent wait, but the failure may confuse first-time users. | p1-evaluator | `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` |
| **I11** | Intermittent page load failure on desktop for Compare runs page — The initial navigation to /compare on desktop resulted in a blank page with null title. The page loaded successfully on a subsequent wait, but the failure may hinder understanding of the product. | p1-evaluator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I12** | Intermittent page load failure on desktop for Init wizard page — The initial navigation to /init on desktop resulted in a blank page with null title. The page loaded successfully on a subsequent wait, but the failure may impede the onboarding process. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I13** | Runs page fails to load on mobile — The mobile navigation to /runs resulted in a null title and no content, likely a timeout or rendering issue. | p2-operator | `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` |
| **I14** | Compare runs page fails to load on desktop — The desktop navigation to /compare returned a null title and empty content, preventing quick side-by-side comparison. | p2-operator | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I15** | Init wizard page fails to load on desktop — The desktop navigation to /init returned a null title and empty content, blocking the setup flow. | p2-operator | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |
| **I16** | Mobile navigation to Runs page fails on first attempt — Step j2-runs-p1-evaluator-s1-mobile-seed1-loop1 outcome is 'fail' with no title and empty errors. The page eventually loads on a subsequent wait, indicating a potential timeout or rendering issue on mobile. | p3-admin | `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` |
| **I17** | Desktop navigation to Compare runs page fails on first load — Step j3-compare-p1-evaluator-s1-desktop-seed1-loop1 outcome is 'fail' with no title and empty errors. A subsequent wait succeeds, suggesting the initial navigation experienced a failure. | p3-admin | `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` |
| **I18** | Desktop navigation to Init wizard page fails on first load — Step j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1 outcome is 'fail' with no title and empty errors. The page loads on retry, indicating a reliability issue. | p3-admin | `j4-init-dogfood-p1-evaluator-s1-desktop-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Slow step completion — Step took 17728ms (>8s perceived delay threshold). | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **I4** | Console warnings on page — 8 warning(s): Generated path "/runs/" for route "/runs/$runId" matched route "/runs/" instead. This can happen when multiple route tem | p2-operator | `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 29 links and 4 headings. | p1-evaluator, p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D3** | Accessible form labels — All 3 form inputs have labels or placeholders. | p3-admin | `j3-compare-p1-evaluator-s2-desktop-seed1-loop1` |
| **D4** | Fast interactions for repeat tasks — 25 steps completed under 3s. | p2-operator | `j1-command-center-p1-evaluator-s2-desktop-seed1-loop1` |
| **D5** | Clear readiness score and summary on the Command Center — The Command Center displays a prominent readiness score (92 Green) and summary of blockers/delights, helping new users quickly assess the product's value. | p1-evaluator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D6** | Guided init wizard with clear steps for setup — The Init wizard provides a structured, step-by-step setup process that mirrors the CLI, making it easy for first-time users to get started. | p1-evaluator | `j4-init-dogfood-p1-evaluator-s2-desktop-seed1-loop1` |
| **D7** | Quick-readiness indicator on command center — The command center prominently displays a green readiness score (92) and time ago, giving operators an instant health check. | p2-operator | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |
| **D8** | Self-test YAML generation from init wizard — The init wizard on mobile offers a clear 'Generate self-test YAML' button, streamlining the setup process. | p2-operator | `j4-init-dogfood-p1-evaluator-s1-mobile-seed1-loop1` |
| **D9** | Clear readiness score on Command center — The Command center displays a '92 · Green' readiness score alongside recent run details, providing immediate trust signals about the product's health. | p3-admin | `j1-command-center-p1-evaluator-s1-desktop-seed1-loop1` |

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
| `j2-runs-p1-evaluator-s1-mobile-seed1-loop1` | j2-runs | navigate | fail | http://127.0.0.1:8081/runs |
| `j2-runs-p1-evaluator-s2-mobile-seed1-loop1` | j2-runs | wait | pass | http://127.0.0.1:8081/runs |
| `j3-compare-p1-evaluator-s1-desktop-seed1-loop1` | j3-compare | navigate | fail | http://127.0.0.1:8081/compare |
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
