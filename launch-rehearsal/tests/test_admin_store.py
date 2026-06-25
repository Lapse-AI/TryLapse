"""Admin/company observability — built after a real incident: a workspace
was created, never ran a single job, and nobody had a way to notice until
the user reported a vague "didn't crawl well." These tests cover the
never-ran detection specifically, plus the access-control default.
"""

from __future__ import annotations

from pathlib import Path

from rehearse.dashboard.admin_store import (
    company_summary,
    failure_breakdown,
    is_admin_email,
    live_jobs,
    recent_activity,
    workspace_detail,
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


def test_workspace_overview_surfaces_product_analysis_when_jobs_never_ran(tmp_path: Path):
    """The exact correction to the original incident: no rehearsal job ever
    ran, but onboarding's product-intelligence analysis did, successfully —
    neverRan must stay true (no readiness score exists) while
    productAnalysis shows the real, successful crawl underneath it."""
    from rehearse.product_intelligence import save_product_model

    _setup(tmp_path)
    owner = create_user(tmp_path, email="sparsh@gmail.com", password="pw123456", name="Sparsh")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="ArgyleHRsolutions",
        target_url="https://faculty-dashboard-eight.vercel.app/login",
        product_name="Argyle Trainer Dashboard", team_role="founder",
    )
    save_product_model(
        tmp_path,
        {
            "pageCount": 8,
            "source": "llm",
            "crawlDiagnostics": {
                "authWallDetected": False,
                "loginAttempted": True,
                "loginSucceeded": True,
            },
        },
        "argylehrsolutions",
    )

    overview = workspace_overview(tmp_path)
    ws = overview[0]
    assert ws["neverRan"] is True
    assert ws["productAnalysis"] is not None
    assert ws["productAnalysis"]["pageCount"] == 8
    assert ws["productAnalysis"]["loginSucceeded"] is True


def test_workspace_overview_product_analysis_none_when_never_analyzed(tmp_path: Path):
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner4@example.com", password="pw123456", name="Owner")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Fresh", target_url="https://fresh.com",
        product_name="Fresh", team_role="founder",
    )
    overview = workspace_overview(tmp_path)
    assert overview[0]["productAnalysis"] is None


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


# ── workspace_detail ──────────────────────────────────────────────────────────


def _write_config_yaml(path: Path, *, personas: list[dict], journeys: list[dict] | None = None) -> None:
    import yaml

    data: dict = {
        "run": {"target_url": "https://example.com", "run_id_prefix": "x", "product_name": "X"},
        "personas": personas,
    }
    if journeys is not None:
        data["journeys"] = journeys
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False))


def test_workspace_detail_returns_none_for_unknown_slug(tmp_path: Path):
    _setup(tmp_path)
    assert workspace_detail(tmp_path, "nonexistent") is None


def test_workspace_detail_reads_personas_with_zero_journeys(tmp_path: Path):
    """The exact gap caught while writing this test: onboarding's
    auto-generated config has personas but zero journeys (journeys get
    supplemented at crawl time) — rehearse.dsl.load_config() would raise on
    this (MIN_JOURNEYS=5) and show empty personas for nearly every real
    workspace. workspace_detail() must show the personas anyway."""
    _setup(tmp_path)
    owner = create_user(tmp_path, email="sparsh@gmail.com", password="pw123456", name="Sparsh")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="ArgyleHRsolutions",
        target_url="https://faculty-dashboard-eight.vercel.app",
        product_name="Argyle Trainer Dashboard", team_role="founder",
    )
    config_path = Path(ws["configPath"])
    _write_config_yaml(
        config_path,
        personas=[
            {"id": "p1-new-signup", "name": "New signup", "role": "first-time user", "goals": ["a", "b"]},
            {"id": "p2-power-user", "name": "Power user", "role": "experienced user", "goals": ["c"]},
        ],
        journeys=[],
    )

    detail = workspace_detail(tmp_path, "argylehrsolutions")
    assert detail is not None
    assert len(detail["personas"]) == 2
    assert detail["personas"][0]["name"] == "New signup"
    assert detail["journeys"] == []
    assert detail["configError"] is None


def test_workspace_detail_includes_full_job_history_and_members(tmp_path: Path):
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner5@example.com", password="pw123456", name="Owner")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="Acme", target_url="https://acme.com",
        product_name="Acme", team_role="founder",
    )
    _write_config_yaml(Path(ws["configPath"]), personas=[{"id": "p1", "name": "P1", "role": "r", "goals": []}])
    for i in range(3):
        save_job(tmp_path, {
            "id": f"job_{i}", "status": "done", "config": "/configs/acme.yaml",
            "startedAt": f"2026-06-{10+i:02d}T00:00:00+00:00", "finishedAt": None,
        })

    detail = workspace_detail(tmp_path, "acme")
    assert len(detail["jobs"]) == 3
    assert len(detail["members"]) == 1
    assert detail["members"][0]["email"] == "owner5@example.com"


