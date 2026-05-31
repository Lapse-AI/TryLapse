import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { useJobs, useTriggerJob, useConfigs, useApiHealth } from "@/lib/api/hooks";
import { Loader2, Play, Network } from "lucide-react";

export const Route = createFileRoute("/runner")({
  head: () => ({ meta: [{ title: "Runner — Launch Rehearsal" }] }),
  component: RunnerPage,
});

function RunnerPage() {
  const { data: live } = useApiHealth();
  const { data: jobs = [] } = useJobs();
  const { data: configs = [] } = useConfigs();
  const trigger = useTriggerJob();

  return (
    <div>
      <PageHeader
        eyebrow="monitor"
        title="Run & crawl triggers"
        description="POST /api/jobs — background CLI runs with live status. Parallel journey seeds, repeat micro-loop, and viewport profiles come from rehearse.yaml."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-5 flex flex-wrap gap-3 items-center">
          <button
            type="button"
            disabled={!live || trigger.isPending}
            onClick={() => trigger.mutate({ mode: "run" })}
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
