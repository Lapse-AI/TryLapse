import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, StatusDot, ClientTime } from "@/components/ui-bits";
import { formatDuration } from "@/lib/mock-data";
import { useRunSummaries } from "@/lib/api/hooks";
import { GitCompare } from "lucide-react";

export const Route = createFileRoute("/runs/")({
  head: () => ({ meta: [{ title: "Runs — Launch Rehearsal" }] }),
  component: RunsList,
});

function RunsList() {
  const { data: runSummaries = [] } = useRunSummaries();
  const latest = runSummaries[0];
  const previous = runSummaries[1];

  return (
    <div>
      <PageHeader
        eyebrow="runs"
        title="Run history"
        description="Every rehearsal, every environment. Includes backend-shaped runs (enterprise-*, cal-*)."
        actions={
          previous && (
            <Link to="/compare" search={{ a: previous.id, b: latest.id }} className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5">
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
              {runSummaries.map((r) => (
                <tr key={r.id} className="border-b border-border last:border-0 hover:bg-surface-2/40">
                  <td className="px-5 py-3"><Link to="/runs/$runId" params={{ runId: r.id }} className="font-mono text-xs text-primary hover:underline">{r.id}</Link></td>
                  <td className="px-5 py-3 text-xs">{r.productName}</td>
                  <td className="px-5 py-3 font-mono text-xs">{r.target}</td>
                  <td className="px-5 py-3"><Chip tone={r.env === "prod-canary" ? "violet" : r.env === "staging" ? "info" : "neutral"}>{r.env}</Chip></td>
                  <td className="px-5 py-3"><div className="flex items-center gap-2"><StatusDot status={r.status} /><span className="font-mono tabular-nums">{r.readiness}</span><span className="text-[10px] text-muted-foreground">{r.readinessBand}</span></div></td>
                  <td className="px-5 py-3 font-mono tabular-nums text-danger">{r.blockers}</td>
                  <td className="px-5 py-3 font-mono tabular-nums text-ready">{r.delights}</td>
                  <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">{r.pages || "—"}</td>
                  <td className="px-5 py-3 font-mono text-muted-foreground">{formatDuration(r.durationSec)}</td>
                  <td className="px-5 py-3 font-mono text-muted-foreground tabular-nums">${r.agentCost.toFixed(2)}</td>
                  <td className="px-5 py-3 text-right text-muted-foreground text-xs"><ClientTime iso={r.startedAt} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}