def test_workspace_detail_handles_missing_config_file(tmp_path: Path):
    """configPath points at a file that's been moved/deleted — must not crash,
    and a missing file is not the same as a malformed one (no configError)."""
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner6@example.com", password="pw123456", name="Owner")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="NoConfig", target_url="https://noconfig.com",
        product_name="NoConfig", team_role="founder",
    )
    Path(ws["configPath"]).unlink()  # create_workspace auto-generates it; remove it

    detail = workspace_detail(tmp_path, "noconfig")
    assert detail is not None
    assert detail["personas"] == []
    assert detail["journeys"] == []
    assert detail["configError"] is None


def test_workspace_detail_surfaces_config_error_on_malformed_yaml(tmp_path: Path):
    _setup(tmp_path)
    owner = create_user(tmp_path, email="owner7@example.com", password="pw123456", name="Owner")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="Broken", target_url="https://broken.com",
        product_name="Broken", team_role="founder",
    )
    Path(ws["configPath"]).write_text("not: valid: yaml: [[[")

    detail = workspace_detail(tmp_path, "broken")
    assert detail is not None
    assert detail["personas"] == []
    assert detail["configError"] is not None


# ── live_jobs ──────────────────────────────────────────────────────────────────


def test_live_jobs_includes_only_queued_and_running(tmp_path: Path):
    save_job(tmp_path, {"id": "j1", "status": "queued", "config": "/x.yaml", "startedAt": "2026-06-01T00:00:00+00:00", "finishedAt": None})
    save_job(tmp_path, {"id": "j2", "status": "running", "config": "/x.yaml", "startedAt": "2026-06-02T00:00:00+00:00", "finishedAt": None})
    save_job(tmp_path, {"id": "j3", "status": "done", "config": "/x.yaml", "startedAt": "2026-06-03T00:00:00+00:00", "finishedAt": None})
    save_job(tmp_path, {"id": "j4", "status": "failed", "config": "/x.yaml", "startedAt": "2026-06-04T00:00:00+00:00", "finishedAt": None})

    live = live_jobs(tmp_path)
    ids = {j["id"] for j in live}
    assert ids == {"j1", "j2"}


def test_live_jobs_empty_when_nothing_active(tmp_path: Path):
    save_job(tmp_path, {"id": "j1", "status": "done", "config": "/x.yaml", "startedAt": "2026-06-01T00:00:00+00:00", "finishedAt": None})
    assert live_jobs(tmp_path) == []


# ── failure_breakdown ──────────────────────────────────────────────────────────


def test_failure_breakdown_groups_by_error_and_config(tmp_path: Path):
    save_job(tmp_path, {
        "id": "j1", "status": "failed", "config": "/configs/acme.yaml",
        "startedAt": "2026-06-01T00:00:00+00:00", "finishedAt": None,
        "error": "Preflight failed: connection refused",
    })
    save_job(tmp_path, {
        "id": "j2", "status": "failed", "config": "/configs/acme.yaml",
        "startedAt": "2026-06-02T00:00:00+00:00", "finishedAt": None,
        "error": "Preflight failed: connection refused",
    })
    save_job(tmp_path, {
        "id": "j3", "status": "failed", "config": "/configs/beta.yaml",
        "startedAt": "2026-06-03T00:00:00+00:00", "finishedAt": None,
        "error": "Timeout waiting for selector",
    })
    save_job(tmp_path, {
        "id": "j4", "status": "done", "config": "/configs/acme.yaml",
        "startedAt": "2026-06-04T00:00:00+00:00", "finishedAt": None,
    })

    breakdown = failure_breakdown(tmp_path)
    assert breakdown["totalFailed"] == 3
    assert breakdown["topErrors"][0]["error"] == "Preflight failed: connection refused"
    assert breakdown["topErrors"][0]["count"] == 2
    assert breakdown["topFailingConfigs"][0]["config"] == "acme.yaml"
    assert breakdown["topFailingConfigs"][0]["count"] == 2


def test_failure_breakdown_empty_when_no_failures(tmp_path: Path):
    save_job(tmp_path, {"id": "j1", "status": "done", "config": "/x.yaml", "startedAt": "2026-06-01T00:00:00+00:00", "finishedAt": None})
    breakdown = failure_breakdown(tmp_path)
    assert breakdown["totalFailed"] == 0
    assert breakdown["topErrors"] == []
    assert breakdown["recentFailures"] == []


def test_failure_breakdown_handles_missing_error_message(tmp_path: Path):
    save_job(tmp_path, {
        "id": "j1", "status": "failed", "config": "/x.yaml",
        "startedAt": "2026-06-01T00:00:00+00:00", "finishedAt": None,
    })
    breakdown = failure_breakdown(tmp_path)
    assert breakdown["totalFailed"] == 1
    assert breakdown["topErrors"][0]["error"] == "unknown error"
