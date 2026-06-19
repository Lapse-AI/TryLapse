"""Per-finding outcome store — severity calibration training data.

Each record captures a developer's judgment about a finding:
  acted_on     — we fixed this, it was real
  dismissed    — we looked at it, not worth fixing
  false_positive — tool was wrong, this isn't a real issue
  deferred     — real but not now

These records are the ground truth for future severity calibration.
Stored in finding_outcomes.json under artifacts_root.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_FILENAME = "finding_outcomes.json"
_VALID_OUTCOMES = {"acted_on", "dismissed", "false_positive", "deferred"}


def _path(artifacts_root: Path) -> Path:
    return artifacts_root / _FILENAME


def _load(artifacts_root: Path) -> list[dict[str, Any]]:
    p = _path(artifacts_root)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(artifacts_root: Path, records: list[dict[str, Any]]) -> None:
    store_path = _path(artifacts_root)
    tmp = store_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(records, indent=2))
    os.replace(tmp, store_path)


def record_finding_outcome(
    artifacts_root: Path,
    run_id: str,
    finding_id: str,
    outcome: str,
) -> dict[str, Any]:
    """Upsert a finding outcome. Returns the saved record."""
    run_id = run_id.strip()
    finding_id = finding_id.strip()
    if not run_id or not finding_id:
        raise ValueError("run_id and finding_id are required")
    if outcome not in _VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(_VALID_OUTCOMES)}")

    key = (run_id, finding_id)
    record: dict[str, Any] = {
        "runId": run_id,
        "findingId": finding_id,
        "outcome": outcome,
        "labeledAt": datetime.now(timezone.utc).isoformat(),
    }

    records = _load(artifacts_root)
    records = [r for r in records if (r.get("runId"), r.get("findingId")) != key]
    records.append(record)
    _save(artifacts_root, records)
    return record


def get_finding_outcomes_for_run(
    artifacts_root: Path,
    run_id: str,
) -> dict[str, str]:
    """Return {finding_id: outcome} for all labeled findings in a run."""
    records = _load(artifacts_root)
    return {
        r["findingId"]: r["outcome"]
        for r in records
        if r.get("runId") == run_id and r.get("findingId") and r.get("outcome")
    }


def list_all_outcomes(artifacts_root: Path) -> list[dict[str, Any]]:
    """Return all outcome records — used for calibration data export."""
    return sorted(_load(artifacts_root), key=lambda r: r.get("labeledAt", ""), reverse=True)
