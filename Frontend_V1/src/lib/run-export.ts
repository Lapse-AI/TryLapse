/** Client-side export helpers — downloads via /files/ (rehearse serve). */

import { artifactUrl } from "@/lib/api/client";
import type { Issue, RunBundle } from "@/lib/mock-data/types";

export type RunExportKind = "scorecard" | "run" | "analysis" | "sitemapJson" | "sitemapMd";

export function runArtifactRelPath(runId: string, kind: RunExportKind): string {
  switch (kind) {
    case "scorecard":
      return `scorecards/${runId}-scorecard.md`;
    case "run":
      return `runs/${runId}.json`;
    case "analysis":
      return `analysis/${runId}.json`;
    case "sitemapJson":
      return `sitemaps/${runId}-sitemap.json`;
    case "sitemapMd":
      return `sitemaps/${runId}-sitemap.md`;
  }
}

export const EXPORT_ITEMS: { kind: RunExportKind; label: string }[] = [
  { kind: "scorecard", label: "scorecard.md" },
  { kind: "run", label: "run.json" },
  { kind: "analysis", label: "analysis.json" },
  { kind: "sitemapJson", label: "sitemap.json" },
  { kind: "sitemapMd", label: "sitemap.md" },
];

function normalizeArtifactPath(path: string): string {
  return path
    .replace(/^launch-rehearsal\/artifacts\//, "")
    .replace(/^artifacts\//, "")
    .replace(/^\//, "");
}

export async function downloadArtifact(relPath: string, filename: string): Promise<void> {
  const clean = normalizeArtifactPath(relPath);
  const res = await fetch(artifactUrl(clean));
  if (!res.ok) {
    throw new Error(`Download failed (${res.status}): ${filename}`);
  }
  const blob = await res.blob();
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

export function buildReproText(issue: Issue, runId: string): string {
  const lines = [
    "# Launch Rehearsal — repro bundle",
    `run_id: ${runId}`,
    `step_id: ${issue.stepId}`,
    `issue_id: ${issue.id}`,
    `severity: ${issue.severity}`,
    `title: ${issue.title}`,
    `persona: ${issue.persona} (${issue.personaId})`,
    `journey: ${issue.journey} (${issue.journeyId})`,
    `dimension: ${issue.dimension}`,
    `confidence: ${issue.confidence}`,
    `owner: ${issue.owner}`,
    "",
    "## Evidence",
    issue.evidence,
  ];
  if (issue.screenshotPath) {
    lines.push("", "## Screenshot", artifactUrl(normalizeArtifactPath(issue.screenshotPath)));
  }
  if (issue.suggestion) {
    lines.push("", "## Suggestion (observe-only)", issue.suggestion);
  }
  return lines.join("\n");
}

export async function copyReproToClipboard(issue: Issue, runId: string): Promise<void> {
  await navigator.clipboard.writeText(buildReproText(issue, runId));
}

export async function downloadRunBundleArtifacts(
  bundle: RunBundle,
): Promise<{ ok: number; failed: string[] }> {
  const runId = bundle.summary.id;
  let ok = 0;
  const failed: string[] = [];

  for (const { kind, label } of EXPORT_ITEMS) {
    try {
      await downloadArtifact(runArtifactRelPath(runId, kind), `${runId}-${label}`);
      ok += 1;
      await new Promise((r) => setTimeout(r, 200));
    } catch {
      failed.push(label);
    }
  }

  for (const shot of bundle.screenshots) {
    try {
      const name = `${shot.stepId}.png`;
      await downloadArtifact(shot.path, `${runId}-${name}`);
      ok += 1;
      await new Promise((r) => setTimeout(r, 150));
    } catch {
      failed.push(shot.stepId);
    }
  }

  return { ok, failed };
}
