"""Per-persona journey discovery — each persona agent autonomously generates
its own journey set based on the ProductModel and its own goals/role.

This replaces the requirement to hand-write YAML journeys. The persona
reads the product, decides what it would do, how often, and what sub-flows
matter — including chatbot interactions, filter states, dashboard drilldowns.
"""

from __future__ import annotations

import json
import os
from typing import Any

_JOURNEY_SYSTEM = """You are a {persona_role} who uses software products.
Given a product description and your role + goals, you will plan exactly how you use this product.
Be realistic about your behaviour — what you actually care about, how often you use each feature,
what confuses or frustrates you, what you wish was easier. Be specific and detailed."""

_JOURNEY_PROMPT = """You are: {persona_name}
Your role: {persona_role}
Your goals: {persona_goals}

The product you use:
{product_summary}

Plan your usage of this product in detail. Return JSON:
{{
  "persona_id": "{persona_id}",
  "usage_pattern": {{
    "session_frequency": "daily|weekly|monthly",
    "avg_session_duration_min": 15,
    "primary_motivation": "why you open the product"
  }},
  "journeys": [
    {{
      "id": "j-{persona_id_short}-{n}",
      "name": "Clear journey name",
      "description": "What you are trying to accomplish",
      "frequency": "daily|weekly|occasional|onboarding-only",
      "priority": "critical|high|medium|low",
      "entry_point": "/path or page name",
      "steps": [
        {{
          "action": "navigate|click|fill|wait|assert_text|scroll",
          "description": "what you do and why",
          "url": "/path (for navigate steps)",
          "intent": "what element you target (for click/fill)",
          "value": "what you type (for fill)",
          "expected_outcome": "what should happen"
        }}
      ],
      "behavioral_intent": "what success looks like for you",
      "failure_signals": ["things that would frustrate you here"],
      "sub_flows": [
        {{
          "name": "sub-flow name",
          "trigger": "what triggers this sub-flow",
          "steps_description": "brief description"
        }}
      ]
    }}
  ],
  "critical_paths": ["journey IDs that are most important to you"],
  "pain_points_anticipated": [
    {{
      "area": "page or feature name",
      "concern": "specific concern from your perspective",
      "severity": "critical|moderate|minor"
    }}
  ],
  "chatbot_test_questions": ["question 1", "question 2"],
  "information_gaps": ["things you expect to find but may not"]
}}

Include 8-15 journeys covering daily tasks, edge cases, and things you'd do repeatedly.
Include sub-flows for pages with multiple states (chatbots, dashboards with filters, pagination).
Be specific about steps — not vague like 'use the feature' but 'click Filter dropdown, select Last 30 days'."""


def _api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("REHEARSE_LLM_API_KEY")


def _call_llm(prompt: str, system: str) -> dict[str, Any] | None:
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
                "temperature": 0.5,
                "max_tokens": 4000,
                "response_format": {"type": "json_object"},
            },
            timeout=90.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        return None


def _product_summary(model: dict[str, Any]) -> str:
    lines = [
        f"Purpose: {model.get('purpose', 'unknown')}",
        f"Type: {model.get('product_type', 'unknown')}",
        f"URL: {model.get('targetUrl', '')}",
        "",
        "Core features:",
    ]
    for f in (model.get("core_features") or [])[:8]:
        lines.append(f"  - {f}")
    lines.append("\nPrimary workflows:")
    for w in (model.get("primary_workflows") or [])[:6]:
        lines.append(f"  - {w.get('name')}: {w.get('description')} [{w.get('frequency')}]")
    tech = model.get("technical_surface") or {}
    features = [k.replace("has_", "") for k, v in tech.items() if v and k.startswith("has_")]
    if features:
        lines.append(f"\nTechnical features: {', '.join(features)}")
    ia = model.get("information_architecture") or {}
    if ia.get("dashboard_gaps"):
        lines.append(f"\nKnown navigation issues: {', '.join(ia['dashboard_gaps'][:3])}")
    return "\n".join(lines)


def discover_journeys_for_persona(
    persona: dict[str, Any],
    product_model: dict[str, Any],
) -> dict[str, Any]:
    """Generate journeys for one persona based on the product model."""
    pid = persona.get("id", "p-unknown")
    pid_short = pid.replace("p-", "").replace("p", "")[:8]
    system = _JOURNEY_SYSTEM.format(
        persona_role=persona.get("role", "user"),
    )
    prompt = _JOURNEY_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        persona_goals="; ".join(persona.get("goals") or ["use the product effectively"]),
        persona_id=pid,
        persona_id_short=pid_short,
        n="N",
        product_summary=_product_summary(product_model),
    )

    result = _call_llm(prompt, system)

    if not result:
        # Template fallback
        workflows = product_model.get("primary_workflows") or []
        result = {
            "persona_id": pid,
            "usage_pattern": {
                "session_frequency": "weekly",
                "avg_session_duration_min": 15,
                "primary_motivation": f"Accomplish {persona.get('role', 'user')} tasks",
            },
            "journeys": [
                {
                    "id": f"j-{pid_short}-{i+1}",
                    "name": w.get("name", f"Workflow {i+1}"),
                    "description": w.get("description", ""),
                    "frequency": w.get("frequency", "weekly"),
                    "priority": "high" if i == 0 else "medium",
                    "entry_point": w.get("entry_point", "/"),
                    "steps": [
                        {"action": "navigate", "url": w.get("entry_point", "/"),
                         "description": "Navigate to workflow entry"},
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
    else:
        result["source"] = "llm"

    result["personaName"] = persona.get("name", "")
    result["personaRole"] = persona.get("role", "")
    return result


def discover_journeys_for_all_personas(
    personas: list[dict[str, Any]],
    product_model: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run journey discovery for every persona in parallel (threaded)."""
    import threading
    results: list[dict[str, Any]] = [{}] * len(personas)

    def _worker(idx: int, persona: dict[str, Any]) -> None:
        results[idx] = discover_journeys_for_persona(persona, product_model)

    threads = [
        threading.Thread(target=_worker, args=(i, p), daemon=True)
        for i, p in enumerate(personas)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    return results
