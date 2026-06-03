import { useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { api } from "@/lib/api/client";
import { GitCompare, CheckCircle2, XCircle, Loader2, FlaskConical, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/experiment/$jobId")({
  head: () => ({ meta: [{ title: "Variant experiment — Launch Rehearsal" }] }),
  component: ExperimentReport,
});

type VariantJob = Awaited<ReturnType<typeof api.getVariantJob>>;

const PHASE_LABELS: Record<string, string> = {
  queued: "Queued",
  "running-A": "Running config A (control)…",
  "running-B": "Running config B (variant)…",
  comparing: "Generating comparison report…",
  done: "Done",
  failed: "Failed",
};

function PhaseBar({ phase }: { phase: string }) {
  const phases = ["running-A", "running-B", "comparing", "done"];
  const idx = phases.indexOf(phase);
  return (
    <div className="flex items-center gap-1 text-xs">
      {phases.map((p, i) => (
        <div key={p} className="flex items-center gap-1">
          <div
            className={[
              "px-2 py-0.5 rounded-full",
              i < idx
                ? "bg-ready/20 text-ready"
                : i === idx
                  ? "bg-primary/20 text-primary font-medium"
                  : "bg-surface-2 text-muted-foreground",
            ].join(" ")}
          >
            {p === "running-A"
              ? "A"
              : p === "running-B"
                ? "B"
                : p === "comparing"
                  ? "compare"
                  : "done"}
          </div>
          {i < phases.length - 1 && <ArrowRight className="size-3 text-muted-foreground" />}
        </div>
      ))}
    </div>
  );
}

function ReadinessBadge({ runId }: { runId: string | null }) {
  const [readiness, setReadiness] = useState<string | null>(null);
  useEffect(() => {
    if (!runId) return;
    api
      .summaries()
      .then((list) => {
        const r = list.find((s) => s.run_id === runId);
        if (r) setReadiness((r as { run_id: string; readiness?: string }).readiness ?? null);
      })
      .catch(() => {});
  }, [runId]);
  if (!runId) return <Chip tone="neutral">—</Chip>;
  if (!readiness) return <Chip tone="neutral">loading…</Chip>;
  return (
    <Chip tone={readiness === "green" ? "ready" : readiness === "red" ? "danger" : "warn"}>
      {readiness}
    </Chip>
  );
}

