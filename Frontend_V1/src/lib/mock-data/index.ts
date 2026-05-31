/** Mock data barrel — types, store, and helpers. Replace with API client in Phase 2. */

export * from "./types";
export * from "./store";

import type { Issue, Status } from "./types";

export const bandFromIssues = (list: Issue[]): Status => {
  if (list.some((i) => i.severity === "P0")) return "danger";
  if (list.some((i) => i.severity === "P1")) return "warn";
  return "ready";
};

export const countBlockers = (list: Issue[]) =>
  list.filter((i) => i.severity === "P0" || i.severity === "P1").length;

export const bandLabel = (s: Status) =>
  s === "danger" ? "Red" : s === "warn" ? "Amber" : s === "ready" ? "Green" : "Neutral";

export const formatRel = (iso: string) => {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

export const formatDuration = (sec: number) => {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
};

export const formatDurationMs = (ms: number) => formatDuration(Math.round(ms / 1000));

import type { RunBundle } from "./types";
import { getJourneysForRun, getPersonasForRun } from "./store";

export const bundlePersonas = (bundle: RunBundle) =>
  bundle.personas ?? getPersonasForRun(bundle.summary.id);
export const bundleJourneys = (bundle: RunBundle) =>
  bundle.journeys ?? getJourneysForRun(bundle.summary.id);
export const cellGrade = (bundle: RunBundle, personaId: string, journeyId: string) =>
  bundle.matrix.find((c) => c.personaId === personaId && c.journeyId === journeyId)?.grade ??
  "pass";
