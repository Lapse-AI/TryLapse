# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `enterprise-20260530-234459` |
| **Date** | 2026-05-30 |
| **Target** | https://faculty-dashboard-eight.vercel.app |
| **Product** | Enterprise Dashboard (example) |
| **Outcome** | complete |
| **Duration** | 45s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Green** |
| **Top blocker** | Icon-only or unlabeled buttons |
| **Top delight** | Clear navigation structure |
| **Issues** | 5 |
| **Delights** | 7 |

| **Pages crawled** | 16 |
| **Auto journeys added** | 2 |
| **Auth** | success |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-deep-link** Deep link to primary surface | **Pass** | **Pass** | **Pass** |
| **j2-primary-list** Browse primary data view | **Pass** | **Pass** | **Pass** |
| **j3-secondary-module** Secondary module | **Pass** | **Pass** | **Pass** |
| **j4-search-surface** Search or AI surface | **Pass** | **Pass** | **Pass** |
| **j5-admin-boundary** Admin boundary check | **Pass** | **Pass** | **Pass** |
| **auto-j1-dashboard** Auto: Dashboard | **Pass** | **Pass** | **Pass** |
| **auto-j5-explore** Auto: Explore /database/profil | **Pass** | **Pass** | **Pass** |

---

## Site map (crawl)

# Site map

**Origin:** https://faculty-dashboard-eight.vercel.app  
**Pages crawled:** 16  

## Hub pages (most outbound links)

