"""Persistent per-run chat threads (NLU-4)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _chat_path(artifacts_root: Path, run_id: str) -> Path:
    safe = run_id.replace("/", "_")
    return artifacts_root / "chats" / f"{safe}.json"


def load_chat_thread(artifacts_root: Path, run_id: str) -> dict[str, Any]:
    path = _chat_path(artifacts_root, run_id)
    if not path.is_file():
        return {"runId": run_id, "turns": [], "updatedAt": None}
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            data.setdefault("runId", run_id)
            data.setdefault("turns", [])
            return data
    except json.JSONDecodeError:
        pass
    return {"runId": run_id, "turns": [], "updatedAt": None}


def save_chat_turn(
    artifacts_root: Path,
    run_id: str,
    *,
    user_message: str,
    assistant_reply: str,
    source: str,
) -> dict[str, Any]:
    thread = load_chat_thread(artifacts_root, run_id)
    now = datetime.now(timezone.utc).isoformat()
    thread["turns"].append(
        {"role": "user", "content": user_message, "at": now},
    )
    thread["turns"].append(
        {"role": "assistant", "content": assistant_reply, "at": now, "source": source},
    )
    thread["updatedAt"] = now
    path = _chat_path(artifacts_root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(thread, indent=2))
    return thread


def chat_history_for_llm(thread: dict[str, Any], *, max_turns: int = 12) -> list[dict[str, str]]:
    turns = thread.get("turns") or []
    out: list[dict[str, str]] = []
    for t in turns[-max_turns:]:
        role = t.get("role")
        content = str(t.get("content", ""))[:2000]
        if role in ("user", "assistant") and content:
            out.append({"role": role, "content": content})
    return out
