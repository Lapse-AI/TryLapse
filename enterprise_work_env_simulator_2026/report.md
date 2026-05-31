# Deep Research Report: Synthetic Company Product Rehearsal

*Methodology: @deep-research · Updated: 2026-05-28*  
*Companion: `../enterprise-work-env-simulator/`*

## Executive summary

**Primary use case (updated):** Pre-customer **product validation** — founders and builders ship SaaS/tools without enough real users to stress-test journeys, UX, integrations, and compliance story.

**The tool being evaluated:** **Your product** (the startup’s app/site), not a third-party vendor in a procurement cycle.

**Synthetic company:** Context around that product — fake team, roles, Slack/Jira noise, and personas who try to complete real jobs using **your** UI.

**Secondary use case (Product B — long-term):** B2B SaaS Solutions Engineering / FDE (pre-POC rehearsal) — same engine, later GTM. See **`PRODUCT.md`** for two-product roadmap and dated phases.

**MiroFish:** Not required. Use twin mocks + LangGraph personas + browser runners.

**Why test this first:** You and design partners *are* the buyer; no enterprise sales cycle; dogfood on any URL in days.

---

## Who is “the tool”?

| | Primary | Secondary |
|---|---------|-----------|
| **Evaluated** | **Your SaaS / tool / website** | **Your product inside a prospect’s stack** |
| **Buyer** | Founder, PM, solo builder, early eng | SE / Sales Eng leader |
| **Pain** | “No customers yet — is this good?” | “POC will surprise us — rehearse first” |
| **Synthetic world** | Typical 20–100 person company using your category | Prospect-specific stack from discovery |

---

## Product definition

**Synthetic Company Rehearsal** — spin up a believable org, run persona agents through week-one ops and core journeys on **your product**, collect structured feedback (functionality, UX, integrations, compliance *signals*), deliver a **readiness scorecard** with replays — before beta users or enterprise POC.

Answers: *“If I don’t have real customers, how do I know it works or what breaks?”*

---

## Why primary = easier to test (for you and me)

1. **You are the ICP** — no recruiting Fortune 500 SE leaders to validate the concept.
2. **Instant subjects** — any staging URL, side project, or TryLapse-class app.
3. **Fast yes** — builders try free/cheap tools; enterprises need security review.
4. **Clear success** — “found 12 P1 issues before launch” vs “shortened sales cycle 20%.”
5. **We can demo in one session** — browser journeys + issue list + replay (no full VEI fork required for v0).

**Tradeoff:** Lower ACV than SE ($29–299/mo PLG vs $10k engagements) until you prove ROI and move upmarket.

---

## MVP (4 weeks, builder-first)

| Week | Deliverable |
|------|-------------|
| 1 | 3 personas × 5 journeys on **one** target URL → markdown scorecard |
| 2 | Parallel runs (3×) + severity rubric (P0–P3) |
| 3 | Optional: lightweight “company context” (roles, blockers in Slack mock JSON) |
| 4 | 5 founder interviews: “Would you run this before launch?” |

**v0 stack:** Playwright/browser MCP + LLM personas + journey scripts. **v1:** VEI-style integrations if builders need “works with Jira” stories.

**Out of scope v0:** Full SOC2 audit, 5-year compression, MiroFish.

---

## Positioning

> For **teams shipping B2B software before they have enough real users**, **[Product]** runs **synthetic customers** through your app in a **fake but realistic company** — and returns a **readiness scorecard** (UX, flows, breaks, compliance signals) **without** waiting for beta users.

**Category name ideas:** Product Rehearsal · Synthetic Beta · Pre-Customer QA

---

## Competitive set (shifted for primary ICP)

| Alternative | Gap you fill |
|-------------|--------------|
| Manual dogfooding | No scale, blind spots |
| UserTesting / Maze | Real humans, slow, not your full stack context |
| Playwright tests | Scripted only, no persona judgment |
| Veris / VEI | Agent *training* gym, not *your product* UX validation story |
| Friends & Twitter beta | Biased, incomplete journeys |

---

## Week 1 test (you + me)

1. Pick **one URL** (your product, or a public SaaS you want to critique).
2. Define **5 journeys** (signup, core action, settings, invite teammate, edge case).
3. Define **3 personas** (power user, confused IC, admin).
4. Run automated passes → **issue backlog** with screenshots.
5. Compare to **your gut** — did it find non-obvious breaks?

If that session feels valuable, you have signal to build the product.

---

## Artifacts

- **`PRODUCT.md`** — **product doc, goals, phased roadmap with dates (benchmark May 28, 2026)**
- `POSITIONING.md` — one-pager positioning
- `results/Recommended_wedge_and_MVP_scope.json` — wedge JSON (updated)
- `../enterprise-work-env-simulator/` — competitor research (still valid; Veris/VEI are adjacent)

---

## Skills to use next

| Skill | When |
|-------|------|
| `@office-hours` | Name one founder you’d sell to in one sentence |
| `@startup-validator` | Re-run if you pursue fundraising |
| `@startup-competitors` | Add Maze, UserTesting, QA bots when fundraising |
