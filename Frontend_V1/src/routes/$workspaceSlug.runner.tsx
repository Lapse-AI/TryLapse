import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useJobs, useTriggerJob, useConfigs, useApiHealth, useConfigYaml } from "@/lib/api/hooks";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { useTestGroup } from "@/hooks/use-test-group";
import { getWorkspace } from "@/lib/workspace";
import { ActiveJobsBanner, JobQueueTable } from "@/components/job-queue-status";
import { VariantRehearsalPanel } from "@/components/variant-rehearsal-panel";
import { CohortRehearsalPanel } from "@/components/cohort-rehearsal-panel";
import { RunLiveGraph } from "@/components/run-live-graph";
import { CrawlLiveGraph } from "@/components/crawl-live-graph";
import { Loader2, Play, Network, FlaskConical, Settings, AlertTriangle, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

export const Route = createFileRoute("/$workspaceSlug/runner")({
  head: () => ({ meta: [{ title: "Runner — Launch Rehearsal" }] }),
  component: RunnerPage,
});

function RunnerPage() {
  const { workspaceSlug } = Route.useParams();
  const { data: live } = useApiHealth();
  const { data: jobs = [] } = useJobs();
  const { data: configs = [] } = useConfigs();
  const trigger = useTriggerJob();
  const { isSignedIn, group, resolvedConfigId } = useTestGroup();
  const { configId, pickConfig } = usePersistedConfigId();
  const workspace = getWorkspace();
  const configHref = workspace?.slug ? `/${workspace.slug}/config` : "/config";
  const [useLlm, setUseLlm] = useState(true);
  const [discoveredRunId, setDiscoveredRunId] = useState<string | undefined>();

  const { data: creds } = useQuery({
    queryKey: ["credentials"],
    queryFn: () => api.getCredentials(),
    enabled: !!live,
    refetchInterval: 5000,
  });

  // Derive workspace run_id_prefix from the saved configPath
  const wsConfigId = workspace?.configPath
    ? (workspace.configPath.split("/").pop()?.replace(/\.ya?ml$/, "") ?? "")
    : "";
  const wsPrefix = wsConfigId.replace(/-\d{8}-\d{6}$/, "");

  // Filter jobs to this workspace only — runId starts with wsPrefix, or job not yet started
  const wsJobs = wsPrefix
    ? jobs.filter((j) => !j.runId || j.runId.startsWith(wsPrefix))
    : jobs;

  // Filter to workspace-relevant configs only (skip unrelated and example configs)
  const wsConfigs = wsPrefix
    ? configs.filter((c) => c.source !== "example" && c.id.startsWith(wsPrefix))
    : configs.filter((c) => c.source !== "example");

  // Sort timestamped configs newest-first
  const timestamped = [...wsConfigs.filter((c) => /\d{8}-\d{6}$/.test(c.id))]
    .sort((a, b) => ((b as { mtime?: number }).mtime ?? 0) - ((a as { mtime?: number }).mtime ?? 0) || b.id.localeCompare(a.id));
  const canonical = wsConfigs.filter((c) => !/\d{8}-\d{6}$/.test(c.id));
  const latestId = timestamped[0]?.id ?? null;
  const displayConfigs = [...timestamped, ...canonical];

  // Workspace-linked config ID (what workspace.json points to — the authoritative source)
  const wsLinkedId = wsConfigId || null;

  // Prefer: explicit user pick (if in wsConfigs) → workspace-linked config → latest timestamped → first
  const selectedConfig =
    wsConfigs.find((c) => c.id === configId) ??
    (wsLinkedId ? wsConfigs.find((c) => c.id === wsLinkedId) : undefined) ??
    (latestId ? wsConfigs.find((c) => c.id === latestId) : undefined) ??
    wsConfigs[0] ??
    configs[0];

  const { data: configFile } = useConfigYaml(selectedConfig?.id ?? "");

  const selfConfig =
    wsConfigs.find((c) => c.id === "lr-self") ?? configs.find((c) => c.id === "self-dashboard");

  const runSelected = () => {
    if (!selectedConfig) {
      toast.error("No config selected — generate one on Init or pick in Config (YAML)");
      return;
    }
    trigger.mutate({ mode: "run", configPath: selectedConfig.path, llm: useLlm });
  };

  const runSelfTest = () => {
    if (!selfConfig) {
      toast.error("No self-test config — use Init → Dogfood to generate lr-self.yaml first");
      return;
    }
    pickConfig(selfConfig.id);
    trigger.mutate({ mode: "run", configPath: selfConfig.path, llm: useLlm });
  };

  const hasInteractiveHint =
    selectedConfig &&
    (selectedConfig.id.includes("enterprise") ||
      selectedConfig.id === "lr-self" ||
      selectedConfig.name.toLowerCase().includes("self"));

  const configHasAuth = configFile?.yaml ? configFile.yaml.includes("\nauth:") || configFile.yaml.startsWith("auth:") : null;
  const credsOk = creds ? creds.hasEmail && creds.hasPassword : null;
  const authReady = configHasAuth && credsOk;

  return (
    <div>
      <PageHeader
        eyebrow="author & rehearse"
        title="Run & crawl triggers"
        description="POST /api/jobs — background CLI runs with live status. Pick a config, then run or crawl."
        actions={
          <Link
            to={configHref}
            className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
          >
            <Settings className="size-3.5" /> Config (YAML)
          </Link>
        }
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <ActiveJobsBanner jobs={wsJobs} workspaceSlug={workspaceSlug} />

        {/* Live run + crawl visualization — shown when a run is in progress */}
        {wsJobs.some(j => j.status === "running") && (() => {
          const liveJob = wsJobs.find(j => j.status === "running");
          // Use runId from job record OR from live progress (whichever is available first)
          const effectiveRunId = liveJob?.runId ?? discoveredRunId;
          return (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <Panel className="p-5">
                <div className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  Live journeys
                </div>
                <RunLiveGraph
                  runId={effectiveRunId}
                  pollingMs={2000}
                  jobId={liveJob?.id}
                  onRunIdDiscovered={setDiscoveredRunId}
                />
              </Panel>
              <Panel className="p-5">
                <div className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-info animate-pulse" />
                  Live crawl graph
                </div>
                {effectiveRunId ? (
                  <CrawlLiveGraph runId={effectiveRunId} pollingMs={1500} />
                ) : (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="size-3 animate-spin" /> Waiting for run ID…
                  </div>
                )}
              </Panel>
            </div>
          );
        })()}

        <Panel className="p-5 space-y-4">
          <div className="text-sm font-medium">Readiness</div>
          <div className="flex flex-wrap gap-2">
            <Chip tone={live ? "ready" : "danger"}>{live ? "API live" : "API offline"}</Chip>
            <Chip tone={selectedConfig ? "ready" : "warn"}>
              {selectedConfig ? `Config: ${selectedConfig.id}` : "No config"}
            </Chip>
            {isSignedIn && (
              <Chip tone="violet">
                Test group · {group.label} ({resolvedConfigId})
              </Chip>
            )}
            {wsJobs.some((j) => j.status === "running" || j.status === "queued") && (
              <Chip tone="info">Job in progress</Chip>
            )}
            {live && creds && (
              <Chip tone={credsOk ? "ready" : "warn"}>
                {credsOk ? "Credentials set" : "No credentials"}
              </Chip>
            )}
            {live && configHasAuth !== null && (
              <Chip tone={configHasAuth ? "ready" : "warn"}>
                {configHasAuth ? "Auth block present" : "No auth block in YAML"}
              </Chip>
            )}
          </div>
          {!live && (
            <p className="text-xs text-muted-foreground">
              Start API:{" "}
              <code className="font-mono">
                ./rehearse serve -o launch-rehearsal/artifacts --port 8765
              </code>
            </p>
          )}
        </Panel>

        <Panel className="p-5 space-y-4">
          <div>
            <label htmlFor="runner-config-id" className="text-xs text-muted-foreground mb-1 block">
              Config to run
            </label>
            <select
              id="runner-config-id"
              aria-label="Config to run"
              className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm font-mono min-w-[240px]"
              value={selectedConfig?.id ?? ""}
              onChange={(e) => pickConfig(e.target.value)}
              disabled={!configs.length}
            >
              {displayConfigs.map((c) => {
                const tsMatch = c.id.match(/^(.+)-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$/);
                const isLatest = c.id === latestId;
                let label = c.id;
                if (tsMatch) {
                  const dt = new Date(`${tsMatch[2]}-${tsMatch[3]}-${tsMatch[4]}T${tsMatch[5]}:${tsMatch[6]}:${tsMatch[7]}Z`);
                  const localStr = isNaN(dt.getTime()) ? `${tsMatch[2]}-${tsMatch[3]}-${tsMatch[4]} ${tsMatch[5]}:${tsMatch[6]}`
                    : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true }).format(dt);
                  label = `${tsMatch[1]} · ${localStr}${isLatest ? " (latest)" : ""}`;
                }
                return (
                  <option key={c.id} value={c.id}>
                    {label}
                  </option>
                );
              })}
            </select>
            {selectedConfig && (
              <div className="mt-2 rounded-md bg-surface-2 border border-border px-3 py-2 space-y-1">
                <div className="text-[11px] text-muted-foreground">
                  File: <code className="font-mono text-foreground">configs/{selectedConfig.id}.yaml</code>
                </div>
                <div className="text-[11px] font-mono text-muted-foreground/80 select-all break-all">
                  ./rehearse run -c launch-rehearsal/artifacts/configs/{selectedConfig.id}.yaml -o launch-rehearsal/artifacts/
                </div>
              </div>
            )}
            <p className="text-[11px] text-muted-foreground mt-2">
              Edit on{" "}
              <Link to={configHref} className="text-primary hover:underline">
                Config (YAML)
              </Link>
              . Selection persists across Sitemap, Workflows, and Runner.
            </p>
            {hasInteractiveHint && (
              <p className="text-[11px] text-muted-foreground mt-1">
                Tip: configs with <span className="font-mono">click</span> /{" "}
                <span className="font-mono">fill</span> steps produce compare focus boxes;
                navigate-only runs may show empty visual diff.
              </p>
            )}
          </div>
          <label htmlFor="runner-use-llm" className="flex items-center gap-2 text-sm">
            <input
              id="runner-use-llm"
              type="checkbox"
              checked={useLlm}
              onChange={(e) => setUseLlm(e.target.checked)}
            />
            LLM enrichment (personas + summaries) — reads DEEPSEEK_API_KEY from repo .env
          </label>
          {live && configHasAuth !== null && (!credsOk || !configHasAuth) && (
            <div className="flex items-start gap-2 rounded-md border border-warn/40 bg-warn/5 px-3 py-2 text-[11px] text-warn">
              <AlertTriangle className="size-3.5 mt-0.5 shrink-0" />
              <span>
                {!configHasAuth && !credsOk
                  ? "Missing credentials and auth block — run will skip login. "
                  : !configHasAuth
                    ? "No auth block in this config YAML — run will skip login. "
                    : "Credentials not set — run will skip login. "}
                <Link to={configHref} className="underline hover:text-foreground">
                  Fix on Config page
                </Link>
              </span>
            </div>
          )}
          {live && authReady && (
            <div className="flex items-center gap-2 rounded-md border border-ready/40 bg-ready/5 px-3 py-2 text-[11px] text-ready">
              <CheckCircle2 className="size-3.5 shrink-0" />
              Auth ready — credentials set and auth block present in config.
            </div>
          )}
          <div className="flex flex-wrap gap-3 items-center">
            <button
              type="button"
              disabled={!live || trigger.isPending || !selectedConfig}
              onClick={runSelected}
              className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground inline-flex items-center gap-2 disabled:opacity-50"
            >
              {trigger.isPending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Play className="size-3.5" />
              )}
              Run selected config
            </button>
            <button
              type="button"
              disabled={!live || trigger.isPending || !selfConfig}
              onClick={runSelfTest}
              className="text-xs px-4 py-2 rounded-md border border-primary/50 bg-primary/10 inline-flex items-center gap-2 disabled:opacity-50"
            >
              {trigger.isPending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <FlaskConical className="size-3.5" />
              )}
              Run self-test (this UI)
            </button>
            <button
              type="button"
              disabled={!live || trigger.isPending}
              onClick={() => trigger.mutate({ mode: "crawl" })}
              className="text-xs px-4 py-2 rounded-md border border-border inline-flex items-center gap-2 disabled:opacity-50"
            >
              <Network className="size-3.5" /> Crawl only
            </button>
          </div>
        </Panel>

        <VariantRehearsalPanel live={!!live} />
        <CohortRehearsalPanel live={!!live} />

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border font-display font-semibold">Job queue</div>
          <JobQueueTable jobs={wsJobs} workspaceSlug={workspaceSlug} />
        </Panel>
      </div>
    </div>
  );
}
