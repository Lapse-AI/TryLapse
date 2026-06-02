# Design partner outreach — §0 Track A

**Authority:** `CEO_DECISIONS.md` · `DESIGN_PARTNER_CHECKLIST.md` · Target: **3 would-pay** by Sep 30, 2026

**Last updated:** 2026-06-02

---

## This week (§0)

| # | Action | Owner | Done |
|---|--------|-------|------|
| 1 | List **10 warm targets** (B2B SaaS, weekly ship, staging URL) | | ☐ |
| 2 | Send **5 intros** using templates below | | ☐ |
| 3 | Book **2 calls** (30 min rehearsal readout) | | ☐ |
| 4 | Dry-run demo on **enterprise-20260530-234231** or Argyle run | | ☐ |
| 5 | Record verbatim: *“Would you run this before every launch?”* | | ☐ |

---

## Demo stack (before any call)

```bash
./rehearse serve -o launch-rehearsal/artifacts --port 8765
cd Frontend_V1 && npm run dev   # :8081
```

Show: Init → **Personas (AI draft)** → Generate YAML → Runner → Run detail matrix + delights.

---

## Intro email (template A — founder peer)

**Subject:** Quick staging rehearsal before your next ship?

Hi {Name},

We're building **Launch Rehearsal** — synthetic personas run your staging URLs and return an evidence-bound scorecard (issues + required delights), no code changes on your side.

Would you be open to a **30-minute walkthrough** on {their product}? We'd run one config on staging beforehand and review persona × journey results together.

North star we're testing: *“Would you run this before every launch?”*

{Your name}

---

## Intro email (template B — post-launch regression)

**Subject:** Catching persona-blind regressions before prod

Hi {Name},

Noticed {company} ships often — we built a tool that rehearses **evaluator / operator / admin** paths on staging with step screenshots and a compare view between releases.

Happy to run a **free rehearsal** on your staging URL and send the markdown scorecard async if easier than a call.

Interested?

---

## Call agenda (30 min)

| Min | Topic |
|-----|--------|
| 0–5 | Their launch pain; what they do today (UAT, manual QA) |
| 5–15 | Live: command center → run detail → one evidence drill-down |
| 15–22 | Init personas + journey draft; honest Phase 2 scope |
| 22–28 | North star question + would-pay (~$49/mo hypothesis) |
| 28–30 | Next step: second run after they edit YAML |

---

## Tracking table

| Company | Contact | Sent | Call | Run ID | Would launch? | Would pay? |
|---------|---------|------|------|--------|---------------|------------|
| | | | | | | |

---

## Related

`DESIGN_PARTNER_CHECKLIST.md` · `FEATURE_SCOPE.md` §0 · `INIT_WIZARD.md`
