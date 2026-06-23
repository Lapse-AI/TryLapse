"""Benchmark recalibration — empirical percentiles from real launch outcomes.

The board flagged the industry-benchmark numbers as hand-estimated with no
path to becoming real. Zero customers have recorded an outcome yet, so every
category should keep using the lr-beta-v1 defaults until MIN_SAMPLES real
outcomes exist for it — these tests cover both the "no data yet" steady
state and the "just cleared the threshold" transition.
"""

from __future__ import annotations

import json
from pathlib import Path

from rehearse.dashboard.benchmark_recalibration import (
    MIN_SAMPLES,
    collect_outcome_readiness_pairs,
    load_calibrated_benchmarks,
    recalibrate_benchmarks,
)
from rehearse.dashboard.outcome_store import record_outcome


def _write_bundle(output_dir: Path, run_id: str, readiness: int, category: str = "b2b_saas") -> None:
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "summary": {
            "id": run_id,
            "readiness": readiness,
            "industryBenchmark": {"category": category, "categoryLabel": "B2B SaaS"},
        }
    }
    (analysis_dir / f"{run_id}.json").write_text(json.dumps(bundle))


# ── collect_outcome_readiness_pairs ──────────────────────────────────────────


def test_collect_pairs_empty_with_no_outcomes(tmp_path: Path):
    assert collect_outcome_readiness_pairs(tmp_path) == []


def test_collect_pairs_joins_outcome_and_bundle(tmp_path: Path):
    _write_bundle(tmp_path, "run-1", 72)
    record_outcome(tmp_path, {"runId": "run-1", "launchSucceeded": True})

    pairs = collect_outcome_readiness_pairs(tmp_path)
    assert len(pairs) == 1
    assert pairs[0]["readiness"] == 72
    assert pairs[0]["category"] == "b2b_saas"
    assert pairs[0]["launchSucceeded"] is True


def test_collect_pairs_skips_outcome_with_no_bundle(tmp_path: Path):
    record_outcome(tmp_path, {"runId": "nonexistent-run", "launchSucceeded": True})
    assert collect_outcome_readiness_pairs(tmp_path) == []


# ── recalibrate_benchmarks ────────────────────────────────────────────────────


def test_recalibrate_below_min_samples_produces_nothing(tmp_path: Path):
    for i in range(MIN_SAMPLES - 1):
        _write_bundle(tmp_path, f"run-{i}", 70 + i)
        record_outcome(tmp_path, {"runId": f"run-{i}", "launchSucceeded": True})

    result = recalibrate_benchmarks(tmp_path)
    assert result == {}


def test_recalibrate_at_min_samples_produces_empirical_entry(tmp_path: Path):
    scores = [50, 60, 70, 80, 90][:MIN_SAMPLES]
    for i, score in enumerate(scores):
        _write_bundle(tmp_path, f"run-{i}", score)
        record_outcome(tmp_path, {"runId": f"run-{i}", "launchSucceeded": True})

    result = recalibrate_benchmarks(tmp_path)
    assert "b2b_saas" in result
    entry = result["b2b_saas"]
    assert entry["sampleSize"] == MIN_SAMPLES
    assert entry["source"] == "empirical-v1"
    assert entry["p25"] <= entry["median"] <= entry["p75"]


def test_recalibrate_separates_categories(tmp_path: Path):
    for i in range(MIN_SAMPLES):
        _write_bundle(tmp_path, f"saas-{i}", 60 + i, category="b2b_saas")
        record_outcome(tmp_path, {"runId": f"saas-{i}", "launchSucceeded": True})
    for i in range(MIN_SAMPLES - 1):
        _write_bundle(tmp_path, f"eco-{i}", 60 + i, category="ecommerce")
        record_outcome(tmp_path, {"runId": f"eco-{i}", "launchSucceeded": True})

    result = recalibrate_benchmarks(tmp_path)
    assert "b2b_saas" in result
    assert "ecommerce" not in result  # below MIN_SAMPLES, correctly omitted


def test_recalibrate_on_nonexistent_artifacts_root_does_not_crash(tmp_path: Path):
    """A fresh deployment with zero runs has no artifacts/ directory at all —
    recalibrate_benchmarks() must not crash trying to write into it."""
    fresh_root = tmp_path / "never-created-yet"
    assert not fresh_root.exists()
    result = recalibrate_benchmarks(fresh_root)
    assert result == {}
    assert (fresh_root / "benchmarks.json").is_file()


def test_recalibrate_writes_benchmarks_json(tmp_path: Path):
    for i in range(MIN_SAMPLES):
        _write_bundle(tmp_path, f"run-{i}", 65 + i)
        record_outcome(tmp_path, {"runId": f"run-{i}", "launchSucceeded": True})
    recalibrate_benchmarks(tmp_path)
    assert (tmp_path / "benchmarks.json").is_file()


# ── load_calibrated_benchmarks ────────────────────────────────────────────────


def test_load_calibrated_benchmarks_empty_when_never_run(tmp_path: Path):
    assert load_calibrated_benchmarks(tmp_path) == {}


def test_load_calibrated_benchmarks_roundtrip(tmp_path: Path):
    for i in range(MIN_SAMPLES):
        _write_bundle(tmp_path, f"run-{i}", 55 + i)
        record_outcome(tmp_path, {"runId": f"run-{i}", "launchSucceeded": True})
    written = recalibrate_benchmarks(tmp_path)
    loaded = load_calibrated_benchmarks(tmp_path)
    assert loaded == written


def test_load_calibrated_benchmarks_handles_corrupt_file(tmp_path: Path):
    (tmp_path / "benchmarks.json").write_text("not valid json{{{")
    assert load_calibrated_benchmarks(tmp_path) == {}


# ── integration with _industry_benchmark ─────────────────────────────────────


def test_industry_benchmark_falls_back_to_default_without_calibration(tmp_path: Path):
    from rehearse.analysis_export import _industry_benchmark

    result = _industry_benchmark("b2b_saas", 70, tmp_path)
    assert result["source"] == "lr-beta-v1"


def test_industry_benchmark_uses_calibrated_data_when_present(tmp_path: Path):
    from rehearse.analysis_export import _industry_benchmark

    for i in range(MIN_SAMPLES):
        _write_bundle(tmp_path, f"run-{i}", 50 + i * 5)
        record_outcome(tmp_path, {"runId": f"run-{i}", "launchSucceeded": True})
    recalibrate_benchmarks(tmp_path)

    result = _industry_benchmark("b2b_saas", 70, tmp_path)
    assert result["source"] == "empirical-v1"
    assert result["sampleSize"] == MIN_SAMPLES


def test_industry_benchmark_without_output_dir_uses_default():
    from rehearse.analysis_export import _industry_benchmark

    result = _industry_benchmark("b2b_saas", 70)
    assert result["source"] == "lr-beta-v1"
