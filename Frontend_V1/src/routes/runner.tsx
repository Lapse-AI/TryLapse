import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useJobs, useTriggerJob, useConfigs, useApiHealth } from "@/lib/api/hooks";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { useTestGroup } from "@/hooks/use-test-group";
import { ActiveJobsBanner, JobQueueTable } from "@/components/job-queue-status";
import { Loader2, Play, Network, FlaskConical, Settings } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/runner")({
  head: () => ({ meta: [{ title: "Runner — Launch Rehearsal" }] }),
  component: RunnerPage,
});

function RunnerPage() {
  const { data: live } = useApiHealth();
  const { data: jobs = [] } = useJobs();
  const { data: configs = [] } = useConfigs();
  const trigger = useTriggerJob();
  const { isSignedIn, group, resolvedConfigId } = useTestGroup();
  const { configId, pickConfig } = usePersistedConfigId();
  const [useLlm, setUseLlm] = useState(true);

  const selectedConfig =
    configs.find((c) => c.id === configId) ?? configs.find((c) => c.id === "lr-self") ?? configs[0];

  const selfConfig =
    configs.find((c) => c.id === "lr-self") ?? configs.find((c) => c.id === "self-dashboard");

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

  return (
    <div>
      <PageHeader
        eyebrow="author & rehearse"
        title="Run & crawl triggers"
        description="POST /api/jobs — background CLI runs with live status. Pick a config, then run or crawl."
        actions={
          <Link
            to="/config"
            className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
          >
            <Settings className="size-3.5" /> Config (YAML)
          </Link>
        }
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <ActiveJobsBanner jobs={jobs} />

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
            {jobs.some((j) => j.status === "running" || j.status === "queued") && (
              <Chip tone="info">Job in progress</Chip>
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
              {configs.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} ({c.source})
                </option>
              ))}
            </select>
            <p className="text-[11px] text-muted-foreground mt-2">
              Edit on{" "}
              <Link to="/config" className="text-primary hover:underline">
                Config (YAML)
              </Link>
              . Selection persists across Sitemap, Workflows, and Runner.
              {isSignedIn && " Switch test group in the top bar to change the default config."}
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

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border font-display font-semibold">Job queue</div>
          <JobQueueTable jobs={jobs} />
        </Panel>
      </div>
    </div>
  );
}
