import { useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { Layers, Loader2, CheckCircle2, XCircle } from "lucide-react";

export const Route = createFileRoute("/cohort/$jobId")({
  head: () => ({ meta: [{ title: "Cohort rehearsal — Launch Rehearsal" }] }),
  component: CohortReport,
});

type CohortJob = Awaited<ReturnType<typeof api.getCohortJob>>;

const CONFIDENCE_TONE = { high: "ready", medium: "warn", low: "neutral" } as const;

function SeedProgress({ completed, total }: { completed: number; total: number }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Seeds completed</span>
        <span className="font-mono">
          {completed} / {total}
        </span>
      </div>
      <div className="h-2 rounded-full bg-surface-2 overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${total > 0 ? (completed / total) * 100 : 0}%` }}
        />
      </div>
    </div>
  );
}

function ConfidenceBand({ agg }: { agg: NonNullable<CohortJob["aggregate"]> }) {
  const range = agg.readinessMax - agg.readinessMin;
  const barWidth = Math.max(range, 4);

  return (
    <Panel className="p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Layers className="size-4 text-primary" />
        <span className="font-display font-semibold text-sm">Readiness confidence band</span>
        <Chip tone={CONFIDENCE_TONE[agg.confidence] ?? "neutral"}>{agg.confidence} confidence</Chip>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>0</span>
          <span>50</span>
          <span>100</span>
        </div>
        <div className="relative h-6 rounded-full bg-surface-2 overflow-hidden">
          {/* Band */}
          <div
            className="absolute h-full bg-primary/20 rounded-full"
            style={{
              left: `${agg.readinessMin}%`,
              width: `${barWidth}%`,
            }}
          />
          {/* Mean marker */}
          <div
            className="absolute top-1 h-4 w-1 rounded-full bg-primary"
            style={{ left: `${agg.readinessMean}%` }}
          />
        </div>
        <div className="flex justify-between text-xs font-mono">
          <span className="text-muted-foreground">min {agg.readinessMin}</span>
          <span className="font-semibold text-primary">mean {agg.readinessMean}</span>
          <span className="text-muted-foreground">max {agg.readinessMax}</span>
        </div>
      </div>

      <div className="text-xs text-muted-foreground">
        Spread {agg.spread} pts across {agg.nSeeds} seeds —{" "}
        {agg.confidence === "high"
          ? "tight band, high repeatability"
          : agg.confidence === "medium"
            ? "moderate variance, run more seeds for certainty"
            : "wide variance — results are flaky or environment unstable"}
      </div>
    </Panel>
  );
}

export default function CohortReport() {
  const { jobId } = Route.useParams();
  const [job, setJob] = useState<CohortJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const data = await api.getCohortJob(jobId);
        if (!cancelled) {
          setJob(data);
          if (data.status === "done" || data.status === "failed") return;
          setTimeout(poll, 2500);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      }
    };
    void poll();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  if (error)
    return (
      <div className="p-8">
        <PageHeader eyebrow="cohort" title="Cohort report" />
        <Panel className="p-6 text-danger">{error}</Panel>
      </div>
    );

  if (!job)
    return (
      <div className="p-8">
        <PageHeader eyebrow="cohort" title="Cohort report" />
        <Panel className="p-6 flex items-center gap-2 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Loading…
        </Panel>
      </div>
    );

  const isRunning = job.status === "queued" || job.status === "running";
  const configName = job.config.split("/").pop()?.replace(".yaml", "") ?? job.config;

  return (
    <div>
      <PageHeader
        eyebrow="cohort"
        title="Cohort rehearsal report"
        description={job.hypothesis || `${job.nSeeds} seeds · ${configName}`}
      />
      <div className="p-8 max-w-[860px] space-y-6">
        {/* Status */}
        <Panel className="p-5 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Layers className="size-4 text-primary" />
              <span className="font-mono text-sm font-semibold">{jobId}</span>
              <Chip
                tone={job.status === "done" ? "ready" : job.status === "failed" ? "danger" : "info"}
              >
                {job.status}
              </Chip>
              <Chip tone="neutral">{job.nSeeds} seeds</Chip>
              <Chip tone="neutral">{configName}</Chip>
            </div>
            {isRunning && <Loader2 className="size-4 animate-spin text-primary" />}
            {job.status === "done" && <CheckCircle2 className="size-4 text-ready" />}
            {job.status === "failed" && <XCircle className="size-4 text-danger" />}
          </div>
          {isRunning && <SeedProgress completed={job.completedSeeds} total={job.nSeeds} />}
          <p className="text-xs text-muted-foreground font-mono">{job.phase}</p>
          {job.error && (
            <div className="text-xs text-danger font-mono bg-danger/5 border border-danger/20 rounded-md p-3">
              {job.error}
            </div>
          )}
        </Panel>

        {/* Hypothesis */}
        {job.hypothesis && (
          <Panel className="p-5">
            <div className="text-xs text-muted-foreground mb-1">Hypothesis</div>
            <p className="text-sm">{job.hypothesis}</p>
          </Panel>
        )}

        {/* Confidence band */}
        {job.aggregate && <ConfidenceBand agg={job.aggregate} />}

        {/* Recurring issues */}
        {job.aggregate?.recurringIssues && job.aggregate.recurringIssues.length > 0 && (
          <Panel className="overflow-hidden">
            <div className="p-4 border-b border-border">
              <span className="font-display font-semibold text-sm">Recurring issues</span>
              <span className="text-xs text-muted-foreground ml-2">appear in ≥50% of seeds</span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2/40">
                  <th className="text-left px-4 py-2 text-xs text-muted-foreground font-medium">
                    Issue
                  </th>
                  <th className="text-center px-4 py-2 text-xs text-muted-foreground font-medium">
                    Seeds
                  </th>
                  <th className="text-center px-4 py-2 text-xs text-muted-foreground font-medium">
                    Rate
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {job.aggregate.recurringIssues.map((iss) => (
                  <tr key={iss.title} className="hover:bg-surface-2/30">
                    <td className="px-4 py-2.5">{iss.title}</td>
                    <td className="px-4 py-2.5 text-center font-mono">{iss.count}</td>
                    <td className="px-4 py-2.5 text-center font-mono text-muted-foreground">
                      {Math.round(iss.rate * 100)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        )}

        {/* Individual runs */}
        {job.runIds.length > 0 && (
          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground mb-2">Individual seed runs</div>
            <div className="flex flex-wrap gap-2">
              {job.runIds.map((rid) => (
                <Link
                  key={rid}
                  to="/runs/$runId"
                  params={{ runId: rid }}
                  className="text-xs font-mono px-2 py-1 rounded-md border border-border hover:bg-surface-2 text-primary"
                >
                  {rid}
                </Link>
              ))}
            </div>
          </Panel>
        )}

        {isRunning && (
          <Panel className="p-4 text-sm text-muted-foreground flex items-center gap-2">
            <Loader2 className="size-4 animate-spin" />
            Running seed {job.completedSeeds + 1} of {job.nSeeds}… polling every 2.5s.
          </Panel>
        )}
      </div>
    </div>
  );
}
