/** Mock data types — shaped to match backend artifacts + future API contract. */

export type Severity = "P0" | "P1" | "P2" | "P3";
export type Status = "ready" | "warn" | "danger" | "neutral";
export type AgentStatus = "running" | "done" | "failed" | "idle" | "skipped";
export type StepOutcome = "pass" | "partial" | "fail" | "skipped";
export type ReadinessBand = "Green" | "Amber" | "Red";
export type EnvId = "staging" | "prod-canary" | "demo" | "local";

export type Persona = {
  id: string;
  name: string;
  role: string;
  goal: string;
  patience: "low" | "medium" | "high";
  stressFactors?: string[];
};

export type Journey = {
  id: string;
  name: string;
  steps: number;
  category: "auth" | "pricing" | "admin" | "search" | "docs" | "dashboard";
};

export type Issue = {
  id: string;
  runId: string;
  severity: Severity;
  title: string;
  detail: string;
  persona: string;
  personaId: string;
  journey: string;
  journeyId: string;
  stepId: string;
  dimension: string;
  confidence: "high" | "hypothesis";
  owner: "frontend" | "backend" | "content" | "security";
  recurring: number;
  evidence: string;
  severityReason?: string;
  personaImpact?: string;
  similarIssueIds?: string[];
  suggestion?: string;
  screenshotPath?: string;
  focusRegion?: FocusRegion | null;
};

export type FocusRegion = {
  x: number;
  y: number;
  width: number;
  height: number;
  viewportWidth: number;
  viewportHeight: number;
  label?: string;
};

export type Delight = {
  id: string;
  runId: string;
  title: string;
  quote: string;
  persona: string;
  journey: string;
  stepId?: string;
  marketingReady?: boolean;
  regressionRisk?: boolean;
};

export type RunSummary = {
  id: string;
  productName: string;
  target: string;
  targetUrl: string;
  env: EnvId;
  workspaceId: string;
  startedAt: string;
  finishedAt: string;
  durationSec: number;
  readiness: number;
  readinessBand: ReadinessBand;
  status: Status;
  blockers: number;
  issues: number;
  delights: number;
  pages: number;
  stepCount: number;
  agentCost: number;
  costEstimate?: {
    usd: number;
    source?: string;
    inputTokens?: number;
    outputTokens?: number;
  };
  outcome: "complete" | "dry_run_complete" | "failed";
  configHash: string;
  authAttempted?: boolean;
  authOutcome?: string;
  llmEnabled?: boolean;
  crawlEnabled?: boolean;
  orphans?: number;
  authGated?: number;
  pagesCrawled?: number;
  agentsRun?: number;
  networkLogPath?: string | null;
  webVitalsPath?: string | null;
};

export type StepSnapshot = {
  stepId: string;
  journeyId: string;
  journeyName: string;
  personaId: string;
  action: string;
  requestedUrl: string | null;
  finalUrl: string | null;
  outcome: StepOutcome;
  durationMs: number;
  note?: string | null;
  errorType?: string | null;
  flaky?: boolean;
  consoleErrors?: string[];
  consoleWarnings?: string[];
  networkFailures?: string[];
  webVitals?: Record<string, number | null>;
  artifactPaths?: string[];
  exploreLog?: {
    round: number;
    url?: string;
    rationale?: string | null;
    done?: boolean;
    error?: string | null;
    actions?: { action: string; intent?: string; outcome: string; error?: string }[];
  }[];
  exploreSummary?: string | null;
  focusRegion?: FocusRegion | null;
};

export type AgentNode = {
  id: string;
  runId: string;
  name: string;
  role: string;
  phase: "crawl" | "workflow" | "journey" | "persona" | "synthesis" | "compliance" | "performance";
  status: AgentStatus;
  durationSec: number;
  costUsd: number;
  lastSummary: string;
  findingsCount?: number;
  delightsCount?: number;
  handoff?: Record<string, string | number>;
  expandableFindings?: { title: string; severity?: Severity }[];
};

export type SitemapPage = {
  id: string;
  path: string;
  title: string;
  type: "hub" | "leaf" | "orphan" | "auth";
  workflow?: Journey["category"];
  errors: number;
  linksFrom?: string[];
  screenshotPath?: string;
};

export type SitemapEdge = { from: string; to: string };

export type WorkflowCoverage = {
  category: Journey["category"];
  coverage: number;
  journeys: number;
  suggested: number;
  paths: string[];
};

