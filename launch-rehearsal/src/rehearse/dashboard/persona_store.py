"""Persona Library store — persists reusable persona definitions across configs.

Personas live in ``artifacts/personas.json`` as a flat list.  Each entry is a
dict with the same shape as a persona inside a YAML config, plus two extra fields:

    id              str   — stable slug, e.g. "lib-persona-senior-hr-manager"
    name            str
    role            str
    goals           list[str]
    enabled         bool   — always True in the library; config can override
    tech_literacy   str   — "novice" | "intermediate" | "expert"
    patience        str   — "low" | "medium" | "high"
    trust_level     str   — "skeptical" | "neutral" | "trusting"
    character       str   — free-text psychological texture
    usage_context   str   — e.g. "first-time user", "switching from Competitor X"
    tags            list[str]   — user-defined labels for filtering
    source          str   — "manual" | "ai-generated" | "imported-from-config"
    created_at      str   — ISO-8601 UTC
    updated_at      str   — ISO-8601 UTC

Design notes
------------
- JSON flat file is intentional: simple, human-readable, git-diffable.
- No UUID auto-increment: caller supplies the id so that config imports are
  idempotent (re-importing the same persona from a config always lands at the
  same library id).
- The ``source`` field is purely informational; it does NOT gate behaviour.
- All mutations go through save_persona() which atomically rewrites the file
  under a threading.Lock — safe for the single-process rehearse server.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_PERSONAS_FILE = "personas.json"

_DEFAULTS = {
    "enabled": True,
    "tech_literacy": "intermediate",
    "patience": "medium",
    "trust_level": "neutral",
    "character": "",
    "usage_context": "",
    "tags": [],
    "source": "manual",
}


# ── Path helper ──────────────────────────────────────────────────────────────

def _path(artifacts_root: Path) -> Path:
    return artifacts_root / _PERSONAS_FILE


# ── Read ─────────────────────────────────────────────────────────────────────

def list_personas(artifacts_root: Path) -> list[dict[str, Any]]:
    """Return all library personas, newest first."""
    p = _path(artifacts_root)
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text())
        personas = data if isinstance(data, list) else data.get("personas", [])
        # Sort by updated_at descending so UI shows most recently touched first
        return sorted(personas, key=lambda x: x.get("updated_at", ""), reverse=True)
    except Exception:
        return []


def get_persona(artifacts_root: Path, persona_id: str) -> dict[str, Any] | None:
    return next((p for p in list_personas(artifacts_root) if p["id"] == persona_id), None)


# ── Write ─────────────────────────────────────────────────────────────────────

def save_persona(artifacts_root: Path, persona: dict[str, Any]) -> dict[str, Any]:
    """Upsert a persona by id.  Returns the saved record.

    If the persona has no ``id``, one is generated from the name.
    Missing fields are filled with safe defaults so callers only need to supply
    the fields they know about.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Ensure id exists
    if not persona.get("id"):
        base = re.sub(r"[^a-z0-9]+", "-", (persona.get("name") or "persona").lower()).strip("-")
        persona["id"] = f"lib-{base}"

    # Fill defaults for any missing behavioral fields
    for key, default in _DEFAULTS.items():
        if key not in persona:
            persona[key] = default

    with _lock:
        existing = list_personas(artifacts_root)
        idx = next((i for i, p in enumerate(existing) if p["id"] == persona["id"]), None)

        if idx is not None:
            # Preserve created_at from the existing record
            persona.setdefault("created_at", existing[idx].get("created_at", now))
            persona["updated_at"] = now
            existing[idx] = persona
        else:
            persona.setdefault("created_at", now)
            persona["updated_at"] = now
            existing.append(persona)

        _path(artifacts_root).write_text(json.dumps(existing, indent=2))

    return persona


def delete_persona(artifacts_root: Path, persona_id: str) -> bool:
    """Remove a persona by id.  Returns True if it existed."""
    with _lock:
        existing = list_personas(artifacts_root)
        new_list = [p for p in existing if p["id"] != persona_id]
        if len(new_list) == len(existing):
            return False
        _path(artifacts_root).write_text(json.dumps(new_list, indent=2))
    return True


# ── Import from config ────────────────────────────────────────────────────────

def import_from_config(
    artifacts_root: Path,
    config_personas: list[dict[str, Any]],
    *,
    product_slug: str = "",
) -> list[dict[str, Any]]:
    """Bulk-import personas from a YAML config into the library.

    IDs are derived deterministically from the product slug + persona id so
    that re-importing is idempotent: running this twice for the same config
    produces one library entry, not two.

    Returns the list of saved persona records.
    """
    saved = []
    for p in config_personas:
        lib_entry = dict(p)
        # Namespace the id so it doesn't collide with personas from other products
        raw_id = p.get("id") or re.sub(r"[^a-z0-9]+", "-", (p.get("name") or "persona").lower())
        if product_slug:
            lib_entry["id"] = f"lib-{product_slug}-{raw_id}".lower()
        else:
            lib_entry["id"] = f"lib-{raw_id}".lower()
        lib_entry["source"] = "imported-from-config"
        lib_entry.setdefault("tags", [product_slug] if product_slug else [])
        saved.append(save_persona(artifacts_root, lib_entry))
    return saved
