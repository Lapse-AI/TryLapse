"""Load .env files into os.environ (does not override existing vars)."""

from __future__ import annotations

import os
from pathlib import Path


def _parse_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[7:].strip()
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip().strip("'").strip('"')
    if not key:
        return None
    return key, value


def load_dotenv_files(*, start: Path | None = None) -> list[Path]:
    """Walk up from start (or cwd) and load the first .env files found (max 3 levels)."""
    loaded: list[Path] = []
    cur = (start or Path.cwd()).resolve()
    for _ in range(4):
        env_path = cur / ".env"
        if env_path.is_file():
            for raw in env_path.read_text(encoding="utf-8").splitlines():
                parsed = _parse_line(raw)
                if not parsed:
                    continue
                key, value = parsed
                os.environ.setdefault(key, value)
            loaded.append(env_path)
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return loaded
