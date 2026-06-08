import { useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import type { Annotation, RunBundle, RunDiff, RunSummary, Workspace } from "@/lib/mock-data/types";
import {
  getLatestRun as mockLatest,
  getRunBundle as mockBundle,
  runSummaries as mockSummaries,
  readinessTrend as mockReadinessTrend,
  crawlSizeTrend as mockCrawlTrend,
  flakeRateTrend as mockFlakeTrend,
  diffRuns as mockDiff,
  workspace as mockWorkspace,
  integrations as mockIntegrations,
  alertChannels as mockAlerts,
  backlogItems as mockBacklog,
  getRunBundle,
  mockCommandDigest,
  mockTrendsNarrative,
  issueRecurrence as mockIssueRecurrence,
} from "@/lib/mock-data";
import { allowsMockFallback } from "@/lib/ui-mode";
import { jobMatchesTestGroup, runMatchesTestGroup } from "@/lib/test-groups";
import { getTestGroupId } from "@/lib/test-auth";
import { getTestGroup } from "@/lib/test-groups";
import { getWorkspace } from "@/lib/workspace";
import { api, checkApiHealth, type JobRecord } from "./client";

export type { JobRecord };

function mockAllowed(live: boolean): boolean {
  return !live && allowsMockFallback();
}

/** Client cache for aggregate NLU endpoints (server also caches LLM output on disk). */
const NARRATIVE_STALE_MS = 30 * 60 * 1000;

export const queryKeys = {
  health: ["rehearse", "health"] as const,
  summaries: ["rehearse", "summaries"] as const,
  bundle: (id: string) => ["rehearse", "bundle", id] as const,
  diff: (a: string, b: string) => ["rehearse", "diff", a, b] as const,
  trends: ["rehearse", "trends"] as const,
  digest: (n: number) => ["rehearse", "digest", n] as const,
  search: (q: string) => ["rehearse", "search", q] as const,
  workspace: ["rehearse", "workspace"] as const,
  integrations: ["rehearse", "integrations"] as const,
  alerts: ["rehearse", "alerts"] as const,
  backlog: ["rehearse", "backlog"] as const,
  library: ["rehearse", "library"] as const,
  init: ["rehearse", "init"] as const,
  jobs: ["rehearse", "jobs"] as const,
  configs: ["rehearse", "configs"] as const,
};

export function useApiHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: checkApiHealth,
    staleTime: 30_000,
    retry: false,
  });
}

export function useRunSummaries() {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.summaries,
    queryFn: async () => {
      if (live) return api.summaries();
      if (mockAllowed(live)) return mockSummaries;
      return [];
    },
    enabled: health.isSuccess && (live || allowsMockFallback()),
    placeholderData: live || !allowsMockFallback() ? undefined : mockSummaries,
  });
}

/** Runs scoped to the active workspace or test group. */
export function useScopedRunSummaries() {
  const { data: all = [], ...rest } = useRunSummaries();
  const userWorkspace = getWorkspace();

  if (userWorkspace) {
    // Real workspace: filter by matching target URL host
    const wsHost = (() => {
      try {
        return new URL(userWorkspace.targetUrl).hostname;
      } catch {
        return "";
      }
    })();
    const scoped = all.filter((r) => {
      if (!r.targetUrl) return false;
      try {
        return new URL(r.targetUrl).hostname === wsHost;
      } catch {
        return false;
      }
    });
    const group = getTestGroup(getTestGroupId());
    return { data: scoped, allRuns: all, group, ...rest };
  }

  // Demo/test mode: filter by test group
  const group = getTestGroup(getTestGroupId());
  const scoped = all.filter((r) => runMatchesTestGroup(r, group));
  return { data: scoped, allRuns: all, group, ...rest };
}

