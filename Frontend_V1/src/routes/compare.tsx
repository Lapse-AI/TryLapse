import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { PageHeader, Panel, Chip } from "@/components/ui-bits";
import { DiffPanel } from "@/components/run-detail";
import { LiftCard } from "@/components/lift-card";
import { useScopedRunSummaries, useRunDiff } from "@/lib/api/hooks";
import { useTestGroup } from "@/hooks/use-test-group";
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
  const { group } = useTestGroup();
  const { data: runSummaries = [] } = useScopedRunSummaries();
  const latest = runSummaries[0];

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

  // Pull numeric readiness from summaries for the lift card
  const summaryA = runSummaries.find((r) => r.id === runA);
  const summaryB = runSummaries.find((r) => r.id === runB);
  const scoreA = (summaryA as Record<string, number> | undefined)?.readiness ?? 0;
  const scoreB = (summaryB as Record<string, number> | undefined)?.readiness ?? 0;
  const bandA = (summaryA as Record<string, string> | undefined)?.readinessBand;
  const bandB = (summaryB as Record<string, string> | undefined)?.readinessBand;

  const { data: diff } = useRunDiff(runA !== runB ? runA : "", runA !== runB ? runB : "");
  const newIssueCount = diff?.newIssues?.length ?? 0;
  const resolvedIssueCount = diff?.resolvedIssues?.length ?? 0;
  const delta = scoreB - scoreA;
  const verdict = delta > 2 ? "held" : delta < -2 ? "regressed" : "inconclusive";

  return (
    <div>
      <PageHeader
        eyebrow="monitor"
        title="Run diff"
        description={`Compare runs for ${group.label} — readiness, sitemap, step outcomes. Only runs matching this product are listed.`}
      />
      <div className="p-8 max-w-[1400px] space-y-6">
        <Panel className="p-5 flex flex-wrap items-center gap-4">
          <div>
            <label htmlFor="compare-run-a" className="text-xs text-muted-foreground mb-1 block">
              Run A (baseline)
            </label>
            <select
              id="compare-run-a"
              aria-label="Run A baseline"
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
            aria-label="Swap run A and run B"
            className="text-xs px-2 py-1 rounded-md border border-border hover:bg-surface-2 text-muted-foreground"
            title="Swap A and B"
          >
            ⇄
          </button>
          <div>
            <label htmlFor="compare-run-b" className="text-xs text-muted-foreground mb-1 block">
              Run B (current)
            </label>
            <select
              id="compare-run-b"
              aria-label="Run B current"
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

        {runA && runB && runA !== runB && (summaryA ?? summaryB) && (
          <LiftCard
            readinessA={scoreA}
            readinessB={scoreB}
            bandA={bandA}
            bandB={bandB}
            newIssues={newIssueCount}
            resolvedIssues={resolvedIssueCount}
            verdict={verdict}
            label="Readiness delta"
          />
        )}

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
