"""Launch outcome store — records post-launch feedback against a run_id.

Schema (per run):
  {
    "runId": "argyle-20260617-120000",
    "recordedAt": "2026-06-24T12:00:00Z",
    "launchSucceeded": true | false | null,
    "launchDate": "2026-06-17",
    "missedIssues": ["title of issue we missed"],
    "falsePositives": ["title of P1 we flagged that wasn't real"],
    "notes": "free text from the team",
    "reportedBy": "user@example.com",
  }

All outcomes are stored in outcomes.json under artifacts_root.
This file feeds the calibration loop that eventually makes scores empirical.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_FILENAME = "outcomes.json"
_REMINDERS_FILENAME = "outcome_reminders_sent.json"

_ALLOWED_KEYS = {
    "runId",
    "launchSucceeded",
    "launchDate",
    "missedIssues",
    "falsePositives",
    "notes",
    "reportedBy",
}


def _outcomes_path(artifacts_root: Path) -> Path:
    return artifacts_root / _FILENAME


def _load(artifacts_root: Path) -> list[dict[str, Any]]:
    p = _outcomes_path(artifacts_root)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(artifacts_root: Path, outcomes: list[dict[str, Any]]) -> None:
    _outcomes_path(artifacts_root).write_text(json.dumps(outcomes, indent=2))


def record_outcome(artifacts_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Upsert a launch outcome for a run. Returns the saved record."""
    run_id = str(payload.get("runId") or "").strip()
    if not run_id:
        raise ValueError("runId is required")

    record: dict[str, Any] = {k: v for k, v in payload.items() if k in _ALLOWED_KEYS}
    record["runId"] = run_id
    record["recordedAt"] = datetime.now(timezone.utc).isoformat()

    outcomes = _load(artifacts_root)
    # Replace existing record for the same runId
    outcomes = [o for o in outcomes if o.get("runId") != run_id]
    outcomes.append(record)
    _save(artifacts_root, outcomes)
    return record


def get_outcome(artifacts_root: Path, run_id: str) -> dict[str, Any] | None:
    """Return the outcome record for a run, or None."""
    outcomes = _load(artifacts_root)
    for o in outcomes:
        if o.get("runId") == run_id:
            return o
    return None


def list_outcomes(artifacts_root: Path) -> list[dict[str, Any]]:
    """Return all recorded outcomes, newest first."""
    return sorted(_load(artifacts_root), key=lambda o: o.get("recordedAt", ""), reverse=True)


def follow_up_due(artifacts_root: Path, now: datetime | None = None) -> list[dict[str, Any]]:
    """Return run IDs from the job store that have no outcome and are 7+ days old."""
    try:
        from rehearse.dashboard.job_store import list_jobs
        now = now or datetime.now(timezone.utc)
        recorded = {o["runId"] for o in _load(artifacts_root)}
        due = []
        for job in list_jobs(artifacts_root, limit=200):
            if job.get("status") not in ("complete", "done"):
                continue
            finished = job.get("finishedAt") or job.get("startedAt") or ""
            if not finished:
                continue
            try:
                from datetime import datetime as _dt
                ft = _dt.fromisoformat(finished.replace("Z", "+00:00"))
                age_days = (now - ft).total_seconds() / 86400
            except Exception:
                continue
            if age_days >= 7 and job["id"] not in recorded:
                due.append({"runId": job["id"], "finishedAt": finished, "ageDays": round(age_days, 1)})
        return due
    except Exception:
        return []


def _reminders_path(artifacts_root: Path) -> Path:
    return artifacts_root / _REMINDERS_FILENAME


def _load_reminders_sent(artifacts_root: Path) -> set[str]:
    p = _reminders_path(artifacts_root)
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text())
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def was_follow_up_sent(artifacts_root: Path, run_id: str) -> bool:
    return run_id in _load_reminders_sent(artifacts_root)


def mark_follow_up_sent(artifacts_root: Path, run_id: str) -> None:
    """Record that a T+7 outcome-reminder email was sent for this run, so the
    daily scheduler doesn't re-send one every day a run stays unrecorded."""
    sent = _load_reminders_sent(artifacts_root)
    sent.add(run_id)
    _reminders_path(artifacts_root).write_text(json.dumps(sorted(sent), indent=2))
