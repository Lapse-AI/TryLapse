import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { workflowCoverage, suggestedJourneys, journeys } from "@/lib/mock-data";
import { useLatestRun, useRunBundle } from "@/lib/api/hooks";
import { Plus, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/workflows")({
  head: () => ({ meta: [{ title: "Workflows — Launch Rehearsal" }] }),
  component: Workflows,
});

function Workflows() {
  const latest = useLatestRun();
  const { data: bundle } = useRunBundle(latest?.id ?? "");
  if (!latest || !bundle) return null;
  const wfAgent = bundle.agents.find((a) => a.id === "ag_wf" || a.name === "Workflow");

  return (
    <div>
      <PageHeader
        eyebrow="map · workflows"
        title="Workflow map"
        description="Patterns auto-detected from crawl (Workflow agent). Coverage shows whether journeys exercise them."
        actions={wfAgent && <Chip tone="info">{wfAgent.lastSummary}</Chip>}
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {workflowCoverage.map((w) => {
            const tone = w.coverage >= 90 ? "ready" : w.coverage >= 70 ? "warn" : "danger";
            return (
              <Panel key={w.category} className="p-5">
                <div className="flex items-center justify-between">
                  <div className="font-display text-lg font-semibold capitalize">{w.category}</div>
                  <Chip tone={tone}>{w.coverage}% covered</Chip>
                </div>
                <div className="mt-3 h-1.5 w-full rounded-full bg-surface-3 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${w.coverage}%`, background: `var(--${tone})` }} />
                </div>
                <div className="mt-3 text-[11px] font-mono text-muted-foreground truncate">{w.paths.join(" · ")}</div>
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground font-mono">
                  <span>{w.journeys} journey{w.journeys === 1 ? "" : "s"}</span>
                  {w.suggested > 0 && <span className="text-warn">+{w.suggested} suggested</span>}
                </div>
              </Panel>
            );
          })}
        </div>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-4">Active journeys · from rehearse.yaml</div>
          <div className="divide-y divide-border">
            {journeys.map((j) => (
              <div key={j.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="font-medium">{j.name}</div>
                  <div className="text-[11px] font-mono text-muted-foreground mt-0.5">{j.id} · {j.steps} steps</div>
                </div>
                <div className="flex items-center gap-2">
                  <Chip>{j.category}</Chip>
                  <Chip tone="ready"><CheckCircle2 className="size-3" /> active</Chip>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-xs text-muted-foreground">Suggested journeys</div>
              <h2 className="font-display text-lg font-semibold mt-0.5">From workflow agent · accept → add to config</h2>
            </div>
          </div>
          <div className="space-y-3">
            {suggestedJourneys.map((s) => (
              <div key={s.id} className="border border-border rounded-lg p-4 flex items-start justify-between gap-4">
                <div>
                  <div className="font-medium">{s.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">{s.reason}</div>
                  <Chip tone="info">{s.category}</Chip>
                  <span className="text-[10px] font-mono text-muted-foreground ml-2">from {s.sourceRunId}</span>
                </div>
                <button type="button" className="text-xs font-mono px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 inline-flex items-center gap-1.5 shrink-0"><Plus className="size-3.5" /> add to config</button>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
