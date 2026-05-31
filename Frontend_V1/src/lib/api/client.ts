/** HTTP client for Launch Rehearsal dashboard API (rehearse serve :8765). */

import type {
  AlertChannel,
  Annotation,
  BacklogItem,
  Integration,
  RunBundle,
  RunDiff,
  RunSummary,
  Workspace,
} from "@/lib/mock-data/types";

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_REHEARSE_API) || "";

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
  diff: (a: string, b: string) =>
    apiFetch<RunDiff>(`/api/diff?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`),
  trends: () =>
    apiFetch<{
      readiness: number[];
      pages: number[];
      flakeRate: number[];
      runIds: string[];
      labels: string[];
    }>("/api/trends"),
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
  jobs: () =>
    apiFetch<{ id: string; mode: string; status: string; runId?: string; error?: string }[]>(
      "/api/jobs",
    ),
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
  preflight: (url: string) =>
    apiFetch<{ ok: boolean; url?: string; status_code?: number; error?: string }>(
      "/api/preflight",
      { method: "POST", body: JSON.stringify({ url }) },
    ),
  annotations: (runId: string) => apiFetch<Annotation[]>(`/api/annotations/${runId}`),
  addAnnotation: (runId: string, ann: Annotation) =>
    apiFetch<Annotation[]>(`/api/annotations/${runId}`, {
      method: "POST",
      body: JSON.stringify(ann),
    }),
  saveConfig: (body: {
    targetUrl: string;
    productName?: string;
    withAuth?: boolean;
    piiRedaction?: boolean;
  }) =>
    apiFetch<{ id: string; path: string; name: string }>("/api/configs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  graphmlUrl: (runId: string) => `${API_BASE}/api/sitemap/${runId}/graphml`,
};
