from pathlib import Path

from rehearse.narrative import build_template_command_digest


def test_command_digest_empty():
    d = build_template_command_digest([])
    assert "No runs" in d["headline"]


def test_command_digest_with_summaries():
    summaries = [
        {"id": "b", "readiness": "Green", "issues": 2, "pages": 10},
        {"id": "a", "readiness": "Amber", "issues": 4, "pages": 8},
    ]
    d = build_template_command_digest(summaries)
    assert d["latestRunId"] == "b"
    assert len(d["bullets"]) >= 1
