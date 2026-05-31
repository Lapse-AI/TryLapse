# Monitoring Platform Spec — Launch Rehearsal

**Purpose:** Inventory of everything needed for the **monitoring, analysis, suggestion, and agent** experience when using Launch Rehearsal at enterprise scale.  
**Scope:** Product surface (dashboard + CLI + API) — not fixes to target applications under test.  
**Date:** May 29, 2026 · **Updated:** May 31, 2026 (CLI + dashboard; dual UI lines)

**Related:** `FEATURE_SCOPE.md` (L1/L2/L3) · `UI_PRODUCT_LINES.md` (Vision vs Deliverable) · `DESIGN_PARTNER_CHECKLIST.md` (outreach + demo gates)

---

## 1. Core principles

| Principle | Implication |
|-----------|-------------|
| Observe, don't modify | Never deploy or patch the customer's product |
| Evidence-bound | Every issue/delight links to `run_id`, `step_id`, artifact |
| Persona × journey E2E | Matrix is mandatory; not a page checklist |
| Multi-agent collaboration | Crawler, workflow, journey, persona, synthesizer agents |
| Enterprise-agnostic | Any URL, any stack; config-driven |

---

## 1.1 Dashboard UI (locked 2026-05-31)

**Dev and Vision both run the newest Vision-level UI** at http://127.0.0.1:8081/ — same routes and chrome. Badge differs (`Dev` vs `Vision`) only.

[`UI_PRODUCT_LINES.md`](UI_PRODUCT_LINES.md)

---

## 2. Run orchestration (backend)

### 2.1 Crawl & discovery

- [ ] Same-origin BFS crawler (depth, page budget, robots respect optional)
- [ ] Sitemap export (JSON, Markdown, GraphML optional)
- [ ] Hub / orphan / auth-gated page detection
- [ ] Workflow classification (auth, pricing, admin, search, docs, dashboard)
- [ ] Auto-journey generation from crawl graph
- [ ] Crawl diff between runs (new/removed/changed pages)
- [ ] Subdomain / multi-tenant URL sets
- [ ] Authenticated crawl (session from env or SSO test account)

### 2.2 Journey execution

- [ ] Journey DSL (navigate, click, fill, wait, assert)
- [ ] Secret injection via env vars only
- [ ] Run budgets (steps, wall time, per-step timeout)
- [ ] SSRF-safe URL preflight
- [ ] Per-step screenshots + text snapshot + ARIA metrics
- [ ] Network/console error capture
- [ ] Parallel journey seeds + FLAKY flag (Phase 2)
- [ ] Repeat micro-loop (3× same journey for friction signal)
- [ ] Mobile / tablet viewport profiles
- [ ] API+UI hybrid steps (optional)

### 2.3 Multi-agent pipeline

| Agent | Responsibility |
|-------|----------------|
| **Crawler** | Site structure, sitemap, orphans |
| **Workflow** | Pattern detection, journey supplementation |
| **Journey runner** | Browser E2E execution |
| **Persona evaluators** (×3+) | Re-grade from prospect / operator / admin lens |
| **Synthesizer** | Dedupe, prioritize, readiness rollup |
| **Compliance agent** (Phase 2) | PII, auth boundary signals |
| **Performance agent** (Phase 2) | Latency, Web Vitals |
| **LLM persona agent** (Phase 2) | Natural-language journey reasoning |

- [ ] Agent status stream (running / done / failed)
- [ ] Agent-to-agent handoff artifacts
- [ ] Human override / replay single agent
- [ ] Agent cost + duration accounting

---

## 3. Monitoring dashboard (primary UI)

### 3.1 Home / command center

- [ ] Readiness gauge (Red / Amber / Green) per product/environment
- [ ] Latest run summary (blockers, delights, duration)
- [ ] Run history sparkline (readiness over time)
- [ ] Quick actions: Run now, Crawl only, Compare last two runs
- [ ] Environment selector (staging, prod-canary, demo)

### 3.2 Run detail view

- [ ] Run metadata (ID, target, config hash, duration, outcome)
- [ ] Persona × journey matrix (interactive — drill to steps)
- [ ] Dimension rollup charts (Functionality, UI/UX, Information + full 8 later)
- [ ] Issues table (P0–P3 filter, evidence links)
- [ ] Delights section (required — not bugs-only)
- [ ] Embedded screenshot gallery per step
- [ ] Side-by-side run diff (same journey, two runs)
- [ ] Export PDF / Markdown / JSON

### 3.3 Site map explorer

- [ ] Interactive graph (pages as nodes, links as edges)
- [ ] Filter: auth-gated, orphans, errors, forms
- [ ] Click page → preview screenshot from last crawl
- [ ] Workflow type badges on nodes
- [ ] Compare sitemap across runs (diff highlight)

### 3.4 Workflow map

- [ ] Detected workflows list (auth, pricing, admin, …)
- [ ] Coverage indicator (which workflows have journey coverage)
- [ ] Suggested new journeys (accept → add to config)

### 3.5 Trends & monitoring

- [ ] Readiness trend by dimension
- [ ] Issue recurrence ("same blocker 3 runs in a row")
- [ ] New issue / resolved issue tracking
- [ ] Flake rate trend
- [ ] Crawl size / depth trend
- [ ] Scheduled runs calendar

