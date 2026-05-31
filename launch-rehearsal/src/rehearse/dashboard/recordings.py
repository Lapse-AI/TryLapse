"""Journey step recorder — compile steps to YAML fragment (BRW-C2)."""

from __future__ import annotations

from typing import Any

import yaml

from rehearse.dsl import ALLOWED_ACTIONS

_ALLOWED = set(ALLOWED_ACTIONS)


def compile_journey_yaml(
    *,
    journey_id: str,
    journey_name: str,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate steps and return YAML snippet for Init / config merge."""
    cleaned: list[dict[str, Any]] = []
    errors: list[str] = []
    for i, raw in enumerate(steps):
        action = str(raw.get("action") or "").strip()
        if action not in _ALLOWED:
            errors.append(f"step {i + 1}: unknown action '{action}'")
            continue
        step: dict[str, Any] = {"action": action}
        for key in ("url", "intent", "selector", "value"):
            if raw.get(key) is not None and str(raw.get(key)).strip():
                step[key] = raw[key]
        if action == "navigate" and not step.get("url"):
            errors.append(f"step {i + 1}: navigate requires url")
        cleaned.append(step)

    fragment = {
        "id": journey_id,
        "name": journey_name,
        "steps": cleaned,
    }
    yaml_text = yaml.dump(
        {"journeys": [fragment]},
        default_flow_style=False,
        sort_keys=False,
    )
    return {
        "journeyId": journey_id,
        "journeyName": journey_name,
        "steps": cleaned,
        "errors": errors,
        "yaml": yaml_text,
        "valid": len(errors) == 0 and len(cleaned) > 0,
    }
