"""User authentication — SQLite users table, PBKDF2 passwords, HS256 JWT (stdlib only).

No external dependencies.  Everything uses Python's built-in hashlib, hmac,
base64, secrets, sqlite3, and json modules.

Environment variables
---------------------
REHEARSE_JWT_SECRET   64-char hex string used to sign tokens.
                      Falls back to a process-scoped random value in dev
                      (all sessions are invalidated on server restart).
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# JWT secret
# ---------------------------------------------------------------------------
_JWT_SECRET: str = os.environ.get("REHEARSE_JWT_SECRET") or secrets.token_hex(32)
_JWT_EXPIRY_SECONDS = 60 * 60 * 24 * 30  # 30 days

_local = threading.local()
_write_lock = threading.Lock()


# ---------------------------------------------------------------------------
# DB connection (same jobs.db as job_store, different thread-local cache key)
# ---------------------------------------------------------------------------

def _connect(artifacts_root: Path) -> sqlite3.Connection:
    """Return a per-thread connection to jobs.db, creating schema if needed."""
    if not hasattr(_local, "auth_conns"):
        _local.auth_conns = {}
    key = str(artifacts_root)
    if key not in _local.auth_conns:
        db_path = artifacts_root / "jobs.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Longer timeout (30s) for concurrent write operations
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        # Allow readers to run alongside writers (WAL mode)
        conn.execute("PRAGMA query_only=OFF")
        _local.auth_conns[key] = conn
    return _local.auth_conns[key]


def ensure_users_table(artifacts_root: Path) -> None:
    """Create users table if it does not already exist (idempotent)."""
    conn = _connect(artifacts_root)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         TEXT PRIMARY KEY,
            email      TEXT UNIQUE NOT NULL,
            name       TEXT NOT NULL DEFAULT '',
            pw_hash    TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.commit()


# ---------------------------------------------------------------------------
# Password hashing — PBKDF2-HMAC-SHA256 (OWASP recommended ≥ 210 000 iters)
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000
    )
    return f"pbkdf2:sha256:260000:{salt}:{dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        _, _, iters_str, salt, dk_hex = stored.split(":")
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iters_str)
        )
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT — HS256, stdlib only
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = (-len(s)) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def _make_jwt(payload: dict) -> str:
    header = _b64url_encode(b'{"alg":"HS256","typ":"JWT"}')
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header}.{body}".encode("ascii")
    sig = hmac.new(
        _JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"


def _decode_jwt(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig_b64 = parts
        signing_input = f"{header}.{body}".encode("ascii")
        expected = hmac.new(
            _JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()
        actual = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected, actual):
            return None
        payload = json.loads(_b64url_decode(body))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_user(
    artifacts_root: Path,
    email: str,
    password: str,
    name: str,
) -> dict | None:
    """Insert a new user row.

    Returns ``{"id", "email", "name"}`` on success, or ``None`` if the email
    is already registered.
    """
    if not email or not password:
        return None
    email_clean = email.strip().lower()
    name_clean = name.strip() or email_clean.split("@")[0]
    uid = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pw_hash = _hash_password(password)

    # Retry up to 3 times on database lock
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = _connect(artifacts_root)
            with _write_lock:
                conn.execute(
                    "INSERT INTO users (id, email, name, pw_hash, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (uid, email_clean, name_clean, pw_hash, now),
                )
                conn.commit()
            return {"id": uid, "email": email_clean, "name": name_clean}
        except sqlite3.IntegrityError:
            return None  # email already taken
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                continue
            raise


def authenticate_user(
    artifacts_root: Path,
    email: str,
    password: str,
) -> dict | None:
    """Verify credentials.

    Returns ``{"id", "email", "name"}`` on success, or ``None`` if the email
    is not found or the password is wrong.  Uses a constant-time dummy hash
    check when the email is not found to resist timing-based enumeration.
    """
    if not email or not password:
        return None
    email_clean = email.strip().lower()
    conn = _connect(artifacts_root)
    row = conn.execute(
        "SELECT id, email, name, pw_hash FROM users WHERE email = ?",
        (email_clean,),
    ).fetchone()
    if not row:
        # Constant-time dummy check — prevent email enumeration via timing
        _verify_password(password, "pbkdf2:sha256:260000:00000000:00000000")
        return None
    if not _verify_password(password, row["pw_hash"]):
        return None
    return {"id": row["id"], "email": row["email"], "name": row["name"]}


def get_user(artifacts_root: Path, user_id: str) -> dict | None:
    """Look up a user by id. Returns ``{"id", "email", "name"}`` or ``None``."""
    conn = _connect(artifacts_root)
    row = conn.execute(
        "SELECT id, email, name FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "name": row[2]}


def list_all_users(artifacts_root: Path) -> list[dict]:
    """All signed-up users, newest first. Admin/company-overview use only —
    never expose this to a non-admin caller."""
    conn = _connect(artifacts_root)
    rows = conn.execute(
        "SELECT id, email, name, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    return [
        {"id": r["id"], "email": r["email"], "name": r["name"], "createdAt": r["created_at"]}
        for r in rows
    ]


def update_user(
    artifacts_root: Path,
    user_id: str,
    *,
    name: str | None = None,
    password: str | None = None,
    current_password: str | None = None,
) -> dict | None:
    """Update a user's name and/or password.

    A password change requires ``current_password`` to verify against the
    stored hash — name-only changes do not. Returns the updated
    ``{"id", "email", "name"}`` record, or ``None`` if the user doesn't exist
    or the current password check fails.
    """
    conn = _connect(artifacts_root)
    row = conn.execute(
        "SELECT id, email, name, pw_hash FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not row:
        return None
    _, email, existing_name, pw_hash = row

    if password:
        if not current_password or not _verify_password(current_password, pw_hash):
            return None
        pw_hash = _hash_password(password)

    new_name = name.strip() if name and name.strip() else existing_name

    with _write_lock:
        conn.execute(
            "UPDATE users SET name = ?, pw_hash = ? WHERE id = ?",
            (new_name, pw_hash, user_id),
        )
        conn.commit()
    return {"id": user_id, "email": email, "name": new_name}


def issue_token(user: dict) -> str:
    """Return a signed 30-day JWT for *user* (dict with id/email/name)."""
    now = int(time.time())
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "iat": now,
        "exp": now + _JWT_EXPIRY_SECONDS,
    }
    return _make_jwt(payload)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT.  Returns the payload dict or ``None``."""
    return _decode_jwt(token)
