"""Dashboard store helpers — config write API."""

from pathlib import Path

import pytest
import yaml

import json

from rehearse.dashboard.store import list_run_summaries, save_config


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


def test_run_state_json_does_not_duplicate_run_summary(tmp_path: Path) -> None:
    """RunStateMachine writes {run_id}-state.json with its own top-level run_id field.
    list_run_summaries() must not treat that as a second evidence file for the same
    run — it was producing duplicate rows in the run list UI for every single run."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    run_id = "myproduct-20260619-230616"

    (runs_dir / f"{run_id}.json").write_text(json.dumps({
        "run_id": run_id,
        "product_name": "My Product",
        "target_url": "https://example.com",
        "started_at": "2026-06-19T23:06:16+00:00",
        "finished_at": "2026-06-19T23:10:00+00:00",
        "duration_ms": 224000,
        "outcome": "complete",
        "steps": [],
    }))
    # RunStateMachine's own file — also has a top-level run_id, must be excluded
    (runs_dir / f"{run_id}-state.json").write_text(json.dumps({
        "run_id": run_id,
        "state": "COMPLETE",
        "log": [],
    }))

    summaries = list_run_summaries(tmp_path)
    matching = [s for s in summaries if s.get("id") == run_id]
    assert len(matching) == 1, f"expected exactly one summary for {run_id}, got {len(matching)}"


def test_save_config_disables_generic_personas_when_curated_journeys_exist(tmp_path: Path) -> None:
    """Once a config has its own persona-scoped journeys, the generic
    p1-evaluator/p2-operator/p3-admin templates must not silently stay enabled
    and run alongside personas the user actually selected."""
    first = save_config(tmp_path, {"targetUrl": "https://app.example.com"})

    # Simulate importing a discovered persona with its own persona-scoped journey
    first_path = Path(first["path"])
    data = _load_yaml_config(first_path)
    data["personas"].append({"id": "model-0-discovered", "name": "Discovered User", "role": "user", "goals": []})
    data["journeys"] = [
        {"id": "j-discovered-1", "name": "Discovered journey", "steps": [{"action": "navigate", "url": "/x"}],
         "persona_ids": ["model-0-discovered"]}
    ]
    first_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    second = save_config(
        tmp_path,
        {"targetUrl": "https://app.example.com", "existingConfigId": first["id"]},
    )
    merged = _load_yaml_config(Path(second["path"]))
    by_id = {p["id"]: p for p in merged["personas"]}
    assert by_id["p1-evaluator"]["enabled"] is False
    assert by_id["p2-operator"]["enabled"] is False
    assert by_id["p3-admin"]["enabled"] is False
    assert by_id["model-0-discovered"]["id"] == "model-0-discovered"


def test_save_config_respects_explicit_persona_enabled_override(tmp_path: Path) -> None:
    """personaEnabled in the request body must win over the auto-disable heuristic."""
    first = save_config(tmp_path, {"targetUrl": "https://app.example.com"})
    first_path = Path(first["path"])
    data = _load_yaml_config(first_path)
    data["personas"].append({"id": "model-0-discovered", "name": "Discovered User", "role": "user", "goals": []})
    data["journeys"] = [
        {"id": "j-discovered-1", "name": "Discovered journey", "steps": [{"action": "navigate", "url": "/x"}],
         "persona_ids": ["model-0-discovered"]}
    ]
    first_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    second = save_config(
        tmp_path,
        {
            "targetUrl": "https://app.example.com",
            "existingConfigId": first["id"],
            "personaEnabled": {"p1-evaluator": True},
        },
    )
    merged = _load_yaml_config(Path(second["path"]))
    by_id = {p["id"]: p for p in merged["personas"]}
    assert by_id["p1-evaluator"]["enabled"] is True
    assert by_id["p2-operator"]["enabled"] is False
