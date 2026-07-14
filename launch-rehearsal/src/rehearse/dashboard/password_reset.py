"""Password reset — token-based password recovery (no external email service)."""

from __future__ import annotations

import datetime
import hashlib
import secrets
import sqlite3
import time
import uuid
from pathlib import Path

_TOKEN_EXPIRY_SECONDS = 60 * 60 * 24  # 24 hours
_write_lock = __import__("threading").Lock()


def _connect(artifacts_root: Path) -> sqlite3.Connection:
    """Return a connection to jobs.db for password reset tokens."""
    db_path = artifacts_root / "jobs.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_reset_tokens_table(artifacts_root: Path) -> None:
    """Create password_reset_tokens table if it doesn't exist."""
    conn = _connect(artifacts_root)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id         TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            email      TEXT NOT NULL,
            token      TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used       INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reset_tokens_user ON password_reset_tokens(user_id)")
    conn.commit()
    conn.close()


def create_reset_token(artifacts_root: Path, user_id: str, email: str) -> str:
    """Generate a password reset token and store it. Returns the token."""
    token = secrets.token_urlsafe(32)
    token_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=_TOKEN_EXPIRY_SECONDS)
    expires_iso = expires.isoformat()

    conn = _connect(artifacts_root)
    with _write_lock:
        conn.execute(
            """INSERT INTO password_reset_tokens (id, user_id, email, token, created_at, expires_at, used)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (token_id, user_id, email, token, now, expires_iso),
        )
        conn.commit()
    conn.close()

    # Log token for console/testing (in production, send via email).
    # flush=True so it appears in Railway/container logs immediately
    # (stdout is block-buffered when not a TTY).
    print(
        f"\n🔐 PASSWORD RESET TOKEN\n   Email: {email}\n   Token: {token}\n"
        f"   Expires: {expires.strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
        flush=True,
    )

    return token


def validate_reset_token(artifacts_root: Path, token: str) -> dict | None:
    """Validate a reset token. Returns {user_id, email} or None if invalid/expired."""
    conn = _connect(artifacts_root)
    row = conn.execute(
        """SELECT user_id, email, expires_at, used FROM password_reset_tokens
           WHERE token = ?""",
        (token,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    # Check if token is expired
    expires_at = datetime.datetime.fromisoformat(row["expires_at"])
    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
        return None

    # Check if token was already used
    if row["used"]:
        return None

    return {"user_id": row["user_id"], "email": row["email"]}


def consume_reset_token(artifacts_root: Path, token: str) -> None:
    """Mark a reset token as used (one-time use only)."""
    conn = _connect(artifacts_root)
    with _write_lock:
        conn.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE token = ?",
            (token,),
        )
        conn.commit()
    conn.close()


def cleanup_expired_tokens(artifacts_root: Path) -> int:
    """Delete expired tokens. Returns count of deleted tokens."""
    conn = _connect(artifacts_root)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with _write_lock:
        cursor = conn.execute(
            "DELETE FROM password_reset_tokens WHERE expires_at < ?",
            (now,),
        )
        count = cursor.rowcount
        conn.commit()
    conn.close()
    return count
