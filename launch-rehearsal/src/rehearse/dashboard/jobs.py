"""Background job queue for dashboard-triggered CLI runs."""

from __future__ import annotations

import json
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _jobs_path(artifacts_root: Path) -> Path:
    return artifacts_root / "jobs.json"


def list_jobs(artifacts_root: Path) -> list[dict[str, Any]]:
    path = _jobs_path(artifacts_root)
    if not path.is_file():
        return []
    return json.loads(path.read_text())


def _save_jobs(artifacts_root: Path, jobs: list[dict[str, Any]]) -> None:
    path = _jobs_path(artifacts_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs[-50:], indent=2))


def enqueue_run(
    artifacts_root: Path,
    *,
    config_path: Path,
    output_dir: Path,
    mode: str = "run",
    use_llm: bool = False,
    no_crawl: bool = False,
) -> dict[str, Any]:
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job = {
        "id": job_id,
        "mode": mode,
        "config": str(config_path),
        "status": "queued",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "finishedAt": None,
        "runId": None,
        "error": None,
    }
    jobs = list_jobs(artifacts_root)
    jobs.insert(0, job)
    _save_jobs(artifacts_root, jobs)

    rehearse_bin = artifacts_root.parent / ".venv" / "bin" / "rehearse"
    if not rehearse_bin.is_file():
        rehearse_bin = Path("rehearse")

    def _worker() -> None:
        jobs = list_jobs(artifacts_root)
        j = next((x for x in jobs if x["id"] == job_id), None)
        if not j:
            return
        j["status"] = "running"
        _save_jobs(artifacts_root, jobs)
        cmd = [
            str(rehearse_bin),
            "crawl" if mode == "crawl" else "run",
            "-c",
            str(config_path),
            "-o",
            str(output_dir),
        ]
        if mode == "run" and use_llm:
            cmd.append("--llm")
        if mode == "run" and no_crawl:
            cmd.append("--no-crawl")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            jobs = list_jobs(artifacts_root)
            j = next((x for x in jobs if x["id"] == job_id), None)
            if not j:
                return
            if proc.returncode == 0:
                j["status"] = "done"
                # try parse run_id from json output last line
                for line in reversed(proc.stdout.splitlines()):
                    if '"run_id"' in line:
                        try:
                            blob = json.loads(line.strip())
                            j["runId"] = blob.get("run_id")
                        except json.JSONDecodeError:
                            pass
                        break
            else:
                j["status"] = "failed"
                j["error"] = (proc.stderr or proc.stdout)[-500:]
            j["finishedAt"] = datetime.now(timezone.utc).isoformat()
            _save_jobs(artifacts_root, jobs)
        except Exception as exc:
            jobs = list_jobs(artifacts_root)
            j = next((x for x in jobs if x["id"] == job_id), None)
            if j:
                j["status"] = "failed"
                j["error"] = str(exc)
                j["finishedAt"] = datetime.now(timezone.utc).isoformat()
                _save_jobs(artifacts_root, jobs)

    threading.Thread(target=_worker, daemon=True, name=f"rehearse-{job_id}").start()
    return job
