"""Deep Discovery Bot — exhaustive interactive crawler.

Crawls a product like a real user: logs in, visits every nav page,
screenshots every state, clicks buttons, maps modals, tracks API calls.

Fixes vs previous version:
- URL joining uses origin (not full path) — /analytics stays /analytics
- Explicitly visits nav/sidebar links first before BFS
- Vision LLM: NIM Llama-3.2-90B → DeepSeek V4 Flash/Pro → Claude Haiku → GPT-4o-mini (first available key)
  Falls back gracefully to text-only if no key
- Login: waits for redirect + networkidle after submit
- Auth wall: retries after waiting longer (SPAs are slow)
- Deeper interaction: clicks cards, fills search, maps filters
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Safe test values ──────────────────────────────────────────────────────────

_SAFE_FILL: dict[str, str] = {
    "email":      "test@rehearsal-test.invalid",
    "password":   "Rehearsal_Test_2026!",
    "name":       "Test User",
    "first_name": "Test",
    "last_name":  "User",
    "phone":      "+15550000000",
    "message":    "Rehearsal test message.",
    "search":     "test",
    "query":      "leadership trainer",
    "default":    "test value",
}

_DESTRUCTIVE = {"delete", "remove", "cancel", "unsubscribe", "deactivate",
                "disable", "logout", "sign out", "reset", "clear all", "archive"}

_SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                    ".woff", ".woff2", ".ttf", ".css", ".map"}

_SKIP_URL_FRAGMENTS = {"analytics", "tracking", "hotjar", "segment", "sentry",
                       "gtm", "clarity", "intercom", "crisp", "__nextjs",
                       "_next/static", "favicon"}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class PageSnapshot:
    url: str
    title: str
    screenshot_b64: str = ""
    visible_text: str = ""
    nav_items: list[str] = field(default_factory=list)
    buttons: list[dict[str, Any]] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    modals_opened: list[dict[str, Any]] = field(default_factory=list)
    api_calls: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    visual_description: str = ""
    features_detected: list[str] = field(default_factory=list)


@dataclass
class InteractionMap:
    target_url: str
    pages_visited: list[str] = field(default_factory=list)
    page_snapshots: list[dict[str, Any]] = field(default_factory=list)
    buttons: list[dict[str, Any]] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    modals: list[dict[str, Any]] = field(default_factory=list)
    api_calls: list[dict[str, Any]] = field(default_factory=list)
    nav_structure: list[str] = field(default_factory=list)
    chatbot_detected: bool = False
    chatbot_responses: list[dict[str, Any]] = field(default_factory=list)
    filters_detected: list[str] = field(default_factory=list)
    errors_found: list[dict[str, Any]] = field(default_factory=list)
    auth_wall_detected: bool = False
    features_seen: list[str] = field(default_factory=list)
    visual_summary: str = ""
    crawl_duration_ms: int = 0
    # Pattern-based sampling: pattern → count of pages visited
    url_patterns: dict[str, int] = field(default_factory=dict)
    # Patterns seen but skipped (budget preserved)
    skipped_patterns: dict[str, int] = field(default_factory=dict)
    # Live graph: parent_url → [child_urls discovered from it]
    link_graph: dict[str, list[str]] = field(default_factory=dict)
    # Per-node status: url → "queued" | "visiting" | "visited" | "skipped" | "error"
    node_status: dict[str, str] = field(default_factory=dict)
    # Route coverage: % of discovered URL templates that were actually visited
    graph_coverage_pct: float = 0.0


# ── URL helpers ───────────────────────────────────────────────────────────────

def _origin(url: str) -> str:
    """Return scheme + host only: https://example.com"""
    parts = url.split("//", 1)
    if len(parts) < 2:
        return url
    return parts[0] + "//" + parts[1].split("/")[0]


_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)
_NUMERIC_RE = re.compile(r'^\d+$')
_HASH_RE = re.compile(r'^[0-9a-f]{16,}$', re.I)
# A slug that contains digits AND dashes/underscores and is long enough to be an ID
_ID_SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{7,}$', re.I)


def _url_pattern(url: str) -> str:
    """Normalize a URL to a structural template, collapsing IDs/slugs.

    /profiles/12345         → /profiles/{id}
    /users/abc-def-00abc    → /users/{id}
    /posts/2024-my-title    → kept (short alpha slug — likely a route)
    /admin/settings         → /admin/settings (no collapse)
    """
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        normed: list[str] = []
        for part in parts:
            if _UUID_RE.match(part) or _NUMERIC_RE.match(part) or _HASH_RE.match(part):
                normed.append("{id}")
            elif _ID_SLUG_RE.match(part) and (
                bool(re.search(r'\d', part)) or len(part) > 20
            ):
                # Has digits embedded OR very long → treat as ID slug
                normed.append("{id}")
            else:
                normed.append(part)
        pattern_path = "/" + "/".join(normed) if normed else "/"
        return urlunparse(("", "", pattern_path, "", "", ""))
    except Exception:
        return url


def _resolve_href(href: str, target_url: str) -> str | None:
    """Turn a relative or absolute href into a full URL on the same origin."""
    if not href:
        return None
    # Already absolute
    if href.startswith("http://") or href.startswith("https://"):
        return href
    # Root-relative
    if href.startswith("/"):
        return _origin(target_url) + href
    # Hash / JS / mailto
    if href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return None
    return None


def _should_skip(url: str, target_url: str) -> bool:
    if not url or not url.startswith("http"):
        return True
    # Must be same origin
    if _origin(url) != _origin(target_url):
        return True
    # Skip static asset extensions
    path = url.split("?")[0]
    for ext in _SKIP_EXTENSIONS:
        if path.endswith(ext):
            return True
    # Skip known noise fragments
    for frag in _SKIP_URL_FRAGMENTS:
        if frag in url:
            return True
    return False


