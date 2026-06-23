"""Workspace store — per-user workspaces in jobs.db."""

from __future__ import annotations

import datetime
import re
import sqlite3
import threading
import uuid
from pathlib import Path

# Default personas per team role
_PERSONAS_BY_ROLE: dict[str, list[dict]] = {
    "founder": [
        {"id": "p1-new-signup", "name": "New signup", "role": "first-time user",
         "goals": ["Complete signup and understand the product value", "Find the key feature fast"]},
        {"id": "p2-power-user", "name": "Power user", "role": "experienced user",
         "goals": ["Complete core tasks efficiently", "Explore advanced features"]},
        {"id": "p3-enterprise", "name": "Enterprise evaluator", "role": "buyer / evaluator",
         "goals": ["Assess security, compliance and team management", "Evaluate pricing and integrations"]},
    ],
    "qa-lead": [
        {"id": "p1-regression", "name": "Regression tester", "role": "QA persona",
         "goals": ["Rerun all known critical paths without regressions", "Verify form validation and error states"]},
        {"id": "p2-edge-case", "name": "Edge-case explorer", "role": "QA persona",
         "goals": ["Attempt unusual inputs and boundary conditions", "Test empty states and error recovery"]},
        {"id": "p3-a11y", "name": "Accessibility auditor", "role": "QA persona",
         "goals": ["Navigate all flows using keyboard only", "Verify screen-reader labels and ARIA roles"]},
    ],
    "engineer": [
        {"id": "p1-new-signup", "name": "New signup", "role": "first-time user",
         "goals": ["Complete onboarding and reach first success", "Identify missing docs or confusing steps"]},
        {"id": "p2-power-user", "name": "Power user", "role": "experienced user",
         "goals": ["Complete core tasks quickly", "Test integrations and API surfaces"]},
        {"id": "p3-dogfood", "name": "Developer dogfooder", "role": "internal engineer",
         "goals": ["Use dev-facing features and find rough edges", "Validate that error messages are actionable"]},
    ],
    "other": [
        {"id": "p1-new-signup", "name": "New signup", "role": "first-time user",
         "goals": ["Complete signup and understand the product value", "Find the key feature fast"]},
        {"id": "p2-power-user", "name": "Power user", "role": "experienced user",
         "goals": ["Complete core tasks efficiently", "Explore advanced features"]},
    ],
}


def _generate_config_yaml(
    configs_dir: Path,
    slug: str,
    target_url: str,
    product_name: str,
    team_role: str,
) -> Path:
    """Write a starter config YAML for a new workspace and return its path."""
    import urllib.parse
    parsed = urllib.parse.urlparse(target_url)
    allow_localhost = parsed.hostname in ("127.0.0.1", "localhost", "0.0.0.0")

    personas = _PERSONAS_BY_ROLE.get(team_role, _PERSONAS_BY_ROLE["other"])

    lines = [
        "run:",
        f"  target_url: {target_url}",
        f"  run_id_prefix: {slug}",
        f"  product_name: {product_name or slug}",
        "  viewports:",
        "  - desktop",
        "  - tablet",
        "  - mobile",
        f"  allow_localhost: {'true' if allow_localhost else 'false'}",
        "  persona_lens: true",
        "crawl:",
        "  enabled: true",
        "  max_depth: 2",
        "  max_pages: 24",
        "  supplement_journeys: true",
        "personas:",
    ]
    for p in personas:
        lines.append(f"- id: {p['id']}")
        lines.append(f"  name: {p['name']}")
        lines.append(f"  role: {p['role']}")
        lines.append("  goals:")
        for g in p["goals"]:
            lines.append(f"  - {g}")

    configs_dir.mkdir(parents=True, exist_ok=True)
    config_path = configs_dir / f"{slug}.yaml"
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path

_local = threading.local()
_write_lock = threading.Lock()