export default function ExperimentReport() {
  const { jobId } = Route.useParams();
  const [job, setJob] = useState<VariantJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const data = await api.getVariantJob(jobId);
        if (!cancelled) {
          setJob(data);
          if (data.status === "done" || data.status === "failed") return;
          setTimeout(poll, 2000);
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

  if (error) {
    return (
      <div className="p-8">
        <PageHeader eyebrow="experiment" title="Variant report" />
        <Panel className="p-6 text-danger">{error}</Panel>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="p-8">
        <PageHeader eyebrow="experiment" title="Variant report" />
        <Panel className="p-6 flex items-center gap-2 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Loading…
        </Panel>
      </div>
    );
  }

  const isRunning = job.status === "queued" || job.status === "running";
  const configAName = job.configA.split("/").pop()?.replace(".yaml", "") ?? job.configA;
  const configBName = job.configB.split("/").pop()?.replace(".yaml", "") ?? job.configB;
  const narrative = (job.diffNarrative ??
    (job.diff as Record<string, unknown> | undefined)?.narrative) as
    | Record<string, string>
    | null
    | undefined;

  return (
    <div>
      <PageHeader
        eyebrow="experiment"
        title="Variant experiment report"
        description={job.hypothesis || "Side-by-side rehearsal — control vs variant"}
      />
      <div className="p-8 max-w-[900px] space-y-6">
        {/* Status + phase */}
        <Panel className="p-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <FlaskConical className="size-4 text-primary" />
              <span className="font-display font-semibold text-sm">{jobId}</span>
              <Chip
                tone={job.status === "done" ? "ready" : job.status === "failed" ? "danger" : "info"}
              >
                {job.status}
              </Chip>
            </div>
            {isRunning && <Loader2 className="size-4 animate-spin text-primary" />}
            {job.status === "done" && <CheckCircle2 className="size-4 text-ready" />}
            {job.status === "failed" && <XCircle className="size-4 text-danger" />}
          </div>
          <PhaseBar phase={job.phase} />
          {job.error && (
            <div className="text-xs text-danger font-mono bg-danger/5 border border-danger/20 rounded-md p-3">
              {job.error}
            </div>
          )}
        </Panel>

        {/* Hypothesis */}
        {(job.hypothesis || job.userGoal) && (
          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground">Experiment spec</div>
            {job.hypothesis && (
              <div>
                <span className="text-xs font-medium text-muted-foreground">Hypothesis: </span>
                <span className="text-sm">{job.hypothesis}</span>
              </div>
            )}
            {job.userGoal && (
              <div>
                <span className="text-xs font-medium text-muted-foreground">User goal: </span>
                <span className="text-sm">{job.userGoal}</span>
              </div>
            )}
          </Panel>
        )}

        {/* A vs B readiness */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground">Config A · control</div>
            <div className="font-display font-semibold text-sm font-mono">{configAName}</div>
            {job.runIdA ? (
              <div className="flex items-center gap-2">
                <ReadinessBadge runId={job.runIdA} />
                <Link
                  to="/runs/$runId"
                  params={{ runId: job.runIdA }}
                  className="text-xs text-primary hover:underline"
                >
                  {job.runIdA}
                </Link>
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                {isRunning && job.phase === "running-A" ? "Running…" : "Pending"}
              </div>
            )}
          </Panel>

          <Panel className="p-5 space-y-2">
            <div className="text-xs text-muted-foreground">Config B · variant</div>
            <div className="font-display font-semibold text-sm font-mono">{configBName}</div>
            {job.runIdB ? (
              <div className="flex items-center gap-2">
                <ReadinessBadge runId={job.runIdB} />
                <Link
                  to="/runs/$runId"
                  params={{ runId: job.runIdB }}
                  className="text-xs text-primary hover:underline"
                >
                  {job.runIdB}
                </Link>
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                {isRunning && job.phase === "running-B" ? "Running…" : "Pending"}
              </div>
            )}
          </Panel>
        </div>

        {/* Narrative from diff */}
        {narrative && (
          <Panel className="p-5 space-y-4">
            <div className="flex items-center gap-2">
              <GitCompare className="size-4 text-primary" />
              <span className="font-display font-semibold text-sm">What changed</span>
              {(narrative as Record<string, string>).source && (
                <Chip tone="info">{(narrative as Record<string, string>).source}</Chip>
              )}
            </div>
            {(narrative as Record<string, string>).executiveSummary && (
              <p className="text-sm">{(narrative as Record<string, string>).executiveSummary}</p>
            )}
            {(narrative as Record<string, string>).founderSummary && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-muted-foreground">Founder view</div>
                <p className="text-sm text-muted-foreground">
                  {(narrative as Record<string, string>).founderSummary}
                </p>
              </div>
            )}
            {(narrative as Record<string, string>).engineeringSummary && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-muted-foreground">Engineering view</div>
                <p className="text-sm text-muted-foreground">
                  {(narrative as Record<string, string>).engineeringSummary}
                </p>
              </div>
            )}
          </Panel>
        )}

        {/* Full compare link */}
        {job.runIdA && job.runIdB && (
          <div className="flex">
            <Link
              to="/compare"
              search={{ a: job.runIdA, b: job.runIdB }}
              className="flex items-center gap-2 text-sm px-4 py-2 rounded-md border border-primary/40 text-primary hover:bg-primary/5"
            >
              <GitCompare className="size-4" />
              Open full compare — A vs B
            </Link>
          </div>
        )}

        {isRunning && (
          <Panel className="p-4 text-sm text-muted-foreground flex items-center gap-2">
            <Loader2 className="size-4 animate-spin" />
            {PHASE_LABELS[job.phase] ?? "Running…"} Polling every 2 seconds.
          </Panel>
        )}
      </div>
    </div>
  );
}
