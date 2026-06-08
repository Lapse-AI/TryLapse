import { createFileRoute, Link, useParams } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, StatusDot, ClientTime } from "@/components/ui-bits";
import { formatDuration } from "@/lib/mock-data";
import { useScopedRunSummaries, useScopedActiveJobs } from "@/lib/api/hooks";
import { RunHistoryLiveRows } from "@/components/run-history-live-rows";
import { GitCompare, Play, Loader2, Rocket } from "lucide-react";
import { getWorkspace } from "@/lib/workspace";
import { useTriggerJob, useApiHealth } from "@/lib/api/hooks";

export const Route = createFileRoute("/$workspaceSlug/runs/")({
  head: () => ({ meta: [{ title: "Runs — TryLapse" }] }),
  component: RunsList,
});

function RunsList() {
  const { workspaceSlug } = useParams({ from: "/$workspaceSlug/runs/" });
  const { data: runSummaries = [], allRuns } = useScopedRunSummaries();
  const { data: activeJobs = [] } = useScopedActiveJobs();
  const trigger = useTriggerJob();
  const { data: live } = useApiHealth();
  const userWorkspace = getWorkspace();
  const latest = runSummaries[0];
  const previous = runSummaries[1];

  const productLabel = userWorkspace?.productName ?? userWorkspace?.name ?? "your product";
  const targetLabel = userWorkspace?.targetUrl ?? "";

  if (runSummaries.length === 0 && activeJobs.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="max-w-md w-full text-center">
          <div className="size-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-5">
            <Rocket className="size-8 text-primary" />
          </div>
          <h2 className="font-display text-2xl font-semibold mb-2">No runs yet</h2>
          <p className="text-sm text-muted-foreground mb-8">
            Trigger your first rehearsal to see results here. Runs will be scoped to{" "}
            <span className="font-mono text-foreground text-xs">
              {targetLabel || workspaceSlug}
            </span>
            .
          </p>
          <button
            type="button"
            onClick={() => trigger.mutate({ mode: "run" })}
            disabled={!live || trigger.isPending}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {trigger.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Play className="size-4" />
            )}
            {trigger.isPending ? "Queuing run…" : "Run rehearsal"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="runs"
        title="Run history"
        description={`${activeJobs.length ? `${activeJobs.length} live · ` : ""}${runSummaries.length} completed for ${productLabel}${allRuns.length !== runSummaries.length ? ` (${allRuns.length} total across all workspaces)` : ""}.`}
        actions={
          previous &&
          latest && (
            <Link
              to="/compare"
              search={{ a: previous.id, b: latest.id }}
              className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
            >
              <GitCompare className="size-3.5" /> Diff last two
            </Link>
          )
        }
      />
      <div className="p-8 max-w-[1400px]">
        <Panel className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr className="border-b border-border bg-surface-2/40">
                <th className="text-left px-5 py-2.5 font-medium">Run ID</th>
                <th className="text-left px-5 py-2.5 font-medium">Product</th>
                <th className="text-left px-5 py-2.5 font-medium">Target</th>
                <th className="text-left px-5 py-2.5 font-medium">Env</th>
                <th className="text-left px-5 py-2.5 font-medium">Readiness</th>
                <th className="text-left px-5 py-2.5 font-medium">Blockers</th>
                <th className="text-left px-5 py-2.5 font-medium">Delights</th>
                <th className="text-left px-5 py-2.5 font-medium">Pages</th>
                <th className="text-left px-5 py-2.5 font-medium">Duration</th>
                <th className="text-left px-5 py-2.5 font-medium">Cost</th>
                <th className="text-right px-5 py-2.5 font-medium">Started</th>
              </tr>
            </thead>
            <tbody>
              <RunHistoryLiveRows jobs={activeJobs} group={{ label: productLabel, targetUrl: targetLabel }} />
              {runSummaries.map((r) => (
                <tr
                  key={r.id}
                  className="border-b border-border last:border-0 hover:bg-surface-2/40"
                >
                  <td className="px-5 py-3">
                    <Link
                      to="/$workspaceSlug/runs/$runId"
                      params={{ workspaceSlug, runId: r.id }}
                      className="font-mono text-xs text-primary hover:underline"
                    >
                      {r.id}
                    </Link>
                  </td>
                  <td className="px-5 py-3 text-xs">{r.productName}</td>
                  <td className="px-5 py-3 font-mono text-xs">{r.target}</td>
                  <td className="px-5 py-3">
                    <Chip
                      tone={
                        r.env === "prod-canary"
                          ? "violet"
                          : r.env === "staging"
                            ? "info"
                            : "neutral"
                      }
                    >
                      {r.env}
                    </Chip>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <StatusDot status={r.status} />
                      <span className="font-mono tabular-nums">{r.readiness}</span>
                      <span className="text-[11px] text-muted-foreground">{r.readinessBand}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 font-mono tabular-nums text-danger">{r.blockers}</td>
                  <td className="px-5 py-3 font-mono tabular-nums text-ready">{r.delights}</td>
                  <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">
                    {r.pages || "—"}
                  </td>
                  <td className="px-5 py-3 font-mono text-muted-foreground">
                    {formatDuration(r.durationSec)}
                  </td>
                  <td className="px-5 py-3 font-mono text-muted-foreground tabular-nums">
                    ${r.agentCost.toFixed(2)}
                  </td>
                  <td className="px-5 py-3 text-right text-muted-foreground text-xs">
                    <ClientTime iso={r.startedAt} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}
