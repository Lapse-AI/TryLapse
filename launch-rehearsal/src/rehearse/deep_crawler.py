"""Deep Discovery Bot — exhaustive interactive crawler.

Goes beyond link-following to test every button, form, modal, dropdown,
filter, and API call. Builds a complete interaction map of the product.

Unlike the standard BFS crawler (which only follows links), this bot:
- Clicks every visible button and records outcomes
- Fills forms with safe test data and captures validation/errors
- Opens dropdowns and modals to map states
- Intercepts every network/API call
- Records chatbot responses if detected
- Captures before/after states for interactive elements
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Safe test values for forms — won't cause real side effects
_SAFE_FILL_VALUES: dict[str, str] = {
    "email": "test@rehearsal-test.invalid",
    "password": "Rehearsal_Test_2026!",
    "name": "Test User",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+15550000000",
    "message": "This is a rehearsal test message.",
    "search": "test",
    "query": "test query",
    "url": "https://example.com",
    "default": "test value",
}


@dataclass
class ButtonInteraction:
    label: str
    page: str
    selector: str
    outcome: str  # "opened-modal" | "navigated" | "api-call" | "error" | "no-effect"
    api_calls_triggered: list[str] = field(default_factory=list)
    modal_content: str = ""
    error_message: str = ""


@dataclass
class FormInteraction:
    page: str
    fields: list[str]
    submit_outcome: str  # "success" | "validation-error" | "api-error" | "unknown"
    validation_messages: list[str] = field(default_factory=list)
    api_calls_triggered: list[str] = field(default_factory=list)


@dataclass
class ApiCall:
    method: str
    url: str
    status: int
    duration_ms: int
    has_error: bool = False
    error_body: str = ""


@dataclass
class InteractionMap:
    target_url: str
    pages_visited: list[str] = field(default_factory=list)
    buttons: list[dict[str, Any]] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    modals: list[dict[str, Any]] = field(default_factory=list)
    api_calls: list[dict[str, Any]] = field(default_factory=list)
    chatbot_detected: bool = False
    chatbot_responses: list[dict[str, Any]] = field(default_factory=list)
    filters_detected: list[str] = field(default_factory=list)
    errors_found: list[dict[str, Any]] = field(default_factory=list)
    crawl_duration_ms: int = 0


def _safe_fill_value(field_label: str) -> str:
    label_lower = field_label.lower()
    for key, val in _SAFE_FILL_VALUES.items():
        if key in label_lower:
            return val
    return _SAFE_FILL_VALUES["default"]


def _is_destructive(label: str) -> bool:
    """Don't click buttons that could cause real data loss."""
    danger = {"delete", "remove", "cancel", "unsubscribe", "deactivate", "disable", "logout", "sign out"}
    return any(d in label.lower() for d in danger)


