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
Tech literacy: {tech_literacy}. Patience: {patience}. Trust disposition: {trust_level}.
{character_line}
You deeply understand your own usage patterns — when you open the product,
what you actually care about, what frustrates you, what you return to daily.
Navigate as this specific person would:
- A novice hesitates, reads labels, uses search; an expert scans and acts directly.
- Low-patience users abandon multi-step flows and look for shortcuts.
- Skeptical users read fine print and verify before committing.
Be realistic, specific, and grounded in the product description provided."""

_PLAN_PROMPT = """You are: {persona_name}
Your role: {persona_role}
Your goals: {persona_goals}
{usage_context_line}

The product you use:
{product_summary}

{dom_reference}

List every distinct journey you undertake with this product — daily tasks,
weekly routines, onboarding steps, edge cases, admin actions, recovery flows,
anything you'd do more than once. Cover breadth: happy paths, frustrated paths,
exploratory paths, and anything persona-specific.

IMPORTANT: For entry_point, use only the exact URLs from the DOM Reference above.

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
      "entry_point": "<exact URL path from DOM Reference>",
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
Tech literacy: {tech_literacy}. Patience: {patience}. Trust disposition: {trust_level}.
{character_line}
Write every step precisely — not vague descriptions but exact browser actions:
which element to click, what to type, what URL to navigate to, what to assert.
Let the persona's disposition shape the path: a novice may use search instead of nav;
a low-patience user skips optional steps; a skeptic checks a confirmation dialog.
Think like a test engineer writing Playwright steps for this exact persona type.
CRITICAL: Use only the EXACT element labels and URLs from the DOM reference provided."""

_EXPAND_PROMPT = """Persona: {persona_name} ({persona_role})
Goals: {persona_goals}
{usage_context_line}

Product:
{product_summary}

{dom_reference}

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

IMPORTANT: For click steps, use the EXACT label text from the DOM Reference above
(e.g. intent: "Candidate Database" not "analytics section link").
For navigate steps, use the exact URLs listed in the DOM Reference.

