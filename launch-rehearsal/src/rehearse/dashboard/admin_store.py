"""Admin / company observability — aggregated view across every user,
workspace, and run in this deployment.

This exists because of a real incident: a brand-new workspace was created,
its config auto-generated with a bad target URL (resolved to a login page,
no auth configured), and no one — including the founder — had any way to
notice until the user reported a vague "didn't crawl well." There was no
view of "which workspaces exist and have they ever actually run." This
module is that view.

Gated by is_admin_email() — see that function for the access model. Every
function here reads across ALL workspaces/users, so nothing in this module
should ever be reachable by a non-admin caller.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def is_admin_email(email: str | None) -> bool:
    """Whether *email* may access admin endpoints.

    REHEARSE_ADMIN_EMAILS is a comma-separated allowlist. If it's unset,
    access is open to any authenticated user — this deployment is currently
    single-tenant with no per-workspace data isolation anyway (any
    authenticated user can already enumerate other workspaces' run data
    through existing endpoints), so an unconfigured allowlist defaulting to
    "deny everyone including the founder" would be strictly worse than the
    status quo. Set the env var the moment there's more than one real admin
    or a customer who'd notice.
    """
    allowlist = os.environ.get("REHEARSE_ADMIN_EMAILS", "").strip()
    if not allowlist:
        return True
    allowed = {e.strip().lower() for e in allowlist.split(",") if e.strip()}
    return bool(email) and email.lower() in allowed


def _last_job_for_slug(artifacts_root: Path, slug: str) -> dict[str, Any] | None:
    from rehearse.dashboard.job_store import list_jobs

    jobs = list_jobs(artifacts_root, limit=1000, config_prefix=slug)
    return jobs[0] if jobs else None


def _run_count_for_slug(artifacts_root: Path, slug: str) -> int:
    from rehearse.dashboard.job_store import list_jobs

    return len(list_jobs(artifacts_root, limit=1000, config_prefix=slug))


def _product_analysis_summary(artifacts_root: Path, slug: str) -> dict[str, Any] | None:
    """A workspace can have zero rehearsal jobs but still have a real,
    successful onboarding-time product analysis (its own deep crawl, separate
    from the job queue) — surfaced so "neverRan" reads as "no readiness score
    yet," not "nothing happened."
    """
    from rehearse.product_intelligence import load_product_model

    product_model = load_product_model(artifacts_root, slug)
    if not product_model:
        return None
    diagnostics = product_model.get("crawlDiagnostics") or {}
    return {
        "pageCount": product_model.get("pageCount", 0),
        "source": product_model.get("source"),
        "authWallDetected": diagnostics.get("authWallDetected"),
        "loginAttempted": diagnostics.get("loginAttempted"),
        "loginSucceeded": diagnostics.get("loginSucceeded"),
    }


def _workspace_summary(
    artifacts_root: Path, ws: dict[str, Any], users_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    from rehearse.dashboard.workspace_store import get_members
    from rehearse.dashboard.billing import check_quota

    slug = ws["slug"]
    last_job = _last_job_for_slug(artifacts_root, slug)
    total_runs = _run_count_for_slug(artifacts_root, slug)
    owner = users_by_id.get(ws.get("ownerId"))
    quota = check_quota(artifacts_root, slug, ws.get("plan"))

    return {
        "id": ws["id"],
        "slug": slug,
        "name": ws["name"],
        "ownerEmail": owner["email"] if owner else None,
        "ownerName": owner["name"] if owner else None,
        "targetUrl": ws["targetUrl"],
        "productName": ws["productName"],
        "plan": ws.get("plan", "design_partner"),
        "createdAt": ws["createdAt"],
        "memberCount": len(get_members(artifacts_root, ws["id"])),
        "totalRuns": total_runs,
        "neverRan": total_runs == 0,
        "lastRunStatus": last_job.get("status") if last_job else None,
        "lastRunAt": last_job.get("startedAt") if last_job else None,
        "lastRunError": last_job.get("error") if last_job else None,
        "runsThisMonth": quota.get("runsThisMonth"),
        "runLimit": quota.get("limit"),
        "productAnalysis": _product_analysis_summary(artifacts_root, slug),
    }


def workspace_overview(artifacts_root: Path) -> list[dict[str, Any]]:
    """Every workspace, enriched with owner email, member count, plan, and
    run history — including whether it has ever run at all."""
    from rehearse.dashboard.auth_store import list_all_users
    from rehearse.dashboard.workspace_store import list_all_workspaces

    users_by_id = {u["id"]: u for u in list_all_users(artifacts_root)}
    return [
        _workspace_summary(artifacts_root, ws, users_by_id)
        for ws in list_all_workspaces(artifacts_root)
    ]


def _read_config_yaml_lenient(
    config_path: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """Read personas/journeys straight from the config YAML for *display
    only* — deliberately does not use rehearse.dsl.load_config(), which
    enforces MIN_PERSONAS/MIN_JOURNEYS for actually running a rehearsal.
    Onboarding's auto-generated config has personas but zero journeys
    (journeys get supplemented at crawl time) — that strict validation would
    raise on every freshly-onboarded workspace and this view would show
    empty personas for almost everyone, which is the opposite of the point.

    Returns (personas, journeys, error) — error is set only on a genuine
    read/parse failure (missing file, invalid YAML), not on "too few" of
    anything.
    """
    if not config_path or not Path(config_path).is_file():
        return [], [], None
    try:
        import yaml as _yaml

        data = _yaml.safe_load(Path(config_path).read_text()) or {}
        personas = [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "role": p.get("role"),
                "goals": p.get("goals") or [],
                "enabled": p.get("enabled", True),
                "techLiteracy": p.get("tech_literacy", "intermediate"),
                "patience": p.get("patience", "medium"),
                "trustLevel": p.get("trust_level", "neutral"),
            }
            for p in (data.get("personas") or [])
        ]
        journeys = [
            {
                "id": j.get("id"),
                "name": j.get("name"),
                "stepCount": len(j.get("steps") or []),
                "personaIds": j.get("persona_ids") or [],
            }
            for j in (data.get("journeys") or [])
        ]
        return personas, journeys, None
    except Exception as exc:
        return [], [], str(exc)[:300]


def workspace_detail(artifacts_root: Path, slug: str) -> dict[str, Any] | None:
    """Full per-workspace deep-dive: everything in workspace_overview() plus
    personas, journeys, the full product intelligence model, every job
    (not just the latest), and the member list with names/emails.

    Returns None if no workspace has this slug.
    """
    from rehearse.dashboard.auth_store import list_all_users
    from rehearse.dashboard.workspace_store import get_workspace_by_slug, get_members
    from rehearse.dashboard.job_store import list_jobs
    from rehearse.product_intelligence import load_product_model

    ws = get_workspace_by_slug(artifacts_root, slug)
    if not ws:
        return None

    users_by_id = {u["id"]: u for u in list_all_users(artifacts_root)}
    summary = _workspace_summary(artifacts_root, ws, users_by_id)

    members = [dict(m) for m in get_members(artifacts_root, ws["id"])]
    config_path = ws.get("configPath")
    personas, journeys, config_error = _read_config_yaml_lenient(config_path)

    all_jobs = list_jobs(artifacts_root, limit=500, config_prefix=slug)
    product_model = load_product_model(artifacts_root, slug)

    return {
        **summary,
        "members": members,
        "personas": personas,
        "journeys": journeys,
        "configError": config_error,
        "jobs": all_jobs,
        "productModel": product_model,
    }


def recent_activity(artifacts_root: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Most recent jobs across every workspace, newest first."""
    from rehearse.dashboard.job_store import list_jobs

    return list_jobs(artifacts_root, limit=limit)


