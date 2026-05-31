# Browser capability parity — customers get Rehearsal only

**Date:** 2026-05-31  
**Principle:** Design partners and production customers never use Cursor Browser DevTools MCP. Every capability that materially improves **observe-only launch rehearsal** must live in `launch-rehearsal` (CLI + API + dashboard artifacts).

**Non-goal:** Replicate Cursor IDE tooling (debug tracepoints, Figma diff, React DevTools panel). Those stay in engineering workflows.

---

## 1. Three layers (what we must own)

| Layer | Customer-visible? | Own in Rehearsal? |
|-------|-------------------|-------------------|
| **A. Browser runtime** | Indirect (reliability of steps) | **Yes** — Playwright session, same engine family as MCP |
| **B. Observation** | **Yes** — scorecard, issues, evidence | **Yes** — screenshots, network, console, a11y counts, (→ vitals) |
| **C. Product pipeline** | **Yes** — readiness, diff, trends | **Yes** — already differentiated vs MCP |

MCP is a **superset for ad-hoc debugging**. Rehearsal must be a **complete superset for the rehearsal job**: repeatable config → crawl → journeys → personas → evidence → scorecard → monitor UI.

---

## 2. Capability matrix (MCP → Rehearsal)

Legend: ✅ shipped · 🟡 partial · 🔴 gap · ➖ not for customers

### 2.1 Navigation & interaction

| Capability | MCP | Rehearsal | Priority |
|------------|-----|-----------|----------|
| Navigate URL | ✅ | ✅ L1-BRW-04 | — |
| Click (role/name/ref) | ✅ ARIA refs | ✅ intent + `resolved_selector` on step | — |
| Fill inputs | ✅ | ✅ | — |
| Select `<select>` / combobox | ✅ | ✅ `select` action | — |
| Hover (menus, tooltips) | ✅ | ✅ `hover` action | — |
| Scroll into view | ✅ | ✅ `scroll` action | — |
| Keyboard (Enter, Esc) | ✅ | ✅ `press` action | — |
| Drag-and-drop | ✅ | 🔴 | **P3** — only if partner apps need it |
| Wait / network idle | ✅ | ✅ | — |
| assert URL contains | — | ✅ | — |
| open_link + fallback | — | ✅ L1-BRW-18 | — |
| Popup / dialog dismiss | ✅ agent ad hoc | 🔴 | **P2** — optional `dismiss` heuristic step |
| Multi-tab | ✅ | 🟡 open_link only | **P3** |

### 2.2 Discovery & crawl

| Capability | MCP | Rehearsal | Priority |
|------------|-----|-----------|----------|
| Explore page structure | ✅ ARIA/AX/HTML | 🟡 BFS link follow + metrics | — |
| Same-origin crawl map | 🟡 manual | ✅ L1-CRL-* | — |
| Hub / orphan / auth-gated | — | ✅ | — |
| Configurable path excludes | — | ✅ `exclude_path_prefixes` | — |
| Crawl + journey auto-seed | — | ✅ L1-WF-03/04 | — |
| Authenticated crawl | ✅ | 🟡 auth before crawl | **P1** — document + test |
| robots.txt respect | — | 🔴 | **P3** |

### 2.3 Observation (evidence)

| Capability | MCP | Rehearsal | Priority |
|------------|-----|-----------|----------|
| Full-page screenshot | ✅ | ✅ L1-BRW-07 | — |
| Page text excerpt | ✅ | ✅ L1-BRW-06 | — |
| Console errors | ✅ | ✅ L1-BRW-10 | — |
| Console warnings | ✅ | ✅ warn + error; P2 spike | — |
| HTTP failures (4xx+) | ✅ | ✅ L1-BRW-11 | — |
| Web Vitals (LCP, CLS, INP) | ✅ o11y | ✅ Performance agent v1 (lab) | — |
| Full HAR / request log | ✅ | 🟡 `network-log.json` (not full HAR) | **P3** — HAR export if partners need |
| ARIA/AX tree snapshot | ✅ | ✅ compact ARIA JSON on navigate/click/fill/select | — |
| Video recording | ✅ | 🔴 | **P3** |

### 2.4 Viewports & environments

| Capability | MCP | Rehearsal | Priority |
|------------|-----|-----------|----------|
| Resize viewport | ✅ | ✅ `run.viewports`: desktop / tablet / mobile | — |
| Resize window | ✅ | 🔴 | P2 |
| Per-step viewport in YAML | — | 🟡 `run.viewports` replays full journey per profile | P2 — per-step override |

### 2.5 Intelligence & agents

| Capability | MCP | Rehearsal | Priority |
|------------|-----|-----------|----------|
| Adaptive “what next?” | ✅ LLM in Cursor | 🔴 YAML-only execution | **P2** — optional `explore` mode; YAML stays canonical |
| Persona × journey matrix | — | ✅ L1-HEU-01 | — |
| 3 personas **execute** browser | — | 🟡 P1 runs browser; P2/P3 lens only | **P1** — honest UI label now; multi-exec later |
| LLM persona analysis | — | ✅ L1-LLM-* | — |
| Heuristics + readiness | — | ✅ | — |
| Run diff / trends | — | ✅ diff + trends API; compare **NLU-2** narrative on `/api/diff` | — |
| Job queue + run_id | — | ✅ | — |

