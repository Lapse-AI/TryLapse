"""Daily T+7 outcome-follow-up dispatch — the piece that made calibration
data theoretical rather than real.

outcome_store.py could record an outcome, and follow_up_due() could
compute which completed runs were 7+ days old with no outcome recorded,
but nothing ever prompted a user to actually record one. Every "vs.
industry benchmark" comparison stayed permanently hand-estimated
(lr-beta-v1) because the real-outcome sample size never grew above zero.
This module is the trigger: resolve each due run to its workspace owner's
email and send the reminder, once per run (tracked via
outcome_store.mark_follow_up_sent so a run stuck unrecorded doesn't
re-email every day).
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

_CHECK_INTERVAL_SECONDS = 24 * 60 * 60  # once a day is enough for a 7-day window


def _resolve_owner_email(artifacts_root: Path, config_path_str: str) -> str | None:
    """config path -> workspace slug (the auto-generated stem convention
    used throughout the dashboard) -> workspace owner's account email."""
    from rehearse.dashboard.auth_store import get_user
    from rehearse.dashboard.workspace_store import get_workspace_by_slug

    slug = Path(config_path_str).stem
    ws = get_workspace_by_slug(artifacts_root, slug)
    if not ws:
        return None
    owner = get_user(artifacts_root, ws["ownerId"])
    return owner["email"] if owner else None


def run_follow_up_check(artifacts_root: Path, *, dashboard_base_url: str = "") -> int:
    """Send one reminder email per completed run that's 7+ days old with no
    outcome recorded and hasn't already gotten a reminder. Returns count sent.

    Never raises — a notification failure must never take down the
    scheduler thread or the server it runs alongside.
    """
    from rehearse.dashboard.job_store import list_jobs
    from rehearse.dashboard.notifications import send_outcome_follow_up_email
    from rehearse.dashboard.outcome_store import follow_up_due, mark_follow_up_sent, was_follow_up_sent

    sent = 0
    try:
        due = follow_up_due(artifacts_root)
        jobs_by_run = {j.get("runId") or j.get("id"): j for j in list_jobs(artifacts_root, limit=200)}
        for item in due:
            run_id = item["runId"]
            if was_follow_up_sent(artifacts_root, run_id):
                continue
            job = jobs_by_run.get(run_id)
            if not job:
                continue
            config_path = job.get("config") or ""
            email = _resolve_owner_email(artifacts_root, config_path)
            if not email:
                continue
            target_url = Path(config_path).stem  # best-effort label if run summary isn't loaded
            dashboard_url = f"{dashboard_base_url.rstrip('/')}/runs/{run_id}" if dashboard_base_url else run_id
            try:
                send_outcome_follow_up_email(email, run_id, target_url, dashboard_url)
                mark_follow_up_sent(artifacts_root, run_id)
                sent += 1
            except Exception:
                continue
    except Exception:
        pass
    return sent


def start_background_scheduler(artifacts_root: Path, *, dashboard_base_url: str = "") -> threading.Thread:
    """Start a daemon thread that runs the T+7 check once daily for the
    lifetime of the dashboard server process."""

    def _loop() -> None:
        while True:
            run_follow_up_check(artifacts_root, dashboard_base_url=dashboard_base_url)
            time.sleep(_CHECK_INTERVAL_SECONDS)

    thread = threading.Thread(target=_loop, daemon=True, name="outcome-follow-up-scheduler")
    thread.start()
    return thread
