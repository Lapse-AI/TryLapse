"""Dashboard store helpers — config write API."""

from pathlib import Path

import pytest
import yaml

from rehearse.dashboard.store import save_config


def _load_yaml_config(path: Path) -> dict:
    lines = [line for line in path.read_text().splitlines() if not line.startswith("#")]
    return yaml.safe_load("\n".join(lines))


def test_save_config_writes_yaml(tmp_path: Path) -> None:
    result = save_config(
        tmp_path,
        {"targetUrl": "https://app.example.com", "productName": "Example App"},
    )
    assert result["id"]
    assert result["name"] == "Example App"
    path = Path(result["path"])
    assert path.is_file()
    data = _load_yaml_config(path)
    assert data["run"]["target_url"] == "https://app.example.com"
    assert data["run"]["product_name"] == "Example App"


def test_save_config_requires_target_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="targetUrl"):
        save_config(tmp_path, {})


def test_save_config_with_auth(tmp_path: Path) -> None:
    result = save_config(
        tmp_path,
        {"targetUrl": "https://secure.example.com", "withAuth": True},
    )
    data = _load_yaml_config(Path(result["path"]))
    assert "auth" in data


def test_save_config_execute_all_personas_in_browser(tmp_path: Path) -> None:
    result = save_config(
        tmp_path,
        {
            "targetUrl": "https://app.example.com",
            "executeAllPersonasInBrowser": True,
        },
    )
    data = _load_yaml_config(Path(result["path"]))
    assert data["run"]["execute_all_personas_in_browser"] is True
