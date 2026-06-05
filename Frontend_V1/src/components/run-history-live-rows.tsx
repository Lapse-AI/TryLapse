import { Link } from "@tanstack/react-router";
import { Chip, StatusDot } from "@/components/ui-bits";
import type { JobRecord } from "@/lib/api/hooks";
import type { TestGroup } from "@/lib/test-groups";
import { Loader2 } from "lucide-react";

function statusLabel(status: string): string {
  if (status === "queued") return "queued";
  if (status === "running") return "running (live)";
  return status;
}

export function RunHistoryLiveRows({ jobs, group }: { jobs: JobRecord[]; group: TestGroup }) {
  if (!jobs.length) return null;

  const targetHost = group.targetUrl.replace(/^https?:\/\//, "");

  return (
    <>
      {jobs.map((j) => (
        <tr key={j.id} className="border-b border-border bg-info/5 hover:bg-info/10">
          <td className="px-5 py-3">
            <div className="flex flex-col gap-1">
              {j.runId ? (
                <Link
                  to="/runs/$runId"
                  params={{ runId: j.runId }}
                  className="font-mono text-xs text-primary hover:underline"
                >
                  {j.runId}
                </Link>
              ) : (
                <span className="font-mono text-xs text-muted-foreground">pending…</span>
              )}
              <Link to="/runner" className="font-mono text-[11px] text-info hover:underline">
                job {j.id}
              </Link>
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
              <StatusDot status="info" />
              <Chip tone={j.status === "queued" ? "warn" : "info"}>{statusLabel(j.status)}</Chip>
            </div>
          </td>
          <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">—</td>
          <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">—</td>
          <td className="px-5 py-3 font-mono tabular-nums text-muted-foreground">—</td>
          <td className="px-5 py-3 font-mono text-muted-foreground">…</td>
          <td className="px-5 py-3 font-mono text-muted-foreground">—</td>
          <td className="px-5 py-3 text-right text-muted-foreground text-xs">
            {j.startedAt ? new Date(j.startedAt).toLocaleString() : "—"}
          </td>
        </tr>
      ))}
    </>
  );
}
