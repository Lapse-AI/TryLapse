"""Workspace membership — multi-user access to a single workspace.

Before this, workspaces had exactly one owner_id and a frozen team_role
string set once at onboarding. There was no way for a second teammate to
access the same workspace under their own login — they'd have to share the
owner's credentials. These tests cover the membership/invite model that
replaces that.
"""

from __future__ import annotations

from pathlib import Path

from rehearse.dashboard.auth_store import create_user, ensure_users_table
from rehearse.dashboard.workspace_store import (
    accept_invite,
    add_member,
    create_invite,
    create_workspace,
    ensure_membership_tables,
    ensure_workspaces_table,
    get_invite,
    get_member_role,
    get_members,
    get_workspace_by_id,
    get_workspace_by_slug,
    get_workspaces_for_user,
    list_invites,
    remove_member,
)


def _setup(tmp_path: Path) -> None:
    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)


def _user(tmp_path: Path, email: str) -> dict:
    return create_user(tmp_path, email=email, password="pw123456", name=email.split("@")[0])


# ── workspace creation auto-adds owner as member ─────────────────────────────


def test_create_workspace_adds_owner_as_member(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="Argyle", target_url="https://argyle.com",
        product_name="Argyle", team_role="engineer",
    )
    members = get_members(tmp_path, ws["id"])
    assert len(members) == 1
    assert members[0]["userId"] == owner["id"]
    assert members[0]["role"] == "owner"
    assert members[0]["name"] == "owner"


