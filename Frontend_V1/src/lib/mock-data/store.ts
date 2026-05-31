import type {
  AgentNode,
  AlertChannel,
  Annotation,
  BacklogItem,
  DimensionScore,
  Integration,
  Issue,
  Journey,
  MatrixCell,
  Persona,
  RunBundle,
  RunDiff,
  RunSummary,
  SitemapEdge,
  SitemapPage,
  StepSnapshot,
  SuggestedJourney,
  Workspace,
  WorkflowCoverage,
} from "./types";

// ─── Shared catalog ───────────────────────────────────────────────────────────

export const personas: Persona[] = [
  {
    id: "p1-evaluator",
    name: "Prospect Priya",
    role: "First-time visitor evaluating",
    goal: "Decide if it's worth a demo",
    patience: "low",
    stressFactors: ["unclear pricing", "signup friction"],
  },
  {
    id: "p2-operator",
    name: "Operator Owen",
    role: "Daily power user",
    goal: "Ship work without friction",
    patience: "medium",
    stressFactors: ["slow loads", "broken shortcuts"],
  },
  {
    id: "p3-admin",
    name: "Admin Ada",
    role: "Owns the workspace",
    goal: "Provision team & guardrails",
    patience: "high",
    stressFactors: ["role confusion", "audit gaps"],
  },
  {
    id: "p4-skeptic",
    name: "Skeptic Sam",
    role: "Security/compliance buyer",
    goal: "Find the deal-breaker",
    patience: "low",
    stressFactors: ["SSO gaps", "data residency"],
  },
];

export const journeys: Journey[] = [
  { id: "j1", name: "Land → Pricing → Signup", steps: 7, category: "pricing" },
  { id: "j2", name: "SSO login → First task", steps: 9, category: "auth" },
  { id: "j3", name: "Invite teammate + role", steps: 6, category: "admin" },
  { id: "j4", name: "Search docs → Code sample", steps: 5, category: "docs" },
  { id: "j5", name: "Dashboard → Drilldown", steps: 8, category: "dashboard" },
  { id: "j6", name: "Global search → Open record", steps: 4, category: "search" },
];

export const enterpriseJourneys: Journey[] = [
  { id: "j1-deep-link", name: "Deep link to primary surface", steps: 1, category: "dashboard" },
  { id: "j2-primary-list", name: "Browse primary data view", steps: 2, category: "dashboard" },
  { id: "j3-secondary-module", name: "Secondary module", steps: 1, category: "dashboard" },
  { id: "j4-search-surface", name: "Search or AI surface", steps: 1, category: "search" },
  { id: "j5-admin-boundary", name: "Admin boundary check", steps: 1, category: "admin" },
];

export const calJourneys: Journey[] = [
  { id: "j1-land", name: "Land on marketing home", steps: 1, category: "pricing" },
  { id: "j2-signup-path", name: "Signup path discovery", steps: 2, category: "auth" },
  { id: "j3-product-depth", name: "Product depth pages", steps: 2, category: "docs" },
  { id: "j4-pricing", name: "Pricing transparency", steps: 1, category: "pricing" },
  { id: "j5-return-nav", name: "Return navigation", steps: 2, category: "dashboard" },
];

const ALL_DIMENSIONS: DimensionScore[] = [
  { name: "Functionality", score: 78, signal: "17% steps pass", automated: true },
  { name: "UI/UX", score: 85, signal: "12 unlabeled buttons", automated: true },
  { name: "Information", score: 81, signal: "CTA copy mismatches", automated: true },
  { name: "Performance", score: 88, signal: "863ms avg step (Phase 2 agent)", automated: false },
  { name: "Accessibility", score: 72, signal: "ARIA gaps on forms", automated: false },
  { name: "Trust", score: 90, signal: "Security copy present", automated: false },
  { name: "Onboarding", score: 76, signal: "Empty states weak", automated: false },
  { name: "Recovery", score: 69, signal: "422 loses form state", automated: false },
];

// ─── Acme run (featured mock — full richness) ─────────────────────────────────

