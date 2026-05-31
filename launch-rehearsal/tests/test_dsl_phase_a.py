"""DSL Phase A — actions, journey minimum, viewports."""

from pathlib import Path

import pytest
import yaml

from rehearse.dsl import ALLOWED_ACTIONS, load_config
from rehearse.errors import ConfigError


def test_allowed_actions_include_interactions():
    assert {"hover", "scroll", "select"}.issubset(ALLOWED_ACTIONS)


def test_load_self_dashboard_six_journeys(tmp_path: Path):
    example = Path(__file__).resolve().parents[1] / "examples" / "self-dashboard.yaml"
    cfg = load_config(example)
    assert len(cfg.journeys) >= 6
    assert cfg.viewports == ["desktop", "tablet", "mobile"]
    assert cfg.crawl and "/runs/" in (cfg.crawl.exclude_path_prefixes or [])


def test_rejects_unknown_action(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        yaml.dump(
            {
                "run": {"target_url": "https://example.com", "run_id_prefix": "x", "product_name": "X"},
                "personas": [
                    {"id": "p1", "name": "a", "role": "r", "goals": []},
                    {"id": "p2", "name": "b", "role": "r", "goals": []},
                    {"id": "p3", "name": "c", "role": "r", "goals": []},
                ],
                "journeys": [
                    {"id": "j1", "name": "J", "steps": [{"action": "double_click"}]},
                    {"id": "j2", "name": "J2", "steps": []},
                    {"id": "j3", "name": "J3", "steps": []},
                    {"id": "j4", "name": "J4", "steps": []},
                    {"id": "j5", "name": "J5", "steps": []},
                ],
            }
        )
    )
    with pytest.raises(ConfigError, match="Unknown action"):
        load_config(path)
