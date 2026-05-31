/** Download fix-before-launch backlog as Linear-friendly markdown. */

import type { BacklogItem, Issue } from "@/lib/mock-data/types";

function downloadText(content: string, filename: string, mime = "text/markdown;charset=utf-8") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function formatLinearMarkdown(
  items: BacklogItem[],
  issuesById: Map<string, Issue>,
  runId?: string,
): string {
  const fixItems = items.filter((b) => b.fixBeforeLaunch);
  const lines = [
    "# Launch Rehearsal — fix before launch",
    "",
    `Exported: ${new Date().toISOString()}`,
  ];
  if (runId) {
    lines.push(`Source run: \`${runId}\``);
  }
  lines.push("", "---", "");

  for (const item of fixItems) {
    const issue = issuesById.get(item.id);
    lines.push(`## ${item.title}`);
    lines.push("");
    lines.push(`- **Severity:** ${item.severity}`);
    lines.push(`- **Owner:** ${item.owner}`);
    lines.push(`- **Fix before launch:** yes`);
    if (issue?.evidence) {
      lines.push(`- **Evidence:** ${issue.evidence}`);
    }
    if (issue?.stepId) {
      lines.push(`- **Step:** \`${issue.stepId}\``);
    }
    if (issue?.dimension) {
      lines.push(`- **Dimension:** ${issue.dimension}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}

function formatLinearJson(items: BacklogItem[], issuesById: Map<string, Issue>, runId?: string) {
  return items
    .filter((b) => b.fixBeforeLaunch)
    .map((item) => {
      const issue = issuesById.get(item.id);
      return {
        title: item.title,
        severity: item.severity,
        owner: item.owner,
        fixBeforeLaunch: true,
        evidence: issue?.evidence ?? null,
        stepId: issue?.stepId ?? null,
        dimension: issue?.dimension ?? null,
        runId: runId ?? issue?.runId ?? null,
      };
    });
}

export function exportBacklogToLinear(
  backlog: BacklogItem[],
  issues: Issue[] = [],
  options?: { runId?: string; format?: "md" | "json" },
) {
  const issuesById = new Map(issues.map((i) => [i.id, i]));
  const runId = options?.runId;
  const format = options?.format ?? "md";
  const stamp = new Date().toISOString().slice(0, 10);

  if (format === "json") {
    const payload = formatLinearJson(backlog, issuesById, runId);
    downloadText(
      JSON.stringify({ exportedAt: new Date().toISOString(), runId, items: payload }, null, 2),
      `launch-rehearsal-linear-${stamp}.json`,
      "application/json;charset=utf-8",
    );
    return;
  }

  downloadText(
    formatLinearMarkdown(backlog, issuesById, runId),
    `launch-rehearsal-linear-${stamp}.md`,
  );
}