def _connect(artifacts_root: Path) -> sqlite3.Connection:
    if not hasattr(_local, "ws_conns"):
        _local.ws_conns = {}
    key = str(artifacts_root)
    if key not in _local.ws_conns:
        db_path = artifacts_root / "jobs.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        _local.ws_conns[key] = conn
    return _local.ws_conns[key]


def ensure_workspaces_table(artifacts_root: Path) -> None:
    """Create workspaces table if it does not exist (idempotent)."""
    conn = _connect(artifacts_root)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id           TEXT PRIMARY KEY,
            slug         TEXT UNIQUE NOT NULL,
            name         TEXT NOT NULL,
            owner_id     TEXT NOT NULL,
            target_url   TEXT NOT NULL DEFAULT '',
            product_name TEXT NOT NULL DEFAULT '',
            team_role    TEXT NOT NULL DEFAULT '',
            config_path  TEXT NOT NULL DEFAULT '',
            created_at   TEXT NOT NULL
        )
    """)
    # Migrate: add config_path column if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE workspaces ADD COLUMN config_path TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass
    # Migrate: add plan column — defaults every workspace to the design-partner
    # tier (unlimited runs during the 90-day design-partner phase) rather than
    # silently capping existing workspaces the moment this column appears.
    try:
        conn.execute("ALTER TABLE workspaces ADD COLUMN plan TEXT NOT NULL DEFAULT 'design_partner'")
    except Exception:
        pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_owner ON workspaces(owner_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_slug  ON workspaces(slug)")
    conn.commit()


def ensure_membership_tables(artifacts_root: Path) -> None:
    """Create workspace_members / workspace_invites tables and backfill owners.

    Single-owner workspaces predate this — every existing workspace's
    owner_id had no corresponding membership row. Backfill them as role
    'owner' so get_workspaces_for_user() (now membership-based) doesn't lose
    access for anyone already using the product.
    """
    conn = _connect(artifacts_root)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workspace_members (
            workspace_id TEXT NOT NULL,
            user_id      TEXT NOT NULL,
            role         TEXT NOT NULL DEFAULT 'member',
            joined_at    TEXT NOT NULL,
            PRIMARY KEY (workspace_id, user_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workspace_invites (
            token        TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            email        TEXT NOT NULL,
            role         TEXT NOT NULL DEFAULT 'member',
            invited_by   TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            accepted_at  TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_members_user ON workspace_members(user_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_invites_email ON workspace_invites(email)"
    )
    with _write_lock:
        rows = conn.execute("SELECT id, owner_id, created_at FROM workspaces").fetchall()
        for row in rows:
            conn.execute(
                """INSERT OR IGNORE INTO workspace_members (workspace_id, user_id, role, joined_at)
                   VALUES (?, ?, 'owner', ?)""",
                (row["id"], row["owner_id"], row["created_at"]),
            )
        conn.commit()


def get_members(artifacts_root: Path, workspace_id: str) -> list[dict]:
    """Active members of a workspace, joined with their user record."""
    conn = _connect(artifacts_root)
    rows = conn.execute(
        """SELECT m.user_id, m.role, m.joined_at, u.email, u.name
           FROM workspace_members m
           JOIN users u ON u.id = m.user_id
           WHERE m.workspace_id = ?
           ORDER BY m.joined_at ASC""",
        (workspace_id,),
    ).fetchall()
    return [
        {
            "userId": r["user_id"],
            "role": r["role"],
            "joinedAt": r["joined_at"],
            "email": r["email"],
            "name": r["name"],
        }
        for r in rows
    ]


def get_member_role(artifacts_root: Path, workspace_id: str, user_id: str) -> str | None:
    conn = _connect(artifacts_root)
    row = conn.execute(
        "SELECT role FROM workspace_members WHERE workspace_id = ? AND user_id = ?",
        (workspace_id, user_id),
    ).fetchone()
    return row["role"] if row else None


def add_member(
    artifacts_root: Path, workspace_id: str, user_id: str, role: str = "member"
) -> dict:
    conn = _connect(artifacts_root)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with _write_lock:
        conn.execute(
            """INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(workspace_id, user_id) DO UPDATE SET role = excluded.role""",
            (workspace_id, user_id, role, now),
        )
        conn.commit()
    return {"workspaceId": workspace_id, "userId": user_id, "role": role, "joinedAt": now}


def remove_member(artifacts_root: Path, workspace_id: str, user_id: str) -> None:
    conn = _connect(artifacts_root)
    with _write_lock:
        conn.execute(
            "DELETE FROM workspace_members WHERE workspace_id = ? AND user_id = ?",
            (workspace_id, user_id),
        )
        conn.commit()


def create_invite(
    artifacts_root: Path,
    workspace_id: str,
    email: str,
    role: str,
    invited_by: str,
) -> dict:
    conn = _connect(artifacts_root)
    token = uuid.uuid4().hex
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with _write_lock:
        conn.execute(
            """INSERT INTO workspace_invites (token, workspace_id, email, role, invited_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (token, workspace_id, email.strip().lower(), role, invited_by, now),
        )
        conn.commit()
    return {
        "token": token,
        "workspaceId": workspace_id,
        "email": email.strip().lower(),
        "role": role,
        "createdAt": now,
    }


