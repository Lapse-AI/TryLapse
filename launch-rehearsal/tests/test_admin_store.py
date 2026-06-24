"""Admin/company observability — built after a real incident: a workspace
was created, never ran a single job, and nobody had a way to notice until
the user reported a vague "didn't crawl well." These tests cover the
never-ran detection specifically, plus the access-control default.
"""

from __future__ import annotations

from pathlib import Path

from rehearse.dashboard.admin_store import (
    company_summary,
    is_admin_email,
    recent_activity,
    workspace_overview,
)
from rehearse.dashboard.auth_store import create_user, ensure_users_table
from rehearse.dashboard.job_store import save_job
from rehearse.dashboard.workspace_store import (
    create_workspace,
    ensure_membership_tables,
    ensure_workspaces_table,
)


def _setup(tmp_path: Path) -> None:
    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)


# ── is_admin_email ────────────────────────────────────────────────────────────


def test_admin_open_when_no_allowlist_configured(monkeypatch):
    monkeypatch.delenv("REHEARSE_ADMIN_EMAILS", raising=False)
    assert is_admin_email("anyone@example.com") is True
    assert is_admin_email(None) is True


def test_admin_restricted_when_allowlist_configured(monkeypatch):
    monkeypatch.setenv("REHEARSE_ADMIN_EMAILS", "founder@trylapse.com, ops@trylapse.com")
    assert is_admin_email("founder@trylapse.com") is True
    assert is_admin_email("FOUNDER@TRYLAPSE.COM") is True  # case-insensitive
    assert is_admin_email("random@example.com") is False
    assert is_admin_email(None) is False


# ── workspace_overview ────────────────────────────────────────────────────────


def test_workspace_overview_flags_never_ran(tmp_path: Path):
    """The exact scenario that motivated this module: a workspace exists
    with zero jobs ever queued against it."""
    _setup(tmp_path)
    owner = create_user(tmp_path, email="sparsh@gmail.com", password="pw123456", name="Sparsh")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="ArgyleHRsolutions",
        target_url="https://faculty-dashboard-eight.vercel.app/login",
        product_name="Argyle Trainer Dashboard", team_role="founder",
    )

    overview = workspace_overview(tmp_path)
    assert len(overview) == 1
    ws = overview[0]
    assert ws["neverRan"] is True
    assert ws["totalRuns"] == 0
    assert ws["lastRunStatus"] is None
    assert ws["ownerEmail"] == "sparsh@gmail.com"
    assert ws["targetUrl"] == "https://faculty-dashboard-eight.vercel.app/login"


def test_workspace_overview_shows_run_history_when_present(tmp_path: Path):
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner@example.com", password="pw123456", name="Owner")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Acme", target_url="https://acme.com",
        product_name="Acme", team_role="founder",
    )
    save_job(tmp_path, {
        "id": "job_1", "status": "done", "config": "/configs/acme.yaml",
        "startedAt": "2026-06-20T00:00:00+00:00", "finishedAt": "2026-06-20T00:05:00+00:00",
    })

    overview = workspace_overview(tmp_path)
    ws = overview[0]
    assert ws["neverRan"] is False
    assert ws["totalRuns"] == 1
    assert ws["lastRunStatus"] == "done"


def test_workspace_overview_surfaces_last_error(tmp_path: Path):
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner2@example.com", password="pw123456", name="Owner")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Beta", target_url="https://beta.com",
        product_name="Beta", team_role="founder",
    )
    save_job(tmp_path, {
        "id": "job_1", "status": "failed", "config": "/configs/beta.yaml",
        "startedAt": "2026-06-20T00:00:00+00:00", "finishedAt": "2026-06-20T00:01:00+00:00",
        "error": "Preflight failed: connection refused",
    })

    overview = workspace_overview(tmp_path)
    ws = overview[0]
    assert ws["lastRunStatus"] == "failed"
    assert "connection refused" in ws["lastRunError"]


def test_workspace_overview_empty_deployment(tmp_path: Path):
    _setup(tmp_path)
    assert workspace_overview(tmp_path) == []


# ── recent_activity ───────────────────────────────────────────────────────────


def test_recent_activity_empty(tmp_path: Path):
    assert recent_activity(tmp_path) == []


def test_recent_activity_respects_limit(tmp_path: Path):
    for i in range(5):
        save_job(tmp_path, {
            "id": f"job_{i}", "status": "done", "config": "/configs/x.yaml",
            "startedAt": f"2026-06-{10+i:02d}T00:00:00+00:00", "finishedAt": None,
        })
    assert len(recent_activity(tmp_path, limit=3)) == 3


# ── company_summary ───────────────────────────────────────────────────────────


def test_company_summary_counts_never_ran_workspaces(tmp_path: Path):
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner3@example.com", password="pw123456", name="Owner")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Stuck", target_url="https://stuck.com",
        product_name="Stuck", team_role="founder",
    )
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Active", target_url="https://active.com",
        product_name="Active", team_role="founder",
    )
    save_job(tmp_path, {
        "id": "job_1", "status": "done", "config": "/configs/active.yaml",
        "startedAt": "2026-06-20T00:00:00+00:00", "finishedAt": None,
    })

    summary = company_summary(tmp_path)
    assert summary["totalUsers"] == 1
    assert summary["totalWorkspaces"] == 2
    assert summary["workspacesNeverRun"] == 1
    assert "stuck" in summary["neverRunSlugs"]


def test_company_summary_empty_deployment(tmp_path: Path):
    _setup(tmp_path)
    summary = company_summary(tmp_path)
    assert summary["totalUsers"] == 0
    assert summary["totalWorkspaces"] == 0
    assert summary["workspacesNeverRun"] == 0
