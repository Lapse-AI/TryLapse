# Launch Rehearsal — Scorecard

| Field | Value |
|-------|--------|
| **Run ID** | `argyle-20260608-002317` |
| **Date** | 2026-06-08 |
| **Target** | https://faculty-dashboard-eight.vercel.app/database |
| **Product** | Argyle Faculty Dashboard |
| **Outcome** | complete |
| **Duration** | 313s |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Red** |
| **Top blocker** | HTTP 404 on navigation |
| **Top delight** | Interactive forms discovered |
| **Issues** | 19 |
| **Delights** | 3 |

| **Pages crawled** | 1 |
| **Auto journeys added** | 1 |

---

## Persona × journey matrix

| Journey | P1 New | P2 Power | P3 Developer | P4 Internal | P5 Internal |
|---------|--------|--------|--------|--------|--------|
| **j-argyle-login** Login to Argyle | **Fail** | **Fail** | **Fail** | **Fail** | **Fail** |
| **j-argyle-explore-dashboard** Explore Dashboard | **Fail** | **Fail** | **Fail** | **Fail** | **Fail** |
| **j-argyle-view-users** View Users List | **Fail** | **Fail** | **Fail** | **Fail** | **Fail** |
| **j-argyle-admin-settings** Access Admin Settings | **Fail** | **Fail** | **Fail** | **Fail** | **Fail** |
| **j-argyle-team-collaboration** Test Team Collaboration | **Fail** | **Fail** | **Fail** | **Fail** | **Fail** |
| **auto-j1-dashboard** Auto: Dashboard | **Fail** | **Fail** | **Fail** | **Fail** | **Fail** |

---

## Site map (crawl)

# Site map

**Origin:** https://faculty-dashboard-eight.vercel.app/database  
**Pages crawled:** 1  

## Hub pages (most outbound links)

- `/database/database` — Argyle Analytics Dashboard

## Auth-gated (redirect to login)

- `/database/database`

## All pages

| Path | Title | Depth | Links | Forms | Words |
|------|-------|-------|-------|-------|-------|
| `/database/database` | Argyle Analytics Dashboard | 0 | 0 | 1 | 22 |

---

## Detected workflows

| Type | Path | Title | Signals |
|------|------|-------|---------|
| dashboard | `/database/database` | Argyle Analytics Dashboard | 1 forms, 3 inputs, auth-gated |

---

## Multi-agent collaboration

