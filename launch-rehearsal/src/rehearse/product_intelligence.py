"""Product Intelligence — LLM-based deep understanding of a target product.

Takes crawl data (sitemap, page excerpts, interaction map) and builds a
structured ProductModel that drives persona generation and journey discovery.
The model is stored in artifacts/product_model.json and is user-editable.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_ANALYSIS_SYSTEM = """You are a product analyst who deeply understands software products.
Given crawl data from a web application, produce a structured JSON analysis.
Be specific, detailed, and grounded in what you actually observed — not generic.
Focus on what makes this product unique and what real users would struggle with or love."""

_ANALYSIS_PROMPT = """Analyze this web product from the crawl data below.

Target URL: {url}
Product name: {product_name}

Pages found ({page_count} total):
{pages_summary}

Interactions detected:
{interactions_summary}

API endpoints hit during crawl:
{api_summary}

Return a JSON object with this exact structure:
{{
  "purpose": "One sentence: what this product does and for whom",
  "product_type": "one of: saas-dashboard, marketplace, developer-tool, communication, analytics, ecommerce, content-platform, other",
  "core_features": ["feature 1", "feature 2", ...],  // 5-10 most important features
  "primary_workflows": [
    {{
      "name": "workflow name",
      "description": "what user accomplishes",
      "entry_point": "/path or page name",
      "steps_estimate": 3,
      "frequency": "daily|weekly|occasional|onboarding-only"
    }}
  ],
  "information_architecture": {{
    "depth_concern": true/false,  // key info buried too deep?
    "dashboard_gaps": ["thing that should be on dashboard but isn't"],
    "navigation_issues": ["observed nav problem"]
  }},
  "technical_surface": {{
    "has_chatbot": true/false,
    "has_search": true/false,
    "has_filters": true/false,
    "has_realtime": true/false,
    "has_forms": true/false,
    "api_heavy": true/false,
    "auth_required": true/false
  }},
  "user_types_observed": [
    {{
      "type": "type name",
      "evidence": "what on the site suggests this user type",
      "primary_goal": "what they want to accomplish"
    }}
  ],
  "quality_concerns": [
    {{
      "area": "UX|Performance|Reliability|Information",
      "concern": "specific concern observed",
      "severity": "critical|moderate|minor"
    }}
  ]
}}"""


def _call_llm(prompt: str, system: str = _ANALYSIS_SYSTEM) -> dict[str, Any] | None:
    from rehearse.persona_journey_discovery import _llm_endpoints, _repair_json
    import httpx
    for (base, model, key) in _llm_endpoints():
        try:
            resp = httpx.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000,
                    "response_format": {"type": "json_object"},
                },
                timeout=60.0,
            )
            if resp.status_code in (429, 500, 502, 503):
                continue
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            result = _repair_json(raw)
            if result:
                return result
        except Exception:
            continue
    return None


def _pages_summary(sitemap_pages: list[dict[str, Any]], max_pages: int = 40) -> str:
    lines = []
    for p in sitemap_pages[:max_pages]:
        path = p.get("path", "")
        title = p.get("title", "")[:60]
        ptype = p.get("type", "")
        links = p.get("linkCount", 0)
        forms = p.get("formCount", 0)
        words = p.get("wordCount", 0)
        lines.append(f"  {path} [{ptype}] — {title} | links:{links} forms:{forms} words:{words}")
    if len(sitemap_pages) > max_pages:
        lines.append(f"  ... and {len(sitemap_pages) - max_pages} more pages")
    return "\n".join(lines) or "  (no pages crawled)"


def _interactions_summary(interaction_map: dict[str, Any]) -> str:
    parts = []
    buttons = interaction_map.get("buttons", [])
    forms = interaction_map.get("forms", [])
    modals = interaction_map.get("modals", [])
    if buttons:
        parts.append(f"  Buttons/CTAs: {len(buttons)} found")
        for b in buttons[:5]:
            parts.append(f"    - {b.get('label', '?')} on {b.get('page', '?')}")
    if forms:
        parts.append(f"  Forms: {len(forms)} found")
        for f in forms[:3]:
            parts.append(f"    - {f.get('fields', '?')} fields on {f.get('page', '?')}")
    if modals:
        parts.append(f"  Modals/dialogs: {len(modals)} detected")
    return "\n".join(parts) or "  (no interaction data)"


def _api_summary(api_calls: list[dict[str, Any]]) -> str:
    if not api_calls:
        return "  (no API calls captured)"
    endpoints: dict[str, list[str]] = {}
    for call in api_calls[:50]:
        method = call.get("method", "GET")
        url = call.get("url", "")
        status = call.get("status", "?")
        path = url.split("?")[0][-60:]
        endpoints.setdefault(path, []).append(f"{method} → {status}")
    lines = []
    for path, calls in list(endpoints.items())[:15]:
        lines.append(f"  {path}: {', '.join(calls[:3])}")
    return "\n".join(lines)


def _visual_summary_section(interaction_map: dict[str, Any]) -> str:
    """Build a rich visual summary from page snapshots for LLM context."""
    snapshots = interaction_map.get("pageSnapshots") or []
    if not snapshots:
        return ""
    lines = ["\nVisual analysis of each page (from screenshots):"]
    for snap in snapshots[:10]:
        url = snap.get("url", "")
        page_type = snap.get("pageType", "")
        desc = snap.get("description", "")
        features = snap.get("featuresDetected") or []
        buttons = snap.get("buttonsVisible") or []
        data = snap.get("dataShown", "")
        lines.append(f"\n  Page: {url} [{page_type}]")
        if desc:
            lines.append(f"  Description: {desc}")
        if features:
            lines.append(f"  Features visible: {', '.join(features[:8])}")
        if buttons:
            lines.append(f"  Buttons/CTAs: {', '.join(buttons[:8])}")
        if data:
            lines.append(f"  Data shown: {data[:200]}")
        if snap.get("isLoading"):
            lines.append("  ⚠ Page was still loading during crawl")
        if snap.get("isError"):
            lines.append("  ⚠ Error state detected on this page")
    features_seen = interaction_map.get("featuresSeen") or []
    if features_seen:
        lines.append(f"\nAll features detected across pages: {', '.join(features_seen[:20])}")
    nav = interaction_map.get("navStructure") or []
    if nav:
        lines.append(f"Navigation items: {', '.join(nav[:15])}")
    if interaction_map.get("authWallDetected"):
        lines.append("\n⚠ Auth wall detected — product requires login to access full features")
    return "\n".join(lines)


def analyze_product(
    target_url: str,
    *,
    product_name: str = "",
    sitemap_pages: list[dict[str, Any]] | None = None,
    interaction_map: dict[str, Any] | None = None,
    api_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a ProductModel from crawl + vision data. Falls back to template if no LLM key."""
    pages = sitemap_pages or []
    interactions = interaction_map or {}
    apis = api_calls or interactions.get("apiCalls") or []

    # Build enhanced prompt with visual data
    visual_section = _visual_summary_section(interactions)
    interactions_text = _interactions_summary(interactions)
    if visual_section:
        interactions_text = interactions_text + "\n" + visual_section

    prompt = _ANALYSIS_PROMPT.format(
        url=target_url,
        product_name=product_name or target_url,
        page_count=max(len(pages), interactions.get("pageCount", 0)),
        pages_summary=_pages_summary(pages),
        interactions_summary=interactions_text,
        api_summary=_api_summary(apis),
    )

    result = _call_llm(prompt)

    if not result:
        # Template fallback when no LLM key
        has_auth = any(p.get("type") in ("auth", "signup") for p in pages)
        result = {
            "purpose": f"Web application at {target_url}",
            "product_type": "saas-dashboard",
            "core_features": [p.get("path", "/") for p in pages[:5]],
            "primary_workflows": [
                {
                    "name": p.get("title") or p.get("path", "/"),
                    "description": f"Workflow on {p.get('path', '/')}",
                    "entry_point": p.get("path", "/"),
                    "steps_estimate": 2,
                    "frequency": "weekly",
                }
                for p in pages[:5]
            ],
            "information_architecture": {
                "depth_concern": len(pages) > 10,
                "dashboard_gaps": [],
                "navigation_issues": [],
            },
            "technical_surface": {
                "has_chatbot": False,
                "has_search": any("search" in p.get("path", "") for p in pages),
                "has_filters": False,
                "has_realtime": False,
                "has_forms": bool(interactions.get("forms")),
                "api_heavy": len(apis) > 10,
                "auth_required": has_auth,
            },
            "user_types_observed": [],
            "quality_concerns": [],
            "source": "template",
        }
    else:
        result["source"] = "llm"

    result["targetUrl"] = target_url
    result["productName"] = product_name or ""
    result["pageCount"] = len(pages)
    return result


