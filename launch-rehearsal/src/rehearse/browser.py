"""Playwright browser execution — product-agnostic step runner."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Page, Response, sync_playwright

from rehearse.dsl import AuthConfig, RunConfig, Step
from rehearse.errors import BrowserStepTimeout, ConfigError, PreflightError
from rehearse.evidence import StepSnapshot

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


def _find_error_phrases(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for phrase in ERROR_PHRASES:
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


def _resolve_locator(page: Page, step: Step):
    if step.selector:
        return page.locator(step.selector)
    if step.intent:
        for factory in (
            lambda: page.get_by_role("button", name=step.intent, exact=False),
            lambda: page.get_by_role("link", name=step.intent, exact=False),
            lambda: page.get_by_label(step.intent, exact=False),
            lambda: page.get_by_placeholder(step.intent, exact=False),
            lambda: page.get_by_text(step.intent, exact=False),
        ):
            loc = factory()
            if loc.count() > 0:
                return loc.first
        return page.get_by_text(step.intent, exact=False).first
    raise PreflightError(f"Step requires selector or intent: {step.action}")


class BrowserSession:
    def __init__(self, config: RunConfig, artifacts_dir: Path) -> None:
        self.config = config
        self.artifacts_dir = artifacts_dir
        self.console_errors: list[str] = []
        self.network_failures: list[str] = []
        self._pw = None
        self._browser = None
        self._context = None
        self.page: Page | None = None

    def __enter__(self) -> BrowserSession:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._context = self._browser.new_context(viewport={"width": 1280, "height": 900})
        self.page = self._context.new_page()
        self.page.on("console", self._on_console)
        self.page.on("response", self._on_response)
        return self

    def __exit__(self, *args: object) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def _on_console(self, msg: Any) -> None:
        if msg.type == "error":
            self.console_errors.append(msg.text[:300])

    def _on_response(self, response: Response) -> None:
        if response.status >= 400:
            self.network_failures.append(f"{response.status} {response.url}"[:300])

    def reset_run_errors(self) -> None:
        self.console_errors = []
        self.network_failures = []

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
    ) -> StepSnapshot:
        page = self.page
        assert page is not None
        timeout = self.config.budgets.step_timeout_ms
        self.reset_run_errors()
        started = time.perf_counter()
        snap = StepSnapshot(
            step_id=step_id,
            journey_id=journey_id,
            journey_name=journey_name,
            persona_id=persona_id,
            action=step.action,
            requested_url=step.url,
        )
        response: Response | None = None

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
                loc = _resolve_locator(page, step)
                loc.fill(value or "", timeout=timeout)
            elif step.action == "click":
                loc = _resolve_locator(page, step)
                target = loc.first
                if target.is_disabled(timeout=3000):
                    snap.outcome = "partial"
                    snap.note = "Target control is disabled"
                else:
                    target.click(timeout=timeout)
                    page.wait_for_load_state("domcontentloaded", timeout=timeout)
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
                    if not snap.note:
                        snap.note = f"open_link failed: expected '{fallback}' in URL"
            elif step.action == "assert_url_contains":
                needle = step.value or step.url or ""
                if needle not in page.url:
                    snap.outcome = "fail"
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
            snap.network_failures = list(self.network_failures)

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
            snap.note = str(exc)[:500]
            try:
                shot = self.artifacts_dir / f"{_safe_filename(step_id)}-error.png"
                page.screenshot(path=str(shot), full_page=True)
                snap.artifact_paths.append(str(shot))
            except Exception:
                pass
            if "Timeout" in snap.note:
                raise BrowserStepTimeout(snap.note) from exc

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
