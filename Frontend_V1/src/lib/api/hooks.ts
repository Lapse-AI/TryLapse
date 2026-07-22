import { useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import type {
  Annotation,
  LibraryPersona,
  RunBundle,
  RunDiff,
  RunSummary,
  Workspace,
} from "@/lib/mock-data/types";
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
  trends: (prefix?: string) => ["rehearse", "trends", prefix ?? ""] as const,
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
  personaLibrary: ["rehearse", "persona-library"] as const,
  personaLibraryItem: (id: string) => ["rehearse", "persona-library", id] as const,
  findingOutcomes: (runId: string) => ["rehearse", "finding-outcomes", runId] as const,
  authMe: ["rehearse", "auth-me"] as const,
  myWorkspaces: ["rehearse", "my-workspaces"] as const,
  workspaceMembers: (slug: string) => ["rehearse", "workspace-members", slug] as const,
  workspaceInvites: (slug: string) => ["rehearse", "workspace-invites", slug] as const,
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
    // Poll every 5s while the orchestrator is still writing partial bundles
    refetchInterval: (q) => (q.state.data?.summary?.partial === true ? 5000 : false),
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
  const ws = getWorkspace();
  const configPrefix = ws?.configPath
    ? (ws.configPath.split("/").pop() ?? "").replace(/\.ya?ml$/i, "").split("-")[0] || undefined
    : undefined;
  return useQuery({
    queryKey: queryKeys.trends(configPrefix),
    queryFn: async () => {
      if (live) return api.trends(configPrefix);
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
    staleTime: 2 * 60 * 1000,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
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

export function useAuthMe() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.authMe,
    queryFn: () => api.authMe(),
    enabled: health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name?: string; currentPassword?: string; newPassword?: string }) =>
      api.updateProfile(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.authMe }),
  });
}

export function useWorkspaceMembers(slug: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.workspaceMembers(slug),
    queryFn: () => api.workspaceMembers(slug),
    enabled: !!slug && health.isSuccess && !!health.data,
  });
}

export function useWorkspaceInvites(slug: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.workspaceInvites(slug),
    queryFn: () => api.workspaceInvites(slug),
    enabled: !!slug && health.isSuccess && !!health.data,
  });
}

export function useInviteToWorkspace(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ email, role }: { email: string; role: "owner" | "member" | "viewer" }) =>
      api.inviteToWorkspace(slug, email, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.workspaceInvites(slug) }),
  });
}

export function useRemoveWorkspaceMember(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => api.removeWorkspaceMember(slug, userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.workspaceMembers(slug) }),
  });
}

export function useMyWorkspaces() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.myWorkspaces,
    queryFn: () => api.myWorkspaces(),
    enabled: health.isSuccess && !!health.data,
  });
}

export function useWorkspaceUsage(slug: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "workspace-usage", slug] as const,
    queryFn: () => api.workspaceUsage(slug),
    enabled: !!slug && health.isSuccess && !!health.data,
  });
}

export function useAdminSummary() {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-summary"] as const,
    queryFn: () => api.adminSummary(),
    enabled: health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useAdminWorkspaces() {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-workspaces"] as const,
    queryFn: () => api.adminWorkspaces(),
    enabled: health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useAdminUsers() {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-users"] as const,
    queryFn: () => api.adminUsers(),
    enabled: health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useAdminActivity(limit = 50) {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-activity", limit] as const,
    queryFn: () => api.adminActivity(limit),
    enabled: health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useAdminLiveJobs() {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-live"] as const,
    queryFn: () => api.adminLiveJobs(),
    enabled: health.isSuccess && !!health.data,
    retry: false,
    refetchInterval: 5000,
  });
}

export function useAdminFailures(limit = 200) {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-failures", limit] as const,
    queryFn: () => api.adminFailures(limit),
    enabled: health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useAdminWorkspaceDetail(slug: string | undefined) {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "admin-workspace-detail", slug] as const,
    queryFn: () => api.adminWorkspaceDetail(slug!),
    enabled: health.isSuccess && !!health.data && !!slug,
    retry: false,
  });
}

export function useCaseStudy(slug: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: ["rehearse", "case-study", slug] as const,
    queryFn: () => api.caseStudy(slug),
    enabled: !!slug && health.isSuccess && !!health.data,
    retry: false,
  });
}