def test_get_workspaces_for_user_includes_owned(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner2@example.com")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="WS", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    workspaces = get_workspaces_for_user(tmp_path, owner["id"])
    assert len(workspaces) == 1
    assert workspaces[0]["name"] == "WS"


def test_get_workspaces_for_user_empty_for_stranger(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner3@example.com")
    stranger = _user(tmp_path, "stranger@example.com")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="WS3", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    assert get_workspaces_for_user(tmp_path, stranger["id"]) == []


# ── invite + accept flow ─────────────────────────────────────────────────────


def test_invite_then_accept_grants_access(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner4@example.com")
    teammate = _user(tmp_path, "teammate@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS4", target_url="https://x.com",
        product_name="X", team_role="founder",
    )

    invite = create_invite(tmp_path, ws["id"], "teammate@example.com", "member", owner["id"])
    assert invite["token"]

    # Teammate has no access yet
    assert get_workspaces_for_user(tmp_path, teammate["id"]) == []

    result = accept_invite(tmp_path, invite["token"], teammate["id"])
    assert result is not None
    assert result["role"] == "member"

    # Now they do
    workspaces = get_workspaces_for_user(tmp_path, teammate["id"])
    assert len(workspaces) == 1
    assert workspaces[0]["id"] == ws["id"]

    members = get_members(tmp_path, ws["id"])
    assert {m["userId"] for m in members} == {owner["id"], teammate["id"]}


def test_invite_cannot_be_accepted_twice(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner5@example.com")
    teammate = _user(tmp_path, "teammate5@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS5", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    invite = create_invite(tmp_path, ws["id"], "teammate5@example.com", "member", owner["id"])
    accept_invite(tmp_path, invite["token"], teammate["id"])
    second = accept_invite(tmp_path, invite["token"], teammate["id"])
    assert second is None


def test_invalid_invite_token_returns_none(tmp_path: Path):
    _setup(tmp_path)
    assert accept_invite(tmp_path, "nonexistent-token", "some-user-id") is None


def test_list_invites_excludes_accepted(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner6@example.com")
    teammate = _user(tmp_path, "teammate6@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS6", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    create_invite(tmp_path, ws["id"], "pending@example.com", "member", owner["id"])
    accepted_invite = create_invite(tmp_path, ws["id"], "teammate6@example.com", "member", owner["id"])
    accept_invite(tmp_path, accepted_invite["token"], teammate["id"])

    pending = list_invites(tmp_path, ws["id"])
    assert len(pending) == 1
    assert pending[0]["email"] == "pending@example.com"


def test_get_invite_returns_full_record(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner7@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS7", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    invite = create_invite(tmp_path, ws["id"], "x@example.com", "owner", owner["id"])
    fetched = get_invite(tmp_path, invite["token"])
    assert fetched["email"] == "x@example.com"
    assert fetched["role"] == "owner"
    assert fetched["acceptedAt"] is None


# ── roles + removal ───────────────────────────────────────────────────────────


def test_get_member_role(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner8@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS8", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    assert get_member_role(tmp_path, ws["id"], owner["id"]) == "owner"
    assert get_member_role(tmp_path, ws["id"], "nobody") is None


def test_add_member_directly(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner9@example.com")
    teammate = _user(tmp_path, "teammate9@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS9", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    add_member(tmp_path, ws["id"], teammate["id"], role="member")
    assert get_member_role(tmp_path, ws["id"], teammate["id"]) == "member"


def test_remove_member_revokes_access(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner10@example.com")
    teammate = _user(tmp_path, "teammate10@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS10", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    add_member(tmp_path, ws["id"], teammate["id"], role="member")
    assert get_member_role(tmp_path, ws["id"], teammate["id"]) == "member"

    remove_member(tmp_path, ws["id"], teammate["id"])
    assert get_member_role(tmp_path, ws["id"], teammate["id"]) is None
    assert get_workspaces_for_user(tmp_path, teammate["id"]) == []


# ── migration backfill ────────────────────────────────────────────────────────


def test_ensure_membership_tables_backfills_existing_owners(tmp_path: Path):
    """A workspace created before this feature existed (owner_id only, no
    membership row) must still be accessible to its owner after the
    migration runs again."""
    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    owner = _user(tmp_path, "legacy@example.com")
    # Simulate a pre-membership workspace: insert directly, skipping create_workspace's
    # membership insert (which doesn't exist without ensure_membership_tables first
    # and the workspace_members table not yet created).
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "jobs.db"))
    conn.execute(
        """INSERT INTO workspaces (id, slug, name, owner_id, target_url, product_name, team_role, config_path, created_at)
           VALUES ('legacy-ws', 'legacy', 'Legacy', ?, 'https://x.com', 'X', 'engineer', '', '2026-01-01T00:00:00+00:00')""",
        (owner["id"],),
    )
    conn.commit()
    conn.close()

    # Now run the migration that should backfill membership
    ensure_membership_tables(tmp_path)

    workspaces = get_workspaces_for_user(tmp_path, owner["id"])
    assert len(workspaces) == 1
    assert workspaces[0]["id"] == "legacy-ws"
    assert get_member_role(tmp_path, "legacy-ws", owner["id"]) == "owner"


def test_get_workspace_by_slug(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner11@example.com")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Argyle Workspace", target_url="https://argyle.com",
        product_name="Argyle", team_role="engineer",
    )
    found = get_workspace_by_slug(tmp_path, "argyle-workspace")
    assert found is not None
    assert found["name"] == "Argyle Workspace"


def test_get_workspace_by_slug_missing(tmp_path: Path):
    _setup(tmp_path)
    assert get_workspace_by_slug(tmp_path, "nonexistent") is None


def test_get_workspace_by_id(tmp_path: Path):
    _setup(tmp_path)
    owner = _user(tmp_path, "owner12@example.com")
    ws = create_workspace(
        tmp_path, owner_id=owner["id"], name="WS12", target_url="https://x.com",
        product_name="X", team_role="founder",
    )
    found = get_workspace_by_id(tmp_path, ws["id"])
    assert found is not None
    assert found["name"] == "WS12"


def test_get_workspace_by_id_missing(tmp_path: Path):
    _setup(tmp_path)
    assert get_workspace_by_id(tmp_path, "nonexistent") is None
