"""B3: Determinism — same evidence always produces the same analysis result.

Running analyze_run() twice on identical inputs must yield identical outputs.
This guards against randomness (dict ordering, set iteration, UUID generation)
sneaking into the severity decision tree.
"""

from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import analyze_run


def _make_config() -> RunConfig:
    return RunConfig(
        target_url="https://example.com",
        run_id_prefix="det",
        product_name="DeterminismTest",
        personas=[
            Persona(id="p1", name="NewUser", role="first-time evaluator", goals=["sign up"]),
            Persona(id="p2", name="PowerUser", role="power operator", goals=["export data"]),
            Persona(id="p3", name="Admin", role="it admin", goals=["configure"]),
        ],
        journeys=[
            Journey(
                id="j1",
                name="Onboarding",
                steps=[
                    Step(action="navigate", url="https://example.com/signup"),
                    Step(action="fill", selector="#email", value="test@example.com"),
                    Step(action="click", selector="button[type=submit]"),
                ],
            ),
            Journey(id="j2", name="Pricing", steps=[Step(action="navigate", url="https://example.com/pricing")]),
            Journey(id="j3", name="Dashboard", steps=[]),
        ],
        budgets=Budgets(),
    )


def _make_evidence(config: RunConfig) -> RunEvidence:
    ev = RunEvidence(
        run_id="det-20260601-120000",
        target_url="https://example.com",
        product_name="DeterminismTest",
        started_at="2026-06-01T12:00:00Z",
    )
    steps = [
        StepSnapshot(
            step_id="j1-p1-s1",
            journey_id="j1",
            journey_name="Onboarding",
            persona_id="p1",
            action="navigate",
            requested_url="https://example.com/signup",
            final_url="https://example.com/signup",
            outcome="pass",
            duration_ms=1200,
            http_status=200,
            body_text_excerpt="Sign up for free. Get started today.",
            unlabeled_button_count=1,
            input_count=3,
            labeled_input_count=2,
            console_errors=["TypeError: cannot read property 'x' of null"],
            seed_index=1,
        ),
        StepSnapshot(
            step_id="j1-p1-s2",
            journey_id="j1",
            journey_name="Onboarding",
            persona_id="p1",
            action="fill",
            outcome="pass",
            duration_ms=300,
            seed_index=1,
        ),
        StepSnapshot(
            step_id="j1-p1-s3",
            journey_id="j1",
            journey_name="Onboarding",
            persona_id="p1",
            action="click",
            outcome="fail",
            duration_ms=9500,
            network_failures=["500 https://example.com/api/signup", "500 https://example.com/api/signup"],
            note="TimeoutError: element not found",
            seed_index=1,
        ),
        StepSnapshot(
            step_id="j2-p1-s1",
            journey_id="j2",
            journey_name="Pricing",
            persona_id="p1",
            action="navigate",
            requested_url="https://example.com/pricing",
            final_url="https://example.com/pricing",
            outcome="pass",
            duration_ms=800,
            http_status=200,
            body_text_excerpt="Pricing plans. Starter $9/mo. Pro $29/mo.",
            heading_count=3,
            link_count=8,
            seed_index=1,
        ),
    ]
    for s in steps:
        ev.add_step(s)
    return ev


def _result_fingerprint(result) -> dict:
    """Extract a stable, order-sensitive representation of an AnalysisResult."""
    issues_sorted = sorted(
        [(i.severity, i.title, i.confidence) for i in result.issues]
    )
    delights_sorted = sorted(
        [(d.title, d.confidence) for d in result.delights]
    )
    matrix_sorted = {
        jid: sorted(pmap.items())
        for jid, pmap in sorted(result.journey_matrix.items())
    }
    return {
        "issues": issues_sorted,
        "delights": delights_sorted,
        "matrix": matrix_sorted,
        "readiness": result.readiness,
        "issue_count": len(result.issues),
        "delight_count": len(result.delights),
    }


def test_analyze_run_is_deterministic():
    """analyze_run() must produce identical output across two calls with the same inputs."""
    config = _make_config()
    ev1 = _make_evidence(config)
    ev2 = _make_evidence(config)

    result1 = analyze_run(config, ev1)
    result2 = analyze_run(config, ev2)

    fp1 = _result_fingerprint(result1)
    fp2 = _result_fingerprint(result2)

    assert fp1 == fp2, (
        f"analyze_run() is not deterministic!\n"
        f"Run 1: {fp1}\n"
        f"Run 2: {fp2}"
    )


def test_analyze_run_deterministic_with_flaky_steps():
    """Determinism holds even when flaky steps are present (severity downgrade is stable)."""
    config = _make_config()
    ev = _make_evidence(config)

    # Make one step flaky
    ev.steps[0].flaky = True
    ev.steps[0].note = "FLAKY: outcomes differ across seeds"

    r1 = analyze_run(config, ev)
    r2 = analyze_run(config, ev)

    assert _result_fingerprint(r1) == _result_fingerprint(r2)


def test_analyze_run_issue_titles_are_unique():
    """No two issues should have identical titles — dedup must work."""
    config = _make_config()
    ev = _make_evidence(config)
    result = analyze_run(config, ev)

    titles = [i.title for i in result.issues]
    assert len(titles) == len(set(titles)), f"Duplicate issue titles: {titles}"