const ACME_ISSUES: Issue[] = [
  {
    id: "iss_001",
    runId: "run_8s7d2",
    severity: "P0",
    title: "SSO callback drops session on Safari 17",
    detail: "After IdP redirect, session cookie never set on Safari 17.",
    persona: "Operator Owen",
    personaId: "p2-operator",
    journey: "SSO login → First task",
    journeyId: "j2",
    stepId: "j2-p2-operator-s4",
    dimension: "Functionality",
    confidence: "high",
    owner: "backend",
    recurring: 3,
    evidence: "Network: 302 → / with no Set-Cookie. Repro 5/5.",
    severityReason: "Blocks all authenticated journeys for Safari users.",
    personaImpact: "Blocks P2 operator and P3 admin; P1 prospect unaffected until signup.",
    similarIssueIds: ["iss_008"],
    suggestion: "Verify Set-Cookie on SSO callback; add cross-browser E2E in CI.",
    screenshotPath: "mock/j2-s4.png",
  },
  {
    id: "iss_002",
    runId: "run_8s7d2",
    severity: "P1",
    title: "Pricing page CTA reads 'Get started' but goes to /demo",
    detail: "Primary CTA label promises signup but routes to demo booking.",
    persona: "Prospect Priya",
    personaId: "p1-evaluator",
    journey: "Land → Pricing → Signup",
    journeyId: "j1",
    stepId: "j1-p1-evaluator-s3",
    dimension: "Information",
    confidence: "high",
    owner: "content",
    recurring: 1,
    evidence: "Screenshot diff: copy mismatch with destination.",
    severityReason: "Misleading CTA erodes trust for evaluators.",
    personaImpact: "Primary blocker for P1 prospect journey.",
    suggestion: "Align CTA copy with destination or fix href.",
    screenshotPath: "mock/j1-s3.png",
  },
  {
    id: "iss_003",
    runId: "run_8s7d2",
    severity: "P1",
    title: "Invite flow loses unsaved role assignment on validation error",
    detail: "Role select resets after 422 from API.",
    persona: "Admin Ada",
    personaId: "p3-admin",
    journey: "Invite teammate + role",
    journeyId: "j3",
    stepId: "j3-p3-admin-s5",
    dimension: "Functionality",
    confidence: "high",
    owner: "frontend",
    recurring: 2,
    evidence: "ARIA: select reverts to default after 422 response.",
    severityReason: "Admin provisioning friction.",
    personaImpact: "Blocks P3 admin invite journey.",
    suggestion: "Preserve form state on validation errors.",
    screenshotPath: "mock/j3-s5.png",
  },
  {
    id: "iss_004",
    runId: "run_8s7d2",
    severity: "P2",
    title: "Empty state for /reports has no primary action",
    detail: "Reports empty state is illustration-only.",
    persona: "Operator Owen",
    personaId: "p2-operator",
    journey: "Dashboard → Drilldown",
    journeyId: "j5",
    stepId: "j5-p2-operator-s2",
    dimension: "UI/UX",
    confidence: "high",
    owner: "frontend",
    recurring: 4,
    evidence: "Step screenshot — viewport only contains illustration.",
    suggestion: "Add CTA to create first report.",
    screenshotPath: "mock/j5-s2.png",
  },
  {
    id: "iss_005",
    runId: "run_8s7d2",
    severity: "P2",
    title: "Docs search returns 0 results for 'webhook signature'",
    detail: "Search index missing common integration terms.",
    persona: "Operator Owen",
    personaId: "p2-operator",
    journey: "Search docs → Code sample",
    journeyId: "j4",
    stepId: "j4-p2-operator-s2",
    dimension: "Information",
    confidence: "high",
    owner: "content",
    recurring: 2,
    evidence: "Search response payload — 0 hits.",
    suggestion: "Index webhook docs; add synonyms.",
    screenshotPath: "mock/j4-s2.png",
  },
  {
    id: "iss_006",
    runId: "run_8s7d2",
    severity: "P2",
    title: "Console error: ResizeObserver loop limit",
    detail: "Non-fatal console noise on dashboard drilldown.",
    persona: "Operator Owen",
    personaId: "p2-operator",
    journey: "Dashboard → Drilldown",
    journeyId: "j5",
    stepId: "j5-p2-operator-s6",
    dimension: "Functionality",
    confidence: "hypothesis",
    owner: "frontend",
    recurring: 1,
    evidence: "Console log — non-fatal, but noisy.",
    suggestion: "Debounce chart resize handler.",
    screenshotPath: "mock/j5-s6.png",
  },
  {
    id: "iss_007",
    runId: "run_8s7d2",
    severity: "P3",
    title: "Footer year still reads 2024",
    detail: "Stale copyright year on marketing pages.",
    persona: "Prospect Priya",
    personaId: "p1-evaluator",
    journey: "Land → Pricing → Signup",
    journeyId: "j1",
    stepId: "j1-p1-evaluator-s1",
    dimension: "Information",
    confidence: "high",
    owner: "content",
    recurring: 6,
    evidence: "OCR text snapshot.",
    suggestion: "Update footer template.",
    screenshotPath: "mock/j1-s1.png",
  },
  {
    id: "iss_008",
    runId: "run_8s7d2",
    severity: "P1",
    title: "Password reset link expires before email delivery on staging",
    detail: "TTL shorter than average email latency on staging.",
    persona: "Skeptic Sam",
    personaId: "p4-skeptic",
    journey: "SSO login → First task",
    journeyId: "j2",
    stepId: "j2-p4-skeptic-s2",
    dimension: "Functionality",
    confidence: "hypothesis",
    owner: "backend",
    recurring: 2,
    evidence: "Timing: 47s avg deliver vs 30s TTL.",
    suggestion: "Extend staging TTL or async token invalidation.",
    screenshotPath: "mock/j2-s2.png",
  },
];

const ACME_DELIGHTS = [
  {
    id: "del_1",
    runId: "run_8s7d2",
    title: "Pricing page has live calculator",
    quote: "I knew the seat price for my team in under 10 seconds — rare.",
    persona: "Prospect Priya",
    journey: "Land → Pricing → Signup",
    stepId: "j1-p1-evaluator-s2",
    marketingReady: true,
  },
  {
    id: "del_2",
    runId: "run_8s7d2",
    title: "Keyboard-first command palette",
    quote: "Cmd-K worked on every screen I tried. Felt native.",
    persona: "Operator Owen",
    journey: "Dashboard → Drilldown",
    stepId: "j5-p2-operator-s4",
    marketingReady: true,
  },
  {
    id: "del_3",
    runId: "run_8s7d2",
    title: "Role permissions diff before save",
    quote: "It showed me exactly what would change — I trusted the button.",
    persona: "Admin Ada",
    journey: "Invite teammate + role",
    stepId: "j3-p3-admin-s4",
    marketingReady: true,
  },
  {
    id: "del_4",
    runId: "run_8s7d2",
    title: "Docs code samples copy as runnable cURL",
    quote: "The token placeholder was even pre-filled from my session.",
    persona: "Operator Owen",
    journey: "Search docs → Code sample",
    stepId: "j4-p2-operator-s4",
    marketingReady: true,
    regressionRisk: false,
  },
];