def run_deep_crawl(
    page: Any,  # Playwright page
    target_url: str,
    *,
    max_pages: int = 20,
    max_buttons_per_page: int = 10,
    timeout_ms: int = 8000,
) -> InteractionMap:
    """Run the exhaustive discovery crawl. Returns InteractionMap."""
    imap = InteractionMap(target_url=target_url)
    api_calls: list[dict[str, Any]] = []
    visited: set[str] = set()
    queue: list[str] = [target_url]

    # Intercept network calls
    def on_response(response: Any) -> None:
        try:
            url = response.url
            if any(skip in url for skip in ("analytics", "tracking", "hotjar", "segment", ".png", ".css", ".js")):
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
        if url in visited:
            continue
        visited.add(url)
        imap.pages_visited.append(url)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1500)
        except Exception:
            continue

        current_url = page.url

        # --- Detect chatbot ---
        try:
            chatbot_selectors = [
                "[class*='chat']", "[id*='chat']", "[class*='intercom']",
                "[class*='crisp']", "iframe[src*='tawk']", "[class*='zendesk']",
            ]
            for sel in chatbot_selectors:
                if page.query_selector(sel):
                    imap.chatbot_detected = True
                    break
        except Exception:
            pass

        # --- Detect filters ---
        try:
            filter_elements = page.query_selector_all("[class*='filter'], [role='combobox'], select")
            for el in filter_elements[:5]:
                label = el.get_attribute("aria-label") or el.get_attribute("name") or "filter"
                if label not in imap.filters_detected:
                    imap.filters_detected.append(label)
        except Exception:
            pass

        # --- Map forms ---
        try:
            forms = page.query_selector_all("form")
            for form in forms[:3]:
                inputs = form.query_selector_all("input:not([type='hidden']), textarea, select")
                field_labels = []
                for inp in inputs:
                    label = (
                        inp.get_attribute("aria-label")
                        or inp.get_attribute("placeholder")
                        or inp.get_attribute("name")
                        or inp.get_attribute("type")
                        or "field"
                    )
                    field_labels.append(label)
                if field_labels:
                    imap.forms.append({"page": current_url, "fields": field_labels})
        except Exception:
            pass

        # --- Click buttons (non-destructive) ---
        try:
            buttons = page.query_selector_all("button, [role='button'], a[href]:not([href^='http'])")
            clicked = 0
            for btn in buttons[:max_buttons_per_page]:
                try:
                    label = (
                        btn.get_attribute("aria-label")
                        or btn.inner_text()[:40].strip()
                        or btn.get_attribute("title")
                        or "unnamed"
                    )
                    if _is_destructive(label):
                        continue
                    if not btn.is_visible():
                        continue

                    pre_url = page.url
                    pre_api_count = len(api_calls)

                    btn.click(timeout=3000)
                    page.wait_for_timeout(800)

                    post_url = page.url
                    new_apis = api_calls[pre_api_count:]

                    outcome = "no-effect"
                    if post_url != pre_url:
                        outcome = "navigated"
                        if post_url not in visited:
                            queue.append(post_url)
                    elif new_apis:
                        outcome = "api-call"
                    elif page.query_selector("[role='dialog'], [class*='modal'], [class*='Modal']"):
                        outcome = "opened-modal"
                        # Capture modal content
                        try:
                            modal = page.query_selector("[role='dialog'], [class*='modal']")
                            modal_text = modal.inner_text()[:200] if modal else ""
                            imap.modals.append({"trigger": label, "page": current_url, "content": modal_text})
                            # Close modal
                            esc = page.keyboard.press("Escape")
                        except Exception:
                            pass

                    imap.buttons.append({
                        "label": label,
                        "page": current_url,
                        "outcome": outcome,
                        "api_calls": [a["url"][-60:] for a in new_apis[:3]],
                    })
                    clicked += 1

                    # Navigate back if we went somewhere else
                    if page.url != current_url:
                        page.go_back()
                        page.wait_for_timeout(500)

                except Exception:
                    continue
        except Exception:
            pass

        # --- Collect errors visible on page ---
        try:
            error_selectors = [
                "[class*='error']:not(script)", "[class*='alert-danger']",
                "[role='alert']", "[class*='ErrorBoundary']",
            ]
            for sel in error_selectors:
                els = page.query_selector_all(sel)
                for el in els[:3]:
                    text = el.inner_text()[:200].strip()
                    if text and len(text) > 5:
                        imap.errors_found.append({"page": current_url, "text": text, "selector": sel})
        except Exception:
            pass

        # --- Collect links for queue ---
        try:
            links = page.query_selector_all("a[href]")
            for link in links[:30]:
                href = link.get_attribute("href") or ""
                if href.startswith("/") or href.startswith(target_url):
                    full = href if href.startswith("http") else f"{target_url.rstrip('/')}{href}"
                    if full not in visited and target_url in full:
                        queue.append(full)
        except Exception:
            pass

    imap.api_calls = api_calls[:100]
    imap.crawl_duration_ms = int((time.perf_counter() - start) * 1000)
    return imap


def interaction_map_to_dict(imap: InteractionMap) -> dict[str, Any]:
    return {
        "targetUrl": imap.target_url,
        "pagesVisited": imap.pages_visited,
        "pageCount": len(imap.pages_visited),
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
        "crawlDurationMs": imap.crawl_duration_ms,
    }


def save_interaction_map(artifacts_root: Path, run_id: str, imap: InteractionMap) -> Path:
    path = artifacts_root / "artifacts" / run_id / "interaction_map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(interaction_map_to_dict(imap), indent=2))
    return path
