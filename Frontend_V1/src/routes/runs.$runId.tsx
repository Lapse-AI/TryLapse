import { useEffect, useState } from "react";
import { createFileRoute, Link, useParams, useSearch, useNavigate } from "@tanstack/react-router";
import { z } from "zod";
import {
  PageHeader,
  Panel,
  Chip,
  StatusDot,
  SeverityChip,
  Stat,
  ClientTime,
  LaunchGateBadge,
  ScoreDeltaBadge,
  BenchmarkContext,
} from "@/components/ui-bits";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DimensionRollupGrid, DimensionBreakdownBanner } from "@/components/dimension-rollup";
import {
  StepsTable,
  ScorecardPanel,
  SitemapPanel,
  ScreenshotGallery,
  DiffPanel,
  RunObservabilityPanel,
  AnnotationsPanel,
  ExportMenu,
  RunNarrativePanel,
  VerdictBanner,
  FunnelPanel,
  FixHierarchyPanel,
  ShareReportDialog,
  TrendSparkline,
} from "@/components/run-detail";
import { ManualAnnotationPanel } from "@/components/manual-annotation-panel";
import { CrawlLiveGraph } from "@/components/crawl-live-graph";
import { JourneyStepTree, type JourneyStepTreeStep } from "@/components/journey-step-tree";
import { ExperimentRunBanner } from "@/components/experiment-spec-panel";
import {
  formatDuration,
  bandFromIssues,
  countBlockers,
  bundlePersonas,
  bundleJourneys,
  cellGrade,
  matrixGrade,
  type Issue,
} from "@/lib/mock-data";
import {
  flakyStepsHint,
  formatAgentCostDisplay,
  READINESS_BAND_HELP,
  displayAgentSummary,
} from "@/lib/run-metrics";
import { countIssuesForDimension } from "@/lib/dimension-match";
import { useRunBundle, useRunSummaries, useTriggerJob } from "@/lib/api/hooks";
import { getWorkspace } from "@/lib/workspace";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  GitCompare,
  ExternalLink,
  ListTree,
  FileText,
  Camera,
  MessageSquare,
  GitBranch,
  Network,
  RotateCcw,
} from "lucide-react";
import { toast } from "sonner";

const searchSchema = z.object({
  tab: z.string().optional(),
  step: z.string().optional(),
  dimension: z.string().optional(),
});

type RunSearch = z.infer<typeof searchSchema>;

export const Route = createFileRoute("/runs/$runId")({
  validateSearch: searchSchema,
  head: ({ params }) => ({ meta: [{ title: `${params.runId} — Run detail` }] }),
  component: RunDetail,
  notFoundComponent: () => (
    <div className="p-12 text-center text-muted-foreground">Run not found.</div>
  ),
});

function formatRunId(id: string): string {
  const m = id.match(/(\d{8})-(\d{6})$/);
  if (!m) return id;
  const [, date, time] = m;
  try {
    const dt = new Date(
      `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}T${time.slice(0, 2)}:${time.slice(2, 4)}:00`,
    );
    if (isNaN(dt.getTime())) return id;
    return (
      dt.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
      " · " +
      dt.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    );
  } catch {
    return id;
  }
}

