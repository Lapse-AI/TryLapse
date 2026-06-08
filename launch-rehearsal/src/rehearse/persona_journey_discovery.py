"""Per-persona journey discovery — each persona agent autonomously generates
its own journey set based on the ProductModel and its own goals/role.

This replaces the requirement to hand-write YAML journeys. The persona
reads the product, decides what it would do, how often, and what sub-flows
matter — including chatbot interactions, filter states, dashboard drilldowns.

Two-phase approach to avoid LLM token truncation:
  Phase 1 — Journey plan: LLM emits a list of journey metadata (no steps).
             Small, fast, never truncates.
  Phase 2 — Step expansion: For each journey, LLM generates deep step-by-step
             instructions, sub-flows, failure signals. One call per journey,
             each fitting cleanly in the token budget.
"""

from __future__ import annotations

import json
import os
from typing import Any

# ── System prompts ────────────────────────────────────────────────────────────

_PLAN_SYSTEM = """You are a {persona_role} who uses software products.
You deeply understand your own usage patterns — when you open the product,
what you actually care about, what frustrates you, what you return to daily.
Be realistic, specific, and grounded in the product description provided."""

_PLAN_PROMPT = """You are: {persona_name}
Your role: {persona_role}
Your goals: {persona_goals}

The product you use:
{product_summary}

List every distinct journey you undertake with this product — daily tasks,
weekly routines, onboarding steps, edge cases, admin actions, recovery flows,
anything you'd do more than once. Cover breadth: happy paths, frustrated paths,
exploratory paths, and anything persona-specific.

Return JSON only:
{{
  "persona_id": "{persona_id}",
  "usage_pattern": {{
    "session_frequency": "daily|weekly|monthly",
    "avg_session_duration_min": <integer>,
    "primary_motivation": "<why you open the product>"
  }},
  "journey_plan": [
    {{
      "id": "j-{pid_short}-1",
      "name": "<clear journey title>",
      "description": "<what you accomplish in one sentence>",
      "frequency": "daily|weekly|occasional|onboarding-only",
      "priority": "critical|high|medium|low",
      "entry_point": "<URL path or page name>",
      "behavioral_intent": "<what success looks like from your perspective>",
      "failure_signals": ["<thing that would frustrate you>", "..."],
      "sub_flow_hints": ["<name of a modal/filter/state worth testing>", "..."]
    }}
  ],
  "critical_paths": ["<journey id of the most important ones>"],
  "pain_points_anticipated": [
    {{"area": "<page/feature>", "concern": "<specific concern>", "severity": "critical|moderate|minor"}}
  ],
  "chatbot_test_questions": ["<question you'd ask the product's chatbot/help>"],
  "information_gaps": ["<thing you expect to find but might not>"]
}}

Include 8–14 journeys. Do not include steps — only metadata."""

_EXPAND_SYSTEM = """You are a {persona_role} walking through a specific workflow.
Write every step precisely — not vague descriptions but exact browser actions:
which element to click, what to type, what URL to navigate to, what to assert.
Think like a test engineer writing Playwright steps for this persona."""

_EXPAND_PROMPT = """Persona: {persona_name} ({persona_role})
Goals: {persona_goals}

Product:
{product_summary}

Journey to expand:
  ID: {journey_id}
  Name: {journey_name}
  Description: {journey_description}
  Entry point: {entry_point}
  Behavioral intent: {behavioral_intent}
  Sub-flows to cover: {sub_flow_hints}

Write the complete step-by-step execution of this journey. Include:
- The main happy path
- Key sub-flows (e.g. opening a modal, using a filter, changing a setting)
- At least one assertion step to verify the outcome
- Realistic fill values (use ${{REHEARSE_EMAIL}} / ${{REHEARSE_PASSWORD}} for auth)

Return JSON only:
{{
  "journey_id": "{journey_id}",
  "steps": [
    {{
      "action": "navigate|click|fill|wait|scroll|hover|select|press|assert_url_contains|open_link|explore|dismiss",
      "description": "<what you do and why>",
      "url": "<full URL or path, for navigate steps>",
      "intent": "<natural language description of the element, for click/fill/scroll>",
      "selector": "<CSS selector if you know it precisely, otherwise omit>",
      "value": "<text to type, wait ms, key to press, or text to assert>",
      "expected_outcome": "<what should happen after this step>"
    }}
  ],
  "sub_flows": [
    {{
      "name": "<sub-flow name>",
      "trigger": "<what causes this sub-flow>",
      "steps": [
        {{"action": "...", "description": "...", "intent": "..."}}
      ]
    }}
  ]
}}

Include 6–14 steps in the main path. Cover the sub-flows listed above.
Be precise: 'click the blue Submit button in the booking form' not 'submit the form'."""


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("REHEARSE_LLM_API_KEY")


