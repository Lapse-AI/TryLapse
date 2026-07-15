"""Job store — SQLite (local dev) or PostgreSQL (DATABASE_URL set).

SQLite backend: WAL mode + per-thread connections, a global write lock.
PostgreSQL backend: ThreadedConnectionPool, activated when DATABASE_URL is set.

All public functions share identical signatures so callers need no changes.
The `artifacts_root` Path argument is used by SQLite only (to locate jobs.db);
the PostgreSQL backend ignores it and uses DATABASE_URL.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── backend selection ────────────────────────────────────────────────────────

_DATABASE_URL: str | None = os.environ.get("DATABASE_URL")
_USE_POSTGRES = bool(_DATABASE_URL)

# ── PostgreSQL connection pool (lazy init) ───────────────────────────────────

_pg_pool: Any = None
_pg_pool_lock = threading.Lock()


def _get_pg_pool():
    global _pg_pool
    if _pg_pool is not None:
        return _pg_pool
    with _pg_pool_lock:
        if _pg_pool is not None:
            return _pg_pool
        try:
            import psycopg2.pool
        except ImportError as e:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg2-binary is not installed. "
                "Run: pip install 'launch-rehearsal[postgres]'"
            ) from e
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=_DATABASE_URL,
        )
        _pg_ensure_schema(_pg_pool)
    return _pg_pool


def _pg_ensure_schema(pool) -> None:
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id          TEXT PRIMARY KEY,
                        status      TEXT NOT NULL DEFAULT 'queued',
                        job_type    TEXT NOT NULL DEFAULT 'run',
                        started_at  TEXT,
                        finished_at TEXT,
                        data        JSONB NOT NULL DEFAULT '{}'::jsonb
                    )
                """)
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_jobs_started "
                    "ON jobs(started_at DESC NULLS LAST)"
                )
    finally:
        pool.putconn(conn)


# ── PostgreSQL helpers ───────────────────────────────────────────────────────

def _pg_row_to_job(row: tuple) -> dict[str, Any]:
    id_, status, started_at, finished_at, data = row
    if isinstance(data, str):
        data = json.loads(data)
    data = dict(data)
    data["id"] = id_
    data["status"] = status
    data["startedAt"] = started_at
    data["finishedAt"] = finished_at
    return data


def _list_jobs_pg(limit: int, config_prefix: str | None) -> list[dict[str, Any]]:
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            if config_prefix:
                cur.execute(
                    """SELECT id, status, started_at, finished_at, data FROM jobs
                       WHERE data->>'config' LIKE %s
                          OR data->>'runId' LIKE %s
                       ORDER BY started_at DESC NULLS LAST LIMIT %s""",
                    (f"%{config_prefix}%", f"{config_prefix}%", limit),
                )
            else:
                cur.execute(
                    "SELECT id, status, started_at, finished_at, data "
                    "FROM jobs ORDER BY started_at DESC NULLS LAST LIMIT %s",
                    (limit,),
                )
            return [_pg_row_to_job(r) for r in cur.fetchall()]
    finally:
        pool.putconn(conn)


def _save_job_pg(job: dict[str, Any]) -> None:
    pool = _get_pg_pool()
    data = {k: v for k, v in job.items() if k not in ("id", "status", "startedAt", "finishedAt")}
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO jobs (id, status, job_type, started_at, finished_at, data)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET
                         status      = EXCLUDED.status,
                         finished_at = EXCLUDED.finished_at,
                         data        = EXCLUDED.data""",
                    (
                        job["id"],
                        job.get("status", "queued"),
                        job.get("type", job.get("mode", "run")),
                        job.get("startedAt"),
                        job.get("finishedAt"),
                        json.dumps(data),
                    ),
                )
    finally:
        pool.putconn(conn)


def _update_job_pg(job_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, status, started_at, finished_at, data FROM jobs WHERE id=%s",
                    (job_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                job = _pg_row_to_job(row)
                job.update(patch)
                data = {k: v for k, v in job.items() if k not in ("id", "status", "startedAt", "finishedAt")}
                cur.execute(
                    "UPDATE jobs SET status=%s, finished_at=%s, data=%s WHERE id=%s",
                    (job.get("status", "queued"), job.get("finishedAt"), json.dumps(data), job_id),
                )
        return job
    finally:
        pool.putconn(conn)


def _mark_stale_running_pg() -> int:
    pool = _get_pg_pool()
    now = datetime.now(timezone.utc).isoformat()
    conn = pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE jobs
                       SET status='failed',
                           finished_at=%s,
                           data=data || '{"error":"Interrupted — rehearse serve restarted"}'::jsonb
                       WHERE status IN ('running','queued')""",
                    (now,),
                )
                return cur.rowcount
    finally:
        pool.putconn(conn)


# ── SQLite backend (unchanged logic) ────────────────────────────────────────

_local = threading.local()
_db_lock = threading.Lock()


def _db_path(artifacts_root: Path) -> Path:
    return artifacts_root / "jobs.db"


def _connect(artifacts_root: Path) -> sqlite3.Connection:
    if not hasattr(_local, "conns"):
        _local.conns = {}
    key = str(artifacts_root)
    if key not in _local.conns:
        path = _db_path(artifacts_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Serialize connection setup: the WAL journal-mode switch takes an
        # exclusive lock and does not reliably honor the busy timeout, so
        # threads racing to create the first connections to a fresh DB can
        # crash with "database is locked".
        with _db_lock:
            conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
            conn.execute("PRAGMA busy_timeout=30000")
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


# ── Public API — routes to correct backend ───────────────────────────────────

def list_jobs(
    artifacts_root: Path,
    limit: int = 50,
    config_prefix: str | None = None,
) -> list[dict[str, Any]]:
    """Return up to `limit` jobs, newest first. Filters by config_prefix when supplied."""
    if _USE_POSTGRES:
        return _list_jobs_pg(limit, config_prefix)

    conn = _connect(artifacts_root)
    conn.row_factory = sqlite3.Row
    if config_prefix:
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
    if _USE_POSTGRES:
        _save_job_pg(job)
        return

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
    if _USE_POSTGRES:
        return _update_job_pg(job_id, patch)

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
    if _USE_POSTGRES:
        return _mark_stale_running_pg()

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
    """One-time migration: import existing jobs.json into the active backend."""
    json_path = artifacts_root / "jobs.json"
    if not json_path.is_file():
        return 0
    if not _USE_POSTGRES:
        conn = _connect(artifacts_root)
        existing = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        if existing > 0:
            return 0
    try:
        jobs = json.loads(json_path.read_text())
        if not isinstance(jobs, list):
            return 0
        for job in jobs:
            save_job(artifacts_root, job)
        json_path.rename(json_path.with_suffix(".json.migrated"))
        return len(jobs)
    except Exception:
        return 0