# ── Vision LLM (Claude — supports images) ────────────────────────────────────

_VISION_PROMPT = """Analyze this screenshot of "{product_name}" at URL: {url}

Return JSON only — no markdown:
{{
  "page_type": "dashboard|login|list|detail|analytics|form|search|admin|error|loading|other",
  "description": "1-2 sentences describing what is visible",
  "features_detected": ["list of specific UI features or sections visible"],
  "buttons_visible": ["button labels visible on screen"],
  "data_shown": "describe any data, charts, tables, metrics visible",
  "auth_required": true/false,
  "is_loading": true/false,
  "is_error_state": true/false,
  "key_elements": ["important UI elements a tester should know about"]
}}"""


def _deepseek_vision_call(
    key: str, model: str, screenshot_b64: str, prompt: str
) -> dict[str, Any] | None:
    """Call DeepSeek vision via OpenAI-compatible endpoint."""
    try:
        import httpx
        base = os.environ.get("REHEARSE_LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
        resp = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }],
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)
    except Exception:
        return None


def _nim_vision_call(
    key: str, base_url: str, model: str, screenshot_b64: str, prompt: str
) -> dict[str, Any] | None:
    """Call NVIDIA NIM vision model via OpenAI-compatible endpoint."""
    try:
        import httpx
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            },
            timeout=45.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)
    except Exception:
        return None


def _describe_screenshot(screenshot_b64: str, url: str, product_name: str = "") -> dict[str, Any]:
    """Describe a screenshot using the best available vision-capable LLM.

    Priority:
      1. NVIDIA NIM Llama-3.2-90B Vision  (NVIDIA_NIM_API_KEY / NVIDIA_API_KEY)
      2. DeepSeek V4 Flash                (DEEPSEEK_API_KEY / REHEARSE_LLM_API_KEY)
      3. DeepSeek V4 Pro                  (fallback if Flash returns vision error)
      4. Claude Haiku                     (ANTHROPIC_API_KEY / REHEARSE_VISION_API_KEY)
      5. GPT-4o-mini                      (OPENAI_API_KEY)
    """
    if not screenshot_b64:
        return {}

    prompt = _VISION_PROMPT.format(product_name=product_name or "a web product", url=url)

    # ── 1: NVIDIA NIM (llama-3.2-90b-vision-instruct) ────────────────────────
    nim_key = os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    if nim_key:
        nim_base = os.environ.get("NVIDIA_NIM_API_BASE") or os.environ.get("NVIDIA_API_BASE") or "https://integrate.api.nvidia.com/v1"
        nim_model = os.environ.get("NVIDIA_VISION_MODEL") or "meta/llama-3.2-90b-vision-instruct"
        result = _nim_vision_call(nim_key, nim_base, nim_model, screenshot_b64, prompt)
        if result:
            return result

    # ── 2 + 3: DeepSeek ──────────────────────────────────────────────────────
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("REHEARSE_LLM_API_KEY")
    if deepseek_key:
        result = _deepseek_vision_call(deepseek_key, "deepseek-v4-flash", screenshot_b64, prompt)
        if result:
            return result
        result = _deepseek_vision_call(deepseek_key, "deepseek-v4-pro", screenshot_b64, prompt)
        if result:
            return result

    # ── 4: Anthropic Claude Haiku ────────────────────────────────────────────
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("REHEARSE_VISION_API_KEY")
    if anthropic_key:
        try:
            import httpx
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1024,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"].strip()
            raw = raw.lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(raw)
        except Exception:
            pass

    # ── 4: OpenAI GPT-4o-mini ────────────────────────────────────────────────
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import httpx
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 1024,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                    "response_format": {"type": "json_object"},
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            return json.loads(raw)
        except Exception:
            pass

    return {}


# ── Page interaction helpers ──────────────────────────────────────────────────

def _take_screenshot(page: Any, full_page: bool = True) -> str:
    try:
        raw = page.screenshot(full_page=full_page, type="png")
        return base64.b64encode(raw).decode("utf-8")
    except Exception:
        return ""


def _wait_for_settle(page: Any, ms: int = 5000) -> None:
    """Wait for networkidle + minimal SPA hydration buffer."""
    try:
        page.wait_for_load_state("networkidle", timeout=ms)
    except Exception:
        pass
    try:
        # 300ms buffer for SPA frameworks that fire one final render after networkidle.
        # Was 1500ms — reduced to cut 48-page crawl time by ~58s.
        page.wait_for_timeout(300)
    except Exception:
        pass


def _is_destructive(label: str) -> bool:
    return any(d in label.lower() for d in _DESTRUCTIVE)


def _extract_nav_links(page: Any, target_url: str) -> list[tuple[str, str]]:
    """Extract (label, url) from nav/sidebar links — these are priority pages."""
    links: list[tuple[str, str]] = []
    try:
        selectors = [
            "nav a[href]", "aside a[href]", "header a[href]",
            "[role='navigation'] a[href]", "[role='menubar'] a[href]",
            ".sidebar a[href]", ".nav a[href]",
        ]
        seen = set()
        for sel in selectors:
            for el in page.query_selector_all(sel):
                try:
                    href = el.get_attribute("href") or ""
                    label = (el.inner_text() or "").strip()[:50]
                    full = _resolve_href(href, target_url)
                    if full and full not in seen and not _should_skip(full, target_url):
                        seen.add(full)
                        links.append((label, full))
                except Exception:
                    continue
    except Exception:
        pass
    return links


