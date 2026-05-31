"""Analysis bundle export — named errors, cost estimate, observability."""

from pathlib import Path

import pytest

from rehearse.analysis_export import build_run_bundle, _compute_cost_estimate, _named_error_issues
from rehearse.context import AgentReport, RunContext
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.errors import BrowserStepTimeout, PreflightError, classify_step_error
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import AnalysisResult


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


def _evidence(*steps: StepSnapshot) -> RunEvidence:
    return RunEvidence(
        run_id="t-20260531-120000",
        target_url="https://example.com",
        product_name="T",
        started_at="2026-05-31T12:00:00Z",
        finished_at="2026-05-31T12:01:00Z",
        duration_ms=60_000,
        outcome="complete",
        steps=list(steps),
    )


def test_classify_step_error_named_types():
    assert classify_step_error(BrowserStepTimeout("timed out")) == "BrowserStepTimeout"
    assert classify_step_error(PreflightError("bad config")) == "PreflightError"
    assert classify_step_error(TimeoutError("page.goto: Timeout")) == "BrowserStepTimeout"
    assert classify_step_error(RuntimeError("boom")) == "BrowserStepError"


def test_named_error_issues_from_failed_steps():
    config = _cfg()
    evidence = _evidence(
        StepSnapshot(
            "j1-s1",
            "j1",
            "One",
            "p1",
            "click",
            outcome="fail",
            error_type="BrowserStepTimeout",
            note="click timeout",
        )
    )
    issues = _named_error_issues(config, evidence, set())
    assert len(issues) == 1
    assert issues[0]["errorType"] == "BrowserStepTimeout"
    assert issues[0]["severity"] == "P1"


def test_cost_estimate_heuristic_without_tokens():
    config = _cfg()
    evidence = _evidence()
    ctx = RunContext(config=config, evidence=evidence)
    ctx.agent_reports = [
        AgentReport(agent_id="crawler", agent_role="Crawl", summary="ok", metadata={"page_count": 3}),
        AgentReport(agent_id="journey", agent_role="Journey", summary="ok"),
    ]
    est = _compute_cost_estimate(ctx, evidence, llm_enabled=False, persona_count=3)
    assert est["source"] == "heuristic"
    assert est["usd"] > 0
    assert est["durationSec"] == 60
    assert est["agentsRun"] == 2
    assert est["totalTokens"] is None


def test_cost_estimate_from_llm_tokens():
    config = _cfg()
    evidence = _evidence()
    ctx = RunContext(config=config, evidence=evidence)
    ctx.agent_reports = [
        AgentReport(
            agent_id="llm-p1",
            agent_role="LLM",
            summary="ok",
            metadata={"input_tokens": 1000, "output_tokens": 500, "cost_usd": 0.0003},
        ),
    ]
    est = _compute_cost_estimate(ctx, evidence, llm_enabled=True, persona_count=3)
    assert est["source"] == "llm_tokens"
    assert est["totalTokens"] == 1500
    assert est["usd"] == pytest.approx(0.0003)


def test_build_run_bundle_observability_fields(tmp_path: Path):
    config = _cfg()
    evidence = _evidence(
        StepSnapshot(
            "j1-s1",
            "j1",
            "One",
            "p1",
            "navigate",
            outcome="fail",
            error_type="StepAssertionFailed",
            note="URL assertion failed",
        )
    )
    ctx = RunContext(config=config, evidence=evidence)
    ctx.agent_reports = [AgentReport(agent_id="journey", agent_role="Journey", summary="done")]
    analysis = AnalysisResult(journey_matrix={"j1": {"p1": "fail"}}, readiness="Red")

    bundle = build_run_bundle(config, evidence, analysis, tmp_path, ctx=ctx, llm_enabled=False)

    summary = bundle["summary"]
    assert summary["durationSec"] == 60
    assert summary["outcome"] == "complete"
    assert summary["pagesCrawled"] == 0
    assert summary["agentsRun"] == 1
    assert summary["configHash"]
    assert summary["agentCost"] > 0
    assert summary["costEstimate"]["source"] == "heuristic"

    step = bundle["steps"][0]
    assert step["errorType"] == "StepAssertionFailed"
    error_issues = [i for i in bundle["issues"] if i.get("errorType")]
    assert any(i["errorType"] == "StepAssertionFailed" for i in error_issues)
