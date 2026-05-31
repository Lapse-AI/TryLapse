"""Run narrative and template chat."""

from rehearse.dsl import Budgets, Journey, Persona, RunConfig
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import analyze_run
from rehearse.narrative import build_run_narrative, build_template_narrative, template_chat_reply


def _fixture():
    config = RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="Acme",
        personas=[
            Persona(id="p1", name="Eval", role="prospect", goals=[]),
            Persona(id="p2", name="Ops", role="operator", goals=[]),
            Persona(id="p3", name="Admin", role="admin", goals=[]),
        ],
        journeys=[
            Journey(id="j1", name="Land", steps=[]),
            Journey(id="j2", name="Two", steps=[]),
            Journey(id="j3", name="Three", steps=[]),
            Journey(id="j4", name="Four", steps=[]),
            Journey(id="j5", name="Five", steps=[]),
        ],
        budgets=Budgets(),
    )
    evidence = RunEvidence(
        run_id="t-1",
        target_url="https://example.com",
        product_name="Acme",
        started_at="2026-05-31T00:00:00Z",
        steps=[
            StepSnapshot(
                "j1-p-s1-desktop-seed1",
                "j1",
                "Land",
                "p1",
                "navigate",
                outcome="pass",
                seed_index=1,
                body_text_excerpt="x" * 100,
            )
        ],
    )
    analysis = analyze_run(config, evidence)
    return config, evidence, analysis


def test_template_narrative_has_sections():
    config, evidence, analysis = _fixture()
    n = build_template_narrative(config, evidence, analysis)
    assert "Acme" in n["executiveSummary"]
    assert n["forFounders"]
    assert len(n["suggestedQuestions"]) >= 3
    assert n["source"] == "template"


def test_template_chat_blockers():
    config, evidence, analysis = _fixture()
    bundle = {
        "summary": {"readinessBand": analysis.readiness},
        "issues": [{"severity": "P1", "title": "Auth broke", "detail": "login loop"}],
        "delights": [],
        "narrative": build_template_narrative(config, evidence, analysis),
    }
    reply = template_chat_reply(bundle, "what are the blockers?")
    assert "Auth broke" in reply


def test_build_run_narrative_without_llm():
    config, evidence, analysis = _fixture()
    n = build_run_narrative(config, evidence, analysis, use_llm=False)
    assert n["source"] == "template"