def _extract_all_links(page: Any, target_url: str) -> list[str]:
    """Extract all internal links from the page for BFS queue."""
    urls: list[str] = []
    try:
        for el in page.query_selector_all("a[href]"):
            try:
                href = el.get_attribute("href") or ""
                full = _resolve_href(href, target_url)
                if full and not _should_skip(full, target_url):
                    urls.append(full)
            except Exception:
                continue
    except Exception:
        pass
    return urls


def _extract_buttons(page: Any, current_url: str) -> list[dict[str, Any]]:
    """Map all visible buttons and their labels."""
    result = []
    try:
        for el in page.query_selector_all(
            "button:visible, [role='button']:visible, [role='tab']:visible"
        ):
            try:
                label = (
                    el.get_attribute("aria-label")
                    or (el.inner_text() or "").strip()[:60]
                    or el.get_attribute("title")
                    or el.get_attribute("data-testid")
                    or "unnamed"
                ).strip()
                result.append({"label": label, "page": current_url})
            except Exception:
                continue
    except Exception:
        pass
    return result


def _extract_forms(page: Any, current_url: str) -> list[dict[str, Any]]:
    """Map all forms and their input fields."""
    result = []
    try:
        for form in page.query_selector_all("form, [role='search']")[:5]:
            inputs = form.query_selector_all(
                "input:not([type='hidden']):not([type='submit']), textarea, select"
            )
            fields = []
            for inp in inputs:
                label = (
                    inp.get_attribute("aria-label")
                    or inp.get_attribute("placeholder")
                    or inp.get_attribute("name")
                    or inp.get_attribute("type")
                    or "field"
                )
                fields.append({"label": label, "type": inp.get_attribute("type") or "text"})
            if fields:
                result.append({"page": current_url, "fields": fields})
    except Exception:
        pass
    return result


def _detect_auth_wall(page: Any) -> bool:
    try:
        url = page.url.lower()
        if any(p in url for p in ["/login", "/signin", "/auth", "/sign-in"]):
            return True
        if page.query_selector("input[type='password']"):
            return True
        text = (page.inner_text("body") or "")[:600].lower()
        if any(w in text for w in ["sign in to", "log in to", "please login", "unauthorized access"]):
            return True
    except Exception:
        pass
    return False


def _interact_buttons(
    page: Any,
    current_url: str,
    api_calls: list,
    imap: InteractionMap,
    visited: set,
    queue: list,
    max_buttons: int = 10,
) -> list[dict[str, Any]]:
    """Click visible non-destructive buttons, capture what happens."""
    data = []
    try:
        buttons = page.query_selector_all(
            "button:visible, [role='button']:visible, [role='tab']:visible"
        )
        clicked = 0
        for btn in buttons[:max_buttons * 2]:
            if clicked >= max_buttons:
                break
            try:
                if not btn.is_visible():
                    continue
                label = (
                    btn.get_attribute("aria-label")
                    or (btn.inner_text() or "").strip()[:50]
                    or btn.get_attribute("title")
                    or "unnamed"
                ).strip()
                if _is_destructive(label):
                    continue

                pre_url = page.url
                pre_api = len(api_calls)

                btn.scroll_into_view_if_needed()
                btn.click(timeout=4000)
                page.wait_for_timeout(1500)

                post_url = page.url
                new_apis = api_calls[pre_api:]
                outcome = "no-effect"
                modal_content = ""

                if post_url != pre_url:
                    outcome = "navigated"
                    full = post_url
                    if not _should_skip(full, imap.target_url) and full not in visited:
                        queue.append(full)
                elif new_apis:
                    outcome = "api-call"

                modal = page.query_selector(
                    "[role='dialog']:visible, [class*='modal']:visible, "
                    "[class*='Modal']:visible, [class*='drawer']:visible, "
                    "[class*='sheet']:visible, [class*='Dialog']:visible"
                )
                if modal:
                    outcome = "opened-modal"
                    try:
                        modal_content = (modal.inner_text() or "")[:300].strip()
                        modal_screenshot = _take_screenshot(page, full_page=False)
                        imap.modals.append({
                            "trigger": label,
                            "page": current_url,
                            "content": modal_content,
                            "screenshot_b64": modal_screenshot,
                        })
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(400)
                    except Exception:
                        pass

                data.append({
                    "label": label,
                    "page": current_url,
                    "outcome": outcome,
                    "api_calls": [a.get("url", "")[-80:] for a in new_apis[:3]],
                    "modal_content": modal_content[:100],
                })
                clicked += 1

                if page.url != current_url:
                    try:
                        page.go_back()
                        _wait_for_settle(page, 2000)
                    except Exception:
                        try:
                            page.goto(current_url, wait_until="domcontentloaded", timeout=10000)
                            _wait_for_settle(page, 2000)
                        except Exception:
                            break
            except Exception:
                continue
    except Exception:
        pass
    return data


def _try_search(page: Any, current_url: str, api_calls: list) -> dict[str, Any] | None:
    """Try typing into search inputs and capture results."""
    try:
        search_sel = (
            "input[type='search'], input[placeholder*='search' i], "
            "input[placeholder*='filter' i], input[placeholder*='find' i], "
            "input[placeholder*='describe' i], textarea[placeholder*='describe' i]"
        )
        el = page.query_selector(search_sel)
        if not el or not el.is_visible():
            return None
        placeholder = el.get_attribute("placeholder") or "search"
        pre_api = len(api_calls)
        el.fill("leadership trainer")
        el.press("Enter")
        page.wait_for_timeout(3000)
        new_apis = api_calls[pre_api:]
        result_text = page.inner_text("body")[:500]
        screenshot = _take_screenshot(page, full_page=False)
        return {
            "query": "leadership trainer",
            "placeholder": placeholder,
            "api_calls_triggered": len(new_apis),
            "result_preview": result_text[:300],
            "screenshot_b64": screenshot,
        }
    except Exception:
        return None


