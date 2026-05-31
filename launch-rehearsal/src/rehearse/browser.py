"""Playwright browser execution — product-agnostic step runner."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Locator, Page, Response, sync_playwright

from rehearse.dsl import AuthConfig, RunConfig, Step
from rehearse.errors import ConfigError, PreflightError, classify_step_error
from rehearse.evidence import StepSnapshot
from rehearse.viewports import VIEWPORT_PROFILES, normalize_viewports
from rehearse.web_vitals import collect_web_vitals

NETWORK_LOG_MAX = 500

ERROR_PHRASES = (
    "error",
    "failed",
    "something went wrong",
    "not found",
    "unauthorized",
    "forbidden",
    "try again",
)


def _safe_filename(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-")[:80] or "step"


def capture_focus_region(
    page: Page,
    locator: Locator,
    *,
    label: str | None = None,
) -> dict[str, Any] | None:
    """Viewport-relative box for UI overlays on full-page screenshots."""
    try:
        box = locator.first.bounding_box()
        if not box or box.get("width", 0) < 2 or box.get("height", 0) < 2:
            return None
        vp = page.viewport_size or {"width": 1280, "height": 900}
        text_label = (label or "").strip()[:120] or "focus"
        return {
            "x": round(float(box["x"]), 1),
            "y": round(float(box["y"]), 1),
            "width": round(float(box["width"]), 1),
            "height": round(float(box["height"]), 1),
            "viewportWidth": int(vp["width"]),
            "viewportHeight": int(vp["height"]),
            "label": text_label,
        }
    except Exception:
        return None


def _body_excerpt(page: Page, limit: int = 2000) -> str:
    try:
        text = page.locator("body").inner_text(timeout=5000)
        return " ".join(text.split())[:limit]
    except Exception:
        return ""


def _collect_a11y_metrics(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const buttons = [...document.querySelectorAll('button')];
          const unlabeledButtons = buttons.filter(b => {
            const label = (b.getAttribute('aria-label') || b.innerText || '').trim();
            return label.length === 0;
          }).length;
          const links = document.querySelectorAll('a[href]').length;
          const headings = document.querySelectorAll('h1,h2,h3').length;
          const inputs = [...document.querySelectorAll('input,textarea,select')];
          const labeledInputs = inputs.filter(el => {
            const id = el.id;
            if (id && document.querySelector(`label[for="${id}"]`)) return true;
            if (el.getAttribute('aria-label')) return true;
            if (el.getAttribute('placeholder')) return true;
            return false;
          }).length;
          return {
            unlabeledButtons,
            linkCount: links,
            headingCount: headings,
            inputCount: inputs.length,
            labeledInputCount: labeledInputs,
          };
        }"""
    )


_JOB_STATUS_FAILED = re.compile(r"job_[a-f0-9]+\s+\w+\s+failed", re.I)

# Substrings where "error" is product/monitoring vocabulary, not a failure surface
_ERROR_BENIGN_CONTEXT = (
    "error rate",
    "job queue",
    "job_",
    "resolved since",
    "new issues in",
    "changed steps",
    "top blocker",
    "readiness band",
    "p0 ·",
    "p1 ·",
    "p2 ·",
    "issues opened",
    "issues resolved",
)


