# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `argyle-20260531-000517` |
| **Date** | 2026-05-31 |
| **Target** | https://faculty-dashboard-eight.vercel.app |
| **Product** | Argyle Faculty Dashboard |
| **Outcome** | complete |
| **Duration** | 128s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Green** |
| **Top blocker** | Icon-only or unlabeled buttons |
| **Top delight** | Clear navigation structure |
| **Issues** | 6 |
| **Delights** | 9 |

| **Pages crawled** | 16 |
| **Auto journeys added** | 0 |
| **Auth** | success |
| **Parallel seeds** | 3 |
| **Flaky steps** | 0 |

---

## Persona × journey matrix

| Journey | P1 First-time | P2 Daily | P3 Admin |
|---------|--------|--------|--------|
| **j1-deep-link** Deep link and pagination at sc | **Pass** | **Pass** | **Partial** |
| **j2-primary-list** Keyword and city filters | **Pass** | **Partial** | **Pass** |
| **j3-profile** View candidate profile | **Pass** | **Pass** | **Pass** |
| **j4-analytics** Analytics overview | **Pass** | **Pass** | **Pass** |
| **j5-admin-boundary** Admin boundary check | **Pass** | **Pass** | **Pass** |

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
| `journey-runner` | E2E journey execution | Executed 57 steps across 5 journeys (0 failures, 0 flaky steps, seeds=3) |
| `persona-p1-evaluator` | Evaluator: First-time evaluator (prospect / new user) | Analysis from prospect / new user perspective |
| `persona-p2-operator` | Evaluator: Daily operator (power user) | Analysis from power user perspective |
| `persona-p3-admin` | Evaluator: Admin / buyer (IT admin) | Analysis from IT admin perspective |
| `llm-p1-evaluator` | LLM evaluator: First-time evaluator | First-time evaluator successfully reached database and opened a candidate profil |
| `llm-p2-operator` | LLM evaluator: Daily operator | Filtering reduces result set quickly, but pagination controls are not evident, h |
| `llm-p3-admin` | LLM evaluator: Admin / buyer | The dashboard shows candidate database functionality but the title says 'Analyti |
| `synthesizer` | Cross-agent synthesis | Synthesized 6 issues, 9 delights from 9 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 5 | 100% steps pass; 0 failures |
| UI/UX | 2 | 42 unlabeled buttons; ~1454ms avg step |
| Information clarity | 5 | 0 sparse-content pages |

---

## Issues (evidence-bound)

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | Icon-only or unlabeled buttons — 1 button(s) lack accessible name on page. | p2-operator, p3-admin | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **I2** | Form inputs missing labels — 1 of 9 inputs lack label, aria-label, or placeholder. | p1-evaluator, p3-admin | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **I4** | Pagination controls are not visible or unlabeled — After filtering, the UI shows 'Displaying 4 matching profiles' but no pagination controls are evident in the excerpts. The consistent 'unlabeled_buttons: 1' across steps suggests a button exists but lacks a label, which could be the pagination control. Without clear pagination, the operator cannot efficiently browse through large result sets. | p2-operator | `j2-primary-list-p1-evaluator-s4-seed1-loop1` |
| **I5** | Misleading page title: 'Analytics Dashboard' shows candidate database instead of analytics — The page is titled 'Argyle Analytics Dashboard' but the content is a candidate database browser. Admin buyers seeking analytics may be misled. | p3-admin | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I3** | Unlabeled button present on page — Each step log indicates one unlabeled button. For a first-time user, this lack of label may cause confusion about its function. | p1-evaluator | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **I6** | Unlabeled button on candidate database page — One or more buttons lack visible labels, reducing clarity for admin users managing data. | p3-admin | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Clear navigation structure — Page has 16 links and 2 headings. | p1-evaluator, p2-operator | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **D2** | Informative landing content — Page includes headings and substantive body copy for first-time evaluators. | p1-evaluator | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **D3** | Interactive forms discovered — 1 pages with forms — workflow automation candidate. | p1-evaluator | `crawl-graph` |
| **D4** | Multi-workflow product surface — Discovered workflow types: admin, dashboard, search. | p1-evaluator, p2-operator, p3-admin | `workflow-graph` |
| **D5** | Fast interactions for repeat tasks — 54 steps completed under 3s. | p2-operator | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **D6** | Helpful semantic search prompt — The page offers example queries like 'Python developers with 5+ years experience in Mumbai', which helps new users understand how to use the AI search. | p1-evaluator | `j1-deep-link-p1-evaluator-s1-seed1-loop1` |
| **D7** | Fast and responsive filtering — Filtering reduces the profile count from 1809 to 4 almost instantly (fill action takes ~50-70ms), allowing quick narrowing of candidate results. | p2-operator | `j2-primary-list-p1-evaluator-s3-seed1-loop1` |
| **D8** | Efficient filtering reduces results from 1809 to 4 based on search terms — The search/filter functionality quickly narrows down candidates, demonstrating data management capability. | p3-admin | `j2-primary-list-p1-evaluator-s3-seed1-loop1` |
| **D9** | Comprehensive candidate profile with skills, experience, and work history — Profile page provides detailed information, aiding admin verification of candidate data. | p3-admin | `j3-profile-p1-evaluator-s5-seed1-loop1` |

