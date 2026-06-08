# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `enterprise-20260530-045757` |
| **Date** | 2026-05-30 |
| **Target** | https://faculty-dashboard-eight.vercel.app |
| **Product** | Enterprise Dashboard (example) |
| **Outcome** | complete |
| **Duration** | 279s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Red** |
| **Top blocker** | Auth wall on deep link |
| **Top delight** | Interactive forms discovered |
| **Issues** | 5 |
| **Delights** | 1 |

| **Pages crawled** | 1 |
| **Auto journeys added** | 1 |
| **Auth** | failed_still_on_login |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-deep-link** Deep link to primary surface | **Partial** | **Partial** | **Partial** |
| **j2-primary-list** Browse primary data view | **Partial** | **Partial** | **Partial** |
| **j3-secondary-module** Secondary module | **Partial** | **Partial** | **Partial** |
| **j4-search-surface** Search or AI surface | **Partial** | **Partial** | **Partial** |
| **j5-admin-boundary** Admin boundary check | **Partial** | **Partial** | **Partial** |
| **auto-j1-dashboard** Auto: Dashboard | **Partial** | **Partial** | **Partial** |

---

## Site map (crawl)

# Site map

**Origin:** https://faculty-dashboard-eight.vercel.app  
**Pages crawled:** 1  

## Hub pages (most outbound links)

- `/` — Argyle Analytics Dashboard

## Auth-gated (redirect to login)

- `/`

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/` | Argyle Analytics Dashboard | 0 | 0 | 1 | 22 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/` | Argyle Analytics Dashboard | 1 forms, 3 inputs, auth-gated |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 1 pages; 1 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: dashboard |
| `journey-runner` | E2E journey execution | Executed 7 steps across 6 journeys (0 failures) |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | LLM analysis failed: The read operation timed out |
| `llm-p2-operator` | LLM evaluator: Daily operator | LLM analysis failed: The read operation timed out |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | LLM analysis failed: The read operation timed out |
| `synthesizer` | Cross-agent synthesis | Synthesized 5 issues, 1 delights from 9 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 2 | 14% steps pass; 0 failures |
| UI/UX | 2 | 14 unlabeled buttons; ~844ms avg step |
| Information clarity | 5 | 0 sparse-content pages |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I4** | Authentication setup failed — Auth outcome: failed_still_on_login. Set credentials env vars or fix login path labels in config. | p3-admin | `auth-setup` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Auth wall on deep link — Navigated to /database but landed on /login — workflow blocked without session. | p1-evaluator, p3-admin | `j1-deep-link-p1-evaluator-s1` |
| **I2** | Icon-only or unlabeled buttons — 2 button(s) lack accessible name on page. | p2-operator, p3-admin | `j1-deep-link-p1-evaluator-s1` |
| **I3** | Form inputs missing labels — 1 of 3 inputs lack label, aria-label, or placeholder. | p1-evaluator, p3-admin | `j1-deep-link-p1-evaluator-s1` |
| **I5** | Auth-gated routes without login surface in crawl — Some paths redirect to login but no /login-style route was classified — wayfinding gap. | p1-evaluator | `workflow-graph` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Interactive forms discovered — 1 pages with forms — workflow automation candidate. | p1-evaluator | `crawl-graph` |

---

## Run log

| Step | Journey | Action | Outcome | URL |
|------|---------|--------|---------|-----|
| `j1-deep-link-p1-evaluator-s1` | j1-deep-link | navigate | partial | https://faculty-dashboard-eight.vercel.app/login |
| `j2-primary-list-p1-evaluator-s1` | j2-primary-list | navigate | partial | https://faculty-dashboard-eight.vercel.app/login |
| `j2-primary-list-p1-evaluator-s2` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j3-secondary-module-p1-evaluator-s1` | j3-secondary-module | navigate | partial | https://faculty-dashboard-eight.vercel.app/login |
| `j4-search-surface-p1-evaluator-s1` | j4-search-surface | navigate | partial | https://faculty-dashboard-eight.vercel.app/login |
| `j5-admin-boundary-p1-evaluator-s1` | j5-admin-boundary | navigate | partial | https://faculty-dashboard-eight.vercel.app/login |
| `auto-j1-dashboard-p1-evaluator-s1` | auto-j1-dashboard | navigate | partial | https://faculty-dashboard-eight.vercel.app/login |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
