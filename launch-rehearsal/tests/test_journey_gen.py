"""Tests for journey_gen.supplement_journeys() — auto-discovered journey injection."""
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.journey_gen import supplement_journeys
from rehearse.workflows import WorkflowGraph


def _cfg(journeys: list[Journey]) -> RunConfig:
    return RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=journeys,
        budgets=Budgets(),
    )


def _graph_with_suggestion(jid="auto-1", url="/auto-page") -> WorkflowGraph:
    graph = WorkflowGraph()
    graph.suggested_journeys.append(
        {"id": jid, "name": "Auto journey", "steps": [{"action": "navigate", "url": url}]}
    )
    return graph


def test_supplements_when_no_persona_scoped_journeys_exist():
    cfg = _cfg([Journey(id="j1", name="Generic", steps=[Step(action="navigate", url="/home")])])
    _, added = supplement_journeys(cfg, _graph_with_suggestion())
    assert added == ["auto-1"]
    assert any(j.id == "auto-1" for j in cfg.journeys)


def test_skips_supplementation_once_persona_scoped_journeys_exist():
    """Once the config has curated, persona-targeted journeys, auto-supplementing
    more persona-agnostic ones would silently run extra work for every persona —
    that's the exact bug this guards against."""
    cfg = _cfg([
        Journey(id="j1", name="Curated", steps=[Step(action="navigate", url="/home")], persona_ids=["p1"]),
    ])
    _, added = supplement_journeys(cfg, _graph_with_suggestion())
    assert added == []
    assert len(cfg.journeys) == 1


def test_does_not_duplicate_existing_url():
    cfg = _cfg([Journey(id="j1", name="Generic", steps=[Step(action="navigate", url="/auto-page")])])
    _, added = supplement_journeys(cfg, _graph_with_suggestion(url="/auto-page"))
    assert added == []
