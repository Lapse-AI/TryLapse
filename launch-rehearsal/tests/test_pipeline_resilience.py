"""LLM pipeline failure-surface guard — Carmack's board finding.

"Each stage you add is a new way to fail silently." Before this fix,
LLMPersonaAgent returned an empty report (no findings, no journey_grades) when
analyze_persona_llm() failed — the failure was only visible in agent metadata,
and the persona's journeys were left ungraded entirely. behavioral_judge.py
already had a template fallback for this exact failure mode; the persona
severity hop didn't.

These tests confirm every persona always gets a non-empty journey_grades dict
even when the LLM call fails outright, and that the degraded path is recorded
in report.metadata so a dashboard can surface "heuristic fallback" rather than
silently presenting it as a normal LLM result.
"""

from __future__ import annotations

from unittest.mock import patch

from rehearse.agents.llm_persona_agent import LLMPersonaAgent
from rehearse.context import RunContext
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.llm import template_persona_analysis


def _ctx_with_steps(*, fail: bool) -> RunContext:
    config = RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="Evaluator", role="evaluator", goals=["evaluate"])],
        journeys=[Journey(id="j1", name="Onboarding", steps=[Step(action="navigate", url="/")])],
        budgets=Budgets(),
    )
    evidence = RunEvidence(
        run_id="t-run",
        target_url=config.target_url,
        product_name=config.product_name,
        started_at="2026-06-17T00:00:00+00:00",
    )
    evidence.add_step(
        StepSnapshot(
            step_id="j1-p1-s1",
            journey_id="j1",
            journey_name="Onboarding",
            persona_id="p1",
            action="navigate",
            outcome="fail" if fail else "pass",
        )
    )
    return RunContext(config=config, evidence=evidence)


def test_template_persona_analysis_grades_every_journey():
    ctx = _ctx_with_steps(fail=False)
    persona = ctx.config.personas[0]
    result = template_persona_analysis(ctx, persona)
    assert result["journey_grades"] == {"j1": "pass"}
    assert result["source"] == "template"
    assert "heuristic fallback" in result["summary"]


def test_template_persona_analysis_grades_failed_journey():
    ctx = _ctx_with_steps(fail=True)
    persona = ctx.config.personas[0]
    result = template_persona_analysis(ctx, persona)
    assert result["journey_grades"] == {"j1": "fail"}


def test_agent_degrades_gracefully_on_llm_error():
    """When analyze_persona_llm returns an error dict, the agent must still
    produce a non-empty journey_grades — not an empty report."""
    ctx = _ctx_with_steps(fail=False)
    persona = ctx.config.personas[0]
    agent = LLMPersonaAgent(persona)

    with patch("rehearse.agents.llm_persona_agent.llm_enabled", return_value=True):
        with patch(
            "rehearse.agents.llm_persona_agent.analyze_persona_llm",
            return_value={"error": "timeout", "summary": "LLM read timed out"},
        ):
            report = agent.execute(ctx)

    assert report.journey_grades, "journey_grades must not be empty on LLM failure"
    assert report.journey_grades["j1"]["p1"] == "pass"
    assert report.metadata["degraded"] is True
    assert report.metadata["llmError"] == "timeout"
    assert report.metadata["provider"] == "heuristic_fallback"


def test_agent_degrades_gracefully_on_no_response():
    """When analyze_persona_llm returns None (e.g. no API key resolved at call time),
    the agent must still produce a non-empty journey_grades."""
    ctx = _ctx_with_steps(fail=True)
    persona = ctx.config.personas[0]
    agent = LLMPersonaAgent(persona)

    with patch("rehearse.agents.llm_persona_agent.llm_enabled", return_value=True):
        with patch("rehearse.agents.llm_persona_agent.analyze_persona_llm", return_value=None):
            report = agent.execute(ctx)

    assert report.journey_grades["j1"]["p1"] == "fail"
    assert report.metadata["degraded"] is True
    assert report.metadata["llmError"] == "no_response"


def test_agent_uses_real_llm_data_when_available():
    """Sanity check: a successful LLM response is NOT marked degraded."""
    ctx = _ctx_with_steps(fail=False)
    persona = ctx.config.personas[0]
    agent = LLMPersonaAgent(persona)

    llm_data = {
        "summary": "All good",
        "journey_grades": {"j1": "pass"},
        "issues": [],
        "delights": [],
    }
    with patch("rehearse.agents.llm_persona_agent.llm_enabled", return_value=True):
        with patch("rehearse.agents.llm_persona_agent.analyze_persona_llm", return_value=llm_data):
            report = agent.execute(ctx)

    assert report.metadata["degraded"] is False
    assert report.metadata["llmError"] is None
    assert report.summary == "All good"
