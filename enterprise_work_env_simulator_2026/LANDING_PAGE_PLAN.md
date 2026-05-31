# Launch Rehearsal — Landing Page Plan

**Version:** 1.0  
**Date:** 2026-05-31  
**Status:** Planning only — **do not implement** until design partner phase assets are ready  
**Audience:** Designer, copywriter, engineer executing the first public marketing surface  
**Authority:** `DESIGN_PARTNER_CHECKLIST.md` · `live-2026-05-31.md` · `FEATURE_SCOPE.md` · `CEO_DECISIONS.md`

---

## Executive context

Launch Rehearsal is in **design partner / concierge** mode, not PLG. The landing page’s job is to **qualify and convert warm leads into booked calls** where you run their staging URL async and walk the dashboard — not to promise self-serve signup, billing, or integrations that are deferred.

**North-star question (record on every call):** *“Would you run this before every launch?”*

**Secondary validation:** *“Would you pay ~$49/mo for this on every release?”* — use in partner conversations only; **do not publish a pricing page** until 3 verbal pay commits (`CEO_DECISIONS.md` §3).

---

## 1. Strategic foundation

### 1.1 ICP — primary persona

| Attribute | Detail |
|-----------|--------|
| **Who** | Engineering lead, founder-CTO, or head of QA at a **B2B SaaS** team shipping weekly |
| **Stage** | Pre-launch → early beta; staging URL exists; 5–50 people |
| **Trigger** | “We’re about to ship and I don’t trust our manual dogfood / UAT” |
| **Pain** | Regressions caught late; persona-blind QA; no evidence bundle for stakeholders |
| **Budget signal** | Already pays for staging infra, CI, maybe Datadog — will pay ~$49/mo if trust is high |

**Jobs to be done (primary):**

1. **Pre-launch gate:** Get a Red/Amber/Green readiness signal with blockers ranked before release day  
2. **Persona coverage:** See the same product through evaluator, operator, and admin lenses — not one happy-path script  
3. **Evidence for stakeholders:** Export a scorecard with screenshots + step IDs PM/design can act on without “trust me”  
4. **Release diff:** Answer “what changed since Tuesday?” with resolved vs new issues  
5. **Async handoff:** Leave the call with markdown export / Linear backlog stub, not a slide deck

### 1.2 ICP — secondary personas

| Persona | Role | JTBD on landing | CTA affinity |
|---------|------|-----------------|--------------|
| **Founder / PM** | Business owner | “Will real users succeed on launch day?” | Sample scorecard, delights section |
| **QA / release manager** | Process owner | “Repeatable rehearsal I can run every sprint” | CLI quickstart, flake rate |
| **Design engineer** | Builder | “Actionable UX findings with repro, not Lighthouse scores alone” | Evidence dialog screenshot |

**Explicitly not primary (Phase 3+):** Enterprise SE leaders, compliance-heavy regulated buyers, solutions engineers doing prospect POCs (Product B / Deal Rehearsal).

### 1.3 Positioning statement

**Category we own:** **Pre-launch readiness monitoring** — observe, score, and report on persona × journey rehearsals with evidence-bound scorecards.

**Positioning statement (internal):**

> For engineering and product leaders shipping B2B SaaS weekly, **Launch Rehearsal** is a **pre-launch readiness monitor** that runs your staging app through three persona lenses and five end-to-end journeys, producing an evidence-bound scorecard in under 30 minutes — unlike generic E2E scripts that only check happy paths, uptime monitors that miss UX regressions, or manual QA that doesn’t scale.

**Tagline (product):** *Synthetic customers for your product — before you have real users.* (`PRODUCT.md` §3)

**Dashboard headline (reuse on landing):** *Pre-launch readiness, observed.*

**Subhead pattern (reuse):** *Evidence-bound, no auto-fix.*

### 1.4 Category differentiation

| vs | They optimize for | Launch Rehearsal difference |
|----|-------------------|----------------------------|
| **Playwright / Cypress** | Deterministic pass/fail on scripts you write | Persona × journey matrix, heuristics + optional LLM grading, **required delights**, readiness band — scripts are input, scorecard is output |
| **Datadog synthetics / Checkly** | Uptime, latency, API checks | Full human journeys, information clarity, UX friction — not just “200 OK” |
| **Manual QA / dogfood** | Human judgment | Repeatable in ~10–30 min, artifact bundle, compare across runs |
| **UserTesting / Maze** | Real humans, research | Pre-customer, anytime on staging, engineering-owned, evidence tied to `run_id` + `step_id` |
| **Veris / agent gyms** | Agent training environments | **Your product URL** is the subject; we sell trust in *your* launch readiness, not a simulation marketplace |

### 1.5 Core promise + proof points (L1/L2 shipped only)

**Core promise:**

> We score your staging app like three personas would — with screenshots, step evidence, and a readiness band — in one run. We observe and report only; we never change your code or deploy.

**Proof points (cite on landing — all L1/L2 shipped):**

| Claim | Evidence source | Example language |
|-------|-----------------|------------------|
| Persona × journey matrix | L1 scorecard + dashboard | 3 personas × 5 journeys; pass / partial / fail per cell |
| Evidence-bound findings | CEO gate + L1 | Every issue links to `run_id`, `step_id`, screenshot |
| Required delights | L1 heuristics | Not bugs-only — “9 marketing-ready delights” on Argyle dogfood (`live-2026-05-31.md`) |
| Crawl + sitemap | L1 crawler | “16 pages crawled”; hub / orphan / auth-gated taxonomy |
| Multi-agent pipeline | L1 agents | Crawler → Workflow → Journey → Persona (×3) → Synthesizer |
| Compare / diff | L1 CLI + L2 UI | “Red → Green”; resolved vs new issues (`/compare`) |
| CLI + dashboard | L1 + Frontend_V1 | `rehearse run`, `rehearse serve`, React command center at `:8081` |
| Init wizard | L2 Sprint 3 | Generate `rehearse.yaml` from URL (`/init`) |
| Export handoff | L2 Sprint 1–3 | Markdown scorecard, Linear backlog download (markdown stub — not OAuth) |
| Human loop | L2 annotations | Agree / Disagree / False positive on findings |
| Flake detection | L1 parallel seeds | FLAKY flag when seeds disagree; flake rate on command center |
| SSRF-safe preflight | L1 | Staging URL validated before run |
| NLU narratives | L1 NLU-1/2 | Run summary + compare “What changed” when LLM key set |
| Time to scorecard | Dogfood metrics | ~2m 08s on live stack (`live-2026-05-31.md`) |

