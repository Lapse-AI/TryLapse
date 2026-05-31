import { useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { z } from "zod";
import {
  PageHeader,
  Panel,
  Chip,
  StatusDot,
  SeverityChip,
  Stat,
  Bar,
  ClientTime,
} from "@/components/ui-bits";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  EvidenceDialog,
  StepsTable,
  ScorecardPanel,
  SitemapPanel,
  ScreenshotGallery,
  DiffPanel,
  AnnotationsPanel,
  ExportMenu,
} from "@/components/run-detail";
import {
  formatDuration,
  bandFromIssues,
  countBlockers,
  bundlePersonas,
  bundleJourneys,
  cellGrade,
  type Severity,
  type Issue,
} from "@/lib/mock-data";
import { useRunBundle, useRunSummaries } from "@/lib/api/hooks";
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
  Image as ImageIcon,
  Filter,
  ExternalLink,
  ListTree,
  FileText,
  Camera,
  MessageSquare,
  GitBranch,
} from "lucide-react";

const searchSchema = z.object({
  tab: z.string().optional(),
  step: z.string().optional(),
});

export const Route = createFileRoute("/runs/$runId")({
  validateSearch: searchSchema,
  head: ({ params }) => ({ meta: [{ title: `${params.runId} — Run detail` }] }),
  component: RunDetail,
  notFoundComponent: () => (
    <div className="p-12 text-center text-muted-foreground">Run not found.</div>
  ),
});

const ALL_SEVERITIES: Severity[] = ["P0", "P1", "P2", "P3"];

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