def get_invite(artifacts_root: Path, token: str) -> dict | None:
    conn = _connect(artifacts_root)
    row = conn.execute(
        "SELECT * FROM workspace_invites WHERE token = ?", (token,)
    ).fetchone()
    if not row:
        return None
    return {
        "token": row["token"],
        "workspaceId": row["workspace_id"],
        "email": row["email"],
        "role": row["role"],
        "invitedBy": row["invited_by"],
        "createdAt": row["created_at"],
        "acceptedAt": row["accepted_at"],
    }


def list_invites(artifacts_root: Path, workspace_id: str) -> list[dict]:
    conn = _connect(artifacts_root)
    rows = conn.execute(
        "SELECT * FROM workspace_invites WHERE workspace_id = ? AND accepted_at IS NULL ORDER BY created_at ASC",
        (workspace_id,),
    ).fetchall()
    return [
        {
            "token": r["token"],
            "email": r["email"],
            "role": r["role"],
            "createdAt": r["created_at"],
        }
        for r in rows
    ]


def accept_invite(artifacts_root: Path, token: str, user_id: str) -> dict | None:
    """Mark an invite accepted and add the accepting user as a member.

    Returns the workspace_members row, or None if the token is invalid or
    already accepted.
    """
    invite = get_invite(artifacts_root, token)
    if not invite or invite["acceptedAt"]:
        return None
    conn = _connect(artifacts_root)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with _write_lock:
        conn.execute(
            "UPDATE workspace_invites SET accepted_at = ? WHERE token = ?", (now, token)
        )
        conn.commit()
    return add_member(artifacts_root, invite["workspaceId"], user_id, invite["role"])


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug or "workspace"


