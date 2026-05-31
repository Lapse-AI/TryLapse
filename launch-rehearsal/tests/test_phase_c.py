from rehearse.dsl import ALLOWED_ACTIONS, load_config
from rehearse.dashboard.recordings import compile_journey_yaml


def test_phase_c_actions_in_dsl():
    assert {"explore", "dismiss"}.issubset(ALLOWED_ACTIONS)


def test_compile_recording_valid():
    out = compile_journey_yaml(
        journey_id="j-rec",
        journey_name="Recorded",
        steps=[
            {"action": "navigate", "url": "{target_url}/"},
            {"action": "click", "intent": "Sign in"},
        ],
    )
    assert out["valid"] is True
    assert "journeys:" in out["yaml"]
    assert out["errors"] == []


def test_build_template_explore_summary():
    from rehearse.explore import build_template_explore_summary

    rounds = [
        {
            "round": 1,
            "done": True,
            "rationale": "Reached dashboard",
            "actions": [{"action": "click", "intent": "Sign in", "outcome": "ok"}],
        }
    ]
    s = build_template_explore_summary("Open app", rounds)
    assert "Sign in" in s
    assert "1 round" in s


def test_compile_recording_rejects_bad_action():
    out = compile_journey_yaml(
        journey_id="j-bad",
        journey_name="Bad",
        steps=[{"action": "fly"}],
    )
    assert out["valid"] is False
    assert out["errors"]