function RunDetail() {
  const { runId } = Route.useParams();
  const { tab: tabSearch, step: highlightStepId } = Route.useSearch();
  const navigate = Route.useNavigate();
  const { data: bundle, isLoading } = useRunBundle(runId);
  const { data: runSummaries = [] } = useRunSummaries();
  const [active, setActive] = useState<Set<Severity>>(new Set(ALL_SEVERITIES));
  const [compareRunId, setCompareRunId] = useState(runSummaries[1]?.id ?? "");
  const [activeTab, setActiveTab] = useState(tabSearch ?? "overview");

  useEffect(() => {
    if (tabSearch) setActiveTab(tabSearch);
  }, [tabSearch]);

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
  const filtered = bundle.issues.filter((i) => active.has(i.severity));
  const band = bandFromIssues(bundle.issues);
  const blockerCount = countBlockers(bundle.issues);

  const toggle = (s: Severity) => {
    const next = new Set(active);
    if (next.has(s)) {
      next.delete(s);
    } else {
      next.add(s);
    }
    if (next.size === 0) ALL_SEVERITIES.forEach((x) => next.add(x));
    setActive(next);
  };

  return (
    <div>
      <PageHeader
        eyebrow={`Run · ${run.env}`}
        title={run.id}
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
            <Link
              to="/compare"
              search={{ a: runSummaries[1]?.id, b: run.id }}
              className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5"
            >
              <GitCompare className="size-3.5" /> Diff
            </Link>
            <ExportMenu runId={run.id} bundle={bundle} />
          </>
        }
      />

      <div className="p-4 md:p-8 space-y-6 max-w-[1400px]">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Stat
            label="Readiness"
            value={run.readiness}
            tone={band}
            hint={`Band: ${run.readinessBand}`}
          />
          <Stat label="Blockers" value={blockerCount} hint="P0 + P1" tone="danger" />
          <Stat label="Delights" value={run.delights} tone="ready" />
          <Stat
            label="Steps"
            value={run.stepCount}
            hint={`${bundle.steps.filter((s) => s.flaky).length} flaky`}
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
              search: (prev) => ({
                ...prev,
                tab: v === "overview" ? undefined : v,
                step: v === "steps" ? prev.step : undefined,
              }),
            });
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
          </TabsList>

          <TabsContent value="overview" className="space-y-8 mt-0">
            <Panel className="p-4 md:p-6 overflow-x-auto">
              <div className="flex items-end justify-between mb-5 gap-3 flex-wrap">
                <div>
                  <div className="text-xs text-muted-foreground">Persona × journey matrix</div>
                  <h2 className="font-display text-xl font-semibold mt-1">
                    {runPersonas.length} personas × {runJourneys.length} journeys
                  </h2>
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
                        <div className="text-[10px] font-mono text-muted-foreground mt-0.5">
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
                        <div className="text-[10px] font-mono text-muted-foreground">{p.role}</div>
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
              <div className="text-xs text-muted-foreground mb-4">
                Dimension rollup · {bundle.dimensions.filter((d) => d.automated).length} automated ·{" "}
                {bundle.dimensions.filter((d) => !d.automated).length} Phase 2
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-4">
                {bundle.dimensions.map((d) => {
                  const tone = d.score >= 85 ? "ready" : d.score >= 75 ? "warn" : "danger";
                  return (
                    <div key={d.name}>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-sm">
                          {d.name}
                          {!d.automated && (
                            <span className="text-[10px] text-muted-foreground ml-1">(P2)</span>
                          )}
                        </span>
                        <span
                          className="font-mono tabular-nums"
                          style={{ color: `var(--${tone})` }}
                        >
                          {d.score}
                        </span>
                      </div>
                      <Bar value={d.score} tone={tone} />
                      {d.signal && (
                        <div className="text-[10px] text-muted-foreground mt-1">{d.signal}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Panel>

            <Panel className="overflow-hidden">
              <div className="p-5 border-b border-border flex items-center justify-between flex-wrap gap-3">
                <div>
                  <div className="text-xs text-muted-foreground inline-flex items-center gap-1.5">
                    <Filter className="size-3" /> Filter
                  </div>
                  <h2 className="font-display text-lg font-semibold mt-0.5">
                    {filtered.length} of {bundle.issues.length} findings
                  </h2>
                </div>
                <div className="flex items-center gap-1 flex-wrap">
                  {ALL_SEVERITIES.map((s) => {
                    const on = active.has(s);
                    const count = bundle.issues.filter((i) => i.severity === s).length;
                    const tone =
                      s === "P0" ? "danger" : s === "P1" ? "warn" : s === "P2" ? "info" : "neutral";
                    return (
                      <button
                        key={s}
                        type="button"
                        onClick={() => toggle(s)}
                        aria-pressed={on}
                        className={`px-2.5 py-1 rounded-md border text-[11px] font-mono inline-flex items-center gap-1.5 transition-colors ${on ? "" : "text-muted-foreground border-border bg-surface hover:bg-surface-2"}`}
                        style={
                          on
                            ? {
                                color: `var(--${tone})`,
                                borderColor: `color-mix(in oklab, var(--${tone}) 40%, var(--border))`,
                                background: `color-mix(in oklab, var(--${tone}) 10%, transparent)`,
                              }
                            : undefined
                        }
                      >
                        {s} · {count}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="divide-y divide-border">
                {filtered.length === 0 ? (
                  <div className="p-10 text-center text-sm text-muted-foreground">
                    No findings match the active filters.
                  </div>
                ) : (
                  filtered.map((i) => (
                    <div key={i.id} className="p-5 hover:bg-surface-2/30">
                      <div className="flex items-start gap-3">
                        <SeverityChip s={i.severity} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-medium">{i.title}</h3>
                            <Chip>{i.dimension}</Chip>
                            <Chip tone={i.confidence === "high" ? "info" : "warn"}>
                              {i.confidence}
                            </Chip>
                            <Chip>owner · {i.owner}</Chip>
                            {i.recurring > 1 && <Chip tone="danger">recurring ×{i.recurring}</Chip>}
                          </div>
                          <p className="text-sm text-muted-foreground mt-2 font-mono">
                            {i.evidence}
                          </p>
                          <div className="text-xs text-muted-foreground mt-2">
                            {i.persona} · {i.journey} ·{" "}
                            <span className="font-mono">{i.stepId}</span>
                          </div>
                        </div>
                        <EvidenceDialog issue={i} runId={run.id}>
                          <button
                            type="button"
                            className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1 px-2 py-1 rounded-md border border-border hover:bg-surface-2 shrink-0"
                          >
                            <ImageIcon className="size-3" /> Evidence
                          </button>
                        </EvidenceDialog>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Panel>

            {bundle.delights.length > 0 && (
              <Panel className="p-6">
                <div className="text-xs text-muted-foreground mb-4">
                  Delights — required section
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {bundle.delights.map((d) => (
                    <div key={d.id} className="border border-border rounded-lg p-4 bg-surface-2/30">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{d.title}</h4>
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
                    {bundle.agents.filter((a) => a.status !== "idle").length} agents · $
                    {bundle.agents.reduce((s, a) => s + a.costUsd, 0).toFixed(2)}
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
                      <p className="text-xs mt-2 text-foreground/80">{a.lastSummary}</p>
                    </div>
                  ))}
              </div>
            </Panel>
          </TabsContent>

          <TabsContent value="scorecard">
            <Panel className="overflow-hidden">
              <ScorecardPanel markdown={bundle.scorecardMd} />
            </Panel>
          </TabsContent>
          <TabsContent value="steps">
            <Panel className="overflow-hidden">
              <StepsTable steps={bundle.steps} highlightStepId={highlightStepId} />
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
          <TabsContent value="annotations">
            <Panel className="overflow-hidden">
              <AnnotationsPanel annotations={bundle.annotations} />
            </Panel>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
