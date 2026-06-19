"""Optional LLM-enhanced persona analysis — evidence-bound, product-agnostic."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any

import httpx

from rehearse.context import RunContext
from rehearse.dsl import Persona
from rehearse.heuristics import Delight, Finding

# ── B4: per-run LLM call budget tracking ─────────────────────────────────────
_llm_lock = threading.Lock()
_llm_call_count: int = 0


def reset_llm_call_count() -> None:
    global _llm_call_count
    with _llm_lock:
        _llm_call_count = 0


def get_llm_call_count() -> int:
    return _llm_call_count


def _record_llm_call() -> None:
    global _llm_call_count
    with _llm_lock:
        _llm_call_count += 1

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
    explicit = os.environ.get("REHEARSE_LLM_API_KEY")
    if explicit:
        return explicit
    # Prefer NIM key; fall back to DeepSeek then OpenAI
    return (
        _nim_api_key()
        or _deepseek_api_key()
        or os.environ.get("OPENAI_API_KEY")
    )


def _nim_base_url() -> str:
    return (
        os.environ.get("NVIDIA_NIM_API_BASE")
        or os.environ.get("NVIDIA_API_BASE")
        or _NIM_DEFAULT_BASE
    ).rstrip("/")


def _deepseek_base_url() -> str:
    return os.environ.get("DEEPSEEK_API_BASE", _DEEPSEEK_DEFAULT_BASE).rstrip("/")


def _nim_api_key() -> str | None:
    return os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY")


def _deepseek_api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY")


def _base_url() -> str:
    explicit = os.environ.get("REHEARSE_LLM_BASE_URL")
    if explicit:
        return explicit.rstrip("/")
    # DeepSeek direct first — NIM free tier has 60-252s latency, worse than direct API.
    # Set REHEARSE_LLM_PRIMARY=nim to flip this when on a paid NIM plan.
    nim_first = os.environ.get("REHEARSE_LLM_PRIMARY", "deepseek").lower() == "nim"
    if nim_first and _nim_configured():
        return _nim_base_url()
    if _deepseek_configured():
        return _deepseek_base_url()
    if _nim_configured():
        return _nim_base_url()
    return _OPENAI_DEFAULT_BASE


_NIM_DEEPSEEK_MODEL = "deepseek-ai/deepseek-v4-flash"  # NIM catalog ID


def _model(base_url: str | None = None) -> str:
    base = (base_url or _base_url()).lower()
    explicit = os.environ.get("REHEARSE_LLM_MODEL")
    if "deepseek.com" in base:
        raw = explicit or os.environ.get("DEEPSEEK_MODEL") or os.environ.get("DEEPSEEK_API_MODEL") or _DEEPSEEK_DEFAULT_MODEL
        return _normalize_deepseek_model(raw)
    if "nvidia" in base or "integrate.api.nvidia" in base:
        return (
            explicit
            or os.environ.get("NVIDIA_NIM_MODEL")
            or os.environ.get("NVIDIA_MODEL")
            or _NIM_DEEPSEEK_MODEL
        )
    return explicit or os.environ.get("DEEPSEEK_MODEL") or os.environ.get("NVIDIA_MODEL") or "gpt-4o-mini"


def _http_timeout() -> httpx.Timeout:
    """Separate connect vs read — NIM free tier queues up to ~280s on 3rd concurrent slot."""
    read_s = float(os.environ.get("REHEARSE_LLM_TIMEOUT_S", "320"))
    connect_s = float(os.environ.get("REHEARSE_LLM_CONNECT_TIMEOUT_S", "30"))
    return httpx.Timeout(connect=connect_s, read=read_s, write=30.0, pool=30.0)


def _max_retries() -> int:
    return int(os.environ.get("REHEARSE_LLM_RETRIES", "2"))


_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Email addresses
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[email]"),
    # JWT — must come before generic token to prevent partial match (eyJ... prefix)
    (re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "[jwt]"),
    # Bearer / API tokens in headers or query params (≥20 char alphanum/dash/underscore/dot)
    (re.compile(r"(?i)(?:bearer|token|api[_\-]?key|apikey|secret|access[_\-]?token)[=:\s\"']+([A-Za-z0-9\-_.~+/]{20,})"), r"[token]"),
    # Generic long opaque strings: 32+ base64/hex chars on a word boundary
    (re.compile(r"\b([A-Za-z0-9+/]{32,}={0,2})\b"), "[token]"),
    # Numeric phone-like patterns (loose)
    (re.compile(r"\b(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"), "[phone]"),
]


def _scrub_pii(text: str) -> str:
    """Remove emails, tokens, JWTs and phone numbers from a text excerpt."""
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _build_evidence_bundle(ctx: RunContext, persona: Persona) -> dict[str, Any]:
    steps = []
    for s in ctx.evidence.steps[:40]:
        steps.append(
            {
                "step_id": s.step_id,
                "journey_id": s.journey_id,
                "action": s.action,
                "outcome": s.outcome,
                "url": _scrub_pii(s.final_url or s.requested_url or ""),
                "title": s.page_title,
                "duration_ms": s.duration_ms,
                "excerpt": _scrub_pii(s.body_text_excerpt[:400]),
                "unlabeled_buttons": s.unlabeled_button_count,
                "errors": [_scrub_pii(e) for e in s.error_phrases_found],
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
        "allow_localhost": ctx.config.allow_localhost,
        "dogfood_note": (
            "Localhost dogfood run: missing login/SSO is expected; do not flag as P1."
            if ctx.config.allow_localhost
            else None
        ),
        "persona": {
            "id": persona.id,
            "name": persona.name,
            "role": persona.role,
            "goals": persona.goals,
            "tech_literacy": getattr(persona, "tech_literacy", "intermediate"),
            "patience": getattr(persona, "patience", "medium"),
            "trust_level": getattr(persona, "trust_level", "neutral"),
            "character": getattr(persona, "character", "") or None,
            "usage_context": getattr(persona, "usage_context", "") or None,
        },
        "steps": steps,
        "sitemap": sitemap_summary,
        "workflows": workflows,
    }


SYSTEM_PROMPT = """You are an enterprise UX evaluation agent for Launch Rehearsal.
You observe B2B SaaS staging products and produce evidence-bound readiness feedback.
You NEVER suggest modifying code, deploying fixes, or prescribe solutions.

