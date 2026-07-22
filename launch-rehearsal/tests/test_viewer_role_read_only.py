"""Viewer role — a read-only stakeholder must not be able to trigger runs
or overwrite configs, only owner/member can.

Prior to this, workspace roles were a binary owner/member split with no
way to give an external stakeholder (an exec who wants to see scorecards,
a client) access without also handing them the ability to burn the
workspace's LLM budget by triggering runs. "viewer" fills that gap for the
highest-value, most cost-impacting write paths (run-triggering,
config-saving) — this is a deliberately partial RBAC surface, not a claim
that every settings/persona/journey-edit endpoint in the API is gated.
"""
from __future__ import annotations

import http.client
import importlib
import json
import threading
import time
from pathlib import Path

import pytest

import rehearse.dashboard.server as server_module
from rehearse.dashboard.auth_store import create_user, ensure_users_table, issue_token
from rehearse.dashboard.workspace_store import (
    add_member,
    create_workspace,
    ensure_membership_tables,
    ensure_workspaces_table,
)


@pytest.fixture
def workspace_with_viewer(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REHEARSE_DISABLE_AUTH", "0")
    monkeypatch.delenv("REHEARSE_API_TOKEN", raising=False)
    importlib.reload(server_module)

    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)

    owner = create_user(tmp_path, email="owner@a.com", password="ownerpass123", name="Owner")
    viewer_user = create_user(tmp_path, email="viewer@a.com", password="viewerpass123", name="Viewer")
    owner_token = issue_token(owner)
    viewer_token = issue_token(viewer_user)

    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="Acme Co", target_url="https://acme.example.com",
        product_name="AcmeProduct", team_role="founder",
    )
    add_member(tmp_path, ws["id"], viewer_user["id"], role="viewer")

    srv, _ = server_module._bind_server("127.0.0.1", 0, tmp_path)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    try:
        yield port, ws, owner_token, viewer_token
    finally:
        srv.shutdown()
        monkeypatch.delenv("REHEARSE_DISABLE_AUTH", raising=False)
        importlib.reload(server_module)


def _post(port: int, path: str, body: dict, token: str) -> tuple[int, dict]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(
        "POST", path, body=json.dumps(body),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    try:
        return resp.status, json.loads(data)
    except Exception:
        return resp.status, {}


def test_viewer_cannot_trigger_run(workspace_with_viewer):
    port, ws, owner_token, viewer_token = workspace_with_viewer
    status, body = _post(port, "/api/jobs", {"configPath": ws["configPath"], "mode": "run"}, viewer_token)
    assert status == 403
    assert "read-only" in body.get("error", "").lower()


def test_viewer_cannot_trigger_cohort_run(workspace_with_viewer):
    port, ws, owner_token, viewer_token = workspace_with_viewer
    status, body = _post(
        port, "/api/jobs/cohort", {"configPath": ws["configPath"], "nSeeds": 3}, viewer_token,
    )
    assert status == 403
    assert "read-only" in body.get("error", "").lower()


def test_viewer_cannot_save_config(workspace_with_viewer):
    port, ws, owner_token, viewer_token = workspace_with_viewer
    status, body = _post(
        port, "/api/configs/save",
        {"yaml": "run:\n  target_url: https://x.com\n", "configId": ws["slug"]},
        viewer_token,
    )
    assert status == 403
    assert "read-only" in body.get("error", "").lower()


def test_owner_is_not_blocked_by_viewer_check(workspace_with_viewer):
    port, ws, owner_token, viewer_token = workspace_with_viewer
    status, body = _post(port, "/api/jobs", {"configPath": ws["configPath"], "mode": "run"}, owner_token)
    assert status != 403


def test_invite_accepts_viewer_role(workspace_with_viewer):
    port, ws, owner_token, viewer_token = workspace_with_viewer
    status, body = _post(
        port, f"/api/workspaces/{ws['slug']}/invite",
        {"email": "newviewer@a.com", "role": "viewer"}, owner_token,
    )
    assert status == 201
    assert body.get("role") == "viewer"


def test_invite_rejects_unknown_role(workspace_with_viewer):
    port, ws, owner_token, viewer_token = workspace_with_viewer
    status, body = _post(
        port, f"/api/workspaces/{ws['slug']}/invite",
        {"email": "x@a.com", "role": "superadmin"}, owner_token,
    )
    assert status == 400
