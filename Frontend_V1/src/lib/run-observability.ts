import type { RunBundle, StepSnapshot } from "@/lib/mock-data/types";

export type WebVitalsMap = Record<string, number | null | undefined>;

export function formatWebVitalsBrief(vitals: WebVitalsMap | undefined): string | null {
  if (!vitals || Object.keys(vitals).length === 0) return null;
  const lcp = vitals.LCP ?? vitals.lcp;
  const cls = vitals.CLS ?? vitals.cls;
  const inp = vitals.INP ?? vitals.inp;
  const parts: string[] = [];
  if (lcp != null) parts.push(`LCP ${Math.round(lcp)}ms`);
  if (cls != null) parts.push(`CLS ${cls.toFixed(3)}`);
  if (inp != null) parts.push(`INP ${Math.round(inp)}ms`);
  return parts.length ? parts.join(" · ") : null;
}

export function stepObservabilityHint(step: StepSnapshot): string | null {
  const vitals = formatWebVitalsBrief(step.webVitals);
  const warnings = step.consoleWarnings?.length ?? 0;
  const parts: string[] = [];
  if (step.errorType) parts.push(step.errorType);
  if (vitals) parts.push(vitals);
  if (warnings > 0) parts.push(`${warnings} console warn`);
  return parts.length ? parts.join(" · ") : null;
}

function normalizeRelPath(raw: string): string {
  return raw
    .replace(/^launch-rehearsal\/artifacts\//, "")
    .replace(/^artifacts\//, "")
    .replace(/^\//, "");
}

export function extraArtifactDownloads(bundle: RunBundle): { relPath: string; label: string }[] {
  const out: { relPath: string; label: string }[] = [];
  const net = bundle.summary.networkLogPath;
  const vitals = bundle.summary.webVitalsPath;
  if (net) out.push({ relPath: normalizeRelPath(net), label: "network-log.json" });
  if (vitals) out.push({ relPath: normalizeRelPath(vitals), label: "web-vitals.json" });
  return out;
}
