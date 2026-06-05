import { createFileRoute, Link } from "@tanstack/react-router";
import {
  PageHeader,
  Panel,
  ReadinessGauge,
  Sparkline,
  Stat,
  Chip,
  StatusDot,
  ClientTime,
} from "@/components/ui-bits";
import { DimensionRollupGrid } from "@/components/dimension-rollup";
import { formatDuration, bandFromIssues, countBlockers } from "@/lib/mock-data";
import { formatAgentCostDisplay, READINESS_BAND_HELP } from "@/lib/run-metrics";
import {
  useLatestRun,
  useRunBundle,
  useRunSummaries,
  useTrends,
  useCommandDigest,
  useTriggerJob,
  useApiHealth,
  useJobs,
} from "@/lib/api/hooks";
import { ActiveJobsBanner } from "@/components/job-queue-status";
import {
  ArrowRight,
  Sparkles,
  AlertOctagon,
  Clock,
  Activity,
  Play,
  GitCompare,
  Network,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  Heart,
} from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Command center — Launch Rehearsal" }] }),
  component: Index,
});

function Index() {
  const latest = useLatestRun();
  const { data: bundle, isLoading } = useRunBundle(latest?.id ?? "");
  const { data: runSummaries = [] } = useRunSummaries();
  const { data: trends } = useTrends();
  const { data: digest } = useCommandDigest(7);
  const { data: live } = useApiHealth();
  const { data: jobs } = useJobs();
  const trigger = useTriggerJob();

  const jobsRunning = (jobs ?? []).some((j) => j.status === "running" || j.status === "queued");
  const liveChipTone = jobsRunning ? "info" : live ? "ready" : "warn";
  const liveChipLabel = jobsRunning ? "running" : live ? "live" : "offline";

  if (!latest || isLoading || !bundle) {
    return (
      <div className="p-12 text-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin inline mr-2" />
        Loading command center…
      </div>
    );
  }
  const band = bandFromIssues(bundle.issues);
  const blockerCount = countBlockers(bundle.issues);
  const agentCost = formatAgentCostDisplay(bundle);
  const topBlocker = bundle.issues.find((i) => i.severity === "P0") ?? bundle.issues[0];
  const topDelight = bundle.delights[0];

  const recurringCount = bundle.issues.filter((i) => i.recurring > 1).length;
  const flakeRates = trends?.flakeRate ?? [];
  const recentFlake = flakeRates.slice(-7);
  const flakeValue =
    recentFlake.length > 0
      ? recentFlake.at(-1)!
      : bundle.steps.length
        ? Math.round((bundle.steps.filter((s) => s.flaky).length / bundle.steps.length) * 1000) / 10
        : 0;
  const priorFlake = flakeRates.length >= 2 ? flakeRates.at(-2)! : null;
  const flakeDelta = priorFlake !== null ? Math.round((flakeValue - priorFlake) * 10) / 10 : null;
  const flakeHint =
    flakeRates.length >= 2 && flakeDelta !== null
      ? `${flakeDelta >= 0 ? "+" : ""}${flakeDelta}% vs prior run`
      : flakeRates.length > 0
        ? `over ${flakeRates.length} run${flakeRates.length === 1 ? "" : "s"}`
        : "single run";
  const flakeTone = flakeValue <= 2 ? "ready" : flakeValue <= 5 ? "warn" : "danger";

  const recurringHint =
    recurringCount === 0
      ? "none recurring across runs"
      : recurringCount === 1
        ? "1 issue seen in multiple runs"
        : `${recurringCount} issues seen in multiple runs`;

  const scorecardHint =
    runSummaries.length > 1 ? `${runSummaries.length} runs · goal < 15m` : "goal < 15m";
  const scorecardTone = latest.durationSec <= 900 ? "ready" : "warn";

  return (
    <div>
      {jobsRunning && jobs && jobs.length > 0 && (
        <div className="px-8 pt-6 max-w-[1400px]">
          <ActiveJobsBanner jobs={jobs} />
        </div>
      )}
      <PageHeader
        eyebrow="Command center"
        title="Pre-launch readiness, observed."
        description={`Live rollup of every persona × journey rehearsal against ${latest.target}. Evidence-bound, no auto-fix.`}
        actions={
          <>
            <Chip tone={liveChipTone}>
              <span
                className={`size-1.5 rounded-full ${live ? "bg-ready" : "bg-warn pulse-dot"}`}
              />{" "}
              {liveChipLabel}
            </Chip>
            {runSummaries.length >= 2 ? (
              <Link
                to="/compare"
                search={{ a: runSummaries[1]?.id, b: latest.id }}
                hash="visual-diff"
                className="text-xs px-3 py-1.5 rounded-md border border-border/70 hover:bg-surface-2 inline-flex items-center gap-1.5 text-muted-foreground"
              >
                <GitCompare className="size-3.5" /> Compare runs
              </Link>
            ) : (
              <Link
                to="/compare"
                className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2 inline-flex items-center gap-1.5 text-muted-foreground"
                title="Need two runs to compare"
              >
                <GitCompare className="size-3.5" /> Compare
              </Link>
            )}
            <Link
              to="/runs"
              className="text-xs px-3 py-1.5 rounded-md border border-border hover:bg-surface-2"
            >
              All runs →
            </Link>
          </>
        }
      />

      <div className="p-4 md:p-8 space-y-7 max-w-[1400px]">
        {digest &&
          (() => {
            const trendWord = digest.readinessTrend?.toLowerCase() ?? "";
            const trendTone =
              trendWord.includes("improv") || trendWord.includes("stable")
                ? "ready"
                : trendWord.includes("soft") || trendWord.includes("declin")
                  ? "warn"
                  : "neutral";
            const TrendIcon = trendWord.includes("improv")
              ? TrendingUp
              : trendWord.includes("soft") || trendWord.includes("declin")
                ? TrendingDown
                : Minus;
            return (
              <div className="relative overflow-hidden rounded-xl panel-glass px-6 py-5">
                {/* Vertical gradient accent bar */}
                <div
                  className="absolute left-0 top-0 bottom-0 w-[3px]"
                  style={{
                    background: `linear-gradient(180deg, var(--primary) 0%, color-mix(in oklab, var(--primary) 15%, transparent) 100%)`,
                  }}
                />

                {/* Header row */}
                <div className="flex items-center gap-2.5 flex-wrap mb-3">
                  <Sparkles className="size-3.5 text-primary" />
                  <span className="font-display text-[15px] font-semibold">Situation report</span>
                  <Chip>{digest.source === "llm+template" ? "AI + rules" : "Rules"}</Chip>
                  <Chip tone={trendTone as "ready" | "warn" | "neutral"}>
                    <TrendIcon className="size-3" />
                    {digest.readinessTrend}
                  </Chip>
                </div>

                {/* Headline */}
                <p className="text-sm leading-relaxed max-w-2xl font-medium text-foreground/90">
                  {digest.headline}
                </p>

                {/* Bullets */}
                <ul className="mt-3 space-y-1.5">
                  {digest.bullets.map((b) => (
                    <li key={b} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="mt-[7px] size-1 rounded-full bg-primary/40 shrink-0" />
                      {b}
                    </li>
                  ))}
                </ul>

                {/* Signal mini-cards */}
                <div className="mt-5 pt-4 border-t border-border/40 grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Top blocker */}
                  <div className="rounded-lg border border-border/60 bg-surface/70 p-3.5 backdrop-blur-sm">
                    <div className="flex items-center gap-1.5 mb-2">
                      <AlertOctagon className="size-3 text-muted-foreground" />
                      <span className="text-[11px] text-muted-foreground font-medium">
                        Top signal
                      </span>
                    </div>
                    {topBlocker ? (
                      <>
                        <p className="text-sm font-semibold leading-snug line-clamp-2">
                          {topBlocker.title}
                        </p>
                        <div className="flex items-center gap-1.5 mt-2">
                          <Chip tone="danger">{topBlocker.severity}</Chip>
                          <Chip>{topBlocker.dimension}</Chip>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm font-semibold text-ready">No blockers this run</p>
                    )}
                  </div>

                  {/* Readiness trend */}
                  <div className="rounded-lg border border-border/60 bg-surface/70 p-3.5 backdrop-blur-sm">
                    <div className="flex items-center gap-1.5 mb-2">
                      <Activity className="size-3 text-muted-foreground" />
                      <span className="text-[11px] text-muted-foreground font-medium">
                        Readiness trend
                      </span>
                    </div>
                    <div className="flex items-baseline gap-1.5">
                      <span
                        className="font-display text-2xl font-bold tabular-nums"
                        style={{ color: `var(--${band})` }}
                      >
                        {latest.readiness}
                      </span>
                      <span className="text-[11px] text-muted-foreground font-mono">
                        / 100 · {latest.readinessBand}
                      </span>
                    </div>
                    <div className="mt-2 h-8">
                      <Sparkline
                        values={(trends?.readiness ?? [latest.readiness]) as number[]}
                        height={28}
                        color={`var(--${trendTone === "ready" ? "ready" : trendTone === "warn" ? "warn" : "info"})`}
                        className="w-full"
                      />
                    </div>
                  </div>

                  {/* Latest delight */}
                  <div className="rounded-lg border border-border/60 bg-surface/70 p-3.5 backdrop-blur-sm">
                    <div className="flex items-center gap-1.5 mb-2">
                      <Heart className="size-3 text-muted-foreground" />
                      <span className="text-[11px] text-muted-foreground font-medium">
                        Latest delight
                      </span>
                    </div>
                    {topDelight ? (
                      <>
                        <p className="text-sm font-semibold leading-snug line-clamp-2">
                          {topDelight.title}
                        </p>
                        <p className="mt-1.5 text-[11px] text-muted-foreground truncate italic">
                          &ldquo;{topDelight.quote}&rdquo;
                        </p>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        {latest.delights} delight{latest.delights !== 1 ? "s" : ""} found this run
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}
        {/* Quick actions */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={!live || trigger.isPending}
            onClick={() => trigger.mutate({ mode: "run" })}
            className="text-xs px-3.5 py-2 rounded-lg bg-primary text-primary-foreground inline-flex items-center gap-1.5 font-semibold hover:opacity-90 disabled:opacity-40 transition-all"
            style={{ boxShadow: "var(--shadow-primary)" }}
          >
            {trigger.isPending ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <Play className="size-3.5" />
            )}{" "}
            Run rehearsal
          </button>
          <button
            type="button"
            disabled={!live || trigger.isPending}
            onClick={() => trigger.mutate({ mode: "crawl" })}
            className="text-xs px-3 py-1.5 rounded-md border border-border/80 text-foreground/85 hover:bg-surface-2 inline-flex items-center gap-1.5 disabled:opacity-50"
          >
            <Network className="size-3.5" /> Crawl only
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
          <Panel className="md:col-span-4 p-6 flex items-center justify-center panel-elevated">
            <ReadinessGauge value={latest.readiness} band={band} />
          </Panel>

          <Panel className="md:col-span-5 p-6 panel-glass">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-muted-foreground">Latest run</div>
                <Link
                  to="/runs/$runId"
                  params={{ runId: latest.id }}
                  className="font-mono text-sm mt-1 text-primary hover:underline"
                >
                  {latest.id}
                </Link>
              </div>
              <Chip tone={band}>{latest.env}</Chip>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-muted-foreground">Blockers</div>
                <div className="font-display text-2xl font-semibold text-danger tabular-nums">
                  {blockerCount}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Delights</div>
                <div className="font-display text-2xl font-semibold text-ready tabular-nums">
                  {latest.delights}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Duration</div>
                <div className="font-display text-2xl font-semibold tabular-nums">
                  {formatDuration(latest.durationSec)}
                </div>
              </div>
            </div>
            <div className="mt-5 border-t border-border pt-4 flex items-center justify-between">
              <div className="text-xs text-muted-foreground">
                {latest.pages} pages crawled ·{" "}
                <ClientTime iso={latest.startedAt} fallback="just now" />
              </div>
              <Link
                to="/runs/$runId"
                params={{ runId: latest.id }}
                className="text-xs font-medium text-primary flex items-center gap-1 hover:underline"
              >
                Open run <ArrowRight className="size-3" />
              </Link>
            </div>
          </Panel>

          <Panel className="md:col-span-3 p-6 panel-glass flex flex-col">
            <div className="text-xs text-muted-foreground">{runSummaries.length}-run trend</div>
            <div className="mt-3 grow flex items-center">
              <Sparkline
                values={trends?.readiness ?? [latest.readiness]}
                height={64}
                className="w-full h-16"
              />
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground font-mono">
              <span>{(trends?.readiness ?? [])[0] ?? latest.readiness}</span>
              <span className="text-ready">
                {(trends?.readiness?.length ?? 0) > 1
                  ? `over ${trends!.readiness.length} runs`
                  : "single run"}
              </span>
              <span>{trends?.readiness?.at(-1) ?? latest.readiness}</span>
            </div>
          </Panel>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
          <Stat
            label="Time to first scorecard"
            value={formatDuration(latest.durationSec)}
            hint={scorecardHint}
            tone={scorecardTone}
          />
          <Stat
            label={`Flake rate${flakeRates.length ? ` (${Math.min(7, flakeRates.length)}d)` : ""}`}
            value={`${flakeValue}%`}
            hint={flakeHint}
            tone={flakeTone}
          />
          <Stat
            label="Recurring blockers"
            value={String(recurringCount)}
            hint={recurringHint}
            tone={recurringCount > 0 ? "warn" : "ready"}
          />
          <Stat
            label="Agent cost / run"
            value={agentCost.value}
            hint={`${agentCost.hint} · ${bundle.agents.filter((a) => a.status !== "idle").length} agents`}
          />
        </div>

        <Panel className="p-6 border-border/60">
          <div className="flex items-end justify-between mb-5">
            <div>
              <div className="text-xs text-muted-foreground">Dimension rollup</div>
              <h2 className="font-display text-xl font-semibold mt-1">8-axis evaluation</h2>
              <p
                className="text-xs text-muted-foreground mt-1 max-w-prose leading-relaxed"
                title={READINESS_BAND_HELP}
              >
                {READINESS_BAND_HELP}
              </p>
            </div>
            <Chip>Evaluation rubric</Chip>
          </div>
          <DimensionRollupGrid
            dimensions={bundle.dimensions}
            issues={bundle.issues}
            runId={latest.id}
            mode="navigate"
          />
        </Panel>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topBlocker && (
            <Panel className="p-6 panel-quiet">
              <div className="flex items-center gap-2 mb-3">
                <AlertOctagon className="size-4 text-danger" />
                <div className="text-xs text-muted-foreground">Top blocker — fix before launch</div>
              </div>
              <h3 className="font-display text-lg font-semibold">{topBlocker.title}</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                <Chip tone="danger">{topBlocker.severity}</Chip>
                <Chip tone="info">{topBlocker.dimension}</Chip>
                <Chip>seen {topBlocker.recurring}× runs</Chip>
              </div>
              <p className="mt-3 text-sm text-muted-foreground font-mono">{topBlocker.evidence}</p>
              <Link
                to="/recommendations"
                className="mt-4 text-xs text-primary hover:underline inline-block"
              >
                View fix-before-launch list →
              </Link>
            </Panel>
          )}

          {topDelight ? (
            <Panel className="p-6 panel-quiet">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="size-4 text-muted-foreground" />
                <div className="text-xs text-muted-foreground">Delight worth shipping with</div>
              </div>
              <h3 className="font-display text-lg font-semibold">{topDelight.title}</h3>
              <blockquote className="mt-3 border-l-2 border-ready pl-3 italic text-sm text-foreground/90">
                &ldquo;{topDelight.quote}&rdquo;
              </blockquote>
              <div className="mt-3 text-xs text-muted-foreground">
                — {topDelight.persona}, {topDelight.journey}
              </div>
            </Panel>
          ) : (
            <Panel className="p-6 panel-quiet">
              <div className="text-xs text-muted-foreground">Delights</div>
              <p className="mt-2 text-sm text-muted-foreground">
                No delights detected this run — required section still emitted in scorecard.
              </p>
            </Panel>
          )}
        </div>

        <Panel className="overflow-hidden border-border/60">
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="size-4 text-primary" />
              <span className="font-display text-base font-semibold">Recent runs</span>
            </div>
            <Link to="/runs" className="text-xs text-muted-foreground hover:text-foreground">
              View all →
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border">
                  <th className="text-left px-5 py-2 font-medium">Run</th>
                  <th className="text-left px-5 py-2 font-medium">Product</th>
                  <th className="text-left px-5 py-2 font-medium">Env</th>
                  <th className="text-left px-5 py-2 font-medium">Readiness</th>
                  <th className="text-left px-5 py-2 font-medium">Blockers</th>
                  <th className="text-left px-5 py-2 font-medium">Delights</th>
                  <th className="text-left px-5 py-2 font-medium">Duration</th>
                  <th className="text-right px-5 py-2 font-medium">When</th>
                </tr>
              </thead>
              <tbody>
                {runSummaries.slice(0, 6).map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-border last:border-0 hover:bg-surface-2/50"
                  >
                    <td className="px-5 py-3">
                      <Link
                        to="/runs/$runId"
                        params={{ runId: r.id }}
                        className="font-mono text-xs hover:text-primary"
                      >
                        {r.id}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-xs">{r.productName}</td>
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
                        <span
                          className="font-mono tabular-nums"
                          style={{ color: `var(--${r.status})` }}
                        >
                          {r.readiness}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3 font-mono tabular-nums text-danger">{r.blockers}</td>
                    <td className="px-5 py-3 font-mono tabular-nums text-ready">{r.delights}</td>
                    <td className="px-5 py-3 font-mono text-muted-foreground">
                      <Clock className="inline size-3 mr-1" />
                      {formatDuration(r.durationSec)}
                    </td>
                    <td className="px-5 py-3 text-right text-muted-foreground text-xs">
                      <ClientTime iso={r.startedAt} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}
