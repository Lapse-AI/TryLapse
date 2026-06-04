/** HTTP client for Launch Rehearsal dashboard API (rehearse serve :8765). */

import type {
  AlertChannel,
  Annotation,
  BacklogItem,
  CommandDigest,
  ExperimentSpec,
  InsightNarrative,
  Integration,
  RunBundle,
  RunDiff,
  RunSummary,
  Workspace,
} from "@/lib/mock-data/types";

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_REHEARSE_API) || "";

export type JobRecord = {
  id: string;
  mode: string;
  status: "queued" | "running" | "done" | "failed" | string;
  runId?: string | null;
  error?: string | null;
  startedAt?: string;
  finishedAt?: string | null;
  config?: string;
  deduped?: boolean;
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

// Optional API token — set VITE_REHEARSE_API_TOKEN in .env.local for deployed auth
const API_TOKEN =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_REHEARSE_API_TOKEN) || "";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeaders: Record<string, string> = API_TOKEN
    ? { Authorization: `Bearer ${API_TOKEN}` }
    : {};
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(text || res.statusText, res.status);
  }
  return res.json() as Promise<T>;
}

export function artifactUrl(relPath: string): string {
  const clean = relPath.replace(/^launch-rehearsal\/artifacts\//, "").replace(/^\//, "");
  return `${API_BASE}/files/${clean}`;
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    await apiFetch<{ ok: boolean }>("/api/health");
    return true;
  } catch {
    return false;
  }
}

