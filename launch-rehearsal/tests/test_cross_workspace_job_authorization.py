"""A signed-in user must not be able to trigger runs against another
workspace's config just by knowing/guessing its path.

Regression: /api/jobs checked authentication (is this JWT valid?) but never
authorization (does this user belong to the workspace that owns this
config?). Found alongside the zero-auth-in-production incident — the same
class of bug one layer deeper: even once a caller is required to present a
valid JWT, that JWT could belong to a completely unrelated workspace and
the run would still be enqueued, silently burning the target workspace's
quota and LLM budget.
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
    create_workspace,
    ensure_membership_tables,
    ensure_workspaces_table,
)


@pytest.fixture
def two_users_two_workspaces(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REHEARSE_DISABLE_AUTH", "0")
    monkeypatch.delenv("REHEARSE_API_TOKEN", raising=False)
    importlib.reload(server_module)

    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)

    alice = create_user(tmp_path, email="alice@a.com", password="alicepass123", name="Alice")
    bob = create_user(tmp_path, email="bob@b.com", password="bobpass1234", name="Bob")
    alice_token = issue_token(alice)
    bob_token = issue_token(bob)

    ws_alice = create_workspace(
        tmp_path, owner_id=alice["id"], name="Alice Co", target_url="https://alice.example.com",
        product_name="AliceProduct", team_role="founder",
    )

    srv, _ = server_module._bind_server("127.0.0.1", 0, tmp_path)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    try:
        yield port, ws_alice, alice_token, bob_token
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


def test_non_member_cannot_trigger_run_against_another_workspace(two_users_two_workspaces):
    port, ws_alice, alice_token, bob_token = two_users_two_workspaces
    status, body = _post(
        port, "/api/jobs", {"configPath": ws_alice["configPath"], "mode": "run"}, bob_token,
    )
    assert status == 403
    assert "not a member" in body.get("error", "").lower()


def test_owner_can_trigger_run_against_their_own_workspace(two_users_two_workspaces):
    port, ws_alice, alice_token, bob_token = two_users_two_workspaces
    status, body = _post(
        port, "/api/jobs", {"configPath": ws_alice["configPath"], "mode": "run"}, alice_token,
    )
    # Not asserting 202 specifically — a real rehearsal subprocess would
    # actually launch, which is out of scope for this test. What matters is
    # that it's NOT rejected for authorization (403) the way Bob's request is.
    assert status != 403
