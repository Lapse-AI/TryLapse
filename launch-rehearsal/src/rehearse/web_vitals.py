"""Web Vitals collection via Performance API (Playwright page.evaluate)."""

from __future__ import annotations

from typing import Any

# Thresholds aligned with Core Web Vitals guidance (approximate for lab runs).
LCP_POOR_MS = 4000
CLS_POOR = 0.25
INP_POOR_MS = 500

_COLLECT_SCRIPT = """
() => {
  const out = { lcp: null, cls: null, inp: null, fcp: null, ttfb: null };
  try {
    const nav = performance.getEntriesByType('navigation')[0];
    if (nav && nav.responseStart > 0) {
      out.ttfb = Math.round(nav.responseStart - nav.requestStart);
    }
    const paints = performance.getEntriesByType('paint');
    const fcp = paints.find((e) => e.name === 'first-contentful-paint');
    if (fcp) out.fcp = Math.round(fcp.startTime);
    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
    if (lcpEntries.length) {
      out.lcp = Math.round(lcpEntries[lcpEntries.length - 1].startTime);
    }
    let cls = 0;
    for (const e of performance.getEntriesByType('layout-shift')) {
      if (!e.hadRecentInput) cls += e.value;
    }
    out.cls = Math.round(cls * 1000) / 1000;
    const events = performance.getEntriesByType('event');
    const slow = events.filter((e) => e.duration > 0).sort((a, b) => b.duration - a.duration);
    if (slow.length) out.inp = Math.round(slow[0].duration);
  } catch (e) {
    out.error = String(e).slice(0, 120);
  }
  return out;
}
"""


def collect_web_vitals(page: Any) -> dict[str, float | None]:
    """Best-effort lab vitals after navigation (may be null if paint not finished)."""
    try:
        raw = page.evaluate(_COLLECT_SCRIPT)
        if not isinstance(raw, dict):
            return {}
        out: dict[str, float | None] = {}
        for key in ("lcp", "cls", "inp", "fcp", "ttfb"):
            val = raw.get(key)
            if val is None:
                out[key] = None
            else:
                try:
                    out[key] = float(val)
                except (TypeError, ValueError):
                    out[key] = None
        return out
    except Exception:
        return {}


def vitals_issues(vitals: dict[str, float | None]) -> list[str]:
    """Human-readable issue strings for poor vitals."""
    notes: list[str] = []
    lcp = vitals.get("lcp")
    if lcp is not None and lcp >= LCP_POOR_MS:
        notes.append(f"LCP {int(lcp)}ms exceeds {LCP_POOR_MS}ms")
    cls = vitals.get("cls")
    if cls is not None and cls >= CLS_POOR:
        notes.append(f"CLS {cls} exceeds {CLS_POOR}")
    inp = vitals.get("inp")
    if inp is not None and inp >= INP_POOR_MS:
        notes.append(f"INP {int(inp)}ms exceeds {INP_POOR_MS}ms")
    return notes