export const api = {
  summaries: () => apiFetch<RunSummary[]>("/api/summaries"),
  bundle: (runId: string) => apiFetch<RunBundle>(`/api/bundle/${runId}`),
  chatRun: (runId: string, message: string) =>
    apiFetch<{ runId: string; reply: string; source: string; llmError?: string }>(
      `/api/runs/${encodeURIComponent(runId)}/chat`,
      {
        method: "POST",
        body: JSON.stringify({ message }),
      },
    ),
  chatThread: (runId: string) =>
    apiFetch<{ runId: string; turns: { role: string; content: string; at?: string }[] }>(
      `/api/runs/${encodeURIComponent(runId)}/chat`,
    ),
  diff: (a: string, b: string) =>
    apiFetch<RunDiff>(`/api/diff?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`),
  trends: () =>
    apiFetch<{
      readiness: (number | string)[];
      pages: number[];
      flakeRate: number[];
      runIds: string[];
      labels: string[];
      issueRecurrence?: {
        name: string;
        runs: number;
        status: string;
        first: string;
        runIds?: string[];
      }[];
      issuesOpened?: number;
      issuesResolved?: number;
      blockerCounts?: number[];
      narrative?: InsightNarrative;
    }>("/api/trends"),
  digest: (n = 7) => apiFetch<CommandDigest>(`/api/digest?n=${n}`),
  compileRecording: (body: {
    journeyId?: string;
    journeyName?: string;
    steps: { action: string; url?: string; intent?: string; value?: string }[];
  }) =>
    apiFetch<{ valid: boolean; yaml: string; errors: string[] }>("/api/recordings/compile", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  search: (q: string) =>
    apiFetch<{ runs: RunSummary[]; issues: unknown[]; pages: unknown[]; query: string }>(
      `/api/search?q=${encodeURIComponent(q)}`,
    ),
  workspace: () => apiFetch<Workspace>("/api/workspace"),
  saveWorkspace: (ws: Partial<Workspace>) =>
    apiFetch<Workspace>("/api/workspace", { method: "PUT", body: JSON.stringify(ws) }),
  integrations: () => apiFetch<Integration[]>("/api/integrations"),
  alerts: () => apiFetch<AlertChannel[]>("/api/alerts"),
  backlog: () => apiFetch<BacklogItem[]>("/api/backlog"),
  configs: () =>
    apiFetch<{ id: string; path: string; name: string; source: string }[]>("/api/configs"),
  library: () =>
    apiFetch<{
      templates: {
        id: string;
        title: string;
        category: string;
        reason: string;
        configPath?: string;
        steps?: number;
      }[];
      suggested: unknown[];
      parallelSeeds: boolean;
      flakyConfig: boolean;
    }>("/api/library"),
  init: () =>
    apiFetch<{
      steps: { id: string; title: string; description: string }[];
      defaults: Record<string, unknown>;
      configs: { id: string; path: string; name: string }[];
      cliHint: string;
      writeHint?: string;
    }>("/api/init"),
  jobs: () => apiFetch<JobRecord[]>("/api/jobs"),
  triggerJob: (body: {
    mode?: "run" | "crawl";
    configPath?: string;
    llm?: boolean;
    noCrawl?: boolean;
  }) =>
    apiFetch<{ id: string; status: string }>("/api/jobs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  triggerCohortJob: (body: {
    configPath: string;
    nSeeds?: number;
    hypothesis?: string;
    llm?: boolean;
  }) =>
    apiFetch<{ id: string; type: string; status: string }>("/api/jobs/cohort", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getCohortJob: (jobId: string) =>
    apiFetch<{
      id: string;
      type: string;
      status: string;
      phase: string;
      config: string;
      nSeeds: number;
      hypothesis: string;
      completedSeeds: number;
      runIds: string[];
      aggregate: {
        readinessMean: number;
        readinessMin: number;
        readinessMax: number;
        spread: number;
        confidence: "high" | "medium" | "low";
        recurringIssues: { title: string; count: number; rate: number }[];
      } | null;
      error: string | null;
      finishedAt: string | null;
    }>(`/api/cohort/${jobId}`),
  triggerVariantJob: (body: {
    configAPath: string;
    configBPath: string;
    hypothesis?: string;
    userGoal?: string;
    llm?: boolean;
  }) =>
    apiFetch<{ id: string; type: string; status: string }>("/api/jobs/variant", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getExperimentReport: (jobId: string) =>
    apiFetch<{
      jobId: string;
      hypothesis: string | null;
      userGoal: string | null;
      readinessDelta: number;
      hypothesisVerdict: "held" | "regressed" | "inconclusive";
      personaComparison: { id: string; name: string; gradeA: string; gradeB: string }[];
      bundleA?: Record<string, unknown>;
      bundleB?: Record<string, unknown>;
      diff?: Record<string, unknown>;
      error?: string;
    }>(`/api/experiment/${jobId}/report`),
  getExperimentChat: (jobId: string) =>
    apiFetch<{ jobId: string; turns: { role: string; content: string; at?: string }[] }>(
      `/api/experiment/${jobId}/chat`,
    ),
  sendExperimentChat: (jobId: string, message: string) =>
    apiFetch<{
      jobId: string;
      reply: string;
      source: string;
      turns: { role: string; content: string; at?: string }[];
    }>(`/api/experiment/${jobId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  getVariantJob: (jobId: string) =>
    apiFetch<{
      id: string;
      type: string;
      status: string;
      phase: string;
      configA: string;
      configB: string;
      hypothesis: string;
      userGoal: string;
      runIdA: string | null;
      runIdB: string | null;
      diffNarrative: Record<string, unknown> | null;
      diff?: Record<string, unknown>;
      error: string | null;
      finishedAt: string | null;
    }>(`/api/variant/${jobId}`),
  preflight: (url: string, opts?: { allowLocalhost?: boolean }) =>
    apiFetch<{ ok: boolean; url?: string; status_code?: number; error?: string }>(
      "/api/preflight",
      {
        method: "POST",
        body: JSON.stringify({ url, allowLocalhost: opts?.allowLocalhost }),
      },
    ),
  annotations: (runId: string) => apiFetch<Annotation[]>(`/api/annotations/${runId}`),
  addAnnotation: (runId: string, ann: Annotation) =>
    apiFetch<Annotation[]>(`/api/annotations/${runId}`, {
      method: "POST",
      body: JSON.stringify(ann),
    }),
  getConfigYaml: (configId: string) =>
    apiFetch<{
      id: string;
      path: string;
      yaml: string;
      experiment?: ExperimentSpec | null;
    }>(`/api/configs/${configId}`),
  saveConfigExperiment: (body: {
    configId: string;
    hypothesis?: string;
    userGoal?: string;
    variantLabel?: string;
  }) =>
    apiFetch<{ id: string; path: string }>("/api/configs/experiment", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  validateConfigYaml: (yaml: string) =>
    apiFetch<{
      valid: boolean;
      errors: string[];
      summary?: { targetUrl?: string; journeyCount?: number };
    }>("/api/configs/validate", {
      method: "POST",
      body: JSON.stringify({ yaml }),
    }),
  saveConfigYaml: (yaml: string, configId?: string) =>
    apiFetch<{ id: string; path: string }>("/api/configs/save", {
      method: "POST",
      body: JSON.stringify({ yaml, configId }),
    }),
  draftJourney: (prompt: string, targetUrl: string) =>
    apiFetch<{ journey: unknown; yamlFragment: string; source: string; hint: string }>(
      "/api/journeys/draft",
      { method: "POST", body: JSON.stringify({ prompt, targetUrl }) },
    ),
  draftPersona: (body: { prompt: string; targetUrl?: string; productName?: string }) =>
    apiFetch<{
      persona: {
        id: string;
        name: string;
        role: string;
        goals: string[];
        enabled?: boolean;
        source?: string;
      };
      yamlFragment: string;
      source: string;
      hint: string;
    }>("/api/personas/draft", { method: "POST", body: JSON.stringify(body) }),
  suggestPersonas: (body: { targetUrl?: string; productName?: string; existingIds?: string[] }) =>
    apiFetch<{
      corePersonas: {
        id: string;
        name: string;
        role: string;
        goals: string[];
        core?: boolean;
        enabled?: boolean;
      }[];
      suggested: {
        id: string;
        name: string;
        role: string;
        goals: string[];
        reason?: string;
      }[];
      source: string;
      hint: string;
    }>("/api/personas/suggest", { method: "POST", body: JSON.stringify(body) }),
  appendPersonaToConfig: (body: { configId: string; persona: Record<string, unknown> }) =>
    apiFetch<{ id: string; path: string }>("/api/configs/append-persona", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateConfigPersonas: (body: {
    configId: string;
    personaEnabled?: Record<string, boolean>;
    personaLens?: boolean;
  }) =>
    apiFetch<{ id: string; path: string }>("/api/configs/personas", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getConfigPersonas: (configId: string) =>
    apiFetch<{
      configId: string;
      personas: { id: string; name: string; role: string; goals: string[]; enabled: boolean }[];
      personaLens: boolean;
    }>(`/api/configs/${configId}/personas`),
  replaceConfigPersonas: (body: {
    configId: string;
    personas: { id: string; name: string; role: string; goals: string[]; enabled?: boolean }[];
    personaLens?: boolean;
  }) =>
    apiFetch<{ id: string; path: string }>("/api/configs/personas/replace", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  appendJourneyToConfig: (body: { configId: string; path: string; title?: string }) =>
    apiFetch<{ configId: string; journeyId: string; url: string }>("/api/configs/append-journey", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  saveConfig: (body: {
    targetUrl: string;
    productName?: string;
    withAuth?: boolean;
    piiRedaction?: boolean;
    allowLocalhost?: boolean;
    selfTest?: boolean;
    excludePathPrefixes?: string | string[];
    viewports?: string | string[];
    executeAllPersonasInBrowser?: boolean;
    personaLens?: boolean;
    personaEnabled?: Record<string, boolean>;
    extraPersonas?: Record<string, unknown>[];
  }) =>
    apiFetch<{ id: string; path: string; name: string }>("/api/configs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  graphmlUrl: (runId: string) => `${API_BASE}/api/sitemap/${runId}/graphml`,
};
