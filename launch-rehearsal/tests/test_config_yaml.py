"""Config YAML API helpers."""

from pathlib import Path

from rehearse.dashboard.config_yaml import (
    draft_journey_from_prompt,
    save_config_yaml,
    validate_config_yaml,
)
from rehearse.init_config import build_config, write_config


def test_validate_config_yaml_ok(tmp_path: Path) -> None:
    cfg = build_config("https://example.com")
    path = tmp_path / "t.yaml"
    write_config(path, cfg)
    result = validate_config_yaml(path.read_text())
    assert result["valid"] is True
    assert result["summary"]["journeyCount"] >= 5


def test_draft_journey_from_prompt() -> None:
    out = draft_journey_from_prompt(
        'Click the "Get started" button after landing',
        target_url="https://app.example.com",
    )
    assert "click" in str(out["journey"]["steps"]).lower()
    assert out["yamlFragment"]


def test_save_config_yaml_roundtrip(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    cfg = build_config("https://save-test.example.com", run_id_prefix="save-test")
    path = tmp_path / "in.yaml"
    write_config(path, cfg)
    text = path.read_text()
    saved = save_config_yaml(artifacts, text, config_id="save-test")
    assert saved["id"] == "save-test"
    assert (artifacts / "configs" / "save-test.yaml").is_file()
