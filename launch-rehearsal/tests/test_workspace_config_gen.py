"""Workspace config generation — every generated config must be runnable.

Regression tests for the launch-blocking bug where auto-generated
workspace configs had zero journeys (dsl.MIN_JOURNEYS=5 is enforced at
load_config time, BEFORE crawl supplement), so every new user's first
run failed. Also covers ensure_starter_journeys() healing of legacy
configs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rehearse.dashboard.workspace_store import (
    _PERSONAS_BY_ROLE,
    _generate_config_yaml,
    ensure_starter_journeys,
)
from rehearse.dsl import MIN_JOURNEYS, MIN_PERSONAS, ConfigError, load_config

ROLES = ["founder", "qa-lead", "engineer", "other", "not-a-real-role"]


@pytest.mark.parametrize("role", ROLES)
def test_generated_config_passes_load_config(tmp_path: Path, role: str):
    p = _generate_config_yaml(tmp_path, f"ws-{role}", "https://example.com", "Prod", role)
    cfg = load_config(p)  # raises ConfigError if invalid
    assert len(cfg.personas) >= MIN_PERSONAS
    assert len(cfg.journeys) >= MIN_JOURNEYS


def test_every_role_template_meets_min_personas():
    for role, personas in _PERSONAS_BY_ROLE.items():
        assert len(personas) >= MIN_PERSONAS, (
            f"role {role!r} has {len(personas)} personas < MIN_PERSONAS={MIN_PERSONAS}"
        )


def test_generated_journeys_are_persona_agnostic(tmp_path: Path):
    """Starter journeys must have no persona_ids so crawl supplement still
    adds discovered journeys on top (journey_gen skips supplementing when
    any journey is persona-scoped)."""
    p = _generate_config_yaml(tmp_path, "ws-agnostic", "https://example.com", "P", "founder")
    cfg = load_config(p)
    assert all(not j.persona_ids for j in cfg.journeys)


def test_heal_legacy_config_without_journeys(tmp_path: Path):
    legacy = tmp_path / "legacy.yaml"
    legacy.write_text(
        "run:\n"
        "  target_url: https://example.com\n"
        "  run_id_prefix: legacy\n"
        "personas:\n"
        "- id: p1\n"
        "  name: One\n"
        "  role: user\n"
        "- id: p2\n"
        "  name: Two\n"
        "  role: user\n"
        "- id: p3\n"
        "  name: Three\n"
        "  role: user\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(legacy)

    assert ensure_starter_journeys(legacy) is True
    cfg = load_config(legacy)
    assert len(cfg.journeys) >= MIN_JOURNEYS


def test_heal_is_noop_when_journeys_exist(tmp_path: Path):
    p = _generate_config_yaml(tmp_path, "ws-noop", "https://example.com", "P", "founder")
    before = p.read_text(encoding="utf-8")
    assert ensure_starter_journeys(p) is False
    assert p.read_text(encoding="utf-8") == before


def test_heal_unparseable_file_returns_false(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("run: [unclosed", encoding="utf-8")
    assert ensure_starter_journeys(bad) is False


def test_generated_config_uses_real_parallelism_by_default(tmp_path: Path):
    """Onboarding-generated configs never set a budgets: block, so every
    hosted user's first run relies entirely on load_config's own fallback.
    That fallback previously hardcoded parallel_journeys=1 (fully
    sequential) regardless of the Budgets dataclass default — this pins the
    real end-to-end value so the two can't silently drift apart again."""
    p = _generate_config_yaml(tmp_path, "ws-parallel", "https://example.com", "P", "founder")
    cfg = load_config(p)
    assert cfg.budgets.parallel_journeys == 2


def test_bare_budgets_dataclass_default_matches_parsed_default():
    from rehearse.dsl import Budgets
    assert Budgets().parallel_journeys == 2
