"""Phase B — Web Vitals, network log, console warnings, press action."""

from rehearse.dsl import ALLOWED_ACTIONS
from rehearse.evidence import StepSnapshot
from rehearse.heuristics import _analyze_console_spike, analyze_run
from rehearse.web_vitals import vitals_issues


def test_press_action_allowed():
    assert "press" in ALLOWED_ACTIONS


def test_vitals_issues_thresholds():
    assert vitals_issues({"lcp": 5000, "cls": 0.1})
    assert not vitals_issues({"lcp": 2000, "cls": 0.1})


def test_console_spike_p2_operator():
    from rehearse.dsl import Budgets, Journey, Persona, RunConfig
    from rehearse.evidence import RunEvidence

    config = RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=[
            Persona(id="p1", name="A", role="evaluator", goals=[]),
            Persona(id="p2", name="B", role="operator", goals=[]),
            Persona(id="p3", name="C", role="admin", goals=[]),
        ],
        journeys=[
            Journey(id="j1", name="J", steps=[]),
            Journey(id="j2", name="J2", steps=[]),
            Journey(id="j3", name="J3", steps=[]),
            Journey(id="j4", name="J4", steps=[]),
            Journey(id="j5", name="J5", steps=[]),
        ],
        budgets=Budgets(),
    )
    steps = [
        StepSnapshot(
            f"j1-p-s{i+1}-desktop-seed1",
            "j1",
            "J",
            "p1",
            "navigate",
            console_errors=["e"],
            console_warnings=["w"],
            seed_index=1,
            body_text_excerpt="x" * 120,
        )
        for i in range(4)
    ]
    evidence = RunEvidence(
        run_id="t-1",
        target_url="https://example.com",
        product_name="T",
        started_at="2026-05-31T00:00:00Z",
        steps=steps,
    )
    result = analyze_run(config, evidence)
    titles = [i.title for i in result.issues]
    assert "Console noise spike across run" in titles
    spike = next(i for i in result.issues if i.title == "Console noise spike across run")
    assert any("p2" in pid or "operator" in pid for pid in spike.persona_ids)
