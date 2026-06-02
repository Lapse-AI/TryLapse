import { Link } from "@tanstack/react-router";
import { Bar } from "@/components/ui-bits";
import type { DimensionScore, Issue } from "@/lib/mock-data";
import { countIssuesForDimension } from "@/lib/dimension-match";

function dimensionTone(score: number): "ready" | "warn" | "danger" {
  if (score >= 85) return "ready";
  if (score >= 75) return "warn";
  return "danger";
}

type DimensionCardProps = {
  dimension: DimensionScore;
  relatedCount: number;
  active?: boolean;
  runId: string;
  mode: "navigate" | "filter";
  onSelect?: (name: string) => void;
};

function DimensionCard({
  dimension: d,
  relatedCount,
  active,
  runId,
  mode,
  onSelect,
}: DimensionCardProps) {
  const tone = dimensionTone(d.score);
  const hint =
    relatedCount > 0
      ? `${relatedCount} related finding${relatedCount === 1 ? "" : "s"}`
      : d.automated
        ? "Automated rubric"
        : "Phase 2 heuristic";

  const inner = (
    <>
      <div className="flex items-center justify-between mb-1.5 gap-2">
        <span className="text-sm font-medium group-hover:text-primary transition-colors">
          {d.name}
          {!d.automated && (
            <span className="text-[10px] text-muted-foreground font-normal ml-1">P2</span>
          )}
        </span>
        <span
          className="font-mono text-sm tabular-nums shrink-0"
          style={{ color: `var(--${tone})` }}
        >
          {d.score}
        </span>
      </div>
      <Bar value={d.score} tone={tone} />
      {d.signal && (
        <p className="text-[10px] text-muted-foreground mt-2 line-clamp-2" title={d.signal}>
          {d.signal}
        </p>
      )}
      <div className="text-[10px] text-primary mt-2 flex items-center justify-between gap-2">
        <span className="text-muted-foreground truncate">{hint}</span>
        <span className="shrink-0 font-medium group-hover:underline">
          {active ? "Showing · click to clear" : "View breakdown →"}
        </span>
      </div>
    </>
  );

  const className = `group block w-full text-left rounded-lg border p-3 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${
    active
      ? "border-primary/50 bg-primary/5"
      : "border-border bg-surface-2/20 hover:border-primary/30 hover:bg-surface-2/60"
  }`;

  if (mode === "navigate") {
    return (
      <Link
        to="/runs/$runId"
        params={{ runId }}
        search={{ dimension: d.name }}
        hash="dimension-breakdown"
        className={className}
        aria-label={`${d.name} score ${d.score}. View breakdown.`}
      >
        {inner}
      </Link>
    );
  }

  return (
    <button
      type="button"
      className={className}
      aria-pressed={active}
      aria-label={`${d.name} score ${d.score}. ${active ? "Clear filter" : "Filter findings by this dimension"}.`}
      onClick={() => onSelect?.(d.name)}
    >
      {inner}
    </button>
  );
}

export function DimensionRollupGrid({
  dimensions,
  issues,
  runId,
  activeDimension,
  mode,
  onSelect,
}: {
  dimensions: DimensionScore[];
  issues: Issue[];
  runId: string;
  activeDimension?: string;
  mode: "navigate" | "filter";
  onSelect?: (name: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
      {dimensions.map((d) => (
        <DimensionCard
          key={d.name}
          dimension={d}
          relatedCount={countIssuesForDimension(issues, d.name)}
          active={activeDimension === d.name}
          runId={runId}
          mode={mode}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

export function DimensionBreakdownBanner({
  dimension,
  relatedCount,
  onClear,
}: {
  dimension: DimensionScore;
  relatedCount: number;
  onClear: () => void;
}) {
  const tone = dimensionTone(dimension.score);
  return (
    <div
      id="dimension-breakdown"
      className="rounded-lg border border-primary/30 bg-primary/5 p-4 mb-4 scroll-mt-24"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs text-muted-foreground">Dimension breakdown</div>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <h3 className="font-display text-lg font-semibold">{dimension.name}</h3>
            <span className="font-mono text-lg tabular-nums" style={{ color: `var(--${tone})` }}>
              {dimension.score}
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded border border-border text-muted-foreground">
              {dimension.automated ? "Automated rubric" : "Phase 2 heuristic"}
            </span>
          </div>
          {dimension.signal && (
            <p className="text-sm text-muted-foreground mt-2 max-w-3xl">{dimension.signal}</p>
          )}
          <p className="text-[11px] text-muted-foreground mt-2">
            {relatedCount > 0
              ? `${relatedCount} finding${relatedCount === 1 ? "" : "s"} tagged to this dimension below.`
              : "No findings tagged to this dimension yet — score comes from automated step/sitemap heuristics."}
          </p>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="text-xs px-2.5 py-1 rounded-md border border-border hover:bg-surface-2 shrink-0"
        >
          Clear filter
        </button>
      </div>
    </div>
  );
}
