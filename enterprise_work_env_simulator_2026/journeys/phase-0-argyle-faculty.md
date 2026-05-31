# Phase 0 — Argyle Faculty Dashboard (dogfood)

**Run ID:** `phase0-argyle-20260529-001`  
**Date:** May 29, 2026  
**Target:** https://faculty-dashboard-eight.vercel.app/database  
**Product:** Argyle Analytics Dashboard (internal faculty analytics)  
**Scope:** Logged-out + login surface only (no test credentials)

---

## Personas (adapted for internal dashboard)

| ID | Persona | Goal |
|----|---------|------|
| P1 | Jordan — new faculty user | Reach database view; understand what the product does from login |
| P2 | Sam — returning user | Log in quickly; remember-me; password visibility |
| P3 | Alex — admin / IT | Auth boundary, error messages, unauthorized access messaging |

---

## Journeys (5)

| ID | Journey | Steps |
|----|---------|-------|
| J1 | Deep link → protected route | Open `/database` → observe redirect |
| J2 | Login affordances | Empty form → fill fields → Login enabled |
| J3 | Invalid credentials | Submit bad password → error UX |
| J4 | Form accessibility | Labels, placeholders, icon-only controls |
| J5 | Wayfinding | `/` → `/database` → consistent login |

---

## Blocked (needs credentials)

- ~~Post-login `/database` UI~~ — **Done** in `phase0-argyle-20260529-002`
- Logout / session persistence validation (optional)
- Role-based access matrix (who should see Admin?)
