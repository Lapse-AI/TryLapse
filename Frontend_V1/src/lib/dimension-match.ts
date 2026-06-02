import type { Issue } from "@/lib/mock-data";

/** Match primary dimension tag or cross-cutting relatedDimensions from bundle export. */
export function issueMatchesDimension(issue: Issue, dimension: string): boolean {
  if (issue.dimension === dimension) return true;
  return (issue.relatedDimensions ?? []).includes(dimension);
}

export function countIssuesForDimension(issues: Issue[], dimension: string): number {
  return issues.filter((i) => issueMatchesDimension(i, dimension)).length;
}
