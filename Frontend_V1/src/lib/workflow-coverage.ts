import type { Journey, RunBundle, SuggestedJourney, WorkflowCoverage } from "@/lib/mock-data/types";

type WorkflowCategory = Journey["category"];

const CATEGORY_ALIASES: Record<string, WorkflowCategory> = {
  auth: "auth",
  authentication: "auth",
  pricing: "pricing",
  admin: "admin",
  search: "search",
  docs: "docs",
  documentation: "docs",
  dashboard: "dashboard",
};

function normalizeCategory(raw: string | undefined): WorkflowCategory | null {
  if (!raw) return null;
  return CATEGORY_ALIASES[raw.toLowerCase()] ?? null;
}

function inferCategoryFromSuggested(raw: Record<string, unknown>): WorkflowCategory {
  const id = String(raw.id ?? "");
  const name = String(raw.name ?? raw.title ?? "");
  for (const [key, cat] of Object.entries(CATEGORY_ALIASES)) {
    if (id.includes(key) || name.toLowerCase().includes(key)) return cat;
  }
  return "dashboard";
}

function pathFromSuggested(raw: Record<string, unknown>): string | undefined {
  const steps = raw.steps;
  if (!Array.isArray(steps) || steps.length === 0) return undefined;
  const first = steps[0] as Record<string, unknown>;
  const url = String(first.url ?? "");
  if (!url) return undefined;
  try {
    return new URL(url).pathname;
  } catch {
    return url.startsWith("/") ? url : undefined;
  }
}

/** Normalize backend suggested-journey shapes into UI SuggestedJourney rows. */
export function normalizeSuggestedJourneys(bundle: RunBundle): SuggestedJourney[] {
  const raw = (bundle.suggestedJourneys ?? []) as Array<
    SuggestedJourney & { name?: string; steps?: unknown[] }
  >;
  return raw.map((s, i) => {
    const category =
      normalizeCategory(String(s.category ?? "")) ??
      inferCategoryFromSuggested(s as Record<string, unknown>);
    const stepCount = Array.isArray(s.steps) ? s.steps.length : undefined;
    const reason =
      s.reason ??
      (stepCount
        ? `Auto-detected ${stepCount}-step journey not yet in rehearse.yaml`
        : "Detected from crawl — not yet in rehearse.yaml");
    return {
      id: s.id ?? `sj_${i}`,
      title: s.title ?? s.name ?? "Suggested journey",
      category,
      reason,
      sourceRunId: s.sourceRunId ?? bundle.summary.id,
      path: s.path ?? pathFromSuggested(s as Record<string, unknown>),
    };
  });
}

/** Build workflow coverage cards from a live run bundle (not mock store). */
export function buildWorkflowCoverage(bundle: RunBundle): WorkflowCoverage[] {
  const workflows = bundle.workflows ?? [];
  if (workflows.length === 0) return [];

  const journeys = bundle.journeys ?? [];
  const suggested = normalizeSuggestedJourneys(bundle);
  const byCategory = new Map<WorkflowCategory, { paths: Set<string>; workflowCount: number }>();

  for (const w of workflows) {
    const category = normalizeCategory(w.category) ?? "dashboard";
    const entry = byCategory.get(category) ?? { paths: new Set<string>(), workflowCount: 0 };
    entry.workflowCount += 1;
    if (w.path) entry.paths.add(w.path);
    byCategory.set(category, entry);
  }

  return [...byCategory.entries()]
    .map(([category, { paths, workflowCount }]) => {
      const journeysInCategory = journeys.filter((j) => j.category === category).length;
      const suggestedInCategory = suggested.filter((s) => s.category === category).length;
      const coverage = Math.min(
        100,
        Math.round((journeysInCategory / Math.max(1, workflowCount)) * 100),
      );
      return {
        category,
        coverage,
        journeys: journeysInCategory,
        suggested: suggestedInCategory,
        paths: [...paths].slice(0, 6),
      };
    })
    .sort((a, b) => a.category.localeCompare(b.category));
}