const ACME_AGENTS: AgentNode[] = [
  {
    id: "ag_crawl",
    runId: "run_8s7d2",
    name: "Crawler",
    role: "Site structure, sitemap, orphans",
    phase: "crawl",
    status: "done",
    durationSec: 84,
    costUsd: 0.12,
    lastSummary: "137 pages, 4 orphans, 12 auth-gated.",
    handoff: { pages: 137, orphans: 4, authGated: 12 },
  },
  {
    id: "ag_wf",
    runId: "run_8s7d2",
    name: "Workflow",
    role: "Pattern detection, journey supplementation",
    phase: "workflow",
    status: "done",
    durationSec: 47,
    costUsd: 0.08,
    lastSummary: "Detected 6 workflows, suggested 2 new journeys.",
    handoff: { workflows: 6, suggested: 2 },
  },
  {
    id: "ag_journey",
    runId: "run_8s7d2",
    name: "Journey runner",
    role: "Browser E2E execution",
    phase: "journey",
    status: "done",
    durationSec: 318,
    costUsd: 0.41,
    lastSummary: "6 journeys, 39 steps, 2 flaky.",
    handoff: { steps: 39, flaky: 2 },
  },
  {
    id: "ag_p1",
    runId: "run_8s7d2",
    name: "Persona — Prospect Priya",
    role: "Re-grade from prospect lens",
    phase: "persona",
    status: "done",
    durationSec: 62,
    costUsd: 0.31,
    lastSummary: "2 blockers, 1 delight. Bounced at pricing CTA mismatch.",
    findingsCount: 2,
    delightsCount: 1,
  },
  {
    id: "ag_p2",
    runId: "run_8s7d2",
    name: "Persona — Operator Owen",
    role: "Re-grade from operator lens",
    phase: "persona",
    status: "done",
    durationSec: 71,
    costUsd: 0.34,
    lastSummary: "3 issues, 2 delights. Loved Cmd-K.",
    findingsCount: 3,
    delightsCount: 2,
  },
  {
    id: "ag_p3",
    runId: "run_8s7d2",
    name: "Persona — Admin Ada",
    role: "Re-grade from admin lens",
    phase: "persona",
    status: "done",
    durationSec: 58,
    costUsd: 0.29,
    lastSummary: "1 P1, 1 delight. Invite UX strong overall.",
    findingsCount: 1,
    delightsCount: 1,
  },
  {
    id: "ag_llm_p1",
    runId: "run_8s7d2",
    name: "LLM — Prospect Priya",
    role: "Natural-language evaluator (NVIDIA NIM)",
    phase: "persona",
    status: "done",
    durationSec: 18,
    costUsd: 0.09,
    lastSummary: "Confirmed CTA mismatch; added onboarding copy note.",
    findingsCount: 2,
    delightsCount: 1,
  },
  {
    id: "ag_synth",
    runId: "run_8s7d2",
    name: "Synthesizer",
    role: "Dedupe, prioritize, readiness rollup",
    phase: "synthesis",
    status: "done",
    durationSec: 22,
    costUsd: 0.18,
    lastSummary: "Merged 23 raw findings → 8 issues. Readiness 82.",
    handoff: { rawFindings: 23, mergedIssues: 8 },
  },
  {
    id: "ag_compl",
    runId: "run_8s7d2",
    name: "Compliance",
    role: "PII, auth boundary signals",
    phase: "compliance",
    status: "idle",
    durationSec: 0,
    costUsd: 0,
    lastSummary: "Not enabled for this run.",
  },
  {
    id: "ag_perf",
    runId: "run_8s7d2",
    name: "Performance",
    role: "Latency, Web Vitals",
    phase: "performance",
    status: "idle",
    durationSec: 0,
    costUsd: 0,
    lastSummary: "Not enabled for this run.",
  },
];

const ACME_PAGES: SitemapPage[] = [
  { id: "pg_1", path: "/", title: "Home", type: "hub", errors: 0, linksFrom: [] },
  {
    id: "pg_2",
    path: "/pricing",
    title: "Pricing",
    type: "hub",
    workflow: "pricing",
    errors: 0,
    linksFrom: ["pg_1"],
  },
  {
    id: "pg_3",
    path: "/signup",
    title: "Sign up",
    type: "leaf",
    workflow: "auth",
    errors: 0,
    linksFrom: ["pg_2"],
  },
  {
    id: "pg_4",
    path: "/login",
    title: "Log in",
    type: "leaf",
    workflow: "auth",
    errors: 0,
    linksFrom: ["pg_1"],
  },
  {
    id: "pg_5",
    path: "/app",
    title: "Dashboard",
    type: "hub",
    workflow: "dashboard",
    errors: 0,
    linksFrom: ["pg_1"],
  },
  {
    id: "pg_6",
    path: "/app/reports",
    title: "Reports",
    type: "leaf",
    workflow: "dashboard",
    errors: 1,
    linksFrom: ["pg_5"],
  },
  {
    id: "pg_7",
    path: "/app/settings/team",
    title: "Team",
    type: "leaf",
    workflow: "admin",
    errors: 0,
    linksFrom: ["pg_5"],
  },
  {
    id: "pg_8",
    path: "/docs",
    title: "Docs",
    type: "hub",
    workflow: "docs",
    errors: 0,
    linksFrom: ["pg_1"],
  },
  {
    id: "pg_9",
    path: "/docs/webhooks",
    title: "Webhooks",
    type: "leaf",
    workflow: "docs",
    errors: 0,
    linksFrom: ["pg_8"],
  },
  {
    id: "pg_10",
    path: "/changelog/old-q3",
    title: "Old changelog",
    type: "orphan",
    errors: 0,
    linksFrom: [],
  },
  {
    id: "pg_11",
    path: "/app/internal/flags",
    title: "Feature flags",
    type: "auth",
    workflow: "admin",
    errors: 0,
    linksFrom: ["pg_7"],
  },
];

const ACME_EDGES: SitemapEdge[] = [
  { from: "pg_1", to: "pg_2" },
  { from: "pg_1", to: "pg_5" },
  { from: "pg_1", to: "pg_8" },
  { from: "pg_2", to: "pg_3" },
  { from: "pg_5", to: "pg_6" },
  { from: "pg_5", to: "pg_7" },
  { from: "pg_8", to: "pg_9" },
  { from: "pg_1", to: "pg_4" },
  { from: "pg_7", to: "pg_11" },
];

function buildAcmeMatrix(): MatrixCell[] {
  const cells: MatrixCell[] = [];
  personas.forEach((p) => {
    journeys.forEach((j) => {
      const seed = (personas.indexOf(p) * 7 + journeys.indexOf(j) * 13) % 11;
      const grade = seed < 1 ? "fail" : seed < 4 ? "partial" : "pass";
      cells.push({ personaId: p.id, journeyId: j.id, grade });
    });
  });
  return cells;
}

function buildAcmeSteps(): StepSnapshot[] {
  return [
    {
      stepId: "j1-p1-evaluator-s1",
      journeyId: "j1",
      journeyName: "Land → Pricing → Signup",
      personaId: "p1-evaluator",
      action: "navigate",
      requestedUrl: "https://app.acme.io/",
      finalUrl: "https://app.acme.io/",
      outcome: "pass",
      durationMs: 820,
    },
    {
      stepId: "j1-p1-evaluator-s3",
      journeyId: "j1",
      journeyName: "Land → Pricing → Signup",
      personaId: "p1-evaluator",
      action: "click",
      requestedUrl: "https://app.acme.io/pricing",
      finalUrl: "https://app.acme.io/demo",
      outcome: "partial",
      durationMs: 1100,
      note: "CTA destination mismatch",
    },
    {
      stepId: "j2-p2-operator-s4",
      journeyId: "j2",
      journeyName: "SSO login → First task",
      personaId: "p2-operator",
      action: "navigate",
      requestedUrl: "https://app.acme.io/auth/callback",
      finalUrl: "https://app.acme.io/",
      outcome: "fail",
      durationMs: 2400,
      note: "No session cookie",
    },
    {
      stepId: "j5-p2-operator-s6",
      journeyId: "j5",
      journeyName: "Dashboard → Drilldown",
      personaId: "p2-operator",
      action: "wait",
      requestedUrl: null,
      finalUrl: "https://app.acme.io/app/reports/1",
      outcome: "partial",
      durationMs: 900,
      consoleErrors: ["ResizeObserver loop limit exceeded"],
      flaky: true,
    },
  ];
}

