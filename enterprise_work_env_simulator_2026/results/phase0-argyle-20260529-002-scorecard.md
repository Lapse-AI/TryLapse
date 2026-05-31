# Launch Rehearsal — Argyle Faculty Dashboard (authenticated)

| Field | Value |
|-------|--------|
| **Run ID** | `phase0-argyle-20260529-002` |
| **Date** | May 29, 2026 |
| **Target** | https://faculty-dashboard-eight.vercel.app/database |
| **Product** | Argyle Analytics Dashboard — Candidate Database |
| **Scope** | Login + `/database` + profile + filters + pagination + Analytics + Admin |
| **Prior run** | `phase0-argyle-20260529-001` (logged-out only) |

---

## Executive summary

| | |
|---|---|
| **Readiness** | **Amber** — strong data product; filter UX and profile polish gaps |
| **Top blocker** | City filter does not apply when typing “Mumbai” (1809 results unchanged) |
| **Top delight** | AI semantic search + keyword filter + rich profile pages on 1,809 candidates |
| **Login** | Success → lands on `/database` with welcome toast |

> **Security note:** Test credentials were shared in chat. Rotate `password123` if this deployment is still live.

---

## Persona × journey matrix (authenticated)

| Journey | P1 Jordan | P2 Sam | P3 Alex |
|---------|-----------|--------|---------|
| **J1** Login → database | **Pass** | **Pass** | **Pass** |
| **J2** Browse & filter table | **Partial** | **Partial** | **Partial** |
| **J3** View candidate profile | **Pass** | **Pass** | **Pass** |
| **J4** Analytics overview | **Pass** | **Pass** | **Pass** |
| **J5** Admin / return nav | **Partial** | **Pass** | **Partial** |

---

## Dimension rollup

| Dimension | Score 1–5 | Top signal |
|-----------|-----------|------------|
| Functionality | 3 | Keyword filter works; city filter broken on type-only |
| Information clarity | 4 | Counts (“1809 profiles”), example semantic queries |
| UI/UX | 4 | Sidebar nav, pagination, skill chips |
| Adaptability | 3 | 7 filter fields + semantic search = heavy for repeat use |
| Integrations | 4 | Admin shows Google Drive + Supabase connected |
| Compliance signals | 2 | Full addresses in table; Admin open to this user |
| Reliability | 4 | Profile deep links work; row “View Profile” click unreliable |
| Speed (perceived) | 4 | Fast load; pagination responsive |

---

## Issues (evidence-bound)

### P1 — Blockers / high impact

| ID | Finding | Persona | Evidence |
|----|---------|---------|----------|
| **I6** | **City filter does not filter:** Typing “Mumbai” shows autocomplete suggestions but **Displaying 1809 matching profiles** unchanged; non-Mumbai rows still visible. | P2 | `J2-S1` — after fill “Search Cities… Mumbai” |
| **I7** | **“View Profile” row link click no-op:** Clicking table link did not navigate; direct URL `/database/profile/{uuid}` works. | P1 | `J3-S1` — click e30 → URL stayed `/database`; `J3-S2` — direct nav OK |

### P2 — Meaningful

| ID | Finding | Persona | Evidence |
|----|---------|---------|----------|
| **I8** | **Profile data quality:** Work Experience entries show company names with **empty role headings** and “-” placeholders. | P2 | `J3-S3` — profile Alefiya: headings `[level=4]` empty before “Plaksa Learning”, “IBM”, etc. |
| **I9** | **Invalid Date** on profile File Information. | P3 | `J3-S4` — “Modified: Invalid Date” |
| **I10** | **Filter panel overload:** 7 text filters + semantic search + weights + spinbutton — high cognitive load for “find Mumbai HR candidate”. | P2 | `J2-S2` — refs e10–e19 on database page |
| **I11** | **Admin accessible** to standard login — “Process Updates”, system status, file mapping. May be intended; verify RBAC. | P3 | `J5-S1` — `/admin` loads Admin Dashboard for test user |
| **I12** | **PII density in table:** Full street addresses visible in list view (e.g. Ludhiana full address). | P3 | `J2-S3` — Gursharan Singh row |

### P3 — Polish (from logged-out run, still valid)

| ID | Finding | Evidence |
|----|---------|----------|
| I1–I5 | Login branding, password toggle a11y, remember-me default | `phase0-argyle-20260529-001` |

---

## Gaps & wishes

| ID | Gap | Confidence |
|----|-----|------------|
| G3 | City filter likely requires **picking autocomplete option**, not free-text — no affordance explains this. | **high** — suggestions appear but table unchanged |
| G4 | Duplicate profiles for same name (“Alefiya Rangwala” × 4 on keyword search) — dedup UX unclear. | **high** — keyword “Alefiya” → 4 rows |
| G5 | Veteran user filtering daily would want saved filter presets. | hypothesis |

---

## Delights & strengths

| ID | Delight | Persona | Evidence |
|----|---------|---------|----------|
| **D5** | **Post-login lands on Candidate Database** with 1,809 profiles and clear counts. | P1 | `J1-S1` — URL `/database`, “Currently 1809 profiles” |
| **D6** | **AI-Powered Semantic Search** with helpful example queries in UI copy. | P1, P2 | `J2-S4` — heading + example “Python developers with 5+ years…” |
| **D7** | **Keyword filter is fast and precise** — “Alefiya” → 4 matching profiles, Page 1 of 1. | P2 | `J2-S5` — Displaying 4 matching |
| **D8** | **Rich profile page:** skills, certifications, specializations, “View Original Document”, Back to Database. | P1 | `J3-S5` — profile sections + Back link |
| **D9** | **Analytics dashboard:** Total Profiles, Avg Experience, Top Skill (Time Management), Top State (Maharashtra), charts. | P3 | `J4-S1` — `/analytics` snapshot |
| **D10** | **Pagination at scale:** Page 2 of 181 works. | P2 | `J2-S6` — Next → “Page 2 of 181” |

---

## CEO gate

| Criterion | Result |
|-----------|--------|
| ≥1 non-obvious issue | **Yes** (I6 city filter, I7 profile click, I8 data quality) |
| ≥1 evidence-backed delight | **Yes** (D5–D10) |
| **Dogfood rehearsal** | **COMPLETE** (authenticated core path) |

---

## Run log

| Step | URL / action | Outcome |
|------|----------------|---------|
| J1-S1 | Login | → `/database`, welcome toast |
| J2-S1 | City = Mumbai | 1809 unchanged (bug) |
| J2-S5 | Keyword = Alefiya | 4 matches |
| J2-S6 | Next page | Page 2 of 181 |
| J3-S1 | Click View Profile | No navigation |
| J3-S2 | Direct profile URL | Full profile rendered |
| J4-S1 | `/analytics` | Metrics + charts |
| J5-S1 | `/admin` | Admin dashboard visible |

---

## Recommended fixes (priority)

1. **Fix city filter** — apply on select or debounced search; update “Displaying N” immediately.  
2. **Fix client-side routing** for “View Profile” links in table.  
3. **Profile parser** — populate job titles; fix “Invalid Date”.  
4. **RBAC** — restrict `/admin` if not all users should process file updates.  
5. **Rotate test password** shared in chat.
