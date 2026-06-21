"""Disabled personas must never execute journeys or appear in the live progress UI.

Regression coverage for a real production bug: orchestrator.run_journey_phase(),
JourneyAgent.execute()/execute_for_persona(), and runner.run_rehearsal()'s progress
tracker all built their persona list from RunConfig.personas directly, ignoring the
`enabled` flag entirely. A user who disabled personas in the dashboard would still
see their journeys execute in the browser and appear in the Runner page UI.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from rehearse.agents.journey_agent import JourneyAgent
from rehearse.browser import BrowserSession
from rehearse.context import RunContext
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence


def _cfg(execute_all=True, parallel_journeys=2) -> RunConfig:
    return RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        execute_all_personas_in_browser=execute_all,
        personas=[
            Persona(id="p1-on", name="Enabled", role="r", goals=[], enabled=True),
            Persona(id="p2-off", name="Disabled", role="r", goals=[], enabled=False),
            Persona(id="p3-off", name="Disabled2", role="r", goals=[], enabled=False),
        ],
        journeys=[
            Journey(id="j-on", name="On journey", steps=[Step(action="navigate", url="/a")],
                     persona_ids=["p1-on"]),
            Journey(id="j-off", name="Off journey", steps=[Step(action="navigate", url="/b")],
                     persona_ids=["p2-off"]),
        ],
        budgets=Budgets(parallel_journeys=parallel_journeys),
    )


def _ctx(cfg: RunConfig) -> RunContext:
    ev = RunEvidence(run_id="t-001", target_url="https://x.com",
                     product_name="T", started_at="2026-06-19T00:00:00Z")
    ctx = RunContext(config=cfg, evidence=ev)
    ctx.metadata = {"output_dir": "/tmp", "deadline": 1e18}
    return ctx


def test_journey_agent_parallel_mode_skips_disabled_personas():
    """workers > 1 path (execute()) must not build work units for disabled personas."""
    cfg = _cfg(parallel_journeys=2)
    ctx = _ctx(cfg)
    session = MagicMock(spec=BrowserSession)
    agent = JourneyAgent(session, Path("/tmp/art"))

    seen_persona_ids = set()

    def fake_worker(ctx, journey, persona_id, seeds, loops, viewports):
        seen_persona_ids.add(persona_id)
        return journey.id, persona_id, []

    with patch.object(agent, "_run_journey_worker", side_effect=fake_worker):
        agent.execute(ctx)

    assert "p2-off" not in seen_persona_ids
    assert "p3-off" not in seen_persona_ids
    assert seen_persona_ids == {"p1-on"}


def test_journey_agent_sequential_mode_skips_disabled_personas():
    """workers == 1, multi-persona path also must not run disabled personas."""
    cfg = _cfg(parallel_journeys=1)
    ctx = _ctx(cfg)
    session = MagicMock(spec=BrowserSession)
    agent = JourneyAgent(session, Path("/tmp/art"))

    seen_persona_ids = set()

    def fake_worker(ctx, journey, persona_id, seeds, loops, viewports):
        seen_persona_ids.add(persona_id)
        return journey.id, persona_id, []

    with patch.object(agent, "_run_journey_worker", side_effect=fake_worker):
        agent.execute(ctx)

    assert seen_persona_ids == {"p1-on"}


def test_journey_agent_execute_for_persona_rejects_disabled_persona():
    """execute_for_persona() must skip a persona_id that is disabled, even if asked."""
    cfg = _cfg()
    ctx = _ctx(cfg)
    session = MagicMock(spec=BrowserSession)
    agent = JourneyAgent(session, Path("/tmp/art"))

    report = agent.execute_for_persona(ctx, "p2-off")
    assert "skipped" in report.summary


def test_orchestrator_run_journey_phase_uses_only_enabled_personas():
    """Sequential streaming-synthesis path (>1 persona, workers==1) must call
    execute_for_persona() only for enabled personas."""
    from rehearse.agents.orchestrator import AgentOrchestrator

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        execute_all_personas_in_browser=True,
        personas=[
            Persona(id="p1-on", name="Enabled1", role="r", goals=[], enabled=True),
            Persona(id="p4-on", name="Enabled2", role="r", goals=[], enabled=True),
            Persona(id="p2-off", name="Disabled", role="r", goals=[], enabled=False),
            Persona(id="p3-off", name="Disabled2", role="r", goals=[], enabled=False),
        ],
        journeys=[
            Journey(id="j-on", name="On journey", steps=[Step(action="navigate", url="/a")]),
        ],
        budgets=Budgets(parallel_journeys=1),
    )
    ctx = _ctx(cfg)
    session = MagicMock(spec=BrowserSession)
    orch = AgentOrchestrator(ctx, session, Path("/tmp/art"))

    with patch.object(orch._journey_agent, "execute_for_persona") as mock_exec:
        mock_exec.return_value = MagicMock(journey_grades={})
        orch.run_journey_phase()
        seen_persona_ids = [c.args[1] for c in mock_exec.call_args_list]

    assert "p2-off" not in seen_persona_ids
    assert "p3-off" not in seen_persona_ids
    assert set(seen_persona_ids) == {"p1-on", "p4-on"}


def test_runner_progress_tracker_excludes_disabled_personas(tmp_path):
    """run_rehearsal()'s ProgressTracker.set_personas() must only list enabled
    personas — this directly feeds the Runner page's persona/journey columns."""
    from rehearse import runner as runner_mod

    cfg = _cfg(parallel_journeys=1)

    captured = {}

    class FakeTracker:
        def __init__(self, *a, **k):
            pass

        def set_config(self, **k):
            pass

        def set_personas(self, personas_data, journeys_per_persona):
            captured["personas_data"] = personas_data
            captured["journeys_per_persona"] = journeys_per_persona

        def set_phase(self, *a, **k):
            pass

    fake_orchestrator = MagicMock()
    fake_orchestrator.run_crawl_phase.return_value = None
    fake_orchestrator.run_journey_phase.return_value = None
    fake_orchestrator.run_persona_analysis_phase.return_value = None
    fake_orchestrator.run_synthesis_phase.return_value = None

    with patch("rehearse.progress.ProgressTracker", FakeTracker), \
         patch.object(runner_mod, "BrowserSession") as MockSession, \
         patch.object(runner_mod, "AgentOrchestrator", return_value=fake_orchestrator), \
         patch.object(runner_mod, "write_scorecard", return_value=None), \
         patch.object(runner_mod, "analyze_run", return_value={}):
        MockSession.return_value.__enter__ = lambda self: self
        MockSession.return_value.__exit__ = lambda self, *a: None
        try:
            runner_mod.run_rehearsal(cfg, output_dir=tmp_path, dry_run=False)
        except Exception:
            pass  # only the progress-tracker call matters for this test

    persona_ids = {p["id"] for p in captured.get("personas_data", [])}
    assert persona_ids == {"p1-on"}
    assert set(captured.get("journeys_per_persona", {}).keys()) == {"p1-on"}