def _repair_json(raw: str) -> dict[str, Any] | None:
    """Attempt to parse JSON; if truncated, recover the last complete object."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Walk forward tracking bracket depth; remember last position where depth hit 0
    depth_obj = depth_arr = 0
    last_valid = 0
    in_string = escape_next = False
    for i, ch in enumerate(raw):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth_obj += 1
        elif ch == "}":
            depth_obj -= 1
            if depth_obj == 0 and depth_arr == 0:
                last_valid = i + 1
        elif ch == "[":
            depth_arr += 1
        elif ch == "]":
            depth_arr -= 1
    if last_valid:
        try:
            return json.loads(raw[:last_valid])
        except json.JSONDecodeError:
            pass
    return None


def _call_llm(prompt: str, system: str, *, max_tokens: int = 3000) -> dict[str, Any] | None:
    key = _api_key()
    if not key:
        return None
    try:
        import httpx
        base = os.environ.get("REHEARSE_LLM_BASE_URL", "https://api.deepseek.com/v1")
        model = os.environ.get("REHEARSE_LLM_MODEL", "deepseek-chat")
        resp = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        choice = resp.json()["choices"][0]
        raw = choice["message"]["content"]
        finish = choice.get("finish_reason", "")
        result = _repair_json(raw)
        if result and finish == "length":
            result["_truncated"] = True
        return result
    except Exception:
        return None


# ── Product model summariser ─────────────────────────────────────────────────

def _product_summary(model: dict[str, Any]) -> str:
    lines = [
        f"Purpose: {model.get('purpose', 'unknown')}",
        f"Type: {model.get('product_type', 'unknown')}",
        f"URL: {model.get('targetUrl', '')}",
        "",
        "Core features:",
    ]
    for f in (model.get("core_features") or [])[:10]:
        lines.append(f"  - {f}")
    lines.append("\nPrimary workflows:")
    for w in (model.get("primary_workflows") or [])[:8]:
        lines.append(
            f"  - {w.get('name')}: {w.get('description')} "
            f"[{w.get('frequency')}] entry: {w.get('entry_point', '/')}"
        )
    tech = model.get("technical_surface") or {}
    features = [k.replace("has_", "") for k, v in tech.items() if v and k.startswith("has_")]
    if features:
        lines.append(f"\nTechnical features: {', '.join(features)}")
    ia = model.get("information_architecture") or {}
    if ia.get("dashboard_gaps"):
        lines.append(f"Navigation gaps: {', '.join(ia['dashboard_gaps'][:4])}")
    user_types = model.get("user_types_observed") or []
    if user_types:
        type_names = [u.get("type", "?") for u in user_types[:5]]
        lines.append(f"User types observed: {', '.join(type_names)}")
    quality = model.get("quality_concerns") or []
    if quality:
        quality_items = [q.get("concern", "?") for q in quality[:3]]
        lines.append(f"Known concerns: {', '.join(quality_items)}")
    return "\n".join(lines)


# ── Phase 1: journey plan ─────────────────────────────────────────────────────

def _discover_journey_plan(
    persona: dict[str, Any],
    product_model: dict[str, Any],
) -> dict[str, Any] | None:
    """Ask LLM for journey metadata (no steps) — fast, small, never truncates."""
    pid = persona.get("id", "p-unknown")
    pid_short = pid.replace("p-", "").replace("p", "")[:8]
    system = _PLAN_SYSTEM.format(persona_role=persona.get("role", "user"))
    prompt = _PLAN_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        persona_goals="; ".join(persona.get("goals") or ["use the product effectively"]),
        persona_id=pid,
        pid_short=pid_short,
        product_summary=_product_summary(product_model),
    )
    return _call_llm(prompt, system, max_tokens=2500)


# ── Phase 2: step expansion ───────────────────────────────────────────────────

def _expand_journey_steps(
    journey_meta: dict[str, Any],
    persona: dict[str, Any],
    product_model: dict[str, Any],
) -> dict[str, Any]:
    """Expand a single journey into full deep steps. One focused LLM call."""
    system = _EXPAND_SYSTEM.format(persona_role=persona.get("role", "user"))
    prompt = _EXPAND_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        persona_goals="; ".join(persona.get("goals") or ["use the product effectively"]),
        product_summary=_product_summary(product_model),
        journey_id=journey_meta.get("id", "j-1"),
        journey_name=journey_meta.get("name", "Journey"),
        journey_description=journey_meta.get("description", ""),
        entry_point=journey_meta.get("entry_point", "/"),
        behavioral_intent=journey_meta.get("behavioral_intent", ""),
        sub_flow_hints=", ".join(journey_meta.get("sub_flow_hints") or []) or "none",
    )
    result = _call_llm(prompt, system, max_tokens=3500)
    if not result:
        # Fallback: minimal navigate + wait steps from entry_point
        entry = journey_meta.get("entry_point", "/")
        result = {
            "journey_id": journey_meta.get("id"),
            "steps": [
                {"action": "navigate", "url": entry, "description": f"Navigate to {entry}",
                 "expected_outcome": "Page loads"},
                {"action": "wait", "value": "2000", "description": "Wait for page to settle"},
            ],
            "sub_flows": [],
            "_fallback": True,
        }
    return result


# ── Template fallback ─────────────────────────────────────────────────────────

def _template_fallback(persona: dict[str, Any], product_model: dict[str, Any]) -> dict[str, Any]:
    pid = persona.get("id", "p-unknown")
    pid_short = pid.replace("p-", "").replace("p", "")[:8]
    workflows = product_model.get("primary_workflows") or []
    return {
        "persona_id": pid,
        "usage_pattern": {
            "session_frequency": "weekly",
            "avg_session_duration_min": 15,
            "primary_motivation": f"Accomplish {persona.get('role', 'user')} tasks",
        },
        "journeys": [
            {
                "id": f"j-{pid_short}-{i + 1}",
                "name": w.get("name", f"Workflow {i + 1}"),
                "description": w.get("description", ""),
                "frequency": w.get("frequency", "weekly"),
                "priority": "high" if i == 0 else "medium",
                "entry_point": w.get("entry_point", "/"),
                "steps": [
                    {"action": "navigate", "url": w.get("entry_point", "/"),
                     "description": "Navigate to workflow entry",
                     "expected_outcome": "Page loads"},
                    {"action": "wait", "value": "2000", "description": "Wait for load"},
                ],
                "behavioral_intent": f"Complete {w.get('name', 'task')} successfully",
                "failure_signals": ["page doesn't load", "action fails"],
                "sub_flows": [],
            }
            for i, w in enumerate(workflows[:5])
        ],
        "critical_paths": [f"j-{pid_short}-1"],
        "pain_points_anticipated": [],
        "chatbot_test_questions": [],
        "information_gaps": [],
        "source": "template",
    }


# ── Public API ────────────────────────────────────────────────────────────────

def discover_journeys_for_persona(
    persona: dict[str, Any],
    product_model: dict[str, Any],
) -> dict[str, Any]:
    """Two-phase deep journey discovery for one persona.

    Phase 1: LLM emits journey plan (8–14 journeys, metadata only, ~2K tokens).
    Phase 2: For each journey, LLM expands full steps + sub-flows (~3K tokens each).
    This guarantees unlimited depth without ever hitting the token limit.
    """
    pid = persona.get("id", "p-unknown")

    # ── Phase 1: get the journey plan ────────────────────────────────────────
    plan = _discover_journey_plan(persona, product_model)
    if not plan or not plan.get("journey_plan"):
        return _template_fallback(persona, product_model)

    journey_plan: list[dict[str, Any]] = plan.get("journey_plan") or []

    # ── Phase 2: expand each journey's steps in parallel ─────────────────────
    import threading
    expanded: dict[str, dict[str, Any]] = {}

    def _expand(jm: dict[str, Any]) -> None:
        jid = jm.get("id", "")
        expanded[jid] = _expand_journey_steps(jm, persona, product_model)

    threads = [
        threading.Thread(target=_expand, args=(jm,), daemon=True)
        for jm in journey_plan
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=90)

    # ── Merge metadata + steps ────────────────────────────────────────────────
    journeys: list[dict[str, Any]] = []
    for jm in journey_plan:
        jid = jm.get("id", "")
        expansion = expanded.get(jid, {})
        journeys.append({
            **jm,
            "steps": expansion.get("steps") or [],
            "sub_flows": expansion.get("sub_flows") or [],
        })

    result: dict[str, Any] = {
        "persona_id": pid,
        "usage_pattern": plan.get("usage_pattern", {}),
        "journeys": journeys,
        "critical_paths": plan.get("critical_paths", []),
        "pain_points_anticipated": plan.get("pain_points_anticipated", []),
        "chatbot_test_questions": plan.get("chatbot_test_questions", []),
        "information_gaps": plan.get("information_gaps", []),
        "source": "llm",
        "personaName": persona.get("name", ""),
        "personaRole": persona.get("role", ""),
    }
    return result


def discover_journeys_for_all_personas(
    personas: list[dict[str, Any]],
    product_model: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run journey discovery for every persona (personas run in parallel,
    but within each persona Phase 2 expansions also run in parallel)."""
    import threading
    results: list[dict[str, Any]] = [{} for _ in range(len(personas))]

    def _worker(idx: int, persona: dict[str, Any]) -> None:
        results[idx] = discover_journeys_for_persona(persona, product_model)

    threads = [
        threading.Thread(target=_worker, args=(i, p), daemon=True)
        for i, p in enumerate(personas)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=300)
    return results