**Real metrics for social proof (Argyle dogfood run `argyle-20260531-000517`):**

- Readiness: **Green**, **0 blockers**, **9 delights**, **16 pages** crawled  
- Compare story: **Red → Green** across consecutive Argyle runs; pages **0 → 16**  
- Command center: **14% flake rate**, **18-run** history trend  

**Real issue/delight language (Phase 0 Cal.com scorecard — methodology proof):**

- Issues: “Top nav IA ambiguity”; “Pricing comparison fatigue”; “Return-user CTA noise”  
- Delights: “Sign up with Google + no credit card without scrolling”; “Interactive booking UI on homepage”; “Free forever tier explicit”  

### 1.6 Explicit “do not claim” list

From `FEATURE_SCOPE.md` §1 and `CEO_DECISIONS.md` §8 — **never on landing, hero, or FAQ “yes” answers:**

| Do NOT claim | Say instead |
|--------------|-------------|
| Self-serve signup / PLG / billing | “Design partner program — we run your staging URL for you” |
| Public pricing / “Start free” tier | “Pricing validated with design partners — book a call” |
| Slack / Jira / email alert delivery | “Export to markdown / Linear backlog download today; native integrations on roadmap” |
| Slack / Jira / GitHub OAuth “Connect” | “Integration catalog — Phase 2” |
| Scheduled cron runs | “Run on demand via CLI or dashboard; scheduled runs Phase 2” |
| SSO / dashboard RBAC | “Local dashboard + API; enterprise auth later” |
| GitHub Action / PR checks product | “CLI JSON output suitable for CI — productized Action Aug 2026 target” |
| Full WCAG / axe audit | “UI/UX heuristics + optional LLM; dedicated a11y agent Phase 2+” |
| Web Vitals / Lighthouse agent (functional) | “Compliance & Performance agents shown as idle — Phase 2” |
| SOC2 certification / pen test | “Compliance *signals* in heuristics — not a security audit” |
| “5-year simulation” / 100× veteran modes | “Repeat micro-loop + parallel seeds for basic friction/flake signals” |
| Auto-fix / auto-deploy | **“Observe and score only — no code changes”** (mandatory) |
| Product B / Deal Rehearsal | Do not mention on Product A landing |
| Journey marketplace | Not on roadmap for landing |
| Open-source | “Closed source until Aug 2026 decision” — omit unless FAQ asked |
| Trends recurrence / calendar (live) | Do not screenshot mock recurrence as live; label “coming soon” if shown |
| Multi-workspace portfolio | Single workspace today |
| Competitor benchmark automation | Manual compare URL — Phase 3 |

### 1.7 North-star CTA hierarchy

| Priority | CTA | Label | Destination |
|----------|-----|-------|-------------|
| **Primary** | Book design partner call | **Get a staging scorecard** | Lead form → Calendly / email |
| **Secondary** | View sample evidence | **See sample scorecard** | Static embed: Argyle or Cal.com Phase 0 PDF/MD |
| **Tertiary** | Developer eval | **Read CLI docs** | GitHub README or `/docs/cli` anchor |
| **Quaternary** | Self-serve curious | **Try init wizard** | Link to demo video or gated sandbox — **not** live `:8081` in production MVP |

**Anti-CTA:** No “Sign up free”, “Buy Pro”, “Connect Slack”, “Start trial”.

---

## 2. Messaging architecture

### 2.1 Headline options (H1)

| # | H1 | Best for |
|---|-----|----------|
| **A (recommended)** | **Pre-launch readiness, observed.** | Matches live dashboard — instant product continuity |
| B | **Run a launch rehearsal on staging — before your users do.** | Outcome-focused, verb-led |
| C | **Three personas. Five journeys. One evidence-bound scorecard.** | Concrete, scannable |
| D | **Stop guessing if you’re ready to ship.** | Pain-led |
| E | **The scorecard your eng lead wants before every release.** | Persona-led (eng lead) |

### 2.2 Subhead options (H2 / hero body)

| Pairs with | Subhead |
|------------|---------|
| A | Launch Rehearsal crawls your staging app, runs end-to-end journeys as evaluator, operator, and admin personas, and delivers a Red/Amber/Green readiness scorecard with screenshots — in under 30 minutes. Evidence-bound. No auto-fix. |
| B | Persona × journey monitoring for B2B SaaS teams who ship weekly. Issues, delights, and repro artifacts — not a bugs-only dump. |
| C | Observe and score only. We never change your code, never deploy, never patch your product. |
| D | Replace “did anyone click around?” with a repeatable rehearsal your PM, QA, and founders can trust. |

### 2.3 Elevator pitches

**30 seconds:**

> Launch Rehearsal is pre-launch readiness monitoring for B2B SaaS. Point it at your staging URL — it crawls your app, runs five end-to-end journeys through three persona lenses, and produces a scorecard with blockers, delights, and screenshot evidence. Think persona-aware QA that finishes in minutes, not a week of manual dogfood. We observe only; we don’t fix your code. Engineering leads use it to answer: would I run this before every launch?

**2 minutes:**

> Most teams launch with happy-path E2E tests and a Slack thread of “looks fine to me.” Launch Rehearsal is different: it’s a monitoring product built for **release readiness**, not uptime alone.
>
> You configure three personas — like first-time evaluator, daily operator, and admin — and five journeys that mirror how humans actually use your product. Our pipeline crawls your site map, classifies workflows, runs browser journeys with step-level screenshots, and grades each persona × journey cell. A synthesizer agent rolls that into a readiness band — Red, Amber, or Green — plus prioritized P0–P3 issues and a **required delights section** so you capture what users would love, not just what’s broken.
>
> Every finding is evidence-bound: run ID, step ID, artifact link. You get a markdown scorecard, a local dashboard, and compare view that tells a release story — Red to Green, resolved vs new issues. CLI-first for engineers; dashboard for the readout with your PM.
>
> We’re in design partner phase: share your staging URL and critical journey, we run it async, and walk you through findings in 30 minutes. No auto-fix, no deploy — observe and score only.

### 2.4 Value pillars (4)

#### Pillar 1 — Persona × journey readiness (not page checks)