### 2.6 Enterprise & safety

| Capability | MCP | Rehearsal | Priority |
|------------|-----|-----------|----------|
| SSRF preflight | — | ✅ L1-PRE-* | — |
| Secrets in env only | — | ✅ | — |
| Run budgets | — | ✅ | — |
| localhost opt-in | — | ✅ `allow_localhost` | — |
| HTTP stub / mock | ✅ stub_* | ➖ not customer | Engineering only |

### 2.7 Engineering-only (do not productize)

| MCP capability | In Rehearsal for customers? |
|----------------|----------------------------|
| Debug tracepoints / logpoints | ➖ No |
| React component ↔ DOM | ➖ No |
| Figma visual diff | ➖ No |
| Cursor `execute` batching | ➖ Internal pattern only |

---

## 3. What “better than MCP” means for customers

Rehearsal should beat ad-hoc MCP on:

1. **Repeatability** — same `rehearse.yaml`, comparable `run_id`, CI/GitHub Action.
2. **Audit trail** — scorecard + step artifacts + persona matrix without prompt drift.
3. **Crawl → journey synthesis** — automatic map and auto-journeys (MCP has no productized sitemap).
4. **Readiness narrative** — Green/Amber/Red, blockers, delights, compare runs, trends.
5. **Team surface** — dashboard, Init, Runner, export — not a chat transcript.

MCP remains faster for **one-off debugging** while building features; winning paths get **encoded in YAML**.

---

## 4. Implementation phases (build in Rehearsal)

### Phase A — Parity blockers (before next design-partner wave) — **shipped 2026-05-31**

| ID | Deliverable | Closes |
|----|-------------|--------|
| **BRW-A1** ✅ | Viewport profiles: `desktop` 1280×900, `tablet` 768×1024, `mobile` 390×844; `run.viewports` replays each journey per profile | MCP resize |
| **BRW-A2** ✅ | DSL: `hover`, `scroll`, `select` (+ docs in examples) | Menus, dropdowns, compare selects |
| **BRW-A3** ✅ | Intent resolution via `getByRole` / label / placeholder / combobox; `resolved_selector` on step note | MCP ref reliability |
| **BRW-A4** ✅ | Compact ARIA JSON artifact on navigate/click/fill/select steps | MCP a11y_take-aria-snapshot |
| **BRW-A5** ✅ | UI: matrix footnote on run detail — browser = P1; P2/P3 = evaluation lens | Honesty gap |
| **BRW-A6** ✅ | Init: `excludePathPrefixes` + viewport checkboxes on `POST /api/configs` | Per-product crawl control |

### Phase B — Observation depth — **shipped 2026-05-31**

| ID | Deliverable | Closes |
|----|-------------|--------|
| **BRW-B1** ✅ | Performance agent v1: lab Web Vitals on last navigate per journey; `web-vitals.json` artifact; P2 findings when over threshold | o11y_get-web-vitals |
| **BRW-B2** ✅ | `network-log.json` artifact (up to 500 requests per run) on `evidence.network_log_path` | HTTP inspection |
| **BRW-B3** ✅ | Console `warning` + `error`; per-step P2/P3 issues; run-level P2 spike for operator persona | Console o11y |
| **BRW-B4** ✅ | `press` action (`value` = key; optional `intent`/`selector` for focus) | Keyboard |

### Phase C — Smarter runner (still evidence-bound) — **shipped 2026-05-31 (v1)**

| ID | Deliverable | Closes |
|----|-------------|--------|
| **BRW-C1** ✅ | DSL `explore` — LLM proposes 1–3 actions per round from compact ARIA (`explore_max_rounds` budget) | Adaptive loop in product |
| **BRW-C2** ✅ | Init journey recorder — `POST /api/recordings/compile` → YAML fragment | MCP-free authoring assist |
| **BRW-C3** ✅ | `run.execute_all_personas_in_browser: true` replays journeys per persona | True matrix execution (3× cost) |
| **BRW-C4** ✅ | DSL `dismiss` — cookie/consent button heuristics + optional intent click | Flaky first paint |

---

## 5. Dogfood acceptance (Rehearsal tests Rehearsal)

Self-test on `http://127.0.0.1:8081` passes Phase A/B when:

- [x] Crawl ≤ ~15 shell routes (excludes `/runs/*`, `/api/*`)
- [x] Journeys cover Init dogfood + Runner page (no self-trigger loop on `j5`)
- [x] Mobile/tablet/desktop viewports complete with artifacts
- [x] Scorecard issues are **actionable** (job queue serialized; stale jobs marked on serve restart)
- [x] Compare run selectors covered by labeled combobox + NLU-2 “What changed” panel
- [x] Compare visual step diff with focus region overlays on screenshots (L2-UI-18 v1)

Use **Browser MCP in Cursor only** to validate new BRW-* features during development; partner-facing proof is always `rehearse run` + dashboard.

---

## 6. Authority order

1. `CEO_DECISIONS.md` — observe-only, no auto-fix  
2. `MONITORING_PLATFORM_SPEC.md` — product surface  
3. **This doc** — browser parity vs MCP  
4. `FEATURE_SCOPE.md` — sprint IDs (add BRW-* rows when scheduled)  
5. `AGENT_BRIEF.md` — demo flow  

---

*Customers buy launch rehearsal, not a browser IDE plugin.*