═══ SEVERITY CALIBRATION (B2B SaaS context) ═══
P1 — BLOCKER: Prevents a trial prospect from completing a core workflow OR prevents an existing customer from operating their account. Examples: broken primary CTA, login wall with no recovery path, data that fails to save, error page with no back-navigation. In B2B, a P1 kills a deal or triggers a churn call.
P2 — MEANINGFUL: Creates significant friction for the target persona but does not block. Examples: confusing label on a key action, missing empty-state guidance, ambiguous confirmation UX, slow page that stalls a demo. In B2B, P2s accumulate into "this product feels rough."
P3 — POLISH: Would not block evaluation or operation but affects impressions. Examples: inconsistent capitalisation, minor spacing, a tooltip that could be clearer. Flag sparingly — 3+ P3s may indicate P2 beneath the surface.

═══ JOURNEY GRADE CRITERIA ═══
"pass"    → All critical steps in the journey completed; friction was minor or P3.
"partial" → The journey completed but required workarounds, produced errors that recovered, or had P2 friction that affected task confidence.
"fail"    → The core task was impossible or the journey was abandoned due to a P1 issue.
Grade every journey_id present in the evidence bundle.

═══ CONFIDENCE CALIBRATION ═══
"high"       → Directly observed in step data: explicit error text, failed step outcome, visible unlabeled element count.
"hypothesis" → Inferred from indirect signals: excerpt suggests confusion but outcome was "pass", no error text observed but flow took 3× longer than expected.

═══ BEHAVIORAL PROFILE MODIFIERS ═══
Apply these to severity, not just description:
- tech_literacy=novice + confusing label → P2 (not P3). They will not figure it out.
- tech_literacy=expert + minor friction → P3 (acceptable). They will adapt.
- patience=low + multi-step discovery path for a frequent task → P2.
- trust_level=skeptical + no confirmation dialog or ambiguous pricing → P2.
- usage_context includes "switching from X" → gaps vs. X are P2, not P3.

═══ CITATION RULE ═══
Every issue and delight MUST cite a step_id from the evidence bundle.
If no step_id applies, do NOT include the finding. Prefer quality over quantity.

═══ SPECIAL CONDITIONS ═══
- If dogfood_note is set: job queue "failed" rows are historical CLI jobs, not page errors.
- If dogfood_note is set: do not flag missing authentication or SSO as issues.
- Do not invent URLs, selectors, or step_ids not present in the evidence bundle.