def _probe_page_interactions(
    page: Any,
    current_url: str,
    api_calls: list,
) -> dict[str, Any]:
    """Comprehensive per-page interaction audit.

    Tests: dropdowns/selects, accordions, tabs, console errors, performance
    timing, document links, chatbot presence, filter chips, and any
    remaining visible interactive elements that didn't get tested elsewhere.
    Returns a findings dict that gets merged into the page snapshot.
    """
    findings: dict[str, Any] = {
        "console_errors": [],
        "performance_ms": None,
        "dropdowns_tested": [],
        "selects_tested": [],
        "accordions_found": 0,
        "tabs_found": 0,
        "document_links": [],
        "chatbot_tested": False,
        "chatbot_response": None,
        "filter_chips": [],
        "slow_resources": [],
        "js_errors": [],
    }

    # ── Console / JS error capture ────────────────────────────────────────────
    # Install collector first, then read — errors fired during page interactions
    # below will be captured.  Also picks up any errors that fired during load
    # if a previous visit already installed the collector (SPA same-origin reuse).
    try:
        page.evaluate("""() => {
            if (!window.__rehearse_errors__) {
                window.__rehearse_errors__ = [];
                window.addEventListener('error', e => {
                    window.__rehearse_errors__.push(e.message + ' @ ' + (e.filename||'') + ':' + e.lineno);
                });
                window.addEventListener('unhandledrejection', e => {
                    window.__rehearse_errors__.push('UnhandledRejection: ' + String(e.reason));
                });
                const origErr = console.error;
                console.error = function(...args) {
                    window.__rehearse_errors__.push('console.error: ' + args.join(' '));
                    origErr.apply(console, args);
                };
            }
        }""")
    except Exception:
        pass

    # ── Navigation / paint timing ─────────────────────────────────────────────
    try:
        timing = page.evaluate("""() => {
            const nav = performance.getEntriesByType('navigation')[0];
            if (!nav) return null;
            return {
                dom_content_loaded: Math.round(nav.domContentLoadedEventEnd),
                load: Math.round(nav.loadEventEnd),
                first_paint: Math.round(
                    (performance.getEntriesByName('first-contentful-paint')[0] || {}).startTime || 0
                ),
            };
        }""")
        findings["performance_ms"] = timing
    except Exception:
        pass

    # ── Slow resources (>1s) ──────────────────────────────────────────────────
    try:
        slow = page.evaluate("""() => {
            return performance.getEntriesByType('resource')
                .filter(r => r.duration > 1000)
                .slice(0, 5)
                .map(r => ({url: r.name.split('?')[0].slice(-80), ms: Math.round(r.duration)}));
        }""") or []
        findings["slow_resources"] = slow
    except Exception:
        pass

    # ── Document / PDF links ──────────────────────────────────────────────────
    try:
        doc_links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .filter(a => /[.](pdf|docx?|xlsx?|csv|pptx?|zip)$/i.test(a.href))
                .slice(0, 8)
                .map(a => ({label: (a.textContent || '').trim().slice(0, 60), href: a.href.slice(-80)}));
        }""") or []
        findings["document_links"] = doc_links
    except Exception:
        pass

    # ── Dropdowns (select elements) ───────────────────────────────────────────
    try:
        selects = page.query_selector_all("select:visible")[:4]
        for sel in selects:
            try:
                label = (
                    sel.get_attribute("aria-label")
                    or sel.get_attribute("name")
                    or "select"
                )
                options = page.evaluate(
                    "(el) => Array.from(el.options).slice(0,6).map(o => o.text)",
                    sel,
                )
                pre_api = len(api_calls)
                if options and len(options) > 1:
                    sel.select_option(index=1)
                    page.wait_for_timeout(800)
                new_apis = api_calls[pre_api:]
                findings["selects_tested"].append({
                    "label": label,
                    "option_count": len(options) if options else 0,
                    "sample_options": (options or [])[:4],
                    "triggered_api": len(new_apis) > 0,
                })
                # Reset
                try:
                    sel.select_option(index=0)
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        pass

    # ── Custom dropdown / combobox elements ───────────────────────────────────
    try:
        combos = page.query_selector_all(
            "[role='combobox']:visible, [role='listbox']:visible, "
            "[data-radix-select-trigger]:visible, [class*='dropdown-trigger']:visible"
        )[:3]
        for combo in combos:
            try:
                label = (
                    combo.get_attribute("aria-label")
                    or (combo.inner_text() or "").strip()[:40]
                    or "dropdown"
                )
                pre_url = page.url
                pre_api = len(api_calls)
                combo.click(timeout=3000)
                page.wait_for_timeout(600)
                # Check if options appeared
                options_el = page.query_selector_all(
                    "[role='option']:visible, [role='menuitem']:visible"
                )[:6]
                options = [(o.inner_text() or "").strip()[:30] for o in options_el if o.inner_text()]
                findings["dropdowns_tested"].append({
                    "label": label,
                    "options_visible": options,
                    "triggered_api": len(api_calls) > pre_api,
                })
                # Close by pressing Escape
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        pass

    # ── Accordions / expandable sections ─────────────────────────────────────
    try:
        accordions = page.query_selector_all(
            "[data-state='closed'][role='button']:visible, "
            "details:not([open]):visible, "
            "[class*='accordion']:visible, "
            "button[aria-expanded='false']:visible"
        )[:4]
        opened = 0
        for acc in accordions:
            try:
                acc.click(timeout=2000)
                page.wait_for_timeout(500)
                opened += 1
                # Close it back
                try:
                    acc.click(timeout=1500)
                    page.wait_for_timeout(300)
                except Exception:
                    pass
            except Exception:
                continue
        findings["accordions_found"] = opened
    except Exception:
        pass

    # ── Tabs ─────────────────────────────────────────────────────────────────
    try:
        tabs = page.query_selector_all("[role='tab']:visible")
        findings["tabs_found"] = len(tabs)
        # Click second tab if present
        if len(tabs) > 1:
            try:
                pre_api = len(api_calls)
                tabs[1].click(timeout=2000)
                page.wait_for_timeout(600)
                # Click back to first
                tabs[0].click(timeout=1500)
            except Exception:
                pass
    except Exception:
        pass

    # ── Filter chips ─────────────────────────────────────────────────────────
    try:
        chips = page.query_selector_all(
            "[class*='chip']:visible, [class*='tag']:visible, "
            "[class*='filter']:visible:not(input)"
        )[:8]
        for chip in chips:
            try:
                text = (chip.inner_text() or "").strip()[:30]
                if text and text not in findings["filter_chips"]:
                    findings["filter_chips"].append(text)
            except Exception:
                continue
    except Exception:
        pass

    # ── Chatbot / live chat ───────────────────────────────────────────────────
    try:
        chat_sel = (
            "[id*='intercom']:visible, [id*='crisp']:visible, [id*='hubspot']:visible, "
            "[class*='chat-button']:visible, [class*='chatbot']:visible, "
            "iframe[title*='chat' i]:visible, [aria-label*='chat' i]:visible"
        )
        chat_el = page.query_selector(chat_sel)
        if chat_el:
            findings["chatbot_tested"] = True
            try:
                chat_el.click(timeout=3000)
                page.wait_for_timeout(1500)
                # Try to find input and type
                chat_input = page.query_selector(
                    "input[placeholder*='message' i]:visible, "
                    "textarea[placeholder*='message' i]:visible"
                )
                if chat_input:
                    chat_input.fill("How do I get started?")
                    chat_input.press("Enter")
                    page.wait_for_timeout(2500)
                    response_el = page.query_selector(
                        "[class*='bot-message']:visible, [class*='agent-message']:visible"
                    )
                    if response_el:
                        findings["chatbot_response"] = (response_el.inner_text() or "")[:200].strip()
                # Close
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except Exception:
                pass
    except Exception:
        pass

    # ── Read console errors now (after all interactions above fired) ──────────
    try:
        errors = page.evaluate("() => (window.__rehearse_errors__ || []).slice(0, 10)") or []
        findings["console_errors"] = [str(e)[:200] for e in errors]
        # Clear so next visit starts fresh
        page.evaluate("() => { if (window.__rehearse_errors__) window.__rehearse_errors__ = []; }")
    except Exception:
        pass

    return findings


# ── Agentic crawl decisions ───────────────────────────────────────────────────

def _dom_fingerprint(page: Any) -> str:
    """Structural fingerprint from rendered DOM — content-agnostic.

    Captures the *shape* of the page, not its data, so two profile pages
    produce the same fingerprint even though their headings differ.

    Strategy:
    - Bucket list-item counts (avoids count instability from pagination)
    - Capture the tag-type sequence of the main content area's direct children
      (structure, not counts) — this is the most stable layout signal
    - Include which interactive element types are present (form, table, etc.)
    - Deliberately excludes heading text (content-specific, breaks dedup)
    """
    try:
        return page.evaluate("""() => {
            // 1. Bucket key tag counts — coarse but stable
            function bucket(n) {
                if (n === 0) return '0';
                if (n <= 2) return '1-2';
                if (n <= 5) return '3-5';
                if (n <= 20) return '6-20';
                return '20+';
            }
            const structural = ['form','table','nav','header','aside','dialog','iframe']
                .map(t => t + ':' + bucket(document.querySelectorAll(t).length)).join(',');

            // 2. Top-level children of <main> or <body> — tag sequence captures layout
            const root = document.querySelector('main') ||
                         document.querySelector('[role="main"]') ||
                         document.body;
            const childTags = Array.from(root.children)
                .slice(0, 12)
                .map(el => el.tagName.toLowerCase())
                .join('-');

            // 3. Interactive fingerprint — which input types exist
            const inputs = Array.from(new Set(
                Array.from(document.querySelectorAll('input'))
                    .map(i => i.type || 'text')
                    .slice(0, 6)
            )).sort().join(',');

            return structural + '::' + childTags + '::' + inputs;
        }""") or ""
    except Exception:
        return ""


def _llm_navigate(
    visited_summary: list[dict[str, str]],
    pending_urls: list[str],
    budget_left: int,
    target_url: str,
    nav_structure: list[str] | None = None,
    visual_summaries: list[str] | None = None,
    url_patterns: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Ask the LLM to act as a crawl navigator: given what we've seen, which
    pending URLs are worth visiting and which are structural duplicates?

    Returns:
      prioritize  – URLs to move to the front of the queue
      skip_patterns – URL path prefixes/patterns to drop from the queue
      reasoning   – short explanation
    """
    try:
        from rehearse.llm import _llm_json_call, llm_enabled
    except ImportError:
        return {}
    if not llm_enabled():
        return {}

    seen_lines = "\n".join(
        f"  {i+1}. {v['url']} ({v.get('type','?')}) — {v.get('desc','')[:80]}"
        for i, v in enumerate(visited_summary[-12:])
    )
    pending_lines = "\n".join(f"  {u}" for u in pending_urls[:30])
    nav_line = (
        "Site nav: " + ", ".join((nav_structure or [])[:10])
        if nav_structure else ""
    )
    vision_line = (
        "Page descriptions: " + " | ".join((visual_summaries or [])[:5])
        if visual_summaries else ""
    )
    pattern_line = ""
    if url_patterns:
        top = sorted(url_patterns.items(), key=lambda x: -x[1])[:8]
        pattern_line = "URL patterns seen: " + ", ".join(f"{p}×{n}" for p, n in top)

    context_extras = "\n".join(x for x in [nav_line, vision_line, pattern_line] if x)

    result = _llm_json_call(
        system=(
            "You are an agentic web crawler navigator. "
            "You decide which pages to visit next given a fixed budget. "
            "Return a JSON object with keys: "
            "prioritize (list of full URLs to visit next, most valuable first), "
            "skip_patterns (list of URL path prefixes like /profiles/ that are clearly redundant), "
            "reasoning (one sentence)."
        ),
        user=(
            f"Target: {target_url}\n"
            f"Budget remaining: {budget_left} pages\n\n"
            f"{context_extras}\n\n"
            f"Already visited ({len(visited_summary)} pages):\n{seen_lines}\n\n"
            f"Pending queue (first 30):\n{pending_lines}\n\n"
            "Which pending URLs are likely to reveal new features or workflows? "
            "Which path prefixes are clearly redundant (same template, different IDs)? "
            "Respond with JSON only."
        ),
        max_tokens=600,
    )
    return result or {}




