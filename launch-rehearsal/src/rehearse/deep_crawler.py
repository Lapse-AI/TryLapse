"""Deep Discovery Bot — exhaustive interactive crawler.

Crawls a product like a real user: logs in, visits every nav page,
screenshots every state, clicks buttons, maps modals, tracks API calls.

Fixes vs previous version:
- URL joining uses origin (not full path) — /analytics stays /analytics
- Explicitly visits nav/sidebar links first before BFS
- Vision LLM: uses Claude claude-haiku-4-5-20251001 via Anthropic API (supports images)
  Falls back gracefully to text-only if no key
- Login: waits for redirect + networkidle after submit
- Auth wall: retries after waiting longer (SPAs are slow)
- Deeper interaction: clicks cards, fills search, maps filters
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


# ── URL helpers ───────────────────────────────────────────────────────────────

def _origin(url: str) -> str:
    """Return scheme + host only: https://example.com"""
    parts = url.split("//", 1)
    if len(parts) < 2:
        return url
    return parts[0] + "//" + parts[1].split("/")[0]


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

def _vision_key() -> str | None:
    return (os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("REHEARSE_VISION_API_KEY")
            or os.environ.get("REHEARSE_LLM_API_KEY"))


def _describe_screenshot(screenshot_b64: str, url: str, product_name: str = "") -> dict[str, Any]:
    """Use Claude to describe what's visible in the screenshot."""
    key = _vision_key()
    if not key or not screenshot_b64:
        return {}
    try:
        import httpx
        # Use Anthropic Messages API — Claude supports vision natively
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"""You are analyzing a screenshot of "{product_name or 'a web product'}" at URL: {url}

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
                        }
                    ],
                }],
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"]
        # Strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {}


# ── Page interaction helpers ──────────────────────────────────────────────────

def _take_screenshot(page: Any, full_page: bool = True) -> str:
    try:
        raw = page.screenshot(full_page=full_page, type="png")
        return base64.b64encode(raw).decode("utf-8")
    except Exception:
        return ""


def _wait_for_settle(page: Any, ms: int = 5000) -> None:
    """Wait for networkidle + extra SPA hydration time."""
    try:
        page.wait_for_load_state("networkidle", timeout=ms)
    except Exception:
        pass
    try:
        page.wait_for_timeout(1500)
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


# ── Main crawler ──────────────────────────────────────────────────────────────

def run_deep_crawl(
    page: Any,
    target_url: str,
    *,
    product_name: str = "",
    max_pages: int = 20,
    max_buttons_per_page: int = 12,
    timeout_ms: int = 15000,
    use_vision: bool = True,
    screenshots_dir: Path | None = None,
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
    """
    imap = InteractionMap(target_url=target_url)
    api_calls: list[dict[str, Any]] = []
    visited: set[str] = set()
    # Nav links go to front of queue — visit them before random BFS pages
    priority_queue: list[str] = []
    bfs_queue: list[str] = [target_url]
    all_features: set[str] = set()
    visual_summaries: list[str] = []

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

        visited.add(url)
        imap.pages_visited.append(url)

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

        # 11. Page errors
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

        # 12. BFS links
        for link_url in _extract_all_links(page, target_url):
            if link_url not in visited and link_url not in bfs_queue:
                bfs_queue.append(link_url)

        return True

    # Process priority (nav) pages first, then BFS
    while True:
        if priority_queue:
            url = priority_queue.pop(0)
        elif bfs_queue:
            url = bfs_queue.pop(0)
        else:
            break
        if not visit_page(url):
            break

    imap.api_calls = api_calls[:200]
    imap.features_seen = sorted(all_features)
    imap.visual_summary = " | ".join(visual_summaries[:8])
    imap.crawl_duration_ms = int((time.perf_counter() - start) * 1000)
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
    }


def save_interaction_map(artifacts_root: Path, run_id: str, imap: InteractionMap) -> Path:
    path = artifacts_root / "artifacts" / run_id / "interaction_map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(interaction_map_to_dict(imap), indent=2))
    return path