export type SuggestedJourney = {
  id: string;
  title: string;
  category: Journey["category"];
  reason: string;
  sourceRunId: string;
};

export type DimensionScore = {
  name: string;
  score: number;
  signal?: string;
  automated?: boolean;
};

export type MatrixCell = {
  personaId: string;
  journeyId: string;
  grade: StepOutcome | "fail";
};

export type Annotation = {
  id: string;
  runId: string;
  targetType: "issue" | "delight" | "finding";
  targetId: string;
  action: "agreed" | "disagree" | "false positive" | "pinned" | "manual";
  author: string;
  note?: string;
  at: string;
};

export type InsightNarrative = {
  headline: string;
  forFounders: string;
  forEngineering: string;
  verdict: string;
  suggestedQuestions?: string[];
  source: string;
  llmNote?: string;
};

export type CommandDigest = {
  headline: string;
  bullets: string[];
  readinessTrend: string;
  source: string;
  latestRunId?: string;
  runCount?: number;
  llmNote?: string;
};

export type CompareNarrative = {
  headline: string;
  forFounders: string;
  forEngineering: string;
  verdict: string;
  readinessDelta?: string;
  suggestedQuestions: string[];
  source: string;
  llmNote?: string;
};

export type RunDiff = {
  runA: string;
  runB: string;
  readinessA: ReadinessBand;
  readinessB: ReadinessBand;
  narrative?: CompareNarrative;
  issuesA: number;
  issuesB: number;
  pagesA: number;
  pagesB: number;
  newPages: string[];
  removedPages: string[];
  changedSteps: {
    stepId: string;
    outcomeA: StepOutcome;
    outcomeB: StepOutcome;
    urlA?: string;
    urlB?: string;
    screenshotPathA?: string | null;
    screenshotPathB?: string | null;
    focusRegionA?: FocusRegion | null;
    focusRegionB?: FocusRegion | null;
    journeyId?: string;
    action?: string;
  }[];
  visualDiffs?: {
    stepId: string;
    journeyId?: string;
    action?: string;
    outcomeA?: string | null;
    outcomeB?: string | null;
    screenshotPathA?: string | null;
    screenshotPathB?: string | null;
    focusRegionA?: FocusRegion | null;
    focusRegionB?: FocusRegion | null;
    onlyInB?: boolean;
  }[];
  stepsOnlyInA: string[];
  stepsOnlyInB: string[];
  resolvedIssues: string[];
  newIssues: string[];
};

export type RunNarrative = {
  executiveSummary: string;
  forFounders: string;
  forEngineering: string;
  suggestedQuestions: string[];
  source: string;
  readinessBand?: string;
  issueCount?: number;
  delightCount?: number;
  chatReadySummary?: string;
  llmNote?: string;
};

export type RunBundle = {
  summary: RunSummary;
  steps: StepSnapshot[];
  issues: Issue[];
  delights: Delight[];
  agents: AgentNode[];
  matrix: MatrixCell[];
  dimensions: DimensionScore[];
  narrative?: RunNarrative;
  scorecardMd: string;
  sitemapMd: string;
  sitemapPages: SitemapPage[];
  sitemapEdges: SitemapEdge[];
  screenshots: { path: string; stepId: string; label: string }[];
  annotations: Annotation[];
  personas?: Persona[];
  journeys?: Journey[];
  workflows?: {
    category: string;
    path: string;
    title: string;
    confidence: number;
    signals: string[];
  }[];
  suggestedJourneys?: SuggestedJourney[];
};

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  targetUrl: string;
  members: number;
  products: number;
  configVersion: string;
  configHash: string;
  gitUrl?: string;
  strictEnterpriseMode: boolean;
  retentionDays: 30 | 90 | 365;
  piiRedaction: boolean;
  env?: EnvId;
};

export type AlertChannel = {
  id: string;
  name: string;
  kind: "slack" | "email" | "webhook";
  trigger: string;
  enabled: boolean;
};

export type Integration = {
  id: string;
  name: string;
  desc: string;
  status: "connected" | "available" | "phase 2";
  category: "ci" | "deploy" | "alert" | "export" | "observability" | "auth";
};

export type BacklogItem = {
  id: string;
  title: string;
  severity: Severity;
  owner: Issue["owner"];
  fixBeforeLaunch: boolean;
  exportTargets: ("linear" | "jira" | "github")[];
};