def _model_path(artifacts_root: Path, config_id: str | None = None) -> Path:
    """Per-config product model path so workspaces don't share state."""
    if config_id:
        return artifacts_root / "product_models" / f"{config_id}.json"
    return artifacts_root / "product_model.json"


def save_interaction_map(
    artifacts_root: Path, imap: dict[str, Any], config_id: str | None = None
) -> None:
    path = (
        artifacts_root / "interaction_maps" / f"{config_id}_imap.json"
        if config_id
        else artifacts_root / "interaction_maps" / "default_imap.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(imap, indent=2))


def load_interaction_map(
    artifacts_root: Path, config_id: str | None = None
) -> dict[str, Any] | None:
    candidates = []
    if config_id:
        candidates.append(artifacts_root / "interaction_maps" / f"{config_id}_imap.json")
    candidates.append(artifacts_root / "interaction_maps" / "default_imap.json")
    for p in candidates:
        if p.is_file():
            try:
                return json.loads(p.read_text())
            except json.JSONDecodeError:
                pass
    return None


def save_product_model(
    artifacts_root: Path, model: dict[str, Any], config_id: str | None = None
) -> Path:
    path = _model_path(artifacts_root, config_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=2))
    return path


def load_product_model(
    artifacts_root: Path, config_id: str | None = None
) -> dict[str, Any] | None:
    # Try per-config path first, fall back to legacy global path
    if config_id:
        path = _model_path(artifacts_root, config_id)
        if path.is_file():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                pass
    path = _model_path(artifacts_root, None)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
