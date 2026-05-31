"""Background job queue for dashboard-triggered CLI runs."""

from __future__ import annotations

import json
import re
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_jobs_file_lock = threading.Lock()
_run_serial_lock = threading.Lock()


def _jobs_path(artifacts_root: Path) -> Path:
    return artifacts_root / "jobs.json"


def list_jobs(artifacts_root: Path) -> list[dict[str, Any]]:
    path = _jobs_path(artifacts_root)
    if not path.is_file():
        return []
    with _jobs_file_lock:
        raw = path.read_text()
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # Concurrent writers can corrupt the file — repair from first valid array.
        backup = path.with_suffix(".json.bak")
        backup.write_text(raw)
        start = raw.find("[")
        if start < 0:
            return []
        end = raw.find("]", start)
        while end >= 0:
            try:
                data = json.loads(raw[start : end + 1])
                if isinstance(data, list):
                    _save_jobs_unlocked(artifacts_root, data)
                    return data
            except json.JSONDecodeError:
                pass
            end = raw.find("]", end + 1)
        return []


def _save_jobs_unlocked(artifacts_root: Path, jobs: list[dict[str, Any]]) -> None:
    path = _jobs_path(artifacts_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jobs[-50:], indent=2))


def _save_jobs(artifacts_root: Path, jobs: list[dict[str, Any]]) -> None:
    with _jobs_file_lock:
        _save_jobs_unlocked(artifacts_root, jobs)


def _load_jobs_unlocked(artifacts_root: Path) -> list[dict[str, Any]]:
    path = _jobs_path(artifacts_root)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _update_job(artifacts_root: Path, job_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    with _jobs_file_lock:
        jobs = _load_jobs_unlocked(artifacts_root)
        j = next((x for x in jobs if x["id"] == job_id), None)
        if not j:
            return None
        j.update(patch)
        _save_jobs_unlocked(artifacts_root, jobs)
        return j


def parse_run_id_from_cli_output(stdout: str, stderr: str = "") -> str | None:
    """Extract run_id from rehearse run JSON stdout (multi-line indent=2)."""
    text = (stdout or "").strip()
    if not text:
        text = (stderr or "").strip()
    if not text:
        return None

    start = text.find("{")
    if start >= 0:
        try:
            blob = json.loads(text[start:])
            rid = blob.get("run_id")
            if isinstance(rid, str) and rid:
                return rid
        except json.JSONDecodeError:
            pass

    match = re.search(r'"run_id"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)

    for line in reversed(text.splitlines()):
        if '"run_id"' not in line:
            continue
        try:
            blob = json.loads(line.strip().rstrip(","))
            rid = blob.get("run_id")
            if isinstance(rid, str) and rid:
                return rid
        except json.JSONDecodeError:
            match = re.search(r'"run_id"\s*:\s*"([^"]+)"', line)
            if match:
                return match.group(1)
    return None


def _latest_run_id_for_prefix(artifacts_root: Path, prefix: str) -> str | None:
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir():
        return None
    candidates = sorted(
        runs_dir.glob(f"{prefix}-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    try:
        return json.loads(candidates[0].read_text()).get("run_id")
    except (json.JSONDecodeError, OSError):
        return candidates[0].stem


def _has_active_job(jobs: list[dict[str, Any]], config_path: Path) -> bool:
    cfg = str(config_path.resolve())
    for j in jobs:
        if j.get("status") not in ("queued", "running"):
            continue
        if str(Path(j.get("config", "")).resolve()) == cfg:
            return True
    return False


def mark_stale_running_jobs(artifacts_root: Path) -> int:
    """On serve startup, mark orphaned running jobs as failed."""
    jobs = list_jobs(artifacts_root)
    changed = 0
    now = datetime.now(timezone.utc).isoformat()
    for j in jobs:
        if j.get("status") == "running":
            j["status"] = "failed"
            j["error"] = "Interrupted — rehearse serve restarted"
            j["finishedAt"] = now
            changed += 1
    if changed:
        _save_jobs(artifacts_root, jobs)
    return changed


def enqueue_run(
    artifacts_root: Path,
    *,
    config_path: Path,
    output_dir: Path,
    mode: str = "run",
    use_llm: bool = False,
    no_crawl: bool = False,
) -> dict[str, Any]:
    config_path = config_path.resolve()
    jobs = list_jobs(artifacts_root)
    if _has_active_job(jobs, config_path):
        existing = next(
            (
                x
                for x in jobs
                if x.get("status") in ("queued", "running")
                and str(Path(x.get("config", "")).resolve()) == str(config_path)
            ),
            None,
        )
        if existing:
            existing["deduped"] = True
            return existing

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
    jobs.insert(0, job)
    _save_jobs(artifacts_root, jobs)

    rehearse_bin = artifacts_root.parent / ".venv" / "bin" / "rehearse"
    if not rehearse_bin.is_file():
        rehearse_bin = Path("rehearse")

    run_prefix: str | None = None
    try:
        import yaml

        cfg_data = yaml.safe_load(config_path.read_text()) or {}
        run_prefix = (cfg_data.get("run") or {}).get("run_id_prefix")
    except Exception:
        pass

    def _load_env_for_subprocess() -> dict[str, str]:
        """Pass through DEEPSEEK / REHEARSE LLM keys from repo .env if present."""
        import os

        env = dict(os.environ)
        for candidate in (
            artifacts_root.parent.parent / ".env",
            artifacts_root.parent / ".env",
        ):
            if not candidate.is_file():
                continue
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in env:
                    env[key] = val
            break
        return env

    def _worker() -> None:
        with _run_serial_lock:
            _update_job(artifacts_root, job_id, {"status": "running"})
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
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600,
                    env=_load_env_for_subprocess(),
                )
                if proc.returncode == 0:
                    run_id = parse_run_id_from_cli_output(proc.stdout, proc.stderr)
                    if not run_id and run_prefix and mode == "run":
                        run_id = _latest_run_id_for_prefix(output_dir, run_prefix)
                    _update_job(
                        artifacts_root,
                        job_id,
                        {
                            "status": "done",
                            "runId": run_id,
                            "finishedAt": datetime.now(timezone.utc).isoformat(),
                            "error": None,
                        },
                    )
                else:
                    _update_job(
                        artifacts_root,
                        job_id,
                        {
                            "status": "failed",
                            "error": (proc.stderr or proc.stdout)[-500:],
                            "finishedAt": datetime.now(timezone.utc).isoformat(),
                        },
                    )
            except Exception as exc:
                _update_job(
                    artifacts_root,
                    job_id,
                    {
                        "status": "failed",
                        "error": str(exc),
                        "finishedAt": datetime.now(timezone.utc).isoformat(),
                    },
                )

    threading.Thread(target=_worker, daemon=True, name=f"rehearse-{job_id}").start()
    return job
