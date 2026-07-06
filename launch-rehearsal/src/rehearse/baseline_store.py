"""Statistical baseline scoring for per-config metric history.

Reads the last N completed analysis files for a given config prefix and
computes rolling mean + standard deviation for key metrics. Returns
z-scores so callers can report "LCP is 3.2σ above your 90-day average"
rather than raw absolute values.

First run: no baseline → z-scores are None. From run 2 onward, z-scores
are computed against the prior N-1 runs (current run is not included in
its own baseline).
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

# Number of prior runs to use for baseline (excludes current run)
_BASELINE_WINDOW = 90


def _config_prefix(run_id: str) -> str:
    m = re.match(r"^(.*)-\d{8}-\d{6}$", run_id)
    return m.group(1) if m else run_id


def _mean_std(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, None
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, math.sqrt(variance)


def _zscore(value: float | None, mean: float | None, std: float | None) -> float | None:
    if value is None or mean is None or std is None or std == 0:
        return None
    return round((value - mean) / std, 2)


def _extract_metrics(summary: dict[str, Any], dimensions: dict[str, Any] | None) -> dict[str, float | None]:
    """Pull the numeric signals we want to baseline from a single bundle summary."""
    metrics: dict[str, float | None] = {
        "readiness": _to_float(summary.get("readiness")),
        "flakeRate": _to_float(summary.get("flakeRate")),
        "blockerCount": _to_float(summary.get("blockers")),
        "issueCount": _to_float(summary.get("issues")),
        "stepCount": _to_float(summary.get("stepCount")),
        "durationSec": _to_float(summary.get("durationSec")),
        "pagesCrawled": _to_float(summary.get("pagesCrawled")),
    }
    # Per-dimension scores
    if dimensions:
        for dim_name, dim_val in dimensions.items():
            score: float | None = None
            if isinstance(dim_val, dict):
                score = _to_float(dim_val.get("score"))
            elif isinstance(dim_val, (int, float)):
                score = float(dim_val)
            if score is not None:
                metrics[f"dim_{dim_name.lower().replace(' ', '_')}"] = score
    return metrics


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _load_prior_metrics(
    artifacts_root: Path, config_prefix_str: str, current_run_id: str
) -> list[dict[str, float | None]]:
    """Read the last _BASELINE_WINDOW analysis files (excluding current) and extract metrics."""
    analysis_dir = artifacts_root / "analysis"
    if not analysis_dir.is_dir():
        return []

    prior_files = sorted(
        [
            f
            for f in analysis_dir.glob(f"{config_prefix_str}-*.json")
            if f.stem != current_run_id
        ],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[: _BASELINE_WINDOW]

    result = []
    for path in prior_files:
        try:
            data = json.loads(path.read_text())
            summary = data.get("summary", {})
            dimensions = data.get("dimensions")
            result.append(_extract_metrics(summary, dimensions))
        except Exception:
            continue
    return result


def compute_baseline(
    artifacts_root: Path,
    run_id: str,
    current_summary: dict[str, Any],
    current_dimensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return baseline statistics for this run relative to prior runs.

    Shape returned:
    {
        "runCount":   int,          # number of prior runs used
        "metrics": {
            "<metric_name>": {
                "current":  float | None,
                "mean":     float | None,
                "std":      float | None,
                "zScore":   float | None,   # (current - mean) / std
                "trend":    "improved" | "degraded" | "stable" | None
            }
        }
    }

    Returns {"runCount": 0, "metrics": {}} on first run.
    """
    prefix = _config_prefix(run_id)
    prior = _load_prior_metrics(artifacts_root, prefix, run_id)
    current_metrics = _extract_metrics(current_summary, current_dimensions)

    if not prior:
        return {"runCount": 0, "metrics": {}}

    # Build per-metric time series from prior runs
    all_keys: set[str] = set(current_metrics) | {k for p in prior for k in p}

    baseline_metrics: dict[str, dict[str, Any]] = {}
    for key in all_keys:
        values = [p[key] for p in prior if p.get(key) is not None]
        current = current_metrics.get(key)
        mean, std = _mean_std([v for v in values if v is not None])
        z = _zscore(current, mean, std)

        # Trend direction: positive z means higher than average.
        # For most metrics higher = worse (flake, blockers, issues, duration).
        # For readiness + dim scores, higher = better.
        higher_is_better = key in {"readiness"} or key.startswith("dim_")
        trend: str | None = None
        if z is not None:
            threshold = 0.5
            if abs(z) < threshold:
                trend = "stable"
            elif (z > 0 and higher_is_better) or (z < 0 and not higher_is_better):
                trend = "improved"
            else:
                trend = "degraded"

        baseline_metrics[key] = {
            "current": current,
            "mean": round(mean, 2) if mean is not None else None,
            "std": round(std, 2) if std is not None else None,
            "zScore": z,
            "trend": trend,
        }

    return {"runCount": len(prior), "metrics": baseline_metrics}