const acmeBundle: RunBundle = {
  summary: {
    id: "run_8s7d2",
    productName: "Acme SaaS",
    target: "app.acme.io",
    targetUrl: "https://app.acme.io",
    env: "prod-canary",
    workspaceId: "ws_acme",
    startedAt: "2026-05-29T14:02:00Z",
    finishedAt: "2026-05-29T14:12:42Z",
    durationSec: 642,
    readiness: 82,
    readinessBand: "Red",
    status: "danger",
    blockers: 4,
    issues: 8,
    delights: 4,
    pages: 137,
    stepCount: 39,
    agentCost: 1.84,
    outcome: "complete",
    configHash: "7f2a91",
    authAttempted: false,
    llmEnabled: true,
    crawlEnabled: true,
    orphans: 4,
    authGated: 12,
  },
  steps: buildAcmeSteps(),
  issues: ACME_ISSUES,
  delights: ACME_DELIGHTS,
  agents: ACME_AGENTS,
  matrix: buildAcmeMatrix(),
  dimensions: ALL_DIMENSIONS,
  scorecardMd: `# Launch Rehearsal — Scorecard\n\n| Field | Value |\n|-------|--------|\n| **Run ID** | \`run_8s7d2\` |\n| **Readiness** | **Red** (P0 present) |\n| **Issues** | 8 |\n| **Delights** | 4 |\n\n---\n\n## Executive summary\n\nFull scorecard rendered from multi-agent pipeline. See Issues and Delights tabs for structured view.`,
  sitemapMd: `# Site map — run_8s7d2\n\n137 pages crawled · 4 orphans · 12 auth-gated\n\n| Path | Type | Workflow |\n|------|------|----------|\n| / | hub | — |\n| /pricing | hub | pricing |\n| /app/reports | leaf | dashboard |`,
  sitemapPages: ACME_PAGES,
  sitemapEdges: ACME_EDGES,
  screenshots: ACME_ISSUES.filter((i) => i.screenshotPath).map((i) => ({
    path: i.screenshotPath!,
    stepId: i.stepId,
    label: i.title,
  })),
  annotations: [
    {
      id: "ann_1",
      runId: "run_8s7d2",
      targetType: "issue",
      targetId: "iss_001",
      action: "agreed",
      author: "danielle@acme.io",
      at: "2026-05-29T15:00:00Z",
    },
    {
      id: "ann_2",
      runId: "run_8s7d2",
      targetType: "issue",
      targetId: "iss_006",
      action: "false positive",
      author: "rob@acme.io",
      note: "Known chart lib noise",
      at: "2026-05-29T15:30:00Z",
    },
    {
      id: "ann_3",
      runId: "run_8s7d2",
      targetType: "delight",
      targetId: "del_2",
      action: "pinned",
      author: "danielle@acme.io",
      at: "2026-05-29T16:00:00Z",
    },
  ],
};

// ─── Enterprise / Argyle run (backend-shaped) ─────────────────────────────────

const enterpriseIssues: Issue[] = [
  {
    id: "ent_001",
    runId: "enterprise-20260530-045757",
    severity: "P0",
    title: "Auth wall on deep link",
    detail: "All journeys redirect to /login without session.",
    persona: "Prospect Priya",
    personaId: "p1-evaluator",
    journey: "Deep link to primary surface",
    journeyId: "j1-deep-link",
    stepId: "j1-deep-link-p1-evaluator-s1",
    dimension: "Functionality",
    confidence: "high",
    owner: "backend",
    recurring: 3,
    evidence: "final_url=/login after navigate to /database. auth_outcome=failed_still_on_login.",
    severityReason: "Blocks every journey — no authenticated surface reached.",
    personaImpact: "All personas blocked at login.",
    suggestion: "Set REHEARSE_EMAIL/PASSWORD or fix auth flow.",
    screenshotPath: "mock/enterprise-j1.png",
  },
  {
    id: "ent_002",
    runId: "enterprise-20260530-045757",
    severity: "P1",
    title: "Login form has unlabeled buttons",
    detail: "2 buttons lack accessible names.",
    persona: "Admin Ada",
    personaId: "p3-admin",
    journey: "Browse primary data view",
    journeyId: "j2-primary-list",
    stepId: "j2-primary-list-p1-evaluator-s1",
    dimension: "Accessibility",
    confidence: "high",
    owner: "frontend",
    recurring: 2,
    evidence: "unlabeled_button_count: 2 on login page.",
    suggestion: "Add aria-label to icon buttons.",
    screenshotPath: "mock/enterprise-login.png",
  },
  {
    id: "ent_003",
    runId: "enterprise-20260530-045757",
    severity: "P2",
    title: "Deep link does not preserve return URL",
    detail: "After login user lands on default route not /database.",
    persona: "Operator Owen",
    personaId: "p2-operator",
    journey: "Deep link to primary surface",
    journeyId: "j1-deep-link",
    stepId: "j1-deep-link-p1-evaluator-s1",
    dimension: "Functionality",
    confidence: "hypothesis",
    owner: "frontend",
    recurring: 1,
    evidence: "Requested /database, stuck on /login.",
    suggestion: "Add ?next= query preservation.",
    screenshotPath: "mock/enterprise-j1.png",
  },
];

