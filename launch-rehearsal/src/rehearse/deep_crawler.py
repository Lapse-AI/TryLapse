"""Deep Discovery Bot — vision-aware exhaustive crawler.

Goes beyond link-following to understand the product like a real user:
- Screenshots every page state and uses vision AI to interpret UI
- Clicks every visible button, opens every modal/drawer/dropdown
- Fills forms, intercepts all API calls, maps auth gates
- Waits for JS-rendered content before analyzing
- Builds a complete VisualInteractionMap for product intelligence

Runs standalone before journey generation — the richer the map,
the better the persona journeys the LLM can generate.
"""

from __future__ import annotations

import base64
import json
import os
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
    "query":      "test query",
    "default":    "test value",
}

_DESTRUCTIVE = {"delete", "remove", "cancel", "unsubscribe", "deactivate",
                "disable", "logout", "sign out", "reset", "clear all", "archive"}

_SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                    ".woff", ".woff2", ".ttf", ".css", ".js", ".map"}


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
    visual_description: str = ""  # from vision LLM
    features_detected: list[str] = field(default_factory=list)  # from vision LLM


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
    visual_summary: str = ""  # aggregated across all pages
    crawl_duration_ms: int = 0


# ── Vision LLM helpers ────────────────────────────────────────────────────────

def _vision_api_key() -> str | None:
    return os.environ.get("REHEARSE_VISION_API_KEY") or os.environ.get("REHEARSE_LLM_API_KEY")


def _vision_base_url() -> str:
    return os.environ.get("REHEARSE_VISION_BASE_URL", "https://api.deepseek.com/v1")


def _describe_screenshot(screenshot_b64: str, url: str, product_name: str = "") -> dict[str, Any]:
    """Ask vision LLM to describe the UI visible in the screenshot."""
    key = _vision_api_key()
    if not key or not screenshot_b64:
        return {}
    try:
        import httpx
        base = _vision_base_url()
        model = os.environ.get("REHEARSE_VISION_MODEL", "deepseek-chat")
        prompt = f"""You are analyzing a screenshot of a web product called "{product_name or 'unknown'}" at URL: {url}

Describe what you see precisely. Return JSON only:
{{
  "page_type": "dashboard|login|onboarding|settings|analytics|table|form|landing|error|loading|other",
  "description": "One paragraph describing what is visible on screen",
  "features_detected": ["list", "of", "specific", "UI features", "or", "sections", "visible"],
  "buttons_visible": ["list of button labels visible on screen"],
  "data_shown": "describe any data, charts, tables, metrics visible",
  "auth_required": true/false,
  "is_loading": true/false,
  "is_error_state": true/false,
  "key_elements": ["important UI elements a tester should know about"]
}}"""
        # Vision model via base64 image
        resp = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{screenshot_b64}",
                            "detail": "high"
                        }},
                    ],
                }],
                "temperature": 0.2,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
            },
            timeout=45.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        return {}


# ── Crawler helpers ───────────────────────────────────────────────────────────

def _safe_fill_value(label: str) -> str:
    label_lower = label.lower()
    for key, val in _SAFE_FILL.items():
        if key in label_lower:
            return val
    return _SAFE_FILL["default"]


def _is_destructive(label: str) -> bool:
    return any(d in label.lower() for d in _DESTRUCTIVE)


def _should_skip_url(url: str, target_url: str) -> bool:
    if not url.startswith("http"):
        return True
    if target_url.split("//")[1].split("/")[0] not in url:
        return True  # different domain
    for ext in _SKIP_EXTENSIONS:
        if url.split("?")[0].endswith(ext):
            return True
    return False


def _take_screenshot(page: Any) -> str:
    """Take screenshot, return base64 string."""
    try:
        raw = page.screenshot(full_page=False, type="png")
        return base64.b64encode(raw).decode("utf-8")
    except Exception:
        return ""


