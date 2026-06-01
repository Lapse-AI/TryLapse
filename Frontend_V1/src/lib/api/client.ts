/** HTTP client for Launch Rehearsal dashboard API (rehearse serve :8765). */

import type {
  AlertChannel,
  Annotation,
  BacklogItem,
  CommandDigest,
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

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
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
    apiFetch<{ id: string; path: string; yaml: string }>(`/api/configs/${configId}`),
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
  }) =>
    apiFetch<{ id: string; path: string; name: string }>("/api/configs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  graphmlUrl: (runId: string) => `${API_BASE}/api/sitemap/${runId}/graphml`,
};