- **Headline:** Every user type, end to end  
- **Body:** Three personas cross five journeys in a single matrix — pass, partial, or fail with drill-down to steps. See whether your admin path fails while your evaluator path passes.  
- **Evidence hook:** Interactive matrix on run detail; click a cell → journey dialog → evidence  
- **Proof stat:** 3×5 matrix; Argyle run Green with 0 blockers  

#### Pillar 2 — Evidence-bound trust

- **Headline:** Findings you can replay, not vibes  
- **Body:** Every issue and delight links to run ID, step ID, and screenshot. Agree or disagree inline — false positives feed back without breaking the trust loop.  
- **Evidence hook:** Evidence dialog with “Copy repro”  
- **Proof quote (methodology):** Phase 0 Cal.com I1 — nav IA issue tagged `J1-S1` with ARIA evidence  

#### Pillar 3 — Delights, not bugs-only

- **Headline:** Capture what users would love  
- **Body:** Scorecards require a delights section — marketing-ready quotes, persona-attributed, tied to steps. Launch with strengths, not just a fix list.  
- **Evidence hook:** “9 marketing-ready delights” on dogfood; D1 Cal.com — “No credit card required without scrolling”  
- **Proof stat:** 9 delights on Argyle Green run  

#### Pillar 4 — Release diff story

- **Headline:** What changed since last deploy?  
- **Body:** Compare two runs side by side — readiness Red → Green, new vs resolved issues, crawl size delta. Export markdown for Linear handoff.  
- **Evidence hook:** Compare page narrative: “Red → Green, 16 pages crawled”  
- **Proof stat:** 0 → 16 pages between Argyle runs  

### 2.5 Objection handling FAQ (12 questions)

| # | Question | Answer (draft) |
|---|----------|----------------|
| 1 | Is this just Playwright with an LLM wrapper? | No. Playwright executes steps; Launch Rehearsal adds persona grading, readiness rollup, required delights, crawl-derived sitemap, multi-agent synthesis, and compare across runs. You get a scorecard, not a test log. |
| 2 | Will you change our code or deploy fixes? | **Never.** Observe and score only. We are explicitly not a fix bot (`MONITORING_PLATFORM_SPEC.md`, `CEO_DECISIONS.md`). |
| 3 | How long does a run take? | Typically under 30 minutes end to end; our dogfood command center shows ~2m 08s time-to-scorecard for a focused run. Crawl depth and journey count affect wall time. |
| 4 | What do you need from us to start? | Staging URL, test credentials for auth-gated flows, and one critical journey (e.g. login → core workflow). We run async before a 30-minute walkthrough. |
| 5 | Is staging data safe? | URLs pass SSRF preflight; secrets via env vars only, never in YAML. We do not exfiltrate data — we observe UI like a browser user. |
| 6 | What about false positives? | Every issue has evidence you can replay. Mark Agree / Disagree / False positive in the dashboard; we tune heuristics from partner feedback. |
| 7 | Does it replace user research? | No. It replaces *guessing* before you have enough users — complementary to UserTesting/Maze later. |
| 8 | Do you integrate with Slack/Jira? | Not yet. Export markdown scorecard and Linear backlog download today; OAuth integrations are Phase 2 (Dec 2026 target). |
| 9 | Can we run it in CI on every PR? | CLI emits JSON summary (`run_id`, readiness, paths). Productized GitHub Action is planned Aug 2026 — not marketed as shipped. |
| 10 | What’s the pricing? | We’re validating willingness to pay with design partners (~$49/mo hypothesis). No public pricing page until partners commit — book a call for early access. |
| 11 | SOC2 / security audit? | We surface compliance *signals* in heuristics (e.g. trust badges visible). We do not perform SOC2 audits or pen tests. |
| 12 | What’s NOT included yet? | Scheduled cron, SSO, alert routing, full WCAG agent, functional Performance agent, PLG signup. Compliance & Performance agents appear as idle in UI — honest Phase 2. |

### 2.6 Social proof strategy

**Phase 1 (MVP landing — ship now):**

| Asset | Use |
|-------|-----|
| Dogfood narrative | “We run Launch Rehearsal on ourselves” — lr-self runs, meta story |
| Argyle faculty dashboard | Anonymizable as “B2B authenticated SaaS” — Green, 9 delights, 16 pages |
| Cal.com Phase 0 scorecard | Public practice target — methodology credibility (issues I1–I3, delights D1–D4) |
| Design review score | “Partner-ready UI — 8.6/10 internal design review” — use cautiously, not as customer quote |
| Pipeline diagram | Multi-agent trace screenshot from `/agents` |

**Phase 2 (after 3 would-pay partners):**

| Asset | Use |
|-------|-----|
| Verbatim partner quotes | “Would you run this before every launch?” yes quotes |
| Logo bar | Partner logos with permission |
| Before/after readiness | Red → Green screenshots from partner runs (redacted) |
| Would-pay count | “3 teams committed at ~$49/mo” — only when true per CEO gate |
| Case study PDF | One-pager per partner vertical |

**Do not use:** Mock Acme `run_8s7d2` data, Lovable preview URLs, fabricated customer logos, “SOC2 compliant” badge.

---

## 3. Page information architecture

**Page type:** Single long-form landing + anchor nav  
**Estimated scroll depth:** 10–12 sections, ~4,500px desktop  
**Global nav:** Logo | How it works | Sample scorecard | Docs | **Get a staging scorecard** (button)

---

### Section 0 — Announcement bar (optional)

| Field | Spec |
|-------|------|
| **Purpose** | Design partner scarcity + honesty |
| **Persona** | All |
| **Message** | Now accepting design partners — free staging scorecard + 30-min readout |
| **CTA** | Same as primary |
| **Visual** | Slim indigo bar, white text |
| **Mobile** | Single line, dismissible |

**Copy:** `Design partner program open — free readiness scorecard on your staging URL.`

---

### Section 1 — Hero (above fold)

| Field | Spec |
|-------|------|
| **Purpose** | Instant category + trust + primary conversion |
| **Persona** | Eng lead, founder |
| **Key message** | Pre-launch readiness with evidence; observe-only |
| **Primary CTA** | Get a staging scorecard |
| **Secondary CTA** | See sample scorecard |
| **Visual direction** | Split layout: left copy, right **animated readiness gauge** (Green) + mini 3×5 matrix fading in. Warm off-white canvas (`oklch(0.985 0.003 260)`), indigo primary (`oklch(0.5 0.14 265)`), `--ready` green for band. Instrument Serif accent on one word optional (“observed”). |
| **Mobile** | Stack: H1 → subhead → primary CTA full width → secondary text link → static hero screenshot (matrix crop) |

