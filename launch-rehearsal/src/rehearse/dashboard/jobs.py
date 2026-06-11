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

from rehearse.dashboard.job_store import (
    list_jobs as _db_list_jobs,
    save_job as _db_save_job,
    update_job as _db_update_job,
    mark_stale_running as _db_mark_stale,
)

_run_serial_lock = threading.Lock()


def list_jobs(artifacts_root: Path) -> list[dict[str, Any]]:
    return _db_list_jobs(artifacts_root)


def _save_job(artifacts_root: Path, job: dict[str, Any]) -> None:
    _db_save_job(artifacts_root, job)


def _update_job(artifacts_root: Path, job_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    return _db_update_job(artifacts_root, job_id, patch)


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


def enqueue_variant_run(
    artifacts_root: Path,
    *,
    config_a: Path,
    config_b: Path,
    hypothesis: str = "",
    user_goal: str = "",
    output_dir: Path,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Run config A then config B sequentially, then build a comparison report (L3-PRED-06)."""
    config_a = config_a.resolve()
    config_b = config_b.resolve()

    job_id = f"variant_{uuid.uuid4().hex[:8]}"
    job: dict[str, Any] = {
        "id": job_id,
        "type": "variant",
        "configA": str(config_a),
        "configB": str(config_b),
        "hypothesis": hypothesis,
        "userGoal": user_goal,
        "status": "queued",
        "phase": "queued",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "finishedAt": None,
        "runIdA": None,
        "runIdB": None,
        "runId": None,
        "diffNarrative": None,
        "error": None,
    }
    jobs = list_jobs(artifacts_root)
    _save_job(artifacts_root, job)

    rehearse_bin = artifacts_root.parent / ".venv" / "bin" / "rehearse"
    if not rehearse_bin.is_file():
        rehearse_bin = Path("rehearse")

    def _run_one(config_path: Path, label: str) -> str | None:
        """Run a single rehearse config and return run_id or None on failure."""
        cmd = [str(rehearse_bin), "run", "-c", str(config_path), "-o", str(output_dir)]
        if use_llm:
            cmd.append("--llm")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=32400,
                                  env=_load_env(artifacts_root))
            if proc.returncode == 0:
                return parse_run_id_from_cli_output(proc.stdout, proc.stderr)
            raise RuntimeError((proc.stderr or proc.stdout)[-400:])
        except Exception as exc:
            raise RuntimeError(f"{label} run failed: {exc}") from exc

    def _worker() -> None:
        with _run_serial_lock:
            try:
                # Phase A
                _update_job(artifacts_root, job_id, {"status": "running", "phase": "running-A"})
                run_id_a = _run_one(config_a, "Config A")
                _update_job(artifacts_root, job_id, {"runIdA": run_id_a, "phase": "running-B"})

                # Phase B
                run_id_b = _run_one(config_b, "Config B")
                _update_job(artifacts_root, job_id, {"runIdB": run_id_b, "phase": "comparing"})

                # Build diff narrative
                diff_narrative = None
                if run_id_a and run_id_b:
                    try:
                        from rehearse.dashboard.diff import diff_runs
                        diff_data = diff_runs(artifacts_root, run_id_a, run_id_b)
                        diff_narrative = diff_data.get("narrative")
                    except Exception:
                        pass

                _update_job(artifacts_root, job_id, {
                    "status": "done",
                    "phase": "done",
                    "runId": run_id_b,
                    "diffNarrative": diff_narrative,
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as exc:
                _update_job(artifacts_root, job_id, {
                    "status": "failed",
                    "phase": "failed",
                    "error": str(exc),
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                })

    threading.Thread(target=_worker, daemon=True, name=f"variant-{job_id}").start()
    return job


def _load_env(artifacts_root: Path) -> dict[str, str]:
    """Load subprocess env, merging .env if present."""
    import os
    env = dict(os.environ)
    for candidate in (artifacts_root.parent.parent / ".env", artifacts_root.parent / ".env"):
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


def enqueue_cohort_run(
    artifacts_root: Path,
    *,
    config_path: Path,
    n_seeds: int = 3,
    hypothesis: str = "",
    output_dir: Path,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Run the same config N times and aggregate results (L3-PRED-03)."""
    config_path = config_path.resolve()
    n_seeds = max(2, min(n_seeds, 10))

    job_id = f"cohort_{uuid.uuid4().hex[:8]}"
    job: dict[str, Any] = {
        "id": job_id,
        "type": "cohort",
        "config": str(config_path),
        "nSeeds": n_seeds,
        "hypothesis": hypothesis,
        "status": "queued",
        "phase": "queued",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "finishedAt": None,
        "runIds": [],
        "completedSeeds": 0,
        "aggregate": None,
        "error": None,
    }
    jobs = list_jobs(artifacts_root)
    _save_job(artifacts_root, job)

    rehearse_bin = artifacts_root.parent / ".venv" / "bin" / "rehearse"
    if not rehearse_bin.is_file():
        rehearse_bin = Path("rehearse")

    def _run_one_seed(seed_num: int) -> str | None:
        cmd = [str(rehearse_bin), "run", "-c", str(config_path), "-o", str(output_dir)]
        if use_llm:
            cmd.append("--llm")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=32400,
                                  env=_load_env(artifacts_root))
            if proc.returncode == 0:
                return parse_run_id_from_cli_output(proc.stdout, proc.stderr)
            raise RuntimeError((proc.stderr or proc.stdout)[-400:])
        except Exception as exc:
            raise RuntimeError(f"Seed {seed_num} failed: {exc}") from exc

    def _aggregate(run_ids: list[str]) -> dict[str, Any]:
        from rehearse.dashboard.store import load_bundle
        scores: list[int] = []
        all_issues: list[dict[str, Any]] = []
        for rid in run_ids:
            b = load_bundle(artifacts_root, rid)
            if not b:
                continue
            s = b.get("summary") or {}
            if s.get("readiness") is not None:
                scores.append(int(s["readiness"]))
            for iss in (b.get("issues") or [])[:20]:
                all_issues.append({"title": iss.get("title"), "severity": iss.get("severity")})

        if not scores:
            return {"runIds": run_ids, "confidence": "low"}

        mean = sum(scores) / len(scores)
        mn, mx = min(scores), max(scores)
        spread = mx - mn
        confidence = "high" if spread <= 5 else ("medium" if spread <= 15 else "low")

        # Issues that appear in ≥50% of runs
        from collections import Counter
        title_counts = Counter(i["title"] for i in all_issues if i.get("title"))
        threshold = max(1, len(run_ids) // 2)
        recurring = [
            {"title": t, "count": c, "rate": round(c / len(run_ids), 2)}
            for t, c in title_counts.most_common(10)
            if c >= threshold
        ]

        return {
            "runIds": run_ids,
            "nSeeds": len(run_ids),
            "readinessMean": round(mean, 1),
            "readinessMin": mn,
            "readinessMax": mx,
            "spread": spread,
            "confidence": confidence,
            "recurringIssues": recurring,
        }

    def _worker() -> None:
        with _run_serial_lock:
            run_ids: list[str] = []
            errors: list[str] = []
            for i in range(n_seeds):
                _update_job(artifacts_root, job_id, {
                    "status": "running",
                    "phase": f"seed-{i + 1}-of-{n_seeds}",
                    "completedSeeds": i,
                })
                try:
                    rid = _run_one_seed(i + 1)
                    if rid:
                        run_ids.append(rid)
                        current_job = next((j for j in list_jobs(artifacts_root) if j["id"] == job_id), None)
                        existing = (current_job or {}).get("runIds") or []
                        _update_job(artifacts_root, job_id, {"runIds": existing + [rid], "completedSeeds": i + 1})
                except Exception as exc:
                    errors.append(str(exc))

            if len(run_ids) < 2:
                _update_job(artifacts_root, job_id, {
                    "status": "failed",
                    "phase": "failed",
                    "error": "; ".join(errors) or "Too few runs completed",
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                })
                return

            _update_job(artifacts_root, job_id, {"phase": "aggregating"})
            try:
                agg = _aggregate(run_ids)
            except Exception as exc:
                agg = {"runIds": run_ids, "error": str(exc)}

            _update_job(artifacts_root, job_id, {
                "status": "done",
                "phase": "done",
                "runIds": run_ids,
                "aggregate": agg,
                "finishedAt": datetime.now(timezone.utc).isoformat(),
            })

    threading.Thread(target=_worker, daemon=True, name=f"cohort-{job_id}").start()
    return job


def mark_stale_running_jobs(artifacts_root: Path) -> int:
    """On serve startup, mark orphaned running jobs as failed."""
    return _db_mark_stale(artifacts_root)


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
    _save_job(artifacts_root, job)

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

    def _worker() -> None:
        with _run_serial_lock:
            # Pre-assign run_id so the job record has it before the subprocess starts.
            # This lets the frontend send pause/stop signals while the run is live.
            pre_run_id: str | None = None
            if mode == "run" and run_prefix:
                from rehearse.evidence import new_run_id as _new_run_id
                pre_run_id = _new_run_id(run_prefix)
                _update_job(artifacts_root, job_id, {"status": "running", "runId": pre_run_id})
            else:
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
            if pre_run_id:
                cmd.extend(["--run-id", pre_run_id])
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=32400,
                    env=_load_env(artifacts_root),
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
