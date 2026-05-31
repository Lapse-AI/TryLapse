"""Heuristics and flaky detection tests."""

from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import _canonical_steps, _journey_status, analyze_run


def _cfg() -> RunConfig:
    personas = [
        Persona(id="p1", name="A", role="evaluator", goals=[]),
        Persona(id="p2", name="B", role="operator", goals=[]),
        Persona(id="p3", name="C", role="admin", goals=[]),
    ]
    journeys = [
        Journey(id="j1", name="One", steps=[Step(action="navigate", url="https://x/")]),
        Journey(id="j2", name="Two", steps=[]),
        Journey(id="j3", name="Three", steps=[]),
        Journey(id="j4", name="Four", steps=[]),
        Journey(id="j5", name="Five", steps=[]),
    ]
    return RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=personas,
        journeys=journeys,
        budgets=Budgets(),
    )


def test_journey_status_fail_and_flaky():
    assert _journey_status([]) == "fail"
    assert _journey_status([StepSnapshot("s", "j1", "J", "p1", "click", outcome="pass")]) == "pass"
    flaky = StepSnapshot("s", "j1", "J", "p1", "click", outcome="pass", flaky=True)
    assert _journey_status([flaky]) == "partial"


def test_canonical_steps_filters_seeds():
    steps = [
        StepSnapshot("a", "j1", "J", "p1", "navigate", seed_index=1, outcome="pass"),
        StepSnapshot("b", "j1", "J", "p1", "navigate", seed_index=2, outcome="fail"),
    ]
    assert len(_canonical_steps(steps)) == 1
    assert _canonical_steps(steps)[0].step_id == "a"


def test_canonical_steps_prefers_desktop_viewport():
    steps = [
        StepSnapshot(
            "j1-p-s1-mobile-seed1",
            "j1",
            "J",
            "p1",
            "navigate",
            seed_index=1,
            viewport="mobile",
            outcome="fail",
        ),
        StepSnapshot(
            "j1-p-s1-desktop-seed1",
            "j1",
            "J",
            "p1",
            "navigate",
            seed_index=1,
            viewport="desktop",
            outcome="pass",
        ),
    ]
    canon = _canonical_steps(steps)
    assert len(canon) == 1
    assert canon[0].viewport == "desktop"


def test_analyze_run_flaky_finding():
    config = _cfg()
    evidence = RunEvidence(
        run_id="t-1",
        target_url="https://example.com",
        product_name="T",
        started_at="2026-05-31T00:00:00Z",
        steps=[
            StepSnapshot(
                "j1-s1-seed1",
                "j1",
                "One",
                "p1",
                "click",
                outcome="pass",
                seed_index=1,
                flaky=True,
                note="FLAKY: outcomes differ across seeds",
            ),
        ],
    )
    result = analyze_run(config, evidence)
    titles = [i.title for i in result.issues]
    assert any("Flaky" in t for t in titles)
