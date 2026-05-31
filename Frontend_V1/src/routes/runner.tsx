import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useJobs, useTriggerJob, useConfigs, useApiHealth } from "@/lib/api/hooks";
import { Loader2, Play, Network, FlaskConical } from "lucide-react";
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
  const [useLlm, setUseLlm] = useState(true);

  const selfConfig =
    configs.find((c) => c.id === "lr-self") ??
    configs.find((c) => c.id === "self-dashboard");

  const runSelfTest = () => {
    if (!selfConfig) {
      toast.error("No self-test config — use Init → Dogfood to generate lr-self.yaml first");
      return;
    }
    trigger.mutate({ mode: "run", configPath: selfConfig.path, llm: useLlm });
  };

  return (
    <div>
      <PageHeader
        eyebrow="monitor"
        title="Run & crawl triggers"
        description="POST /api/jobs — background CLI runs with live status. Parallel journey seeds, repeat micro-loop, and viewport profiles come from rehearse.yaml."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-5 space-y-4">
          <div className="text-sm text-muted-foreground">
            Dogfood: generate <span className="font-mono text-xs">lr-self.yaml</span> on{" "}
            <Link to="/init" className="text-primary underline-offset-2 hover:underline">
              Init
            </Link>{" "}
            with <span className="font-mono text-xs">http://127.0.0.1:8081</span>, then run below.
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
            onClick={() => trigger.mutate({ mode: "run", llm: useLlm })}
            className="text-xs px-4 py-2 rounded-md bg-primary text-primary-foreground inline-flex items-center gap-2 disabled:opacity-50"
          >
            {trigger.isPending ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Play className="size-3.5" />
            )}
            Run full rehearsal
          </button>
          <button
            type="button"
            disabled={!live || trigger.isPending}
            onClick={() => trigger.mutate({ mode: "crawl" })}
            className="text-xs px-4 py-2 rounded-md border border-border inline-flex items-center gap-2 disabled:opacity-50"
          >
            <Network className="size-3.5" /> Crawl only
          </button>
          {!live && (
            <Chip tone="warn">Start API: rehearse serve -o launch-rehearsal/artifacts</Chip>
          )}
          {live && !selfConfig && (
            <Chip tone="warn">Self-test config missing — open Init → Dogfood</Chip>
          )}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border font-display font-semibold">Job queue</div>
          {jobs.length === 0 ? (
            <div className="p-8 text-sm text-muted-foreground text-center">
              No jobs yet — trigger a run above.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground border-b border-border">
                <tr>
                  <th className="text-left px-5 py-2">Job</th>
                  <th className="text-left px-5 py-2">Mode</th>
                  <th className="text-left px-5 py-2">Status</th>
                  <th className="text-left px-5 py-2">Run ID</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3 font-mono text-xs">{j.id}</td>
                    <td className="px-5 py-3">{j.mode}</td>
                    <td className="px-5 py-3">
                      <Chip
                        tone={
                          j.status === "done" ? "ready" : j.status === "failed" ? "danger" : "info"
                        }
                      >
                        {j.status}
                      </Chip>
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">{j.runId ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel className="p-5">
          <div className="text-xs text-muted-foreground mb-3">Available configs</div>
          <ul className="space-y-2 text-sm font-mono">
            {configs.map((c) => (
              <li key={c.id} className="flex items-center gap-2">
                <Chip tone={c.source === "example" ? "info" : "neutral"}>{c.source}</Chip>
                {c.name}
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