const enterpriseSteps: StepSnapshot[] = [
  {
    stepId: "j1-deep-link-p1-evaluator-s1",
    journeyId: "j1-deep-link",
    journeyName: "Deep link to primary surface",
    personaId: "p1-evaluator",
    action: "navigate",
    requestedUrl: "https://faculty-dashboard-eight.vercel.app/database",
    finalUrl: "https://faculty-dashboard-eight.vercel.app/login",
    outcome: "partial",
    durationMs: 689,
  },
  {
    stepId: "j2-primary-list-p1-evaluator-s1",
    journeyId: "j2-primary-list",
    journeyName: "Browse primary data view",
    personaId: "p1-evaluator",
    action: "navigate",
    requestedUrl: "https://faculty-dashboard-eight.vercel.app/database",
    finalUrl: "https://faculty-dashboard-eight.vercel.app/login",
    outcome: "partial",
    durationMs: 614,
  },
  {
    stepId: "j2-primary-list-p1-evaluator-s2",
    journeyId: "j2-primary-list",
    journeyName: "Browse primary data view",
    personaId: "p1-evaluator",
    action: "wait",
    requestedUrl: null,
    finalUrl: "https://faculty-dashboard-eight.vercel.app/login",
    outcome: "pass",
    durationMs: 2038,
  },
  {
    stepId: "j5-admin-boundary-p1-evaluator-s1",
    journeyId: "j5-admin-boundary",
    journeyName: "Admin boundary check",
    personaId: "p1-evaluator",
    action: "navigate",
    requestedUrl: "https://faculty-dashboard-eight.vercel.app/admin",
    finalUrl: "https://faculty-dashboard-eight.vercel.app/login",
    outcome: "partial",
    durationMs: 520,
  },
];

function buildEnterpriseMatrix(): MatrixCell[] {
  return enterpriseJourneys.flatMap((j) =>
    personas.slice(0, 3).map((p) => ({ personaId: p.id, journeyId: j.id, grade: "fail" as const })),
  );
}

const enterpriseBundle: RunBundle = {
  summary: {
    id: "enterprise-20260530-045757",
    productName: "Enterprise Dashboard (example)",
    target: "faculty-dashboard-eight.vercel.app",
    targetUrl: "https://faculty-dashboard-eight.vercel.app",
    env: "staging",
    workspaceId: "ws_acme",
    startedAt: "2026-05-30T04:57:57Z",
    finishedAt: "2026-05-30T05:02:37Z",
    durationSec: 279,
    readiness: 34,
    readinessBand: "Red",
    status: "danger",
    blockers: 2,
    issues: 9,
    delights: 0,
    pages: 0,
    stepCount: 6,
    agentCost: 0.92,
    outcome: "complete",
    configHash: "a3c91e",
    authAttempted: true,
    authOutcome: "failed_still_on_login",
    llmEnabled: true,
    crawlEnabled: false,
  },
  steps: enterpriseSteps,
  issues: enterpriseIssues,
  delights: [],
  agents: [
    {
      id: "journey-runner",
      runId: "enterprise-20260530-045757",
      name: "Journey runner",
      role: "E2E journey execution",
      phase: "journey",
      status: "done",
      durationSec: 45,
      costUsd: 0.12,
      lastSummary: "Executed 6 steps across 5 journeys (0 hard failures)",
    },
    {
      id: "persona-p1",
      runId: "enterprise-20260530-045757",
      name: "Persona — First-time evaluator",
      role: "Prospect / new user lens",
      phase: "persona",
      status: "done",
      durationSec: 12,
      costUsd: 0.08,
      lastSummary: "Auth wall blocks all paths",
    },
    {
      id: "llm-p1",
      runId: "enterprise-20260530-045757",
      name: "LLM — First-time evaluator",
      role: "NVIDIA NIM deep analysis",
      phase: "persona",
      status: "done",
      durationSec: 14,
      costUsd: 0.11,
      lastSummary: "All journeys land on login with unlabeled buttons",
    },
    {
      id: "synthesizer",
      runId: "enterprise-20260530-045757",
      name: "Synthesizer",
      role: "Cross-agent synthesis",
      phase: "synthesis",
      status: "done",
      durationSec: 8,
      costUsd: 0.06,
      lastSummary: "Synthesized 9 issues, 0 delights from 7 agent reports",
    },
  ],
  matrix: buildEnterpriseMatrix(),
  dimensions: ALL_DIMENSIONS.map((d) => ({
    ...d,
    score: d.name === "Functionality" ? 22 : d.name === "UI/UX" ? 35 : Math.max(20, d.score - 40),
  })),
  scorecardMd: `# Launch Rehearsal — Scorecard\n\n| **Run ID** | \`enterprise-20260530-045757\` |\n| **Readiness** | **Red** |\n| **Auth** | failed_still_on_login |\n| **Issues** | 9 |\n| **Delights** | 0 |`,
  sitemapMd: "No sitemap — crawl disabled for this run.",
  sitemapPages: [
    { id: "pg_login", path: "/login", title: "Login", type: "auth", workflow: "auth", errors: 0 },
  ],
  sitemapEdges: [],
  screenshots: enterpriseSteps.map((s) => ({
    path: `mock/${s.stepId}.png`,
    stepId: s.stepId,
    label: s.journeyName,
  })),
  annotations: [],
};

// ─── Cal.com run (crawl enabled) ──────────────────────────────────────────────

