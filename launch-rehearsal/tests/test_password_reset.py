"""Password reset flow — token lifecycle, set_password, email lookup.

Covers the pieces added for the forgot/reset password feature:
auth_store.get_user_by_email, auth_store.set_password, and the
password_reset token store (create/validate/consume/expire).
"""

from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

from rehearse.dashboard.auth_store import (
    authenticate_user,
    create_user,
    ensure_users_table,
    get_user_by_email,
    set_password,
)
from rehearse.dashboard.password_reset import (
    consume_reset_token,
    create_reset_token,
    ensure_reset_tokens_table,
    validate_reset_token,
)


def _setup(tmp_path: Path) -> dict:
    ensure_users_table(tmp_path)
    ensure_reset_tokens_table(tmp_path)
    user = create_user(tmp_path, email="reset@example.com", password="original123", name="Resetter")
    assert user is not None
    return user


# ── get_user_by_email ────────────────────────────────────────────────────


def test_get_user_by_email_found(tmp_path: Path):
    user = _setup(tmp_path)
    found = get_user_by_email(tmp_path, "reset@example.com")
    assert found is not None
    assert found["id"] == user["id"]


def test_get_user_by_email_normalizes_case_and_whitespace(tmp_path: Path):
    user = _setup(tmp_path)
    found = get_user_by_email(tmp_path, "  RESET@Example.COM ")
    assert found is not None
    assert found["id"] == user["id"]


def test_get_user_by_email_unknown_returns_none(tmp_path: Path):
    _setup(tmp_path)
    assert get_user_by_email(tmp_path, "nobody@example.com") is None


def test_get_user_by_email_empty_returns_none(tmp_path: Path):
    _setup(tmp_path)
    assert get_user_by_email(tmp_path, "") is None


# ── set_password ─────────────────────────────────────────────────────────


def test_set_password_changes_credential(tmp_path: Path):
    user = _setup(tmp_path)
    out = set_password(tmp_path, user["id"], "brandNewPass99")
    assert out is not None
    assert authenticate_user(tmp_path, "reset@example.com", "brandNewPass99") is not None
    assert authenticate_user(tmp_path, "reset@example.com", "original123") is None


def test_set_password_unknown_user_returns_none(tmp_path: Path):
    _setup(tmp_path)
    assert set_password(tmp_path, "no-such-id", "whatever123") is None


def test_set_password_empty_password_returns_none(tmp_path: Path):
    user = _setup(tmp_path)
    assert set_password(tmp_path, user["id"], "") is None
    # original credential still works
    assert authenticate_user(tmp_path, "reset@example.com", "original123") is not None


# ── reset token lifecycle ────────────────────────────────────────────────


def test_token_roundtrip(tmp_path: Path):
    user = _setup(tmp_path)
    token = create_reset_token(tmp_path, user["id"], user["email"])
    data = validate_reset_token(tmp_path, token)
    assert data is not None
    assert data["user_id"] == user["id"]
    assert data["email"] == user["email"]


def test_invalid_token_rejected(tmp_path: Path):
    _setup(tmp_path)
    assert validate_reset_token(tmp_path, "totally-bogus") is None


def test_consumed_token_rejected(tmp_path: Path):
    user = _setup(tmp_path)
    token = create_reset_token(tmp_path, user["id"], user["email"])
    consume_reset_token(tmp_path, token)
    assert validate_reset_token(tmp_path, token) is None


def test_expired_token_rejected(tmp_path: Path):
    user = _setup(tmp_path)
    token = create_reset_token(tmp_path, user["id"], user["email"])
    # Force-expire the token directly in the DB
    past = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    ).isoformat()
    conn = sqlite3.connect(str(tmp_path / "jobs.db"))
    conn.execute(
        "UPDATE password_reset_tokens SET expires_at = ? WHERE token = ?", (past, token)
    )
    conn.commit()
    conn.close()
    assert validate_reset_token(tmp_path, token) is None