/** Active jobs (queued/running) scoped to the active workspace or test group. */
export function useScopedActiveJobs() {
  const { data: jobs = [], ...rest } = useJobs();
  const userWorkspace = getWorkspace();

  if (userWorkspace) {
    const wsHost = (() => {
      try {
        return new URL(userWorkspace.targetUrl).hostname;
      } catch {
        return "";
      }
    })();
    const active = jobs.filter((j) => {
      if (j.status !== "queued" && j.status !== "running") return false;
      if (!j.config) return false;
      // Match jobs whose target host aligns with workspace
      try {
        return (j as { targetUrl?: string }).targetUrl
          ? new URL((j as { targetUrl?: string }).targetUrl!).hostname === wsHost
          : true;
      } catch {
        return true;
      }
    });
    const group = getTestGroup(getTestGroupId());
    return { data: active, group, ...rest };
  }

  const group = getTestGroup(getTestGroupId());
  const active = jobs.filter(
    (j) => (j.status === "queued" || j.status === "running") && jobMatchesTestGroup(j, group),
  );
  return { data: active, group, ...rest };
}

export function useLatestRun(): RunSummary | undefined {
  const { data: scoped } = useScopedRunSummaries();
  const health = useApiHealth();
  if (health.data === true) return scoped?.[0];
  if (allowsMockFallback()) return scoped?.[0] ?? mockLatest();
  return scoped?.[0];
}

export function useRunBundle(runId: string) {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.bundle(runId),
    queryFn: async (): Promise<RunBundle> => {
      if (live) return api.bundle(runId);
      if (mockAllowed(live)) {
        const mock = mockBundle(runId);
        if (!mock) throw new Error("Run not found");
        return mock;
      }
      throw new Error("Run not found");
    },
    enabled: !!runId && health.isSuccess && (live || allowsMockFallback()),
    placeholderData: live || !allowsMockFallback() ? undefined : getRunBundle(runId),
  });
}

export function useRunDiff(runA: string, runB: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.diff(runA, runB),
    queryFn: async (): Promise<RunDiff> => {
      if (health.data) return api.diff(runA, runB);
      if (mockAllowed(!!health.data)) {
        const mock = mockDiff(runA, runB);
        if (!mock) throw new Error("Could not diff");
        return mock;
      }
      throw new Error("Could not diff");
    },
    enabled: !!runA && !!runB && health.isSuccess && (health.data || allowsMockFallback()),
    staleTime: NARRATIVE_STALE_MS,
    refetchOnWindowFocus: false,
  });
}

export function useCommandDigest(n = 7) {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.digest(n),
    queryFn: async () => {
      if (live) return api.digest(n);
      if (mockAllowed(live)) return mockCommandDigest;
      throw new Error("Digest unavailable");
    },
    enabled: health.isSuccess && (live || allowsMockFallback()),
    placeholderData: live || !allowsMockFallback() ? undefined : mockCommandDigest,
    staleTime: NARRATIVE_STALE_MS,
    refetchOnWindowFocus: false,
  });
}

export function useTrends() {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.trends,
    queryFn: async () => {
      if (live) return api.trends();
      if (mockAllowed(live)) {
        return {
          readiness: mockReadinessTrend,
          pages: mockCrawlTrend,
          flakeRate: mockFlakeTrend,
          runIds: mockSummaries.map((r) => r.id),
          labels: mockSummaries.map((r) => r.startedAt.slice(0, 10)),
          issueRecurrence: mockIssueRecurrence,
          issuesOpened: 1,
          issuesResolved: 1,
          blockerCounts: [3, 2, 2, 3, 2, 2, 0, 4, 4],
          narrative: mockTrendsNarrative,
        };
      }
      return { readiness: [], pages: [], flakeRate: [], runIds: [], labels: [] };
    },
    enabled: health.isSuccess && (live || allowsMockFallback()),
    staleTime: NARRATIVE_STALE_MS,
    refetchOnWindowFocus: false,
  });
}

export function useSearch(q: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.search(q),
    queryFn: () => api.search(q),
    enabled: health.data === true && q.trim().length >= 2,
  });
}

export function useWorkspace() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.workspace,
    queryFn: async () => {
      if (health.data) return api.workspace();
      if (mockAllowed(!!health.data)) return mockWorkspace;
      throw new Error("Workspace unavailable");
    },
    enabled: health.isSuccess && (health.data || allowsMockFallback()),
    placeholderData: allowsMockFallback() ? mockWorkspace : undefined,
  });
}

