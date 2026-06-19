"""Tests for RunStateMachine — explicit run state transitions."""

import json
import pytest
from pathlib import Path

from rehearse.run_manager import RunStateMachine, RunStateMachineError


def test_happy_path(tmp_path):
    sm = RunStateMachine("run-001", tmp_path)
    sm.start()
    assert sm.state == "QUEUED"

    sm.transition("CRAWLING", reason="crawl start")
    sm.transition("RUNNING", reason="journey start")
    sm.transition("SYNTHESIZING", reason="analysis start")
    sm.transition("COMPLETE", reason="done")

    assert sm.state == "COMPLETE"
    assert sm.is_terminal

    state_file = tmp_path / "run-001-state.json"
    data = json.loads(state_file.read_text())
    assert data["state"] == "COMPLETE"
    assert len(data["log"]) == 5  # QUEUED + 4 transitions


def test_invalid_transition_raises(tmp_path):
    sm = RunStateMachine("run-002", tmp_path)
    sm.start()
    with pytest.raises(RunStateMachineError, match="Invalid transition"):
        sm.transition("SYNTHESIZING")  # skips CRAWLING and RUNNING


def test_fail_from_any_state(tmp_path):
    sm = RunStateMachine("run-003", tmp_path)
    sm.start()
    sm.transition("CRAWLING")
    sm.fail(reason="crawler crashed")
    assert sm.state == "FAILED"
    assert sm.is_terminal

    # Further transitions should no-op (fail) gracefully
    sm.fail(reason="double fail")  # should not raise
    assert sm.state == "FAILED"


def test_terminal_transition_raises(tmp_path):
    sm = RunStateMachine("run-004", tmp_path)
    sm.start()
    sm.transition("CRAWLING")
    sm.transition("RUNNING")
    sm.transition("SYNTHESIZING")
    sm.transition("COMPLETE")
    with pytest.raises(RunStateMachineError, match="terminal state"):
        sm.transition("FAILED")


def test_context_manager_fails_on_exception(tmp_path):
    sm = RunStateMachine("run-005", tmp_path)
    sm.start()
    sm.transition("CRAWLING")
    try:
        with sm:
            sm.transition("RUNNING")
            raise ValueError("journey exploded")
    except ValueError:
        pass
    assert sm.state == "FAILED"


def test_recover_stale(tmp_path):
    # Create two state files — one stale (RUNNING), one terminal (COMPLETE)
    stale = RunStateMachine("run-stale", tmp_path)
    stale.start()
    stale.transition("CRAWLING")
    stale.transition("RUNNING")
    # Simulate crash: state file left in RUNNING

    done = RunStateMachine("run-done", tmp_path)
    done.start()
    done.transition("CRAWLING")
    done.transition("RUNNING")
    done.transition("SYNTHESIZING")
    done.transition("COMPLETE")

    recovered = RunStateMachine.recover_stale(tmp_path)
    assert "run-stale" in recovered
    assert "run-done" not in recovered

    stale_data = json.loads((tmp_path / "run-stale-state.json").read_text())
    assert stale_data["state"] == "FAILED"
    assert "process restart" in stale_data["log"][-1]["reason"]


def test_atomic_write_survives_reread(tmp_path):
    sm = RunStateMachine("run-006", tmp_path)
    sm.start()
    sm.transition("CRAWLING")

    # Read directly from disk — must match in-memory state
    on_disk = json.loads((tmp_path / "run-006-state.json").read_text())
    assert on_disk["state"] == "CRAWLING"
    assert on_disk["run_id"] == "run-006"
