"""Usage metering — runs per workspace per billing period.

Foundational for plan-tier enforcement: a tier's "8 runs/month" limit is
meaningless without a reliable count. Jobs aren't linked to workspace_id
directly, so these tests cover the config_prefix attribution path (same
mechanism the Runs page already uses) and the calendar-month boundary math.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rehearse.dashboard.job_store import save_job
from rehearse.dashboard.usage_store import (
    count_runs_in_period,
    current_period_bounds,
    usage_for_workspace,
)


def _job(job_id: str, config: str, started_at: str) -> dict:
    return {
        "id": job_id,
        "status": "done",
        "config": config,
        "startedAt": started_at,
        "finishedAt": started_at,
    }


# ── current_period_bounds ────────────────────────────────────────────────────


def test_period_bounds_mid_month():
    now = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    start, end = current_period_bounds(now)
    assert start == "2026-06-01T00:00:00+00:00"
    assert end == "2026-07-01T00:00:00+00:00"


def test_period_bounds_december_rolls_to_next_year():
    now = datetime(2026, 12, 20, tzinfo=timezone.utc)
    start, end = current_period_bounds(now)
    assert start == "2026-12-01T00:00:00+00:00"
    assert end == "2027-01-01T00:00:00+00:00"


def test_period_bounds_january():
    now = datetime(2026, 1, 5, tzinfo=timezone.utc)
    start, end = current_period_bounds(now)
    assert start == "2026-01-01T00:00:00+00:00"
    assert end == "2026-02-01T00:00:00+00:00"


# ── count_runs_in_period ──────────────────────────────────────────────────────


def test_count_runs_in_period_matches_prefix(tmp_path: Path):
    save_job(tmp_path, _job("j1", "/configs/argyle.yaml", "2026-06-05T00:00:00+00:00"))
    save_job(tmp_path, _job("j2", "/configs/argyle.yaml", "2026-06-10T00:00:00+00:00"))
    save_job(tmp_path, _job("j3", "/configs/other.yaml", "2026-06-12T00:00:00+00:00"))

    count = count_runs_in_period(
        tmp_path, "argyle", "2026-06-01T00:00:00+00:00", "2026-07-01T00:00:00+00:00"
    )
    assert count == 2


def test_count_runs_in_period_excludes_outside_window(tmp_path: Path):
    save_job(tmp_path, _job("j1", "/configs/argyle.yaml", "2026-05-30T00:00:00+00:00"))
    save_job(tmp_path, _job("j2", "/configs/argyle.yaml", "2026-06-05T00:00:00+00:00"))
    save_job(tmp_path, _job("j3", "/configs/argyle.yaml", "2026-07-01T00:00:00+00:00"))

    count = count_runs_in_period(
        tmp_path, "argyle", "2026-06-01T00:00:00+00:00", "2026-07-01T00:00:00+00:00"
    )
    assert count == 1


def test_count_runs_in_period_empty_when_no_match(tmp_path: Path):
    save_job(tmp_path, _job("j1", "/configs/other.yaml", "2026-06-05T00:00:00+00:00"))
    count = count_runs_in_period(
        tmp_path, "argyle", "2026-06-01T00:00:00+00:00", "2026-07-01T00:00:00+00:00"
    )
    assert count == 0


def test_count_runs_in_period_no_jobs_at_all(tmp_path: Path):
    count = count_runs_in_period(
        tmp_path, "argyle", "2026-06-01T00:00:00+00:00", "2026-07-01T00:00:00+00:00"
    )
    assert count == 0


# ── usage_for_workspace ───────────────────────────────────────────────────────


def test_usage_for_workspace_shape(tmp_path: Path):
    now = datetime.now(timezone.utc)
    save_job(tmp_path, _job("j1", "/configs/argyle.yaml", now.isoformat()))
    result = usage_for_workspace(tmp_path, "argyle")
    assert result["workspaceSlug"] == "argyle"
    assert result["runsThisMonth"] == 1
    assert "periodStart" in result and "periodEnd" in result


def test_usage_for_workspace_zero_when_no_runs(tmp_path: Path):
    result = usage_for_workspace(tmp_path, "nonexistent-workspace")
    assert result["runsThisMonth"] == 0
