"""Draft and suggest personas for Init wizard (L2-UI-68–69)."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

import yaml

from rehearse.llm import llm_enabled

PERSONA_DRAFT_SYSTEM = """You draft synthetic user personas for Launch Rehearsal — pre-launch product evaluation.
Respond with JSON only:
{
  "id": "p4-slug",
  "name": "Short display name",
  "role": "one-line role",
  "goals": ["goal 1", "goal 2"]
}
Rules:
- id must start with p and use lowercase letters, digits, hyphens only (e.g. p4-security-reviewer)
- goals: 1-3 concrete goals tied to the user description
- do not duplicate the three core archetypes (evaluator, daily operator, admin) unless the prompt is very specific
"""


def _slug_id(text: str, *, prefix: str = "p4") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:28]
    return f"{prefix}-{slug}" if slug else f"{prefix}-custom"


def _infer_role(prompt: str) -> str:
    lower = prompt.lower()
    if any(w in lower for w in ("security", "compliance", "soc2", "audit", "pen test")):
        return "security / compliance reviewer"
    if any(w in lower for w in ("billing", "finance", "procurement", "buyer")):
        return "buyer / finance stakeholder"
    if any(w in lower for w in ("support", "cs ", "customer success", "onboarding")):
        return "customer success / onboarding specialist"
    if any(w in lower for w in ("developer", "engineer", "api", "devtool")):
        return "developer / integrator"
    if any(w in lower for w in ("executive", "vp ", "director", "champion")):
        return "executive champion"
    if any(w in lower for w in ("mobile", "field", "offline")):
        return "mobile / field user"
    return "specialized user"


def _template_persona(prompt: str, *, product_name: str | None = None) -> dict[str, Any]:
    prompt = prompt.strip()
    role = _infer_role(prompt)
    short_name = prompt.split(".")[0].split(",")[0].strip()
    if len(short_name) > 42:
        short_name = short_name[:39] + "…"
    name = short_name.title() if short_name else "Custom persona"
    goals = [prompt[:160]]
    if product_name:
        goals.append(f"Evaluate {product_name} from a {role} perspective")
    return {
        "id": _slug_id(prompt),
        "name": name,
        "role": role,
        "goals": goals[:3],
        "enabled": True,
        "source": "template",
    }


def _normalize_persona(raw: dict[str, Any], *, source: str = "llm") -> dict[str, Any]:
    pid = str(raw.get("id") or _slug_id(str(raw.get("name") or "custom")))
    pid = re.sub(r"[^a-z0-9-]", "-", pid.lower()).strip("-")
    if not pid.startswith("p"):
        pid = f"p4-{pid}"
    goals_raw = raw.get("goals") or []
    if isinstance(goals_raw, str):
        goals = [goals_raw]
    else:
        goals = [str(g).strip() for g in goals_raw if str(g).strip()]
    if not goals:
        goals = ["Complete primary workflow without friction"]
    return {
        "id": pid[:40],
        "name": str(raw.get("name") or "Custom persona")[:80],
        "role": str(raw.get("role") or "specialized user")[:120],
        "goals": goals[:3],
        "enabled": bool(raw.get("enabled", True)),
        "source": source,
    }


def _draft_persona_llm(
    prompt: str,
    *,
    product_name: str | None,
    target_url: str | None,
) -> dict[str, Any] | None:
    if not llm_enabled():
        return None
    from rehearse.llm import _api_key, _base_url, _http_timeout, _max_retries, _model, _post_chat

    import httpx
    import time

    key = _api_key()
    if not key:
        return None

    context = {
        "user_description": prompt,
        "product_name": product_name,
        "target_url": target_url,
        "core_personas_already_defined": [
            "First-time evaluator (prospect / new user)",
            "Daily operator (power user)",
            "Admin / buyer (IT admin)",
        ],
    }
    payload: dict[str, Any] = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": PERSONA_DRAFT_SYSTEM},
            {"role": "user", "content": json.dumps(context, indent=2)},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }
    timeout = _http_timeout()
    content: str | None = None
    for attempt in range(_max_retries() + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = _post_chat(client, payload)
                if resp.status_code >= 400 and "response_format" in payload:
                    payload = {k: v for k, v in payload.items() if k != "response_format"}
                    resp = _post_chat(client, payload)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                break
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt < _max_retries():
                time.sleep(2**attempt)
                continue
            return None
        except Exception:
            return None

    if not content:
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            return None
        parsed = json.loads(match.group())
    if not isinstance(parsed, dict):
        return None
    return _normalize_persona(parsed, source="llm")


def draft_persona_from_prompt(
    prompt: str,
    *,
    product_name: str | None = None,
    target_url: str | None = None,
) -> dict[str, Any]:
    """Turn natural-language user need into a persona dict + YAML fragment."""
    prompt = (prompt or "").strip()
    if len(prompt) < 6:
        raise ValueError("Describe the user in at least a few words")

    persona = _draft_persona_llm(prompt, product_name=product_name, target_url=target_url)
    if persona is None:
        persona = _template_persona(prompt, product_name=product_name)

    fragment = yaml.dump(
        [persona_to_yaml_entry(persona)],
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    return {
        "persona": persona,
        "yamlFragment": fragment,
        "source": persona.get("source", "template"),
        "hint": "Append under personas: in your config, or use Add to config after generating YAML.",
    }


def persona_to_yaml_entry(persona: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": persona["id"],
        "name": persona["name"],
        "role": persona["role"],
        "goals": list(persona.get("goals") or []),
    }
    if persona.get("enabled") is False:
        entry["enabled"] = False
    return entry


CORE_PERSONAS: list[dict[str, Any]] = [
    {
        "id": "p1-evaluator",
        "name": "First-time evaluator",
        "role": "prospect / new user",
        "goals": ["Understand value from landing and primary workflow"],
        "core": True,
        "enabled": True,
    },
    {
        "id": "p2-operator",
        "name": "Daily operator",
        "role": "power user",
        "goals": ["Complete core tasks quickly and reliably"],
        "core": True,
        "enabled": True,
    },
    {
        "id": "p3-admin",
        "name": "Admin / buyer",
        "role": "IT admin",
        "goals": ["Verify access boundaries and trust signals"],
        "core": True,
        "enabled": True,
    },
]


def _product_hints(product_name: str, host: str) -> list[dict[str, Any]]:
    blob = f"{product_name} {host}".lower()
    suggestions: list[dict[str, Any]] = []

    def add(pid_suffix: str, name: str, role: str, goals: list[str]) -> None:
        suggestions.append(
            {
                "id": f"p4-{pid_suffix}",
                "name": name,
                "role": role,
                "goals": goals,
                "enabled": True,
                "core": False,
                "reason": f"Common for products like {product_name or host}",
            }
        )

    if any(w in blob for w in ("b2b", "saas", "enterprise", "dashboard", "platform")):
        add(
            "champion",
            "Internal champion",
            "team lead / champion",
            ["Validate rollout to their team", "Find blockers before wider launch"],
        )
    if any(w in blob for w in ("api", "dev", "developer", "tool", "github")):
        add(
            "integrator",
            "Developer integrator",
            "engineer integrating the product",
            ["Complete API setup and first successful call", "Find docs and error clarity gaps"],
        )
    if any(w in blob for w in ("health", "hipaa", "clinical", "patient", "finance", "bank")):
        add(
            "compliance",
            "Compliance reviewer",
            "security / compliance buyer",
            ["Verify trust signals and data handling UX", "Find deal-breakers before POC"],
        )
    if any(w in blob for w in ("shop", "checkout", "commerce", "store")):
        add(
            "shopper",
            "First-time shopper",
            "new customer",
            ["Complete purchase without support", "Understand shipping and returns"],
        )
    if any(w in blob for w in ("cal.", "booking", "schedule", "calendar")):
        add(
            "scheduler",
            "Meeting booker",
            "prospect booking time",
            ["Book a slot without creating unnecessary friction", "Trust the booking confirmation flow"],
        )

    # Always offer a skeptic if nothing matched
    if not suggestions:
        add(
            "skeptic",
            "Skeptical evaluator",
            "hard-to-convince buyer",
            ["Find reasons not to adopt", "Stress-test claims on pricing and security pages"],
        )
    return suggestions[:4]


def suggest_personas_for_product(
    *,
    product_name: str | None = None,
    target_url: str | None = None,
    existing_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Suggest optional personas beyond the core three (template/heuristic)."""
    host = urlparse(target_url or "").netloc.replace("www.", "")
    product = (product_name or host.split(".")[0] or "your product").strip()
    existing = set(existing_ids or [])
    for core in CORE_PERSONAS:
        existing.add(core["id"])

    raw = _product_hints(product, host)
    filtered = [s for s in raw if s["id"] not in existing]
    return {
        "corePersonas": CORE_PERSONAS,
        "suggested": filtered,
        "source": "heuristic",
        "hint": "Core three are always in generated YAML. Add suggestions or AI drafts as extras.",
    }


