import { Link } from "@tanstack/react-router";
import { Panel, Chip } from "@/components/ui-bits";
import type { JobRecord } from "@/lib/api/hooks";
import { Loader2, AlertCircle, CheckCircle2, Clock } from "lucide-react";

function statusTone(status: string): "ready" | "warn" | "danger" | "info" {
  if (status === "done") return "ready";
  if (status === "failed") return "danger";
  if (status === "queued") return "warn";
  return "info";
}

function StatusIcon({ status }: { status: string }) {
  if (status === "running") return <Loader2 className="size-4 animate-spin text-info" />;
  if (status === "failed") return <AlertCircle className="size-4 text-danger" />;
  if (status === "done") return <CheckCircle2 className="size-4 text-ready" />;
  return <Clock className="size-4 text-warn" />;
}

export function ActiveJobsBanner({ jobs }: { jobs: JobRecord[] }) {
  const active = jobs.filter((j) => j.status === "queued" || j.status === "running");
  if (!active.length) return null;

  return (
    <Panel className="p-4 border border-info/40 bg-info/5 space-y-3">
      <div className="text-sm font-medium">Rehearsal in progress</div>
      {active.map((j) => (
        <div
          key={j.id}
          className="flex flex-wrap items-center gap-3 text-sm border border-border/60 rounded-md px-3 py-2 bg-surface/80"
        >
          <StatusIcon status={j.status} />
          <Chip tone={statusTone(j.status)}>{j.status}</Chip>
          <span className="font-mono text-xs text-muted-foreground">{j.id}</span>
          <span className="text-xs text-muted-foreground">{j.mode}</span>
          {j.runId ? (
            <Link
              to="/runs/$runId"
              params={{ runId: j.runId }}
              className="text-xs text-primary hover:underline font-mono"
            >
              {j.runId}
            </Link>
          ) : (
            <span className="text-xs text-muted-foreground">run id pending…</span>
          )}
        </div>
      ))}
      <p className="text-[11px] text-muted-foreground">
        Status updates every ~1.5s. Live jobs also appear at the top of{" "}
        <Link to="/runs" className="text-primary hover:underline">
          Run history
        </Link>{" "}
        before the run id exists.
      </p>
    </Panel>
  );
}

export function JobQueueTable({ jobs }: { jobs: JobRecord[] }) {
  if (!jobs.length) {
    return (
      <div className="p-8 text-sm text-muted-foreground text-center">
        No jobs yet — trigger a run above.
      </div>
    );
  }

  return (
    <table className="w-full text-sm">
      <thead className="text-xs text-muted-foreground border-b border-border">
        <tr>
          <th className="text-left px-5 py-2">Job</th>
          <th className="text-left px-5 py-2">Mode</th>
          <th className="text-left px-5 py-2">Status</th>
          <th className="text-left px-5 py-2">Run ID</th>
          <th className="text-left px-5 py-2">Detail</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((j) => (
          <tr key={j.id} className="border-b border-border last:border-0">
            <td className="px-5 py-3 font-mono text-xs">{j.id}</td>
            <td className="px-5 py-3">{j.mode}</td>
            <td className="px-5 py-3">
              <div className="flex items-center gap-2">
                {(j.status === "queued" || j.status === "running") && (
                  <Loader2 className="size-3.5 animate-spin shrink-0" />
                )}
                <Chip tone={statusTone(j.status)}>{j.status}</Chip>
              </div>
            </td>
            <td className="px-5 py-3 font-mono text-xs">
              {j.runId ? (
                <Link
                  to="/runs/$runId"
                  params={{ runId: j.runId }}
                  className="text-primary hover:underline"
                >
                  {j.runId}
                </Link>
              ) : (
                "—"
              )}
            </td>
            <td className="px-5 py-3 text-xs text-muted-foreground max-w-[280px] truncate">
              {j.status === "failed" && j.error ? j.error : j.startedAt ? j.startedAt.slice(0, 19) : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
