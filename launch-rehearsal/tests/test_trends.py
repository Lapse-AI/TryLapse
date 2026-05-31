"""Trends API aggregation."""

import json
from pathlib import Path

from rehearse.dashboard.store import get_trends


def test_get_trends_issue_recurrence(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    for run_id, title in (
        ("run-a", "Missing labels"),
        ("run-b", "Missing labels"),
        ("run-c", "New only issue"),
    ):
        runs.joinpath(f"{run_id}.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "target_url": "http://example.com",
                    "product_name": "Test",
                    "started_at": "2026-05-31T00:00:00+00:00",
                    "finished_at": "2026-05-31T00:01:00+00:00",
                    "duration_ms": 1000,
                    "steps": [],
                    "outcome": "complete",
                }
            )
        )
        analysis = {
            "summary": {
                "id": run_id,
                "readiness": 50,
                "readinessBand": "Red",
                "pages": 1,
                "startedAt": "2026-05-31",
            },
            "issues": (
                [{"id": "I1", "title": title, "severity": "P2"}]
                if run_id != "run-c"
                else [{"id": "I2", "title": "New only issue", "severity": "P2"}]
            ),
            "steps": [],
        }
        (tmp_path / "analysis").mkdir(exist_ok=True)
        (tmp_path / "analysis" / f"{run_id}.json").write_text(json.dumps(analysis))

    trends = get_trends(tmp_path)
    assert trends["readiness"]
    names = {r["name"] for r in trends["issueRecurrence"]}
    assert "Missing labels" in names
    missing = next(r for r in trends["issueRecurrence"] if r["name"] == "Missing labels")
    assert missing["runs"] >= 2