# ── Library persona AI generation ─────────────────────────────────────────────
# This generates a richer persona than draft_persona_from_prompt: it includes
# all five behavioral depth fields (tech_literacy, patience, trust_level,
# character, usage_context) and optional tags.  It is used by the Persona
# Library page — not the Init wizard.

_LIBRARY_PERSONA_SYSTEM = """You are a UX research expert generating a richly detailed synthetic user persona
for product evaluation.  The persona will be saved to a reusable persona library and used to
drive automated browser-based journey testing.

Respond with JSON only — no markdown fences, no commentary:
{
  "name": "Short display name (2-4 words)",
  "role": "One-line job title or role description",
  "goals": ["goal 1 (specific, action-oriented)", "goal 2", "goal 3"],
  "tech_literacy": "novice|intermediate|expert",
  "patience": "low|medium|high",
  "trust_level": "skeptical|neutral|trusting",
  "character": "2-3 sentence psychological texture — habits, anxieties, quirks that shape UX decisions",
  "usage_context": "One sentence: how they arrive at this product (e.g. 'Switching from Competitor X', 'First time trying a tool like this', 'Assigned by IT after company rollout')",
  "tags": ["tag1", "tag2"]
}

Rules:
- goals: 2-4 concrete, observable outcomes — not aspirations, but tasks they'd measure success by
- tech_literacy: choose the one that best describes how they interact with software products
- patience: how long they'll tolerate confusion before abandoning a flow
- trust_level: default disposition toward new software — do they read fine print or just click accept?
- character: be specific and human — avoid generic phrases like "busy professional"
- tags: 1-3 short labels for filtering (e.g. "enterprise", "mobile-first", "compliance")
"""


