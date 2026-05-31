# Launch Rehearsal — Argyle Faculty Dashboard

| Field | Value |
|-------|--------|
| **Run ID** | `phase0-argyle-20260529-001` |
| **Date** | May 29, 2026 |
| **Target** | [faculty-dashboard-eight.vercel.app/database](https://faculty-dashboard-eight.vercel.app/database) |
| **Product** | Argyle Analytics Dashboard |
| **Method** | Browser DevTools MCP (logged-out + login UX) |
| **Readiness** | **Red** for launch rehearsal of *database* — **blocked by auth**; **Amber** for login surface |

---

## Executive summary

Your deep link to `/database` **does not expose the database UI** to anonymous visitors. Every tested route (`/`, `/login`, `/database`, and even 404 paths like `/signup`) **ends on `/login`**. That is correct for a private dashboard, but it means Launch Rehearsal **cannot score the page you care about** until we have test credentials.

What we *could* evaluate: login form UX, auth redirect, and invalid-login feedback.

---

## Persona × journey matrix

| Journey | P1 Jordan | P2 Sam | P3 Alex |
|---------|-----------|--------|---------|
| **J1** Deep link `/database` | **Pass** (redirect to login) | — | **Pass** (auth enforced) |
| **J2** Login affordances | **Pass** | **Partial** | **Pass** |
| **J3** Invalid credentials | **Pass** | — | **Pass** |
| **J4** Form a11y | **Partial** | **Partial** | **Partial** |
| **J5** Wayfinding | **Pass** | **Pass** | **Pass** |

---

## Dimension rollup (login surface only)

| Dimension | Score 1–5 | Note |
|-----------|-----------|------|
| Functionality | 3 | Auth gate works; core app unreachable without login |
| Information clarity | 2 | No product description beyond “Welcome Back”; URL says “faculty”, title says “Argyle Analytics” |
| UI/UX | 4 | Clean form; disabled Login until fields filled |
| Adaptability | N/A | Not testable logged-out |
| Integrations | N/A | — |
| Compliance signals | 3 | “Only authorized users” copy; no privacy/terms links |
| Reliability | 4 | 401 from `/api/auth/login` on bad creds; user-visible toast |
| Speed (perceived) | 4 | Fast redirect to login |

---

## Issues (evidence-bound)

### P1 — Blockers for rehearsal of `/database`

| ID | Finding | Evidence |
|----|---------|----------|
| **I0** | **Target journey blocked:** `/database` never renders for unauthenticated users; rehearsal stops at login. | `J1-S1` — nav to `/database` → Page URL: `.../login` |

### P2 — Meaningful UX / product

| ID | Finding | Persona | Evidence |
|----|---------|---------|----------|
| **I1** | **Brand / URL mismatch:** Deploy URL implies *faculty dashboard*; page title is *Argyle Analytics Dashboard* — new users may not trust they landed on the right app. | P1 | `J1-S2` — title vs hostname |
| **I2** | **No “what is this?” on login:** Only “Welcome Back” + credential fields; no hint of database/analytics value (charts, faculty workflows). | P1 | `J1-S3` — visible text: Welcome Back, authorized-users line only |
| **I3** | **Password toggle has no accessible name** — icon-only `button` before Login in ARIA tree. | P2 | `J4-S1` — `button [ref=e3]: - img` with no `name` |
| **I4** | **No forgot-password or support link** on login screen. | P1, P3 | `J2-S2` — snapshot has no link roles besides form controls |
| **I5** | **Remember me checked by default** — shared-machine risk for university lab computers. | P3 | `J2-S3` — `checkbox "Remember me" [checked]` |

### P3 — Polish

| ID | Finding | Evidence |
|----|---------|----------|
| I6 | Invalid login returns **401** in network console; user sees toast (good), but screen reader gets `alert` + status region — verify focus management. | `J3-S1` — toast: “Login Failed Email or password is incorrect” |

---

## Gaps & wishes

| ID | Gap | Confidence |
|----|-----|------------|
| G1 | After login, can user return to `/database` bookmark without extra clicks? | **unknown** — needs credentials |
| G2 | Veteran user (daily login) — is Remember me + no SSO slowing repeat access? | hypothesis |

---

## Delights & strengths

| ID | Delight | Evidence |
|----|---------|----------|
| **D1** | **Login disabled until both fields filled** — prevents empty submit noise. | `J2-S1` — `Login [disabled]` empty; enabled after fill |
| **D2** | **Clear auth failure toast** in notifications region: “Login Failed — Email or password is incorrect”. | `J3-S2` — status in `Notifications (F8)` list |
| **D3** | **Explicit access boundary copy:** “Only authorized users can access this dashboard.” | `J1-S4` — paragraph on login |
| **D4** | **Deep link protection:** `/database` does not leak content when logged out. | `J1-S1` — redirect to `/login` |

---

## CEO gate (this run)

| Criterion | Result |
|-----------|--------|
| ≥1 non-obvious issue | **Yes** (I1–I5; I0 for scope) |
| ≥1 evidence-backed delight | **Yes** (D1–D4) |
| **Methodology** | **PASS** |
| **Product `/database` rehearsal** | **INCOMPLETE** — need test account |

---

## Recommended next steps

1. Share a **test email/password** (or magic link) for read-only access.  
2. Re-run journeys on **post-login** `/database`: tables, filters, export, empty states.  
3. Fix **I3** (aria-label on password toggle) and consider **I1** (align title/URL/branding).  
4. Add `launch-rehearsal/examples/argyle-faculty.yaml` to CLI dry-run preflight (already added).

---

## Run log

| Step | URL | Outcome |
|------|-----|---------|
| J1-S1 | `/database` | → `/login` |
| J2-S1 | `/login` | Login disabled → enabled on fill |
| J3-S1 | `/login` + bad creds | Toast error; API 401 |
| J4-S1 | `/login` | Unlabeled password toggle |
| J5-S1 | `/`, `/signup` (404) | All → `/login` |