═══ FEW-SHOT EXAMPLE ═══
Evidence snapshot (abbreviated):
  steps: [
    {"step_id": "j-signup-p1-s3", "action": "click", "outcome": "fail",
     "excerpt": "Error: email already registered", "unlabeled_buttons": 0},
    {"step_id": "j-signup-p1-s5", "action": "navigate", "outcome": "pass",
     "excerpt": "Welcome to Acme! Here's how to get started...", "unlabeled_buttons": 0}
  ]
  persona: {role: "first-time evaluator", tech_literacy: "novice", patience: "low"}

Good response:
{
  "summary": "Signup flow blocks new users with a non-recoverable email-conflict error.",
  "journey_grades": {"j-signup": "partial"},
  "issues": [
    {
      "severity": "P1",
      "title": "Email-already-registered error has no recovery action",
      "detail": "Step j-signup-p1-s3 shows 'email already registered' with no link to login or password reset. A novice user with low patience will abandon rather than guess.",
      "step_id": "j-signup-p1-s3",
      "confidence": "high"
    }
  ],
  "delights": [
    {
      "title": "Onboarding welcome message sets clear next step",
      "detail": "Step j-signup-p1-s5 shows a focused 'here's how to get started' prompt — removes guesswork for first-time users.",
      "step_id": "j-signup-p1-s5"
    }
  ]
}

═══ OUTPUT FORMAT ═══
Respond with JSON only — no markdown, no preamble:
{
  "summary": "one sentence covering the persona's overall experience",
  "journey_grades": {"journey_id": "pass|partial|fail"},
  "issues": [{"severity":"P1|P2|P3","title":"...","detail":"...","step_id":"...","confidence":"high|hypothesis"}],
  "delights": [{"title":"...","detail":"...","step_id":"..."}]
}
"""


def _post_chat(client: httpx.Client, payload: dict[str, Any], *, base: str | None = None, key: str | None = None) -> httpx.Response:
    _key = key or _api_key()
    assert _key
    _base = base or _base_url()
    return client.post(
        f"{_base}/chat/completions",
        headers={"Authorization": f"Bearer {_key}", "Content-Type": "application/json"},
        json=payload,
    )


_MAX_RETRY_WAIT_S = 65  # max seconds we'll wait on a 429 before falling back


def _retry_after_seconds(resp: httpx.Response) -> float | None:
    """Parse Retry-After (seconds int or HTTP-date) from a 429 response."""
    raw = resp.headers.get("Retry-After") or resp.headers.get("x-ratelimit-reset-requests")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        reset = parsedate_to_datetime(raw)
        delta = (reset - __import__("datetime").datetime.now(__import__("datetime").timezone.utc)).total_seconds()
        return max(delta, 0)
    except Exception:
        return None


def _post_chat_with_fallback(client: httpx.Client, payload: dict[str, Any]) -> httpx.Response:
    """Try NIM first with Retry-After-aware backoff; fall back to DeepSeek on persistent 429/5xx."""
    _NIM_429_RETRIES = 4

    if _nim_configured():
        nim_key = _nim_api_key()
        nim_url = _nim_base_url()
        nim_payload = {**payload, "model": _model(nim_url)}
        for attempt in range(_NIM_429_RETRIES):
            try:
                resp = _post_chat(client, nim_payload, base=nim_url, key=nim_key)
                if resp.status_code == 429:
                    wait = _retry_after_seconds(resp) or min(10 * (2 ** attempt), _MAX_RETRY_WAIT_S)
                    if wait <= _MAX_RETRY_WAIT_S and attempt < _NIM_429_RETRIES - 1:
                        print(f"[llm] nim 429 — waiting {wait:.0f}s (attempt {attempt+1}/{_NIM_429_RETRIES})", flush=True)
                        time.sleep(wait)
                        continue
                    print(f"[llm] nim 429 Retry-After={wait:.0f}s — falling back to DeepSeek", flush=True)
                    break
                if resp.status_code in (500, 502, 503):
                    print(f"[llm] nim {resp.status_code} — falling back to DeepSeek", flush=True)
                    break
                return resp
            except Exception:
                break
        # NIM failed — fall through to DeepSeek

    if _deepseek_configured():
        ds_key = _deepseek_api_key()
        ds_url = _deepseek_base_url() + "/v1"
        ds_payload = {**payload, "model": _model(ds_url)}
        return _post_chat(client, ds_payload, base=ds_url, key=ds_key)
    # Neither NIM nor DeepSeek — use whatever _base_url() returns
    return _post_chat(client, payload)


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

    _record_llm_call()  # B4: track LLM calls per run
    timeout = _http_timeout()
    last_exc: Exception | None = None
    content: str | None = None
    usage: dict[str, Any] | None = None

    for attempt in range(_max_retries() + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = _post_chat_with_fallback(client, payload)
                if resp.status_code == 429:
                    wait = min(2 ** attempt * 5, 60)
                    time.sleep(wait)
                    resp = _post_chat_with_fallback(client, payload)
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
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                return {"error": "invalid_json", "summary": "LLM returned non-JSON"}
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


NARRATIVE_SYSTEM_PROMPT = """You are a launch-readiness storyteller for Launch Rehearsal.
Turn structured rehearsal evidence into plain language for founders and engineers.
You NEVER recommend code changes or deployments — only interpret monitoring results.

