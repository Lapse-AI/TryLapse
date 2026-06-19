"""HMAC-signed, time-limited URLs for sharing artifacts outside the dashboard.

The /files/ endpoint is otherwise unauthenticated — these signatures let a
specific file be shared (e.g. in a Slack message) without opening up the
whole artifacts tree, and the link stops working after ttl_seconds.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from pathlib import Path

_SECRET_FILE = ".signing_secret"


def _get_secret(artifacts_root: Path) -> bytes:
    env_secret = os.environ.get("REHEARSE_SIGNING_SECRET")
    if env_secret:
        return env_secret.encode("utf-8")
    secret_path = artifacts_root / _SECRET_FILE
    if secret_path.is_file():
        try:
            return secret_path.read_bytes()
        except Exception:
            pass
    secret = os.urandom(32)
    try:
        artifacts_root.mkdir(parents=True, exist_ok=True)
        secret_path.write_bytes(secret)
    except Exception:
        pass
    return secret


def _sign(rel_path: str, exp: int, secret: bytes) -> str:
    msg = f"{rel_path}:{exp}".encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def sign_path(artifacts_root: Path, rel_path: str, *, ttl_seconds: int = 86400) -> tuple[str, int]:
    """Return (signature, expiry_epoch) for rel_path, valid for ttl_seconds."""
    secret = _get_secret(artifacts_root)
    exp = int(time.time()) + ttl_seconds
    return _sign(rel_path, exp, secret), exp


def verify_signature(artifacts_root: Path, rel_path: str, sig: str | None, exp: str | int | None) -> bool:
    if not sig or exp is None:
        return False
    try:
        exp_int = int(exp)
    except (TypeError, ValueError):
        return False
    if exp_int < int(time.time()):
        return False
    secret = _get_secret(artifacts_root)
    expected = _sign(rel_path, exp_int, secret)
    return hmac.compare_digest(expected, sig)


def build_signed_file_url(
    artifacts_root: Path, rel_path: str, *, base_url: str = "", ttl_seconds: int = 86400
) -> str:
    sig, exp = sign_path(artifacts_root, rel_path, ttl_seconds=ttl_seconds)
    return f"{base_url}/files/{rel_path}?sig={sig}&exp={exp}"