function MatrixCellDialog({
  pi,
  ji,
  grade,
  issues,
  persona,
  journey,
}: {
  pi: number;
  ji: number;
  grade: ReturnType<typeof matrixGrade>;
  issues: Issue[];
  persona: { name: string; role: string; goal: string };
  journey: { name: string; category: string; steps: number; id?: string };
}) {
  const matching = issues.filter(
    (i) => i.persona === persona.name && (i.journey === journey.name || i.journeyId === journey.id),
  );
  const label = grade === "pass" ? "pass" : grade === "partial" ? "partial" : "fail";
  const tone = grade === "pass" ? "ready" : grade === "partial" ? "warn" : "danger";
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          aria-label={`${persona.name}, ${journey.name}: ${label}`}
          className="h-12 w-full rounded-md border flex items-center justify-center text-[11px] font-mono uppercase tracking-wider cursor-pointer transition-all hover:scale-[1.04] focus:outline-none focus:ring-2 focus:ring-ring"
          style={{
            background: `color-mix(in oklab, var(--${tone}) 14%, transparent)`,
            borderColor: `color-mix(in oklab, var(--${tone}) 45%, var(--border))`,
            color: `var(--${tone})`,
          }}
        >
          {label}
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <Chip tone={tone}>{label}</Chip>
            <Chip>{journey.category}</Chip>
            <Chip>{journey.steps} steps</Chip>
          </div>
          <DialogTitle className="font-display">
            {persona.name} · {journey.name}
          </DialogTitle>
          <DialogDescription>
            {persona.role} — goal: {persona.goal}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {matching.length === 0 ? (
            <div className="text-sm text-muted-foreground border border-dashed border-border rounded-md p-4 text-center">
              No findings for this cell — journey completed cleanly.
            </div>
          ) : (
            matching.map((i) => (
              <div key={i.id} className="border border-border rounded-md p-3">
                <div className="flex items-center gap-2 mb-1">
                  <SeverityChip s={i.severity} />
                  <span className="text-sm font-medium">{i.title}</span>
                </div>
                <p className="text-xs font-mono text-muted-foreground">{i.evidence}</p>
                <div className="text-[11px] text-muted-foreground mt-1.5">
                  step <span className="font-mono">{i.stepId}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function RunDetail() {
  // Use strict:false so this component works from both /runs/$runId
  // and /$workspaceSlug/runs/$runId without route-specific binding.
  const { runId } = useParams({ strict: false }) as { runId: string };
  const {
    tab: tabSearch,
    step: highlightStepId,
    dimension: dimensionFilter,
  } = useSearch({ strict: false }) as {
    tab?: string;
    step?: string;
    dimension?: string;
  };
  const navigate = useNavigate();
  const { data: bundle, isLoading } = useRunBundle(runId);
  const { data: runSummaries = [] } = useRunSummaries();
  const [compareRunId, setCompareRunId] = useState(runSummaries[1]?.id ?? "");
  const trigger = useTriggerJob();
  const wsSlug = getWorkspace()?.slug;
  const [activeTab, setActiveTab] = useState(tabSearch ?? "overview");

  useEffect(() => {
    if (tabSearch) setActiveTab(tabSearch);
  }, [tabSearch]);

  useEffect(() => {
    if (!dimensionFilter) return;
    const el = document.getElementById("dimension-breakdown");
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [dimensionFilter, bundle?.summary.id]);

  const selectDimension = (name: string) => {
    const next = dimensionFilter === name ? undefined : name;

    void navigate({
      search: (prev: RunSearch): RunSearch => ({ ...prev, dimension: next }),
      hash: next ? "dimension-breakdown" : undefined,
    } as Parameters<typeof navigate>[0]);
  };

  const activeDimensionMeta = dimensionFilter
    ? bundle?.dimensions.find((d) => d.name === dimensionFilter)
    : undefined;

  useEffect(() => {
    if (!highlightStepId || activeTab !== "steps") return;
    const el = document.getElementById(`step-${highlightStepId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightStepId, activeTab, bundle?.steps.length]);

  if (isLoading || !bundle) {
    return <div className="p-12 text-center text-muted-foreground">Loading run…</div>;
  }

  const run = bundle.summary;
  const runPersonas = bundlePersonas(bundle);
  const runJourneys = bundleJourneys(bundle);
  const band = bandFromIssues(bundle.issues);
  const blockerCount = countBlockers(bundle.issues);

  return (
    <div>
      <PageHeader
        eyebrow={`Run · ${run.env}`}
        title={formatRunId(run.id)}
        description={
          <>
            {run.productName} ·{" "}
            <a
              href={run.targetUrl}
              className="text-primary hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              {run.target}
            </a>
            {" · "}
            <ClientTime iso={run.startedAt} /> · {formatDuration(run.durationSec)}
            {" · "}config {run.configHash}
            {run.authAttempted && (
              <>
                {" "}
                · auth{" "}
                <Chip tone={run.authOutcome?.includes("fail") ? "danger" : "ready"}>
                  {run.authOutcome}
                </Chip>
              </>
            )}
          </>
        }
        actions={
          <>
            <button
              type="button"
              disabled={trigger.isPending}
              onClick={() => {
                const configId = run.configId ?? run.id.replace(/-\d{8}-\d{6}$/, "");
                trigger.mutate(
                  { mode: "run", configPath: configId, llm: true },
                  { onSuccess: () => toast.success("Re-run triggered — check the Runner page") },
                );
              }}
              className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5 disabled:opacity-40"
              title="Re-run with the same config"
            >
              <RotateCcw className="size-3.5" />
              {trigger.isPending ? "Triggering…" : "Re-run"}
            </button>
            {wsSlug ? (
              <Link
                to="/$workspaceSlug/compare"
                params={{ workspaceSlug: wsSlug }}
                search={{ a: runSummaries[1]?.id, b: run.id }}
                className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
              >
                <GitCompare className="size-3.5" /> Diff
              </Link>
            ) : (
              <Link
                to="/compare"
                search={{ a: runSummaries[1]?.id, b: run.id }}
                className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
              >
                <GitCompare className="size-3.5" /> Diff
              </Link>
            )}
            <ExportMenu runId={run.id} bundle={bundle} />
          </>
        }
      />

      <div className="p-4 md:p-8 space-y-6 max-w-[1400px]">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Stat
            label="Readiness"
            value={
              <span className="flex items-baseline gap-2">
                {run.readiness}
                {run.scoreDelta != null && run.scoreDelta !== 0 && (
                  <ScoreDeltaBadge delta={run.scoreDelta} />
                )}
              </span>
            }
            tone={band}
            hint={run.launchGate ? undefined : `Band: ${run.readinessBand}`}
            title={READINESS_BAND_HELP}
          >
            {run.launchGate && (
              <div className="mt-2">
                <LaunchGateBadge gate={run.launchGate} />
              </div>
            )}
            {run.industryBenchmark && <BenchmarkContext bench={run.industryBenchmark} />}
          </Stat>
          <Stat label="Blockers" value={blockerCount} hint="Critical + High" tone="danger" />
          <Stat label="Highlights" value={run.delights} tone="ready" />
          <Stat
            label="Steps"
            value={run.stepCount}
            hint={flakyStepsHint(bundle.steps)}
            title="Flaky = same step outcome varied across parallel seeds"
          />
          <Stat
            label="Pages"
            value={run.pages || "—"}
            hint={
              run.crawlEnabled
                ? `${run.orphans ?? 0} orphans · ${run.authGated ?? 0} auth-gated`
                : "crawl off"
            }
          />
        </div>

        <Tabs
          value={activeTab}
          onValueChange={(v) => {
            setActiveTab(v);

            void navigate({
              search: (prev: RunSearch): RunSearch => ({
                ...prev,
                tab: v === "overview" ? undefined : v,
                step: v === "steps" ? prev.step : undefined,
              }),
            } as Parameters<typeof navigate>[0]);
          }}
          className="space-y-4"
        >
          <TabsList className="flex flex-wrap h-auto gap-1 bg-surface-2 p-1">
            <TabsTrigger value="overview" className="text-xs">
              Overview
            </TabsTrigger>
            <TabsTrigger value="scorecard" className="text-xs">
              <FileText className="size-3 mr-1 inline" />
              Scorecard
            </TabsTrigger>
            <TabsTrigger value="steps" className="text-xs">
              <ListTree className="size-3 mr-1 inline" />
              Steps ({bundle.steps.length})
            </TabsTrigger>
            <TabsTrigger value="journeys" className="text-xs">
              <ListTree className="size-3 mr-1 inline" />
              Journeys
            </TabsTrigger>
            <TabsTrigger value="crawl-graph" className="text-xs">
              <Network className="size-3 mr-1 inline" />
              Crawl Graph
            </TabsTrigger>
            <TabsTrigger value="sitemap" className="text-xs">
              <GitBranch className="size-3 mr-1 inline" />
              Sitemap
            </TabsTrigger>
            <TabsTrigger value="screenshots" className="text-xs">
              <Camera className="size-3 mr-1 inline" />
              Screenshots
            </TabsTrigger>
            <TabsTrigger value="diff" className="text-xs">
              <GitCompare className="size-3 mr-1 inline" />
              Diff
            </TabsTrigger>
            <TabsTrigger value="annotations" className="text-xs">
              <MessageSquare className="size-3 mr-1 inline" />
              Annotations
            </TabsTrigger>
            <TabsTrigger value="recordings" className="text-xs">
              <Camera className="size-3 mr-1 inline" />
              Recording
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-8 mt-0">
            {bundle.narrative?.layer1Verdict && (
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <VerdictBanner verdict={bundle.narrative.layer1Verdict} />
                </div>
                <div className="pt-1 shrink-0">
                  <ShareReportDialog bundle={bundle} />
                </div>
              </div>
            )}
            <ExperimentRunBanner experiment={run.experiment} />
            {run.outcome === "partial" && bundle.steps.length > 0 && (
              <Panel className="p-4 border border-warn/30 bg-warn/5 flex items-start gap-3">
                <span className="text-warn text-lg mt-0.5">⚠</span>
                <div>
                  <div className="text-sm font-semibold text-warn">
                    Partial run — timed out or stopped early
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {bundle.steps.length} step{bundle.steps.length !== 1 ? "s" : ""} captured before
                    the run was interrupted. Results below reflect only the completed journeys.
                    Re-run to get the full picture.
                  </p>
                </div>
              </Panel>
            )}
            {bundle.steps.length === 0 && (bundle.parallelErrors?.length ?? 0) > 0 && (
              <Panel className="p-4 border border-danger/30 bg-danger/5 space-y-2">
                <div className="text-sm font-semibold text-danger">
                  Journey execution failed — 0 steps recorded
                </div>
                <p className="text-xs text-muted-foreground">
                  Parallel browser workers threw errors. Auth cookies may not have reached workers,
                  or Playwright threading failed. Check errors below, then restart the server and
                  re-run.
                </p>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {bundle.parallelErrors!.map((e, i) => (
                    <pre
                      key={i}
                      className="text-[10px] font-mono text-danger/80 bg-surface/60 rounded px-2 py-1 whitespace-pre-wrap"
                    >
                      {e}
                    </pre>
                  ))}
                </div>
              </Panel>
            )}
            {bundle.steps.length === 0 &&
              (bundle.parallelErrors?.length ?? 0) === 0 &&
              run.stepCount === 0 && (
                <Panel className="p-4 border border-warn/30 bg-warn/5">
                  <div className="text-sm font-semibold text-warn">0 browser steps recorded</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Journey execution produced no step data. Common causes: auth wasn't set up
                    (check Config → Run credentials), all journeys failed immediately, or the server
                    wasn't restarted after a code change.
                  </p>
                </Panel>
              )}
            <RunNarrativePanel runId={run.id} bundle={bundle} />
            <RunObservabilityPanel bundle={bundle} />
            <TrendSparkline currentSummary={run} allSummaries={runSummaries} />
            <Panel className="p-4 md:p-6 overflow-x-auto">
              <div className="flex items-end justify-between mb-5 gap-3 flex-wrap">
                <div>
                  <div className="text-xs text-muted-foreground">Persona × journey matrix</div>
                  <h2 className="font-display text-xl font-semibold mt-1">
                    {runPersonas.length} personas × {runJourneys.length} journeys
                  </h2>
                  <p className="text-[11px] text-muted-foreground mt-2 max-w-xl">
                    Browser steps run as the first persona (evaluator) only. Medium and Low severity
                    columns reflect the same technical journey outcome through persona-specific
                    findings, not separate browser sessions.
                  </p>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1.5">
                    <StatusDot status="ready" /> pass
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <StatusDot status="warn" /> partial
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <StatusDot status="danger" /> fail
                  </span>
                </div>
              </div>
              <table className="w-full text-sm border-collapse min-w-[600px]">
                <thead>
                  <tr>
                    <th className="text-left p-2" />
                    {runJourneys.map((j) => (
                      <th key={j.id} className="text-left p-2 font-normal">
                        <div className="text-xs font-medium">{j.name}</div>
                        <div className="text-[11px] font-mono text-muted-foreground mt-0.5">
                          {j.category} · {j.steps} steps
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {runPersonas.map((p, pi) => (
                    <tr key={p.id} className="border-t border-border">
                      <td className="p-2 align-top">
                        <div className="text-sm font-medium">{p.name}</div>
                        <div className="text-[11px] font-mono text-muted-foreground">{p.role}</div>
                      </td>
                      {runJourneys.map((j, ji) => (
                        <td key={j.id} className="p-2">
                          <MatrixCellDialog
                            pi={pi}
                            ji={ji}
                            grade={cellGrade(bundle, p.id, j.id)}
                            issues={bundle.issues}
                            persona={p}
                            journey={j}
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>

            <Panel className="p-6">
              <div className="text-xs text-muted-foreground mb-2">
                Dimension rollup · {bundle.dimensions.filter((d) => d.automated).length} automated ·{" "}
                {bundle.dimensions.filter((d) => !d.automated).length} estimated
              </div>
              <p className="text-[11px] text-muted-foreground mb-4 max-w-2xl">
                {READINESS_BAND_HELP}
              </p>
              <DimensionRollupGrid
                dimensions={bundle.dimensions}
                issues={bundle.issues}
                runId={run.id}
                activeDimension={dimensionFilter}
                mode="filter"
                onSelect={selectDimension}
              />
            </Panel>

            {activeDimensionMeta && (
              <DimensionBreakdownBanner
                dimension={activeDimensionMeta}
                relatedCount={countIssuesForDimension(bundle.issues, activeDimensionMeta.name)}
                onClear={() =>
                  void navigate({
                    search: (prev: RunSearch): RunSearch => ({ ...prev, dimension: undefined }),
                    hash: undefined,
                  } as Parameters<typeof navigate>[0])
                }
              />
            )}

            <FunnelPanel bundle={bundle} />

            <FixHierarchyPanel bundle={bundle} />

            {bundle.delights.length > 0 && (
              <Panel className="p-6">
                <div className="text-xs text-muted-foreground mb-4">Highlights</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {bundle.delights.map((d) => (
                    <div key={d.id} className="border border-border rounded-lg p-4 bg-surface-2/30">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-medium">{d.title}</h4>
                        {d.confidence && (
                          <Chip tone={d.confidence === "high" ? "info" : "warn"}>
                            {d.confidence}
                          </Chip>
                        )}
                        {d.marketingReady && <Chip tone="ready">marketing-ready</Chip>}
                        {d.regressionRisk && <Chip tone="warn">regression risk</Chip>}
                      </div>
                      <blockquote className="mt-2 border-l-2 border-ready pl-3 text-sm italic text-foreground/90">
                        &ldquo;{d.quote}&rdquo;
                      </blockquote>
                      <div className="mt-2 text-[11px] text-muted-foreground">— {d.persona}</div>
                    </div>
                  ))}
                </div>
              </Panel>
            )}

            <Panel className="p-6">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <div>
                  <div className="text-xs text-muted-foreground">Agent participation</div>
                  <h2 className="font-display text-lg font-semibold mt-0.5">
                    {bundle.agents.filter((a) => a.status !== "idle").length} agents ·{" "}
                    {formatAgentCostDisplay(bundle).value}{" "}
                    <span className="text-muted-foreground font-normal text-xs">
                      ({formatAgentCostDisplay(bundle).hint})
                    </span>
                    {run.llmEnabled && <Chip tone="violet">LLM on</Chip>}
                  </h2>
                </div>
                <Link
                  to="/agents"
                  className="text-xs text-primary inline-flex items-center gap-1 hover:underline"
                >
                  Control center <ExternalLink className="size-3" />
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {bundle.agents
                  .filter((a) => a.status !== "idle")
                  .map((a) => (
                    <div key={a.id} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">{a.name}</div>
                        <Chip
                          tone={
                            a.status === "done"
                              ? "ready"
                              : a.status === "running"
                                ? "info"
                                : "danger"
                          }
                        >
                          {a.status}
                        </Chip>
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-1">{a.role}</div>
                      <div className="mt-2 flex items-center justify-between font-mono text-[11px] text-muted-foreground">
                        <span>{formatDuration(a.durationSec)}</span>
                        <span>${a.costUsd.toFixed(2)}</span>
                      </div>
                      <p className="text-xs mt-2 text-foreground/80">
                        {displayAgentSummary(a.lastSummary)}
                      </p>
                    </div>
                  ))}
              </div>
            </Panel>
          </TabsContent>

          <TabsContent value="scorecard">
            <Panel className="overflow-hidden">
              <ScorecardPanel markdown={bundle.scorecardMd} bundle={bundle} />
            </Panel>
          </TabsContent>
          <TabsContent value="steps">
            <Panel className="overflow-hidden">
              <StepsTable steps={bundle.steps} highlightStepId={highlightStepId} />
            </Panel>
          </TabsContent>
          <TabsContent value="journeys">
            <Panel className="p-6">
              <div className="text-sm font-medium mb-1">Journey execution tree</div>
              <p className="text-xs text-muted-foreground mb-4">
                Each persona's journeys and their step-by-step outcomes. Click any row to expand.
              </p>
              <JourneyStepTree
                steps={bundle.steps as unknown as JourneyStepTreeStep[]}
                personas={runPersonas.map((p) => ({ id: p.id, name: p.name }))}
                journeys={runJourneys.map((j) => ({ id: j.id, name: j.name }))}
              />
            </Panel>
          </TabsContent>
          <TabsContent value="crawl-graph">
            <Panel className="p-6">
              <div className="text-sm font-medium mb-4">
                Crawl graph — pages discovered during crawl phase
              </div>
              <CrawlLiveGraph runId={run.id} phase="done" pollingMs={0} />
            </Panel>
          </TabsContent>
          <TabsContent value="sitemap">
            <Panel className="overflow-hidden">
              <SitemapPanel markdown={bundle.sitemapMd} />
            </Panel>
          </TabsContent>
          <TabsContent value="screenshots">
            <Panel className="overflow-hidden">
              <ScreenshotGallery shots={bundle.screenshots} />
            </Panel>
          </TabsContent>
          <TabsContent value="diff">
            <Panel className="overflow-hidden">
              <div className="p-4 border-b border-border flex items-center gap-3 flex-wrap">
                <span className="text-xs text-muted-foreground">Compare with:</span>
                <select
                  value={compareRunId}
                  onChange={(e) => setCompareRunId(e.target.value)}
                  className="bg-surface border border-border rounded-md px-2 py-1 text-sm font-mono"
                >
                  {runSummaries
                    .filter((r) => r.id !== run.id)
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.id}
                      </option>
                    ))}
                </select>
              </div>
              {compareRunId && <DiffPanel runA={compareRunId} runB={run.id} />}
            </Panel>
          </TabsContent>
          <TabsContent value="annotations" className="space-y-4">
            <ManualAnnotationPanel runId={run.id} />
            <Panel className="overflow-hidden">
              <AnnotationsPanel runId={run.id} annotations={bundle.annotations} />
            </Panel>
          </TabsContent>
          <TabsContent value="recordings">
            <Panel className="overflow-hidden">
              <div className="relative">
                <div className="p-4 space-y-4 blur-sm pointer-events-none select-none opacity-50">
                  <h3 className="text-sm font-semibold">Journey Recording</h3>
                  <p className="text-xs text-muted-foreground">
                    View event replay and video recordings of journeys
                  </p>
                  <div className="h-32 bg-surface-2 rounded-lg" />
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="bg-surface border border-border rounded-2xl px-8 py-6 text-center shadow-xl">
                    <div className="size-12 rounded-xl bg-warn/10 border border-warn/20 flex items-center justify-center mx-auto mb-3">
                      <Camera className="size-6 text-warn" />
                    </div>
                    <h3 className="font-display text-base font-semibold">Recordings Coming Soon</h3>
                    <p className="text-xs text-muted-foreground mt-1.5 max-w-xs">
                      rrweb session replay will be available in a future release.
                    </p>
                  </div>
                </div>
              </div>
            </Panel>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
