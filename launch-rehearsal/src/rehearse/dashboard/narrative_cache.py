"""Disk cache for aggregate NLU narratives — avoid repeat LLM calls on page load."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _cache_dir(artifacts_root: Path) -> Path:
    d = artifacts_root / "narratives"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _fingerprint(parts: list[str]) -> str:
    blob = "|".join(parts)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_cached(artifacts_root: Path, name: str, fingerprint: str) -> dict[str, Any] | None:
    path = _cache_dir(artifacts_root) / f"{name}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
        if data.get("fingerprint") == fingerprint and isinstance(data.get("narrative"), dict):
            return data["narrative"]
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_cached(
    artifacts_root: Path,
    name: str,
    fingerprint: str,
    narrative: dict[str, Any],
) -> None:
    path = _cache_dir(artifacts_root) / f"{name}.json"
    path.write_text(
        json.dumps({"fingerprint": fingerprint, "narrative": narrative}, indent=2)
    )


def digest_fingerprint(summaries: list[dict[str, Any]], *, limit: int) -> str:
    ids = [s.get("id", "") for s in summaries[:limit]]
    return _fingerprint(["digest", str(limit), *ids])


def trends_fingerprint(summaries: list[dict[str, Any]]) -> str:
    ids = [s.get("id", "") for s in summaries]
    return _fingerprint(["trends", *ids])


def diff_fingerprint(run_a: str, run_b: str) -> str:
    return _fingerprint(["diff", run_a, run_b])
