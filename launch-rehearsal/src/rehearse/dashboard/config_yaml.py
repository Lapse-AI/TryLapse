"""YAML config load, validate, save, journey draft, and append helpers."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml

from rehearse.dashboard.store import list_configs
from rehearse.dsl import load_config
from rehearse.errors import ConfigError
from rehearse.dashboard.persona_draft import persona_to_yaml_entry


def _resolve_config_path(artifacts_root: Path, config_id: str) -> Path | None:
    cfg_dir = artifacts_root / "configs"
    candidate = cfg_dir / f"{config_id}.yaml"
    if candidate.is_file():
        return candidate
    for item in list_configs(artifacts_root):
        if item["id"] == config_id:
            p = Path(item["path"])
            if p.is_file():
                return p
    return None


def _experiment_payload(cfg) -> dict[str, str] | None:
    if not cfg.experiment:
        return None
    exp = cfg.experiment
    out: dict[str, str] = {}
    if exp.hypothesis:
        out["hypothesis"] = exp.hypothesis
    if exp.user_goal:
        out["userGoal"] = exp.user_goal
    if exp.variant_label:
        out["variantLabel"] = exp.variant_label
    return out or None


def get_config_yaml(artifacts_root: Path, config_id: str) -> dict[str, Any]:
    path = _resolve_config_path(artifacts_root, config_id)
    if not path:
        raise ValueError(f"Config not found: {config_id}")
    payload: dict[str, Any] = {
        "id": path.stem,
        "path": str(path.resolve()),
        "yaml": path.read_text(),
    }
    try:
        cfg = load_config(path)
        payload["experiment"] = _experiment_payload(cfg)
    except ConfigError:
        payload["experiment"] = None
    return payload


def validate_config_yaml(yaml_text: str) -> dict[str, Any]:
    if not yaml_text.strip():
        return {"valid": False, "errors": ["YAML is empty"]}
    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as exc:
        return {"valid": False, "errors": [f"YAML parse error: {exc}"]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write(yaml_text)
        tmp_path = Path(tmp.name)
    try:
        load_config(tmp_path)
    except ConfigError as exc:
        return {"valid": False, "errors": [str(exc)]}
    finally:
        tmp_path.unlink(missing_ok=True)
    run = data.get("run") or {}
    journeys = data.get("journeys") or []
    exp = data.get("experiment") if isinstance(data.get("experiment"), dict) else {}
    return {
        "valid": True,
        "errors": [],
        "summary": {
            "targetUrl": run.get("target_url"),
            "productName": run.get("product_name"),
            "personaCount": len(data.get("personas") or []),
            "journeyCount": len(journeys),
            "hasExperiment": bool(exp),
        },
    }


def set_config_experiment(
    artifacts_root: Path,
    *,
    config_id: str,
    hypothesis: str = "",
    user_goal: str = "",
    variant_label: str = "",
) -> dict[str, Any]:
    """Merge optional experiment block into config YAML (L3-PRED-02)."""
    meta = get_config_yaml(artifacts_root, config_id)
    data = yaml.safe_load(meta["yaml"]) or {}
    fields = {
        "hypothesis": (hypothesis or "").strip(),
        "user_goal": (user_goal or "").strip(),
        "variant_label": (variant_label or "").strip(),
    }
    if any(fields.values()):
        data["experiment"] = {k: v for k, v in fields.items() if v}
    elif "experiment" in data:
        del data["experiment"]
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return save_config_yaml(artifacts_root, new_yaml, config_id=config_id)


def append_persona_to_config(
    artifacts_root: Path,
    *,
    config_id: str,
    persona: dict[str, Any],
) -> dict[str, Any]:
    """Append or replace a persona entry on saved config."""
    meta = get_config_yaml(artifacts_root, config_id)
    data = yaml.safe_load(meta["yaml"]) or {}
    personas = list(data.get("personas") or [])
    entry = persona_to_yaml_entry(persona)
    personas = [p for p in personas if p.get("id") != entry["id"]]
    personas.append(entry)
    data["personas"] = personas
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return save_config_yaml(artifacts_root, new_yaml, config_id=config_id)


def update_config_personas(
    artifacts_root: Path,
    *,
    config_id: str,
    persona_enabled: dict[str, bool] | None = None,
    persona_lens: bool | None = None,
) -> dict[str, Any]:
    """Toggle core/extra personas or persona lens on existing config."""
    meta = get_config_yaml(artifacts_root, config_id)
    data = yaml.safe_load(meta["yaml"]) or {}
    run = data.setdefault("run", {})
    if persona_lens is not None:
        run["persona_lens"] = bool(persona_lens)
    if persona_enabled:
        personas = list(data.get("personas") or [])
        for p in personas:
            pid = p.get("id")
            if pid in persona_enabled:
                p["enabled"] = bool(persona_enabled[pid])
        data["personas"] = personas
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return save_config_yaml(artifacts_root, new_yaml, config_id=config_id)


def save_config_yaml(artifacts_root: Path, yaml_text: str, *, config_id: str | None = None) -> dict[str, Any]:
    check = validate_config_yaml(yaml_text)
    if not check["valid"]:
        raise ValueError("; ".join(check["errors"]))
    data = yaml.safe_load(yaml_text) or {}
    slug = config_id or (data.get("run") or {}).get("run_id_prefix") or "config"
    cfg_dir = artifacts_root / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    path = cfg_dir / f"{slug}.yaml"
    path.write_text(yaml_text)
    return {"id": path.stem, "path": str(path.resolve()), "name": (data.get("run") or {}).get("product_name")}


def draft_journey_from_prompt(prompt: str, *, target_url: str) -> dict[str, Any]:
    """Template-first journey draft; optional LLM enrichment later."""
    prompt = (prompt or "").strip()
    if len(prompt) < 8:
        raise ValueError("Describe the journey in at least a few words")
    base = target_url.rstrip("/")
    slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower())[:32].strip("-") or "custom"
    journey_id = f"j-custom-{slug[:20]}"

    steps: list[dict[str, Any]] = [
        {"action": "navigate", "url": f"{base}/"},
        {"action": "wait", "value": "2000"},
    ]
    lower = prompt.lower()
    if any(w in lower for w in ("click", "button", "cta", "submit", "sign up", "login")):
        intent = _extract_quoted_intent(prompt) or prompt[:60]
        steps.append({"action": "click", "intent": intent})
    elif any(w in lower for w in ("fill", "form", "email", "password", "type")):
        steps.append({"action": "fill", "intent": "email", "value": "${REHEARSE_EMAIL}"})
    elif any(w in lower for w in ("explore", "discover", "find", "search")):
        steps.append({"action": "explore", "value": "2"})
    else:
        steps.append({"action": "explore", "value": "1"})

    journey = {
        "id": journey_id,
        "name": prompt[:80],
        "priority": "critical",
        "steps": steps,
    }
    fragment = yaml.dump(
        [{"id": journey["id"], "name": journey["name"], "priority": "critical", "steps": steps}],
        default_flow_style=False,
        sort_keys=False,
    )
    return {
        "journey": journey,
        "yamlFragment": fragment,
        "source": "template",
        "hint": "Paste under journeys: in your config, then validate and save on Workspace.",
    }


def _extract_quoted_intent(prompt: str) -> str | None:
    for quote in ('"', "'", "“", "”"):
        if quote in prompt:
            parts = prompt.split(quote)
            if len(parts) >= 3 and parts[1].strip():
                return parts[1].strip()
    return None


def append_navigate_journey(
    artifacts_root: Path,
    *,
    config_id: str,
    path: str,
    title: str | None = None,
) -> dict[str, Any]:
    path = path if path.startswith("/") else f"/{path}"
    meta = get_config_yaml(artifacts_root, config_id)
    data = yaml.safe_load(meta["yaml"]) or {}
    base = (data.get("run") or {}).get("target_url", "").rstrip("/")
    if not base:
        raise ValueError("Config missing run.target_url")
    journeys = list(data.get("journeys") or [])
    jid = f"j-sitemap-{re.sub(r'[^a-z0-9]+', '-', path.strip('/').lower())[:24] or 'root'}"
    if any(j.get("id") == jid for j in journeys):
        jid = f"{jid}-2"
    name = title or f"Visit {path}"
    url = urljoin(f"{base}/", path.lstrip("/"))
    journeys.append(
        {
            "id": jid,
            "name": name,
            "priority": "smoke",
            "steps": [{"action": "navigate", "url": url}, {"action": "wait", "value": "1500"}],
        }
    )
    data["journeys"] = journeys
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    save_config_yaml(artifacts_root, new_yaml, config_id=config_id)
    return {"configId": config_id, "journeyId": jid, "url": url}
