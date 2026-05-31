import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
} from "@/lib/mock-data";
import { api, checkApiHealth } from "./client";

export const queryKeys = {
  health: ["rehearse", "health"] as const,
  summaries: ["rehearse", "summaries"] as const,
  bundle: (id: string) => ["rehearse", "bundle", id] as const,
  diff: (a: string, b: string) => ["rehearse", "diff", a, b] as const,
  trends: ["rehearse", "trends"] as const,
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
      return mockSummaries;
    },
    enabled: health.isSuccess,
    placeholderData: live ? undefined : mockSummaries,
  });
}

export function useLatestRun(): RunSummary | undefined {
  const health = useApiHealth();
  const { data } = useRunSummaries();
  if (health.data === true) return data?.[0];
  return data?.[0] ?? mockLatest();
}

export function useRunBundle(runId: string) {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.bundle(runId),
    queryFn: async (): Promise<RunBundle> => {
      if (live) return api.bundle(runId);
      const mock = mockBundle(runId);
      if (!mock) throw new Error("Run not found");
      return mock;
    },
    enabled: !!runId && health.isSuccess,
    placeholderData: live ? undefined : getRunBundle(runId),
  });
}

export function useRunDiff(runA: string, runB: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.diff(runA, runB),
    queryFn: async (): Promise<RunDiff> => {
      if (health.data) return api.diff(runA, runB);
      const mock = mockDiff(runA, runB);
      if (!mock) throw new Error("Could not diff");
      return mock;
    },
    enabled: !!runA && !!runB && health.isSuccess,
  });
}

export function useTrends() {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.trends,
    queryFn: async () => {
      if (live) return api.trends();
      return {
        readiness: mockReadinessTrend,
        pages: mockCrawlTrend,
        flakeRate: mockFlakeTrend,
        runIds: mockSummaries.map((r) => r.id),
        labels: mockSummaries.map((r) => r.startedAt.slice(0, 10)),
      };
    },
    enabled: health.isSuccess,
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
    queryFn: async () => (health.data ? api.workspace() : mockWorkspace),
    enabled: health.isSuccess,
    placeholderData: mockWorkspace,
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
    queryFn: async () => (health.data ? api.integrations() : mockIntegrations),
    enabled: health.isSuccess,
    placeholderData: mockIntegrations,
  });
}

export function useAlerts() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: async () => (health.data ? api.alerts() : mockAlerts),
    enabled: health.isSuccess,
    placeholderData: mockAlerts,
  });
}

export function useBacklog() {
  const health = useApiHealth();
  const live = health.data === true;
  return useQuery({
    queryKey: queryKeys.backlog,
    queryFn: async () => (live ? api.backlog() : mockBacklog),
    enabled: health.isSuccess,
    placeholderData: live ? undefined : mockBacklog,
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

export function useJobs() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.jobs,
    queryFn: () => api.jobs(),
    enabled: health.data === true,
    refetchInterval: 5000,
  });
}

export function useTriggerJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.triggerJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.jobs }),
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

export function useAddAnnotation(runId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ann: Annotation) => api.addAnnotation(runId, ann),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.bundle(runId) }),
  });
}
