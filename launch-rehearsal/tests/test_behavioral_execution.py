"""Behavioral-profile-driven execution — Karpathy's board finding.

tech_literacy / patience / trust_level previously only biased LLM severity
grading after a run finished. These tests cover the pure functions that now
make those same traits change what actually happens during execution:
timeout budget (patience), pre-action hesitation (trust_level on sensitive
actions), and post-navigate settle time (tech_literacy).
"""

from __future__ import annotations

from rehearse.browser import (
    _behavioral_pre_action_pause_ms,
    _behavioral_settle_pause_ms,
    _behavioral_timeout,
    _resolve_persona,
)
from rehearse.dsl import Persona, RunConfig, Step, Budgets


def _persona(**kwargs) -> Persona:
    defaults = dict(id="p1", name="Test", role="user", goals=[])
    defaults.update(kwargs)
    return Persona(**defaults)


def _config_with(persona: Persona) -> RunConfig:
    return RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=[persona],
        journeys=[],
        budgets=Budgets(),
    )


def test_resolve_persona_finds_by_id():
    p = _persona(id="p-abc")
    config = _config_with(p)
    found = _resolve_persona(config, "p-abc")
    assert found is p


def test_resolve_persona_missing_returns_none():
    config = _config_with(_persona())
    assert _resolve_persona(config, "nonexistent") is None


def test_low_patience_shrinks_timeout():
    p = _persona(patience="low")
    assert _behavioral_timeout(10_000, p) == 6_000


def test_high_patience_extends_timeout():
    p = _persona(patience="high")
    assert _behavioral_timeout(10_000, p) == 13_000


def test_medium_patience_unchanged_timeout():
    p = _persona(patience="medium")
    assert _behavioral_timeout(10_000, p) == 10_000


def test_no_persona_unchanged_timeout():
    assert _behavioral_timeout(10_000, None) == 10_000


def test_skeptical_persona_hesitates_on_sensitive_click():
    p = _persona(trust_level="skeptical")
    step = Step(action="click", intent="Confirm purchase")
    assert _behavioral_pre_action_pause_ms(p, step) == 1200


def test_skeptical_persona_no_hesitation_on_neutral_click():
    p = _persona(trust_level="skeptical")
    step = Step(action="click", intent="View documentation")
    assert _behavioral_pre_action_pause_ms(p, step) == 0


def test_trusting_persona_never_hesitates():
    p = _persona(trust_level="trusting")
    step = Step(action="click", intent="Delete account")
    assert _behavioral_pre_action_pause_ms(p, step) == 0


def test_hesitation_only_applies_to_click_and_fill():
    p = _persona(trust_level="skeptical")
    step = Step(action="navigate", url="/checkout")
    assert _behavioral_pre_action_pause_ms(p, step) == 0


def test_no_persona_no_hesitation():
    step = Step(action="click", intent="Confirm purchase")
    assert _behavioral_pre_action_pause_ms(None, step) == 0


def test_novice_settles_after_navigate():
    p = _persona(tech_literacy="novice")
    assert _behavioral_settle_pause_ms(p) == 800


def test_expert_does_not_settle():
    p = _persona(tech_literacy="expert")
    assert _behavioral_settle_pause_ms(p) == 0


def test_no_persona_no_settle():
    assert _behavioral_settle_pause_ms(None) == 0