| Agent | Role | Summary |
|-------|------|---------|
| `crawler` | Site structure discovery | Crawled 1 pages; 1 auth-gated; 0 orphans |
| `workflow` | Workflow & journey planning | Detected workflow types: dashboard |
| `journey-runner` | E2E journey execution | Executed 51 steps across 6 journeys (30 failures, 0 flaky steps, seeds=1, viewpo |
| `performance-v1` | Web Vitals (lab) | Web Vitals captured for 1 journey(s); no threshold breaches |
| `persona-p1-new-signup` | Evaluator: New signup (first-time user) | Analysis from first-time user perspective |
| `persona-p2-power-user` | Evaluator: Power user (experienced user) | Analysis from experienced user perspective |
| `persona-p3-dogfood` | Evaluator: Developer dogfooder (internal engineer) | Analysis from internal engineer perspective |
| `persona-p4-internal-champion` | Evaluator: Internal champion (team lead / champion) | Analysis from team lead / champion perspective |
| `persona-p4-champion` | Evaluator: Internal champion (team lead / champion) | Analysis from team lead / champion perspective |
| `llm-p1-new-signup` | LLM evaluator: New signup | New signup users cannot onboard because the login page only supports existing us |
| `llm-p2-power-user` | LLM evaluator: Power user | All journeys are blocked by a failed login flow, preventing any core task comple |
| `llm-p3-dogfood` | LLM evaluator: Developer dogfooder | The dogfooding session reveals a broken login flow that prevents access to all d |
| `llm-p4-internal-champion` | LLM evaluator: Internal champion | All journeys fail because the login form click action consistently fails, preven |
| `llm-p4-champion` | LLM evaluator: Internal champion | All authenticated journeys are blocked by login redirection; no dashboard functi |
| `synthesizer` | Cross-agent synthesis | Synthesized 19 issues, 3 delights from 14 agent reports |

---

## Dimension rollup (automated subset)

| Dimension | Score 1–5 | Signal |
|-----------|-----------|--------|
| Functionality | 2 | 41% steps pass; 30 failures |
| UI/UX | 2 | 48 unlabeled buttons; 24/72 inputs unlabeled; ~3920ms avg step |
| Information clarity | 2 | 27 content-sparse pages; 0 headings; 0 links |

---

## Issues (evidence-bound)

### P1

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I1** | HTTP 404 on navigation — Requested https://faculty-dashboard-eight.vercel.app/database/database/database returned status 404. | p4-internal-champion | `auto-j1-dashboard-p1-new-signup-s1-desktop-seed1-loop1` |
| **I7** | Crawl found error pages — Paths: /database/database | p4-internal-champion | `crawl-graph` |
| **I9** | No signup/registration option on login page — The login page only displays 'Welcome Back' and offers login for existing users. New signup users have no way to register or create an account, which blocks onboarding entirely. | p1-new-signup | `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` |
| **I10** | All click actions fail after login page — Every click attempt (both on login and subsequent journeys) results in a failure with no error message or transition, suggesting broken interaction logic or missing elements. | p1-new-signup | `j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1` |
| **I13** | Login submission fails across all devices — The click action on the login page (step s3) consistently fails after entering credentials, preventing any access to the dashboard. This blocks all core tasks for power users. | p2-power-user | `j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1` |
| **I15** | Login form submission fails silently — Click actions on the login page (step j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1 and equivalent) fail without any error message or feedback, preventing users from logging in and accessing any dashboard features. | p3-dogfood | `j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1` |
| **I17** | Login form submission fails on all devices — After navigating to the login page and entering credentials, the click action on the login button fails (step outcome 'fail') across desktop, tablet, and mobile viewports. This prevents authentication and blocks all subsequent journeys. | p4-internal-champion | `j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1` |
| **I18** | Dashboard inaccessible behind authentication wall — Every attempt to navigate to /database results in an immediate redirect to /login, and subsequent click actions on the login page fail (no credentials submitted). No dashboard content is reachable, making the entire product non-functional for an unauthenticated test user. | p4-champion | `j-argyle-explore-dashboard-p1-new-signup-s1-desktop-seed1-loop1` |
| **I19** | Login flow appears broken; no successful authentication possible — Login page renders with email/password fields and a Login button, but all click actions (step s3) time out or fail, and no successful login occurs. This prevents any further testing of dashboard features. | p4-champion | `j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1` |

### P2

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I2** | Icon-only or unlabeled buttons — 2 button(s) lack accessible name on page. | p1-new-signup, p4-internal-champion | `auto-j1-dashboard-p1-new-signup-s1-desktop-seed1-loop1` |
| **I3** | Form inputs missing labels — 1 of 3 inputs lack label, aria-label, or placeholder. | p1-new-signup, p4-internal-champion | `auto-j1-dashboard-p1-new-signup-s1-desktop-seed1-loop1` |
| **I4** | Console errors on page — 1 console error(s): Failed to load resource: the server responded with a status of 404 () | p1-new-signup | `auto-j1-dashboard-p1-new-signup-s1-desktop-seed1-loop1` |
| **I5** | Sparse page content — Page body has very little text — value proposition may be unclear. | p1-new-signup | `j-argyle-admin-settings-p1-new-signup-s1-desktop-seed1-loop1` |
| **I8** | Auth-gated routes without login surface in crawl — Some paths redirect to login but no /login-style route was classified — wayfinding gap. | p1-new-signup | `workflow-graph` |
| **I12** | Unlabeled buttons on login page (hypothesis) — The login page has 2 unlabeled buttons, which lack descriptive text or accessible labels, creating confusion for first-time users about their purpose. | p1-new-signup | `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` |

### P3

| ID | Finding | Personas | Evidence |
|----|---------|----------|----------|
| **I6** | Slow step completion — Step took 40728ms (>8s perceived delay threshold). | p1-new-signup | `j-argyle-explore-dashboard-p1-new-signup-s3-desktop-seed1-loop1` |
| **I11** | Initial navigation to '/' or '/database' fails with redirect — Navigating to the root or dashboard URL results in a failed step before redirecting to /login, which may confuse users expecting direct access. | p1-new-signup | `j-argyle-login-p1-new-signup-s1-desktop-seed1-loop1` |
| **I14** | Login form buttons are unlabeled — The login page contains 2 unlabeled buttons, which may hinder keyboard navigation and reduce efficiency for experienced users. | p2-power-user | `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` |
| **I16** | Login page has 2 unlabeled buttons — The login page reports 2 unlabeled buttons, which hinders accessibility and makes it harder for developers to identify interactive elements during testing. | p3-dogfood | `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` |

---

## Delights & strengths (required)

| ID | Delight | Personas | Evidence |
|----|---------|----------|----------|
| **D1** | Interactive forms discovered — 1 pages with forms — workflow automation candidate. | p1-new-signup | `crawl-graph` |
| **D2** | Fast interactions for repeat tasks — 17 steps completed under 3s. | p2-power-user | `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` |
| **D3** | Security message clearly displayed — The login page explicitly states 'Only authorized users can access this dashboard.', which sets proper security expectations. | p3-dogfood | `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` |

---

## Run log

| Step | Journey | Action | Outcome | URL |
|------|---------|--------|---------|-----|
| `j-argyle-login-p1-new-signup-s1-desktop-seed1-loop1` | j-argyle-login | navigate | fail | / |
| `j-argyle-login-p1-new-signup-s2-desktop-seed1-loop1` | j-argyle-login | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-login-p1-new-signup-s3-desktop-seed1-loop1` | j-argyle-login | click | fail | — |
| `j-argyle-login-p1-new-signup-s4-desktop-seed1-loop1` | j-argyle-login | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-login-p1-new-signup-s1-tablet-seed1-loop1` | j-argyle-login | navigate | fail | / |
| `j-argyle-login-p1-new-signup-s2-tablet-seed1-loop1` | j-argyle-login | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-login-p1-new-signup-s3-tablet-seed1-loop1` | j-argyle-login | click | fail | — |
| `j-argyle-login-p1-new-signup-s4-tablet-seed1-loop1` | j-argyle-login | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-login-p1-new-signup-s1-mobile-seed1-loop1` | j-argyle-login | navigate | fail | / |
| `j-argyle-login-p1-new-signup-s2-mobile-seed1-loop1` | j-argyle-login | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-login-p1-new-signup-s3-mobile-seed1-loop1` | j-argyle-login | click | fail | — |
| `j-argyle-login-p1-new-signup-s4-mobile-seed1-loop1` | j-argyle-login | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-explore-dashboard-p1-new-signup-s1-desktop-seed1-loop1` | j-argyle-explore-dashboard | navigate | fail | /database |
| `j-argyle-explore-dashboard-p1-new-signup-s2-desktop-seed1-loop1` | j-argyle-explore-dashboard | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-explore-dashboard-p1-new-signup-s3-desktop-seed1-loop1` | j-argyle-explore-dashboard | scroll | fail | — |
| `j-argyle-explore-dashboard-p1-new-signup-s1-tablet-seed1-loop1` | j-argyle-explore-dashboard | navigate | fail | /database |
| `j-argyle-explore-dashboard-p1-new-signup-s2-tablet-seed1-loop1` | j-argyle-explore-dashboard | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-explore-dashboard-p1-new-signup-s3-tablet-seed1-loop1` | j-argyle-explore-dashboard | scroll | fail | — |
| `j-argyle-explore-dashboard-p1-new-signup-s1-mobile-seed1-loop1` | j-argyle-explore-dashboard | navigate | fail | /database |
| `j-argyle-explore-dashboard-p1-new-signup-s2-mobile-seed1-loop1` | j-argyle-explore-dashboard | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-explore-dashboard-p1-new-signup-s3-mobile-seed1-loop1` | j-argyle-explore-dashboard | scroll | fail | — |
| `j-argyle-view-users-p1-new-signup-s1-desktop-seed1-loop1` | j-argyle-view-users | navigate | fail | /database |
| `j-argyle-view-users-p1-new-signup-s2-desktop-seed1-loop1` | j-argyle-view-users | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-view-users-p1-new-signup-s3-desktop-seed1-loop1` | j-argyle-view-users | click | fail | — |
| `j-argyle-view-users-p1-new-signup-s1-tablet-seed1-loop1` | j-argyle-view-users | navigate | fail | /database |
| `j-argyle-view-users-p1-new-signup-s2-tablet-seed1-loop1` | j-argyle-view-users | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-view-users-p1-new-signup-s3-tablet-seed1-loop1` | j-argyle-view-users | click | fail | — |
| `j-argyle-view-users-p1-new-signup-s1-mobile-seed1-loop1` | j-argyle-view-users | navigate | fail | /database |
| `j-argyle-view-users-p1-new-signup-s2-mobile-seed1-loop1` | j-argyle-view-users | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-view-users-p1-new-signup-s3-mobile-seed1-loop1` | j-argyle-view-users | click | fail | — |
| `j-argyle-admin-settings-p1-new-signup-s1-desktop-seed1-loop1` | j-argyle-admin-settings | navigate | fail | /database |
| `j-argyle-admin-settings-p1-new-signup-s2-desktop-seed1-loop1` | j-argyle-admin-settings | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-admin-settings-p1-new-signup-s3-desktop-seed1-loop1` | j-argyle-admin-settings | click | fail | — |
| `j-argyle-admin-settings-p1-new-signup-s1-tablet-seed1-loop1` | j-argyle-admin-settings | navigate | fail | /database |
| `j-argyle-admin-settings-p1-new-signup-s2-tablet-seed1-loop1` | j-argyle-admin-settings | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-admin-settings-p1-new-signup-s3-tablet-seed1-loop1` | j-argyle-admin-settings | click | fail | — |
| `j-argyle-admin-settings-p1-new-signup-s1-mobile-seed1-loop1` | j-argyle-admin-settings | navigate | fail | /database |
| `j-argyle-admin-settings-p1-new-signup-s2-mobile-seed1-loop1` | j-argyle-admin-settings | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-admin-settings-p1-new-signup-s3-mobile-seed1-loop1` | j-argyle-admin-settings | click | fail | — |
| `j-argyle-team-collaboration-p1-new-signup-s1-desktop-seed1-loop1` | j-argyle-team-collaboration | navigate | fail | /database |
| `j-argyle-team-collaboration-p1-new-signup-s2-desktop-seed1-loop1` | j-argyle-team-collaboration | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-team-collaboration-p1-new-signup-s3-desktop-seed1-loop1` | j-argyle-team-collaboration | explore | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-team-collaboration-p1-new-signup-s1-tablet-seed1-loop1` | j-argyle-team-collaboration | navigate | fail | /database |
| `j-argyle-team-collaboration-p1-new-signup-s2-tablet-seed1-loop1` | j-argyle-team-collaboration | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-team-collaboration-p1-new-signup-s3-tablet-seed1-loop1` | j-argyle-team-collaboration | explore | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-team-collaboration-p1-new-signup-s1-mobile-seed1-loop1` | j-argyle-team-collaboration | navigate | fail | /database |
| `j-argyle-team-collaboration-p1-new-signup-s2-mobile-seed1-loop1` | j-argyle-team-collaboration | wait | pass | https://faculty-dashboard-eight.vercel.app/login |
| `j-argyle-team-collaboration-p1-new-signup-s3-mobile-seed1-loop1` | j-argyle-team-collaboration | explore | pass | https://faculty-dashboard-eight.vercel.app/login |
| `auto-j1-dashboard-p1-new-signup-s1-desktop-seed1-loop1` | auto-j1-dashboard | navigate | fail | https://faculty-dashboard-eight.vercel.app/login |
| `auto-j1-dashboard-p1-new-signup-s1-tablet-seed1-loop1` | auto-j1-dashboard | navigate | fail | https://faculty-dashboard-eight.vercel.app/login |
| `auto-j1-dashboard-p1-new-signup-s1-mobile-seed1-loop1` | auto-j1-dashboard | navigate | fail | https://faculty-dashboard-eight.vercel.app/login |

---

*Generated by Launch Rehearsal CLI — product-agnostic heuristics. Findings require human review before production decisions.*
