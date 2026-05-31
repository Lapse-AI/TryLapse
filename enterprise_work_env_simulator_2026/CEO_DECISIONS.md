# CEO Executive Decisions

**Authority:** plan-ceo-review (pro CEO call)  
**Date:** May 28, 2026  
**Status:** LOCKED — overrides conflicting roadmap text unless amended via Section 13 log

---

## 1. Mode & posture

| Decision | Choice |
|----------|--------|
| **Strategic scope** | **HOLD** — Vision, two-product architecture, founder-first ICP, full `EVALUATION_FRAMEWORK.md` as **north star** (unchanged). |
| **Phase 1 engineering** | **REDUCTION** — Ship the smallest automated slice that earns trust; defer everything else to Phase 2+. |
| **Implementation approach** | **B — Vertical slice** (confirmed). |
| **Expansions adopted** | Evidence binding, run budgets, flake score, confidence labels, SSRF preflight, run observability. |

**CEO principle:** Sell **trust**, not **coverage**. A scorecard founders distrust kills the company faster than a narrow scorecard they believe.

---

## 2. North star (May 2026 – Mar 2027)

**One metric:** *“Would you run this before every launch?”* — measured by **5 founder design partners**, not signup count.

| Phase | North star |
|-------|------------|
| 0 (Jun 7) | ≥1 non-obvious issue + ≥1 evidence-backed delight on a real URL |
| 1 (Jul 5) | Same URL, 3 runs, &lt;30 min, repeatable CLI scorecard |
| 2 (Sep 30) | ≥3/5 design partners say “would pay ~$49/mo” |
| 3 (Mar 2027) | $5k MRR **or** kill / pivot |

---

## 3. Hard gates (non-negotiable)

1. **No Phase 1 code until Phase 0 passes** (Jun 7, 2026).  
2. **No Product B** work (docs, code, pricing) before **Mar 31, 2027** PMF gate.  
3. **No public pricing page** until **3** design partners verbally commit to paying.  
4. **No delight or gap in scorecard** without `run_id` + `step_id` + artifact link.  
5. **Kill / pause** if Phase 0 fails to surface novel insight on first dogfood URL.

---

## 4. Phase 1 scope — CEO mandate (Jul 5, 2026)

### IN (must ship)

| # | Deliverable |
|---|-------------|
| 1 | CLI: `rehearse run --config <file>` |
| 2 | Journey DSL: URL + 3 personas + 5 E2E journeys |
| 3 | Browser runner with per-step logs + screenshots |
| 4 | Persona agents (goal-driven; not dumb scripts only) |
| 5 | Scorecard: persona×journey matrix, P0–P3 issues, **required** delights section |
| 6 | **Evidence binding** enforced at report generation |
| 7 | **3 auto dimensions:** Functionality, UI/UX, Information clarity |
| 8 | Manual template slots for other dimensions (optional fill) |
| 9 | Light repeat loop (3× same micro-journey in one run) for basic “friction” signal |
| 10 | 3 parallel seeds + **FLAKY** flag when disagree |
| 11 | Run budgets (steps, time, tokens) + named errors |
| 12 | URL preflight + **SSRF guardrails** |
| 13 | Structured logs: `run_id`, duration, cost estimate, outcome |

### OUT (explicitly not Phase 1)

- Signup / billing / PLG dashboard  
- GitHub Action CI integration  
- Heavy-use / return-after-gap / 100× veteran modes  
- Slack/Jira/CRM twins  
- Full 8-dimension automation  
- Product B  
- Journey marketplace  
- Open-source release (decide Aug 1; default **closed** until then)

---

## 5. Naming (interim)

| Layer | CEO pick |
|-------|----------|
| **Product A (ship this name)** | **Launch Rehearsal** |
| **Product B (reserved)** | **Deal Rehearsal** |
| **Platform (rename by Jul 5)** | Keep *Synthetic Company Rehearsal* as working umbrella |

---

## 6. Build order (engineering)

```
1. URL preflight + SSRF guard
2. Browser runner + step artifacts
3. Evidence store (run_id, steps, screenshots)
4. Scorecard generator (evidence-bound only)
5. Persona layer on top of journeys
6. Parallel seeds + flake detection
7. CLI polish
```

Do **not** start with personas or LLM breadth — start with **provable artifacts**.

---

## 7. Open questions — CEO resolutions

| Question | CEO decision |
|----------|--------------|
| Open-source vs closed? | **Closed** until Aug 1, 2026; revisit after 10 active workspaces |
| VEI fork vs mocks? | **Defer** to Dec 2026; Phase 1 is browser-on-target-product only |
| First dogfood URL? | **Required by Jun 7** — use your own product or one you ship |
| Product B vertical? | **Do not decide** until Mar 2027 gate |

---

## 8. What we are NOT doing (CEO NO list)

- Competing with Veris on “agent gym” messaging  
- Promising SOC2 or “5-year simulation” in marketing  
- Building MiroFish dependency  
- Optimizing for SE revenue before founder PMF  
- Shipping a bugs-only report (delights section is mandatory)
- **Fixing or deploying the target product under test** — Launch Rehearsal **observes, scores, and reports** only

---

## 9. Next 7 days (CEO calendar)

| Date | Action |
|------|--------|
| **May 29–30** | Pick dogfood URL; write `journeys/phase-0.md` |
| **May 31–Jun 6** | Run Phase 0 manual rehearsal; save scorecard |
| **Jun 7** | Go/no-go on Phase 1 code |
| **Jun 8** | If go: scaffold CLI + runner (no personas yet) |

---

## 10. Verdict

**GO** on the company direction. **GO** on Phase 1 with **reduced** scope above. **STOP** all work that does not serve Launch Rehearsal trust loop before Jul 5.

*Signed: CEO review session 2026-05-28*