const calBundle: RunBundle = {
  summary: {
    id: "cal-20260529-193724",
    productName: "Cal.com (Phase 0)",
    target: "cal.com",
    targetUrl: "https://cal.com",
    env: "demo",
    workspaceId: "ws_acme",
    startedAt: "2026-05-29T19:37:24Z",
    finishedAt: "2026-05-29T19:45:10Z",
    durationSec: 466,
    readiness: 71,
    readinessBand: "Amber",
    status: "warn",
    blockers: 2,
    issues: 5,
    delights: 3,
    pages: 48,
    stepCount: 14,
    agentCost: 1.12,
    outcome: "complete",
    configHash: "c4e82b",
    llmEnabled: false,
    crawlEnabled: true,
    orphans: 2,
    authGated: 3,
  },
  steps: [
    {
      stepId: "j1-land-p1-evaluator-s1",
      journeyId: "j1-land",
      journeyName: "Land on marketing home",
      personaId: "p1-evaluator",
      action: "navigate",
      requestedUrl: "https://cal.com",
      finalUrl: "https://cal.com",
      outcome: "pass",
      durationMs: 1200,
    },
    {
      stepId: "j4-pricing-p1-evaluator-s1",
      journeyId: "j4-pricing",
      journeyName: "Pricing transparency",
      personaId: "p1-evaluator",
      action: "navigate",
      requestedUrl: "https://cal.com/pricing",
      finalUrl: "https://cal.com/pricing",
      outcome: "pass",
      durationMs: 980,
    },
  ],
  issues: [
    {
      id: "cal_001",
      runId: "cal-20260529-193724",
      severity: "P1",
      title: "Signup CTA buried below fold on mobile",
      detail: "Primary signup not visible at 375px width.",
      persona: "Prospect Priya",
      personaId: "p1-evaluator",
      journey: "Land on marketing home",
      journeyId: "j1-land",
      stepId: "j1-land-p1-evaluator-s1",
      dimension: "UI/UX",
      confidence: "high",
      owner: "frontend",
      recurring: 1,
      evidence: "Screenshot at 375×812 — CTA below fold.",
      suggestion: "Sticky mobile CTA on marketing pages.",
    },
    {
      id: "cal_002",
      runId: "cal-20260529-193724",
      severity: "P2",
      title: "Docs search latency > 3s",
      detail: "Search debounce + network slow on docs.",
      persona: "Operator Owen",
      personaId: "p2-operator",
      journey: "Product depth pages",
      journeyId: "j3-product-depth",
      stepId: "j3-product-depth-p1-evaluator-s1",
      dimension: "Performance",
      confidence: "hypothesis",
      owner: "backend",
      recurring: 1,
      evidence: "Step duration 3200ms on search submit.",
    },
  ],
  delights: [
    {
      id: "cal_d1",
      runId: "cal-20260529-193724",
      title: "Open-source positioning clear above fold",
      quote: "I immediately knew this was OSS-friendly — rare for scheduling tools.",
      persona: "Prospect Priya",
      journey: "Land on marketing home",
      marketingReady: true,
    },
    {
      id: "cal_d2",
      runId: "cal-20260529-193724",
      title: "Pricing tiers easy to compare",
      quote: "Three columns, no hidden enterprise-only footnote.",
      persona: "Skeptic Sam",
      journey: "Pricing transparency",
      marketingReady: true,
    },
  ],
  agents: ACME_AGENTS.slice(0, 7).map((a) => ({
    ...a,
    runId: "cal-20260529-193724",
    lastSummary: a.lastSummary.replace("137", "48").replace("6 workflows", "4 workflows"),
  })),
  matrix: buildAcmeMatrix().slice(0, 15),
  dimensions: ALL_DIMENSIONS.map((d) => ({ ...d, score: Math.min(95, d.score + 5) })),
  scorecardMd: `# Launch Rehearsal — Scorecard\n\n| **Run ID** | \`cal-20260529-193724\` |\n| **Target** | https://cal.com |\n| **Readiness** | **Amber** |\n| **Pages crawled** | 48 |`,
  sitemapMd: `# Site map — cal-20260529-193724\n\n48 pages · 2 orphans · 3 auth-gated`,
  sitemapPages: ACME_PAGES.slice(0, 6).map((p) => ({ ...p, path: p.path.replace("/app", "/org") })),
  sitemapEdges: ACME_EDGES.slice(0, 5),
  screenshots: [
    { path: "mock/cal-land.png", stepId: "j1-land-p1-evaluator-s1", label: "Marketing home" },
  ],
  annotations: [],
};

// ─── Additional historical runs (summaries only) ─────────────────────────────

const historicalSummaries: RunSummary[] = [
  {
    id: "run_8s6q1",
    productName: "Acme SaaS",
    target: "app.acme.io",
    targetUrl: "https://app.acme.io",
    env: "staging",
    workspaceId: "ws_acme",
    startedAt: "2026-05-29T08:11:00Z",
    finishedAt: "2026-05-29T08:22:41Z",
    durationSec: 701,
    readiness: 74,
    readinessBand: "Amber",
    status: "warn",
    blockers: 3,
    issues: 7,
    delights: 3,
    pages: 141,
    stepCount: 39,
    agentCost: 1.92,
    outcome: "complete",
    configHash: "7f2a90",
    crawlEnabled: true,
    llmEnabled: true,
  },
  {
    id: "run_8s5l9",
    productName: "Acme SaaS",
    target: "app.acme.io",
    targetUrl: "https://app.acme.io",
    env: "prod-canary",
    workspaceId: "ws_acme",
    startedAt: "2026-05-28T19:33:00Z",
    finishedAt: "2026-05-28T19:43:12Z",
    durationSec: 612,
    readiness: 79,
    readinessBand: "Amber",
    status: "warn",
    blockers: 2,
    issues: 6,
    delights: 5,
    pages: 136,
    stepCount: 39,
    agentCost: 1.71,
    outcome: "complete",
    configHash: "7f2a8f",
    crawlEnabled: true,
  },
  {
    id: "run_8s1k4",
    productName: "Acme SaaS",
    target: "app.acme.io",
    targetUrl: "https://app.acme.io",
    env: "staging",
    workspaceId: "ws_acme",
    startedAt: "2026-05-26T16:08:00Z",
    finishedAt: "2026-05-26T16:17:59Z",
    durationSec: 591,
    readiness: 84,
    readinessBand: "Green",
    status: "ready",
    blockers: 0,
    issues: 3,
    delights: 6,
    pages: 129,
    stepCount: 39,
    agentCost: 1.62,
    outcome: "complete",
    configHash: "7f2a8a",
    crawlEnabled: true,
  },
  {
    id: "enterprise-20260529-213552",
    productName: "Enterprise Dashboard (example)",
    target: "faculty-dashboard-eight.vercel.app",
    targetUrl: "https://faculty-dashboard-eight.vercel.app",
    env: "staging",
    workspaceId: "ws_acme",
    startedAt: "2026-05-29T21:35:52Z",
    finishedAt: "2026-05-29T21:37:09Z",
    durationSec: 77,
    readiness: 28,
    readinessBand: "Red",
    status: "danger",
    blockers: 2,
    issues: 9,
    delights: 0,
    pages: 0,
    stepCount: 6,
    agentCost: 0.88,
    outcome: "complete",
    configHash: "a3c91d",
    authAttempted: true,
    authOutcome: "failed_still_on_login",
    llmEnabled: true,
    crawlEnabled: false,
  },
];

// Clone enterprise bundle for earlier run id
const enterprise213552: RunBundle = {
  ...enterpriseBundle,
  summary: historicalSummaries.find((r) => r.id === "enterprise-20260529-213552")!,
  issues: enterpriseIssues.map((i) => ({
    ...i,
    runId: "enterprise-20260529-213552",
    id: i.id.replace("ent_", "ent213_"),
  })),
};

// ─── Registry ─────────────────────────────────────────────────────────────────