# ── Config connector ──────────────────────────────────────────────────────────

def discovered_journey_to_config_entry(journey: dict[str, Any]) -> dict[str, Any]:
    """Convert a discovered journey into a YAML-config-ready dict.

    Strips behavioral metadata (behavioral_intent, failure_signals, etc.) that
    is used only by the behavioral judge. Keeps only what the DSL Step consumes:
    action, url, intent, selector, value.
    """
    _ALLOWED = {
        "navigate", "click", "fill", "wait", "hover", "scroll",
        "select", "press", "assert_url_contains", "open_link",
        "explore", "dismiss",
    }
    clean_steps: list[dict[str, Any]] = []
    for raw in journey.get("steps") or []:
        action = str(raw.get("action") or "").strip()
        if action not in _ALLOWED:
            # Map common LLM aliases
            action = {"type": "fill", "go_to": "navigate"}.get(action, "")
            if not action:
                continue
        step: dict[str, Any] = {"action": action}
        for key in ("url", "intent", "selector", "value"):
            v = raw.get(key)
            if v is not None and str(v).strip():
                step[key] = str(v).strip()
        clean_steps.append(step)

    if not clean_steps:
        entry_point = journey.get("entry_point", "/")
        clean_steps = [
            {"action": "navigate", "url": entry_point},
            {"action": "wait", "value": "2000"},
        ]

    return {
        "id": journey.get("id", "j-unknown"),
        "name": journey.get("name", "Untitled journey"),
        "steps": clean_steps,
    }
