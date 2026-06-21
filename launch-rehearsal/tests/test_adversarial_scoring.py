"""Adversarial scoring guard — Schneier's board finding.

"Run your own heuristics against a product you've deliberately broken and check
if the score degrades predictably. If it doesn't, your scoring is theater."

These tests build synthetic runs at five severity tiers (clean → light → moderate
→ severe → critical), each injecting a known, named failure mode, and assert that:

1. readiness score is monotonically non-increasing as severity increases
2. launchGate escalates in the right direction (never PASS at critical, never
   BLOCKED/CAUTION at clean)
3. a single P0-equivalent failure (HTTP 5xx / broken auth) is sufficient to
   move the gate off PASS — the score can't be "bought back" by padding good
   steps around one hard blocker

This is a regression guard, not a one-off check: if someone tunes heuristics or
the gate thresholds in a way that makes the score insensitive to real product
breakage, these tests fail and say so explicitly.
"""

from __future__ import annotations

from pathlib import Path

from rehearse.analysis_export import build_run_bundle
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import analyze_run


def _config() -> RunConfig:
    return RunConfig(
        target_url="https://example.com",
        run_id_prefix="adversarial",
        product_name="Adversarial Test Product",
        personas=[
            Persona(id="p1", name="First-Time Evaluator", role="evaluator", goals=["evaluate"]),
            Persona(id="p2", name="Daily Operator", role="operator", goals=["operate"]),
        ],
        journeys=[
            Journey(id="j1", name="Onboarding", steps=[Step(action="navigate", url="/")]),
            Journey(id="j2", name="Core workflow", steps=[Step(action="click", intent="primary action")]),
        ],
        budgets=Budgets(),
    )


def _clean_step(step_id: str, journey_id: str, persona_id: str) -> StepSnapshot:
    """A step with no defects at all — the floor for what 'good' looks like."""
    return StepSnapshot(
        step_id=step_id,
        journey_id=journey_id,
        journey_name=journey_id,
        persona_id=persona_id,
        action="navigate",
        requested_url="https://example.com/",
        final_url="https://example.com/",
        http_status=200,
        outcome="pass",
        duration_ms=400,
        body_text_excerpt="Welcome — here is a rich, well-structured page with clear navigation and helpful copy describing what to do next.",
        link_count=5,
        heading_count=2,
        input_count=2,
        labeled_input_count=2,
    )


def _build_run(severity: str) -> tuple[RunConfig, RunEvidence]:
    """Build a run with injected defects scaled to `severity`.

    Tiers: clean, light, moderate, severe, critical. Each tier scales ONE
    consistent failure dimension (fraction of steps that hard-fail with an
    HTTP 500) rather than mixing failure *types* — mixing types caused a false
    positive here once: an auth-wall-everywhere finding correctly escalates to
    P0/BLOCKED in production (total lockout is uniquely catastrophic), which
    is *more* severe than a single P1 HTTP error despite "auth wall" being an
    earlier rung on an intuitive severity ladder. Keep the failure type fixed
    so severity is purely a function of how much of the run is broken.
    """
    config = _config()
    evidence = RunEvidence(
        run_id=f"adversarial-{severity}",
        target_url=config.target_url,
        product_name=config.product_name,
        started_at="2026-06-17T00:00:00+00:00",
        finished_at="2026-06-17T00:05:00+00:00",
        duration_ms=300_000,
    )

    # Fraction of (persona, journey) steps that hard-fail with HTTP 500, plus
    # a baseline polish defect (unlabeled buttons) that scales the same way.
    fail_fraction = {
        "clean": 0.0,
        "light": 0.0,
        "moderate": 0.0,
        "severe": 0.5,
        "critical": 1.0,
    }[severity]
    unlabeled_count = {
        "clean": 0,
        "light": 2,
        "moderate": 5,
        "severe": 5,
        "critical": 6,
    }[severity]
    sparse_content = severity in ("moderate", "severe", "critical")

    combos = [(p, j) for p in config.personas for j in config.journeys]
    n_fail = round(len(combos) * fail_fraction)

    for idx, (persona, journey) in enumerate(combos):
        step = _clean_step(f"{journey.id}-{persona.id}-s1", journey.id, persona.id)
        step.unlabeled_button_count = unlabeled_count
        if sparse_content:
            step.body_text_excerpt = "Click here."
        if idx < n_fail:
            step.outcome = "fail"
            step.http_status = 500
            step.error_type = "HTTPError"
            step.note = "Server returned 500 on core navigation step"
            step.body_text_excerpt = ""
        evidence.add_step(step)

    return config, evidence


