"""SQLite-backed job store — replaces the single-file jobs.json (P3 infra).

WAL mode + connection-per-thread gives safe concurrent reads and serialised
writes without an external process.  The JSON blob column preserves full
backward compatibility with the dict-based job format everywhere else.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_local = threading.local()
_db_lock = threading.Lock()


def _db_path(artifacts_root: Path) -> Path:
    return artifacts_root / "jobs.db"


def _connect(artifacts_root: Path) -> sqlite3.Connection:
    """Return a per-thread connection, creating the DB + schema if needed."""
    if not hasattr(_local, "conns"):
        _local.conns = {}
    key = str(artifacts_root)
    if key not in _local.conns:
        path = _db_path(artifacts_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), check_same_thread=False, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'queued',
                job_type    TEXT NOT NULL DEFAULT 'run',
                started_at  TEXT,
                finished_at TEXT,
                data        TEXT NOT NULL DEFAULT '{}'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_started ON jobs(started_at DESC)")
        conn.commit()
        _local.conns[key] = conn
    return _local.conns[key]


def _row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    data = json.loads(row["data"])
    data["id"] = row["id"]
    data["status"] = row["status"]
    data["startedAt"] = row["started_at"]
    data["finishedAt"] = row["finished_at"]
    return data


def list_jobs(
    artifacts_root: Path,
    limit: int = 50,
    config_prefix: str | None = None,
) -> list[dict[str, Any]]:
    """Return up to `limit` jobs, newest first.

    config_prefix
        When supplied, only jobs whose stored ``config`` path stem starts with
        this prefix are returned.  This is how workspace-scoped filtering works:
        the caller derives the prefix from the workspace's active config filename
        (e.g. ``faculty-dashboard-eight-vercel-app``) and passes it here so the
        SQLite WHERE clause does the filtering rather than the client.

        We push the filter into SQLite via ``json_extract`` so we scan only the
        rows we need even as the jobs table grows.
    """
    conn = _connect(artifacts_root)
    conn.row_factory = sqlite3.Row

    if config_prefix:
        # json_extract pulls the ``config`` field from the JSON blob column.
        # We match jobs whose config path contains the prefix anywhere in the
        # filename stem (handles both absolute paths and relative ones).
        # INSTR is case-sensitive on SQLite by default which is fine since
        # config file names are always lowercase slugs.
        rows = conn.execute(
            """SELECT * FROM jobs
               WHERE json_extract(data, '$.config') LIKE ?
               OR json_extract(data, '$.runId') LIKE ?
               ORDER BY started_at DESC LIMIT ?""",
            (f"%{config_prefix}%", f"{config_prefix}%", limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()

    return [_row_to_job(r) for r in rows]


def save_job(artifacts_root: Path, job: dict[str, Any]) -> None:
    """Insert or replace a job record."""
    conn = _connect(artifacts_root)
    blob = json.dumps({k: v for k, v in job.items() if k not in ("id", "status", "startedAt", "finishedAt")})
    with _db_lock:
        conn.execute(
            """INSERT INTO jobs (id, status, job_type, started_at, finished_at, data)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 status=excluded.status,
                 finished_at=excluded.finished_at,
                 data=excluded.data""",
            (
                job["id"],
                job.get("status", "queued"),
                job.get("type", job.get("mode", "run")),
                job.get("startedAt"),
                job.get("finishedAt"),
                blob,
            ),
        )
        conn.commit()


def update_job(artifacts_root: Path, job_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    """Apply patch fields to an existing job and return the updated record."""
    conn = _connect(artifacts_root)
    conn.row_factory = sqlite3.Row
    with _db_lock:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        job = _row_to_job(row)
        job.update(patch)
        blob = json.dumps({k: v for k, v in job.items() if k not in ("id", "status", "startedAt", "finishedAt")})
        conn.execute(
            "UPDATE jobs SET status=?, finished_at=?, data=? WHERE id=?",
            (job.get("status", "queued"), job.get("finishedAt"), blob, job_id),
        )
        conn.commit()
    return job


def mark_stale_running(artifacts_root: Path) -> int:
    """Mark any jobs stuck in 'running' as failed (called on serve startup)."""
    conn = _connect(artifacts_root)
    now = datetime.now(timezone.utc).isoformat()
    with _db_lock:
        cur = conn.execute(
            "UPDATE jobs SET status='failed', finished_at=?, "
            "data=json_patch(data, '{\"error\":\"Interrupted — rehearse serve restarted\"}') "
            "WHERE status IN ('running','queued')",
            (now,),
        )
        conn.commit()
    return cur.rowcount


def migrate_from_json(artifacts_root: Path) -> int:
    """One-time migration: import existing jobs.json into SQLite if DB is empty."""
    json_path = artifacts_root / "jobs.json"
    if not json_path.is_file():
        return 0
    conn = _connect(artifacts_root)
    existing = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if existing > 0:
        return 0  # already migrated
    try:
        jobs = json.loads(json_path.read_text())
        if not isinstance(jobs, list):
            return 0
        for job in jobs:
            save_job(artifacts_root, job)
        # Rename old file so we don't migrate twice
        json_path.rename(json_path.with_suffix(".json.migrated"))
        return len(jobs)
    except Exception:
        return 0
