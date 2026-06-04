"""Job queue — SQLite store, dedupe, stale recovery."""

import threading
from pathlib import Path

from rehearse.dashboard.job_store import save_job, list_jobs as db_list_jobs, update_job
from rehearse.dashboard.jobs import (
    list_jobs,
    mark_stale_running_jobs,
    parse_run_id_from_cli_output,
)


def test_parse_run_id_multiline_json():
    stdout = '{\n  "run_id": "lr-self-20260531-120000",\n  "outcome": "complete"\n}\n'
    assert parse_run_id_from_cli_output(stdout) == "lr-self-20260531-120000"


def test_list_jobs_empty(tmp_path: Path):
    assert list_jobs(tmp_path) == []


def test_save_and_list_job(tmp_path: Path):
    job = {"id": "job_a", "status": "queued", "config": "/x.yaml", "startedAt": "2026-01-01T00:00:00Z", "finishedAt": None}
    save_job(tmp_path, job)
    jobs = list_jobs(tmp_path)
    assert len(jobs) == 1
    assert jobs[0]["id"] == "job_a"
    assert jobs[0]["status"] == "queued"


def test_update_job(tmp_path: Path):
    job = {"id": "job_b", "status": "running", "config": "/y.yaml", "startedAt": "2026-01-01T00:00:00Z", "finishedAt": None}
    save_job(tmp_path, job)
    updated = update_job(tmp_path, "job_b", {"status": "done", "runId": "lr-self-001", "finishedAt": "2026-01-01T00:01:00Z"})
    assert updated is not None
    assert updated["status"] == "done"
    assert updated["runId"] == "lr-self-001"
    jobs = list_jobs(tmp_path)
    assert jobs[0]["status"] == "done"


def test_mark_stale_running_jobs(tmp_path: Path):
    for i, status in enumerate(["running", "queued", "done"]):
        save_job(tmp_path, {"id": f"job_{i}", "status": status, "config": "/a.yaml",
                            "startedAt": "2026-01-01T00:00:00Z", "finishedAt": None})
    n = mark_stale_running_jobs(tmp_path)
    assert n == 2  # running + queued both marked failed
    jobs = list_jobs(tmp_path)
    failed = [j for j in jobs if j["status"] == "failed"]
    assert len(failed) == 2


def test_concurrent_writes_no_corruption(tmp_path: Path):
    """SQLite WAL mode handles concurrent writes without data corruption."""
    import random, time

    def writer(i: int):
        for k in range(5):
            job = {
                "id": f"job_{i}_{k}",
                "status": "queued",
                "config": "/c.yaml",
                "startedAt": "2026-01-01T00:00:00Z",
                "finishedAt": None,
            }
            save_job(tmp_path, job)
            time.sleep(random.uniform(0, 0.01))

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    jobs = list_jobs(tmp_path)
    assert len(jobs) == 20
    ids = {j["id"] for j in jobs}
    assert len(ids) == 20  # no duplicates


def test_update_nonexistent_job_returns_none(tmp_path: Path):
    result = update_job(tmp_path, "does_not_exist", {"status": "done"})
    assert result is None
