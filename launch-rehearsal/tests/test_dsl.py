"""DSL loader and validation tests."""

from pathlib import Path

import pytest

from rehearse.dsl import ALLOWED_ACTIONS, load_config
from rehearse.errors import ConfigError

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_minimal_fixture():
    cfg = load_config(FIXTURES / "minimal-valid.yaml")
    assert cfg.target_url == "https://example.com"
    assert len(cfg.personas) == 3
    assert len(cfg.journeys) == 5
    assert cfg.journeys[0].steps[0].url == "https://example.com/"


def test_open_link_in_allowed_actions():
    assert "open_link" in ALLOWED_ACTIONS


def test_rejects_wrong_persona_count(tmp_path: Path):
    path = tmp_path / "two-personas.yaml"
    path.write_text(
        """
run:
  target_url: https://example.com
personas:
  - {id: p1, name: A, role: r, goals: []}
  - {id: p2, name: B, role: r, goals: []}
journeys:
  - {id: j1, name: J1, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j2, name: J2, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j3, name: J3, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j4, name: J4, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j5, name: J5, steps: [{action: navigate, url: "https://example.com"}]}
"""
    )
    with pytest.raises(ConfigError, match="Expected 3 personas"):
        load_config(path)


def test_rejects_unknown_action(tmp_path: Path):
    text = (FIXTURES / "minimal-valid.yaml").read_text().replace(
        "action: navigate", "action: teleport", 1
    )
    path = tmp_path / "bad-action.yaml"
    path.write_text(text)
    with pytest.raises(ConfigError, match="Unknown action"):
        load_config(path)