const FULL_BUNDLES: Record<string, RunBundle> = {
  run_8s7d2: acmeBundle,
  "enterprise-20260530-045757": enterpriseBundle,
  "enterprise-20260529-213552": enterprise213552,
  "cal-20260529-193724": calBundle,
};

function summaryFromBundle(b: RunBundle): RunSummary {
  return b.summary;
}

function cloneAcmeForSummary(s: RunSummary): RunBundle {
  return {
    ...acmeBundle,
    summary: s,
    issues: acmeBundle.issues.map((i) => ({ ...i, runId: s.id, id: `${s.id}_${i.id}` })),
    delights: acmeBundle.delights.map((d) => ({ ...d, runId: s.id, id: `${s.id}_${d.id}` })),
    agents: acmeBundle.agents.map((a) => ({ ...a, runId: s.id })),
    annotations: [],
  };
}

export const runSummaries: RunSummary[] = [
  acmeBundle.summary,
  enterpriseBundle.summary,
  calBundle.summary,
  ...historicalSummaries.filter((s) => s.id !== "enterprise-20260529-213552"),
];

export function getRunBundle(runId: string): RunBundle | undefined {
  if (FULL_BUNDLES[runId]) return FULL_BUNDLES[runId];
  const summary = runSummaries.find((r) => r.id === runId);
  if (!summary) return undefined;
  return cloneAcmeForSummary(summary);
}

export function getLatestRun(): RunSummary {
  return runSummaries[0];
}

export function diffRuns(runA: string, runB: string): RunDiff | null {
  const a = getRunBundle(runA);
  const b = getRunBundle(runB);
  if (!a || !b) return null;
  const stepsA = new Map(a.steps.map((s) => [s.stepId, s]));
  const stepsB = new Map(b.steps.map((s) => [s.stepId, s]));
  const changedSteps = [...stepsA.keys()]
    .filter((id) => stepsB.has(id))
    .filter((id) => stepsA.get(id)!.outcome !== stepsB.get(id)!.outcome)
    .map((stepId) => ({
      stepId,
      outcomeA: stepsA.get(stepId)!.outcome,
      outcomeB: stepsB.get(stepId)!.outcome,
      urlA: stepsA.get(stepId)!.finalUrl ?? undefined,
      urlB: stepsB.get(stepId)!.finalUrl ?? undefined,
    }));
  const pagesA = new Set(a.sitemapPages.map((p) => p.path));
  const pagesB = new Set(b.sitemapPages.map((p) => p.path));
  return {
    runA,
    runB,
    readinessA: a.summary.readinessBand,
    readinessB: b.summary.readinessBand,
    issuesA: a.summary.issues,
    issuesB: b.summary.issues,
    pagesA: a.summary.pages,
    pagesB: b.summary.pages,
    newPages: [...pagesB].filter((p) => !pagesA.has(p)),
    removedPages: [...pagesA].filter((p) => !pagesB.has(p)),
    changedSteps,
    stepsOnlyInA: [...stepsA.keys()].filter((k) => !stepsB.has(k)),
    stepsOnlyInB: [...stepsB.keys()].filter((k) => !stepsA.has(k)),
    resolvedIssues: ["Footer year still reads 2024"],
    newIssues: ["SSO callback drops session on Safari 17"],
  };
}

// ─── Workspace & platform config ──────────────────────────────────────────────

export const workspace: Workspace = {
  id: "ws_acme",
  name: "Acme Inc.",
  slug: "acme",
  targetUrl: "https://app.acme.io",
  members: 4,
  products: 2,
  configVersion: "v14",
  configHash: "7f2a91",
  gitUrl: "github.com/acme/rehearse-config",
  strictEnterpriseMode: true,
  retentionDays: 90,
  piiRedaction: false,
};

export const workflowCoverage: WorkflowCoverage[] = [
  {
    category: "auth",
    coverage: 100,
    journeys: 2,
    suggested: 0,
    paths: ["/login", "/signup", "/auth/callback"],
  },
  { category: "pricing", coverage: 100, journeys: 1, suggested: 0, paths: ["/pricing"] },
  {
    category: "admin",
    coverage: 75,
    journeys: 1,
    suggested: 1,
    paths: ["/app/settings/team", "/billing/seats"],
  },
  {
    category: "search",
    coverage: 60,
    journeys: 1,
    suggested: 1,
    paths: ["/search", "/docs/search"],
  },
  {
    category: "docs",
    coverage: 100,
    journeys: 1,
    suggested: 0,
    paths: ["/docs", "/docs/webhooks"],
  },
  {
    category: "dashboard",
    coverage: 85,
    journeys: 1,
    suggested: 0,
    paths: ["/app", "/app/reports"],
  },
];

export const suggestedJourneys: SuggestedJourney[] = [
  {
    id: "sj_1",
    title: "Billing seat upgrade → invoice",
    category: "admin",
    reason: "Detected /billing/seats but no journey covers it.",
    sourceRunId: "run_8s7d2",
  },
  {
    id: "sj_2",
    title: "Global search → facet filter → save",
    category: "search",
    reason: "Search workflow exists but no save-state journey.",
    sourceRunId: "run_8s7d2",
  },
];

export const alertChannels: AlertChannel[] = [
  {
    id: "ch_1",
    name: "#launch-readiness",
    kind: "slack",
    trigger: "Readiness drop > 5 points",
    enabled: true,
  },
  {
    id: "ch_2",
    name: "P0 instant alert",
    kind: "slack",
    trigger: "Any P0 issue surfaces",
    enabled: true,
  },
  {
    id: "ch_3",
    name: "founders@acme.io",
    kind: "email",
    trigger: "Weekly digest · Mon 9am",
    enabled: true,
  },
  {
    id: "ch_4",
    name: "GitHub deploy hook",
    kind: "webhook",
    trigger: "Post-deploy on main",
    enabled: true,
  },
  {
    id: "ch_5",
    name: "Vercel preview rehearsal",
    kind: "webhook",
    trigger: "Every PR preview",
    enabled: false,
  },
];

