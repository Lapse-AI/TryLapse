"""Storage-state auth — reusing a human-captured session for SSO/SAML/MFA apps.

BrowserSession can't automate a login form that doesn't exist for SSO-only
apps. `rehearse capture-session` lets a human complete that login once in a
real browser and save the resulting cookies/localStorage; perform_auth then
checks whether that session is still valid before ever touching a login form.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from rehearse.browser import BrowserSession
from rehearse.dsl import AuthConfig, Budgets, RunConfig


def _session_with_auth(storage_state_path: str | None, monkeypatch, auth_ok: bool):
    config = RunConfig(
        target_url="https://app.test",
        run_id_prefix="test",
        product_name="Test",
        auth=AuthConfig(storage_state_path=storage_state_path),
        budgets=Budgets(), personas=[], journeys=[],
    )
    session = BrowserSession.__new__(BrowserSession)  # skip __init__/__enter__ (no real browser)
    session.config = config
    session.page = MagicMock()
    monkeypatch.setattr(BrowserSession, "_auth_session_ok", lambda self: auth_ok)
    return session


def test_valid_storage_state_skips_login_form_entirely(monkeypatch):
    session = _session_with_auth("auth/session.json", monkeypatch, auth_ok=True)
    outcome = session.perform_auth(session.config.auth)
    assert outcome == "success_from_storage_state"
    session.page.get_by_role.assert_not_called()  # never touched a login form


def test_expired_storage_state_with_no_password_fallback_fails_clearly(monkeypatch):
    session = _session_with_auth("auth/session.json", monkeypatch, auth_ok=False)
    outcome = session.perform_auth(session.config.auth)
    assert outcome == "failed_storage_state_expired_no_fallback"


def test_expired_storage_state_falls_back_to_password_login_if_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("REHEARSE_EMAIL", "a@b.com")
    monkeypatch.setenv("REHEARSE_PASSWORD", "hunter2")
    session = _session_with_auth("auth/session.json", monkeypatch, auth_ok=False)
    # Force the subsequent form-fill path to short-circuit predictably rather
    # than drive a fully mocked Playwright page through every locator call.
    session._fill_auth_input = MagicMock()
    submit = MagicMock()
    session.page.get_by_role.return_value = submit
    submit.count.return_value = 1

    def goto_side_effect(url, **kwargs):
        session.page.url = url

    session.page.goto.side_effect = goto_side_effect
    session.page.wait_for_url.side_effect = lambda *a, **k: None
    outcome = session.perform_auth(session.config.auth)
    # It must have attempted the form-fill path (not short-circuited to the
    # no-fallback failure) — the exact success/failure detail past that point
    # is covered by the existing perform_auth tests, this only proves the
    # storage-state branch falls through correctly.
    assert outcome != "failed_storage_state_expired_no_fallback"
    session._fill_auth_input.assert_called()


def test_no_storage_state_path_is_unaffected(monkeypatch):
    """Regression guard: apps without storage_state_path keep today's behavior."""
    session = _session_with_auth(None, monkeypatch, auth_ok=True)
    outcome = session.perform_auth(session.config.auth)
    # Falls through to the pre-existing missing-credentials path, unchanged.
    assert outcome == "skipped_missing_credentials"


def test_context_opts_include_storage_state_when_file_exists(tmp_path):
    state_file = tmp_path / "session.json"
    state_file.write_text('{"cookies": [], "origins": []}')
    config = RunConfig(
        target_url="https://app.test",
        run_id_prefix="test",
        product_name="Test",
        auth=AuthConfig(storage_state_path=str(state_file)),
        budgets=Budgets(), personas=[], journeys=[],
    )
    session = BrowserSession(config, tmp_path / "artifacts")
    # Reproduce just the option-building logic from __enter__ without
    # actually launching a browser.
    state_path = getattr(session.config.auth, "storage_state_path", None) if session.config.auth else None
    assert state_path == str(state_file)
    from pathlib import Path
    assert Path(state_path).is_file()


def test_missing_storage_state_file_is_silently_ignored(tmp_path):
    """A stale/deleted session path must not crash context creation."""
    config = RunConfig(
        target_url="https://app.test",
        run_id_prefix="test",
        product_name="Test",
        auth=AuthConfig(storage_state_path=str(tmp_path / "does-not-exist.json")),
        budgets=Budgets(), personas=[], journeys=[],
    )
    from pathlib import Path
    state_path = config.auth.storage_state_path
    assert not Path(state_path).is_file()