def live_jobs(artifacts_root: Path) -> list[dict[str, Any]]:
    """Jobs currently queued or running, across every workspace — the
    real-time "what's happening right now" view. Scans the most recent 500
    jobs rather than the whole table; a live job that's somehow older than
    that has bigger problems than not showing up here."""
    from rehearse.dashboard.job_store import list_jobs

    jobs = list_jobs(artifacts_root, limit=500)
    return [j for j in jobs if j.get("status") in ("queued", "running")]


def failure_breakdown(artifacts_root: Path, limit: int = 200) -> dict[str, Any]:
    """Where things are failing, aggregated across every workspace: which
    error messages recur, and which workspaces carry the most failures."""
    from rehearse.dashboard.job_store import list_jobs

    jobs = list_jobs(artifacts_root, limit=limit)
    failed = [j for j in jobs if j.get("status") == "failed"]

    by_error: dict[str, int] = {}
    by_config: dict[str, int] = {}
    for j in failed:
        # Errors are often unique (stack traces, timestamps) — bucket by the
        # first line so genuinely repeated failure modes still group together.
        error_line = (j.get("error") or "unknown error").strip().splitlines()[0][:200]
        by_error[error_line] = by_error.get(error_line, 0) + 1
        config = (j.get("config") or "unknown").split("/")[-1]
        by_config[config] = by_config.get(config, 0) + 1

    top_errors = sorted(by_error.items(), key=lambda kv: kv[1], reverse=True)[:20]
    top_configs = sorted(by_config.items(), key=lambda kv: kv[1], reverse=True)[:20]

    return {
        "totalFailed": len(failed),
        "totalChecked": len(jobs),
        "topErrors": [{"error": e, "count": c} for e, c in top_errors],
        "topFailingConfigs": [{"config": cfg, "count": c} for cfg, c in top_configs],
        "recentFailures": failed[:20],
    }


def company_summary(artifacts_root: Path) -> dict[str, Any]:
    """Top-line numbers for a single glance: users, workspaces, stuck
    workspaces, and recent failures."""
    from rehearse.dashboard.auth_store import list_all_users

    users = list_all_users(artifacts_root)
    workspaces = workspace_overview(artifacts_root)
    recent = recent_activity(artifacts_root, limit=200)

    never_ran = [w for w in workspaces if w["neverRan"]]
    failed_recent = [j for j in recent if j.get("status") == "failed"]

    return {
        "totalUsers": len(users),
        "totalWorkspaces": len(workspaces),
        "workspacesNeverRun": len(never_ran),
        "neverRunSlugs": [w["slug"] for w in never_ran],
        "failedJobsRecent": len(failed_recent),
        "totalJobsRecorded": len(recent),
    }
