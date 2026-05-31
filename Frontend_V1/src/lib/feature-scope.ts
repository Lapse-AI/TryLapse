/**
 * Maps UI surfaces to backend support level.
 * Authority: enterprise_work_env_simulator_2026/FEATURE_SCOPE.md
 */

import type { UiMode } from "./ui-mode";
import { getUiMode } from "./ui-mode";

export type ScopeLevel = "L1" | "L2" | "L3";

export type RouteScope = {
  path: string;
  label: string;
  level: ScopeLevel;
  /** Shown in deliverable build (L1-backed or honest catalog). */
  deliverable: boolean;
  notes?: string;
};

/** Nav + route registry — Vision shows all; Deliverable filters to L1 + static catalogs. */
export const ROUTE_SCOPE: RouteScope[] = [
  { path: "/", label: "Command center", level: "L1", deliverable: true },
  { path: "/runs", label: "Runs", level: "L1", deliverable: true },
  { path: "/runner", label: "Runner", level: "L1", deliverable: true },
  { path: "/compare", label: "Compare runs", level: "L1", deliverable: true },
  {
    path: "/trends",
    label: "Trends",
    level: "L1",
    deliverable: true,
    notes: "Sparklines from /api/trends; recurrence/schedule are Vision-only",
  },
  {
    path: "/alerts",
    label: "Alerts",
    level: "L2",
    deliverable: true,
    notes: "Static rule catalog (L1 API); delivery + feed are Vision",
  },
  { path: "/recommendations", label: "Recommendations", level: "L1", deliverable: true },
  { path: "/sitemap", label: "Site map", level: "L1", deliverable: true },
  { path: "/workflows", label: "Workflows", level: "L1", deliverable: true },
  { path: "/library", label: "Journey library", level: "L1", deliverable: true },
  {
    path: "/agents",
    label: "Agent control",
    level: "L1",
    deliverable: true,
    notes: "Roster from bundle; config/replay toggles are Vision",
  },
  { path: "/init", label: "Init wizard", level: "L1", deliverable: true },
  {
    path: "/config",
    label: "Workspace",
    level: "L2",
    deliverable: true,
    notes: "Workspace API L1; YAML editor / audit log Vision",
  },
  {
    path: "/integrations",
    label: "Integrations",
    level: "L2",
    deliverable: true,
    notes: "Catalog L1; OAuth Connect Vision",
  },
  { path: "/cli", label: "CLI", level: "L1", deliverable: true },
];

export function routesForMode(mode: UiMode = getUiMode()): RouteScope[] {
  if (mode === "vision") return ROUTE_SCOPE;
  return ROUTE_SCOPE.filter((r) => r.deliverable);
}

export function isRouteDeliverable(path: string): boolean {
  const row = ROUTE_SCOPE.find((r) => r.path === path || path.startsWith(`${r.path}/`));
  return row?.deliverable ?? false;
}

/** UI sections that exist only in Vision (mock or Phase 2 shell). */
export const VISION_ONLY_SECTIONS = [
  "trends.recurrence",
  "trends.scheduledRuns",
  "trends.calendarHeatmap",
  "trends.hardcodedIssueStats",
  "trends.dimensionSparklinesMock",
  "alerts.recentFeed",
  "alerts.addChannel",
  "integrations.connectButtons",
  "config.yamlEditor",
  "config.personasEditor",
  "config.secretsVault",
  "config.auditLog",
  "config.agentToggles",
  "agents.configurePanel",
  "agents.replayFindings",
  "agents.llmConfigDefaults",
  "chrome.envSelector",
  "chrome.mockFallback",
] as const;

export type VisionSection = (typeof VISION_ONLY_SECTIONS)[number];

/** All sections render in dev and Vision — same newest UI tier. */
export function showVisionSection(_section: VisionSection): boolean {
  return true;
}
