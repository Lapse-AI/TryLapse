"""Optional LLM-enhanced persona analysis — evidence-bound, product-agnostic."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import httpx

from rehearse.context import RunContext
from rehearse.dsl import Persona
from rehearse.heuristics import Delight, Finding

_NIM_DEFAULT_BASE = "https://integrate.api.nvidia.com/v1"
_DEEPSEEK_DEFAULT_BASE = "https://api.deepseek.com"
_DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash"
_OPENAI_DEFAULT_BASE = "https://api.openai.com/v1"


def _normalize_deepseek_model(name: str) -> str:
    """Map display names / NVIDIA catalog ids to api.deepseek.com model ids."""
    raw = name.strip()
    lower = raw.lower().replace("_", "-")
    if lower.startswith("deepseek-ai/"):
        lower = lower.split("/", 1)[1]
    if "v4-flash" in lower or lower == "deepseek-v4-flash":
        return "deepseek-v4-flash"
    if "v4-pro" in lower:
        return "deepseek-v4-pro"
    if lower in ("deepseek-chat", "deepseek-reasoner"):
        return lower
    # e.g. DeepSeek-V4-Flash → deepseek-v4-flash
    if "deepseek" in lower and "flash" in lower:
        return "deepseek-v4-flash"
    if "deepseek" in lower and "pro" in lower:
        return "deepseek-v4-pro"
    return raw


def _deepseek_configured() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY"))


def _nim_configured() -> bool:
    return bool(os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY"))


def llm_enabled() -> bool:
    return bool(
        os.environ.get("REHEARSE_LLM_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or _nim_configured()
    )


def llm_provider() -> str:
    if os.environ.get("REHEARSE_LLM_API_KEY") or os.environ.get("REHEARSE_LLM_BASE_URL"):
        base = (os.environ.get("REHEARSE_LLM_BASE_URL") or "").lower()
        if "deepseek" in base:
            return "deepseek"
        if "nvidia" in base or "integrate.api.nvidia" in base:
            return "nvidia-nim"
        return "openai-compatible"
    if _deepseek_configured():
        return "deepseek"
    if _nim_configured():
        return "nvidia-nim"
    return "openai"


def _api_key() -> str | None:
    return (
        os.environ.get("REHEARSE_LLM_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("NVIDIA_NIM_API_KEY")
        or os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )


def _base_url() -> str:
    explicit = os.environ.get("REHEARSE_LLM_BASE_URL")
    if explicit:
        return explicit.rstrip("/")

    if _deepseek_configured() and not _nim_configured():
        return os.environ.get("DEEPSEEK_API_BASE", _DEEPSEEK_DEFAULT_BASE).rstrip("/")

    if _deepseek_configured():
        # Both keys present — prefer DeepSeek direct API (faster, no NIM trial limits)
        return os.environ.get("DEEPSEEK_API_BASE", _DEEPSEEK_DEFAULT_BASE).rstrip("/")

    if _nim_configured():
        return (
            os.environ.get("NVIDIA_NIM_API_BASE")
            or os.environ.get("NVIDIA_API_BASE")
            or _NIM_DEFAULT_BASE
        ).rstrip("/")

    return _OPENAI_DEFAULT_BASE


def _model() -> str:
    base = _base_url().lower()
    if "deepseek.com" in base:
        raw = (
            os.environ.get("REHEARSE_LLM_MODEL")
            or os.environ.get("DEEPSEEK_MODEL")
            or os.environ.get("DEEPSEEK_API_MODEL")
            or os.environ.get("NVIDIA_MODEL")
            or _DEEPSEEK_DEFAULT_MODEL
        )
        return _normalize_deepseek_model(raw)
    return (
        os.environ.get("REHEARSE_LLM_MODEL")
        or os.environ.get("DEEPSEEK_MODEL")
        or os.environ.get("NVIDIA_MODEL")
        or os.environ.get("NVIDIA_NIM_MODEL")
        or "gpt-4o-mini"
    )


def _http_timeout() -> httpx.Timeout:
    """Separate connect vs read — NIM free tier often needs long read; DeepSeek is faster."""
    read_s = float(os.environ.get("REHEARSE_LLM_TIMEOUT_S", "180"))
    connect_s = float(os.environ.get("REHEARSE_LLM_CONNECT_TIMEOUT_S", "30"))
    return httpx.Timeout(connect=connect_s, read=read_s, write=30.0, pool=30.0)


def _max_retries() -> int:
    return int(os.environ.get("REHEARSE_LLM_RETRIES", "2"))


def _build_evidence_bundle(ctx: RunContext, persona: Persona) -> dict[str, Any]:
    steps = []
    for s in ctx.evidence.steps[:40]:
        steps.append(
            {
                "step_id": s.step_id,
                "journey_id": s.journey_id,
                "action": s.action,
                "outcome": s.outcome,
                "url": s.final_url or s.requested_url,
                "title": s.page_title,
                "duration_ms": s.duration_ms,
                "excerpt": s.body_text_excerpt[:400],
                "unlabeled_buttons": s.unlabeled_button_count,
                "errors": s.error_phrases_found,
            }
        )
    sitemap_summary = None
    if ctx.sitemap:
        sitemap_summary = {
            "page_count": len(ctx.sitemap.pages),
            "hub_paths": ctx.sitemap.hub_paths[:8],
            "orphan_paths": ctx.sitemap.orphan_paths[:8],
            "auth_gated": ctx.sitemap.auth_gated_paths[:8],
            "error_paths": ctx.sitemap.error_paths[:8],
        }
    workflows = []
    if ctx.workflows:
        workflows = [
            {"type": w.workflow_type, "path": w.path, "title": w.title}
            for w in ctx.workflows.workflows[:15]
        ]
    return {
        "product": ctx.config.product_name,
        "target_url": ctx.config.target_url,
        "persona": {
            "id": persona.id,
            "name": persona.name,
            "role": persona.role,
            "goals": persona.goals,
        },
        "steps": steps,
        "sitemap": sitemap_summary,
        "workflows": workflows,
    }


SYSTEM_PROMPT = """You are an enterprise UX evaluation agent for Launch Rehearsal.
You observe web products and produce monitoring feedback — you NEVER suggest modifying code or deploying fixes.

