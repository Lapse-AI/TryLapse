import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
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
  const navigate = useNavigate({ from: Route.fullPath });
  const { a, b } = Route.useSearch();
  const latest = useLatestRun();
  const { data: runSummaries = [] } = useRunSummaries();

  const defaultA = runSummaries[1]?.id ?? runSummaries[0]?.id ?? latest?.id ?? "";
  const defaultB = latest?.id ?? runSummaries[0]?.id ?? "";
  const runA = a ?? defaultA;
  const runB = b ?? defaultB;

  const setRunA = (id: string) => {
    void navigate({ search: (prev) => ({ ...prev, a: id }) });
  };
  const setRunB = (id: string) => {
    void navigate({ search: (prev) => ({ ...prev, b: id }) });
  };

  const swapRuns = () => {
    void navigate({ search: { a: runB, b: runA } });
  };

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
              className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm font-mono min-w-[240px]"
              value={runA}
              onChange={(e) => setRunA(e.target.value)}
            >
              {runSummaries.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={swapRuns}
            className="text-xs px-2 py-1 rounded-md border border-border hover:bg-surface-2 text-muted-foreground"
            title="Swap A and B"
          >
            ⇄
          </button>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Run B (current)</div>
            <select
              className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm font-mono min-w-[240px]"
              value={runB}
              onChange={(e) => setRunB(e.target.value)}
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
          {runA && runB && runA !== runB ? (
            <DiffPanel key={`${runA}-${runB}`} runA={runA} runB={runB} />
          ) : (
            <div className="p-8 text-center text-sm text-muted-foreground">
              Pick two different runs to compare.
            </div>
          )}
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
