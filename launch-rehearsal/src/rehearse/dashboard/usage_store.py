"""Usage metering — runs per workspace per billing period.

Jobs aren't linked to a workspace_id directly; they're attributed by
config_prefix (== workspace slug, since create_workspace() sets
run_id_prefix=slug on the auto-generated config YAML). This mirrors the
same prefix-matching list_jobs() already uses for the Runs page.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rehearse.dashboard.job_store import _USE_POSTGRES, _connect, _get_pg_pool


def current_period_bounds(now: datetime | None = None) -> tuple[str, str]:
    """ISO bounds [start, end) of the current UTC calendar month."""
    now = now or datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start.isoformat(), end.isoformat()


def count_runs_in_period(
    artifacts_root: Path, config_prefix: str, start_iso: str, end_iso: str
) -> int:
    """Count jobs attributed to config_prefix with started_at in [start_iso, end_iso)."""
    if _USE_POSTGRES:
        pool = _get_pg_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT COUNT(*) FROM jobs
                       WHERE (data->>'config' LIKE %s OR data->>'runId' LIKE %s)
                         AND started_at >= %s AND started_at < %s""",
                    (f"%{config_prefix}%", f"{config_prefix}%", start_iso, end_iso),
                )
                return cur.fetchone()[0]
        finally:
            pool.putconn(conn)

    conn = _connect(artifacts_root)
    row = conn.execute(
        """SELECT COUNT(*) FROM jobs
           WHERE (json_extract(data, '$.config') LIKE ? OR json_extract(data, '$.runId') LIKE ?)
             AND started_at >= ? AND started_at < ?""",
        (f"%{config_prefix}%", f"{config_prefix}%", start_iso, end_iso),
    ).fetchone()
    return row[0] if row else 0


def usage_for_workspace(artifacts_root: Path, workspace_slug: str) -> dict[str, Any]:
    """Current-month run count for a workspace, keyed by its slug as config_prefix."""
    start_iso, end_iso = current_period_bounds()
    runs_this_month = count_runs_in_period(artifacts_root, workspace_slug, start_iso, end_iso)
    return {
        "workspaceSlug": workspace_slug,
        "runsThisMonth": runs_this_month,
        "periodStart": start_iso,
        "periodEnd": end_iso,
    }
