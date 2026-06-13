import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Chip, StatusDot } from "@/components/ui-bits";
import type { JobRecord } from "@/lib/api/hooks";
import { Loader2, Pause, Play, Square } from "lucide-react";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

function statusLabel(status: string, paused: boolean): string {
  if (paused) return "paused";
  if (status === "queued") return "queued";
  if (status === "running") return "running (live)";
  return status;
}

type GroupMeta = { label: string; targetUrl?: string };

export function RunHistoryLiveRows({
  jobs,
  group,
  workspaceSlug,
}: {
  jobs: JobRecord[];
  group: GroupMeta;
  workspaceSlug?: string;
}) {
  const [paused, setPaused] = useState<Set<string>>(new Set());
  if (!jobs.length) return null;

  const targetHost = (group.targetUrl ?? "").replace(/^https?:\/\//, "");

  async function sendSignal(runId: string, signal: "pause" | "resume" | "stop") {
    try {
      await api.controlRun(runId, signal);
      if (signal === "pause") {
        setPaused((prev) => new Set(prev).add(runId));
        toast.info("Pausing — will stop before next journey");
      } else if (signal === "resume") {
        setPaused((prev) => {
          const s = new Set(prev);
          s.delete(runId);
          return s;
        });
        toast.success("Run resumed");
      } else {
        toast.info("Stop signal sent — finishes current journey then stops");
      }
    } catch {
      toast.error("Failed to send signal");
    }
  }

  return (
    <>
      {jobs.map((j) => {
        const isPaused = j.runId ? paused.has(j.runId) : false;
        const canControl = j.status === "running" && !!j.runId;
        return (
          <tr key={j.id} className="border-b border-border bg-info/5 hover:bg-info/10">
            <td className="px-5 py-3">
              <div className="flex flex-col gap-1">
                {j.runId ? (
                  workspaceSlug ? (
                    <Link
                      to="/$workspaceSlug/runs/$runId"
                      params={{ workspaceSlug, runId: j.runId }}
                      className="font-mono text-xs text-primary hover:underline"
                    >
                      {j.runId}
                    </Link>
                  ) : (
                    <Link
                      to="/runs/$runId"
                      params={{ runId: j.runId }}
                      className="font-mono text-xs text-primary hover:underline"
                    >
                      {j.runId}
                    </Link>
                  )
                ) : (
                  <span className="font-mono text-xs text-muted-foreground">pending…</span>
                )}
                {workspaceSlug ? (
                  <Link
                    to="/$workspaceSlug/runner"
                    params={{ workspaceSlug }}
                    className="font-mono text-[11px] text-info hover:underline"
                  >
                    job {j.id}
                  </Link>
                ) : (
                  <Link to="/runner" className="font-mono text-[11px] text-info hover:underline">
                    job {j.id}
                  </Link>
                )}
              </div>
            </td>
            <td className="px-5 py-3 text-xs">{group.label}</td>
            <td className="px-5 py-3 font-mono text-xs">{targetHost}</td>
            <td className="px-5 py-3">
              <Chip tone="info">staging</Chip>
            </td>
            <td className="px-5 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="size-3.5 animate-spin text-info" />
                <StatusDot status="neutral" />
                <Chip tone={j.status === "queued" ? "warn" : "info"}>
                  {statusLabel(j.status, isPaused)}
                </Chip>
              </div>
            </td>
            <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">—</td>
            <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">—</td>
            <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">—</td>
            <td className="px-5 py-3 font-mono text-muted-foreground">…</td>
            <td className="px-5 py-3 font-mono text-muted-foreground">—</td>
            <td className="px-5 py-3 text-right text-muted-foreground text-xs">
              <div className="flex flex-col items-end gap-1.5">
                <span>{j.startedAt ? new Date(j.startedAt).toLocaleString() : "—"}</span>
                {canControl && (
                  <div className="flex items-center gap-1">
                    {isPaused ? (
                      <button
                        onClick={() => sendSignal(j.runId!, "resume")}
                        className="flex items-center gap-1 px-1.5 py-0.5 text-[11px] rounded border border-border/60 hover:bg-surface text-muted-foreground hover:text-foreground"
                        title="Resume run"
                      >
                        <Play className="size-2.5" /> Resume
                      </button>
                    ) : (
                      <button
                        onClick={() => sendSignal(j.runId!, "pause")}
                        className="flex items-center gap-1 px-1.5 py-0.5 text-[11px] rounded border border-border/60 hover:bg-surface text-muted-foreground hover:text-foreground"
                        title="Pause before next journey"
                      >
                        <Pause className="size-2.5" /> Pause
                      </button>
                    )}
                    <button
                      onClick={() => sendSignal(j.runId!, "stop")}
                      className="flex items-center gap-1 px-1.5 py-0.5 text-[11px] rounded border border-danger/40 hover:bg-danger/10 text-danger/70 hover:text-danger"
                      title="Stop after current journey"
                    >
                      <Square className="size-2.5" /> Stop
                    </button>
                  </div>
                )}
              </div>
            </td>
          </tr>
        );
      })}
    </>
  );
}
