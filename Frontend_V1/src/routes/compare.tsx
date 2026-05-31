import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { DiffPanel } from "@/components/run-detail";
import { useLatestRun, useRunSummaries } from "@/lib/api/hooks";
import { z } from "zod";

const searchSchema = z.object({
  a: z.string().optional(),
  b: z.string().optional(),
});

export const Route = createFileRoute("/compare")({
  validateSearch: searchSchema,
  head: () => ({ meta: [{ title: "Compare runs — Launch Rehearsal" }] }),
  component: ComparePage,
});

function ComparePage() {
  const { a, b } = Route.useSearch();
  const latest = useLatestRun();
  const { data: runSummaries = [] } = useRunSummaries();
  const runA = a ?? runSummaries[1]?.id ?? latest?.id ?? "";
  const runB = b ?? latest?.id ?? "";

  return (
    <div>
      <PageHeader
        eyebrow="monitor"
        title="Run diff"
        description="Side-by-side comparison — readiness, sitemap, step outcomes. Mirrors rehearse diff CLI and GET /api/diff."
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-5 flex flex-wrap items-center gap-4">
          <div>
            <div className="text-xs text-muted-foreground mb-1">Run A (baseline)</div>
            <select
              className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm font-mono"
              defaultValue={runA}
            >
              {runSummaries.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id}
                </option>
              ))}
            </select>
          </div>
          <div className="text-muted-foreground">→</div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Run B (current)</div>
            <select
              className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm font-mono"
              defaultValue={runB}
            >
              {runSummaries.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id}
                </option>
              ))}
            </select>
          </div>
          <Chip tone="info">
            CLI: rehearse diff {runA} {runB}
          </Chip>
        </Panel>

        <Panel className="overflow-hidden">
          <DiffPanel runA={runA} runB={runB} />
        </Panel>

        <div className="text-sm text-muted-foreground">
          Open individual runs:{" "}
          <Link
            to="/runs/$runId"
            params={{ runId: runA }}
            className="text-primary hover:underline font-mono"
          >
            {runA}
          </Link>
          {" · "}
          <Link
            to="/runs/$runId"
            params={{ runId: runB }}
            className="text-primary hover:underline font-mono"
          >
            {runB}
          </Link>
        </div>
      </div>
    </div>
  );
}