---

## Run log

| Step | Journey | Action | Outcome | URL |
|------|---------|--------|---------|-----|
| `j1-deep-link-p1-evaluator-s1-seed1-loop1` | j1-deep-link | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s2-seed1-loop1` | j1-deep-link | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s3-seed1-loop1` | j1-deep-link | click | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s4-seed1-loop1` | j1-deep-link | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s1-seed2-loop1` | j1-deep-link | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s2-seed2-loop1` | j1-deep-link | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s3-seed2-loop1` | j1-deep-link | click | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s4-seed2-loop1` | j1-deep-link | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s1-seed3-loop1` | j1-deep-link | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s2-seed3-loop1` | j1-deep-link | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s3-seed3-loop1` | j1-deep-link | click | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j1-deep-link-p1-evaluator-s4-seed3-loop1` | j1-deep-link | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s1-seed1-loop1` | j2-primary-list | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s2-seed1-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s3-seed1-loop1` | j2-primary-list | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s4-seed1-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s5-seed1-loop1` | j2-primary-list | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s6-seed1-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s1-seed2-loop1` | j2-primary-list | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s2-seed2-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s3-seed2-loop1` | j2-primary-list | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s4-seed2-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s5-seed2-loop1` | j2-primary-list | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s6-seed2-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s1-seed3-loop1` | j2-primary-list | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s2-seed3-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s3-seed3-loop1` | j2-primary-list | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s4-seed3-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s5-seed3-loop1` | j2-primary-list | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j2-primary-list-p1-evaluator-s6-seed3-loop1` | j2-primary-list | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s1-seed1-loop1` | j3-profile | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s2-seed1-loop1` | j3-profile | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s3-seed1-loop1` | j3-profile | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s4-seed1-loop1` | j3-profile | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s5-seed1-loop1` | j3-profile | open_link | pass | https://faculty-dashboard-eight.vercel.app/database/profile/ |
| `j3-profile-p1-evaluator-s1-seed2-loop1` | j3-profile | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s2-seed2-loop1` | j3-profile | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s3-seed2-loop1` | j3-profile | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s4-seed2-loop1` | j3-profile | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s5-seed2-loop1` | j3-profile | open_link | pass | https://faculty-dashboard-eight.vercel.app/database/profile/ |
| `j3-profile-p1-evaluator-s1-seed3-loop1` | j3-profile | navigate | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s2-seed3-loop1` | j3-profile | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s3-seed3-loop1` | j3-profile | fill | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s4-seed3-loop1` | j3-profile | wait | pass | https://faculty-dashboard-eight.vercel.app/database |
| `j3-profile-p1-evaluator-s5-seed3-loop1` | j3-profile | open_link | pass | https://faculty-dashboard-eight.vercel.app/database/profile/ |
| `j4-analytics-p1-evaluator-s1-seed1-loop1` | j4-analytics | navigate | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j4-analytics-p1-evaluator-s2-seed1-loop1` | j4-analytics | wait | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j4-analytics-p1-evaluator-s1-seed2-loop1` | j4-analytics | navigate | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j4-analytics-p1-evaluator-s2-seed2-loop1` | j4-analytics | wait | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j4-analytics-p1-evaluator-s1-seed3-loop1` | j4-analytics | navigate | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j4-analytics-p1-evaluator-s2-seed3-loop1` | j4-analytics | wait | pass | https://faculty-dashboard-eight.vercel.app/analytics |
| `j5-admin-boundary-p1-evaluator-s1-seed1-loop1` | j5-admin-boundary | navigate | pass | https://faculty-dashboard-eight.vercel.app/admin |
| `j5-admin-boundary-p1-evaluator-s2-seed1-loop1` | j5-admin-boundary | wait | pass | https://faculty-dashboard-eight.vercel.app/admin |
| `j5-admin-boundary-p1-evaluator-s1-seed2-loop1` | j5-admin-boundary | navigate | pass | https://faculty-dashboard-eight.vercel.app/admin |
| `j5-admin-boundary-p1-evaluator-s2-seed2-loop1` | j5-admin-boundary | wait | pass | https://faculty-dashboard-eight.vercel.app/admin |
| `j5-admin-boundary-p1-evaluator-s1-seed3-loop1` | j5-admin-boundary | navigate | pass | https://faculty-dashboard-eight.vercel.app/admin |
| `j5-admin-boundary-p1-evaluator-s2-seed3-loop1` | j5-admin-boundary | wait | pass | https://faculty-dashboard-eight.vercel.app/admin |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