export function useSaveWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ws: Partial<Workspace>) => api.saveWorkspace(ws),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.workspace }),
  });
}

export function useIntegrations() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.integrations,
    queryFn: async () => {
      if (health.data) return api.integrations();
      if (mockAllowed(!!health.data)) return mockIntegrations;
      return [];
    },
    enabled: health.isSuccess && (health.data || allowsMockFallback()),
    placeholderData: allowsMockFallback() ? mockIntegrations : undefined,
  });
}

export function useAlerts() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: async () => {
      if (health.data) return api.alerts();
      if (mockAllowed(!!health.data)) return mockAlerts;
      return [];
    },
    enabled: health.isSuccess && (health.data || allowsMockFallback()),
    placeholderData: allowsMockFallback() ? mockAlerts : undefined,
  });
}

export function useBacklog() {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.backlog,
    queryFn: async () => {
      if (live) return api.backlog();
      if (mockAllowed(live)) return mockBacklog;
      return [];
    },
    enabled: health.isSuccess && (live || allowsMockFallback()),
    placeholderData: live || !allowsMockFallback() ? undefined : mockBacklog,
  });
}

export function useLibrary() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.library,
    queryFn: () => api.library(),
    enabled: health.data === true,
  });
}

export function useInitWizard() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.init,
    queryFn: () => api.init(),
    enabled: health.data === true,
  });
}

function jobsHaveActive(jobs: JobRecord[] | undefined): boolean {
  return (jobs ?? []).some((j) => j.status === "queued" || j.status === "running");
}

export function useJobs() {
  const health = useApiHealth();
  const qc = useQueryClient();
  const prevStatusRef = useRef<Record<string, string>>({});

  const query = useQuery({
    queryKey: queryKeys.jobs,
    queryFn: () => api.jobs(),
    enabled: health.data === true,
    refetchInterval: (q) => (jobsHaveActive(q.state.data) ? 1500 : 8000),
  });

  useEffect(() => {
    const jobs = query.data;
    if (!jobs?.length) return;

    let refreshedRuns = false;
    for (const j of jobs) {
      const prev = prevStatusRef.current[j.id];
      const now = j.status;
      if (
        prev &&
        (prev === "queued" || prev === "running") &&
        (now === "done" || now === "failed")
      ) {
        if (now === "done" && j.runId) {
          toast.success(`Run finished: ${j.runId}`, {
            action: { label: "Open", onClick: () => (window.location.href = `/runs/${j.runId}`) },
          });
        } else if (now === "failed") {
          toast.error(j.error?.slice(0, 120) || `Job ${j.id} failed`);
        }
        refreshedRuns = true;
      }
      prevStatusRef.current[j.id] = now;
    }

    if (refreshedRuns) {
      void qc.invalidateQueries({ queryKey: queryKeys.summaries });
      void qc.invalidateQueries({ queryKey: queryKeys.trends });
      void qc.invalidateQueries({ queryKey: ["rehearse", "digest"] });
    }
  }, [query.data, qc]);

  return query;
}

export function useTriggerJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof api.triggerJob>[0]) => {
      // Inject workspace configPath so the run targets the user's product, not the demo config
      const ws = getWorkspace();
      if (ws?.configPath && !body.configPath) {
        return api.triggerJob({ ...body, configPath: ws.configPath });
      }
      return api.triggerJob(body);
    },
    onSuccess: (job) => {
      toast.info(`Job ${job.status}: ${job.id}`, { description: "Watch status on Runner" });
      void qc.invalidateQueries({ queryKey: queryKeys.jobs });
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Could not start job");
    },
  });
}

export function useConfigs() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.configs,
    queryFn: () => api.configs(),
    enabled: health.data === true,
  });
}

export function useSaveConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.saveConfig,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.configs });
      qc.invalidateQueries({ queryKey: queryKeys.init });
    },
  });
}

export function useConfigYaml(configId: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["configYaml", configId],
    queryFn: () => api.getConfigYaml(configId),
    enabled: health.data === true && !!configId,
  });
}

export function useAddAnnotation(runId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ann: Annotation) => api.addAnnotation(runId, ann),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.bundle(runId) }),
  });
}
