"""Benchmark recalibration — replace hand-estimated lr-beta-v1 percentiles
with empirical ones, per product category, once enough real launch outcomes
exist to trust.

The deployment-readiness board review flagged this directly: the industry
benchmark numbers in analysis_export._BENCHMARKS were hand-estimated, not
measured — labeled 'lr-beta-v1' to be honest about that, but with no
mechanism to ever become real. This module is that mechanism. Zero
customers have recorded an outcome yet, so every category will keep using
the hand-estimated defaults for a while — that's expected, not a bug. A
category only gets recalibrated once it clears MIN_SAMPLES real outcomes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MIN_SAMPLES = 5


def _benchmarks_path(artifacts_root: Path) -> Path:
    return artifacts_root / "benchmarks.json"


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile — no numpy dependency for one function."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def collect_outcome_readiness_pairs(artifacts_root: Path) -> list[dict[str, Any]]:
    """Pair every recorded launch outcome with the readiness score and product
    category from that run's analysis bundle.

    Category is read from summary.industryBenchmark.category — already
    persisted on every bundle, so no schema change was needed to wire this up.
    """
    from rehearse.dashboard.outcome_store import list_outcomes
    from rehearse.dashboard.store import load_bundle

    pairs: list[dict[str, Any]] = []
    for outcome in list_outcomes(artifacts_root):
        run_id = outcome.get("runId")
        if not run_id:
            continue
        bundle = load_bundle(artifacts_root, run_id, rebuild=False)
        if not bundle:
            continue
        summary = bundle.get("summary", {})
        readiness = summary.get("readiness")
        category = (summary.get("industryBenchmark") or {}).get("category")
        if readiness is None or not category:
            continue
        pairs.append({
            "runId": run_id,
            "category": category,
            "readiness": readiness,
            "launchSucceeded": outcome.get("launchSucceeded"),
        })
    return pairs


def recalibrate_benchmarks(artifacts_root: Path, *, min_samples: int = MIN_SAMPLES) -> dict[str, Any]:
    """Recompute p25/median/p75 per category from real outcomes where there's
    enough data to trust it. Categories below min_samples are simply omitted
    from the result — load_calibrated_benchmarks() falls back to the
    hand-estimated defaults for anything not present here.
    """
    pairs = collect_outcome_readiness_pairs(artifacts_root)
    by_category: dict[str, list[int]] = {}
    for p in pairs:
        by_category.setdefault(p["category"], []).append(p["readiness"])

    calibrated: dict[str, Any] = {}
    for category, scores in by_category.items():
        if len(scores) < min_samples:
            continue
        sorted_scores = sorted(scores)
        calibrated[category] = {
            "p25": round(_percentile(sorted_scores, 25)),
            "median": round(_percentile(sorted_scores, 50)),
            "p75": round(_percentile(sorted_scores, 75)),
            "sampleSize": len(scores),
            "source": "empirical-v1",
        }

    path = _benchmarks_path(artifacts_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(calibrated, indent=2))
    return calibrated


def load_calibrated_benchmarks(artifacts_root: Path) -> dict[str, Any]:
    """Read benchmarks.json — empty dict if recalibration has never run or no
    category has cleared MIN_SAMPLES yet (the overwhelmingly common case)."""
    path = _benchmarks_path(artifacts_root)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}