Rules:
- Be concise, specific, and cite journey names or issue titles from the evidence.
- Do not invent issues or URLs not in the input.
- If dogfood_note is set, ignore job-queue "failed" rows and missing SSO as blockers.

Respond with JSON only:
{
  "executiveSummary": "2-3 sentences for any stakeholder",
  "forFounders": "short markdown bullets for GTM/founder readout",
  "forEngineering": "short markdown bullets for eng triage",
  "suggestedQuestions": ["3-5 questions to ask in a launch review meeting"],
  "chatReadySummary": "one dense paragraph a chatbot can use as system context"
}
"""

CHAT_SYSTEM_PROMPT = """You answer questions about a single Launch Rehearsal run.
Use ONLY the run context provided. If unsure, say what evidence is missing.
Never suggest modifying code. Cite issue titles or journey names when relevant.
Keep answers under 200 words unless the user asks for detail.
"""


def _llm_json_call(system: str, user: str, *, max_tokens: int = 2048) -> dict[str, Any] | None:
    key = _api_key()
    if not key:
        return None
    payload: dict[str, Any] = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    if os.environ.get("REHEARSE_LLM_JSON_MODE", "1") not in ("0", "false", "no"):
        payload["response_format"] = {"type": "json_object"}
    _record_llm_call()  # B4: track LLM calls per run
    try:
        with httpx.Client(timeout=_http_timeout()) as client:
            resp = _post_chat(client, payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", content or "")
            if match:
                try:
                    parsed = json.loads(match.group())
                except json.JSONDecodeError:
                    return {"error": "invalid_json"}
            else:
                return {"error": "invalid_json"}
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        return {"error": str(exc)[:300]}
    return None


def _narrative_context(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    *,
    ctx: RunContext | None,
    template: dict[str, Any],
) -> dict[str, Any]:
    from rehearse.heuristics import _canonical_steps

    steps = _canonical_steps(evidence.steps)
    return {
        "product": config.product_name,
        "target_url": config.target_url,
        "run_id": evidence.run_id,
        "readiness": analysis.readiness,
        "template_narrative": template,
        "top_blocker": analysis.top_blocker,
        "top_delight": analysis.top_delight,
        "issues": [
            {
                "severity": i.severity,
                "title": i.title,
                "detail": i.detail[:300],
                "step_id": i.step_id,
            }
            for i in analysis.issues[:20]
        ],
        "delights": [
            {"title": d.title, "detail": d.detail[:200], "step_id": d.step_id}
            for d in analysis.delights[:10]
        ],
        "journey_matrix": analysis.journey_matrix,
        "step_outcomes": {
            "pass": sum(1 for s in steps if s.outcome == "pass"),
            "partial": sum(1 for s in steps if s.outcome == "partial"),
            "fail": sum(1 for s in steps if s.outcome == "fail"),
            "total": len(steps),
        },
        "dogfood_note": (
            "Localhost dogfood — job queue failures are not page errors."
            if config.allow_localhost
            else None
        ),
        "sitemap_pages": len(ctx.sitemap.pages) if ctx and ctx.sitemap else 0,
    }


def generate_run_narrative_llm(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    *,
    ctx: RunContext | None = None,
    template: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    from rehearse.narrative import build_template_narrative

    base = template or build_template_narrative(config, evidence, analysis, ctx=ctx)
    ctx_blob = _narrative_context(config, evidence, analysis, ctx=ctx, template=base)
    user_msg = f"Write narratives for this rehearsal:\n{json.dumps(ctx_blob, indent=2)}"
    return _llm_json_call(NARRATIVE_SYSTEM_PROMPT, user_msg, max_tokens=2048)


COMPARE_NARRATIVE_PROMPT = """You compare two Launch Rehearsal runs for stakeholders.
Use only the diff and optional run narratives provided. No code-change advice.

