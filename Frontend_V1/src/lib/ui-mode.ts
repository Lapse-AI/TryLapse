/**
 * UI modes — **both render the same newest (Vision-level) dashboard chrome.**
 *
 * | Mode        | Command              | Purpose |
 * |-------------|----------------------|---------|
 * | **dev**     | `npm run dev`        | Daily work at http://127.0.0.1:8081/ |
 * | **vision**  | `npm run dev:vision` | Same UI; explicit reference / design builds |
 *
 * Data: live API when `./rehearse serve` is up; Acme mock fallback in **both** when API is down
 * so you always see the full UI while developing. Partner demos: run the API (real runs, not mock).
 *
 * See enterprise_work_env_simulator_2026/UI_PRODUCT_LINES.md
 */

export type UiMode = "vision" | "dev";

/** @deprecated use isDevMode */
export type LegacyUiMode = "vision" | "deliverable";

export function getUiMode(): UiMode {
  const raw = import.meta.env.VITE_UI_MODE;
  if (raw === "vision") return "vision";
  // deliverable env name kept for backwards compat → dev
  return "dev";
}

export const isDevMode = (): boolean => getUiMode() === "dev";
export const isVisionMode = (): boolean => getUiMode() === "vision";
/** @deprecated alias */
export const isDeliverableMode = isDevMode;

/** Both modes show full Vision-level UI with mock when API is offline. */
export const allowsMockFallback = (): boolean => true;

export const uiModeLabel = (): string => (isDevMode() ? "Dev" : "Vision");

/** Both modes ship the same newest UI — use for copy/tooltips. */
export const uiTierLabel = (): string => "Vision UI";