export function useCreateCheckoutSession() {
  return useMutation({
    mutationFn: ({ plan, workspaceSlug }: { plan: string; workspaceSlug: string }) =>
      api.createCheckoutSession(plan, workspaceSlug),
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

function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    void Notification.requestPermission();
  }
}

function fireRunNotification(title: string, body: string, runId?: string) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const n = new Notification(title, {
    body,
    icon: "/favicon.ico",
    tag: runId ?? "rehearsal-run",
  });
  if (runId) {
    n.onclick = () => {
      window.focus();
      window.location.href = `/runs/${runId}`;
    };
  }
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
          fireRunNotification(
            "Rehearsal complete",
            `Run ${j.runId} finished. Open to view the scorecard.`,
            j.runId,
          );
        } else if (now === "failed") {
          toast.error(j.error?.slice(0, 120) || `Job ${j.id} failed`);
          fireRunNotification("Rehearsal failed", j.error?.slice(0, 100) || `Job ${j.id} failed`);
        }
        refreshedRuns = true;
      }
      prevStatusRef.current[j.id] = now;
    }

    if (refreshedRuns) {
      void qc.invalidateQueries({ queryKey: queryKeys.summaries });
      void qc.invalidateQueries({ queryKey: ["rehearse", "trends"] });
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
      // Ask permission to send an OS notification when this run completes
      requestNotificationPermission();
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

// ── Persona Library hooks ───────────────────────────────────────────────────
// These hit /api/persona-library, a workspace-global persona store that
// lives in artifacts/personas.json.  Personas saved here can be imported
// into any config without re-describing them from scratch.

/** Fetch all library personas.  Polls every 60s to stay fresh. */
export function usePersonaLibrary() {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.personaLibrary,
    queryFn: () => api.listPersonaLibrary(),
    enabled: health.data === true,
    staleTime: 60_000,
  });
}

/** Save (create or update) a persona in the library. */
export function useSavePersonaLibrary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: Partial<LibraryPersona> & { name: string; role: string }) =>
      api.savePersonaLibrary(p),
    onSuccess: (saved) => {
      void qc.invalidateQueries({ queryKey: queryKeys.personaLibrary });
      void qc.invalidateQueries({ queryKey: queryKeys.personaLibraryItem(saved.id) });
      toast.success(`Persona "${saved.name}" saved to library`);
    },
  });
}

/** AI-generate a rich behavioral persona and optionally save it. */
export function useGeneratePersona() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      prompt: string;
      productName?: string;
      targetUrl?: string;
      save?: boolean;
    }) => api.generatePersonaLibrary(body),
    onSuccess: (result, variables) => {
      if (variables.save) {
        void qc.invalidateQueries({ queryKey: queryKeys.personaLibrary });
        toast.success(`Persona "${result.persona.name}" generated and saved`);
      }
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Generation failed");
    },
  });
}

/** Bulk-import all personas from a config into the library. */
export function useImportPersonasFromConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (configId: string) => api.importPersonasFromConfig(configId),
    onSuccess: (result) => {
      void qc.invalidateQueries({ queryKey: queryKeys.personaLibrary });
      toast.success(
        `Imported ${result.imported} persona${result.imported !== 1 ? "s" : ""} into library`,
      );
    },
  });
}

/** Delete a persona from the library. */
export function useDeletePersonaLibrary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deletePersonaLibrary(id),
    onSuccess: (_, id) => {
      void qc.invalidateQueries({ queryKey: queryKeys.personaLibrary });
      void qc.invalidateQueries({ queryKey: queryKeys.personaLibraryItem(id) });
    },
  });
}

/** A5: Per-finding outcomes for severity calibration. */
export function useFindingOutcomes(runId: string) {
  const health = useApiHealth();
  return useQuery({
    queryKey: queryKeys.findingOutcomes(runId),
    queryFn: () => api.findingOutcomes(runId),
    enabled: !!runId && health.data === true,
    staleTime: 60_000,
  });
}

export function useSetFindingOutcome(runId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ findingId, outcome }: { findingId: string; outcome: string }) =>
      api.setFindingOutcome(runId, findingId, outcome),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.findingOutcomes(runId) });
    },
  });
}