**Trust chips below CTAs:** `Evidence-bound` · `No auto-fix` · `CLI + dashboard` · `~30 min scorecard`

---

### Section 2 — Problem (pain)

| Field | Spec |
|-------|------|
| **Purpose** | Agitate launch anxiety |
| **Persona** | Founder, eng lead |
| **Key message** | Happy-path tests and manual dogfood miss persona-blind regressions |
| **Primary CTA** | Get a staging scorecard (text link repeat) |
| **Visual** | Three-column pain cards with subtle red/amber left border |
| **Mobile** | Horizontal scroll cards or vertical stack |

**Header:** The launch checklist nobody trusts  
**Body:** See copy deck §4.

---

### Section 3 — How it works (3 steps)

| Field | Spec |
|-------|------|
| **Purpose** | Explain concierge flow + pipeline simply |
| **Persona** | QA, eng lead |
| **Key message** | Share staging → we run → you get scorecard + walkthrough |
| **Primary CTA** | Get a staging scorecard |
| **Visual** | Numbered steps with icons: URL → agents → scorecard. Optional thin agent pipeline strip (Crawler → … → Synthesizer) |
| **Mobile** | Vertical timeline |

**Steps:**

1. **Share staging** — URL, test login, one critical journey  
2. **We rehearse** — crawl, journeys, persona agents, synthesis (~30 min)  
3. **Review evidence** — 30-min readout + markdown export you keep  

---

### Section 4 — Product story (screenshots)

| Field | Spec |
|-------|------|
| **Purpose** | Show the dashboard is real |
| **Persona** | All; especially PM/founder |
| **Key message** | Command center → matrix → evidence is the product |
| **Primary CTA** | See sample scorecard |
| **Visual** | Tabbed or scroll-snap gallery: Command center, Run detail matrix, Evidence dialog, Compare Red→Green |
| **Mobile** | Swipe carousel with dot indicators |

**Caption pattern:** `[Feature name] — [one benefit]` e.g. “Run detail matrix — see which persona fails which journey”

---

### Section 5 — Persona matrix demo

| Field | Spec |
|-------|------|
| **Purpose** | Explain differentiation vs E2E |
| **Persona** | Eng lead, QA |
| **Key message** | Same product, three lenses |
| **Primary CTA** | Get a staging scorecard |
| **Visual** | Static or lightly animated 3×5 grid. Row labels: First-time evaluator, Daily operator, Admin/buyer. Column labels from Cal.com template: Land and grasp value · Start signup path · Explore product depth · Pricing evaluation · Return visitor navigation |
| **Mobile** | Rotate to card-per-journey with persona pills |

**Annotation callouts:** Pass (green), Partial (amber), Fail (red), FLAKY (hatched)

---

### Section 6 — Sample scorecard

| Field | Spec |
|-------|------|
| **Purpose** | Prove methodology with real language |
| **Persona** | PM, founder, skeptical eng |
| **Key message** | Real issues + real delights, evidence-tagged |
| **Primary CTA** | Download sample PDF / View full markdown |
| **Visual** | Styled markdown preview: Executive summary table, matrix snippet, 2 issue rows, 2 delight rows with quotes. Redacted run ID ok. |
| **Mobile** | Collapsible sections |

**Source content:** Blend `phase0-20260528-001-scorecard.md` (Cal.com) for issues/delights + Argyle metrics line for Green/9 delights/16 pages.

---

### Section 7 — Compare / diff story

| Field | Spec |
|-------|------|
| **Purpose** | Release-over-release value |
| **Persona** | Eng lead, release manager |
| **Key message** | Red → Green narrative |
| **Primary CTA** | Get a staging scorecard |
| **Visual** | Before/after readiness badges + short NLU compare quote panel. Screenshot from `/compare?a=argyle-20260530-235656&b=argyle-20260531-000517` |
| **Mobile** | Stacked before/after |

**Stat callouts:** Readiness Red → Green · Pages crawled 0 → 16 · Resolved vs new issues

---

### Section 8 — CLI + dashboard

| Field | Spec |
|-------|------|
| **Purpose** | Developer credibility |
| **Persona** | Eng lead, design engineer |
| **Key message** | CLI for automation, dashboard for readout |
| **Primary CTA** | Read CLI docs (GitHub) |
| **Visual** | Split: terminal with `rehearse run` / JSON output + browser chrome at `:8081/` command center. JetBrains Mono for code |
| **Mobile** | Tab toggle CLI | Dashboard |

**Code block (display):**

```bash
./rehearse run -c rehearse.yaml -o artifacts --llm
./rehearse serve -o artifacts
# Dashboard: cd Frontend_V1 && npm run dev → :8081
```

---

### Section 9 — Integrations (honest)

| Field | Spec |
|-------|------|
| **Purpose** | Preempt integration questions; build trust via honesty |
| **Persona** | Eng lead |
| **Key message** | Export today; OAuth later |
| **Primary CTA** | None — informational |
| **Visual** | Grid: **Available now** (Markdown export, Linear markdown download, JSON/GraphML sitemap, CLI diff) vs **Roadmap** (Slack, Jira OAuth, GitHub Action, cron, SSO) — grayed roadmap cards |
| **Mobile** | Two stacked lists |

**Header:** Integrations — what works today  
**Subhead:** We’d rather show an honest export path than a broken Connect button.

---

### Section 10 — Pricing teaser (no public pricing)

| Field | Spec |
|-------|------|
| **Purpose** | Anchor value without violating CEO gate |
| **Persona** | Founder |
| **Key message** | Design partner pricing conversation |
| **Primary CTA** | Get a staging scorecard |
| **Visual** | Single card: “Design partner — free staging scorecard” + bullet list of what’s included. Small footnote: “Pro tier ~$49/mo under validation — not billed during partner phase” |
| **Mobile** | Same card, full width |

**Do NOT:** Tier table with $49/$199, “Buy now”, feature comparison vs competitors on price.

---

### Section 11 — Design partner CTA (conversion block)

