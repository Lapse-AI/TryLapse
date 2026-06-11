/** Client-side export helpers — downloads via /files/ (rehearse serve). */

import { artifactUrl } from "@/lib/api/client";
import { extraArtifactDownloads } from "@/lib/run-observability";
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

  for (const { relPath, label } of extraArtifactDownloads(bundle)) {
    try {
      await downloadArtifact(relPath, `${runId}-${label}`);
      ok += 1;
      await new Promise((r) => setTimeout(r, 150));
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

export function generateReportMarkdown(bundle: RunBundle): string {
  const run = bundle.summary;
  const SEVERITY_LABELS: Record<string, string> = { P0: "Critical", P1: "High", P2: "Medium", P3: "Low" };
  const sevs = ["P0", "P1", "P2", "P3"] as const;

  const lines: string[] = [
    `# TryLapse Run Report`,
    ``,
    `**Run ID:** \`${run.id}\`  `,
    `**Product:** ${run.productName}  `,
    `**Target:** ${run.targetUrl}  `,
    `**Environment:** ${run.env}  `,
    `**Started:** ${new Date(run.startedAt).toLocaleString()}  `,
    `**Duration:** ${run.durationSec}s  `,
    ``,
    `## Readiness`,
    ``,
    `| Metric | Value |`,
    `|--------|-------|`,
    `| Score | **${run.readiness}** |`,
    `| Band | **${run.readinessBand}** |`,
    `| Critical | ${bundle.issues.filter((i) => i.severity === "P0").length} |`,
    `| High | ${bundle.issues.filter((i) => i.severity === "P1").length} |`,
    `| Total issues | ${bundle.issues.length} |`,
    `| Highlights | ${bundle.delights.length} |`,
    `| Steps | ${run.stepCount} |`,
    `| Pages | ${run.pages || 0} |`,
    `| Agent cost | $${run.agentCost.toFixed(4)} |`,
    ``,
  ];

  if (bundle.narrative) {
    lines.push(`## Executive Summary`, ``);
    lines.push(bundle.narrative.executiveSummary, ``);
    if (bundle.narrative.forFounders) {
      lines.push(`### For Founders`, ``, bundle.narrative.forFounders, ``);
    }
    if (bundle.narrative.forEngineering) {
      lines.push(`### For Engineering`, ``, bundle.narrative.forEngineering, ``);
    }
  }

  if (bundle.issues.length > 0) {
    lines.push(`## Findings`, ``);
    for (const sev of sevs) {
      const sevIssues = bundle.issues.filter((i) => i.severity === sev);
      if (!sevIssues.length) continue;
      lines.push(
        `### ${SEVERITY_LABELS[sev]} (${sev}) — ${sevIssues.length} issue${sevIssues.length > 1 ? "s" : ""}`,
        ``,
      );
      for (const issue of sevIssues) {
        lines.push(`**${issue.title}**`);
        lines.push(`- Persona: ${issue.persona}`);
        lines.push(`- Journey: ${issue.journey} · Step: \`${issue.stepId}\``);
        lines.push(`- Dimension: ${issue.dimension} · Owner: ${issue.owner}`);
        lines.push(`- Confidence: ${issue.confidence}`);
        lines.push(`- Evidence: ${issue.evidence}`);
        if (issue.suggestion) lines.push(`- Suggestion: ${issue.suggestion}`);
        lines.push(``);
      }
    }
  }

  if (bundle.delights.length > 0) {
    lines.push(`## Highlights`, ``);
    for (const d of bundle.delights) {
      lines.push(`### ${d.title}`);
      lines.push(`> "${d.quote}"`);
      lines.push(`— ${d.persona}${d.marketingReady ? " · ⭐ marketing-ready" : ""}`, ``);
    }
  }

  if (bundle.dimensions.length > 0) {
    lines.push(`## Dimension Scores`, ``);
    lines.push(`| Dimension | Score |`);
    lines.push(`|-----------|-------|`);
    for (const d of bundle.dimensions) {
      lines.push(`| ${d.name} | ${d.score} |`);
    }
    lines.push(``);
  }

  const activeAgents = bundle.agents.filter((a) => a.status !== "idle");
  if (activeAgents.length > 0) {
    lines.push(`## Agent Participation`, ``);
    lines.push(`| Agent | Status | Duration | Cost |`);
    lines.push(`|-------|--------|----------|------|`);
    for (const a of activeAgents) {
      lines.push(`| ${a.name} | ${a.status} | ${a.durationSec}s | $${a.costUsd.toFixed(4)} |`);
    }
    lines.push(``);
  }

  lines.push(
    `---`,
    ``,
    `*Generated by TryLapse · ${new Date().toLocaleString()}*`,
  );

  return lines.join("\n");
}

export function downloadReportMarkdown(bundle: RunBundle): void {
  const md = generateReportMarkdown(bundle);
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${bundle.summary.id}-report.md`;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function printReportAsPdf(bundle: RunBundle): void {
  const run = bundle.summary;
  const critical = bundle.issues.filter((i) => i.severity === "P0");
  const high = bundle.issues.filter((i) => i.severity === "P1");
  const medium = bundle.issues.filter((i) => i.severity === "P2");
  const low = bundle.issues.filter((i) => i.severity === "P3");

  const bandColor = run.readinessBand === "Green" ? "#16a34a" : run.readinessBand === "Amber" ? "#ca8a04" : "#dc2626";
  const bandBg = run.readinessBand === "Green" ? "#dcfce7" : run.readinessBand === "Amber" ? "#fef9c3" : "#fee2e2";

  const severityRows = (issues: Issue[], color: string) =>
    issues
      .map(
        (i) => `<tr>
        <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;vertical-align:top;width:52px">
          <span style="background:${color}18;color:${color};border:1px solid ${color}44;border-radius:4px;padding:1px 6px;font-size:11px;font-weight:600">${i.severity}</span>
        </td>
        <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;vertical-align:top;font-weight:500;font-size:13px">${i.title}</td>
        <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;vertical-align:top;font-size:12px;color:#6b7280;width:140px">${i.persona}<br/><span style="font-family:monospace">${i.journey}</span></td>
        <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;vertical-align:top;font-family:monospace;font-size:11px;color:#6b7280">${(i.evidence || "").slice(0, 120)}${(i.evidence || "").length > 120 ? "…" : ""}</td>
      </tr>`,
      )
      .join("");

  const issueSection = (label: string, issues: Issue[], color: string) =>
    issues.length === 0
      ? ""
      : `<h3 style="font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin:20px 0 8px">${label} — ${issues.length}</h3>
         <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
           <thead><tr style="background:#f9fafb">
             <th style="padding:6px 12px;text-align:left;font-size:11px;color:#9ca3af;font-weight:500;border-bottom:2px solid #e5e7eb">Sev.</th>
             <th style="padding:6px 12px;text-align:left;font-size:11px;color:#9ca3af;font-weight:500;border-bottom:2px solid #e5e7eb">Title</th>
             <th style="padding:6px 12px;text-align:left;font-size:11px;color:#9ca3af;font-weight:500;border-bottom:2px solid #e5e7eb">Context</th>
             <th style="padding:6px 12px;text-align:left;font-size:11px;color:#9ca3af;font-weight:500;border-bottom:2px solid #e5e7eb">Evidence</th>
           </tr></thead>
           <tbody>${severityRows(issues, color)}</tbody>
         </table>`;

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>TryLapse Report — ${run.id}</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#111;background:#fff;padding:48px;max-width:960px;margin:0 auto;font-size:14px;line-height:1.5}
    h1{font-size:26px;font-weight:800;letter-spacing:-.02em;margin-bottom:4px}
    h2{font-size:15px;font-weight:700;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid #e5e7eb;color:#374151}
    .meta{color:#6b7280;font-size:13px;margin-bottom:4px}
    .stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:20px 0}
    .stat{background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px}
    .stat-label{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}
    .stat-value{font-size:28px;font-weight:800;line-height:1}
    .narrative{background:#f0f9ff;border:1px solid #bae6fd;border-left:4px solid #0ea5e9;border-radius:8px;padding:18px;margin:16px 0}
    .narrative-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:14px}
    .narrative-label{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
    .highlight-card{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px 18px;margin-bottom:10px}
    blockquote{border-left:3px solid #22c55e;padding-left:12px;font-style:italic;margin:10px 0;color:#374151}
    .dim-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0}
    .dim{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center}
    .footer{margin-top:48px;padding-top:16px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af}
    @media print{body{padding:24px}@page{margin:.75in}}
  </style>
</head>
<body>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
    <div>
      <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">TryLapse · Run Report</div>
      <h1>${run.productName}</h1>
      <div class="meta">${run.targetUrl}</div>
      <div class="meta" style="font-family:monospace;font-size:12px">${run.id}</div>
      <div class="meta">${new Date(run.startedAt).toLocaleString()} · ${run.durationSec}s · ${run.env}</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:11px;color:#9ca3af;margin-bottom:4px">READINESS</div>
      <div style="font-size:52px;font-weight:900;color:${bandColor};line-height:1">${run.readiness}</div>
      <div style="background:${bandBg};color:${bandColor};border-radius:6px;padding:3px 12px;font-size:13px;font-weight:700;display:inline-block;margin-top:4px">${run.readinessBand}</div>
    </div>
  </div>

  <div class="stat-grid">
    <div class="stat"><div class="stat-label">Critical</div><div class="stat-value" style="color:#dc2626">${critical.length}</div></div>
    <div class="stat"><div class="stat-label">High</div><div class="stat-value" style="color:#ea580c">${high.length}</div></div>
    <div class="stat"><div class="stat-label">Highlights</div><div class="stat-value" style="color:#16a34a">${bundle.delights.length}</div></div>
    <div class="stat"><div class="stat-label">Pages</div><div class="stat-value">${run.pages || "—"}</div></div>
  </div>

  ${
    bundle.narrative
      ? `<h2>Executive Summary</h2>
    <div class="narrative">
      <p style="font-weight:500;margin-bottom:12px">${bundle.narrative.executiveSummary}</p>
      <div class="narrative-grid">
        <div><div class="narrative-label">For founders</div><p style="font-size:13px;color:#374151">${bundle.narrative.forFounders}</p></div>
        <div><div class="narrative-label">For engineering</div><p style="font-size:13px;color:#374151">${bundle.narrative.forEngineering}</p></div>
      </div>
    </div>`
      : ""
  }

  ${
    bundle.issues.length > 0
      ? `<h2>Findings (${bundle.issues.length} total)</h2>
    ${issueSection("Critical", critical, "#ef4444")}
    ${issueSection("High", high, "#f97316")}
    ${issueSection("Medium", medium, "#3b82f6")}
    ${issueSection("Low", low, "#6b7280")}`
      : ""
  }

  ${
    bundle.delights.length > 0
      ? `<h2>Highlights (${bundle.delights.length})</h2>
    ${bundle.delights
      .map(
        (d) => `<div class="highlight-card">
      <strong style="font-size:13px">${d.title}</strong>${d.marketingReady ? ` <span style="background:#dcfce7;color:#166534;border-radius:4px;padding:1px 6px;font-size:11px;margin-left:6px">marketing-ready</span>` : ""}
      <blockquote>"${d.quote}"</blockquote>
      <div style="font-size:12px;color:#9ca3af;margin-top:4px">— ${d.persona}</div>
    </div>`,
      )
      .join("")}`
      : ""
  }

  ${
    bundle.dimensions.length > 0
      ? `<h2>Dimension Scores</h2>
    <div class="dim-grid">
      ${bundle.dimensions
        .map((d) => {
          const c = d.score >= 80 ? "#16a34a" : d.score >= 60 ? "#ca8a04" : "#dc2626";
          return `<div class="dim"><span style="font-size:13px">${d.name}</span><span style="font-family:monospace;font-weight:800;font-size:18px;color:${c}">${d.score}</span></div>`;
        })
        .join("")}
    </div>`
      : ""
  }

  <h2>Run Details</h2>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:6px 12px;color:#9ca3af;font-size:12px;width:160px;border-bottom:1px solid #f3f4f6">Steps</td><td style="padding:6px 12px;font-family:monospace;border-bottom:1px solid #f3f4f6">${run.stepCount}</td></tr>
    <tr><td style="padding:6px 12px;color:#9ca3af;font-size:12px;border-bottom:1px solid #f3f4f6">Agent cost</td><td style="padding:6px 12px;font-family:monospace;border-bottom:1px solid #f3f4f6">$${run.agentCost.toFixed(4)}</td></tr>
    <tr><td style="padding:6px 12px;color:#9ca3af;font-size:12px;border-bottom:1px solid #f3f4f6">Config hash</td><td style="padding:6px 12px;font-family:monospace;font-size:12px;border-bottom:1px solid #f3f4f6">${run.configHash}</td></tr>
    ${run.authAttempted ? `<tr><td style="padding:6px 12px;color:#9ca3af;font-size:12px;border-bottom:1px solid #f3f4f6">Auth</td><td style="padding:6px 12px;font-family:monospace;border-bottom:1px solid #f3f4f6">${run.authOutcome || "attempted"}</td></tr>` : ""}
    ${run.llmEnabled ? `<tr><td style="padding:6px 12px;color:#9ca3af;font-size:12px">LLM</td><td style="padding:6px 12px">enabled</td></tr>` : ""}
  </table>

  <div class="footer">Generated by TryLapse · ${new Date().toLocaleString()}</div>
</body>
</html>`;

  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to generate the PDF report.");
    return;
  }
  win.document.write(html);
  win.document.close();
  win.focus();
  setTimeout(() => win.print(), 600);
}
