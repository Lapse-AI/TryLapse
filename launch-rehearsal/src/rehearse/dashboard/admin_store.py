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


def workspace_overview(artifacts_root: Path) -> list[dict[str, Any]]:
    """Every workspace, enriched with owner email, member count, plan, and
    run history — including whether it has ever run at all."""
    from rehearse.dashboard.auth_store import list_all_users
    from rehearse.dashboard.workspace_store import list_all_workspaces, get_members
    from rehearse.dashboard.billing import check_quota
    from rehearse.product_intelligence import load_product_model

    users_by_id = {u["id"]: u for u in list_all_users(artifacts_root)}
    overview = []
    for ws in list_all_workspaces(artifacts_root):
        slug = ws["slug"]
        last_job = _last_job_for_slug(artifacts_root, slug)
        total_runs = _run_count_for_slug(artifacts_root, slug)
        owner = users_by_id.get(ws.get("ownerId"))
        quota = check_quota(artifacts_root, slug, ws.get("plan"))

        # A workspace can have zero rehearsal jobs but still have a real,
        # successful onboarding-time product analysis (its own deep crawl,
        # separate from the job queue) — surface that explicitly so
        # "neverRan" reads as "no readiness score yet," not "nothing happened."
        product_model = load_product_model(artifacts_root, slug)
        product_analysis = None
        if product_model:
            diagnostics = product_model.get("crawlDiagnostics") or {}
            product_analysis = {
                "pageCount": product_model.get("pageCount", 0),
                "source": product_model.get("source"),
                "authWallDetected": diagnostics.get("authWallDetected"),
                "loginAttempted": diagnostics.get("loginAttempted"),
                "loginSucceeded": diagnostics.get("loginSucceeded"),
            }

        overview.append({
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
            "productAnalysis": product_analysis,
        })
    return overview


def recent_activity(artifacts_root: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Most recent jobs across every workspace, newest first."""
    from rehearse.dashboard.job_store import list_jobs

    return list_jobs(artifacts_root, limit=limit)


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