Respond with JSON only:
{
  "headline": "one sentence comparing older vs newer run",
  "forFounders": "2-4 short bullets for GTM",
  "forEngineering": "2-4 short bullets for triage",
  "verdict": "improved|regressed|neutral|mixed",
  "suggestedQuestions": ["2-4 review questions"]
}
"""


def generate_compare_narrative_llm(
    diff: dict[str, Any],
    *,
    bundle_a: dict[str, Any] | None = None,
    bundle_b: dict[str, Any] | None = None,
    template: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    blob = {
        "diff": diff,
        "run_a_narrative": (bundle_a or {}).get("narrative"),
        "run_b_narrative": (bundle_b or {}).get("narrative"),
        "template": template,
    }
    return _llm_json_call(
        COMPARE_NARRATIVE_PROMPT,
        f"Compare these two rehearsal runs:\n{json.dumps(blob, indent=2)[:12000]}",
        max_tokens=1024,
    )


TRENDS_NARRATIVE_PROMPT = """You interpret Launch Rehearsal trend time series for stakeholders.
Use only the trends JSON (readiness bands, flake rates, recurrence, issue open/resolve counts).

Respond with JSON only:
{
  "headline": "one sentence on overall trajectory",
  "forFounders": "2-4 bullets",
  "forEngineering": "2-4 bullets",
  "verdict": "improved|regressed|neutral|mixed",
  "suggestedQuestions": ["2-4 questions"]
}
"""


def generate_trends_narrative_llm(
    trends: dict[str, Any],
    *,
    template: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    blob = {"trends": trends, "template": template}
    return _llm_json_call(
        TRENDS_NARRATIVE_PROMPT,
        f"Summarize rehearsal trends:\n{json.dumps(blob, indent=2)[:10000]}",
        max_tokens=1024,
    )


DIGEST_NARRATIVE_PROMPT = """You write a command-center digest across the last N rehearsal runs.
Use summaries and optional latest narratives only.

