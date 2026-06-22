"""Auth store — user creation, login, profile updates.

No test coverage existed for auth_store.py before the profile/settings page
work. These cover the existing create/authenticate/token flow plus the new
get_user/update_user functions needed to back a profile settings page.
"""

from __future__ import annotations

from pathlib import Path

from rehearse.dashboard.auth_store import (
    authenticate_user,
    create_user,
    decode_token,
    ensure_users_table,
    get_user,
    issue_token,
    update_user,
)


def _setup(tmp_path: Path) -> None:
    ensure_users_table(tmp_path)


def test_create_user_returns_id_email_name(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="A@Example.com", password="hunter2pass", name="Ada")
    assert user is not None
    assert user["email"] == "a@example.com"  # normalized lowercase
    assert user["name"] == "Ada"
    assert user["id"]


def test_create_user_duplicate_email_returns_none(tmp_path: Path):
    _setup(tmp_path)
    create_user(tmp_path, email="dup@example.com", password="pw123456", name="One")
    second = create_user(tmp_path, email="dup@example.com", password="pw123456", name="Two")
    assert second is None


def test_create_user_defaults_name_from_email(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="noname@example.com", password="pw123456", name="")
    assert user["name"] == "noname"


def test_authenticate_user_correct_password(tmp_path: Path):
    _setup(tmp_path)
    create_user(tmp_path, email="auth@example.com", password="correctpw", name="Auth")
    user = authenticate_user(tmp_path, email="auth@example.com", password="correctpw")
    assert user is not None
    assert user["email"] == "auth@example.com"


def test_authenticate_user_wrong_password(tmp_path: Path):
    _setup(tmp_path)
    create_user(tmp_path, email="auth2@example.com", password="correctpw", name="Auth")
    user = authenticate_user(tmp_path, email="auth2@example.com", password="wrongpw")
    assert user is None


def test_authenticate_user_unknown_email(tmp_path: Path):
    _setup(tmp_path)
    user = authenticate_user(tmp_path, email="nope@example.com", password="anything")
    assert user is None


def test_issue_and_decode_token_roundtrip(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="tok@example.com", password="pw123456", name="Tok")
    token = issue_token(user)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user["id"]
    assert payload["email"] == "tok@example.com"


# ── get_user / update_user (new, for profile settings) ──────────────────────


def test_get_user_returns_current_record(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="lookup@example.com", password="pw123456", name="Lookup")
    found = get_user(tmp_path, user["id"])
    assert found == {"id": user["id"], "email": "lookup@example.com", "name": "Lookup"}


def test_get_user_missing_returns_none(tmp_path: Path):
    _setup(tmp_path)
    assert get_user(tmp_path, "nonexistent-id") is None


def test_update_user_name_only(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="rename@example.com", password="pw123456", name="Old Name")
    updated = update_user(tmp_path, user["id"], name="New Name")
    assert updated["name"] == "New Name"
    assert get_user(tmp_path, user["id"])["name"] == "New Name"


def test_update_user_password_requires_current_password(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="pwchange@example.com", password="oldpw1234", name="X")
    # Wrong current password — rejected
    result = update_user(tmp_path, user["id"], password="newpw5678", current_password="wrongpw")
    assert result is None
    # Old password still works
    assert authenticate_user(tmp_path, email="pwchange@example.com", password="oldpw1234") is not None


def test_update_user_password_with_correct_current_password(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="pwchange2@example.com", password="oldpw1234", name="X")
    result = update_user(
        tmp_path, user["id"], password="newpw5678", current_password="oldpw1234"
    )
    assert result is not None
    assert authenticate_user(tmp_path, email="pwchange2@example.com", password="newpw5678") is not None
    assert authenticate_user(tmp_path, email="pwchange2@example.com", password="oldpw1234") is None


def test_update_user_missing_user_returns_none(tmp_path: Path):
    _setup(tmp_path)
    assert update_user(tmp_path, "nonexistent-id", name="X") is None


def test_update_user_blank_name_keeps_existing(tmp_path: Path):
    _setup(tmp_path)
    user = create_user(tmp_path, email="blank@example.com", password="pw123456", name="Keep Me")
    updated = update_user(tmp_path, user["id"], name="   ")
    assert updated["name"] == "Keep Me"
