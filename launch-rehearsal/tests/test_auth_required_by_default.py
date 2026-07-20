"""Auth must be required by default — regression for a live production incident.

Production behavior before this fix: `_check_auth` returned True
unconditionally whenever REHEARSE_API_TOKEN was unset ("auth disabled —
local dev"). On the hosted deployment that env var was never set, so every
API endpoint — including triggering rehearsal runs and listing all jobs
across all workspaces — was reachable with zero authentication. Verified
live against production: an unauthenticated POST to /api/jobs queued and
ran a real job against another user's workspace config.

The fix: auth is required by default regardless of whether
REHEARSE_API_TOKEN is set. An explicit REHEARSE_DISABLE_AUTH=1 is the only
opt-out, and REHEARSE_API_TOKEN becomes an *additional* accepted
credential rather than a switch that silently turns auth off when absent.

These tests spin up a real DashboardServer on a loopback port and drive it
with actual HTTP requests — the bug was in request-dispatch wiring, not
pure logic, so a real request is the only faithful reproduction.
"""
from __future__ import annotations

import http.client
import json
import threading
import time
from pathlib import Path

import pytest

import rehearse.dashboard.server as server_module
from rehearse.dashboard.server import _bind_server


@pytest.fixture
def live_server(tmp_path: Path, monkeypatch):
    """Real server on a loopback port, with auth env vars reset per-test."""
    monkeypatch.delenv("REHEARSE_API_TOKEN", raising=False)
    monkeypatch.delenv("REHEARSE_DISABLE_AUTH", raising=False)
    # These are read once as module-level constants at import time — the
    # server module must be reloaded so it re-reads the (now-patched) env.
    import importlib
    importlib.reload(server_module)

    srv, _ = server_module._bind_server("127.0.0.1", 0, tmp_path)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    yield port
    srv.shutdown()


def _get(port: int, path: str, headers: dict | None = None) -> int:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path, headers=headers or {})
    resp = conn.getresponse()
    resp.read()
    conn.close()
    return resp.status


def _post(port: int, path: str, body: dict, headers: dict | None = None) -> tuple[int, dict]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    payload = json.dumps(body)
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    conn.request("POST", path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    try:
        return resp.status, json.loads(data)
    except Exception:
        return resp.status, {}


def test_unauthenticated_request_to_protected_endpoint_is_rejected(live_server):
    """The core incident: no token configured must NOT mean no auth enforced."""
    status = _get(live_server, "/api/jobs")
    assert status == 401


def test_unauthenticated_job_trigger_is_rejected(live_server):
    status, _ = _post(live_server, "/api/jobs", {"configPath": "", "mode": "run"})
    assert status == 401


def test_public_paths_remain_reachable_without_auth(live_server):
    assert _get(live_server, "/api/health") == 200


def test_explicit_disable_auth_opt_out_still_works(tmp_path, monkeypatch):
    """Local-dev convenience must survive as an explicit, named opt-in."""
    monkeypatch.setenv("REHEARSE_DISABLE_AUTH", "1")
    monkeypatch.delenv("REHEARSE_API_TOKEN", raising=False)
    import importlib
    importlib.reload(server_module)

    srv, _ = server_module._bind_server("127.0.0.1", 0, tmp_path)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    try:
        assert _get(port, "/api/jobs") == 200
    finally:
        srv.shutdown()
        monkeypatch.delenv("REHEARSE_DISABLE_AUTH", raising=False)
        importlib.reload(server_module)


def test_static_api_token_still_works_as_additional_credential(tmp_path, monkeypatch):
    monkeypatch.setenv("REHEARSE_API_TOKEN", "test-token-123")
    monkeypatch.delenv("REHEARSE_DISABLE_AUTH", raising=False)
    import importlib
    importlib.reload(server_module)

    srv, _ = server_module._bind_server("127.0.0.1", 0, tmp_path)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    try:
        assert _get(port, "/api/jobs", {"Authorization": "Bearer test-token-123"}) == 200
        assert _get(port, "/api/jobs", {"Authorization": "Bearer wrong-token"}) == 401
        assert _get(port, "/api/jobs") == 401
    finally:
        srv.shutdown()
        monkeypatch.delenv("REHEARSE_API_TOKEN", raising=False)
        importlib.reload(server_module)
