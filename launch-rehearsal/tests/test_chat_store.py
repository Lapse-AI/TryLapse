from pathlib import Path

from rehearse.dashboard.chat_store import load_chat_thread, save_chat_turn


def test_chat_persistence(tmp_path: Path):
    root = tmp_path / "artifacts"
    root.mkdir()
    save_chat_turn(
        root,
        "run-1",
        user_message="What blocked readiness?",
        assistant_reply="No P1 blockers.",
        source="template",
    )
    thread = load_chat_thread(root, "run-1")
    assert len(thread["turns"]) == 2
    assert thread["turns"][0]["role"] == "user"
