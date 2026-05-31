import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, Panel, Sparkline, Stat, Chip } from "@/components/ui-bits";
import { issueRecurrence, scheduledRuns, dimensions } from "@/lib/mock-data";
import { useLatestRun, useRunBundle, useTrends } from "@/lib/api/hooks";

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
  if (!latest || !bundle) return null;

  return (
    <div>
      <PageHeader eyebrow="monitor" title="Trends & monitoring" description="Readiness drift, recurring issues, flake rate, crawl size — observe the curve, not the snapshot." />
      <div className="p-8 max-w-[1400px] space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Readiness avg (7d)" value="76.6" tone="warn" hint="goal ≥ 80" />
          <Stat label="Issues opened" value={5} hint="last 7 days" />
          <Stat label="Issues resolved" value={7} tone="ready" hint="net −2" />
          <Stat label="Flake rate" value={`${flakeRateTrend.at(-1)}%`} tone="ready" hint="of all steps" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Readiness trend</div>
            <div className="mt-3"><Sparkline values={readinessTrend} height={48} /></div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Crawl size trend</div>
            <div className="mt-3"><Sparkline values={crawlSizeTrend} color="var(--info)" height={48} /></div>
            <div className="text-[11px] font-mono text-muted-foreground mt-2">{crawlSizeTrend.at(-1)} pages latest</div>
          </Panel>
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground">Flake rate trend</div>
            <div className="mt-3"><Sparkline values={flakeRateTrend} color="var(--warn)" height={48} /></div>
          </Panel>
        </div>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground">Readiness by dimension — {readinessTrend.length} runs</div>
          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-6">
            {bundle.dimensions.map((d, i) => {
              const seed = readinessTrend.map((v, j) => Math.max(40, Math.min(100, v + ((i * 3 + j) % 7) - 3)));
              const tone = d.score >= 85 ? "var(--ready)" : d.score >= 75 ? "var(--warn)" : "var(--danger)";
              return (
                <div key={d.name}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">{d.name}</span>
                    <span className="font-mono text-sm tabular-nums" style={{ color: tone }}>{d.score}</span>
                  </div>
                  <Sparkline values={seed} color={tone} height={32} />
                </div>
              );
            })}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="p-5 border-b border-border">
            <div className="text-xs text-muted-foreground">Issue recurrence</div>
            <div className="font-display text-base font-semibold mt-0.5">Same issue, multiple runs</div>
          </div>
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
              {issueRecurrence.map((i, idx) => (
                <tr key={idx} className="border-b border-border last:border-0 hover:bg-surface-2/40">
                  <td className="px-5 py-3">{i.name}</td>
                  <td className="px-5 py-3 font-mono tabular-nums">{i.runs}×</td>
                  <td className="px-5 py-3">
                    <Chip tone={i.status === "new" ? "info" : i.status === "regression" ? "danger" : i.status === "open" ? "warn" : "neutral"}>{i.status}</Chip>
                  </td>
                  <td className="px-5 py-3 text-right text-muted-foreground font-mono text-xs">{i.first}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-3">Scheduled runs · rehearse schedule (planned CLI)</div>
          <div className="space-y-2 mb-4">
            {scheduledRuns.map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm font-mono border border-border rounded-md px-3 py-2">
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
                <div key={i} className={`aspect-square rounded border ${has ? "bg-primary/20 border-primary/40" : "bg-surface-2 border-border"} flex items-center justify-center text-xs font-mono`}>
                  {i + 1}
                </div>
              );
            })}
          </div>
        </Panel>
      </div>
    </div>
  );
}