| Field | Spec |
|-------|------|
| **Purpose** | Primary lead capture |
| **Persona** | Qualified ICP |
| **Key message** | Free run + 30-min readout |
| **Primary CTA** | Form submit → Calendly |
| **Visual** | Full-width indigo band, white form fields, serif headline |
| **Mobile** | Form fields stack; sticky bottom CTA optional |

**Form fields:** See §6.

---

### Section 12 — FAQ

| Field | Spec |
|-------|------|
| **Purpose** | Objection handling + SEO |
| **Persona** | All |
| **Key message** | Honest scope |
| **Primary CTA** | Get a staging scorecard (bottom) |
| **Visual** | Accordion, Radix-style |
| **Mobile** | Full width accordion |

Use FAQ copy from §2.5.

---

### Section 13 — Footer

| Field | Spec |
|-------|------|
| **Purpose** | Nav + legal + GitHub |
| **Columns** | Product (How it works, Sample scorecard, CLI docs) · Company (GitHub, Contact) · Legal (Privacy, Terms placeholder) |
| **Microcopy** | © 2026 Lapse AI · Launch Rehearsal · Observe and score only |
| **Mobile** | Collapsed columns |

---

## 4. Copy deck (draft actual words)

### 4.1 Hero

**H1:** Pre-launch readiness, observed.

**H2:** Launch Rehearsal runs your staging app through three persona lenses and five end-to-end journeys — then delivers a Red/Amber/Green scorecard with screenshot evidence in under 30 minutes. Evidence-bound. No auto-fix.

**Primary button:** Get a staging scorecard  
**Secondary link:** See sample scorecard → anchor `#sample-scorecard`  
**Tertiary link:** Read CLI docs → GitHub README

### 4.2 Problem section

**Header:** The launch checklist nobody trusts  
**Body:** Your E2E suite goes green on the happy path. Someone clicked around staging in Slack. Marketing wants “just ship it.” You still don’t know if an admin sees Red while a prospect sees Green — or what you’d actually show the board if asked “are we ready?” Launch Rehearsal replaces guesswork with a persona × journey rehearsal and an evidence bundle your PM can open without asking engineering for another favor.

### 4.3 How it works

**Header:** How a design partner run works  
**Body:** We operate the CLI and walk the dashboard with you — no self-serve signup required during the partner phase.

**Step 1 — Share staging**  
Send your staging URL, test credentials for auth flows, and one critical journey (login → core workflow is enough). We preflight the URL and scaffold config with `rehearse init`.

**Step 2 — We rehearse**  
Our pipeline crawls your app (when enabled), classifies workflows, runs browser journeys with step screenshots, and grades each persona × journey cell. Persona agents and a synthesizer produce your readiness band, blockers, and delights.

**Step 3 — Review evidence**  
Before a 30-minute call, you receive a markdown scorecard. On the call we drill into the matrix, open evidence dialogs, and compare to your last run if you have one. You keep the export — including Linear backlog markdown.

### 4.4 Product story tabs

**Tab 1 — Command center**  
Live rollup of readiness, blockers, delights, flake rate, and run history — not a demo database.

**Tab 2 — Persona × journey matrix**  
The hero view: which journeys pass for which personas. Click any cell to inspect steps.

**Tab 3 — Evidence dialog**  
Screenshot, step ID, copy-paste repro — every finding is replayable.

**Tab 4 — Compare runs**  
Red → Green across releases. Resolved vs new issues. Crawl size delta.

### 4.5 Persona matrix section

**Header:** Three personas. Five journeys. One matrix.  
**Body:** Generic E2E tests ask “did the script pass?” Launch Rehearsal asks “would the evaluator, the daily operator, and the admin each succeed on the paths that matter?” Partial cells surface friction that happy-path automation misses — before your users do.

**Persona blurbs:**

- **First-time evaluator** — Grasp value, reach signup, survive first-run confusion  
- **Daily operator** — Repeat tasks, filters, navigation efficiency  
- **Admin / buyer** — Boundaries, trust signals, plan comparison  

### 4.6 Sample scorecard section

**Header:** Sample findings — evidence-bound, not a bug dump  
**Body:** From a public Phase 0 rehearsal (Cal.com practice target). Your staging scorecard uses the same format with your product’s screenshots and step IDs.

**Sample executive summary (display):**

| | |
|---|---|
| **Readiness** | Amber — strong product; marketing surface has comparison fatigue |
| **Top blocker** | Pricing comparison overload for admin persona |
| **Top delight** | Signup above fold with “no credit card” + live booking preview |

**Sample issue (display):**  
**P2 — Pricing comparison fatigue:** Feature breakdown extremely long; admin must scroll massive matrix to compare plans. Evidence: `J4-S1` on pricing journey.

**Sample delight (display):**  
**D1 — Immediate time-to-value:** Hero offers Sign up with Google, email signup, and “No credit card required” without scrolling. Evidence: `J1-S3`.

**Footnote:** Dogfood run on authenticated B2B SaaS: Green, 0 blockers, 9 delights, 16 pages crawled.

### 4.7 Compare section

**Header:** What changed since Tuesday?  
**Body:** Compare two runs side by side — readiness band shift, new and resolved issues, sitemap delta. Our dogfood runs went Red → Green as crawl coverage grew from 0 to 16 pages. That’s the story you want before standup, not a wall of test logs.

### 4.8 CLI + dashboard section

**Header:** CLI for engineers. Dashboard for the readout.  
**Body:** Run `rehearse run` in CI or locally. Serve artifacts with `rehearse serve` and open the React command center for persona matrix review, annotations, and export. Init wizard scaffolds YAML from your URL — no manual DSL archaeology.

### 4.9 Integrations section

**Header:** Export paths that work today  
**Body:** Markdown scorecards, JSON analysis bundles, GraphML sitemaps, CLI diff, and Linear backlog markdown download. Native Slack, Jira OAuth, scheduled cron, and SSO are on the roadmap — we won’t pretend they’re live.

**Available now:** Markdown export · Linear backlog (markdown) · CLI JSON summary · GraphML sitemap · Compare API  
**Roadmap:** Slack alerts · Jira OAuth · GitHub Action · Cron scheduling · SSO  

### 4.10 Pricing teaser

**Header:** Design partner program  
**Body:** Free staging scorecard and 30-minute evidence walkthrough. We’re validating a Pro tier (~$49/mo hypothesis) with partners who would run this before every launch — you won’t be billed during the partner phase.

