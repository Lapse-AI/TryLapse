"""Persona draft API (L2-UI-68–69)."""

from pathlib import Path

import yaml

from rehearse.dashboard.config_yaml import append_persona_to_config
from rehearse.dashboard.persona_draft import (
    draft_persona_from_prompt,
    suggest_personas_for_product,
)
from rehearse.dashboard.store import save_config
from rehearse.dsl import active_personas, load_config
from rehearse.init_config import build_config, write_config


def test_draft_persona_template() -> None:
    out = draft_persona_from_prompt(
        "SOC2 reviewer who checks audit logs and SSO settings",
        product_name="Acme SaaS",
        target_url="https://app.example.com",
    )
    assert out["persona"]["id"].startswith("p")
    assert "compliance" in out["persona"]["role"].lower() or "security" in out["persona"]["role"].lower()
    assert out["yamlFragment"]
    assert out["source"] in ("template", "llm")


def test_suggest_personas_excludes_core() -> None:
    out = suggest_personas_for_product(
        product_name="DevTools API",
        target_url="https://api.example.com",
    )
    assert len(out["corePersonas"]) == 3
    ids = {p["id"] for p in out["suggested"]}
    assert "p1-evaluator" not in ids
    assert len(out["suggested"]) >= 1


def test_append_persona_to_config(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    cfg = build_config("https://persona-test.example.com", run_id_prefix="persona-test")
    write_config(artifacts / "configs" / "persona-test.yaml", cfg)
    append_persona_to_config(
        artifacts,
        config_id="persona-test",
        persona={
            "id": "p4-champion",
            "name": "Champion",
            "role": "team lead",
            "goals": ["Roll out to team"],
        },
    )
    data = yaml.safe_load((artifacts / "configs" / "persona-test.yaml").read_text())
    assert any(p["id"] == "p4-champion" for p in data["personas"])


def test_save_config_extra_personas_and_lens(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    save_config(
        artifacts,
        {
            "targetUrl": "https://save-persona.example.com",
            "personaLens": False,
            "personaEnabled": {"p2-operator": False},
            "extraPersonas": [
                {
                    "id": "p4-custom",
                    "name": "Custom",
                    "role": "niche user",
                    "goals": ["Do one thing well"],
                }
            ],
        },
    )
    cfg_path = next((artifacts / "configs").glob("*.yaml"))
    loaded = load_config(cfg_path)
    assert loaded.persona_lens is False
    assert any(p.id == "p4-custom" for p in loaded.personas)
    disabled = next(p for p in loaded.personas if p.id == "p2-operator")
    assert disabled.enabled is False
    assert active_personas(loaded) == []
