"""Job queue — locking, dedupe, stale recovery."""

import json
import threading
from pathlib import Path

from rehearse.dashboard.jobs import (
    _save_jobs,
    list_jobs,
    mark_stale_running_jobs,
    parse_run_id_from_cli_output,
)


def test_parse_run_id_multiline_json():
    stdout = '{\n  "run_id": "lr-self-20260531-120000",\n  "outcome": "complete"\n}\n'
    assert parse_run_id_from_cli_output(stdout) == "lr-self-20260531-120000"


def test_list_jobs_recovers_truncated_concat(tmp_path: Path):
    path = tmp_path / "jobs.json"
    good = [{"id": "job_a", "status": "done", "config": "/x.yaml"}]
    path.write_text(json.dumps(good) + "\n" + json.dumps([{"id": "job_b"}]))
    jobs = list_jobs(tmp_path)
    assert len(jobs) >= 1
    assert jobs[0]["id"] == "job_a"


def test_mark_stale_running_jobs(tmp_path: Path):
    _save_jobs(
        tmp_path,
        [
            {"id": "job_1", "status": "running", "config": "/a.yaml"},
            {"id": "job_2", "status": "done", "config": "/b.yaml"},
        ],
    )
    n = mark_stale_running_jobs(tmp_path)
    assert n == 1
    jobs = list_jobs(tmp_path)
    assert jobs[0]["status"] == "failed"
    assert "restarted" in (jobs[0].get("error") or "").lower()


def test_concurrent_save_no_extra_data(tmp_path: Path):
    jobs = [{"id": f"job_{i}", "status": "queued", "config": "/c.yaml"} for i in range(20)]

    def writer():
        for _ in range(10):
            j = list_jobs(tmp_path)
            j.insert(0, {"id": "job_x", "status": "queued", "config": "/c.yaml"})
            _save_jobs(tmp_path, j)

    threads = [threading.Thread(target=writer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    data = json.loads((tmp_path / "jobs.json").read_text())
    assert isinstance(data, list)