**Bullets:**

- Async run on your staging URL before the call  
- Markdown scorecard + dashboard walkthrough  
- Compare against a prior run when available  
- Direct line to shape Phase 2 integrations  

### 4.11 Design partner CTA block

**Header:** Would you run this before every launch?  
**Body:** Share staging access and one critical journey. We’ll run Launch Rehearsal async and walk you through blockers, delights, and evidence in 30 minutes.

**Button:** Request partner slot  
**Privacy microcopy:** Staging credentials used only for your rehearsal run. Secrets via env vars — never committed to config in git.

### 4.12 Microcopy

| Element | Copy |
|---------|------|
| Nav logo alt | Launch Rehearsal |
| Nav CTA | Get a scorecard |
| Readiness badge Green | Green — ready to ship (review P2/P3 polish) |
| Readiness badge Amber | Amber — ship with known issues |
| Readiness badge Red | Red — blockers need attention |
| Evidence tooltip | Opens screenshot + step ID + copy repro |
| FLAKY badge | Parallel seeds disagreed — investigate flake |
| Observe-only badge | Observe and score only |
| Cost label (if shown) | estimate · not billed |
| Footer tagline | Observe and score only — no auto-fix, no deploy |

### 4.13 Meta / OG

**Title:** Launch Rehearsal — Pre-launch readiness monitoring for B2B SaaS  
**Meta description:** Persona × journey rehearsals on your staging URL. Evidence-bound scorecards with blockers, delights, and screenshots in ~30 minutes. Observe only — no auto-fix.  
**OG title:** Pre-launch readiness, observed.  
**OG description:** Three personas. Five journeys. One evidence-bound scorecard. Free design partner staging run.  
**OG image concept:** Command center crop — Green readiness gauge + matrix thumbnail + logo wordmark on warm off-white  

---

## 5. Visual & interaction spec

### 5.1 Tone and brand

| Element | Spec |
|---------|------|
| **Voice** | Calm, precise, engineering-trustworthy — not hype-y AI buzz |
| **Typography** | Inter (UI), Instrument Serif (optional display accent), JetBrains Mono (CLI/code) — match `Frontend_V1/src/styles.css` |
| **Color** | Warm off-white background; slate ink text; indigo primary; semantic `--ready` / `--warn` / `--danger` for readiness bands |
| **Density** | SaaS command-center feel — cards, subtle borders, not marketing fluff gradients |
| **Anti-patterns** | Purple AI gradients, stock photos of diverse teams pointing at laptops, “autonomous agent” hero without evidence |

### 5.2 Hero visual concept

**Recommended:** **Terminal + dashboard split** with readiness gauge animation:

1. On load: gauge animates 0 → 92, band fades Green  
2. Mini 3×5 matrix cells populate pass/partial sequentially (stagger 50ms)  
3. Subtle screenshot parallax on scroll  

**Alternative:** Full-bleed annotated screenshot of `/runs/argyle-20260531-000517` with callout pins on matrix + delights panel.

### 5.3 Screenshot / asset list

Capture with `./rehearse serve` running + `Frontend_V1` at `:8081`, run ID `argyle-20260531-000517`, viewport **1280×720** (desktop) and **390×844** (mobile). Hide Dev badge: use `npm run dev:vision` or production build.

| Asset ID | Route | Capture notes | Use |
|----------|-------|---------------|-----|
| SS-01 | `/` | Command center with live KPIs, readiness explainer visible | Hero alternate, product tab 1 |
| SS-02 | `/runs/argyle-20260531-000517` | Full matrix + delights panel | Hero primary, persona section |
| SS-03 | `/runs/argyle-20260531-000517` | Evidence dialog open on any issue | Product tab 3, trust pillar |
| SS-04 | `/compare?a=argyle-20260530-235656&b=argyle-20260531-000517` | Red→Green summary visible; Advanced JSON collapsed | Compare section |
| SS-05 | `/agents` | Collaboration trace; Compliance/Performance idle | How it works / pipeline |
| SS-06 | `/sitemap?run=argyle-20260531-000517` | Hub/leaf/orphan list | Optional crawl story |
| SS-07 | `/init` | Generate & write YAML enabled | CLI section |
| SS-08 | `/recommendations` | Export to Linear button visible | Integrations |
| SS-09 | `/runner` | Run form with target URL | Optional |
| SS-10 | `/cli` | Terminal-style CLI reference page | CLI section |
| SS-11 | Mobile `/` @ 390px | Hamburger nav open | Mobile credibility |
| SS-12 | Mobile `/runs/argyle-20260531-000517` | Matrix scroll | Mobile product tab |

**Static exports (non-screenshot):**

- PDF/markdown: `enterprise_work_env_simulator_2026/results/phase0-20260528-001-scorecard.md`  
- Annotated sample: render styled HTML from scorecard template  

**Video (Phase 2):** 90s screen recording: command center → matrix → evidence → compare.

### 5.4 Motion / animation

| Element | Motion |
|---------|--------|
| Readiness gauge | 1.2s ease-out fill on hero load |
| Matrix cells | Stagger fade-in; pass=green pulse once |
| Scroll reveals | Sections fade up 20px, 0.4s, respect `prefers-reduced-motion` |
| Compare Red→Green | Badge morph animation on scroll into view |
| CTA button | Subtle indigo darken on hover; no infinite bounce |

### 5.5 Accessibility

| Requirement | Spec |
|-------------|------|
| Contrast | WCAG AA minimum for text; readiness colors paired with text labels (not color-only) |
| Focus | Visible focus rings matching `--ring` indigo |
| Motion | `prefers-reduced-motion: reduce` disables gauge/matrix animations |
| Images | Alt text describes content: “Persona journey matrix showing Green readiness with 9 delights” |
| Forms | Labels associated; error messages announced |
| Headings | Single H1; logical H2/H3 hierarchy |
| Interactive demo | If embed live UI, keyboard-trap-free; prefer static screenshots for MVP |

---

## 6. Conversion funnel

### 6.1 Primary paths

```text
Landing hero CTA
    → Lead form (minimal)
        → Auto-reply email with sample scorecard link
        → Calendly 30-min slot
            → Async: partner sends staging URL + creds
            → Preflight + `./rehearse run`
            → Email scorecard MD + dashboard link (deployed demo or Loom)
            → Call: north star + would-pay questions
```