def _wait_for_content(page: Any, timeout_ms: int = 5000) -> None:
    """Wait for page to settle after JS rendering."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        pass
    try:
        # Extra wait for SPAs that render after networkidle
        page.wait_for_timeout(1500)
    except Exception:
        pass


def _extract_nav(page: Any) -> list[str]:
    """Extract navigation items."""
    nav_items = []
    try:
        navs = page.query_selector_all("nav a, [role='navigation'] a, header a, aside a")
        for el in navs[:20]:
            text = (el.inner_text() or "").strip()[:40]
            if text and text not in nav_items:
                nav_items.append(text)
    except Exception:
        pass
    return nav_items


def _extract_visible_text(page: Any, max_chars: int = 1000) -> str:
    """Extract key visible text from page."""
    try:
        # Get headings and key text
        texts = []
        for sel in ["h1", "h2", "h3", "[role='heading']", "p"]:
            els = page.query_selector_all(sel)
            for el in els[:8]:
                t = (el.inner_text() or "").strip()[:100]
                if t:
                    texts.append(t)
        return " | ".join(texts)[:max_chars]
    except Exception:
        return ""


def _detect_auth_wall(page: Any) -> bool:
    """Detect if page requires authentication."""
    try:
        url = page.url.lower()
        if any(p in url for p in ["/login", "/signin", "/auth", "/sign-in"]):
            return True
        # Check for login form
        if page.query_selector("input[type='password']"):
            return True
        # Check for auth-related text
        text = page.inner_text("body")[:500].lower()
        if any(w in text for w in ["sign in", "log in", "please login", "unauthorized"]):
            return True
    except Exception:
        pass
    return False


def _map_forms(page: Any, current_url: str) -> list[dict[str, Any]]:
    """Map all forms on page."""
    forms_data = []
    try:
        forms = page.query_selector_all("form, [role='form']")
        for form in forms[:5]:
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
                inp_type = inp.get_attribute("type") or "text"
                fields.append({"label": label, "type": inp_type})
            if fields:
                forms_data.append({"page": current_url, "fields": fields})
    except Exception:
        pass
    return forms_data


def _interact_buttons(
    page: Any,
    current_url: str,
    api_calls: list[dict[str, Any]],
    imap: InteractionMap,
    visited: set[str],
    queue: list[str],
    max_buttons: int = 12,
) -> list[dict[str, Any]]:
    """Click all visible non-destructive buttons, capture outcomes."""
    buttons_data = []
    try:
        button_sels = (
            "button:visible, [role='button']:visible, "
            "[role='tab']:visible, [role='menuitem']:visible"
        )
        buttons = page.query_selector_all(button_sels)

        clicked = 0
        for btn in buttons[:max_buttons * 2]:
            if clicked >= max_buttons:
                break
            try:
                if not btn.is_visible():
                    continue

                label = (
                    btn.get_attribute("aria-label")
                    or (btn.inner_text() or "")[:50].strip()
                    or btn.get_attribute("title")
                    or btn.get_attribute("data-testid")
                    or "unnamed"
                )
                label = label.strip()

                if _is_destructive(label) or not label:
                    continue

                pre_url = page.url
                pre_api_count = len(api_calls)
                pre_screenshot = _take_screenshot(page)

                btn.scroll_into_view_if_needed()
                btn.click(timeout=4000)
                page.wait_for_timeout(1200)
                _wait_for_content(page, 2000)

                post_url = page.url
                new_apis = api_calls[pre_api_count:]

                outcome = "no-effect"
                modal_content = ""
                modal_screenshot = ""

                if post_url != pre_url and not _should_skip_url(post_url, imap.target_url):
                    outcome = "navigated"
                    if post_url not in visited:
                        queue.append(post_url)
                elif new_apis:
                    outcome = "api-call"

                # Check for modals/drawers
                modal = page.query_selector(
                    "[role='dialog']:visible, [class*='modal']:visible, "
                    "[class*='Modal']:visible, [class*='drawer']:visible, "
                    "[class*='Drawer']:visible, [class*='sheet']:visible"
                )
                if modal:
                    outcome = "opened-modal"
                    try:
                        modal_content = (modal.inner_text() or "")[:300].strip()
                        modal_screenshot = _take_screenshot(page)
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

                buttons_data.append({
                    "label": label,
                    "page": current_url,
                    "outcome": outcome,
                    "api_calls": [a.get("url", "")[-80:] for a in new_apis[:3]],
                    "modal_content": modal_content[:100] if modal_content else "",
                })
                clicked += 1

                # Go back if navigated away
                if page.url != current_url:
                    try:
                        page.go_back()
                        _wait_for_content(page, 1500)
                    except Exception:
                        try:
                            page.goto(current_url, wait_until="domcontentloaded", timeout=8000)
                            _wait_for_content(page, 1500)
                        except Exception:
                            break

            except Exception:
                continue

    except Exception:
        pass
    return buttons_data


# ── Main crawler ──────────────────────────────────────────────────────────────

def run_deep_crawl(
    page: Any,
    target_url: str,
    *,
    product_name: str = "",
    max_pages: int = 15,
    max_buttons_per_page: int = 12,
    timeout_ms: int = 12000,
    use_vision: bool = True,
    screenshots_dir: Path | None = None,
) -> InteractionMap:
    """
    Run exhaustive vision-aware discovery crawl.

    For each page:
      1. Navigate and wait for JS to fully render
      2. Take full screenshot
      3. Ask vision LLM to describe UI, features, buttons
      4. Map nav, forms, filters, chatbot
      5. Click every visible button, capture outcomes (modal, navigate, API)
      6. Collect errors and API calls

    Returns a rich InteractionMap for product intelligence analysis.
    """
    imap = InteractionMap(target_url=target_url)
    api_calls: list[dict[str, Any]] = []
    visited: set[str] = set()
    queue: list[str] = [target_url]
    all_features: set[str] = set()
    visual_summaries: list[str] = []

    def on_response(response: Any) -> None:
        try:
            url = response.url
            skip = {"analytics", "tracking", "hotjar", "segment", "sentry",
                    ".png", ".css", ".js", ".woff", "favicon", "gtm", "clarity"}
            if any(s in url for s in skip):
                return
            api_calls.append({
                "method": response.request.method,
                "url": url,
                "status": response.status,
                "has_error": response.status >= 400,
            })
        except Exception:
            pass

    try:
        page.on("response", on_response)
    except Exception:
        pass

    start = time.perf_counter()

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited or _should_skip_url(url, target_url):
            continue
        visited.add(url)
        imap.pages_visited.append(url)

        # 1. Navigate and wait for content — SPAs need extra time
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            _wait_for_content(page, 6000)
        except Exception:
            continue

        current_url = page.url
        title = ""
        try:
            title = page.title() or ""
        except Exception:
            pass

        # 2. Check for auth wall
        if _detect_auth_wall(page):
            imap.auth_wall_detected = True
            imap.errors_found.append({
                "page": current_url,
                "text": "Auth wall detected — page requires login",
                "type": "auth"
            })
            # Still screenshot and describe the login page
            screenshot_b64 = _take_screenshot(page)
            if use_vision and screenshot_b64:
                vision_result = _describe_screenshot(screenshot_b64, current_url, product_name)
                if vision_result:
                    imap.page_snapshots.append({
                        "url": current_url,
                        "title": title,
                        "pageType": vision_result.get("page_type", "login"),
                        "description": vision_result.get("description", ""),
                        "featuresDetected": vision_result.get("features_detected", []),
                        "buttonsVisible": vision_result.get("buttons_visible", []),
                        "authRequired": True,
                        "screenshot_b64": screenshot_b64,
                    })
            continue

        # 3. Take screenshot
        screenshot_b64 = _take_screenshot(page)
        if screenshots_dir and screenshot_b64:
            try:
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                safe_name = url.replace("://", "_").replace("/", "_")[:80]
                (screenshots_dir / f"{safe_name}.png").write_bytes(
                    base64.b64decode(screenshot_b64)
                )
            except Exception:
                pass

        # 4. Vision analysis
        vision_result: dict[str, Any] = {}
        if use_vision and screenshot_b64:
            vision_result = _describe_screenshot(screenshot_b64, current_url, product_name)
            if vision_result:
                features = vision_result.get("features_detected") or []
                for f in features:
                    all_features.add(f)
                desc = vision_result.get("description", "")
                if desc:
                    visual_summaries.append(f"[{current_url}] {desc}")
                imap.page_snapshots.append({
                    "url": current_url,
                    "title": title,
                    "pageType": vision_result.get("page_type", "other"),
                    "description": desc,
                    "featuresDetected": features,
                    "buttonsVisible": vision_result.get("buttons_visible", []),
                    "dataShown": vision_result.get("data_shown", ""),
                    "isLoading": vision_result.get("is_loading", False),
                    "isError": vision_result.get("is_error_state", False),
                    "keyElements": vision_result.get("key_elements", []),
                    "screenshot_b64": screenshot_b64,
                })

                # If still loading, wait longer and re-screenshot (up to 3 retries)
                retries = 0
                while vision_result.get("is_loading") and retries < 3:
                    page.wait_for_timeout(5000)
                    screenshot_b64 = _take_screenshot(page)
                    if use_vision and screenshot_b64:
                        vision_result2 = _describe_screenshot(screenshot_b64, current_url, product_name)
                        if vision_result2:
                            vision_result = vision_result2
                            for f in (vision_result2.get("features_detected") or []):
                                all_features.add(f)
                    retries += 1

        # 5. Extract nav structure
        nav_items = _extract_nav(page)
        for item in nav_items:
            if item not in imap.nav_structure:
                imap.nav_structure.append(item)

        # 6. Detect chatbot
        try:
            for sel in ["[class*='chat']", "[id*='chat']", "[class*='intercom']",
                        "[class*='crisp']", "iframe[src*='tawk']", "[class*='zendesk']",
                        "[class*='drift']", "[aria-label*='chat']"]:
                if page.query_selector(sel):
                    imap.chatbot_detected = True
                    break
        except Exception:
            pass

        # 7. Detect filters
        try:
            for el in page.query_selector_all(
                "[class*='filter'], [role='combobox'], select, [aria-label*='filter']"
            )[:8]:
                label = (
                    el.get_attribute("aria-label")
                    or el.get_attribute("name")
                    or el.get_attribute("placeholder")
                    or "filter"
                )
                if label and label not in imap.filters_detected:
                    imap.filters_detected.append(label)
        except Exception:
            pass

        # 8. Map forms
        forms = _map_forms(page, current_url)
        imap.forms.extend(forms)

        # 9. Collect visible text for context
        visible_text = _extract_visible_text(page)

        # 10. Click buttons and map interactions
        buttons = _interact_buttons(
            page, current_url, api_calls, imap,
            visited, queue, max_buttons_per_page
        )
        imap.buttons.extend(buttons)

        # 11. Collect page errors
        try:
            for sel in ["[class*='error']:not(script)", "[role='alert']",
                        "[class*='ErrorBoundary']", "[class*='toast'][class*='error']"]:
                for el in page.query_selector_all(sel)[:3]:
                    text = (el.inner_text() or "")[:200].strip()
                    if text and len(text) > 5:
                        imap.errors_found.append({
                            "page": current_url,
                            "text": text,
                            "type": "ui-error"
                        })
        except Exception:
            pass

        # 12. Collect links for BFS queue
        try:
            for link in page.query_selector_all("a[href]")[:40]:
                href = link.get_attribute("href") or ""
                if href.startswith("/"):
                    full = target_url.rstrip("/") + href
                elif href.startswith("http"):
                    full = href
                else:
                    continue
                if full not in visited and not _should_skip_url(full, target_url):
                    queue.append(full)
        except Exception:
            pass

    imap.api_calls = api_calls[:150]
    imap.features_seen = sorted(all_features)
    imap.visual_summary = " | ".join(visual_summaries[:5])
    imap.crawl_duration_ms = int((time.perf_counter() - start) * 1000)
    return imap


# ── Serialisation ─────────────────────────────────────────────────────────────

def interaction_map_to_dict(imap: InteractionMap) -> dict[str, Any]:
    """Convert to dict — strip raw screenshots from summary to keep it lean."""
    snapshots_summary = []
    for s in imap.page_snapshots:
        snapshots_summary.append({k: v for k, v in s.items() if k != "screenshot_b64"})

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
    }


def save_interaction_map(artifacts_root: Path, run_id: str, imap: InteractionMap) -> Path:
    path = artifacts_root / "artifacts" / run_id / "interaction_map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(interaction_map_to_dict(imap), indent=2))
    return path