_SEVERITY_TIERS = ["clean", "light", "moderate", "severe", "critical"]


def _bundle_for(severity: str, tmp_path: Path) -> dict:
    config, evidence = _build_run(severity)
    analysis = analyze_run(config, evidence)
    return build_run_bundle(config, evidence, analysis, tmp_path)


def test_readiness_score_is_monotonically_non_increasing(tmp_path: Path) -> None:
    scores = []
    for severity in _SEVERITY_TIERS:
        bundle = _bundle_for(severity, tmp_path / severity)
        scores.append(bundle["summary"]["readiness"])

    for i in range(1, len(scores)):
        assert scores[i] <= scores[i - 1], (
            f"Scoring regression: '{_SEVERITY_TIERS[i]}' scored {scores[i]} which is "
            f"HIGHER than '{_SEVERITY_TIERS[i-1]}' at {scores[i-1]}. Increasing severity "
            f"must never increase the readiness score — the heuristics are insensitive "
            f"to real defects (Goodhart drift)."
        )


def test_clean_run_never_blocked_or_caution(tmp_path: Path) -> None:
    bundle = _bundle_for("clean", tmp_path)
    gate = bundle["summary"]["launchGate"]
    assert gate not in ("BLOCKED", "CAUTION"), (
        f"A defect-free run got gate={gate!r}. A clean run must never be gated "
        f"as if it had real problems — that would make every score noise."
    )


def test_critical_run_never_passes(tmp_path: Path) -> None:
    bundle = _bundle_for("critical", tmp_path)
    gate = bundle["summary"]["launchGate"]
    assert gate != "PASS", (
        f"A run with a hard HTTP 500 blocker got gate=PASS. A single critical "
        f"failure must never be 'bought back' to a passing verdict by padding "
        f"the rest of the run with clean steps — that's exactly the gameable "
        f"scoring Schneier flagged."
    )


def test_gate_escalates_with_severity(tmp_path: Path) -> None:
    """Gate severity rank must be non-decreasing as injected severity increases."""
    rank = {"PASS": 0, "REVIEW": 1, "CAUTION": 2, "BLOCKED": 3}
    gates = []
    for severity in _SEVERITY_TIERS:
        bundle = _bundle_for(severity, tmp_path / severity)
        gates.append(bundle["summary"]["launchGate"])

    ranks = [rank[g] for g in gates]
    for i in range(1, len(ranks)):
        assert ranks[i] >= ranks[i - 1], (
            f"Gate regression: '{_SEVERITY_TIERS[i]}' produced gate={gates[i]!r} "
            f"which is LESS severe than '{_SEVERITY_TIERS[i-1]}' at {gates[i-1]!r}. "
            f"Full tier sequence was: {list(zip(_SEVERITY_TIERS, gates))}"
        )


def test_critical_defect_alone_outweighs_clean_padding(tmp_path: Path) -> None:
    """One hard blocker must dominate the score even when surrounded by mostly-clean steps.

    This is the literal Goodhart check: can a team game the score by shipping
    19 trivial clean pages and 1 broken core workflow? The answer must be no.
    """
    config = _config()
    evidence = RunEvidence(
        run_id="adversarial-padded",
        target_url=config.target_url,
        product_name=config.product_name,
        started_at="2026-06-17T00:00:00+00:00",
        finished_at="2026-06-17T00:05:00+00:00",
        duration_ms=300_000,
    )
    # 9 clean steps padding the run...
    for i in range(9):
        evidence.add_step(_clean_step(f"pad-{i}", "j1", "p1"))
    # ...and exactly 1 hard blocker on the core workflow journey.
    blocker = _clean_step("j2-p1-s1", "j2", "p1")
    blocker.outcome = "fail"
    blocker.http_status = 500
    blocker.error_type = "HTTPError"
    blocker.note = "Core workflow endpoint returns 500"
    evidence.add_step(blocker)

    analysis = analyze_run(config, evidence)
    bundle = build_run_bundle(config, evidence, analysis, tmp_path)

    assert bundle["summary"]["launchGate"] != "PASS", (
        "9 clean steps padded around 1 critical blocker still produced PASS — "
        "the score can be gamed by volume of trivial-good steps."
    )
