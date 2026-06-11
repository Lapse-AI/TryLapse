import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Panel, Chip } from "@/components/ui-bits";
import type { JobRecord } from "@/lib/api/hooks";
import { Loader2, AlertCircle, CheckCircle2, Clock, Pause, Play, Square } from "lucide-react";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

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

export function ActiveJobsBanner({ jobs, workspaceSlug }: { jobs: JobRecord[]; workspaceSlug?: string }) {
  const active = jobs.filter((j) => j.status === "queued" || j.status === "running");
  const [paused, setPaused] = useState<Set<string>>(new Set());
  if (!active.length) return null;

  async function sendSignal(runId: string, signal: "pause" | "resume" | "stop") {
    try {
      await api.controlRun(runId, signal);
      if (signal === "pause") {
        setPaused((prev) => new Set(prev).add(runId));
        toast.info("Run pausing — will stop before next journey");
      } else if (signal === "resume") {
        setPaused((prev) => { const s = new Set(prev); s.delete(runId); return s; });
        toast.success("Run resumed");
      } else {
        toast.info("Stop signal sent — run will finish current journey then stop");
      }
    } catch {
      toast.error("Failed to send signal");
    }
  }

  return (
    <Panel className="p-4 border border-info/40 bg-info/5 space-y-3">
      <div className="text-sm font-medium">Rehearsal in progress</div>
      {active.map((j) => {
        const isPaused = j.runId ? paused.has(j.runId) : false;
        return (
          <div
            key={j.id}
            className="flex flex-wrap items-center gap-3 text-sm border border-border/60 rounded-md px-3 py-2 bg-surface/80"
          >
            <StatusIcon status={j.status} />
            <Chip tone={statusTone(j.status)}>{isPaused ? "paused" : j.status}</Chip>
            <span className="font-mono text-xs text-muted-foreground">{j.id}</span>
            <span className="text-xs text-muted-foreground">{j.mode}</span>
            {j.runId ? (
              <a
                href={workspaceSlug ? `/${workspaceSlug}/runs/${j.runId}` : `/runs/${j.runId}`}
                className="text-xs text-primary hover:underline font-mono"
              >
                {j.runId}
              </a>
            ) : (
              <span className="text-xs text-muted-foreground">run id pending…</span>
            )}
            {j.status === "running" && j.runId && (
              <div className="ml-auto flex items-center gap-1">
                {isPaused ? (
                  <button
                    onClick={() => sendSignal(j.runId!, "resume")}
                    className="flex items-center gap-1 px-2 py-0.5 text-xs rounded border border-border/60 hover:bg-surface text-muted-foreground hover:text-foreground"
                    title="Resume run"
                  >
                    <Play className="size-3" /> Resume
                  </button>
                ) : (
                  <button
                    onClick={() => sendSignal(j.runId!, "pause")}
                    className="flex items-center gap-1 px-2 py-0.5 text-xs rounded border border-border/60 hover:bg-surface text-muted-foreground hover:text-foreground"
                    title="Pause before next journey"
                  >
                    <Pause className="size-3" /> Pause
                  </button>
                )}
                <button
                  onClick={() => sendSignal(j.runId!, "stop")}
                  className="flex items-center gap-1 px-2 py-0.5 text-xs rounded border border-danger/40 hover:bg-danger/10 text-danger/80 hover:text-danger"
                  title="Stop after current journey"
                >
                  <Square className="size-3" /> Stop
                </button>
              </div>
            )}
          </div>
        );
      })}
      <p className="text-[11px] text-muted-foreground">
        Status updates every ~1.5s. Live jobs also appear at the top of{" "}
        <a href={workspaceSlug ? `/${workspaceSlug}/runs` : "/runs"} className="text-primary hover:underline">
          Run history
        </a>{" "}
        before the run id exists.
      </p>
    </Panel>
  );
}

export function JobQueueTable({ jobs, workspaceSlug }: { jobs: JobRecord[]; workspaceSlug?: string }) {
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
                <a
                  href={workspaceSlug ? `/${workspaceSlug}/runs/${j.runId}` : `/runs/${j.runId}`}
                  className="text-primary hover:underline"
                >
                  {j.runId}
                </a>
              ) : (
                "—"
              )}
            </td>
            <td className="px-5 py-3 text-xs text-muted-foreground max-w-[280px] truncate">
              {j.status === "failed" && j.error
                ? j.error
                : j.startedAt
                  ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true }).format(new Date(j.startedAt))
                  : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
