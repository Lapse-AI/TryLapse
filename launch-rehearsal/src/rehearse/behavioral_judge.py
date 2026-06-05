"""Behavioral Judge — LLM evaluates each step not just technically but from
the persona's perspective: "Did this serve my goal?"

This is the key difference between technical pass/fail and behavioral quality.
A chatbot that responds 200 OK but gives a wrong answer is a behavioral fail.
A button that works but takes 4 clicks to reach is a friction signal.
"""

from __future__ import annotations

import json
import os
from typing import Any

_JUDGE_SYSTEM = """You are evaluating a software product from the perspective of a specific user persona.
You have access to what happened on each page (text, errors, timing) and the persona's goals.
Judge not just whether it worked technically, but whether it served the user's actual need.
Be specific and honest. Identify friction even when the technical path succeeded."""

_STEP_JUDGE_PROMPT = """Persona: {persona_name} ({persona_role})
Persona goals: {goals}
Current journey: {journey_name}
Behavioral intent: {behavioral_intent}

Step performed: {action} on {url}
Expected outcome: {expected_outcome}

What happened:
- Technical outcome: {technical_outcome}
- Page content: {page_excerpt}
- Duration: {duration_ms}ms
- Console errors: {console_errors}
- Network failures: {network_failures}
- Heading count: {heading_count}, Links: {link_count}
- Unlabeled buttons: {unlabeled_buttons}

Evaluate this step from the persona's perspective. Return JSON:
{{
  "behavioral_verdict": "pass|partial|fail",
  "goal_served": true/false,
  "friction_signals": ["specific friction observed"],
  "chatbot_quality": null,
  "ux_concerns": ["UX issue observed"],
  "information_gap": null,
  "note": "brief explanation of verdict"
}}

For chatbot steps, add "chatbot_quality": {{"response_relevant": true/false, "quality": "good|poor|hallucination", "detail": "why"}}
For navigation steps, assess information architecture (is important content accessible? buried?)
For form steps, assess if labels, validation, and feedback are clear.
Return null for fields that don't apply."""

_JOURNEY_JUDGE_PROMPT = """Persona: {persona_name} ({persona_role})
Journey: {journey_name}
Behavioral intent: {behavioral_intent}
Failure signals anticipated: {failure_signals}

Step verdicts:
{step_verdicts}

Overall page content seen:
{combined_excerpts}

Synthesize the behavioral analysis for this journey. Return JSON:
{{
  "behavioral_journey_verdict": "pass|partial|fail",
  "goal_completion": "fully|partially|failed",
  "friction_score": 0-10,
  "key_friction_points": ["specific moments of friction"],
  "ux_improvements": [
    {{
      "type": "information-architecture|navigation|label|feedback|performance|content",
      "finding": "specific finding",
      "recommendation": "specific improvement"
    }}
  ],
  "information_access_issues": ["things the persona needed but couldn't find easily"],
  "journey_length_assessment": "appropriate|too-long|could-be-shorter",
  "priority_for_persona": "critical|high|medium|low",
  "behavioral_summary": "2-3 sentence summary from persona perspective"
}}"""


def _api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("REHEARSE_LLM_API_KEY")


def _call_llm(prompt: str) -> dict[str, Any] | None:
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
                    {"role": "system", "content": _JUDGE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        return None


def judge_step(
    step: dict[str, Any],
    *,
    persona: dict[str, Any],
    journey: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one step from the persona's behavioral perspective."""
    prompt = _STEP_JUDGE_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        goals="; ".join(persona.get("goals") or []),
        journey_name=journey.get("name", ""),
        behavioral_intent=journey.get("behavioral_intent", ""),
        expected_outcome=step.get("expected_outcome", ""),
        action=step.get("action", ""),
        url=step.get("finalUrl") or step.get("requestedUrl") or "",
        technical_outcome=step.get("outcome", "unknown"),
        page_excerpt=(step.get("bodyTextExcerpt") or "")[:500],
        duration_ms=step.get("durationMs", 0),
        console_errors=len(step.get("consoleErrors") or []),
        network_failures=len(step.get("networkFailures") or []),
        heading_count=step.get("headingCount", 0),
        link_count=step.get("linkCount", 0),
        unlabeled_buttons=step.get("unlabeledButtonCount", 0),
    )
    result = _call_llm(prompt)
    if not result:
        # Template fallback based on technical outcome
        outcome = step.get("outcome", "pass")
        return {
            "behavioral_verdict": outcome if outcome in ("pass", "partial", "fail") else "pass",
            "goal_served": outcome == "pass",
            "friction_signals": (
                [f"Step took {step.get('durationMs', 0)}ms"] if (step.get("durationMs") or 0) > 5000 else []
            ),
            "chatbot_quality": None,
            "ux_concerns": (
                [f"{step.get('unlabeledButtonCount', 0)} unlabeled buttons"]
                if (step.get("unlabeledButtonCount") or 0) > 0 else []
            ),
            "information_gap": None,
            "note": "Template verdict — enable LLM for behavioral analysis",
            "source": "template",
        }
    result["source"] = "llm"
    return result


def judge_journey(
    journey_steps: list[dict[str, Any]],
    step_verdicts: list[dict[str, Any]],
    *,
    persona: dict[str, Any],
    journey: dict[str, Any],
) -> dict[str, Any]:
    """Synthesize behavioral analysis across all steps of a journey."""
    verdicts_text = "\n".join(
        f"  Step {i+1} ({s.get('action', '?')}): {v.get('behavioral_verdict', '?')} — {v.get('note', '')}"
        for i, (s, v) in enumerate(zip(journey_steps, step_verdicts))
    )
    combined = " | ".join(
        (s.get("bodyTextExcerpt") or "")[:100]
        for s in journey_steps
        if s.get("bodyTextExcerpt")
    )[:600]

    prompt = _JOURNEY_JUDGE_PROMPT.format(
        persona_name=persona.get("name", "User"),
        persona_role=persona.get("role", "user"),
        journey_name=journey.get("name", ""),
        behavioral_intent=journey.get("behavioral_intent", ""),
        failure_signals="; ".join(journey.get("failure_signals") or []),
        step_verdicts=verdicts_text,
        combined_excerpts=combined,
    )
    result = _call_llm(prompt)
    if not result:
        pass_count = sum(1 for v in step_verdicts if v.get("behavioral_verdict") == "pass")
        total = len(step_verdicts) or 1
        return {
            "behavioral_journey_verdict": "pass" if pass_count / total >= 0.8 else "partial",
            "goal_completion": "fully" if pass_count == total else "partially",
            "friction_score": max(0, 10 - int((pass_count / total) * 10)),
            "key_friction_points": [],
            "ux_improvements": [],
            "information_access_issues": [],
            "journey_length_assessment": "appropriate",
            "priority_for_persona": journey.get("priority", "medium"),
            "behavioral_summary": "Template verdict — enable LLM for behavioral analysis",
            "source": "template",
        }
    result["source"] = "llm"
    return result
