import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, UnderConstruction } from "@/components/ui-bits";
import { agentConfigDefaults, formatDuration } from "@/lib/mock-data";
import { useLatestRun, useRunBundle } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";
import { ArrowRight, RotateCw, MessageSquare, Sliders } from "lucide-react";

export const Route = createFileRoute("/agents")({
  head: () => ({ meta: [{ title: "Agents — Launch Rehearsal" }] }),
  component: Agents,
});

const pipelinePhases = [
  { phase: "crawl", label: "Crawler" },
  { phase: "workflow", label: "Workflow" },
  { phase: "journey", label: "Journey runner" },
  { phase: "persona", label: "Persona ×N + LLM" },
  { phase: "synthesis", label: "Synthesizer" },
];

function Agents() {
  const latest = useLatestRun();
  const { data: bundle } = useRunBundle(latest?.id ?? "");
  if (!latest || !bundle) return null;

  return (
    <UnderConstruction>
      <div>
        <PageHeader
          eyebrow="multi-agent"
          title="Agent control center"
          description="Each rehearsal is a chain of specialized agents. Inspect handoffs, replay stages, configure LLM persona agents."
          actions={
            <VisionOnly section="agents.configurePanel">
              <button
                type="button"
                className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
              >
                <Sliders className="size-3.5" /> configure
              </button>
            </VisionOnly>
          }
        />
        <div className="p-8 max-w-[1400px] space-y-6">
          <Panel className="p-6">
            <div className="text-xs text-muted-foreground mb-4">
              Collaboration trace · {latest.id}
            </div>
            <div className="flex items-stretch gap-2 overflow-x-auto pb-2">
              {pipelinePhases.map((step, i) => {
                const agentsInPhase = bundle.agents.filter(
                  (a) => a.phase === step.phase && a.status !== "idle",
                );
                return (
                  <div key={step.phase} className="flex items-center gap-2">
                    <div className="border border-border rounded-lg p-3 min-w-[160px] bg-surface-2/40">
                      <div className="text-xs text-muted-foreground">stage {i + 1}</div>
                      <div className="text-sm font-medium mt-1">{step.label}</div>
                      <Chip tone={agentsInPhase.length ? "ready" : "neutral"}>
                        {agentsInPhase.length ? "done" : "skipped"}
                      </Chip>
                      {agentsInPhase[0]?.handoff && (
                        <div className="text-[11px] font-mono text-muted-foreground mt-2">
                          {Object.entries(agentsInPhase[0].handoff)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(" · ")}
                        </div>
                      )}
                    </div>
                    {i < pipelinePhases.length - 1 && (
                      <ArrowRight className="size-4 text-muted-foreground shrink-0" />
                    )}
                  </div>
                );
              })}
            </div>
          </Panel>

          <VisionOnly section="agents.llmConfigDefaults">
            <Panel className="p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-muted-foreground">LLM provider</div>
                <div className="font-mono text-sm mt-1">{agentConfigDefaults.llmProvider}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Model</div>
                <div className="font-mono text-xs mt-1 truncate">
                  {agentConfigDefaults.llmModel}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Crawl budget</div>
                <div className="font-mono text-sm mt-1">
                  {agentConfigDefaults.crawlMaxPages} pages · depth{" "}
                  {agentConfigDefaults.crawlMaxDepth}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Strict enterprise</div>
                <div className="font-mono text-sm mt-1 text-ready">
                  {agentConfigDefaults.strictEnterpriseMode ? "on" : "off"}
                </div>
              </div>
            </Panel>
          </VisionOnly>

          <Panel className="overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <div className="text-xs text-muted-foreground">Agent roster</div>
                <div className="font-display text-lg font-semibold mt-0.5">
                  {bundle.agents.length} agents ·{" "}
                  {bundle.agents.filter((a) => a.status !== "idle").length} active
                </div>
              </div>
              <Chip tone="violet">Phase 2 idle: Compliance, Performance</Chip>
            </div>
            <div className="divide-y divide-border">
              {bundle.agents.map((a) => (
                <div key={a.id} className="p-5 hover:bg-surface-2/30">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-medium">{a.name}</h3>
                        <Chip
                          tone={
                            a.status === "done"
                              ? "ready"
                              : a.status === "running"
                                ? "info"
                                : a.status === "failed"
                                  ? "danger"
                                  : "neutral"
                          }
                        >
                          {a.status}
                        </Chip>
                        <Chip tone="neutral">{a.phase}</Chip>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">{a.role}</div>
                      <p className="text-sm mt-2 text-foreground/90">{a.lastSummary}</p>
                      {a.expandableFindings && (
                        <div className="mt-2 text-xs text-muted-foreground">
                          Pre-synthesis findings available
                        </div>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <div className="font-mono text-xs text-muted-foreground">
                        {a.status === "idle" ? "—" : formatDuration(a.durationSec)}
                      </div>
                      <div className="font-mono text-xs text-muted-foreground">
                        ${a.costUsd.toFixed(2)}
                      </div>
                      <div className="mt-2 flex gap-1 justify-end">
                        <VisionOnly section="agents.replayFindings">
                          <button
                            type="button"
                            className="text-[11px] font-mono px-2 py-1 rounded border border-border hover:bg-surface-2 inline-flex items-center gap-1"
                          >
                            <RotateCw className="size-3" /> replay
                          </button>
                          <button
                            type="button"
                            className="text-[11px] font-mono px-2 py-1 rounded border border-border hover:bg-surface-2 inline-flex items-center gap-1"
                          >
                            <MessageSquare className="size-3" /> findings
                          </button>
                        </VisionOnly>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel className="p-6">
            <div className="text-xs text-muted-foreground mb-3">
              Human-in-the-loop · annotations
            </div>
            <div className="space-y-3">
              {bundle.annotations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No annotations on this run yet.</p>
              ) : (
                bundle.annotations.map((a) => (
                  <div key={a.id} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-mono text-xs text-muted-foreground">{a.author}</span>{" "}
                      <Chip
                        tone={
                          a.action === "agreed"
                            ? "ready"
                            : a.action === "false positive"
                              ? "warn"
                              : "violet"
                        }
                      >
                        {a.action}
                      </Chip>{" "}
                      <span className="ml-2">{a.targetId}</span>
                    </div>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      {a.at.slice(0, 10)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Panel>
        </div>
      </div>
    </UnderConstruction>
  );
}
