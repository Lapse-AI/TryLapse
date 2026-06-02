import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip, SeverityChip } from "@/components/ui-bits";
import { useLatestRun, useBacklog, useRunBundle } from "@/lib/api/hooks";
import { exportBacklogToLinear } from "@/lib/linear-export";
import { Download, Rocket, Target } from "lucide-react";

export const Route = createFileRoute("/recommendations")({
  head: () => ({ meta: [{ title: "Recommendations — Launch Rehearsal" }] }),
  component: Recommendations,
});

function Recommendations() {
  const latest = useLatestRun();
  const { data: bundle } = useRunBundle(latest?.id ?? "");
  const { data: backlogItems = [] } = useBacklog();
  const fixBeforeLaunch = backlogItems.filter((b) => b.fixBeforeLaunch);
  const backlog = backlogItems.filter((b) => !b.fixBeforeLaunch);
  const delights = bundle?.delights ?? [];
  if (!latest) return null;

  return (
    <div>
      <PageHeader
        eyebrow="analysis"
        title="Recommendations & backlog"
        description="Prioritized export — no auto-fix. Evidence-bound suggestions aligned with Evaluation rubric."
        actions={
          <button
            type="button"
            onClick={() =>
              exportBacklogToLinear(backlogItems, bundle?.issues ?? [], { runId: latest.id })
            }
            className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground inline-flex items-center gap-1.5"
          >
            <Download className="size-3.5" /> Export to Linear
          </button>
        }
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-6 border-danger/30">
          <div className="flex items-center gap-2 mb-4">
            <Rocket className="size-4 text-danger" />
            <h2 className="font-display text-lg font-semibold">Fix before launch</h2>
            <Chip tone="danger">{fixBeforeLaunch.length} items</Chip>
          </div>
          <div className="space-y-3">
            {fixBeforeLaunch.map((b) => (
              <div
                key={b.id}
                className="flex items-center justify-between border border-border rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <SeverityChip s={b.severity} />
                  <div>
                    <div className="font-medium">{b.title}</div>
                    <div className="text-xs text-muted-foreground mt-0.5 capitalize">
                      owner · {b.owner}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  {b.exportTargets.map((t) => (
                    <Chip key={t}>{t}</Chip>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Target className="size-4 text-primary" />
            <h2 className="font-display text-lg font-semibold">Prioritized backlog</h2>
          </div>
          <div className="divide-y divide-border">
            {backlog.map((b) => (
              <div key={b.id} className="py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <SeverityChip s={b.severity} />
                  <span>{b.title}</span>
                </div>
                <Chip tone="neutral">{b.owner}</Chip>
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-3">
            Delights to protect (regression watch)
          </div>
          {delights.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No delights in {latest.id} — scorecard still emits the required section.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {delights.map((d) => (
                <div key={d.id} className="border border-ready/30 rounded-lg p-3 bg-ready/5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="font-medium">{d.title}</div>
                    {d.confidence && (
                      <Chip tone={d.confidence === "high" ? "info" : "warn"}>{d.confidence}</Chip>
                    )}
                  </div>
                  <blockquote className="text-sm italic mt-1 text-foreground/80">
                    &ldquo;{d.quote}&rdquo;
                  </blockquote>
                  <div className="text-[11px] text-muted-foreground mt-2">
                    Latest run:{" "}
                    <Link
                      to="/runs/$runId"
                      params={{ runId: latest.id }}
                      className="text-primary font-mono"
                    >
                      {latest.id}
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel className="p-6">
          <div className="text-xs text-muted-foreground mb-2">
            Competitive benchmark slot (manual)
          </div>
          <p className="text-sm text-muted-foreground">
            Optional compare URL — paste a competitor for side-by-side rubric scoring. Phase 2.
          </p>
          <input
            placeholder="https://competitor.example.com"
            className="mt-3 w-full max-w-md bg-surface border border-border rounded-md px-3 py-2 text-sm font-mono"
            disabled
          />
        </Panel>
      </div>
    </div>
  );
}