Rules:
- Every issue and delight MUST cite a step_id from the evidence bundle.
- Use severity P1 (blocker), P2 (meaningful), P3 (polish).
- Include confidence: "high" or "hypothesis".
- Required: at least 0 issues and 0 delights if none found; prefer quality over quantity.
- Evaluate from the given persona's goals and role.
- Do not invent URLs or step_ids not in the bundle.

Respond with JSON only:
{
  "summary": "one sentence",
  "journey_grades": {"journey_id": "pass|partial|fail"},
  "issues": [{"severity":"P2","title":"...","detail":"...","step_id":"...","confidence":"high"}],
  "delights": [{"title":"...","detail":"...","step_id":"..."}]
}
"""


def _post_chat(client: httpx.Client, payload: dict[str, Any]) -> httpx.Response:
    key = _api_key()
    assert key
    return client.post(
        f"{_base_url()}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
    )


def analyze_persona_llm(ctx: RunContext, persona: Persona) -> dict[str, Any] | None:
    key = _api_key()
    if not key:
        return None

    bundle = _build_evidence_bundle(ctx, persona)
    user_msg = f"Evaluate this rehearsal evidence from persona lens:\n{json.dumps(bundle, indent=2)}"

    payload: dict[str, Any] = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
        "max_tokens": int(os.environ.get("REHEARSE_LLM_MAX_TOKENS", "2048")),
    }
    use_json_mode = os.environ.get("REHEARSE_LLM_JSON_MODE", "1") not in ("0", "false", "no")
    if use_json_mode:
        payload["response_format"] = {"type": "json_object"}

    timeout = _http_timeout()
    last_exc: Exception | None = None
    content: str | None = None
    usage: dict[str, Any] | None = None

    for attempt in range(_max_retries() + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = _post_chat(client, payload)
                if resp.status_code == 429:
                    wait = min(2 ** attempt * 5, 60)
                    time.sleep(wait)
                    resp = _post_chat(client, payload)
                if resp.status_code >= 400 and use_json_mode and "response_format" in payload:
                    payload_retry = {k: v for k, v in payload.items() if k != "response_format"}
                    resp = _post_chat(client, payload_retry)
                resp.raise_for_status()
                body = resp.json()
                content = body["choices"][0]["message"]["content"]
                usage = body.get("usage")
                break
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout) as exc:
            last_exc = exc
            if attempt < _max_retries():
                time.sleep(2 ** attempt)
                continue
            return {
                "error": "timeout",
                "summary": (
                    f"LLM read timed out after {timeout.read}s "
                    f"(provider={llm_provider()}, model={_model()}). "
                    "Set REHEARSE_LLM_TIMEOUT_S=300 or check API status."
                ),
            }
        except Exception as exc:
            last_exc = exc
            break

    if content is None:
        return {"error": str(last_exc), "summary": f"LLM analysis failed: {last_exc}"}

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            parsed = json.loads(match.group())
        else:
            return {"error": "invalid_json", "summary": "LLM returned non-JSON"}
    if usage:
        parsed["_usage"] = usage
    return parsed


def llm_to_findings(data: dict[str, Any], persona_id: str) -> tuple[list[Finding], list[Delight], dict[str, str]]:
    findings: list[Finding] = []
    delights: list[Delight] = []
    grades: dict[str, str] = {}

    for item in data.get("issues") or []:
        if not item.get("step_id") or not item.get("title"):
            continue
        findings.append(
            Finding(
                id="LLM",
                severity=str(item.get("severity", "P2")),
                title=str(item["title"]),
                detail=str(item.get("detail", "")),
                persona_ids=[persona_id],
                step_id=str(item["step_id"]),
                confidence=str(item.get("confidence", "high")),
            )
        )
    for item in data.get("delights") or []:
        if not item.get("step_id") or not item.get("title"):
            continue
        delights.append(
            Delight(
                id="LLM",
                title=str(item["title"]),
                detail=str(item.get("detail", "")),
                persona_ids=[persona_id],
                step_id=str(item["step_id"]),
            )
        )
    for jid, status in (data.get("journey_grades") or {}).items():
        if status in ("pass", "partial", "fail"):
            grades[jid] = status
    return findings, delights, grades