export const integrations: Integration[] = [
  {
    id: "int_gh",
    name: "GitHub Actions",
    desc: "Run rehearsal on PR / pre-deploy",
    status: "connected",
    category: "ci",
  },
  {
    id: "int_vercel",
    name: "Vercel & Netlify hooks",
    desc: "Post-deploy rehearsal",
    status: "connected",
    category: "deploy",
  },
  {
    id: "int_slack",
    name: "Slack",
    desc: "Alerts + scorecard snippets",
    status: "connected",
    category: "alert",
  },
  {
    id: "int_linear",
    name: "Linear",
    desc: "Export issues as backlog",
    status: "connected",
    category: "export",
  },
  {
    id: "int_jira",
    name: "Jira",
    desc: "Export issues as backlog",
    status: "available",
    category: "export",
  },
  {
    id: "int_dd",
    name: "Datadog / Sentry",
    desc: "Correlate with prod errors (Phase 2)",
    status: "phase 2",
    category: "observability",
  },
  {
    id: "int_sso",
    name: "SSO (Okta, Google, Azure AD)",
    desc: "Dashboard login (Phase 2)",
    status: "phase 2",
    category: "auth",
  },
  {
    id: "int_rbac",
    name: "RBAC",
    desc: "Admin · viewer · run-only",
    status: "available",
    category: "auth",
  },
];

export const backlogItems: BacklogItem[] = [
  {
    id: "bl_1",
    title: "SSO callback drops session on Safari 17",
    severity: "P0",
    owner: "backend",
    fixBeforeLaunch: true,
    exportTargets: ["linear", "github"],
  },
  {
    id: "bl_2",
    title: "Pricing page CTA copy mismatch",
    severity: "P1",
    owner: "content",
    fixBeforeLaunch: true,
    exportTargets: ["linear"],
  },
  {
    id: "bl_3",
    title: "Invite flow loses role on validation error",
    severity: "P1",
    owner: "frontend",
    fixBeforeLaunch: true,
    exportTargets: ["jira", "linear"],
  },
  {
    id: "bl_4",
    title: "Empty state for /reports",
    severity: "P2",
    owner: "frontend",
    fixBeforeLaunch: false,
    exportTargets: ["github"],
  },
];

export const readinessTrend = [62, 68, 71, 70, 74, 79, 77, 74, 82];
export const crawlSizeTrend = [112, 118, 121, 125, 129, 132, 134, 136, 137];
export const flakeRateTrend = [5.2, 4.8, 4.1, 3.9, 3.5, 3.4, 3.2, 3.1, 3.1];

export const issueRecurrence = [
  {
    name: "SSO callback drops session on Safari 17",
    runs: 3,
    status: "open" as const,
    first: "May 26",
    runIds: ["run_8s5l9", "run_8s6q1", "run_8s7d2"],
  },
  {
    name: "Pricing CTA copy mismatch",
    runs: 1,
    status: "new" as const,
    first: "May 29",
    runIds: ["run_8s7d2"],
  },
  {
    name: "Invite role lost on validation error",
    runs: 2,
    status: "regression" as const,
    first: "May 27",
    runIds: ["run_8s6q1", "run_8s7d2"],
  },
  {
    name: "Auth wall on deep link (Argyle)",
    runs: 2,
    status: "open" as const,
    first: "May 29",
    runIds: ["enterprise-20260529-213552", "enterprise-20260530-045757"],
  },
  {
    name: "Old footer year (2024)",
    runs: 6,
    status: "won't-fix?" as const,
    first: "May 22",
    runIds: ["run_8s1k4"],
  },
];

export const scheduledRuns = [
  { cron: "0 */6 * * *", env: "prod-canary" as const, next: "2026-05-30T18:00:00Z", enabled: true },
  { cron: "0 9 * * 1", env: "staging" as const, next: "2026-06-02T09:00:00Z", enabled: true },
  { cron: "0 0 * * *", env: "demo" as const, next: "2026-05-31T00:00:00Z", enabled: false },
];

export const auditLog = [
  { at: "2026-05-29T14:12:42Z", who: "cli@local", action: "run complete", target: "run_8s7d2" },
  {
    at: "2026-05-29T15:00:00Z",
    who: "danielle@acme.io",
    action: "viewed scorecard",
    target: "run_8s7d2",
  },
  {
    at: "2026-05-29T15:30:00Z",
    who: "rob@acme.io",
    action: "annotated iss_006",
    target: "false positive",
  },
  {
    at: "2026-05-30T05:02:37Z",
    who: "cli@local",
    action: "run complete",
    target: "enterprise-20260530-045757",
  },
];

export const agentConfigDefaults = {
  enabled: ["crawler", "workflow", "journey", "persona", "synthesizer", "llm_persona"],
  optional: ["compliance", "performance"],
  crawlMaxDepth: 4,
  crawlMaxPages: 200,
  crawlRespectRobots: true,
  strictEnterpriseMode: true,
  llmModel: "deepseek-ai/deepseek-v4-flash",
  llmProvider: "NVIDIA NIM",
};

// Legacy compat exports used by existing components
export const runs = runSummaries.map((s) => ({
  id: s.id,
  target: s.target,
  env: s.env,
  startedAt: s.startedAt,
  durationSec: s.durationSec,
  readiness: s.readiness,
  status: s.status,
  blockers: s.blockers,
  delights: s.delights,
  pages: s.pages,
  agentCost: s.agentCost,
}));

export const issues = acmeBundle.issues;
export const delights = acmeBundle.delights;
export const agents = acmeBundle.agents;
export const pages = ACME_PAGES.map((p) => ({
  id: p.id,
  url: p.path,
  title: p.title,
  type: p.type,
  workflow: p.workflow,
  errors: p.errors,
}));
export const dimensions = ALL_DIMENSIONS.map((d) => ({ name: d.name, score: d.score }));

export function matrixGrade(
  pi: number,
  ji: number,
  runId?: string,
): import("./types").StepOutcome | "fail" {
  const bundle = runId ? getRunBundle(runId) : acmeBundle;
  if (!bundle) return "pass";
  const p = personas[pi];
  const j = (
    runId?.startsWith("enterprise")
      ? enterpriseJourneys
      : runId?.startsWith("cal")
        ? calJourneys
        : journeys
  )[ji];
  if (!p || !j) return "pass";
  const cell = bundle.matrix.find((c) => c.personaId === p.id && c.journeyId === j.id);
  return cell?.grade ?? "pass";
}

export function getJourneysForRun(runId: string): Journey[] {
  if (runId.startsWith("enterprise")) return enterpriseJourneys;
  if (runId.startsWith("cal")) return calJourneys;
  return journeys;
}

export function getPersonasForRun(runId: string): Persona[] {
  if (runId.startsWith("enterprise")) return personas.slice(0, 3);
  return personas;
}
