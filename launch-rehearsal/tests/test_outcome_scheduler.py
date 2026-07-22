"""T+7 outcome-follow-up dispatch.

follow_up_due() could already compute which completed runs were 7+ days
old with no outcome recorded, but nothing ever prompted a user to record
one — the calibration loop (benchmark_recalibration.py's MIN_SAMPLES=5)
never accrued real data because the sample size never grew above zero.
This is the trigger: resolve each due run to its workspace owner's email
and send a reminder, exactly once per run.
"""
from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import patch

from rehearse.dashboard.auth_store import create_user, ensure_users_table
from rehearse.dashboard.job_store import save_job
from rehearse.dashboard.outcome_scheduler import run_follow_up_check
from rehearse.dashboard.outcome_store import (
    mark_follow_up_sent,
    record_outcome,
    was_follow_up_sent,
)
from rehearse.dashboard.workspace_store import (
    create_workspace,
    ensure_membership_tables,
    ensure_workspaces_table,
)


def _setup_workspace(tmp_path: Path, slug_stem: str = "acme") -> dict:
    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)
    owner = create_user(tmp_path, email="owner@acme.com", password="ownerpass123", name="Owner")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name=slug_stem.title(),
        target_url=f"https://{slug_stem}.example.com", product_name="P", team_role="founder",
    )
    return ws


def _old_completed_job(tmp_path: Path, run_id: str, config_path: str, days_old: int = 8) -> None:
    finished = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_old)).isoformat()
    save_job(tmp_path, {
        "id": run_id,
        "runId": run_id,
        "status": "done",
        "config": config_path,
        "startedAt": finished,
        "finishedAt": finished,
    })


def test_sends_reminder_for_due_run_with_resolvable_owner(tmp_path: Path):
    ws = _setup_workspace(tmp_path)
    _old_completed_job(tmp_path, "run-1", ws["configPath"])

    with patch("rehearse.dashboard.notifications._send_email") as mock_send:
        mock_send.return_value = True
        sent_count = run_follow_up_check(tmp_path)

    assert sent_count == 1
    mock_send.assert_called_once()
    assert mock_send.call_args.args[0] == "owner@acme.com"
    assert was_follow_up_sent(tmp_path, "run-1")


def test_does_not_resend_after_already_sent(tmp_path: Path):
    ws = _setup_workspace(tmp_path)
    _old_completed_job(tmp_path, "run-2", ws["configPath"])
    mark_follow_up_sent(tmp_path, "run-2")

    with patch("rehearse.dashboard.notifications._send_email") as mock_send:
        sent_count = run_follow_up_check(tmp_path)

    assert sent_count == 0
    mock_send.assert_not_called()


def test_skips_run_with_recorded_outcome(tmp_path: Path):
    ws = _setup_workspace(tmp_path)
    _old_completed_job(tmp_path, "run-3", ws["configPath"])
    record_outcome(tmp_path, {"runId": "run-3", "launchSucceeded": True})

    with patch("rehearse.dashboard.notifications._send_email") as mock_send:
        sent_count = run_follow_up_check(tmp_path)

    assert sent_count == 0
    mock_send.assert_not_called()


def test_skips_run_younger_than_seven_days(tmp_path: Path):
    ws = _setup_workspace(tmp_path)
    _old_completed_job(tmp_path, "run-4", ws["configPath"], days_old=2)

    with patch("rehearse.dashboard.notifications._send_email") as mock_send:
        sent_count = run_follow_up_check(tmp_path)

    assert sent_count == 0
    mock_send.assert_not_called()


def test_skips_run_with_no_matching_workspace(tmp_path: Path):
    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)
    _old_completed_job(tmp_path, "run-5", "/data/artifacts/configs/no-such-workspace.yaml")

    with patch("rehearse.dashboard.notifications._send_email") as mock_send:
        sent_count = run_follow_up_check(tmp_path)

    assert sent_count == 0
    mock_send.assert_not_called()


def test_never_raises_on_internal_error(tmp_path: Path):
    """The scheduler runs on a background thread for the server's lifetime —
    an exception here must never crash it."""
    ws = _setup_workspace(tmp_path)
    _old_completed_job(tmp_path, "run-6", ws["configPath"])

    with patch("rehearse.dashboard.notifications._send_email", side_effect=Exception("smtp down")):
        sent_count = run_follow_up_check(tmp_path)  # must not raise

    assert sent_count == 0
    assert not was_follow_up_sent(tmp_path, "run-6")  # not marked sent since it wasn't