def _unique_slug(conn: sqlite3.Connection, base: str) -> str:
    slug = base
    for i in range(1, 100):
        row = conn.execute("SELECT id FROM workspaces WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return slug
        slug = f"{base}-{i}"
    return f"{base}-{uuid.uuid4().hex[:6]}"


def create_workspace(
    artifacts_root: Path,
    owner_id: str,
    name: str,
    target_url: str,
    product_name: str,
    team_role: str,
) -> dict:
    uid = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = _connect(artifacts_root)
    with _write_lock:
        slug = _unique_slug(conn, _slugify(name))
        # Auto-generate config YAML for this workspace
        configs_dir = artifacts_root / "configs"
        config_path = _generate_config_yaml(
            configs_dir=configs_dir,
            slug=slug,
            target_url=target_url.strip(),
            product_name=(product_name or name).strip(),
            team_role=team_role.strip(),
        )
        conn.execute(
            """INSERT INTO workspaces
               (id, slug, name, owner_id, target_url, product_name, team_role, config_path, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid, slug, name.strip(), owner_id, target_url.strip(),
             product_name.strip(), team_role.strip(), str(config_path), now),
        )
        conn.execute(
            """INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
               VALUES (?, ?, 'owner', ?)""",
            (uid, owner_id, now),
        )
        conn.commit()
    return _row_to_dict(conn.execute(
        "SELECT * FROM workspaces WHERE id = ?", (uid,)
    ).fetchone())


def get_workspace_by_slug(artifacts_root: Path, slug: str) -> dict | None:
    conn = _connect(artifacts_root)
    row = conn.execute("SELECT * FROM workspaces WHERE slug = ?", (slug,)).fetchone()
    return _row_to_dict(row) if row else None


def get_workspace_by_id(artifacts_root: Path, workspace_id: str) -> dict | None:
    conn = _connect(artifacts_root)
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return _row_to_dict(row) if row else None


def set_workspace_plan(artifacts_root: Path, slug: str, plan: str) -> dict | None:
    """Update a workspace's billing plan (called from the Stripe webhook handler)."""
    conn = _connect(artifacts_root)
    with _write_lock:
        conn.execute("UPDATE workspaces SET plan = ? WHERE slug = ?", (plan, slug))
        conn.commit()
    return get_workspace_by_slug(artifacts_root, slug)


def get_workspaces_for_user(artifacts_root: Path, user_id: str) -> list[dict]:
    """Workspaces this user can access — owned or invited-and-joined.

    Membership-based rather than owner_id-only, so an invited teammate sees
    the same workspace under their own login instead of needing the owner's
    shared credentials.
    """
    conn = _connect(artifacts_root)
    rows = conn.execute(
        """SELECT w.* FROM workspaces w
           JOIN workspace_members m ON m.workspace_id = w.id
           WHERE m.user_id = ?
           ORDER BY w.created_at ASC""",
        (user_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def sync_target_url_for_config_path(artifacts_root: Path, config_path: Path, target_url: str) -> None:
    """Keep workspaces.target_url in sync with the config YAML it points to.

    The workspace table caches target_url separately from the config YAML's
    own run.target_url — editing the YAML alone (e.g. via the settings
    endpoint) leaves the cached column stale, so the UI keeps showing the old
    URL even after the underlying config is fixed. Call this any time a
    config's target_url is written so the two can't drift apart.
    """
    conn = _connect(artifacts_root)
    with _write_lock:
        conn.execute(
            "UPDATE workspaces SET target_url = ? WHERE config_path = ?",
            (target_url, str(config_path)),
        )
        conn.commit()


def backfill_config_paths(artifacts_root: Path, workspaces: list[dict]) -> list[dict]:
    """For workspaces missing a configPath, generate their config YAML now."""
    conn = _connect(artifacts_root)
    updated = []
    for ws in workspaces:
        if ws.get("configPath"):
            updated.append(ws)
            continue
        # Generate config and update DB row
        try:
            config_path = _generate_config_yaml(
                configs_dir=artifacts_root / "configs",
                slug=ws["slug"],
                target_url=ws["targetUrl"],
                product_name=ws["productName"],
                team_role=ws["teamRole"],
            )
            with _write_lock:
                conn.execute(
                    "UPDATE workspaces SET config_path = ? WHERE id = ?",
                    (str(config_path), ws["id"]),
                )
                conn.commit()
            ws = {**ws, "configPath": str(config_path)}
        except Exception:
            pass
        updated.append(ws)
    return updated


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "ownerId": row["owner_id"],
        "targetUrl": row["target_url"],
        "productName": row["product_name"],
        "teamRole": row["team_role"],
        "configPath": row["config_path"],
        "createdAt": row["created_at"],
        "plan": row["plan"] if "plan" in row.keys() else "design_partner",
    }
