"""Analysis bundle export — named errors, cost estimate, observability."""

from pathlib import Path

import pytest

from rehearse.analysis_export import (
    build_run_bundle,
    _compute_cost_estimate,
    _dimension_for_finding,
    _named_error_issues,
    issue_matches_dimension,
)
from rehearse.context import AgentReport, RunContext
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.errors import BrowserStepTimeout, PreflightError, classify_step_error
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import AnalysisResult, analyze_run


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


def test_dimension_for_finding_tags():
    assert _dimension_for_finding("Icon-only or unlabeled buttons", "3 button(s) lack accessible name") == "UI/UX"
    assert _dimension_for_finding("Form inputs missing labels", "2 of 4 inputs lack label") == "Accessibility"
    assert _dimension_for_finding("Slow step completion", "Step took 9000ms") == "Performance"
    assert _dimension_for_finding("Sparse page content", "Page body has very little text") == "Information"
    assert _dimension_for_finding("Auth wall on deep link", "landed on /login") == "Trust"
    assert _dimension_for_finding("BrowserStepTimeout: One", "click timeout") == "Functionality"


def test_build_run_bundle_tags_heuristic_issues_by_dimension(tmp_path: Path):
    config = _cfg()
    evidence = _evidence(
        StepSnapshot(
            "j1-s1",
            "j1",
            "One",
            "p1",
            "click",
            outcome="pass",
            unlabeled_button_count=8,
            duration_ms=5000,
            body_text_excerpt="short",
        ),
        StepSnapshot(
            "j1-s2",
            "j1",
            "One",
            "p1",
            "click",
            outcome="pass",
            unlabeled_button_count=6,
            input_count=3,
            labeled_input_count=1,
            duration_ms=4000,
            body_text_excerpt="enough body text for this step to not be sparse content",
        ),
    )
    analysis = analyze_run(config, evidence)
    bundle = build_run_bundle(config, evidence, analysis, tmp_path)

    ui_issues = [i for i in bundle["issues"] if issue_matches_dimension(i, "UI/UX")]
    a11y_issues = [i for i in bundle["issues"] if issue_matches_dimension(i, "Accessibility")]
    assert ui_issues, "expected UI/UX findings for unlabeled buttons"
    assert a11y_issues, "expected Accessibility findings for labels or related UI/UX"

    unlabeled = next(i for i in bundle["issues"] if "unlabeled" in i["title"].lower())
    assert "14 button" in unlabeled["detail"]
    assert unlabeled["dimension"] == "UI/UX"
    assert "Accessibility" in unlabeled.get("relatedDimensions", [])