def draft_library_persona(
    prompt: str,
    *,
    product_name: str | None = None,
    target_url: str | None = None,
) -> dict[str, Any]:
    """Generate a full behavioral persona for the library from a natural-language prompt.

    Falls back to a heuristic template if LLM is unavailable.
    Returns a complete persona dict ready to pass to persona_store.save_persona().
    """
    prompt = (prompt or "").strip()
    if len(prompt) < 6:
        raise ValueError("Describe the user in at least a few words")

    result: dict[str, Any] | None = None

    if llm_enabled():
        from rehearse.llm import (
            _api_key, _base_url, _http_timeout, _max_retries, _model,
            _post_chat_with_fallback,
        )
        import httpx, time

        key = _api_key()
        if key:
            context_parts = [f"User description: {prompt}"]
            if product_name:
                context_parts.append(f"Product: {product_name}")
            if target_url:
                context_parts.append(f"URL: {target_url}")
            context_str = "\n".join(context_parts)

            payload: dict[str, Any] = {
                "model": _model(),
                "messages": [
                    {"role": "system", "content": _LIBRARY_PERSONA_SYSTEM},
                    {"role": "user", "content": context_str},
                ],
                "temperature": 0.5,
                "max_tokens": 600,
                "response_format": {"type": "json_object"},
            }
            timeout = _http_timeout()
            for attempt in range(_max_retries() + 1):
                try:
                    with httpx.Client(timeout=timeout) as client:
                        resp = _post_chat_with_fallback(client, payload)
                        if resp.status_code >= 400 and "response_format" in payload:
                            payload = {k: v for k, v in payload.items() if k != "response_format"}
                            resp = _post_chat_with_fallback(client, payload)
                        resp.raise_for_status()
                        raw_content = resp.json()["choices"][0]["message"]["content"]
                        break
                except (httpx.ReadTimeout, httpx.ConnectTimeout):
                    if attempt < _max_retries():
                        time.sleep(2 ** attempt)
                        continue
                    raw_content = None
                    break
                except Exception:
                    raw_content = None
                    break
            else:
                raw_content = None

            if raw_content:
                try:
                    parsed = json.loads(raw_content)
                except json.JSONDecodeError:
                    m = re.search(r"\{[\s\S]*\}", raw_content)
                    parsed = json.loads(m.group()) if m else None

                if isinstance(parsed, dict):
                    result = parsed

    if result is None:
        # Heuristic fallback — populate behavioral fields with sensible defaults
        tmpl = _template_persona(prompt, product_name=product_name)
        result = {
            "name": tmpl["name"],
            "role": tmpl["role"],
            "goals": tmpl["goals"],
            "tech_literacy": "intermediate",
            "patience": "medium",
            "trust_level": "neutral",
            "character": "",
            "usage_context": prompt[:200],
            "tags": [],
        }

    # Normalise and stamp source
    result["source"] = "ai-generated"
    # Ensure id is derived from name for library storage
    raw_name = str(result.get("name") or prompt)
    result.setdefault("id", f"lib-{re.sub(r'[^a-z0-9]+', '-', raw_name.lower()).strip('-')[:40]}")
    result.setdefault("enabled", True)
    for field, default in [
        ("tech_literacy", "intermediate"), ("patience", "medium"),
        ("trust_level", "neutral"), ("character", ""), ("usage_context", ""), ("tags", []),
    ]:
        result.setdefault(field, default)

    return result
