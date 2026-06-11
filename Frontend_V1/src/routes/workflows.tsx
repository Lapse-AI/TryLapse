import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, UnderConstruction } from "@/components/ui-bits";
import { useLatestRun, useRunBundle, useConfigs } from "@/lib/api/hooks";
import { usePersistedConfigId } from "@/hooks/use-persisted-config-id";
import { buildWorkflowCoverage, normalizeSuggestedJourneys } from "@/lib/workflow-coverage";
import { api } from "@/lib/api/client";
import { Plus, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/workflows")({
  head: () => ({ meta: [{ title: "Workflows — Launch Rehearsal" }] }),
  component: Workflows,
});

function Workflows() {
  const latest = useLatestRun();
  const { data: bundle } = useRunBundle(latest?.id ?? "");
  const { data: configs = [] } = useConfigs();
  const { configId, pickConfig } = usePersistedConfigId();
  const [appendPending, setAppendPending] = useState<string | null>(null);
  const configOptions = useMemo(
    () => (configs.length ? configs : [{ id: "lr-self", name: "lr-self" }]),
    [configs],
  );

  if (!latest || !bundle) return null;
  const wfAgent = bundle.agents.find((a) => a.id === "ag_wf" || a.name === "Workflow");
  const workflowCoverage = buildWorkflowCoverage(bundle);
  const suggestedJourneys = normalizeSuggestedJourneys(bundle);
  const journeys = bundle.journeys ?? [];

  const appendJourney = async (suggestedId: string, path: string, title: string) => {
    setAppendPending(suggestedId);
    try {
      const out = await api.appendJourneyToConfig({ configId, path, title });
      toast.success(`Added ${out.journeyId} — edit on Config (YAML), then Run in Runner`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not append journey");
    } finally {
      setAppendPending(null);
    }
  };

  return (
    <UnderConstruction>
    <div>
      <PageHeader
        eyebrow="map · workflows"
        title="Workflow map"
        description="Patterns auto-detected from crawl (Workflow agent). Coverage shows whether journeys exercise them."
        actions={wfAgent && <Chip tone="info">{wfAgent.lastSummary}</Chip>}
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        {workflowCoverage.length === 0 ? (
          <Panel className="p-8 text-center text-sm text-muted-foreground">
            No workflows detected in {latest.id}. Run a crawl-enabled rehearsal to populate the
            workflow map.
          </Panel>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {workflowCoverage.map((w) => {
              const tone = w.coverage >= 90 ? "ready" : w.coverage >= 70 ? "warn" : "danger";
              return (
                <Panel key={w.category} className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="font-display text-lg font-semibold capitalize">
                      {w.category}
                    </div>
                    <Chip tone={tone}>{w.coverage}% covered</Chip>
                  </div>
                  <div className="mt-3 h-1.5 w-full rounded-full bg-surface-3 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${w.coverage}%`, background: `var(--${tone})` }}
                    />
                  </div>
                  <div className="mt-3 text-[11px] font-mono text-muted-foreground truncate">
                    {w.paths.join(" · ")}
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground font-mono">
                    <span>
                      {w.journeys} journey{w.journeys === 1 ? "" : "s"}
                    </span>
                    {w.suggested > 0 && <span className="text-warn">+{w.suggested} suggested</span>}
                  </div>
                </Panel>
              );
            })}
          </div>
        )}

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-4">
            Active journeys · from rehearse.yaml
          </div>
          {journeys.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No journeys in this run bundle.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {journeys.map((j) => (
                <div key={j.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-medium">{j.name}</div>
                    <div className="text-[11px] font-mono text-muted-foreground mt-0.5">
                      {j.id} · {j.steps} steps
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Chip>{j.category}</Chip>
                    <Chip tone="ready">
                      <CheckCircle2 className="size-3" /> active
                    </Chip>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel className="p-6">
          <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
            <div>
              <div className="text-xs text-muted-foreground">Suggested journeys</div>
              <h2 className="font-display text-lg font-semibold mt-0.5">
                From workflow agent · accept → add to config
              </h2>
            </div>
            <div>
              <label htmlFor="wf-config-id" className="text-xs text-muted-foreground mb-1 block">
                Target config
              </label>
              <select
                id="wf-config-id"
                aria-label="Target config for append journey"
                className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm font-mono min-w-[160px]"
                value={configId}
                onChange={(e) => pickConfig(e.target.value)}
              >
                {configOptions.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.id}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {suggestedJourneys.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No suggested journeys for {latest.id}.
            </div>
          ) : (
            <div className="space-y-3">
              {suggestedJourneys.map((s) => (
                <div
                  key={s.id}
                  className="border border-border rounded-lg p-4 flex items-start justify-between gap-4"
                >
                  <div>
                    <div className="font-medium">{s.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">{s.reason}</div>
                    <Chip tone="info">{s.category}</Chip>
                    {s.path && (
                      <span className="text-[11px] font-mono text-muted-foreground ml-2">
                        {s.path}
                      </span>
                    )}
                    <span className="text-[11px] font-mono text-muted-foreground ml-2">
                      from {s.sourceRunId}
                    </span>
                  </div>
                  <button
                    type="button"
                    disabled={!s.path || appendPending === s.id}
                    title={s.path ? undefined : "No navigate path in suggested journey"}
                    onClick={() => void appendJourney(s.id, s.path!, s.title)}
                    className="text-xs font-mono px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 inline-flex items-center gap-1.5 shrink-0 disabled:opacity-50"
                  >
                    {appendPending === s.id ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <Plus className="size-3.5" />
                    )}{" "}
                    add to config
                  </button>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
    </UnderConstruction>
  );
}
