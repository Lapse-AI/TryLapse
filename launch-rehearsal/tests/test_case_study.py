"""Auto-generated before/after case study — turns the outcome feedback loop
into a sales asset, not just a calibration mechanism.

Needs at least two runs for a workspace to say anything meaningful; a single
run produces no case study rather than a thin, unconvincing one.
"""

from __future__ import annotations

import json
from pathlib import Path

from rehearse.dashboard.case_study import generate_case_study, render_case_study_markdown
from rehearse.dashboard.outcome_store import record_outcome


def _write_run(output_dir: Path, run_id: str, *, readiness: int, gate: str, blockers: int,
                delights: int = 3, started_at: str, product_name: str = "Acme") -> None:
    runs_dir = output_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / f"{run_id}.json").write_text(json.dumps({"run_id": run_id, "steps": []}))

    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "summary": {
            "id": run_id,
            "productName": product_name,
            "readiness": readiness,
            "launchGate": gate,
            "blockers": blockers,
            "delights": delights,
            "startedAt": started_at,
        }
    }
    (analysis_dir / f"{run_id}.json").write_text(json.dumps(bundle))


# ── generate_case_study ───────────────────────────────────────────────────────


def test_no_case_study_with_zero_runs(tmp_path: Path):
    assert generate_case_study(tmp_path, "acme") is None


def test_no_case_study_with_single_run(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    assert generate_case_study(tmp_path, "acme") is None


def test_case_study_picks_earliest_and_latest(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=60, gate="CAUTION", blockers=1,
               started_at="2026-06-10T00:00:00+00:00")
    _write_run(tmp_path, "acme-3", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")

    case_study = generate_case_study(tmp_path, "acme")
    assert case_study["before"]["runId"] == "acme-1"
    assert case_study["after"]["runId"] == "acme-3"
    assert case_study["totalRuns"] == 3
    assert case_study["readinessDelta"] == 45
    assert case_study["blockersResolved"] == 3


def test_case_study_excludes_other_workspaces(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=80, gate="PASS", blockers=0,
               started_at="2026-06-15T00:00:00+00:00")
    _write_run(tmp_path, "other-1", readiness=50, gate="CAUTION", blockers=2,
               started_at="2026-06-05T00:00:00+00:00")

    case_study = generate_case_study(tmp_path, "acme")
    assert case_study["totalRuns"] == 2
    assert case_study["before"]["runId"] == "acme-1"
    assert case_study["after"]["runId"] == "acme-2"


def test_case_study_includes_outcome_when_recorded(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")
    record_outcome(tmp_path, {
        "runId": "acme-2", "launchSucceeded": True, "notes": "Smooth launch, no incidents.",
    })

    case_study = generate_case_study(tmp_path, "acme")
    assert case_study["outcome"]["launchSucceeded"] is True
    assert case_study["outcome"]["notes"] == "Smooth launch, no incidents."


def test_case_study_outcome_is_none_when_not_recorded(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")
    case_study = generate_case_study(tmp_path, "acme")
    assert case_study["outcome"] is None


def test_case_study_blockers_resolved_never_negative(tmp_path: Path):
    """If blockers somehow increased, blockersResolved should clamp at 0, not go negative."""
    _write_run(tmp_path, "acme-1", readiness=70, gate="REVIEW", blockers=0,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=50, gate="CAUTION", blockers=2,
               started_at="2026-06-10T00:00:00+00:00")
    case_study = generate_case_study(tmp_path, "acme")
    assert case_study["blockersResolved"] == 0
    assert case_study["readinessDelta"] == -20


# ── render_case_study_markdown ────────────────────────────────────────────────


def test_render_markdown_includes_key_figures(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")
    case_study = generate_case_study(tmp_path, "acme")
    md = render_case_study_markdown(case_study)

    assert "40" in md
    assert "85" in md
    assert "BLOCKED" in md
    assert "PASS" in md
    assert "+45" in md
    assert "acme-1" in md
    assert "acme-2" in md


def test_render_markdown_shows_unrecorded_outcome_notice(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")
    case_study = generate_case_study(tmp_path, "acme")
    md = render_case_study_markdown(case_study)
    assert "not yet recorded" in md.lower()


def test_render_markdown_shows_successful_outcome(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")
    record_outcome(tmp_path, {"runId": "acme-2", "launchSucceeded": True, "notes": "Great launch."})
    case_study = generate_case_study(tmp_path, "acme")
    md = render_case_study_markdown(case_study)
    assert "succeeded" in md.lower()
    assert "Great launch." in md


def test_render_markdown_shows_failed_outcome(tmp_path: Path):
    _write_run(tmp_path, "acme-1", readiness=40, gate="BLOCKED", blockers=3,
               started_at="2026-06-01T00:00:00+00:00")
    _write_run(tmp_path, "acme-2", readiness=85, gate="PASS", blockers=0,
               started_at="2026-06-20T00:00:00+00:00")
    record_outcome(tmp_path, {"runId": "acme-2", "launchSucceeded": False, "notes": "Rocky rollout."})
    case_study = generate_case_study(tmp_path, "acme")
    md = render_case_study_markdown(case_study)
    assert "did not go as planned" in md.lower()