def _find_error_phrases(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []

    if "failed" in lower:
        job_failed = len(_JOB_STATUS_FAILED.findall(lower))
        if lower.count("failed") > job_failed:
            found.append("failed")

    if "error" in lower and not any(ctx in lower for ctx in _ERROR_BENIGN_CONTEXT):
        found.append("error")

    for phrase in ERROR_PHRASES:
        if phrase in ("error", "failed"):
            continue
        if phrase in lower:
            found.append(phrase)
    return found


def _absolute_url(base: str, href: str) -> str:
    if href.startswith("http"):
        return href
    base = base.rstrip("/")
    if href.startswith("/"):
        return f"{base}{href}"
    return f"{base}/{href}"


def _perform_open_link(
    page: Page,
    step: Step,
    *,
    base_url: str,
    timeout: int,
    fallback_path: str = "/database/profile",
) -> str | None:
    """Click a link; if navigation fails, follow href or first matching profile link."""
    note: str | None = None
    loc = None
    if step.intent:
        link_loc = page.get_by_role("link", name=step.intent, exact=False)
        if link_loc.count() > 0:
            loc = link_loc.first
    if loc is None:
        loc = _resolve_locator(page, step).first

    url_before = page.url
    context = page.context
    try:
        with context.expect_page(timeout=min(timeout, 8000)) as popup:
            loc.click(timeout=timeout, no_wait_after=True)
        new_tab = popup.value
        new_tab.wait_for_load_state("domcontentloaded", timeout=timeout)
        if fallback_path in new_tab.url:
            page.goto(new_tab.url, wait_until="domcontentloaded", timeout=timeout)
            note = "open_link: followed new-tab navigation"
        new_tab.close()
    except Exception:
        try:
            with page.expect_navigation(timeout=timeout, wait_until="domcontentloaded"):
                loc.click(timeout=timeout)
        except Exception:
            loc.click(timeout=timeout, no_wait_after=True)
            page.wait_for_timeout(800)

    if fallback_path not in (page.url or ""):
        href = loc.get_attribute("href")
        if href and fallback_path in href:
            page.goto(_absolute_url(base_url, href), wait_until="domcontentloaded", timeout=timeout)
            note = "open_link: navigated via element href"
        else:
            profile_loc = page.locator(f'a[href*="{fallback_path}"]').first
            if profile_loc.count() > 0:
                alt_href = profile_loc.get_attribute("href")
                if alt_href:
                    page.goto(
                        _absolute_url(base_url, alt_href),
                        wait_until="domcontentloaded",
                        timeout=timeout,
                    )
                    note = "open_link: navigated via first profile link on page"
            elif url_before == page.url:
                note = "open_link: click did not change URL and no profile href found"

    try:
        page.wait_for_load_state("networkidle", timeout=min(timeout, 12000))
    except Exception:
        pass
    return note


def _compact_aria_tree(page: Page, *, max_nodes: int = 120) -> dict[str, Any]:
    """Accessibility tree for evidence (MCP a11y snapshot equivalent)."""
    try:
        tree = page.accessibility.snapshot()
        if not tree:
            return {"role": "document", "children": []}

        def trim(node: dict[str, Any], budget: list[int]) -> dict[str, Any]:
            if budget[0] <= 0:
                return {"role": node.get("role", "?"), "truncated": True}
            budget[0] -= 1
            out: dict[str, Any] = {"role": node.get("role", "?")}
            if node.get("name"):
                out["name"] = str(node["name"])[:120]
            children = node.get("children") or []
            if children and budget[0] > 0:
                out["children"] = [trim(c, budget) for c in children[:12]]
            return out

        return trim(tree, [max_nodes])
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _save_aria_artifact(artifacts_dir: Path, step_id: str, tree: dict[str, Any]) -> str:
    path = artifacts_dir / f"{_safe_filename(step_id)}-aria.json"
    path.write_text(json.dumps(tree, indent=2)[:80000])
    return str(path)


def _resolve_locator(page: Page, step: Step) -> tuple[Locator, str]:
    """Resolve element; return locator and human-readable resolution note."""
    if step.selector:
        return page.locator(step.selector).first, f"selector={step.selector}"

    if step.intent:
        strategies: list[tuple[str, Any]] = [
            ("getByRole(button)", lambda: page.get_by_role("button", name=step.intent, exact=False)),
            ("getByRole(link)", lambda: page.get_by_role("link", name=step.intent, exact=False)),
            ("getByLabel", lambda: page.get_by_label(step.intent, exact=False)),
            ("getByPlaceholder", lambda: page.get_by_placeholder(step.intent, exact=False)),
            ("getByRole(combobox)", lambda: page.get_by_role("combobox", name=step.intent, exact=False)),
            ("getByText", lambda: page.get_by_text(step.intent, exact=False)),
        ]
        for label, factory in strategies:
            loc = factory()
            if loc.count() > 0:
                return loc.first, f"resolved={label}({step.intent!r})"
        return page.get_by_text(step.intent, exact=False).first, f"fallback=getByText({step.intent!r})"

    raise PreflightError(f"Step requires selector or intent: {step.action}")


class BrowserSession:
    def __init__(self, config: RunConfig, artifacts_dir: Path) -> None:
        self.config = config
        self.artifacts_dir = artifacts_dir
        self.console_errors: list[str] = []
        self.console_warnings: list[str] = []
        self.network_failures: list[str] = []
        self.network_log: list[dict[str, Any]] = []
        self._pw = None
        self._browser = None
        self._context = None
        self.page: Page | None = None
        self._viewport = "desktop"

    def __enter__(self) -> BrowserSession:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        first = normalize_viewports(self.config.viewports)[0]
        self._context = self._browser.new_context(viewport=VIEWPORT_PROFILES[first])
        self.page = self._context.new_page()
        self._viewport = first
        self.page.on("console", self._on_console)
        self.page.on("response", self._on_response)
        return self

    def set_viewport(self, profile: str) -> None:
        key = profile.strip().lower()
        if key not in VIEWPORT_PROFILES:
            key = "desktop"
        self._viewport = key
        page = self.page
        assert page is not None
        page.set_viewport_size(VIEWPORT_PROFILES[key])

    def __exit__(self, *args: object) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def _on_console(self, msg: Any) -> None:
        text = (msg.text or "")[:300]
        if msg.type == "error":
            self.console_errors.append(text)
        elif msg.type == "warning":
            self.console_warnings.append(text)

    def _on_response(self, response: Response) -> None:
        try:
            req = response.request
            if len(self.network_log) < NETWORK_LOG_MAX:
                self.network_log.append(
                    {
                        "url": response.url[:500],
                        "method": req.method,
                        "status": response.status,
                        "resourceType": req.resource_type,
                    }
                )
        except Exception:
            pass
        if response.status >= 400:
            self.network_failures.append(f"{response.status} {response.url}"[:300])

    def reset_run_errors(self) -> None:
        self.console_errors = []
        self.console_warnings = []
        self.network_failures = []

    def flush_network_log(self) -> str | None:
        if not self.network_log:
            return None
        path = self.artifacts_dir / "network-log.json"
        path.write_text(json.dumps(self.network_log, indent=2)[:2_000_000])
        return str(path)

    def _auth_session_ok(self) -> bool:
        page = self.page
        assert page is not None
        url = page.url.lower()
        if not url or url.startswith("about:") or url == "data:":
            return False
        body = _body_excerpt(page).lower()
        if "logout" in body or "logged in as" in body:
            return True
        path = urlparse(page.url).path.rstrip("/").lower()
        return path not in ("/login", "/signin", "/signup")

    def _fill_auth_input(self, auth: AuthConfig, field: str, value: str, timeout_ms: int) -> None:
        page = self.page
        assert page is not None
        if field == "email":
            locators = [
                page.get_by_label(auth.email_label, exact=False),
                page.get_by_placeholder("email", exact=False),
                page.locator('input[type="email"]'),
                page.locator('input[name="email"]'),
                page.locator('input[autocomplete="email"]'),
            ]
        else:
            locators = [
                page.get_by_label(auth.password_label, exact=False),
                page.get_by_placeholder("password", exact=False),
                page.locator('input[type="password"]'),
                page.locator('input[name="password"]'),
            ]
        last_exc: Exception | None = None
        for loc in locators:
            try:
                target = loc.first
                target.wait_for(state="visible", timeout=timeout_ms // len(locators))
                target.fill(value, timeout=5000)
                return
            except Exception as exc:
                last_exc = exc
        raise PreflightError(f"Could not fill auth {field}: {last_exc}")

    def perform_auth(self, auth: AuthConfig) -> str:
        import os

        email = os.environ.get(auth.email_env)
        password = os.environ.get(auth.password_env)
        if not email or not password:
            return "skipped_missing_credentials"

        page = self.page
        assert page is not None
        login_url = self.config.login_url()
        assert login_url

        if self._auth_session_ok():
            return "success_already_authenticated"

        timeout = self.config.budgets.step_timeout_ms
        last_outcome = "failed_still_on_login"

        for attempt in range(3):
            try:
                self.reset_run_errors()
                page.goto(login_url, wait_until="domcontentloaded", timeout=timeout)
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                page.wait_for_timeout(500)

                self._fill_auth_input(auth, "email", email, timeout_ms=12000)
                self._fill_auth_input(auth, "password", password, timeout_ms=12000)

                submit = page.get_by_role("button", name=auth.submit_label, exact=False)
                if submit.count() == 0:
                    submit = page.get_by_role("button", name="Login", exact=False)
                submit.first.click(timeout=10000)

                try:
                    page.wait_for_url(
                        lambda url: "/login" not in url.lower() and "/signin" not in url.lower(),
                        timeout=20000,
                    )
                except Exception:
                    pass
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                page.wait_for_timeout(1000)

                if self._auth_session_ok():
                    return "success"
                last_outcome = "failed_still_on_login"
            except Exception as exc:
                last_outcome = f"failed_attempt_{attempt + 1}"
                if attempt < 2:
                    page.wait_for_timeout(1500)
                    continue
                return last_outcome

        return last_outcome

    def execute_step(
        self,
        step: Step,
        *,
        step_id: str,
        journey_id: str,
        journey_name: str,
        persona_id: str,
        viewport: str | None = None,
    ) -> StepSnapshot:
        page = self.page
        assert page is not None
        timeout = self.config.budgets.step_timeout_ms
        self.reset_run_errors()
        started = time.perf_counter()
        vp = viewport or self._viewport
        snap = StepSnapshot(
            step_id=step_id,
            journey_id=journey_id,
            journey_name=journey_name,
            persona_id=persona_id,
            action=step.action,
            requested_url=step.url,
            viewport=vp,
        )
        response: Response | None = None
        resolution_note: str | None = None
        focus_locator: Locator | None = None

        try:
            if step.action == "navigate":
                if not step.url:
                    raise PreflightError("navigate step requires url")
                response = page.goto(step.url, wait_until="domcontentloaded", timeout=timeout)
                page.wait_for_load_state("networkidle", timeout=min(timeout, 15000))
            elif step.action == "wait":
                ms = int(step.value or step.url or "1000")
                page.wait_for_timeout(ms)
            elif step.action == "fill":
                value = step.resolve_value() if step.value else ""
                loc, resolution_note = _resolve_locator(page, step)
                focus_locator = loc
                loc.fill(value or "", timeout=timeout)
            elif step.action == "click":
                loc, resolution_note = _resolve_locator(page, step)
                focus_locator = loc
                if loc.is_disabled(timeout=3000):
                    snap.outcome = "partial"
                    snap.note = "Target control is disabled"
                else:
                    loc.click(timeout=timeout)
                    page.wait_for_load_state("domcontentloaded", timeout=timeout)
            elif step.action == "hover":
                loc, resolution_note = _resolve_locator(page, step)
                focus_locator = loc
                loc.hover(timeout=timeout)
            elif step.action == "scroll":
                if step.intent or step.selector:
                    loc, resolution_note = _resolve_locator(page, step)
                    focus_locator = loc
                    loc.scroll_into_view_if_needed(timeout=timeout)
                else:
                    page.mouse.wheel(0, int(step.value or "600"))
            elif step.action == "select":
                loc, resolution_note = _resolve_locator(page, step)
                focus_locator = loc
                loc.select_option(step.value or "", timeout=timeout)
            elif step.action == "press":
                key = (step.value or "Enter").strip()
                if step.selector or step.intent:
                    loc, resolution_note = _resolve_locator(page, step)
                    focus_locator = loc
                    loc.press(key, timeout=timeout)
                else:
                    page.keyboard.press(key)
            elif step.action == "open_link":
                fallback = step.value or "/database/profile"
                link_note = _perform_open_link(
                    page,
                    step,
                    base_url=self.config.target_url,
                    timeout=timeout,
                    fallback_path=fallback,
                )
                if link_note:
                    snap.note = link_note
                if fallback not in (page.url or ""):
                    snap.outcome = "fail"
                    snap.error_type = "BrowserNavigationFailed"
                    if not snap.note:
                        snap.note = f"open_link failed: expected '{fallback}' in URL"
            elif step.action == "dismiss":
                dismissed = False
                for label in (
                    "Accept all",
                    "Accept",
                    "Allow all",
                    "Close",
                    "Dismiss",
                    "Got it",
                    "OK",
                    "Agree",
                ):
                    try:
                        btn = page.get_by_role("button", name=label, exact=False)
                        if btn.count() > 0:
                            btn.first.click(timeout=min(timeout, 4000))
                            snap.note = f"dismiss: {label}"
                            dismissed = True
                            break
                    except Exception:
                        continue
                if not dismissed and (step.intent or step.selector):
                    loc, resolution_note = _resolve_locator(page, step)
                    focus_locator = loc
                    loc.click(timeout=timeout)
                    snap.note = resolution_note or "dismiss: intent click"
                elif not dismissed:
                    snap.outcome = "partial"
                    snap.note = "dismiss: no banner matched"
            elif step.action == "explore":
                from rehearse.explore import run_explore_loop

                max_rounds = int(step.value or self.config.budgets.explore_max_rounds)
                run_explore_loop(self, step, snap, max_rounds=max_rounds)
            elif step.action == "assert_url_contains":
                needle = step.value or step.url or ""
                if needle not in page.url:
                    snap.outcome = "fail"
                    snap.error_type = "StepAssertionFailed"
                    snap.note = f"URL assertion failed: expected '{needle}' in {page.url}"
            else:
                raise PreflightError(f"Unsupported action: {step.action}")

            snap.final_url = page.url
            snap.page_title = page.title()
            snap.http_status = response.status if response else None
            snap.body_text_excerpt = _body_excerpt(page)
            metrics = _collect_a11y_metrics(page)
            snap.unlabeled_button_count = int(metrics.get("unlabeledButtons", 0))
            snap.link_count = int(metrics.get("linkCount", 0))
            snap.heading_count = int(metrics.get("headingCount", 0))
            snap.input_count = int(metrics.get("inputCount", 0))
            snap.labeled_input_count = int(metrics.get("labeledInputCount", 0))
            snap.error_phrases_found = _find_error_phrases(snap.body_text_excerpt)
            snap.console_errors = list(self.console_errors)
            snap.console_warnings = list(self.console_warnings)
            snap.network_failures = list(self.network_failures)
            if step.action == "navigate":
                snap.web_vitals = collect_web_vitals(page)
            if resolution_note:
                snap.resolved_selector = resolution_note
                snap.note = resolution_note if not snap.note else f"{snap.note}; {resolution_note}"

            if focus_locator is not None:
                snap.focus_region = capture_focus_region(
                    page,
                    focus_locator,
                    label=step.intent or step.selector or step.action,
                )

            if step.action in ("navigate", "click", "fill", "select"):
                aria_path = _save_aria_artifact(
                    self.artifacts_dir,
                    step_id,
                    _compact_aria_tree(page),
                )
                snap.artifact_paths.append(aria_path)

            shot = self.artifacts_dir / f"{_safe_filename(step_id)}.png"
            page.screenshot(path=str(shot), full_page=True)
            snap.artifact_paths.append(str(shot))

            text_path = self.artifacts_dir / f"{_safe_filename(step_id)}.txt"
            text_path.write_text(snap.body_text_excerpt)
            snap.artifact_paths.append(str(text_path))

            if snap.outcome != "fail":
                snap.outcome = _grade_step(snap, step)
        except Exception as exc:
            snap.outcome = "fail"
            snap.error_type = classify_step_error(exc)
            snap.note = str(exc)[:500]
            try:
                shot = self.artifacts_dir / f"{_safe_filename(step_id)}-error.png"
                page.screenshot(path=str(shot), full_page=True)
                snap.artifact_paths.append(str(shot))
            except Exception:
                pass

        snap.duration_ms = int((time.perf_counter() - started) * 1000)
        return snap


def _grade_step(snap: StepSnapshot, step: Step) -> str:
    if snap.http_status and snap.http_status >= 400:
        return "fail"
    if snap.body_text_excerpt.strip().lower() in ("initializing...", "loading..."):
        return "partial"
    if len(snap.body_text_excerpt.strip()) < 40:
        return "partial"
    if step.action == "navigate" and snap.requested_url:
        req_path = urlparse(snap.requested_url).path.rstrip("/") or "/"
        final_path = urlparse(snap.final_url or "").path.rstrip("/") or "/"
        if req_path not in ("/login", "/signin", "/signup") and final_path in ("/login", "/signin"):
            return "partial"
    if snap.network_failures and any("401" in n or "403" in n for n in snap.network_failures):
        return "partial"
    return "pass"