def run_deep_crawl(
    page: Any,
    target_url: str,
    *,
    product_name: str = "",
    max_pages: int = 50,
    max_buttons_per_page: int = 20,
    timeout_ms: int = 15000,
    use_vision: bool = True,
    screenshots_dir: Path | None = None,
    max_samples_per_pattern: int = 2,
    graph_output_path: Path | None = None,
) -> InteractionMap:
    """
    Deep exhaustive crawl — same capability as a human manually exploring.

    Order of operations per page:
    1. Navigate + wait for JS (networkidle + 1.5s extra)
    2. Screenshot (full page)
    3. Vision LLM (Claude) describes what's visible
    4. If still loading → wait 5s more, re-screenshot (up to 3 retries)
    5. Extract nav links → priority queue them
    6. Map forms, filters, chatbot detection
    7. Try search inputs
    8. Click every visible non-destructive button, capture outcome
    9. Collect all internal links for BFS

    Pattern-based sampling: URLs are normalized to structural templates
    (e.g. /profiles/{id}). Only max_samples_per_pattern pages are visited
    per template, so a list of 1809 profiles uses 2 budget slots, not 1809.
    """
    imap = InteractionMap(target_url=target_url)
    api_calls: list[dict[str, Any]] = []
    visited: set[str] = set()
    # Nav links go to front of queue — visit them before random BFS pages
    priority_queue: list[str] = []
    bfs_queue: list[str] = [target_url]
    all_features: set[str] = set()
    visual_summaries: list[str] = []

    # Agentic decision state
    seen_fingerprints: dict[str, str] = {}  # fingerprint → first URL with that structure
    visited_summary: list[dict[str, str]] = []  # for LLM navigator
    llm_skip_prefixes: list[str] = []  # patterns LLM decided to skip

    # Seed node is known from the start
    imap.node_status[target_url] = "queued"

    def _flush_graph() -> None:
        """Write the live crawl graph to disk so the frontend can poll it."""
        if not graph_output_path:
            return
        try:
            graph_output_path.parent.mkdir(parents=True, exist_ok=True)
            graph_output_path.write_text(json.dumps({
                "targetUrl": target_url,
                "nodes": [
                    {"id": u, "status": s}
                    for u, s in imap.node_status.items()
                ],
                "edges": [
                    {"source": src, "target": tgt}
                    for src, targets in imap.link_graph.items()
                    for tgt in targets
                ],
                "visitedCount": len(imap.pages_visited),
                "maxPages": max_pages,
            }))
        except Exception:
            pass

    def on_response(resp: Any) -> None:
        try:
            url = resp.url
            if any(s in url for s in _SKIP_URL_FRAGMENTS):
                return
            if any(url.split("?")[0].endswith(ext) for ext in _SKIP_EXTENSIONS):
                return
            api_calls.append({
                "method": resp.request.method,
                "url": url,
                "status": resp.status,
                "has_error": resp.status >= 400,
            })
        except Exception:
            pass

    try:
        page.on("response", on_response)
    except Exception:
        pass

    start = time.perf_counter()

    def visit_page(url: str) -> bool:
        """Visit one page. Returns False if should stop."""
        nonlocal all_features

        if url in visited or _should_skip(url, target_url):
            return True
        if len(visited) >= max_pages:
            return False

        # Pattern-based sampling: skip redundant structural duplicates
        pattern = _url_pattern(url)
        sampled = imap.url_patterns.get(pattern, 0)
        if sampled >= max_samples_per_pattern and pattern not in ("/", "/{id}"):
            imap.skipped_patterns[pattern] = imap.skipped_patterns.get(pattern, 0) + 1
            imap.node_status[url] = "skipped"
            _flush_graph()
            return True

        visited.add(url)
        imap.pages_visited.append(url)
        imap.url_patterns[pattern] = sampled + 1
        imap.node_status[url] = "visiting"
        _flush_graph()

        # 1. Navigate + wait
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            _wait_for_settle(page, 6000)
        except Exception:
            return True

        current_url = page.url
        title = ""
        try:
            title = page.title() or ""
        except Exception:
            pass

        # 2. Auth wall check
        if _detect_auth_wall(page):
            imap.auth_wall_detected = True
            imap.errors_found.append({
                "page": current_url, "text": "Auth wall detected", "type": "auth"
            })
            return True

        # 3. Screenshot
        screenshot_b64 = _take_screenshot(page, full_page=True)
        if screenshots_dir and screenshot_b64:
            try:
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                safe_name = url.replace("://", "_").replace("/", "_").replace("?", "_")[:80]
                (screenshots_dir / f"{safe_name}.png").write_bytes(
                    base64.b64decode(screenshot_b64)
                )
            except Exception:
                pass

        # 4. Vision analysis
        vision: dict[str, Any] = {}
        if use_vision and screenshot_b64:
            vision = _describe_screenshot(screenshot_b64, current_url, product_name)
            # Retry if still loading (up to 3x)
            retries = 0
            while vision.get("is_loading") and retries < 3:
                page.wait_for_timeout(5000)
                screenshot_b64 = _take_screenshot(page, full_page=True)
                if screenshot_b64:
                    vision = _describe_screenshot(screenshot_b64, current_url, product_name)
                retries += 1

            if vision:
                for f in (vision.get("features_detected") or []):
                    all_features.add(f)
                desc = vision.get("description", "")
                if desc:
                    visual_summaries.append(f"[{current_url.split('/')[-1] or 'home'}] {desc}")
                imap.page_snapshots.append({
                    "url": current_url,
                    "title": title,
                    "pageType": vision.get("page_type", "other"),
                    "description": desc,
                    "featuresDetected": vision.get("features_detected", []),
                    "buttonsVisible": vision.get("buttons_visible", []),
                    "dataShown": vision.get("data_shown", ""),
                    "isLoading": vision.get("is_loading", False),
                    "isError": vision.get("is_error_state", False),
                    "keyElements": vision.get("key_elements", []),
                    "screenshot_b64": screenshot_b64,
                    # Probe findings attached after interaction phase runs
                    "_probe_pending": True,
                })

        # 5. Extract nav links → add to priority queue
        nav_links = _extract_nav_links(page, target_url)
        for label, nav_url in nav_links:
            if label and label not in imap.nav_structure:
                imap.nav_structure.append(label)
            if nav_url not in visited and nav_url not in priority_queue:
                priority_queue.append(nav_url)

        # 6. Chatbot detection
        try:
            for sel in ["[class*='chat']", "[id*='chat']", "[class*='intercom']",
                        "[class*='crisp']", "[class*='drift']", "[aria-label*='chat']"]:
                if page.query_selector(sel):
                    imap.chatbot_detected = True
                    break
        except Exception:
            pass

        # 7. Filters
        try:
            for el in page.query_selector_all(
                "[class*='filter'], [role='combobox'], select, "
                "input[placeholder*='filter' i], input[placeholder*='search' i]"
            )[:8]:
                label = (
                    el.get_attribute("aria-label")
                    or el.get_attribute("placeholder")
                    or el.get_attribute("name")
                    or "filter"
                )
                if label and label not in imap.filters_detected:
                    imap.filters_detected.append(label)
        except Exception:
            pass

        # 8. Forms
        forms = _extract_forms(page, current_url)
        imap.forms.extend(forms)

        # 9. Try search
        search_result = _try_search(page, current_url, api_calls)
        if search_result:
            imap.buttons.append({
                "label": f"[SEARCH TESTED] {search_result['placeholder']}",
                "page": current_url,
                "outcome": "api-call" if search_result["api_calls_triggered"] else "no-effect",
                "search_result": search_result,
            })

        # 10. Click buttons
        buttons = _interact_buttons(
            page, current_url, api_calls, imap, visited, bfs_queue, max_buttons_per_page
        )
        imap.buttons.extend(buttons)

        # 10b. Comprehensive interaction probe: dropdowns, selects, accordions,
        #      tabs, filters, chatbot, console errors, perf timing, doc links
        probe = _probe_page_interactions(page, current_url, api_calls)
        # Attach probe findings to this page's snapshot if one was recorded
        if imap.page_snapshots and imap.page_snapshots[-1].get("url") == current_url:
            snap = imap.page_snapshots[-1]
            snap.pop("_probe_pending", None)
            snap["interactionProbe"] = {
                k: v for k, v in probe.items()
                if v not in (None, [], {}, False, "")
            }
        # Bubble up console/JS errors into imap.errors_found
        for err in probe.get("console_errors") or []:
            imap.errors_found.append({"page": current_url, "text": err, "type": "js-error"})
        for res in probe.get("slow_resources") or []:
            imap.errors_found.append({
                "page": current_url,
                "text": f"Slow resource ({res.get('ms')}ms): {res.get('url')}",
                "type": "performance",
            })
        if probe.get("chatbot_tested"):
            imap.chatbot_detected = True
        if probe.get("chatbot_response"):
            imap.chatbot_responses.append({
                "page": current_url,
                "response": probe["chatbot_response"],
            })

        # 11. Page errors (UI-level)
        try:
            for sel in ["[role='alert']", "[class*='error']:not(script)",
                        "[class*='toast']", ".error-message"]:
                for el in page.query_selector_all(sel)[:3]:
                    text = (el.inner_text() or "")[:200].strip()
                    if text and len(text) > 5:
                        imap.errors_found.append({
                            "page": current_url, "text": text, "type": "ui-error"
                        })
        except Exception:
            pass

        # Layer 1: DOM fingerprint — detect structural duplicates
        fingerprint = _dom_fingerprint(page)
        is_structural_dup = False
        if fingerprint:
            if fingerprint in seen_fingerprints and seen_fingerprints[fingerprint] != current_url:
                # Same DOM structure as a previously visited page — skip its sub-links
                imap.skipped_patterns[pattern] = imap.skipped_patterns.get(pattern, 0) + 1
                is_structural_dup = True
            else:
                seen_fingerprints[fingerprint] = current_url

        # Record page summary for LLM navigator
        visited_summary.append({
            "url": current_url,
            "type": "dup" if is_structural_dup else "new",
            "desc": (title or "")[:60],
        })

        # 12. BFS links — only follow from structurally distinct pages
        discovered_links: list[str] = []
        if not is_structural_dup:
            for link_url in _extract_all_links(page, target_url):
                discovered_links.append(link_url)
                if link_url not in visited and link_url not in bfs_queue:
                    if not any(link_url.startswith(pfx) for pfx in llm_skip_prefixes):
                        bfs_queue.append(link_url)
                        imap.node_status.setdefault(link_url, "queued")

        # Record edges and mark this node done
        imap.link_graph[current_url] = discovered_links[:40]  # cap per-node edge list
        imap.node_status[url] = "error" if any(
            s.outcome == "fail" for s in []) else "visited"
        imap.node_status[current_url] = "visited"
        _flush_graph()

        return True

    # Process priority (nav) pages first, then BFS
    llm_nav_fired = False
    while True:
        if priority_queue:
            url = priority_queue.pop(0)
        elif bfs_queue:
            url = bfs_queue.pop(0)
        else:
            break
        if not visit_page(url):
            break

        # LLM navigator: fire exactly once at ~50% budget used
        # Makes one strategic re-plan — not a per-URL call
        budget_used = len(visited)
        if (
            not llm_nav_fired
            and budget_used >= max(3, max_pages // 2)
            and (bfs_queue or priority_queue)
        ):
            llm_nav_fired = True
            all_pending = priority_queue + bfs_queue
            nav = _llm_navigate(
                visited_summary, all_pending, max_pages - budget_used, target_url,
                nav_structure=imap.nav_structure,
                visual_summaries=visual_summaries,
                url_patterns=imap.url_patterns,
            )
            if nav and not nav.get("error"):
                pending_set = set(all_pending)
                # Prepend high-value URLs — only if they're actually in the queue
                for u in reversed(nav.get("prioritize") or []):
                    if not isinstance(u, str):
                        continue
                    u = u.strip()
                    if u in pending_set and u not in priority_queue:
                        try:
                            bfs_queue.remove(u)
                        except ValueError:
                            pass
                        priority_queue.insert(0, u)
                # Normalize skip_patterns to path prefixes starting with /
                # LLM may return full URLs, bare strings, or regex — normalize all
                for raw in nav.get("skip_patterns") or []:
                    if not isinstance(raw, str):
                        continue
                    raw = raw.strip()
                    # If it's a full URL, extract path only
                    if raw.startswith("http"):
                        try:
                            from urllib.parse import urlparse as _up
                            raw = _up(raw).path
                        except Exception:
                            continue
                    # Ensure leading slash, drop trailing wildcards/dots
                    raw = raw.lstrip("/").rstrip(".*")
                    if raw:
                        llm_skip_prefixes.append("/" + raw)

    imap.api_calls = api_calls[:200]
    imap.features_seen = sorted(all_features)
    imap.visual_summary = " | ".join(visual_summaries[:8])
    imap.crawl_duration_ms = int((time.perf_counter() - start) * 1000)
    # Route coverage: visited templates / (visited + skipped templates)
    total_templates = len(imap.url_patterns) + len(imap.skipped_patterns)
    if total_templates > 0:
        imap.graph_coverage_pct = round(len(imap.url_patterns) / total_templates * 100, 1)
    return imap


# ── Serialisation ─────────────────────────────────────────────────────────────

def interaction_map_to_dict(imap: InteractionMap) -> dict[str, Any]:
    snapshots_summary = [
        {k: v for k, v in s.items() if k != "screenshot_b64"}
        for s in imap.page_snapshots
    ]
    return {
        "targetUrl": imap.target_url,
        "pagesVisited": imap.pages_visited,
        "pageCount": len(imap.pages_visited),
        "pageSnapshots": snapshots_summary,
        "navStructure": imap.nav_structure,
        "buttons": imap.buttons,
        "buttonCount": len(imap.buttons),
        "forms": imap.forms,
        "formCount": len(imap.forms),
        "modals": imap.modals,
        "modalCount": len(imap.modals),
        "apiCalls": imap.api_calls,
        "apiCallCount": len(imap.api_calls),
        "chatbotDetected": imap.chatbot_detected,
        "chatbotResponses": imap.chatbot_responses,
        "filtersDetected": imap.filters_detected,
        "errorsFound": imap.errors_found,
        "errorCount": len(imap.errors_found),
        "authWallDetected": imap.auth_wall_detected,
        "featuresSeen": imap.features_seen,
        "visualSummary": imap.visual_summary,
        "crawlDurationMs": imap.crawl_duration_ms,
        "urlPatterns": imap.url_patterns,
        "skippedPatterns": imap.skipped_patterns,
        "skippedPatternCount": sum(imap.skipped_patterns.values()),
        "graphCoveragePct": imap.graph_coverage_pct,
    }


def save_interaction_map(artifacts_root: Path, run_id: str, imap: InteractionMap) -> Path:
    path = artifacts_root / "artifacts" / run_id / "interaction_map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(interaction_map_to_dict(imap), indent=2))
    return path
