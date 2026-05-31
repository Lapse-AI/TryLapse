import { createFileRoute } from "@tanstack/react-router";
import { InsightNarrativePanel } from "@/components/InsightNarrativePanel";
import { PageHeader, Panel, Sparkline, Stat, Chip } from "@/components/ui-bits";
import { scheduledRuns } from "@/lib/mock-data";
import { useLatestRun, useRunBundle, useTrends } from "@/lib/api/hooks";
import { VisionOnly } from "@/components/vision-only";

export const Route = createFileRoute("/trends")({
  head: () => ({ meta: [{ title: "Trends — Launch Rehearsal" }] }),
  component: Trends,
});

function Trends() {
  const latest = useLatestRun();
  const { data: bundle } = useRunBundle(latest?.id ?? "");
  const { data: trends } = useTrends();
  const readinessTrend = trends?.readiness ?? [];
  const crawlSizeTrend = trends?.pages ?? [];
  const flakeRateTrend = trends?.flakeRate ?? [];
  const recurrence = trends?.issueRecurrence ?? [];
  const readinessAvg =
    readinessTrend.length > 0
      ? (readinessTrend.reduce((a, b) => a + b, 0) / readinessTrend.length).toFixed(1)
      : "—";
  if (!latest || !bundle) return null;

  const issuesOpened = trends?.issuesOpened;
  const issuesResolved = trends?.issuesResolved;

  return (
    <div>
      <PageHeader
        eyebrow="monitor"
        title="Trends & monitoring"
        description="Readiness drift, recurring issues, flake rate, crawl size — observe the curve, not the snapshot."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <InsightNarrativePanel title="Trends insight" narrative={trends?.narrative} />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Readiness avg (7d)" value={readinessAvg} tone="warn" hint="goal ≥ 80" />
          <Stat
            label="Issues opened"
            value={issuesOpened ?? "—"}
            hint={issuesOpened != null ? "new in latest run" : "from artifacts"}
          />
          <Stat
            label="Issues resolved"
            value={issuesResolved ?? "—"}
            tone={issuesResolved && issuesResolved > 0 ? "ready" : "neutral"}
            hint={issuesResolved != null ? "since prior run" : "from artifacts"}
          />
          <Stat
            label="Flake rate"
            value={`${flakeRateTrend.at(-1) ?? "—"}%`}
            tone="ready"
            hint="of all steps"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Readiness trend</div>
            <div className="mt-3">
              <Sparkline values={readinessTrend} height={48} />
            </div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Crawl size trend</div>
            <div className="mt-3">
              <Sparkline values={crawlSizeTrend} color="var(--info)" height={48} />
            </div>
            <div className="text-[11px] font-mono text-muted-foreground mt-2">
              {crawlSizeTrend.at(-1)} pages latest
            </div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Flake rate trend</div>
            <div className="mt-3">
              <Sparkline values={flakeRateTrend} color="var(--warn)" height={48} />
            </div>
          </Panel>
        </div>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground">
            Readiness by dimension — latest run ({latest.id})
          </div>
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4">
            {bundle.dimensions.map((d) => (
              <div key={d.name} className="text-sm">
                <span className="text-muted-foreground">{d.name}</span>
                <span className="font-mono ml-2 tabular-nums">{d.score}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="text-xs text-muted-foreground">Issue recurrence</div>
              <Chip tone="neutral">Phase 2</Chip>
            </div>
            <div className="font-display text-base font-semibold mt-0.5">
              Same issue, multiple runs
            </div>
          </div>
          {recurrence.length === 0 ? (
            <div className="p-8 text-sm text-muted-foreground text-center">
              No recurring issues across stored runs yet.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border">
                  <th className="text-left px-5 py-2 font-medium">Issue</th>
                  <th className="text-left px-5 py-2 font-medium">Runs seen</th>
                  <th className="text-left px-5 py-2 font-medium">Status</th>
                  <th className="text-right px-5 py-2 font-medium">First seen</th>
                </tr>
              </thead>
              <tbody>
                {recurrence.map((i, idx) => (
                  <tr
                    key={`${i.name}-${idx}`}
                    className="border-b border-border last:border-0 hover:bg-surface-2/40"
                  >
                    <td className="px-5 py-3">{i.name}</td>
                    <td className="px-5 py-3 font-mono tabular-nums">{i.runs}×</td>
                    <td className="px-5 py-3">
                      <Chip
                        tone={
                          i.status === "new"
                            ? "info"
                            : i.status === "regression"
                              ? "danger"
                              : i.status === "open"
                                ? "warn"
                                : "neutral"
                        }
                      >
                        {i.status}
                      </Chip>
                    </td>
                    <td className="px-5 py-3 text-right text-muted-foreground font-mono text-xs">
                      {i.first}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <VisionOnly section="trends.scheduledRuns">
        <Panel className="p-6">
          <div className="flex items-center gap-2 mb-3">
            <div className="text-xs text-muted-foreground">
              Scheduled runs · rehearse schedule (planned CLI)
            </div>
            <Chip tone="neutral">Phase 2</Chip>
          </div>
          <div className="space-y-2 mb-4">
            {scheduledRuns.map((s, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-sm font-mono border border-border rounded-md px-3 py-2"
              >
                <span>{s.cron}</span>
                <Chip tone={s.enabled ? "ready" : "neutral"}>{s.env}</Chip>
                <span className="text-xs text-muted-foreground">next {s.next.slice(0, 10)}</span>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: 14 }).map((_, i) => {
              const has = [0, 1, 3, 5, 6, 8, 10, 12, 13].includes(i);
              return (
                <div
                  key={i}
                  className={`aspect-square rounded border ${has ? "bg-primary/20 border-primary/40" : "bg-surface-2 border-border"} flex items-center justify-center text-xs font-mono`}
                >
                  {i + 1}
                </div>
              );
            })}
          </div>
        </Panel>
        </VisionOnly>
      </div>
    </div>
  );
}
