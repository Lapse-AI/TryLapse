import { Fragment, useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, Chip, SeverityChip, SEVERITY_LABEL } from "@/components/ui-bits";
import type {
  Annotation,
  Issue,
  Layer1Verdict,
  RunBundle,
  RunSummary,
  StepSnapshot,
} from "@/lib/mock-data";
import { formatDurationMs } from "@/lib/mock-data";
import { artifactUrl } from "@/lib/api/client";
import {
  useAddAnnotation,
  useRunDiff,
  useFindingOutcomes,
  useSetFindingOutcome,
} from "@/lib/api/hooks";
import {
  copyReproToClipboard,
  downloadArtifact,
  downloadRunBundleArtifacts,
  downloadReportMarkdown,
  printReportAsPdf,
  EXPORT_ITEMS,
  runArtifactRelPath,
} from "@/lib/run-export";
import {
  extraArtifactDownloads,
  formatWebVitalsBrief,
  stepObservabilityHint,
} from "@/lib/run-observability";
import { formatAgentCostDisplay } from "@/lib/run-metrics";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Camera, Share2 } from "lucide-react";
import { AnnotatedScreenshot, CompareVisualDiffPanel } from "@/components/annotated-screenshot";

export function EvidenceDialog({
  issue,
  runId,
  children,
}: {
  issue: Issue;
  runId: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [copying, setCopying] = useState(false);

  const handleCopyRepro = async () => {
    setCopying(true);
    try {
      await copyReproToClipboard(issue, runId);
      toast.success("Repro copied to clipboard");
    } catch {
      toast.error("Could not copy repro");
    } finally {
      setCopying(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild onClick={() => setOpen(true)}>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <SeverityChip s={issue.severity} />
            <Chip>{issue.dimension}</Chip>
            <Chip tone={issue.confidence === "high" ? "info" : "warn"}>{issue.confidence}</Chip>
          </div>
          <DialogTitle className="font-display">{issue.title}</DialogTitle>
          <DialogDescription>
            {issue.persona} · {issue.journey} · <span className="font-mono">{issue.stepId}</span>
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {/* D2: Story format for P0/P1 — user perspective, not technical language */}
          {issue.severity === "P0" || issue.severity === "P1" ? (
            <FindingStoryCard issue={issue} videoUrl={null} runId={runId} />
          ) : (
            <>
              <div className="aspect-video rounded-md border border-border bg-surface-2 overflow-hidden">
                {issue.screenshotPath ? (
                  <AnnotatedScreenshot
                    src={artifactUrl(issue.screenshotPath)}
                    region={issue.focusRegion}
                    alt={`Screenshot for ${issue.stepId}`}
                    className="h-full min-h-[200px]"
                  />
                ) : (
                  <div className="h-full grid-bg flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <Camera className="size-6 mx-auto mb-2 opacity-60" />
                      <div className="text-xs font-mono">
                        screenshot · {issue.stepId} · 1280×720
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Evidence</div>
                <p className="text-sm font-mono bg-surface-2 border border-border rounded-md p-3">
                  {issue.evidence}
                </p>
              </div>
            </>
          )}
          {issue.screenshotPath && (issue.severity === "P0" || issue.severity === "P1") && (
            <div className="aspect-video rounded-md border border-border bg-surface-2 overflow-hidden">
              <AnnotatedScreenshot
                src={artifactUrl(issue.screenshotPath)}
                region={issue.focusRegion}
                alt={`Screenshot for ${issue.stepId}`}
                className="h-full min-h-[200px]"
              />
            </div>
          )}
          {issue.severityReason && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Why {issue.severity}</div>
              <p className="text-sm">{issue.severityReason}</p>
            </div>
          )}
          {issue.suggestion && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Suggestion (no auto-fix)</div>
              <p className="text-sm text-foreground/90">{issue.suggestion}</p>
            </div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <div className="text-xs text-muted-foreground">Owner</div>
              <div className="font-medium mt-0.5 capitalize">{issue.owner}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Recurrence</div>
              <div className="font-medium mt-0.5">×{issue.recurring} runs</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Step</div>
              <div className="font-mono mt-0.5 text-xs">{issue.stepId}</div>
            </div>
            {issue.personaImpact && (
              <div className="col-span-2">
                <div className="text-xs text-muted-foreground">Persona impact</div>
                <div className="text-xs mt-0.5">{issue.personaImpact}</div>
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <button
            type="button"
            disabled={copying}
            onClick={() => void handleCopyRepro()}
            className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 disabled:opacity-50"
          >
            {copying ? "Copying…" : "Copy repro"}
          </button>
          <Link
            to="/runs/$runId"
            params={{ runId }}
            search={{ tab: "steps", step: issue.stepId }}
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 inline-flex items-center"
          >
            Open in step timeline
          </Link>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function RunObservabilityPanel({ bundle }: { bundle: RunBundle }) {
  const summary = bundle.summary;
  const stepsWithVitals = bundle.steps.filter((s) => formatWebVitalsBrief(s.webVitals));
  const warnSteps = bundle.steps.filter((s) => (s.consoleWarnings?.length ?? 0) > 0);
  const errorSteps = bundle.steps.filter((s) => s.errorType);
  const abandonSteps = bundle.steps.filter(
    (s) => (s as Record<string, unknown>).behavior === "abandon",
  );
  const hesitateSteps = bundle.steps.filter(
    (s) => (s as Record<string, unknown>).behavior === "hesitate",
  );
  const extras = extraArtifactDownloads(bundle);
  const pagesCrawled = summary.pagesCrawled ?? summary.pages;
  const cost = formatAgentCostDisplay(bundle);

  return (
    <Panel className="p-4 md:p-5 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="font-display font-semibold text-sm">Run observability</div>
        <Chip tone="neutral">Phase 1 tail</Chip>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div>
          <div className="text-xs text-muted-foreground">Duration</div>
          <div className="font-mono tabular-nums mt-0.5">{summary.durationSec}s</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Outcome</div>
          <div className="font-mono text-xs mt-0.5 uppercase">{summary.outcome}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Est. cost</div>
          <div className="font-mono tabular-nums mt-0.5">{cost.value}</div>
          <div className="text-[11px] text-muted-foreground">{cost.hint}</div>
        </div>
        {summary.agentsRun != null && (
          <div>
            <div className="text-xs text-muted-foreground">Agents run</div>
            <div className="font-mono tabular-nums mt-0.5">{summary.agentsRun}</div>
          </div>
        )}
        {pagesCrawled > 0 && (
          <div>
            <div className="text-xs text-muted-foreground">Pages crawled</div>
            <div className="font-mono tabular-nums mt-0.5">{pagesCrawled}</div>
          </div>
        )}
        {stepsWithVitals.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground">Web Vitals samples</div>
            <div className="font-mono tabular-nums mt-0.5">{stepsWithVitals.length} steps</div>
          </div>
        )}
        {warnSteps.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground">Console warnings</div>
            <div className="font-mono tabular-nums mt-0.5">{warnSteps.length} steps</div>
          </div>
        )}
        {errorSteps.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground">Named step errors</div>
            <div className="font-mono tabular-nums mt-0.5">{errorSteps.length} steps</div>
          </div>
        )}
        {abandonSteps.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground">Abandon</div>
            <div className="font-mono tabular-nums mt-0.5 text-danger">
              {abandonSteps.length} steps
            </div>
          </div>
        )}
        {hesitateSteps.length > 0 && (
          <div>
            <div className="text-xs text-muted-foreground">Hesitate</div>
            <div className="font-mono tabular-nums mt-0.5 text-warn">
              {hesitateSteps.length} steps
            </div>
          </div>
        )}
      </div>
      {errorSteps.length > 0 && (
        <p className="text-[11px] text-muted-foreground font-mono">
          {Array.from(new Set(errorSteps.map((s) => s.errorType).filter(Boolean))).join(" · ")}
        </p>
      )}
      {extras.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {extras.map(({ relPath, label }) => (
            <a
              key={label}
              href={artifactUrl(relPath)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono px-2.5 py-1 rounded-md border border-border hover:bg-surface-2"
            >
              {label} ↗
            </a>
          ))}
        </div>
      )}
    </Panel>
  );
}

export function StepsTable({
  steps,
  highlightStepId,
}: {
  steps: StepSnapshot[];
  highlightStepId?: string;
}) {
  if (!steps.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        No steps recorded for this run.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-xs text-muted-foreground">
          <tr className="border-b border-border bg-surface-2/40">
            <th className="text-left px-5 py-2 font-medium">Step ID</th>
            <th className="text-left px-5 py-2 font-medium">Journey</th>
            <th className="text-left px-5 py-2 font-medium">Action</th>
            <th className="text-left px-5 py-2 font-medium">Outcome</th>
            <th className="text-left px-5 py-2 font-medium">Duration</th>
            <th className="text-left px-5 py-2 font-medium">URL</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((s) => (
            <Fragment key={s.stepId}>
              <tr
                id={`step-${s.stepId}`}
                className={`border-b border-border hover:bg-surface-2/30 ${
                  highlightStepId === s.stepId ? "bg-primary/10 ring-1 ring-primary/30" : ""
                }`}
              >
                <td className="px-5 py-3 font-mono text-xs">
                  {s.stepId}
                  {s.flaky && (
                    <span className="ml-2">
                      <Chip tone="warn">flaky</Chip>
                    </span>
                  )}
                  {(s as Record<string, unknown>).behavior === "abandon" && (
                    <span className="ml-2">
                      <Chip tone="danger">abandon</Chip>
                    </span>
                  )}
                  {(s as Record<string, unknown>).behavior === "hesitate" && (
                    <span className="ml-2">
                      <Chip tone="warn">hesitate</Chip>
                    </span>
                  )}
                </td>
                <td className="px-5 py-3 text-xs">{s.journeyId}</td>
                <td className="px-5 py-3">
                  <div>{s.action}</div>
                  {s.action === "explore" && s.exploreSummary && (
                    <p className="text-xs text-muted-foreground mt-1 max-w-md whitespace-pre-wrap">
                      {s.exploreSummary}
                    </p>
                  )}
                  {stepObservabilityHint(s) && (
                    <p className="text-[11px] font-mono text-muted-foreground mt-1">
                      {stepObservabilityHint(s)}
                    </p>
                  )}
                </td>
                <td className="px-5 py-3">
                  <Chip
                    tone={
                      s.outcome === "pass"
                        ? "ready"
                        : s.outcome === "partial"
                          ? "warn"
                          : s.outcome === "fail"
                            ? "danger"
                            : "neutral"
                    }
                  >
                    {s.outcome}
                  </Chip>
                </td>
                <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                  {formatDurationMs(s.durationMs)}
                </td>
                <td className="px-5 py-3 font-mono text-xs max-w-[200px] truncate text-muted-foreground">
                  {(s.finalUrl ?? s.requestedUrl ?? "—").slice(0, 60)}
                </td>
              </tr>
              {s.action === "explore" && (s.exploreLog?.length || s.exploreSummary) ? (
                <tr key={`${s.stepId}-explore`} className="border-b border-border last:border-0">
                  <td colSpan={6} className="px-5 py-3 bg-surface-2/40 text-xs space-y-2">
                    {s.exploreSummary && (
                      <p className="text-sm leading-relaxed">{s.exploreSummary}</p>
                    )}
                    {s.exploreLog?.map((rnd) => (
                      <div key={rnd.round} className="font-mono text-[11px] text-muted-foreground">
                        Round {rnd.round}
                        {rnd.rationale ? ` — ${rnd.rationale}` : ""}
                        {(rnd.actions ?? []).map((a, i) => (
                          <span key={i} className="ml-2">
                            [{a.outcome}] {a.action}
                            {a.intent ? `: ${a.intent}` : ""}
                          </span>
                        ))}
                      </div>
                    ))}
                  </td>
                </tr>
              ) : null}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { RunNarrativePanel } from "./run-detail/RunNarrativePanel";

export function ScorecardPanel({ markdown, bundle }: { markdown: string; bundle?: RunBundle }) {
  const run = bundle?.summary;
  const sevs = ["P0", "P1", "P2", "P3"] as const;
  const sevColors: Record<string, string> = {
    P0: "danger",
    P1: "warn",
    P2: "info",
    P3: "neutral",
  };

  return (
    <div className="divide-y divide-border">
      {/* Stats bar */}
      {run && bundle && (
        <div className="p-5 grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <div className="text-[11px] text-muted-foreground">Readiness</div>
            <div className="text-2xl font-bold font-mono tabular-nums mt-0.5">{run.readiness}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">{run.readinessBand}</div>
          </div>
          {sevs.map((s) => {
            const count = bundle.issues.filter((i) => i.severity === s).length;
            return (
              <div key={s}>
                <div className="text-[11px] text-muted-foreground">{SEVERITY_LABEL[s]}</div>
                <div
                  className="text-2xl font-bold font-mono tabular-nums mt-0.5"
                  style={{
                    color:
                      count > 0 && (s === "P0" || s === "P1")
                        ? `var(--${sevColors[s]})`
                        : undefined,
                  }}
                >
                  {count}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Executive summary */}
      {bundle?.narrative && (
        <div className="p-5 bg-primary/3 border-l-4 border-primary/30">
          <div className="text-[11px] text-muted-foreground mb-2 font-medium uppercase tracking-wide">
            Executive summary
          </div>
          <p className="text-sm font-medium leading-relaxed mb-4">
            {bundle.narrative.executiveSummary}
          </p>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-[11px] text-muted-foreground mb-1">For founders</div>
              <p className="text-foreground/85 leading-relaxed">{bundle.narrative.forFounders}</p>
            </div>
            <div>
              <div className="text-[11px] text-muted-foreground mb-1">For engineering</div>
              <p className="text-foreground/85 leading-relaxed">
                {bundle.narrative.forEngineering}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Issues by severity */}
      {bundle &&
        sevs.map((sev) => {
          const sevIssues = bundle.issues.filter((i) => i.severity === sev);
          if (!sevIssues.length) return null;
          const tone = sevColors[sev] as "danger" | "warn" | "info" | "neutral";
          return (
            <div key={sev} className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <SeverityChip s={sev} />
                <span className="text-sm font-semibold">{SEVERITY_LABEL[sev]}</span>
                <span className="text-[11px] text-muted-foreground">
                  {sevIssues.length} {sevIssues.length === 1 ? "issue" : "issues"}
                </span>
              </div>
              <div className="space-y-2">
                {sevIssues.map((issue) => (
                  <div
                    key={issue.id}
                    className="rounded-lg border p-4 space-y-1.5"
                    style={{
                      borderColor: `color-mix(in oklab, var(--${tone}) 25%, var(--border))`,
                      background: `color-mix(in oklab, var(--${tone}) 4%, transparent)`,
                    }}
                  >
                    <div className="flex items-start gap-3 justify-between">
                      <h4 className="text-sm font-semibold leading-snug">{issue.title}</h4>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <Chip tone={issue.confidence === "high" ? "info" : "warn"}>
                          {issue.confidence}
                        </Chip>
                        <Chip>{issue.owner}</Chip>
                      </div>
                    </div>
                    <p className="text-xs font-mono text-muted-foreground leading-relaxed">
                      {issue.evidence}
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-muted-foreground flex-wrap">
                      <span>{issue.persona}</span>
                      <span>·</span>
                      <span>{issue.journey}</span>
                      <span>·</span>
                      <span className="font-mono">{issue.stepId}</span>
                      {issue.recurring > 1 && (
                        <>
                          <span>·</span>
                          <span className="text-danger">recurring ×{issue.recurring}</span>
                        </>
                      )}
                    </div>
                    {issue.suggestion && (
                      <p className="text-xs text-foreground/75 mt-1 italic">
                        Suggestion: {issue.suggestion}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}

      {/* Highlights */}
      {bundle && bundle.delights.length > 0 && (
        <div className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="size-5 rounded-full bg-ready/20 flex items-center justify-center">
              <span className="text-[10px] text-ready">★</span>
            </div>
            <span className="text-sm font-semibold">Highlights</span>
            <span className="text-[11px] text-muted-foreground">{bundle.delights.length}</span>
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {bundle.delights.map((d) => (
              <div key={d.id} className="rounded-lg border border-ready/20 bg-ready/4 p-4">
                <div className="flex items-center gap-2 flex-wrap mb-2">
                  <h4 className="text-sm font-semibold">{d.title}</h4>
                  {d.marketingReady && <Chip tone="ready">marketing-ready</Chip>}
                </div>
                <blockquote className="border-l-2 border-ready pl-3 text-sm italic text-foreground/85">
                  &ldquo;{d.quote}&rdquo;
                </blockquote>
                <div className="text-[11px] text-muted-foreground mt-1.5">— {d.persona}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dimension scores */}
      {bundle && bundle.dimensions.length > 0 && (
        <div className="p-5">
          <div className="text-[11px] text-muted-foreground mb-3 font-medium">Dimension scores</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {bundle.dimensions.map((d) => (
              <div
                key={d.name}
                className="flex items-center justify-between rounded-md border border-border bg-surface-2/30 px-3 py-2"
              >
                <span className="text-xs text-muted-foreground truncate">{d.name}</span>
                <span
                  className="font-mono font-bold text-sm tabular-nums ml-2 shrink-0"
                  style={{
                    color:
                      d.score >= 80
                        ? "var(--ready)"
                        : d.score >= 60
                          ? "var(--warn)"
                          : "var(--danger)",
                  }}
                >
                  {d.score}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw markdown fallback */}
      <details className="group">
        <summary className="px-5 py-3 text-xs text-muted-foreground cursor-pointer hover:text-foreground list-none flex items-center gap-1.5">
          <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
          Raw scorecard markdown
        </summary>
        <pre className="px-5 pb-5 text-[11.5px] font-mono leading-relaxed overflow-x-auto text-foreground/70 whitespace-pre-wrap">
          {markdown}
        </pre>
      </details>
    </div>
  );
}

export function SitemapPanel({ markdown }: { markdown: string }) {
  return (
    <pre className="p-5 text-[12.5px] font-mono leading-relaxed overflow-x-auto bg-surface-2/30 text-foreground/95 whitespace-pre-wrap">
      {markdown}
    </pre>
  );
}

type ShotMeta = RunBundle["screenshots"][number];

function ScreenshotCard({ s }: { s: ShotMeta }) {
  const [open, setOpen] = useState(false);
  const outcomeColor =
    s.outcome === "pass"
      ? "text-ready"
      : s.outcome === "fail"
        ? "text-danger"
        : "text-muted-foreground";
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <figure
          className="border border-border rounded-lg overflow-hidden bg-surface-2/30 cursor-pointer hover:border-primary/40 hover:shadow-sm transition-all group"
          onClick={() => setOpen(true)}
        >
          <div className="aspect-video relative overflow-hidden">
            <AnnotatedScreenshot
              src={artifactUrl(s.path)}
              alt={s.stepId}
              className="h-full group-hover:scale-[1.02] transition-transform duration-200"
            />
            {s.outcome && (
              <span
                className={`absolute top-1.5 right-1.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-background/80 backdrop-blur-sm ${outcomeColor}`}
              >
                {s.outcome}
              </span>
            )}
          </div>
          <figcaption className="p-2 text-[11px] text-muted-foreground border-t border-border">
            <div className="font-medium text-foreground truncate">{s.label}</div>
            <div className="font-mono truncate opacity-60">{s.stepId}</div>
          </figcaption>
        </figure>
      </DialogTrigger>
      <DialogContent className="max-w-4xl w-full">
        <DialogHeader>
          <DialogTitle className="text-sm font-medium">{s.journeyName || s.label}</DialogTitle>
          {s.url && (
            <DialogDescription className="font-mono text-xs truncate">{s.url}</DialogDescription>
          )}
        </DialogHeader>
        <div className="rounded-lg overflow-hidden border border-border bg-black">
          <img
            src={artifactUrl(s.path)}
            alt={s.stepId}
            className="w-full object-contain max-h-[60vh]"
          />
        </div>
        <div className="grid grid-cols-2 gap-3 text-xs">
          {s.action && (
            <div className="space-y-0.5">
              <div className="text-muted-foreground font-medium uppercase tracking-wide text-[10px]">
                Action
              </div>
              <div className="font-mono">
                {s.action}
                {s.intent ? ` — ${s.intent}` : ""}
              </div>
            </div>
          )}
          {s.outcome && (
            <div className="space-y-0.5">
              <div className="text-muted-foreground font-medium uppercase tracking-wide text-[10px]">
                Outcome
              </div>
              <div className={`font-medium ${outcomeColor}`}>
                {s.outcome}
                {s.durationMs ? ` · ${(s.durationMs / 1000).toFixed(1)}s` : ""}
              </div>
            </div>
          )}
          {s.personaId && (
            <div className="space-y-0.5">
              <div className="text-muted-foreground font-medium uppercase tracking-wide text-[10px]">
                Persona
              </div>
              <div className="font-mono">{s.personaId}</div>
            </div>
          )}
          {s.note && (
            <div className="space-y-0.5 col-span-2">
              <div className="text-muted-foreground font-medium uppercase tracking-wide text-[10px]">
                Observation
              </div>
              <div className="text-foreground/80">{s.note}</div>
            </div>
          )}
          {(s.consoleErrors?.length ?? 0) > 0 && (
            <div className="space-y-0.5 col-span-2">
              <div className="text-danger font-medium uppercase tracking-wide text-[10px]">
                Console errors
              </div>
              {s.consoleErrors!.map((e, i) => (
                <div key={i} className="font-mono text-danger/80 truncate">
                  {e}
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="text-[10px] font-mono text-muted-foreground/50">{s.stepId}</div>
      </DialogContent>
    </Dialog>
  );
}

export function ScreenshotGallery({ shots }: { shots: ShotMeta[] }) {
  if (!shots.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">No screenshots captured.</div>
    );
  }
  return (
    <div className="p-5 grid grid-cols-2 md:grid-cols-3 gap-4">
      {shots.map((s) => (
        <ScreenshotCard key={s.stepId} s={s} />
      ))}
    </div>
  );
}

export function DiffPanel({ runA, runB }: { runA: string; runB: string }) {
  const { data: diff, isLoading, error } = useRunDiff(runA, runB);
  if (isLoading) {
    return <div className="p-8 text-center text-sm text-muted-foreground">Loading diff…</div>;
  }
  if (error || !diff) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        Could not diff runs — one or both not found.
      </div>
    );
  }
  const cn = diff.narrative;

  return (
    <div className="p-5 space-y-4">
      {cn && (
        <Panel className="p-4 md:p-5 space-y-3 border-primary/20 bg-primary/5">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="font-display font-semibold">What changed</div>
            <Chip
              tone={
                cn.verdict === "improved" ? "ready" : cn.verdict === "regressed" ? "danger" : "warn"
              }
            >
              {cn.verdict}
            </Chip>
            <Chip tone="neutral">{cn.source === "llm+template" ? "AI + rules" : "Rules"}</Chip>
          </div>
          <p className="text-sm leading-relaxed">{cn.headline}</p>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-muted-foreground mb-1">For founders</div>
              <p className="whitespace-pre-wrap">{cn.forFounders}</p>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">For engineering</div>
              <p className="whitespace-pre-wrap">{cn.forEngineering}</p>
            </div>
          </div>
        </Panel>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Readiness</div>
          <div className="font-mono text-sm mt-1">
            {diff.readinessA} → {diff.readinessB}
          </div>
        </Panel>
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Issues</div>
          <div className="font-mono text-sm mt-1">
            {diff.issuesA} → {diff.issuesB}
          </div>
        </Panel>
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Pages crawled</div>
          <div className="font-mono text-sm mt-1">
            {diff.pagesA} → {diff.pagesB}
          </div>
        </Panel>
        <Panel className="p-3">
          <div className="text-xs text-muted-foreground">Changed steps</div>
          <div className="font-mono text-sm mt-1">{diff.changedSteps.length}</div>
        </Panel>
      </div>
      {diff.newIssues.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">New issues in {runB}</div>
          <ul className="text-sm space-y-1">
            {diff.newIssues.map((i) => (
              <li key={i} className="text-danger">
                + {i}
              </li>
            ))}
          </ul>
        </div>
      )}
      {diff.resolvedIssues.length > 0 && (
        <div>
          <div className="text-xs text-muted-foreground mb-2">Resolved since {runA}</div>
          <ul className="text-sm space-y-1">
            {diff.resolvedIssues.map((i) => (
              <li key={i} className="text-ready">
                − {i}
              </li>
            ))}
          </ul>
        </div>
      )}
      {(diff.visualDiffs?.length ?? 0) > 0 && (
        <div id="visual-diff" className="space-y-3 scroll-mt-24">
          <div className="font-display font-semibold text-sm">Visual step diff</div>
          <p className="text-xs text-muted-foreground">
            Side-by-side screenshots for changed steps. Boxes show the control that was clicked,
            filled, or selected (new runs only).
          </p>
          <CompareVisualDiffPanel items={diff.visualDiffs ?? []} />
        </div>
      )}

      {(diff.newPages.length > 0 || diff.removedPages.length > 0) && (
        <Panel className="p-4 space-y-3">
          <div className="text-xs text-muted-foreground">Sitemap diff</div>
          {diff.newPages.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-1">
                New in {runB} ({diff.newPages.length})
              </div>
              <ul className="text-sm font-mono space-y-0.5 max-h-32 overflow-y-auto">
                {diff.newPages.slice(0, 20).map((p) => (
                  <li key={p} className="text-ready">
                    + {p}
                  </li>
                ))}
                {diff.newPages.length > 20 && (
                  <li className="text-muted-foreground">…and {diff.newPages.length - 20} more</li>
                )}
              </ul>
            </div>
          )}
          {diff.removedPages.length > 0 && (
            <div>
              <div className="text-[11px] text-muted-foreground mb-1">
                Removed since {runA} ({diff.removedPages.length})
              </div>
              <ul className="text-sm font-mono space-y-0.5 max-h-32 overflow-y-auto">
                {diff.removedPages.slice(0, 20).map((p) => (
                  <li key={p} className="text-danger">
                    − {p}
                  </li>
                ))}
                {diff.removedPages.length > 20 && (
                  <li className="text-muted-foreground">
                    …and {diff.removedPages.length - 20} more
                  </li>
                )}
              </ul>
            </div>
          )}
        </Panel>
      )}
      <details className="group">
        <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
          Advanced · raw diff JSON
        </summary>
        <pre className="mt-2 text-[11px] font-mono bg-surface-2 border border-border rounded-lg p-4 overflow-x-auto">
          {JSON.stringify(diff, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export function AnnotationsPanel({
  runId: _runId,
  annotations,
}: {
  runId: string;
  annotations: Annotation[];
}) {
  if (!annotations.length) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground">
        No human annotations yet. Agree, disagree, or pin findings from the Issues tab.
      </div>
    );
  }
  return (
    <div className="divide-y divide-border">
      {annotations.map((a) => (
        <div key={a.id} className="p-4 flex items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs text-muted-foreground">{a.author}</span>
            <Chip
              tone={
                a.action === "agreed"
                  ? "ready"
                  : a.action === "false positive"
                    ? "warn"
                    : a.action === "pinned"
                      ? "violet"
                      : "info"
              }
            >
              {a.action}
            </Chip>
            <span>
              {a.targetType} · <span className="font-mono">{a.targetId}</span>
            </span>
            {a.note && <span className="text-muted-foreground text-xs">— {a.note}</span>}
          </div>
          <span className="text-[11px] text-muted-foreground font-mono shrink-0">
            {a.at.slice(0, 10)}
          </span>
        </div>
      ))}
    </div>
  );
}

type AnnotationAction = Extract<
  Annotation["action"],
  "agreed" | "disagree" | "false positive" | "pinned"
>;

const ANNOTATION_ACTIONS: {
  action: AnnotationAction;
  label: string;
  tone: "ready" | "info" | "warn";
}[] = [
  { action: "agreed", label: "Agree", tone: "ready" },
  { action: "disagree", label: "Disagree", tone: "info" },
  { action: "false positive", label: "False positive", tone: "warn" },
  { action: "pinned", label: "Pin", tone: "info" },
];

export function IssueAnnotationActions({
  runId,
  issue,
  existing,
}: {
  runId: string;
  issue: Issue;
  existing?: Annotation;
}) {
  const addAnnotation = useAddAnnotation(runId);

  const submit = (action: AnnotationAction) => {
    const ann: Annotation = {
      id: `ann_${Date.now()}`,
      runId,
      targetType: "issue",
      targetId: issue.id,
      action,
      author: "operator",
      at: new Date().toISOString(),
    };
    addAnnotation.mutate(ann, {
      onSuccess: () => toast.success(`Marked ${action}`),
      onError: () => toast.error("Could not save annotation"),
    });
  };

  if (existing) {
    return (
      <Chip
        tone={
          existing.action === "agreed"
            ? "ready"
            : existing.action === "false positive"
              ? "warn"
              : existing.action === "pinned"
                ? "violet"
                : "info"
        }
      >
        {existing.action}
      </Chip>
    );
  }

  return (
    <div className="flex items-center gap-1 shrink-0">
      {ANNOTATION_ACTIONS.map(({ action, label, tone }) => (
        <button
          key={action}
          type="button"
          disabled={addAnnotation.isPending}
          onClick={() => submit(action)}
          className="text-[11px] font-mono px-2 py-1 rounded-md border border-border hover:bg-surface-2 disabled:opacity-50"
          style={{ color: `var(--${tone})` }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function ExportMenu({ runId, bundle }: { runId: string; bundle: RunBundle }) {
  const [busy, setBusy] = useState<string | null>(null);

  const downloadOne = async (kind: (typeof EXPORT_ITEMS)[number]["kind"], label: string) => {
    setBusy(label);
    try {
      await downloadArtifact(runArtifactRelPath(runId, kind), `${runId}-${label}`);
      toast.success(`Downloaded ${label}`);
    } catch {
      toast.error(`Could not download ${label} — is ./rehearse serve running?`);
    } finally {
      setBusy(null);
    }
  };

  const downloadAll = async () => {
    setBusy("all");
    try {
      const { ok, failed } = await downloadRunBundleArtifacts(bundle);
      if (failed.length) {
        toast.warning(`Downloaded ${ok} files; missing: ${failed.slice(0, 5).join(", ")}`);
      } else {
        toast.success(`Downloaded ${ok} artifacts`);
      }
    } catch {
      toast.error("Bulk download failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2"
        >
          Export
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export run artifacts</DialogTitle>
          <DialogDescription>
            Files from launch-rehearsal/artifacts/ — served at /files/ when rehearse serve is
            running.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <div className="pb-2 border-b border-border mb-1">
            <div className="text-[11px] text-muted-foreground mb-1.5 px-1">Reports</div>
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => {
                downloadReportMarkdown(bundle);
                toast.success("Report downloaded");
              }}
              className="w-full text-left px-3 py-2 rounded-md border border-border hover:bg-surface-2 font-mono text-sm disabled:opacity-50"
            >
              report.md — full structured report
            </button>
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => printReportAsPdf(bundle)}
              className="w-full text-left px-3 py-2 rounded-md border border-primary/40 bg-primary/5 hover:bg-primary/10 text-primary font-mono text-sm disabled:opacity-50 mt-1.5"
            >
              Print / Save as PDF ↗
            </button>
          </div>
          {EXPORT_ITEMS.map(({ kind, label }) => (
            <button
              key={label}
              type="button"
              disabled={busy !== null}
              onClick={() => void downloadOne(kind, label)}
              className="w-full text-left px-3 py-2 rounded-md border border-border hover:bg-surface-2 font-mono text-sm disabled:opacity-50"
            >
              {busy === label ? `Downloading ${label}…` : label}
            </button>
          ))}
          {extraArtifactDownloads(bundle).map(({ relPath, label }) => (
            <button
              key={label}
              type="button"
              disabled={busy !== null}
              onClick={() => {
                setBusy(label);
                void downloadArtifact(relPath, `${runId}-${label}`)
                  .then(() => toast.success(`Downloaded ${label}`))
                  .catch(() =>
                    toast.error(`Could not download ${label} — is ./rehearse serve running?`),
                  )
                  .finally(() => setBusy(null));
              }}
              className="w-full text-left px-3 py-2 rounded-md border border-border hover:bg-surface-2 font-mono text-sm disabled:opacity-50"
            >
              {busy === label ? `Downloading ${label}…` : label}
            </button>
          ))}
          {bundle.screenshots.length > 0 && (
            <p className="text-[11px] text-muted-foreground px-1 pt-1">
              Download all includes {bundle.screenshots.length} PNG screenshots (no zip yet).
            </p>
          )}
        </div>
        <DialogFooter>
          <button
            type="button"
            disabled={busy !== null}
            onClick={() => void downloadAll()}
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
          >
            {busy === "all" ? "Downloading…" : "Download all"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── D1: Verdict Banner ────────────────────────────────────────────────────────
// Large go/no-go verdict displayed at the very top of the run detail overview.
// A non-technical founder must understand the answer in under 3 seconds.

const VERDICT_CONFIG = {
  no_ship: {
    emoji: "🔴",
    label: "Don't launch yet.",
    bg: "bg-danger/8 border-danger/30 border-l-danger",
    text: "text-danger",
    subtext: "text-danger/70",
  },
  caution: {
    emoji: "🟡",
    label: "Almost ready.",
    bg: "bg-warn/8 border-warn/30 border-l-warn",
    text: "text-warn",
    subtext: "text-warn/70",
  },
  ship: {
    emoji: "🟢",
    label: "You're clear to launch.",
    bg: "bg-ready/8 border-ready/30 border-l-ready",
    text: "text-ready",
    subtext: "text-ready/70",
  },
} as const;

export function VerdictBanner({ verdict }: { verdict: Layer1Verdict }) {
  const cfg = VERDICT_CONFIG[verdict.decision] ?? VERDICT_CONFIG.caution;
  return (
    <div
      className={`rounded-xl border border-l-4 p-5 md:p-6 ${cfg.bg}`}
      role="status"
      aria-label={`Launch verdict: ${verdict.headline}`}
    >
      <div className="flex items-start gap-4">
        <span className="text-4xl md:text-5xl leading-none select-none" aria-hidden>
          {cfg.emoji}
        </span>
        <div className="min-w-0">
          <div className={`text-2xl md:text-3xl font-bold font-display leading-tight ${cfg.text}`}>
            {verdict.headline}
          </div>
          <p className={`mt-2 text-sm leading-relaxed ${cfg.subtext}`}>{verdict.reason}</p>
        </div>
      </div>
    </div>
  );
}

// ── D2: Finding Story Card ────────────────────────────────────────────────────
// Renders a P0/P1 finding in user-story format with an optional video player.
// Used inside EvidenceDialog for high-severity issues.

function personaLabel(persona: string): string {
  const lower = persona.toLowerCase();
  if (lower.includes("mobile")) return "a mobile user";
  if (lower.includes("new")) return "a first-time visitor";
  if (lower.includes("enterprise") || lower.includes("admin")) return "an enterprise admin";
  if (lower.includes("power")) return "a power user";
  if (lower.includes("keyboard")) return "a keyboard-only user";
  if (lower.includes("international") || lower.includes("rtl")) return "an international user";
  return `a ${persona.toLowerCase()} user`;
}

const FINDING_OUTCOME_LABELS: Record<string, { label: string; color: string }> = {
  acted_on: { label: "Fixed it", color: "text-green-600" },
  dismissed: { label: "Not worth it", color: "text-muted-foreground" },
  false_positive: { label: "Not real", color: "text-orange-500" },
  deferred: { label: "Later", color: "text-blue-500" },
};

function FindingOutcomeButtons({ runId, findingId }: { runId: string; findingId: string }) {
  const { data: outcomes } = useFindingOutcomes(runId);
  const { mutate, isPending } = useSetFindingOutcome(runId);
  const currentOutcome = outcomes?.[findingId];

  return (
    <div className="flex items-center gap-1 flex-wrap">
      <span className="text-[10px] text-muted-foreground mr-1 shrink-0">What happened?</span>
      {Object.entries(FINDING_OUTCOME_LABELS).map(([outcome, { label, color }]) => (
        <button
          key={outcome}
          disabled={isPending}
          onClick={() => mutate({ findingId, outcome })}
          className={[
            "text-[11px] px-2 py-0.5 rounded-full border transition-colors",
            currentOutcome === outcome
              ? `${color} border-current bg-current/5 font-medium`
              : "border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground",
          ].join(" ")}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function FindingStoryCard({
  issue,
  videoUrl,
  runId,
}: {
  issue: Issue;
  videoUrl?: string | null;
  runId?: string;
}) {
  const story = [
    `We sent ${personaLabel(issue.persona)} through the ${issue.journey} flow.`,
    issue.detail,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="space-y-3">
      {/* Story prose */}
      <div className="bg-surface-2 border border-border rounded-lg p-4">
        <div className="text-[11px] text-muted-foreground mb-2 uppercase tracking-wide font-medium">
          What happened
        </div>
        <p className="text-sm leading-relaxed">{story}</p>
      </div>

      {/* Video player — P0 evidence clip */}
      {videoUrl && (
        <div className="rounded-lg border border-border overflow-hidden bg-black">
          <div className="text-[11px] text-muted-foreground px-3 py-1.5 bg-surface-2 border-b border-border">
            Journey recording · {issue.journey}
          </div>
          <video
            src={videoUrl}
            autoPlay
            muted
            loop
            controls
            playsInline
            className="w-full max-h-[320px] object-contain"
          />
        </div>
      )}

      {/* Technical one-liner for developers */}
      <details className="group">
        <summary className="text-[11px] text-muted-foreground cursor-pointer hover:text-foreground select-none list-none flex items-center gap-1">
          <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
          Technical detail (for developers)
        </summary>
        <p className="mt-2 text-xs font-mono bg-surface-2 border border-border rounded-md p-3 text-foreground/80">
          {issue.evidence}
        </p>
      </details>

      {/* A5: Severity calibration — developer labels this finding's outcome */}
      {runId && <FindingOutcomeButtons runId={runId} findingId={issue.id} />}
    </div>
  );
}

// ── L3-PRED-07: Funnel Drop-off Panel ─────────────────────────────────────────
// Shows step-by-step pass/fail/partial rates per journey so teams can see
// exactly where personas abandon or struggle. Integrated with behavioralJourneys
// friction scores when the deep analysis engine ran.

type StepBucket = {
  idx: number;
  action: string;
  total: number;
  pass: number;
  partial: number;
  fail: number;
  skipped: number;
  avgMs: number;
};

type JourneyFunnel = {
  journeyId: string;
  journeyName: string;
  steps: StepBucket[];
  frictionScore?: number;
  frictionPoints?: string[];
};

function buildFunnels(bundle: RunBundle): JourneyFunnel[] {
  const { steps, behavioralJourneys } = bundle;
  if (!steps.length) return [];

  const byJourney = new Map<string, StepSnapshot[]>();
  for (const s of steps) {
    const arr = byJourney.get(s.journeyId) ?? [];
    arr.push(s);
    byJourney.set(s.journeyId, arr);
  }

  const funnels: JourneyFunnel[] = [];
  for (const [journeyId, jSteps] of byJourney) {
    const byIdx = new Map<number, StepSnapshot[]>();
    for (const s of jSteps) {
      const idx = parseInt(s.stepId.match(/-s(\d+)$/)?.[1] ?? "0") || 0;
      const arr = byIdx.get(idx) ?? [];
      arr.push(s);
      byIdx.set(idx, arr);
    }

    if (byIdx.size < 2) continue;

    const buckets: StepBucket[] = [...byIdx.entries()]
      .sort(([a], [b]) => a - b)
      .map(([idx, ss]) => ({
        idx,
        action: ss[0].action,
        total: ss.length,
        pass: ss.filter((s) => s.outcome === "pass").length,
        partial: ss.filter((s) => s.outcome === "partial").length,
        fail: ss.filter((s) => s.outcome === "fail").length,
        skipped: ss.filter((s) => s.outcome === "skipped").length,
        avgMs: ss.reduce((acc, s) => acc + s.durationMs, 0) / ss.length,
      }));

    const jName = jSteps[0]?.journeyName ?? journeyId;
    const bj = behavioralJourneys?.[journeyId] ?? behavioralJourneys?.[jName];

    funnels.push({
      journeyId,
      journeyName: jName,
      steps: buckets,
      frictionScore: bj?.friction_score,
      frictionPoints: bj?.key_friction_points?.slice(0, 3),
    });
  }

  return funnels.sort((a, b) => {
    const aFails = a.steps.reduce((sum, s) => sum + s.fail, 0);
    const bFails = b.steps.reduce((sum, s) => sum + s.fail, 0);
    return bFails - aFails;
  });
}

function frictionColor(score: number): string {
  if (score >= 7) return "text-danger";
  if (score >= 4) return "text-warn";
  return "text-ready";
}

function StepFunnelRow({ bucket }: { bucket: StepBucket }) {
  const passW = bucket.total > 0 ? (bucket.pass / bucket.total) * 100 : 0;
  const partialW = bucket.total > 0 ? (bucket.partial / bucket.total) * 100 : 0;
  const failW = bucket.total > 0 ? (bucket.fail / bucket.total) * 100 : 0;
  const skipW = bucket.total > 0 ? (bucket.skipped / bucket.total) * 100 : 0;
  const hasProblem = bucket.fail > 0 || bucket.partial > 0;

  return (
    <div className="flex items-center gap-3 py-1.5">
      <div
        className={`text-[11px] tabular-nums w-4 shrink-0 text-right ${
          hasProblem ? "text-danger/70" : "text-muted-foreground/50"
        }`}
      >
        {bucket.idx}
      </div>
      <div className="flex-1 min-w-0 space-y-1">
        <div className="text-xs text-foreground/80 truncate" title={bucket.action}>
          {bucket.action}
        </div>
        <div
          className="h-2 rounded-full overflow-hidden flex"
          style={{ background: "color-mix(in oklab, var(--border) 50%, transparent)" }}
        >
          {passW > 0 && (
            <div
              style={{ width: `${passW}%`, background: "var(--ready)" }}
              className="h-full transition-all"
            />
          )}
          {partialW > 0 && (
            <div
              style={{ width: `${partialW}%`, background: "var(--warn)" }}
              className="h-full transition-all"
            />
          )}
          {failW > 0 && (
            <div
              style={{ width: `${failW}%`, background: "var(--danger)" }}
              className="h-full transition-all"
            />
          )}
          {skipW > 0 && (
            <div
              style={{ width: `${skipW}%`, opacity: 0.3, background: "var(--muted-foreground)" }}
              className="h-full transition-all"
            />
          )}
        </div>
      </div>
      <div className="text-[11px] tabular-nums text-muted-foreground w-16 shrink-0 text-right">
        {Math.round(passW)}% pass
      </div>
    </div>
  );
}

function JourneyFunnelCard({ funnel }: { funnel: JourneyFunnel }) {
  const totalFails = funnel.steps.reduce((sum, s) => sum + s.fail, 0);
  const totalSteps = funnel.steps.reduce((sum, s) => sum + s.total, 0);
  const overallPassRate =
    totalSteps > 0
      ? Math.round((funnel.steps.reduce((sum, s) => sum + s.pass, 0) / totalSteps) * 100)
      : 0;

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 bg-surface-2 border-b border-border">
        <span className="text-sm font-medium truncate flex-1">{funnel.journeyName}</span>
        {funnel.frictionScore !== undefined && (
          <span
            className={`text-[11px] tabular-nums font-medium ${frictionColor(funnel.frictionScore)}`}
            title={`Friction score: ${funnel.frictionScore}/10`}
          >
            friction {funnel.frictionScore}/10
          </span>
        )}
        <span className="text-[11px] tabular-nums text-muted-foreground">
          {overallPassRate}% overall
        </span>
        {totalFails > 0 && (
          <Chip tone="danger">
            {totalFails} fail{totalFails !== 1 ? "s" : ""}
          </Chip>
        )}
      </div>
      <div className="px-4 py-2 divide-y divide-border/40">
        {funnel.steps.map((s) => (
          <StepFunnelRow key={s.idx} bucket={s} />
        ))}
      </div>
      {funnel.frictionPoints && funnel.frictionPoints.length > 0 && (
        <div className="px-4 pb-3 pt-1 space-y-1">
          <div className="text-[11px] text-muted-foreground uppercase tracking-wide font-medium">
            Key friction points
          </div>
          {funnel.frictionPoints.map((fp, i) => (
            <div key={i} className="text-xs text-foreground/70 flex gap-2">
              <span className="text-warn shrink-0">·</span>
              <span>{fp}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function FunnelPanel({ bundle }: { bundle: RunBundle }) {
  const funnels = useMemo(() => buildFunnels(bundle), [bundle]);
  if (!funnels.length) return null;

  return (
    <Panel className="p-5 space-y-4">
      <div>
        <div className="text-xs text-muted-foreground uppercase tracking-wide font-medium mb-0.5">
          Journey drop-off
        </div>
        <div className="text-[11px] text-muted-foreground">
          Step-by-step pass rate across all personas — red bars show where users fail or get stuck.
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {funnels.map((f) => (
          <JourneyFunnelCard key={f.journeyId} funnel={f} />
        ))}
      </div>
    </Panel>
  );
}

// ── D3: Fix Hierarchy Panel ────────────────────────────────────────────────────
// Three-section layout: "Fix before launch" (P0), "Fix this week" (P1),
// "On the radar" (P2/P3, collapsed by default). Togglable Founder/Developer view.

function FixIssueRow({
  issue,
  bundle,
  founderMode,
}: {
  issue: Issue;
  bundle: RunBundle;
  founderMode: boolean;
}) {
  const issueAnnotation = bundle.annotations.find(
    (a) => a.targetType === "issue" && a.targetId === issue.id,
  );

  if (founderMode) {
    return (
      <div className="p-5">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium mb-3">{issue.title}</h3>
            <FindingStoryCard issue={issue} videoUrl={null} runId={bundle.summary.id} />
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <IssueAnnotationActions
              runId={bundle.summary.id}
              issue={issue}
              existing={issueAnnotation}
            />
            <EvidenceDialog issue={issue} runId={bundle.summary.id}>
              <button
                type="button"
                className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1 px-2 py-1 rounded-md border border-border hover:bg-surface-2"
              >
                <Camera className="size-3" /> Evidence
              </button>
            </EvidenceDialog>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 hover:bg-surface-2/30">
      <div className="flex items-start gap-3">
        <SeverityChip s={issue.severity} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-medium">{issue.title}</h3>
            <Chip>{issue.dimension}</Chip>
            <Chip tone={issue.confidence === "high" ? "info" : "warn"}>{issue.confidence}</Chip>
            <Chip>owner · {issue.owner}</Chip>
            {issue.recurring > 1 && <Chip tone="danger">recurring ×{issue.recurring}</Chip>}
          </div>
          <p className="text-sm text-muted-foreground mt-2 font-mono">{issue.evidence}</p>
          <div className="text-xs text-muted-foreground mt-2">
            {issue.persona} · {issue.journey} · <span className="font-mono">{issue.stepId}</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <IssueAnnotationActions
            runId={bundle.summary.id}
            issue={issue}
            existing={issueAnnotation}
          />
          <EvidenceDialog issue={issue} runId={bundle.summary.id}>
            <button
              type="button"
              className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1 px-2 py-1 rounded-md border border-border hover:bg-surface-2"
            >
              <Camera className="size-3" /> Evidence
            </button>
          </EvidenceDialog>
        </div>
      </div>
    </div>
  );
}

function FixSection({
  title,
  sub,
  tone,
  issues,
  bundle,
  founderMode,
  bordered = true,
}: {
  title?: string;
  sub?: string;
  tone: "danger" | "warn" | "neutral";
  issues: Issue[];
  bundle: RunBundle;
  founderMode: boolean;
  bordered?: boolean;
}) {
  const headerBorder =
    tone === "danger" ? "border-danger/30" : tone === "warn" ? "border-warn/20" : "border-border";
  const bg = tone === "danger" ? "bg-danger/5" : tone === "warn" ? "bg-warn/5" : "";
  const titleColor =
    tone === "danger" ? "text-danger" : tone === "warn" ? "text-warn" : "text-foreground";

  return (
    <div className={`border-t border-border ${bg}`}>
      {title && (
        <div className={`px-5 py-3 border-b ${headerBorder} flex items-center gap-3`}>
          <span className={`text-sm font-semibold ${titleColor}`}>{title}</span>
          {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
        </div>
      )}
      <div className={bordered ? "divide-y divide-border" : ""}>
        {issues.map((i) => (
          <FixIssueRow key={i.id} issue={i} bundle={bundle} founderMode={founderMode} />
        ))}
      </div>
    </div>
  );
}

export function FixHierarchyPanel({ bundle }: { bundle: RunBundle }) {
  const [founderMode, setFounderMode] = useState(() => {
    try {
      return localStorage.getItem("trylapse-view-mode") !== "dev";
    } catch {
      return true;
    }
  });
  const [radarOpen, setRadarOpen] = useState(false);

  const setMode = (dev: boolean) => {
    setFounderMode(!dev);
    try {
      localStorage.setItem("trylapse-view-mode", dev ? "dev" : "founder");
    } catch {
      // localStorage unavailable (e.g. private browsing) — view mode just won't persist
    }
  };

  const p0 = bundle.issues.filter((i) => i.severity === "P0");
  const p1 = bundle.issues.filter((i) => i.severity === "P1");
  const radar = bundle.issues.filter((i) => i.severity === "P2" || i.severity === "P3");

  if (!bundle.issues.length) return null;

  return (
    <Panel className="overflow-hidden" id="findings">
      <div className="p-5 border-b border-border flex items-center justify-between gap-3 flex-wrap">
        <div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide font-medium mb-0.5">
            Action plan
          </div>
          <div className="text-sm text-muted-foreground">
            {bundle.issues.length} finding{bundle.issues.length !== 1 ? "s" : ""} across{" "}
            {new Set(bundle.issues.map((i) => i.journey)).size} journey
            {new Set(bundle.issues.map((i) => i.journey)).size !== 1 ? "s" : ""}
          </div>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-2 p-1 rounded-lg border border-border">
          <button
            type="button"
            onClick={() => setMode(false)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${founderMode ? "bg-background shadow-sm font-medium text-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            Founder view
          </button>
          <button
            type="button"
            onClick={() => setMode(true)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${!founderMode ? "bg-background shadow-sm font-medium text-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            Developer view
          </button>
        </div>
      </div>

      {p0.length > 0 && (
        <FixSection
          title="Fix before you launch"
          sub={`${p0.length} blocker${p0.length !== 1 ? "s" : ""} — will cost real users`}
          tone="danger"
          issues={p0}
          bundle={bundle}
          founderMode={founderMode}
        />
      )}

      {p1.length > 0 && (
        <FixSection
          title="Fix this week"
          sub={`${p1.length} issue${p1.length !== 1 ? "s" : ""}`}
          tone="warn"
          issues={p1}
          bundle={bundle}
          founderMode={founderMode}
        />
      )}

      {radar.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setRadarOpen((o) => !o)}
            className="w-full p-4 border-t border-border flex items-center justify-between text-sm hover:bg-surface-2/30 transition-colors"
          >
            <span className="font-medium text-muted-foreground">
              On the radar
              <span className="ml-2 text-xs font-normal">
                {radar.length} lower-priority observation{radar.length !== 1 ? "s" : ""}
              </span>
            </span>
            <span className="text-xs text-muted-foreground">{radarOpen ? "▲ hide" : "▼ show"}</span>
          </button>
          {radarOpen && (
            <FixSection tone="neutral" issues={radar} bundle={bundle} founderMode={founderMode} />
          )}
        </div>
      )}
    </Panel>
  );
}

// ── D4: Share Report Dialog ───────────────────────────────────────────────────
// Pre-written Slack / Email message a founder can send without editing.

function buildShareMessage(bundle: RunBundle, format: "slack" | "email"): string {
  const { narrative, issues, summary } = bundle;
  const verdict = narrative?.layer1Verdict;
  const p0 = issues.filter((i) => i.severity === "P0");
  const p1 = issues.filter((i) => i.severity === "P1");

  const b = (s: string) => (format === "slack" ? `*${s}*` : s);

  const lines: string[] = [];

  if (format === "email") {
    const decisionLabel =
      verdict?.decision === "ship"
        ? "Clear to ship"
        : verdict?.decision === "caution"
          ? "Almost ready"
          : "Don't launch yet";
    lines.push(
      `Subject: TryLapse found ${issues.length} thing${issues.length !== 1 ? "s" : ""} before launch — ${decisionLabel}`,
    );
    lines.push("");
  }

  lines.push(verdict?.headline ?? `TryLapse run complete — ${summary.readiness}/100 readiness`);
  if (verdict?.reason) lines.push(verdict.reason);
  lines.push("");

  if (p0.length > 0) {
    lines.push(b(`🔴 Fix before launch (${p0.length}):`));
    p0.slice(0, 3).forEach((i) => lines.push(`• ${i.title}`));
    lines.push("");
  }

  if (p1.length > 0) {
    lines.push(b(`🟡 Fix this week (${p1.length}):`));
    p1.slice(0, 5).forEach((i) => lines.push(`• ${i.title}`));
    lines.push("");
  }

  if (narrative?.layer4Forward?.length) {
    lines.push(b("Next actions:"));
    narrative.layer4Forward.slice(0, 3).forEach((a) => lines.push(`→ ${a}`));
    lines.push("");
  }

  lines.push(`Full report: [open in TryLapse dashboard]`);
  lines.push(
    `Run on ${new Date(summary.finishedAt).toLocaleDateString()} · ${summary.durationSec}s · ${summary.agentsRun ?? 0} agents`,
  );

  return lines.join("\n");
}

export function ShareReportDialog({ bundle }: { bundle: RunBundle }) {
  const [format, setFormat] = useState<"slack" | "email">("slack");
  const [copied, setCopied] = useState(false);

  const message = buildShareMessage(bundle, format);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard write denied/unavailable — the share dialog stays open, nothing to recover
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-border hover:bg-surface-2 transition-colors"
        >
          <Share2 className="size-3" />
          Share
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Share report</DialogTitle>
          <DialogDescription>Pre-written message you can send without editing</DialogDescription>
        </DialogHeader>
        <div className="flex gap-1 mb-2">
          {(["slack", "email"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFormat(f)}
              className={`px-3 py-1 text-xs rounded-md border transition-colors ${
                format === f
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border hover:bg-surface-2 text-muted-foreground"
              }`}
            >
              {f === "slack" ? "Slack" : "Email"}
            </button>
          ))}
        </div>
        <pre className="text-xs bg-surface-2 border border-border rounded-lg p-4 whitespace-pre-wrap max-h-64 overflow-y-auto font-mono">
          {message}
        </pre>
        <DialogFooter>
          <button
            type="button"
            onClick={handleCopy}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            {copied ? "Copied!" : "Copy to clipboard"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── D5: Trend Sparkline ───────────────────────────────────────────────────────
// Score trajectory across recent runs for the same product.
// Shows delta from last run and resolved issue count — the dopamine hit.

const BAND_COLOR: Record<string, string> = {
  green: "var(--ready)",
  amber: "var(--warn)",
  red: "var(--danger)",
};

export function TrendSparkline({
  currentSummary,
  allSummaries,
}: {
  currentSummary: RunSummary;
  allSummaries: RunSummary[];
}) {
  const history = allSummaries
    .filter(
      (s) =>
        s.productName === currentSummary.productName &&
        (s.status === "complete" || s.outcome === "complete") &&
        s.id !== currentSummary.id,
    )
    .sort((a, b) => new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime())
    .slice(-14);

  const dots = [...history, currentSummary];
  if (dots.length < 2) return null;

  const scores = dots.map((d) => d.readiness);
  const minScore = Math.max(0, Math.min(...scores) - 5);
  const maxScore = Math.min(100, Math.max(...scores) + 5);
  const range = maxScore - minScore || 1;

  const prev = dots[dots.length - 2];
  const delta =
    currentSummary.scoreDelta != null
      ? currentSummary.scoreDelta
      : currentSummary.readiness - prev.readiness;
  const resolvedCount =
    prev.blockers != null && currentSummary.blockers != null
      ? Math.max(0, prev.blockers - currentSummary.blockers)
      : 0;

  const allGreen = dots.length >= 5 && dots.slice(-5).every((d) => d.readinessBand === "green");

  return (
    <Panel className="p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide font-medium mb-1">
            Score trend · last {dots.length} run{dots.length !== 1 ? "s" : ""}
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {delta !== 0 && (
              <span className={`text-sm font-semibold ${delta > 0 ? "text-ready" : "text-danger"}`}>
                {delta > 0 ? "+" : ""}
                {delta} pts from last run
              </span>
            )}
            {resolvedCount > 0 && (
              <span className="text-xs text-ready">
                ✓ {resolvedCount} blocker{resolvedCount !== 1 ? "s" : ""} resolved
              </span>
            )}
            {delta === 0 && resolvedCount === 0 && (
              <span className="text-xs text-muted-foreground">Score unchanged from last run</span>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-bold tabular-nums">{currentSummary.readiness}</div>
          <div className="text-xs text-muted-foreground">readiness</div>
        </div>
      </div>

      <div className="flex items-end gap-1 h-10">
        {dots.map((d) => {
          const pct = (d.readiness - minScore) / range;
          const height = Math.max(4, Math.round(pct * 36));
          const isCurrent = d.id === currentSummary.id;
          const color = BAND_COLOR[d.readinessBand] ?? "var(--muted-foreground)";
          return (
            <div
              key={d.id}
              title={`${d.readiness} · ${d.readinessBand}`}
              className="flex-1 rounded-sm transition-all"
              style={{
                height: `${height}px`,
                background: color,
                opacity: isCurrent ? 1 : 0.4,
                outline: isCurrent ? `2px solid ${color}` : undefined,
                outlineOffset: isCurrent ? "2px" : undefined,
              }}
            />
          );
        })}
      </div>

      {allGreen && (
        <div className="mt-3 text-xs text-ready border border-ready/30 bg-ready/5 rounded-md px-3 py-2">
          Consistently green — you've built a reliable release process.
        </div>
      )}
    </Panel>
  );
}