- `/database` — Argyle Analytics Dashboard
- `/` — Argyle Analytics Dashboard
- `/admin` — Argyle Analytics Dashboard
- `/ai-search` — Argyle Analytics Dashboard
- `/analytics` — Argyle Analytics Dashboard
- `/resume-parser-gemini` — Argyle Analytics Dashboard
- `/database/profile/03ea1ef9-cb02-4e5d-b4b6-b6fff1d94512` — Argyle Analytics Dashboard
- `/database/profile/276a7cf3-a290-4557-83b2-49234a146628` — Argyle Analytics Dashboard

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/` | Argyle Analytics Dashboard | 0 | 6 | 0 | 49 |
| `/admin` | Argyle Analytics Dashboard | 1 | 6 | 0 | 57 |
| `/ai-search` | Argyle Analytics Dashboard | 1 | 6 | 1 | 48 |
| `/analytics` | Argyle Analytics Dashboard | 1 | 6 | 0 | 138 |
| `/database` | Argyle Analytics Dashboard | 1 | 16 | 0 | 252 |
| `/database/profile/03ea1ef9-cb02-4e5d-b4b6-b6fff1d94512` | Argyle Analytics Dashboard | 2 | 7 | 0 | 96 |
| `/database/profile/276a7cf3-a290-4557-83b2-49234a146628` | Argyle Analytics Dashboard | 2 | 7 | 0 | 174 |
| `/database/profile/359604ac-00e5-43d1-8981-892d9eb63ae9` | Argyle Analytics Dashboard | 2 | 7 | 0 | 333 |
| `/database/profile/3efdf537-97e8-4597-b99b-a0f5d937daad` | Argyle Analytics Dashboard | 2 | 7 | 0 | 117 |
| `/database/profile/65198cc7-015b-4945-9ee6-77146595b16a` | Argyle Analytics Dashboard | 2 | 7 | 0 | 88 |
| `/database/profile/9adb256e-d8a5-4cf9-bbb8-bf9dc1daa8ae` | Argyle Analytics Dashboard | 2 | 7 | 0 | 204 |
| `/database/profile/9ae8a5ad-6371-46c8-a89c-fedc5906b3a0` | Argyle Analytics Dashboard | 2 | 7 | 0 | 130 |
| `/database/profile/b9727c77-87ba-4694-8044-5783019ed644` | Argyle Analytics Dashboard | 2 | 7 | 0 | 223 |
| `/database/profile/dcad854d-3ea2-436b-becd-789b0eb4aa6c` | Argyle Analytics Dashboard | 2 | 7 | 0 | 111 |
| `/database/profile/e96532c9-30cf-4991-ac62-5b1fdb73e321` | Argyle Analytics Dashboard | 2 | 7 | 0 | 106 |
| `/resume-parser-gemini` | Argyle Analytics Dashboard | 1 | 6 | 0 | 49 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/` | Argyle Analytics Dashboard | — |
| admin | `/admin` | Argyle Analytics Dashboard | — |
| dashboard | `/admin` | Argyle Analytics Dashboard | — |
| search | `/ai-search` | Argyle Analytics Dashboard | 1 forms |
| dashboard | `/ai-search` | Argyle Analytics Dashboard | 1 forms |
| dashboard | `/analytics` | Argyle Analytics Dashboard | — |
| dashboard | `/database` | Argyle Analytics Dashboard | 9 inputs |
| dashboard | `/resume-parser-gemini` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/03ea1ef9-cb02-4e5d-b4b6-b6fff1d94512` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/276a7cf3-a290-4557-83b2-49234a146628` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/359604ac-00e5-43d1-8981-892d9eb63ae9` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/3efdf537-97e8-4597-b99b-a0f5d937daad` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/65198cc7-015b-4945-9ee6-77146595b16a` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/9adb256e-d8a5-4cf9-bbb8-bf9dc1daa8ae` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/9ae8a5ad-6371-46c8-a89c-fedc5906b3a0` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/b9727c77-87ba-4694-8044-5783019ed644` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/dcad854d-3ea2-436b-becd-789b0eb4aa6c` | Argyle Analytics Dashboard | — |
| dashboard | `/database/profile/e96532c9-30cf-4991-ac62-5b1fdb73e321` | Argyle Analytics Dashboard | — |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 16 pages; 0 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: admin, dashboard, search |
| `journey-runner` | E2E journey execution | Executed 8 steps across 7 journeys (0 failures) |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | First-time evaluator can reach primary workflow via deep link, but unlabeled nav |
| `llm-p2-operator` | LLM evaluator: Daily operator | The candidate database dashboard is largely functional for efficient navigation, |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | Admin can navigate all pages without access errors, but a minor accessibility is |
| `synthesizer` | Cross-agent synthesis | Synthesized 5 issues, 7 delights from 9 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 5 | 100% steps pass; 0 failures |
| UI/UX | 3 | 3 unlabeled buttons; ~1180ms avg step |
| Information clarity | 5 | 0 sparse-content pages |

---

## Issues (evidence-bound)

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Icon-only or unlabeled buttons — 1 button(s) lack accessible name on page. | p2-operator, p3-admin | `j1-deep-link-p1-evaluator-s1` |
| **I2** | Form inputs missing labels — 1 of 9 inputs lack label, aria-label, or placeholder. | p1-evaluator, p3-admin | `j1-deep-link-p1-evaluator-s1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I3** | Unlabeled navigation button on dashboard — The dashboard has 1 unlabeled button, which may confuse first-time users about its function, especially when trying to navigate from a shared link. | p1-evaluator | `j1-deep-link-p1-evaluator-s1` |
| **I4** | Unlabeled button on candidate database page — The database page has one unlabeled button. For a daily operator relying on efficient navigation, this button's purpose is unclear, potentially causing confusion or extra clicks. | p2-operator | `j1-deep-link-p1-evaluator-s1` |
| **I5** | Unlabeled button on database page — One button on the database page lacks an accessible label, which may hinder screen reader users and reduce trust in accessibility compliance. | p3-admin | `j1-deep-link-p1-evaluator-s1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 16 links and 2 headings. | p1-evaluator, p2-operator | `j1-deep-link-p1-evaluator-s1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `j1-deep-link-p1-evaluator-s1` |
| **D3** | Interactive forms discovered — 1 pages with forms — workflow automation candidate. | p1-evaluator | `crawl-graph` |
| **D4** | Multi-workflow product surface — Discovered workflow types: admin, dashboard, search. | p1-evaluator, p2-operator, p3-admin | `workflow-graph` |
| **D5** | Fast interactions for repeat tasks — 8 steps completed under 3s. | p2-operator | `j1-deep-link-p1-evaluator-s1` |
| **D6** | Fast page loads from shared link — The deep link to /database loaded in 1.6 seconds, providing a quick entry to the primary workflow. | p1-evaluator | `j1-deep-link-p1-evaluator-s1` |
| **D7** | Clear user identity display — The dashboard prominently shows the logged-in user's email ('Logged in as: 0sparsh2@gmail.com'), providing a strong trust signal for admin verification. | p3-admin | `j1-deep-link-p1-evaluator-s1` |

---

## Run log

| Step | Journey | Action | Outcome | URL |
|------|---------|--------|---------|-----|
| `j1-deep-link-p1-evaluator-s1` | j1-deep-link | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s1` | j2-primary-list | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s2` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-secondary-module-p1-evaluator-s1` | j3-secondary-module | navigate | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j4-search-surface-p1-evaluator-s1` | j4-search-surface | navigate | pass | https://faculty-dashboard-eight.vercel.app/ai-search |
| `j5-admin-boundary-p1-evaluator-s1` | j5-admin-boundary | navigate | pass | https://faculty-dashboard-eight.vercel.app/admin |
| `auto-j1-dashboard-p1-evaluator-s1` | auto-j1-dashboard | navigate | pass | https://faculty-dashboard-eight.vercel.app/resume-parser-gem |
| `auto-j5-explore-p1-evaluator-s1` | auto-j5-explore | navigate | pass | https://faculty-dashboard-eight.vercel.app/database/profile/ |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