### 3.6 Alerts & notifications

- [ ] Slack / email on readiness drop
- [ ] P0 issue instant alert
- [ ] Weekly digest scorecard
- [ ] Webhook for CI (GitHub Action, Vercel deploy hook)

---

## 4. Analysis & suggestions

### 4.1 Issue intelligence

- [ ] Severity explanation (why P1 vs P2)
- [ ] Confidence label (`high` vs `hypothesis`)
- [ ] Persona impact ("blocks P3 admin, not P1 prospect")
- [ ] Similar issues from past runs
- [ ] Suggested owner (frontend, backend, content, security) — heuristic or LLM
- [ ] **No auto-fix** — suggestion text only, with evidence links

### 4.2 Recommendation engine

- [ ] Prioritized backlog export (Jira, Linear, GitHub Issues)
- [ ] "Fix before launch" shortlist (CEO gate style)
- [ ] Gap / wish list (repeat-user friction, hypothesis)
- [ ] Competitive benchmark slot (manual compare URL optional)
- [ ] Rubric alignment (`EVALUATION_FRAMEWORK.md` dimension tags)

### 4.3 Delights & strengths

- [ ] Required section in every scorecard
- [ ] Marketing-ready quotes from persona agents
- [ ] Regression detection if delight disappears

---

## 5. Agent page (multi-agent control center)

### 5.1 Agent roster

- [ ] Live status per agent in current run
- [ ] Agent role description + last summary
- [ ] Expandable findings/delights per agent before synthesis
- [ ] Persona agent "voice" — goals, patience, stress factors from config

### 5.2 Agent configuration

- [ ] Enable/disable agents per run
- [ ] Persona editor (3–7 personas, goals, roles)
- [ ] Crawl budget sliders
- [ ] Strict enterprise mode toggle (expect pricing/docs/admin paths)
- [ ] LLM model pick for Phase 2 persona agents

### 5.3 Collaboration trace

- [ ] Timeline: Crawler → Workflow → Journey → Persona×N → Synthesizer
- [ ] Handoff payloads (sitemap JSON, step count, merge stats)
- [ ] Replay from any agent stage

### 5.4 Human-in-the-loop

- [ ] Annotate finding (agree / disagree / false positive)
- [ ] Add manual finding with evidence upload
- [ ] Pin finding for design partner review

---

## 6. Configuration & workspaces

- [ ] Workspace per product (multi-product portfolio)
- [ ] YAML editor + validator for journey DSL
- [ ] Config versioning (git link optional)
- [ ] Environment variables manager (REHEARSE_* secrets, never in YAML)
- [ ] Journey library / templates by vertical (SaaS, e-commerce, internal tools)
- [ ] Import OpenAPI / sitemap.xml as crawl seed

---

## 7. Integrations (enterprise)

| Integration | Use |
|-------------|-----|
| GitHub Actions | Run on PR / pre-deploy |
| Vercel / Netlify hooks | Post-deploy rehearsal |
| Slack | Alerts + scorecard snippet |
| Jira / Linear | Issue export |
| Datadog / Sentry | Correlate with prod errors (Phase 2) |
| SSO | Dashboard login (Phase 2) |
| RBAC | Admin vs viewer vs run-only |

---

## 8. CLI (shipped / planned)

| Command | Status |
|---------|--------|
| `rehearse run` | Shipped — crawl + journeys + multi-agent + scorecard + analysis bundle |
| `rehearse crawl` | Shipped — sitemap only |
| `rehearse scorecard` | Shipped — regenerate from evidence |
| `rehearse diff` | Shipped — compare two runs (CLI + `/api/diff`) |
| `rehearse init` | Shipped — scaffold config from URL |
| `rehearse serve` | Shipped — dashboard API + artifact server |
| `rehearse backfill` | Shipped — rebuild analysis bundles |
| `rehearse schedule` | Planned — cron wrapper |

---

## 9. Data & compliance

- [ ] Evidence retention policy (30/90/365 days)
- [ ] PII redaction in screenshots/text optional
- [ ] Audit log (who ran, who viewed scorecard)
- [ ] SOC2-ready storage story (Phase 2)
- [ ] Customer-managed keys for secrets

---

## 10. Phase map

| Phase | Focus |
|-------|--------|
| **Now (CLI)** | Crawl, journeys, multi-agent heuristics, scorecard |
| **Phase 2** | Web dashboard (§3–5), LLM persona agents, CI integration |
| **Phase 3** | Design partner workspaces, billing, trend alerting |
| **Phase 4** | Product B (Deal Rehearsal) — synthetic org context |

---

## 11. Success metrics (platform)

- Time to first scorecard &lt; 15 min for new URL
- ≥1 non-obvious issue + ≥1 delight on real dogfood URL
- Founders answer "would run before every launch" (5 design partners — track in `DESIGN_PARTNER_CHECKLIST.md`)
- False positive rate tracked via human annotations

---

*This spec is the north star for the monitoring product surface. CLI + partial dashboard API implement §2 and §8; full dashboard UX is L1/L2 mix per `FEATURE_SCOPE.md`.*
