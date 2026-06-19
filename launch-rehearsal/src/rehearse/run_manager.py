"""Explicit run state machine — atomic state transitions, no partial-run observability.

Every run passes through exactly:
  QUEUED → CRAWLING → RUNNING → SYNTHESIZING → COMPLETE
       ↓         ↓          ↓             ↓
     FAILED    FAILED    FAILED        FAILED

Transitions are logged with timestamps to runs/{run_id}-state.json.
On process restart, any run still in a non-terminal state is treated as FAILED.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Terminal states — no further transitions allowed
_TERMINAL = {"COMPLETE", "FAILED"}

# Valid forward transitions
_TRANSITIONS: dict[str, set[str]] = {
    "QUEUED":       {"CRAWLING", "FAILED"},
    "CRAWLING":     {"RUNNING", "FAILED"},
    "RUNNING":      {"SYNTHESIZING", "FAILED"},
    "SYNTHESIZING": {"COMPLETE", "FAILED"},
}


class RunStateMachineError(Exception):
    pass


class RunStateMachine:
    """Owns all state transitions for one run. One instance per run."""

    def __init__(self, run_id: str, runs_dir: Path) -> None:
        self.run_id = run_id
        self._state_path = runs_dir / f"{run_id}-state.json"
        self._log: list[dict[str, Any]] = []
        self._current: str = "QUEUED"

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def recover_stale(cls, runs_dir: Path) -> list[str]:
        """Mark any non-terminal runs as FAILED on process restart.

        Returns list of run_ids that were recovered (useful for logging).
        """
        recovered: list[str] = []
        for path in runs_dir.glob("*-state.json"):
            try:
                data = json.loads(path.read_text())
                if data.get("state") not in _TERMINAL:
                    data["state"] = "FAILED"
                    data["log"].append({
                        "from": data.get("state", "UNKNOWN"),
                        "to": "FAILED",
                        "at": _now(),
                        "reason": "process restart — run was not in terminal state",
                    })
                    _atomic_write(path, data)
                    recovered.append(data.get("run_id", path.stem.replace("-state", "")))
            except Exception:
                pass
        return recovered

    def start(self) -> None:
        """Initialize state file in QUEUED state."""
        data: dict[str, Any] = {
            "run_id": self.run_id,
            "state": "QUEUED",
            "log": [{"from": None, "to": "QUEUED", "at": _now(), "reason": "run queued"}],
        }
        _atomic_write(self._state_path, data)
        self._log = data["log"]

    def transition(self, new_state: str, *, reason: str = "") -> None:
        """Advance to new_state. Raises if the transition is not allowed."""
        if self._current in _TERMINAL:
            raise RunStateMachineError(
                f"Run {self.run_id} is already in terminal state {self._current!r} — "
                f"cannot transition to {new_state!r}"
            )
        allowed = _TRANSITIONS.get(self._current, set())
        if new_state not in allowed:
            raise RunStateMachineError(
                f"Invalid transition {self._current!r} → {new_state!r} for run {self.run_id}. "
                f"Allowed: {sorted(allowed)}"
            )
        entry = {"from": self._current, "to": new_state, "at": _now(), "reason": reason}
        self._log.append(entry)
        self._current = new_state
        _atomic_write(self._state_path, {
            "run_id": self.run_id,
            "state": new_state,
            "log": self._log,
        })

    def fail(self, reason: str = "") -> None:
        """Unconditionally transition to FAILED from any non-terminal state."""
        if self._current in _TERMINAL:
            return  # already terminal — no-op
        entry = {"from": self._current, "to": "FAILED", "at": _now(), "reason": reason or "run failed"}
        self._log.append(entry)
        self._current = "FAILED"
        _atomic_write(self._state_path, {
            "run_id": self.run_id,
            "state": "FAILED",
            "log": self._log,
        })

    @property
    def state(self) -> str:
        return self._current

    @property
    def is_terminal(self) -> bool:
        return self._current in _TERMINAL

    # ── Context-manager helpers ───────────────────────────────────────────────

    def __enter__(self) -> RunStateMachine:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is not None and not self.is_terminal:
            self.fail(reason=f"{exc_type.__name__}: {exc_val!s:.200}")
        return False  # never suppress exceptions


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically — reader never sees a partial file."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)  # atomic on POSIX; near-atomic on Windows
