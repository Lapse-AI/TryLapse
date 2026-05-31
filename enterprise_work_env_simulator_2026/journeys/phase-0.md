# Phase 0 — Launch Rehearsal (manual run)

**Run ID:** `phase0-20260528-001`  
**Date:** May 28, 2026  
**Target:** https://cal.com (practice B2B SaaS — no owned product URL in repo yet)  
**CEO gate:** Pass if ≥1 non-obvious issue + ≥1 evidence-backed delight  

> **Re-run required:** Replace target with your staging URL when available (founder dogfood).

---

## Product under test

| Field | Value |
|-------|--------|
| Name | Cal.com |
| Category | Scheduling / meeting infrastructure (B2B SaaS) |
| Why this target | Clear E2E journeys without login; representative founder ICP product surface |

---

## Personas (3)

### P1 — Jordan (first-time founder)

- **Goal:** Understand if Cal.com fits “let customers book calls” in 10 minutes  
- **Patience:** Low — will bounce if value unclear  
- **Stress:** Information clarity, time-to-first-value  

### P2 — Sam (daily operator)

- **Goal:** Configure event types, availability, and sharing links efficiently  
- **Patience:** Medium — tolerates depth if patterns are consistent  
- **Stress:** Speed, UI density, repeat-task friction  

### P3 — Alex (team admin)

- **Goal:** Evaluate team features, permissions, upgrade path  
- **Patience:** Low for sales fluff — wants specifics  
- **Stress:** Pricing transparency, enterprise signals, settings discoverability  

---

## Journeys (5)

| ID | Journey | Primary persona | Success criteria |
|----|---------|-----------------|------------------|
| J1 | **Land → grasp value** | P1 | Value prop clear in one scroll; obvious CTA |
| J2 | **Start signup path** | P1 | Sign up / Get started reachable without hunt |
| J3 | **Explore product depth** | P2 | Features or docs explain workflows |
| J4 | **Pricing & plans** | P3 | Plans comparable; no surprise hidden limits |
| J5 | **Return / second look** | P2 | Main nav stable; can re-find pricing & signup |

---

## Steps (E2E outline)

### J1 — Land → grasp value (P1)

1. Open homepage  
2. Read hero + subhead  
3. Identify primary CTA  
4. Note: open-source / self-host signals?  

### J2 — Start signup (P1)

1. From home, click Get started / Sign up  
2. Observe auth options (email, Google, etc.)  
3. Note friction before account creation  

### J3 — Explore depth (P2)

1. Navigate to Features or equivalent  
2. Scan for integrations, routing, teams  
3. Judge information hierarchy  

### J4 — Pricing (P3)

1. Open Pricing  
2. Compare tiers  
3. Note missing dimensions (seats, features, limits)  

### J5 — Return navigation (P2)

1. Home → Pricing → Home  
2. Re-locate signup CTA  
3. Note wayfinding consistency  

---

## Evidence requirements

Each finding must cite:

- `run_id`: phase0-20260528-001  
- `step_id`: J{n}-S{m}  
- URL path + observation (screenshot path when saved)

---

## Out of scope (Phase 0)

- Logged-in flows (no test account)  
- Payment completion  
- Mobile viewport (desktop only this run)  
- Compliance audit  