**Path B — CLI curious:**

```text
Read CLI docs (GitHub) → star repo → return to form when staging ready
```

**Path C — Sample scorecard:**

```text
See sample scorecard → scroll to CTA → form (lower friction — email only ok)
```

### 6.2 Lead capture form fields (minimal)

| Field | Required | Notes |
|-------|----------|-------|
| Work email | Yes | Block free domains optional (gmail ok for founders) |
| Staging URL | Yes | Validates https:// |
| Role | Yes | Dropdown: Eng lead / Founder / PM / QA / Other |
| Company | No | |
| Critical journey (1 sentence) | No | Placeholder: “Login → dashboard → export report” |
| How did you hear about us? | No | |

**Do not ask on MVP form:** Credit card, password, OAuth, file upload.

### 6.3 Post-submit experience

1. **Immediate:** Thank-you page — “We’ll email you within 1 business day to schedule. Meanwhile, here’s the sample scorecard.”  
2. **Email 1 (auto):** Sample scorecard PDF/link + link to GitHub README + what to prepare (staging URL, test login, one journey)  
3. **Email 2 (human, <24h):** Calendly link or proposed times  
4. **After run:** Scorecard attachment + optional deployed read-only dashboard link  
5. **After call:** Log north star + would-pay in `DESIGN_PARTNER_CHECKLIST.md` tracking table  

### 6.4 Analytics events

| Event | Trigger |
|-------|---------|
| `landing_view` | Page load |
| `cta_click_hero` | Primary hero CTA |
| `cta_click_sample` | Sample scorecard link |
| `cta_click_cli` | CLI docs link |
| `form_start` | First field focus |
| `form_submit` | Successful submit |
| `form_error` | Validation fail |
| `section_view_*` | Intersection observer per section (how_it_works, sample, compare, faq) |
| `sample_download` | PDF/markdown download |
| `outbound_github` | GitHub README click |

**Stack suggestion:** Plausible or PostHog — lightweight, no cookie banner if possible.

---

## 7. SEO & distribution

### 7.1 Target keywords

| Intent | Keywords |
|--------|----------|
| Primary | pre-launch testing, launch readiness, staging QA automation |
| Secondary | persona testing SaaS, E2E testing before launch, release readiness scorecard |
| Long-tail | “run QA on staging before launch”, “evidence-based QA report”, “B2B SaaS launch checklist engineering” |
| Avoid bidding | “SOC2 automation”, “Playwright alternative” (adversarial, inaccurate) |

### 7.2 Page title structure

`Launch Rehearsal — Pre-launch readiness monitoring | Persona × journey scorecards`

Future blog titles cross-linking:

- “Red → Green: what a release diff scorecard looks like”  
- “Why we require a delights section in every scorecard”  
- “Observe-only QA: why Launch Rehearsal never auto-fixes your app”  

### 7.3 Cross-promotion links

| Destination | Link text |
|-------------|-----------|
| GitHub README | CLI quickstart |
| `launch-rehearsal/README.md` | Commands reference |
| `DESIGN_PARTNER_CHECKLIST.md` (internal) | Not public — operational |
| Future docs site | `/docs/init`, `/docs/config` |

### 7.4 Launch channels (design partner phase)

| Channel | Message | CTA |
|---------|---------|-----|
| Warm network / YC alumni | Free staging scorecard offer | Direct email |
| Twitter/X builder audience | Dogfood thread — lr-self meta narrative | Sample scorecard |
| Hacker News (Show HN) | **Defer until 1+ partner quote** — risk of PLG expectations | GitHub + partner CTA |
| Product Hunt | **Defer** — same reason | |
| Eng Slack communities | “Would you run this before every launch?” poll + offer | Form |
| Founder podcasts | Concierge offer | Custom URL `?ref=` |

**HN/PH risk:** Audience expects instant signup — landing must lead with design partner honesty.

---

## 8. Technical implementation notes (for eng)

### 8.1 Suggested stack

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A. Static site (Astro/Next export)** in `marketing/` | Fast, SEO, no coupling | Design token duplication | **Recommended for MVP** |
| **B. New route in Frontend_V1** | Shared tokens/components | Mixes app + marketing; TanStack Start complexity | Avoid for MVP |
| **C. Separate domain + Webflow** | Designer-friendly | Token drift, cost | Only if non-eng owns updates |

**MVP path:** `marketing/` Astro or Next static export → deploy Vercel/Cloudflare Pages at `launchrehearsal.dev` or `trylapse.com/launch-rehearsal`.

### 8.2 Design tokens / components

**Reuse from Frontend_V1:**

- CSS variables from `styles.css`: `--ready`, `--warn`, `--danger`, `--primary`, fonts  
- Readiness gauge concept from command center (reimplement or extract shared package later)  
- Matrix cell colors: pass/partial/fail/FLAKY  

**Do not embed** live `:8081` dashboard in iframe on public landing — security, mock fallback confusion, no auth.

### 8.3 Sample scorecard embed

| Approach | When |
|----------|------|
| **Static HTML** rendered at build from `phase0-20260528-001-scorecard.md` | MVP |
| **PDF export** from same source | Email attachment |
| **API embed** from `/api/runs/...` | Phase 2 — requires deployed public demo API |

Build script: `pnpm build:marketing` copies sanitized scorecard markdown → HTML.

### 8.4 Performance budget

| Metric | Target |
|--------|--------|
| LCP | < 2.5s on 4G |
| Total JS | < 100kb gzipped (static preferred) |
| Hero image | WebP, max 200kb per screenshot |
| Fonts | Self-host or Google with `display=swap` — match dashboard |

### 8.5 Form backend

Options: Formspree, Netlify Forms, or thin API route on same host posting to email + Notion/Airtable partner table.

---

## 9. Phased rollout

### 9.1 MVP landing (design partner phase) — ship now

| Content | Ready? |
|---------|--------|
| Hero + problem + how it works | ✅ Copy ready |
| Product screenshots from `:8081` | ✅ Requires capture session |
| Sample scorecard (Cal.com Phase 0) | ✅ File exists |
| Compare Red→Green story | ✅ Argyle runs |
| CLI section + GitHub link | ✅ |
| Honest integrations grid | ✅ |
| Design partner form + Calendly | ⚠️ Needs form backend |
| FAQ | ✅ |
| Pricing teaser (no tiers) | ✅ |
| Customer logos / quotes | ❌ Blocked — no partners closed yet |
| Public pricing page | ❌ CEO gate |
| Live demo sandbox | ❌ Deferred |

