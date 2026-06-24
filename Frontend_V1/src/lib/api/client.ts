/** HTTP client for Launch Rehearsal dashboard API (rehearse serve :8765). */

import type {
  AlertChannel,
  Annotation,
  BacklogItem,
  CommandDigest,
  ExperimentSpec,
  InsightNarrative,
  Integration,
  LibraryPersona,
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

// Optional static API token — set VITE_REHEARSE_API_TOKEN in .env.local for deployed auth.
// Falls back to a user JWT stored by /auth/login if no static token is set.
const API_TOKEN =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_REHEARSE_API_TOKEN) || "";

const JWT_STORAGE_KEY = "rehearse:jwt";

export function getStoredJwt(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(JWT_STORAGE_KEY) || "";
}

async function apiFetch<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const bearer = API_TOKEN || getStoredJwt();
  const authHeaders: Record<string, string> = bearer ? { Authorization: `Bearer ${bearer}` } : {};
  const timeoutMs = init?.timeoutMs ?? 30000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const { timeoutMs: _t, ...fetchInit } = init ?? {};
    const res = await fetch(`${API_BASE}${path}`, {
      ...fetchInit,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...(fetchInit?.headers ?? {}),
      },
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new ApiError(text || res.statusText, res.status);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

export function artifactUrl(relPath: string): string {
  // Strip absolute prefix (launch-rehearsal/artifacts/ or /abs/path/.../artifacts/)
  // but keep relative sub-paths like artifacts/{run_id}/... intact —
  // /files/{rel} maps directly to artifacts_root/{rel} on the server.
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
  trends: (configPrefix?: string) =>
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
    }>(
      configPrefix ? `/api/trends?configPrefix=${encodeURIComponent(configPrefix)}` : "/api/trends",
    ),
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
  getProductModel: (configId?: string | null) =>
    apiFetch<Record<string, unknown>>(`/api/product${configId ? `?configId=${configId}` : ""}`),
  analyzeProduct: (body: {
    targetUrl: string;
    productName?: string;
    configId?: string;
    sitemapPages?: unknown[];
  }) =>
    apiFetch<Record<string, unknown>>("/api/product/analyze", {
      method: "POST",
      body: JSON.stringify(body),
      timeoutMs: 360000, // 6 min — max_pages=40 with vision can take a few minutes
    }),
  updateProductModel: (updates: Record<string, unknown>, configId?: string | null) =>
    apiFetch<Record<string, unknown>>("/api/product/update", {
      method: "POST",
      body: JSON.stringify({ ...updates, configId: configId || "" }),
    }),
  getConfigSettings: (configId: string) =>
    apiFetch<{
      targetUrl?: string;
      productName?: string;
      loginPath?: string;
      hasAuth?: boolean;
      hasEmail?: boolean;
      hasPassword?: boolean;
    }>(`/api/configs/${encodeURIComponent(configId)}/settings`),
  saveConfigSettings: (
    configId: string,
    settings: {
      targetUrl?: string;
      productName?: string;
      loginPath?: string;
      email?: string;
      password?: string;
    },
  ) =>
    apiFetch<{ targetUrl?: string; productName?: string; loginPath?: string }>(
      `/api/configs/${encodeURIComponent(configId)}/settings`,
      { method: "POST", body: JSON.stringify(settings) },
    ),
  discoverJourneys: (personas: unknown[], configId?: string | null, productModel?: unknown) =>
    apiFetch<{ personaJourneys: unknown[]; count: number }>("/api/journeys/discover", {
      method: "POST",
      body: JSON.stringify({
        personas,
        configId: configId || "",
        productModel: productModel || null,
      }),
      timeoutMs: 180000,
    }),
  discoverJourneysForPersona: (
    persona: unknown,
    configId?: string | null,
    productModel?: unknown,
  ) =>
    apiFetch<Record<string, unknown>>("/api/journeys/discover/persona", {
      method: "POST",
      body: JSON.stringify({
        persona,
        configId: configId || "",
        productModel: productModel || null,
      }),
      timeoutMs: 120000,
    }),
  discoverJourneysForPersonaStream: async function* (
    persona: unknown,
    configId?: string | null,
    productModel?: unknown,
  ): AsyncGenerator<Record<string, unknown>> {
    const bearer = API_TOKEN || getStoredJwt();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (bearer) headers["Authorization"] = `Bearer ${bearer}`;
    const res = await fetch(`${API_BASE}/api/journeys/discover/persona/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        persona,
        configId: configId || "",
        productModel: productModel || null,
      }),
    });
    if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() ?? "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            yield JSON.parse(line.slice(6)) as Record<string, unknown>;
          } catch {
            /* skip */
          }
        }
      }
    }
  },
  importJourneysToConfig: (configId: string, journeys: unknown[]) =>
    apiFetch<{ configId: string; added: number; skipped: number; total: number }>(
      "/api/journeys/import",
      {
        method: "POST",
        body: JSON.stringify({ configId, journeys }),
      },
    ),
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
    apiFetch<{
      ok: boolean;
      url?: string;
      status_code?: number;
      error?: string;
      looks_like_auth_wall?: boolean;
      redirected?: boolean;
    }>("/api/preflight", {
      method: "POST",
      body: JSON.stringify({ url, allowLocalhost: opts?.allowLocalhost }),
    }),
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
    localTimestamp?: string; // YYYYMMDD-HHmmss in user's local timezone
    existingConfigId?: string; // copy journeys from this config into the new file
  }) =>
    apiFetch<{ id: string; path: string; name: string }>("/api/configs", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  crawlGraph: async (runId: string) => {
    type CrawlGraphData = {
      targetUrl?: string;
      nodes: { id: string; status: "queued" | "visiting" | "visited" | "skipped" | "error" }[];
      edges: { source: string; target: string }[];
      visitedCount: number;
      maxPages: number;
    };
    // Try the dedicated endpoint; fall back to /files/ for servers without this route
    try {
      const result = await apiFetch<CrawlGraphData>(
        `/api/runs/${encodeURIComponent(runId)}/crawl-graph`,
      );
      if (result && result.nodes?.length > 0) return result;
    } catch {
      /* fall through */
    }
    return apiFetch<CrawlGraphData>(`/files/runs/${encodeURIComponent(runId)}-crawl-graph.json`);
  },
  productCrawlGraph: (configId: string) => {
    type CrawlGraphData = {
      targetUrl?: string;
      nodes: { id: string; status: "queued" | "visiting" | "visited" | "skipped" | "error" }[];
      edges: { source: string; target: string }[];
      visitedCount: number;
      maxPages: number;
    };
    return apiFetch<CrawlGraphData>(`/api/product/${encodeURIComponent(configId)}/crawl-graph`);
  },
  getCredentials: () => apiFetch<{ hasEmail: boolean; hasPassword: boolean }>("/api/credentials"),
  saveCredentials: (
    email: string,
    password: string,
    opts?: { configId?: string; loginPath?: string },
  ) =>
    apiFetch<{ ok: boolean; yamlUpdated: boolean }>("/api/credentials", {
      method: "POST",
      body: JSON.stringify({ email, password, ...opts }),
    }),
  controlRun: (runId: string, signal: "pause" | "resume" | "stop") =>
    apiFetch<{ runId: string; signal: string }>(`/api/runs/${encodeURIComponent(runId)}/control`, {
      method: "POST",
      body: JSON.stringify({ signal }),
    }),
  graphmlUrl: (runId: string) => `${API_BASE}/api/sitemap/${runId}/graphml`,

  // Auth
  authSignup: (email: string, password: string, name: string) =>
    apiFetch<{ token: string; user: { id: string; email: string; name: string } }>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),
  authLogin: (email: string, password: string) =>
    apiFetch<{ token: string; user: { id: string; email: string; name: string } }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  authMe: () => apiFetch<{ id: string; email: string; name: string }>("/auth/me"),
  updateProfile: (body: { name?: string; currentPassword?: string; newPassword?: string }) =>
    apiFetch<{ id: string; email: string; name: string }>("/auth/me", {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  // Workspaces
  myWorkspaces: () =>
    apiFetch<
      {
        id: string;
        slug: string;
        name: string;
        ownerId: string;
        targetUrl: string;
        productName: string;
        teamRole: string;
        configPath: string;
        createdAt: string;
        plan: string;
      }[]
    >("/api/workspaces/me"),
  createWorkspace: (body: {
    name: string;
    targetUrl: string;
    productName: string;
    teamRole: string;
  }) =>
    apiFetch<{
      id: string;
      slug: string;
      name: string;
      ownerId: string;
      targetUrl: string;
      productName: string;
      teamRole: string;
      configPath: string;
      createdAt: string;
    }>("/api/workspaces", { method: "POST", body: JSON.stringify(body) }),

  // Workspace membership
  workspaceMembers: (slug: string) =>
    apiFetch<
      { userId: string; role: "owner" | "member"; joinedAt: string; email: string; name: string }[]
    >(`/api/workspaces/${encodeURIComponent(slug)}/members`),
  workspaceInvites: (slug: string) =>
    apiFetch<{ token: string; email: string; role: "owner" | "member"; createdAt: string }[]>(
      `/api/workspaces/${encodeURIComponent(slug)}/invites`,
    ),
  inviteToWorkspace: (slug: string, email: string, role: "owner" | "member" = "member") =>
    apiFetch<{
      token: string;
      workspaceId: string;
      email: string;
      role: string;
      createdAt: string;
    }>(`/api/workspaces/${encodeURIComponent(slug)}/invite`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    }),
  removeWorkspaceMember: (slug: string, userId: string) =>
    apiFetch<{ removed: string }>(
      `/api/workspaces/${encodeURIComponent(slug)}/members/${encodeURIComponent(userId)}`,
      { method: "DELETE" },
    ),
  workspaceUsage: (slug: string) =>
    apiFetch<{
      workspaceSlug: string;
      runsThisMonth: number;
      periodStart: string;
      periodEnd: string;
    }>(`/api/workspaces/${encodeURIComponent(slug)}/usage`),
  caseStudy: (slug: string) =>
    apiFetch<{
      workspaceSlug: string;
      productName: string | null;
      before: {
        runId: string;
        readiness: number;
        launchGate: string;
        blockers: number;
        delights: number;
        startedAt: string;
      };
      after: {
        runId: string;
        readiness: number;
        launchGate: string;
        blockers: number;
        delights: number;
        startedAt: string;
      };
      readinessDelta: number;
      blockersResolved: number;
      totalRuns: number;
      outcome: { launchSucceeded: boolean | null; notes?: string } | null;
    }>(`/api/workspaces/${encodeURIComponent(slug)}/case-study`),
  createCheckoutSession: (plan: string, workspaceSlug: string) =>
    apiFetch<{ url: string; sessionId: string } | { error: string }>("/api/billing/checkout", {
      method: "POST",
      body: JSON.stringify({
        plan,
        workspaceSlug,
        successUrl: `${typeof window !== "undefined" ? window.location.origin : ""}/${workspaceSlug}/settings?upgraded=1`,
        cancelUrl: `${typeof window !== "undefined" ? window.location.origin : ""}/${workspaceSlug}/settings`,
      }),
    }),

  // Admin / company observability — gated server-side by REHEARSE_ADMIN_EMAILS
  adminSummary: () =>
    apiFetch<{
      totalUsers: number;
      totalWorkspaces: number;
      workspacesNeverRun: number;
      neverRunSlugs: string[];
      failedJobsRecent: number;
      totalJobsRecorded: number;
    }>("/api/admin/summary"),
  adminWorkspaces: () =>
    apiFetch<
      {
        id: string;
        slug: string;
        name: string;
        ownerEmail: string | null;
        ownerName: string | null;
        targetUrl: string;
        productName: string;
        plan: string;
        createdAt: string;
        memberCount: number;
        totalRuns: number;
        neverRan: boolean;
        lastRunStatus: string | null;
        lastRunAt: string | null;
        lastRunError: string | null;
        runsThisMonth: number;
        runLimit: number | null;
        productAnalysis: {
          pageCount: number;
          source: string | null;
          authWallDetected: boolean | null;
          loginAttempted: boolean | null;
          loginSucceeded: boolean | null;
        } | null;
      }[]
    >("/api/admin/workspaces"),
  adminUsers: () =>
    apiFetch<{ id: string; email: string; name: string; createdAt: string }[]>("/api/admin/users"),
  adminActivity: (limit = 50) => apiFetch<JobRecord[]>(`/api/admin/activity?limit=${limit}`),

  acceptInvite: (token: string) =>
    apiFetch<{ workspaceId: string; userId: string; role: string; joinedAt: string }>(
      `/api/invites/${encodeURIComponent(token)}/accept`,
      { method: "POST" },
    ),
  getInvite: (token: string) =>
    apiFetch<{
      token: string;
      workspaceId: string;
      email: string;
      role: string;
      invitedBy: string;
      createdAt: string;
      acceptedAt: string | null;
      workspaceName: string | null;
      workspaceSlug: string | null;
    }>(`/api/invites/${encodeURIComponent(token)}`),

  // ── Persona Library ─────────────────────────────────────────────────────
  // The library is workspace-global: personas can be reused across products.

  /** Fetch all library personas (newest first). */
  listPersonaLibrary: () => apiFetch<LibraryPersona[]>("/api/persona-library"),

  /** Fetch a single library persona by id. */
  getPersonaLibrary: (id: string) =>
    apiFetch<LibraryPersona>(`/api/persona-library/${encodeURIComponent(id)}`),

  /** Create or update a persona in the library. */
  savePersonaLibrary: (persona: Partial<LibraryPersona> & { name: string; role: string }) =>
    apiFetch<LibraryPersona>("/api/persona-library", {
      method: "POST",
      body: JSON.stringify(persona),
    }),

  /** AI-generate a rich behavioral persona.
   *  Pass save=true to persist immediately, or false to preview first. */
  generatePersonaLibrary: (body: {
    prompt: string;
    productName?: string;
    targetUrl?: string;
    save?: boolean;
  }) =>
    apiFetch<{ persona: LibraryPersona; yamlFragment: string }>("/api/persona-library/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** Bulk-import all personas from an existing config into the library. */
  importPersonasFromConfig: (configId: string) =>
    apiFetch<{ imported: number; personas: LibraryPersona[] }>("/api/persona-library/import", {
      method: "POST",
      body: JSON.stringify({ configId }),
    }),

  /** Delete a library persona by id. */
  deletePersonaLibrary: (id: string) =>
    apiFetch<{ deleted: string }>(`/api/persona-library/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  /** A5: Get per-finding outcomes for a run (severity calibration data). */
  findingOutcomes: (runId: string) =>
    apiFetch<Record<string, string>>(`/api/finding-outcomes/${encodeURIComponent(runId)}`),

  /** A5: Record a developer's judgment on a finding. */
  setFindingOutcome: (runId: string, findingId: string, outcome: string) =>
    apiFetch<{ runId: string; findingId: string; outcome: string; labeledAt: string }>(
      "/api/finding-outcomes",
      { method: "POST", body: JSON.stringify({ runId, findingId, outcome }) },
    ),
};