Return JSON only:
{{
  "journey_id": "{journey_id}",
  "steps": [
    {{
      "action": "navigate|click|fill|wait|scroll|hover|select|press|assert_url_contains|open_link|explore|dismiss",
      "description": "<what you do and why>",
      "url": "<full URL or path, for navigate steps>",
      "intent": "<EXACT element label text from DOM Reference, for click/fill/scroll>",
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
Be precise: use 'click "Candidate Database"' not 'click the data section link'."""


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _api_key() -> str | None:
    # NIM first, then DeepSeek
    return (
        os.environ.get("REHEARSE_LLM_API_KEY")
        or os.environ.get("NVIDIA_NIM_API_KEY")
        or os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
    )


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


_NIM_BASE = "https://integrate.api.nvidia.com/v1"
_NIM_MODEL = "deepseek-ai/deepseek-v4-flash"
_DS_BASE = "https://api.deepseek.com/v1"
_DS_MODEL = "deepseek-v4-flash"


def _llm_endpoints() -> list[tuple[str, str, str]]:
    """Return (base_url, model, api_key) in priority order: DeepSeek direct first, NIM as fallback.

    NIM free tier has 60-252s latency for DeepSeek V4 Flash which is worse than direct.
    Flip REHEARSE_LLM_PRIMARY=nim to use NIM first when on a paid plan with fast cold-starts.
    """
    explicit_base = os.environ.get("REHEARSE_LLM_BASE_URL", "").rstrip("/")
    explicit_model = os.environ.get("REHEARSE_LLM_MODEL", "")
    explicit_key = os.environ.get("REHEARSE_LLM_API_KEY", "")

    if explicit_base and explicit_key:
        return [(explicit_base, explicit_model or _DS_MODEL, explicit_key)]

    nim_first = os.environ.get("REHEARSE_LLM_PRIMARY", "deepseek").lower() == "nim"
    endpoints = []

    ds_key = os.environ.get("DEEPSEEK_API_KEY")
    ds_entry = None
    if ds_key:
        ds_base = os.environ.get("DEEPSEEK_API_BASE", _DS_BASE).rstrip("/")
        ds_model = os.environ.get("DEEPSEEK_MODEL") or _DS_MODEL
        ds_entry = (ds_base, ds_model, ds_key)

    nim_key = os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    nim_entry = None
    if nim_key:
        nim_base = (os.environ.get("NVIDIA_NIM_API_BASE") or os.environ.get("NVIDIA_API_BASE") or _NIM_BASE).rstrip("/")
        nim_model = os.environ.get("NVIDIA_NIM_MODEL") or os.environ.get("NVIDIA_MODEL") or _NIM_MODEL
        nim_entry = (nim_base, nim_model, nim_key)

    if nim_first:
        if nim_entry: endpoints.append(nim_entry)
        if ds_entry: endpoints.append(ds_entry)
    else:
        if ds_entry: endpoints.append(ds_entry)
        if nim_entry: endpoints.append(nim_entry)

    return endpoints


def _call_llm(prompt: str, system: str, *, max_tokens: int = 3000) -> dict[str, Any] | None:
    import time as _time
    import httpx

    endpoints = _llm_endpoints()
    if not endpoints:
        return None

    payload_base = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    _MAX_RETRY_WAIT_S = 65  # max seconds we'll wait on a 429 before falling to next provider

    for (base, model, key) in endpoints:
        provider = "nim" if "nvidia" in base else "deepseek" if "deepseek" in base else "openai"
        payload = {**payload_base, "model": model}
        last_exc: Exception | None = None
        for attempt in range(5):
            try:
                t0 = _time.time()
                resp = httpx.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=320.0,  # NIM free tier can queue up to ~280s on 3rd concurrent slot
                )
                elapsed = _time.time() - t0

                if resp.status_code == 429:
                    retry_after = None
                    raw_ra = resp.headers.get("Retry-After") or resp.headers.get("x-ratelimit-reset-requests")
                    if raw_ra:
                        try:
                            retry_after = float(raw_ra)
                        except ValueError:
                            pass

                    if retry_after is None:
                        # Exponential fallback: 10s, 20s, 40s... up to cap
                        retry_after = min(10 * (2 ** attempt), _MAX_RETRY_WAIT_S)

                    if retry_after <= _MAX_RETRY_WAIT_S and attempt < 4:
                        print(f"[llm] {provider} 429 — waiting {retry_after:.0f}s (attempt {attempt+1}/5)", flush=True)
                        _time.sleep(retry_after)
                        last_exc = Exception(f"rate limited (429), waited {retry_after:.0f}s")
                        continue
                    else:
                        print(f"[llm] {provider} 429 Retry-After={retry_after:.0f}s — falling back to next provider", flush=True)
                        last_exc = Exception("rate limited (429) — retry-after too long")
                        break  # try next endpoint

                if resp.status_code >= 500:
                    print(f"[llm] {provider} {resp.status_code} server error — trying fallback", flush=True)
                    last_exc = Exception(f"server error {resp.status_code}")
                    break  # try next endpoint, not retry same

                print(f"[llm] {provider}/{model.split('/')[-1]} {elapsed:.1f}s status={resp.status_code}", flush=True)
                resp.raise_for_status()
                choice = resp.json()["choices"][0]
                raw = choice["message"]["content"]
                finish = choice.get("finish_reason", "")
                result = _repair_json(raw)
                if result and finish == "length":
                    result["_truncated"] = True
                return result
            except Exception as exc:
                last_exc = exc
        # This endpoint exhausted — try next (fallback)
        _ = last_exc
    return None


# ── Product model summariser ─────────────────────────────────────────────────

def _dom_reference(interaction_map: dict[str, Any] | None) -> str:
    """Build a DOM reference block the LLM can use for exact element labels."""
    if not interaction_map:
        return ""
    lines = ["=== DOM Reference (use EXACT text from here) ==="]

    nav = interaction_map.get("navStructure") or interaction_map.get("nav_structure") or []
    if nav:
        lines.append(f"Navigation labels: {' | '.join(nav)}")

    pages = interaction_map.get("pagesVisited") or interaction_map.get("pages_visited") or []
    base = interaction_map.get("targetUrl") or interaction_map.get("target_url") or ""
    paths = []
    for p in pages[:12]:
        path = p.replace(base, "") or "/"
        if path not in paths:
            paths.append(path)
    if paths:
        lines.append(f"Discovered pages (use these exact URLs): {' | '.join(paths)}")

    buttons = interaction_map.get("buttons") or []
    real_labels = [
        b.get("label", "") for b in buttons
        if b.get("label") and not b.get("label", "").startswith("[")
        and b.get("label") not in ("unnamed",)
    ]
    if real_labels:
        lines.append(f"Clickable elements found: {' | '.join(dict.fromkeys(real_labels))[:300]}")

    url_patterns = interaction_map.get("urlPatterns") or interaction_map.get("url_patterns") or {}
    if url_patterns:
        lines.append(f"URL patterns: {', '.join(url_patterns.keys())}")

    lines.append("=== End DOM Reference ===")
    return "\n".join(lines)


def _product_summary_from_imap(imap: dict[str, Any]) -> str:
    """Minimal product summary derived purely from the interaction map when product model is empty."""
    base = imap.get("targetUrl") or imap.get("target_url") or ""
    pages = imap.get("pagesVisited") or imap.get("pages_visited") or []
    nav = imap.get("navStructure") or imap.get("nav_structure") or []
    paths = list(dict.fromkeys(
        (p.replace(base, "") or "/") for p in pages[:12]
    ))
    lines = [
        f"URL: {base}",
        f"Navigation: {', '.join(nav)}" if nav else "",
        f"Discovered pages: {', '.join(paths)}" if paths else "",
    ]
    return "\n".join(l for l in lines if l)


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
    interaction_map: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Ask LLM for journey metadata (no steps) — fast, small, never truncates."""
    pid = persona.get("id", "p-unknown")
    pid_short = pid.replace("p-", "").replace("p", "")[:8]
    system = _PLAN_SYSTEM.format(
        persona_role=persona.get("role", "user"),
        tech_literacy=persona.get("tech_literacy") or "intermediate",
        patience=persona.get("patience") or "medium",
        trust_level=persona.get("trust_level") or "neutral",
        character_line=persona.get("character") or "",
    )
    usage_ctx = persona.get("usage_context") or ""
    prompt = _PLAN_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        persona_goals="; ".join(persona.get("goals") or ["use the product effectively"]),
        usage_context_line=f"Context: {usage_ctx}" if usage_ctx else "",
        persona_id=pid,
        pid_short=pid_short,
        product_summary=_product_summary(product_model),
        dom_reference=_dom_reference(interaction_map),
    )
    return _call_llm(prompt, system, max_tokens=2500)


# ── Phase 2: step expansion ───────────────────────────────────────────────────

def _expand_journey_steps(
    journey_meta: dict[str, Any],
    persona: dict[str, Any],
    product_model: dict[str, Any],
    interaction_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Expand a single journey into full deep steps. One focused LLM call."""
    usage_ctx = persona.get("usage_context") or ""
    system = _EXPAND_SYSTEM.format(
        persona_role=persona.get("role", "user"),
        tech_literacy=persona.get("tech_literacy") or "intermediate",
        patience=persona.get("patience") or "medium",
        trust_level=persona.get("trust_level") or "neutral",
        character_line=persona.get("character") or "",
    )
    prompt = _EXPAND_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        persona_goals="; ".join(persona.get("goals") or ["use the product effectively"]),
        usage_context_line=f"Context: {usage_ctx}" if usage_ctx else "",
        product_summary=_product_summary(product_model),
        dom_reference=_dom_reference(interaction_map),
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
    interaction_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Two-phase deep journey discovery for one persona.

    Phase 1: LLM emits journey plan (8–14 journeys, metadata only, ~2K tokens).
    Phase 2: For each journey, LLM expands full steps + sub-flows (~3K tokens each).
    This guarantees unlimited depth without ever hitting the token limit.
    """
    pid = persona.get("id", "p-unknown")

    # If product model is empty but we have interaction_map, bootstrap from crawl data
    if not product_model and interaction_map:
        product_model = {
            "purpose": _product_summary_from_imap(interaction_map),
            "targetUrl": interaction_map.get("targetUrl") or interaction_map.get("target_url", ""),
        }

    # ── Phase 1: get the journey plan ────────────────────────────────────────
    plan = _discover_journey_plan(persona, product_model, interaction_map)
    if not plan or not plan.get("journey_plan"):
        return _template_fallback(persona, product_model)

    journey_plan: list[dict[str, Any]] = plan.get("journey_plan") or []

    # ── Phase 2: expand each journey's steps in parallel ─────────────────────
    import threading
    expanded: dict[str, dict[str, Any]] = {}

    def _expand(jm: dict[str, Any]) -> None:
        jid = jm.get("id", "")
        expanded[jid] = _expand_journey_steps(jm, persona, product_model, interaction_map)

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


def discover_journeys_for_persona_streaming(
    persona: dict[str, Any],
    product_model: dict[str, Any],
    interaction_map: dict[str, Any] | None = None,
    on_event: Any = None,
) -> dict[str, Any]:
    """Same two-phase discovery as discover_journeys_for_persona, but fires
    on_event(dict) callbacks as each journey is expanded so callers can stream
    results to the client incrementally.

    Events emitted:
      {"type": "phase1_start"}
      {"type": "phase1_done", "count": N, "names": [...], "usage_pattern": {...}}
      {"type": "journey_ready", "journey": {...}}  — once per expanded journey
      {"type": "done", "persona_id": "...", "journeys_count": N}
    """
    import threading as _threading

    pid = persona.get("id", "p-unknown")

    def emit(event: dict[str, Any]) -> None:
        if on_event:
            try:
                on_event(event)
            except Exception:
                pass

    if not product_model and interaction_map:
        product_model = {
            "purpose": _product_summary_from_imap(interaction_map),
            "targetUrl": interaction_map.get("targetUrl") or interaction_map.get("target_url", ""),
        }

    emit({"type": "phase1_start", "message": "Generating journey plan from product + crawl data…"})
    plan = _discover_journey_plan(persona, product_model, interaction_map)

    if not plan or not plan.get("journey_plan"):
        result = _template_fallback(persona, product_model)
        fallback_journeys: list[dict[str, Any]] = result.get("journeys") or []
        emit({
            "type": "phase1_done",
            "count": len(fallback_journeys),
            "names": [j.get("name", "") for j in fallback_journeys],
            "usage_pattern": result.get("usage_pattern", {}),
            "source": "template",
        })
        for fj in fallback_journeys:
            emit({"type": "journey_ready", "journey": fj})
        emit({"type": "done", "persona_id": pid, "source": "template", "journeys_count": len(fallback_journeys)})
        return result

    journey_plan: list[dict[str, Any]] = plan.get("journey_plan") or []
    emit({
        "type": "phase1_done",
        "count": len(journey_plan),
        "names": [j.get("name", "") for j in journey_plan],
        "usage_pattern": plan.get("usage_pattern", {}),
    })

    expanded: dict[str, dict[str, Any]] = {}
    lock = _threading.Lock()

    def _expand(jm: dict[str, Any]) -> None:
        exp = _expand_journey_steps(jm, persona, product_model, interaction_map)
        merged = {**jm, "steps": exp.get("steps") or [], "sub_flows": exp.get("sub_flows") or []}
        with lock:
            expanded[jm.get("id", "")] = merged
        emit({"type": "journey_ready", "journey": merged})

    threads = [
        _threading.Thread(target=_expand, args=(jm,), daemon=True)
        for jm in journey_plan
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=90)

    journeys = [
        expanded.get(jm.get("id", ""), {**jm, "steps": [], "sub_flows": []})
        for jm in journey_plan
    ]
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
    emit({"type": "done", "persona_id": pid, "journeys_count": len(journeys)})
    return result


def discover_journeys_for_all_personas(
    personas: list[dict[str, Any]],
    product_model: dict[str, Any],
    interaction_map: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run journey discovery for every persona (personas run in parallel,
    but within each persona Phase 2 expansions also run in parallel)."""
    import threading
    results: list[dict[str, Any]] = [{} for _ in range(len(personas))]

    def _worker(idx: int, persona: dict[str, Any]) -> None:
        results[idx] = discover_journeys_for_persona(persona, product_model, interaction_map)

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

    entry: dict[str, Any] = {
        "id": journey.get("id", "j-unknown"),
        "name": journey.get("name", "Untitled journey"),
        "steps": clean_steps,
    }
    # Preserve which persona this journey was discovered for
    pid = journey.get("persona_id") or journey.get("personaId")
    if pid:
        entry["persona_ids"] = [str(pid)]
    return entry