Respond with JSON only:
{
  "headline": "one sentence",
  "bullets": ["3-5 short bullets for the home page"],
  "readinessTrend": "improving|stable|softening|unknown"
}
"""


def generate_command_digest_llm(
    summaries: list[dict[str, Any]],
    *,
    bundles: list[dict[str, Any]] | None = None,
    template: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    blob = {
        "summaries": summaries[:7],
        "narratives": [(b or {}).get("narrative") for b in (bundles or [])[:3]],
        "template": template,
    }
    return _llm_json_call(
        DIGEST_NARRATIVE_PROMPT,
        f"Command center digest:\n{json.dumps(blob, indent=2)[:10000]}",
        max_tokens=768,
    )


EXPERIMENT_CHAT_SYSTEM_PROMPT = """You are an experiment analyst for Launch Rehearsal.
You have access to the results of two rehearsal runs (A = control, B = variant) and the diff between them.
Answer questions about what changed, whether the hypothesis held, and what persona-level friction shifted.
Be direct and evidence-based. Do not claim lift or fidelity — say 'directional' when uncertain.
Use ONLY the experiment context provided."""


def chat_about_experiment(
    job: dict[str, Any],
    bundle_a: dict[str, Any] | None,
    bundle_b: dict[str, Any] | None,
    diff: dict[str, Any] | None,
    message: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Answer a question scoped to a variant experiment (both run bundles + diff)."""
    from rehearse.narrative import template_chat_reply

    def _bundle_compact(bundle: dict[str, Any] | None, label: str) -> dict[str, Any]:
        if not bundle:
            return {"label": label, "available": False}
        s = bundle.get("summary") or {}
        return {
            "label": label,
            "readiness": s.get("readiness"),
            "readinessBand": s.get("readinessBand"),
            "blockers": s.get("blockers"),
            "issues": s.get("issues"),
            "delights": s.get("delights"),
            "topIssues": [
                {"severity": i.get("severity"), "title": i.get("title"), "persona": i.get("persona")}
                for i in (bundle.get("issues") or [])[:8]
            ],
            "topDelights": [{"title": d.get("title")} for d in (bundle.get("delights") or [])[:5]],
        }

    compact = {
        "hypothesis": job.get("hypothesis") or "not specified",
        "userGoal": job.get("userGoal") or "",
        "configA": job.get("configA", "").split("/")[-1].replace(".yaml", ""),
        "configB": job.get("configB", "").split("/")[-1].replace(".yaml", ""),
        "runA": _bundle_compact(bundle_a, "control"),
        "runB": _bundle_compact(bundle_b, "variant"),
        "diff": {
            "newIssues": (diff or {}).get("newIssues", [])[:6],
            "resolvedIssues": (diff or {}).get("resolvedIssues", [])[:6],
            "narrativeSummary": ((diff or {}).get("narrative") or {}).get("executiveSummary", ""),
        } if diff else {},
    }

    key = _api_key()
    if not key:
        readiness_a = (bundle_a or {}).get("summary", {}).get("readiness")
        readiness_b = (bundle_b or {}).get("summary", {}).get("readiness")
        if readiness_a is not None and readiness_b is not None:
            delta = readiness_b - readiness_a
            verdict = "improved" if delta > 0 else ("regressed" if delta < 0 else "unchanged")
            reply = (
                f"Directional result: readiness {verdict} from {readiness_a} to {readiness_b} "
                f"({delta:+d} pts). New issues: {len((diff or {}).get('newIssues', []))}. "
                f"Resolved: {len((diff or {}).get('resolvedIssues', []))}."
            )
        else:
            reply = "One or both runs are still pending. Check the status panel above."
        return {"reply": reply, "source": "template"}

    messages: list[dict[str, str]] = [
        {"role": "system", "content": EXPERIMENT_CHAT_SYSTEM_PROMPT + "\n\nExperiment context:\n" + json.dumps(compact)},
    ]
    for turn in (history or [])[-6:]:
        role = turn.get("role", "user")
        content = str(turn.get("content", ""))[:2000]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message[:4000]})

    payload: dict[str, Any] = {
        "model": _model(),
        "messages": messages,
        "temperature": 0.35,
        "max_tokens": int(os.environ.get("REHEARSE_CHAT_MAX_TOKENS", "800")),
    }
    try:
        with httpx.Client(timeout=_http_timeout()) as client:
            resp = _post_chat(client, payload)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"].strip()
        return {"reply": reply, "source": "llm"}
    except Exception as exc:
        return {"reply": f"LLM unavailable: {exc}", "source": "template", "llmError": str(exc)[:200]}


def chat_about_run(
    bundle: dict[str, Any],
    message: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Answer a natural-language question about a run bundle."""
    from rehearse.narrative import narrative_from_bundle, template_chat_reply

    narrative = narrative_from_bundle(bundle) or {}
    summary = bundle.get("summary") or {}
    compact = {
        "run_id": summary.get("id"),
        "product": summary.get("productName"),
        "readiness_band": summary.get("readinessBand"),
        "readiness_score": summary.get("readiness"),
        "blockers": summary.get("blockers"),
        "issues_count": summary.get("issues"),
        "narrative": {
            "executiveSummary": narrative.get("executiveSummary"),
            "forFounders": narrative.get("forFounders"),
            "chatReadySummary": narrative.get("chatReadySummary"),
        },
        "issues": [
            {"severity": i.get("severity"), "title": i.get("title"), "detail": (i.get("detail") or "")[:200]}
            for i in (bundle.get("issues") or [])[:15]
        ],
        "delights": [
            {"title": d.get("title"), "detail": (d.get("detail") or "")[:150]}
            for d in (bundle.get("delights") or [])[:8]
        ],
    }

    key = _api_key()
    if not key:
        return {
            "reply": template_chat_reply(bundle, message),
            "source": "template",
        }

    messages: list[dict[str, str]] = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT + "\n\nRun context:\n" + json.dumps(compact)},
    ]
    for turn in (history or [])[-6:]:
        role = turn.get("role", "user")
        content = str(turn.get("content", ""))[:2000]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message[:4000]})

    payload: dict[str, Any] = {
        "model": _model(),
        "messages": messages,
        "temperature": 0.35,
        "max_tokens": int(os.environ.get("REHEARSE_CHAT_MAX_TOKENS", "800")),
    }
    try:
        with httpx.Client(timeout=_http_timeout()) as client:
            resp = _post_chat(client, payload)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"].strip()
        return {"reply": reply, "source": "llm"}
    except Exception as exc:
        return {
            "reply": template_chat_reply(bundle, message),
            "source": "template",
            "llmError": str(exc)[:200],
        }
