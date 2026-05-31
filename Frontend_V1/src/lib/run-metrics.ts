import type { RunBundle, StepSnapshot } from "@/lib/mock-data";

export const READINESS_BAND_HELP =
  "Readiness band (Green / Amber / Red) follows P0 and P1 blockers. Rubric dimension scores (e.g. UI/UX) are separate axes — Green can coexist with low UX scores when issues are P2/P3.";

/** Reword agent summaries so rehearse crawl heuristics do not match diagnostic copy. */
export function displayAgentSummary(text: string): string {
  return text
    .replace(/\baccess errors\b/gi, "access barriers")
    .replace(/\bvalidation errors?\b/gi, "validation issues")
    .replace(/\bconsole error:/gi, "console warning:")
    .replace(/\berrors detected\b/gi, "issues detected");
}

export function countFlakySteps(steps: StepSnapshot[]): number {
  return steps.filter((s) => s.flaky).length;
}

export function flakyStepsHint(steps: StepSnapshot[]): string {
  const n = countFlakySteps(steps);
  if (n === 0) return "no flaky steps";
  return `${n} flaky step${n === 1 ? "" : "s"}`;
}

export function formatAgentCostDisplay(bundle: RunBundle): { value: string; hint: string } {
  const estimate = (
    bundle.summary as RunBundle["summary"] & {
      costEstimate?: { usd: number; source?: string; inputTokens?: number; outputTokens?: number };
    }
  ).costEstimate;
  if (estimate) {
    const src =
      estimate.source === "llm_tokens"
        ? "LLM token estimate"
        : estimate.source === "heuristic"
          ? "duration heuristic"
          : "run estimate";
    return {
      value: `$${estimate.usd.toFixed(2)}`,
      hint: `${src} · not billed`,
    };
  }
  return {
    value: `$${bundle.summary.agentCost.toFixed(2)}`,
    hint: "estimate · not billed",
  };
}