### 9.2 v2 landing (post 3 would-pay)

| Addition | Gate |
|----------|------|
| Partner quotes + logos | 3 verbal pay commits |
| Public pricing page | CEO §3 |
| “Start free” PLG CTA | L3-OPS-06 shipped |
| Interactive demo (init wizard public) | Self-serve stable |
| GitHub Action badge | Aug 2026 |
| Case studies | 1+ partner published |

### 9.3 Content blocked on assets

| Asset | Blocker | Owner |
|-------|---------|-------|
| Partner testimonial | No completed partner calls | Founder |
| Logo bar | Permission | Founder |
| OG image | Design export | Designer |
| 90s product video | Screen recording | Eng/design |
| Public demo API | Infra + redacted runs | Eng |

---

## 10. Appendix

### 10.1 Competitor differentiation table

| Capability | Launch Rehearsal | Playwright/Cypress | Datadog synthetics | Manual QA | UserTesting |
|------------|------------------|--------------------|--------------------|-----------|-------------|
| Persona × journey matrix | ✅ Core | ❌ DIY | ❌ | ⚠️ Ad hoc | ✅ Humans |
| Required delights | ✅ | ❌ | ❌ | ⚠️ | ✅ |
| Readiness Red/Amber/Green | ✅ | ❌ | ⚠️ Uptime | ❌ | ❌ |
| Evidence screenshots + step ID | ✅ | ⚠️ Trace | ⚠️ Screenshots | ⚠️ | ✅ |
| Crawl + sitemap | ✅ | ❌ | ❌ | ❌ | ❌ |
| Compare runs / release diff | ✅ | ⚠️ CI history | ⚠️ | ❌ | ❌ |
| Multi-agent narrative | ✅ | ❌ | ❌ | ❌ | ❌ |
| Time to first scorecard | ~10–30 min | Hours (author tests) | Hours | Days | Days–weeks |
| Observes only (no fix) | ✅ Explicit | N/A | N/A | N/A | N/A |
| Pre-customer / no users yet | ✅ ICP | ✅ | ✅ | ✅ | ❌ Needs users |
| Price (hypothesis) | ~$49/mo Pro | Free OSS | $$$$ | Labor cost | $$$ per session |

### 10.2 Glossary

| Term | Definition |
|------|------------|
| **Readiness band** | Red / Amber / Green rollup from blockers and dimension scores — executive launch signal |
| **Persona** | Synthetic user lens (e.g. first-time evaluator, daily operator, admin) with goals — not a single test user |
| **Journey** | End-to-end scripted flow (navigate, click, fill, wait, assert) — typically 5 per config |
| **Scorecard** | Markdown report: matrix, issues P0–P3, delights, dimensions, evidence links |
| **Evidence-bound** | Finding must cite `run_id` + `step_id` + artifact or generator rejects it |
| **Flake rate** | Share of steps/runs where parallel seeds disagree — FLAKY flag |
| **Blocker** | P0/P1 issue counting against readiness |
| **Delight** | Documented positive — quote + persona + step evidence; required section |
| **Observe-only** | Product never modifies, deploys, or patches the target application |
| **Design partner** | Concierge customer — free run, feedback, would-pay validation |

### 10.3 Doc cross-reference map

| Landing claim | Backing doc |
|---------------|-------------|
| North star question | `DESIGN_PARTNER_CHECKLIST.md`, `CEO_DECISIONS.md` §2 |
| Design partner offer | `DESIGN_PARTNER_CHECKLIST.md` §Offer |
| 8.6/10 UI partner-ready | `live-2026-05-31.md` |
| Argyle Green / 9 delights / 16 pages | `live-2026-05-31.md`, `AGENT_BRIEF.md` |
| Red → Green compare | `live-2026-05-31.md`, `AGENT_BRIEF.md` demo flow |
| Observe-only / no auto-fix | `CEO_DECISIONS.md` §8, `MONITORING_PLATFORM_SPEC.md` §1 |
| Do-not-promise list | `FEATURE_SCOPE.md` §1, `AGENT_BRIEF.md` |
| No public pricing | `CEO_DECISIONS.md` §3 |
| ~$49/mo hypothesis | `DESIGN_PARTNER_CHECKLIST.md`, `PRODUCT.md` §4.4, `POSITIONING.md` |
| Persona/journey counts (3×5) | `FEATURE_SCOPE.md` L1-DSL-01, `CEO_DECISIONS.md` §4 |
| CLI commands | `launch-rehearsal/README.md`, `FEATURE_SCOPE.md` L1-CLI |
| Init wizard | `FEATURE_SCOPE.md` L2-UI-63, PR #14 |
| Linear export stub | `FEATURE_SCOPE.md` L2-UI-50 |
| NLU compare/summary | `INTERPRETABILITY.md` |
| Dashboard headline copy | `Frontend_V1/src/routes/index.tsx` |
| Visual tokens | `Frontend_V1/src/styles.css` |
| Cal.com sample issues/delights | `results/phase0-20260528-001-scorecard.md` |
| Journey naming examples | `launch-rehearsal/examples/cal-com-phase0.yaml`, `argyle-20260531-000517.yaml` |
| Category / ICP | `PRODUCT.md`, `POSITIONING.md` |
| Competitive context | `PRODUCT.md` §1, `pricing-landscape.md` |
| UI product lines / demo stack | `UI_PRODUCT_LINES.md` |
| Phase 0 CEO gate pass | `results/phase0-20260528-001-scorecard.md`, `PHASE0_GO_NOGO.md` |

---

## Implementation checklist (for executor)

- [ ] Capture SS-01 through SS-12 from live stack  
- [ ] Build static marketing site in `marketing/`  
- [ ] Render sample scorecard HTML from Phase 0 markdown  
- [ ] Wire form → email + partner tracking table  
- [ ] Legal: privacy policy placeholder for staging creds handling  
- [ ] CEO review: confirm no deferred features in hero/FAQ  
- [ ] Soft launch to 5 warm contacts before HN  
- [ ] Log north star answers in partner tracking table  

---

*Plan authored 2026-05-31. Planning + synthesis only — no code implemented.*
