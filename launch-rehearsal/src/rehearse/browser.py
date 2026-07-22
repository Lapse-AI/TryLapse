"""Playwright browser execution — product-agnostic step runner."""

from __future__ import annotations

import hashlib
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


def _launch_browser(pw: Any, engine: str, *, headless: bool = True) -> Any:
    """Launch the configured Playwright browser engine.

    Centralizes engine selection so "chromium-only" isn't hardcoded at every
    call site — journey_agent.py's parallel worker uses this too.
    """
    browser_type = getattr(pw, engine, None)
    if browser_type is None:
        raise ConfigError(f"Unknown browser engine: {engine!r}")
    return browser_type.launch(headless=headless)

# ── Flake-rate mitigations ────────────────────────────────────────────────────
# Injected as CSS on every page after navigation to eliminate timing-based
# flakes caused by click targets moving during CSS transitions.
_ANIMATION_FREEZE_CSS = (
    "*, *::before, *::after {"
    "  animation-duration: 0s !important;"
    "  transition-duration: 0s !important;"
    "  animation-delay: 0s !important;"
    "  scroll-behavior: auto !important;"
    "}"
)

# Pure analytics / telemetry origins that have no functional role in the app
# under test. Blocking these removes a major source of non-deterministic timing.
# Intentionally excludes: reCAPTCHA, Stripe.js, Auth0, LaunchDarkly — things
# that can affect app behaviour and must not be silently dropped.
_ANALYTICS_BLOCK_PATTERNS = [
    "**/analytics.js",
    "**/analytics.min.js",
    "**segment.io/**",
    "**segment.com/**",
    "**intercom.io/**",
    "**intercomcdn.com/**",
    "**hotjar.com/**",
    "**fullstory.com/**",
    "**googletagmanager.com/**",
    "**google-analytics.com/**",
    "**mixpanel.com/**",
    "**amplitude.com/**",
    "**heap.io/**",
    "**clarity.ms/**",
    "**sentry.io/**",
    "**datadoghq.com/**",
    "**logrocket.io/**",
    "**logrocket.com/**",
]


def _abort_route(route: Any) -> None:
    try:
        route.abort()
    except Exception:
        pass


def _inject_animation_freeze(page: Page) -> None:
    """Inject CSS that disables all animations and transitions on the current page.

    Called after every navigate to remove the primary source of click-timing
    flakes. Safe to call multiple times — CSS rules are idempotent.
    """
    try:
        page.add_style_tag(content=_ANIMATION_FREEZE_CSS)
    except Exception:
        pass  # never block execution; this is a reliability aid, not a feature


def _block_analytics_routes(context: Any) -> None:
    """Register abort handlers for known analytics/telemetry origins.

    Must be called once after context creation, before any page navigation.
    Handlers persist for the lifetime of the context.
    """
    for pattern in _ANALYTICS_BLOCK_PATTERNS:
        try:
            context.route(pattern, _abort_route)
        except Exception:
            pass


_ANIMATION_FREEZE_INIT_SCRIPT = (
    "document.addEventListener('DOMContentLoaded', function() {"
    "  var s = document.createElement('style');"
    "  s.id = '__trylapse_freeze';"
    "  s.textContent = '"
    + _ANIMATION_FREEZE_CSS.replace("'", "\\'")
    + "';"
    "  (document.head || document.documentElement).appendChild(s);"
    "}, {once: false, capture: true});"
)


def setup_page_for_run(page: Any) -> None:
    """Apply all per-page flake mitigations to a freshly created Playwright page.

    Call once after page creation — before any navigation. Idempotent (safe to
    call on an already-configured page; duplicate style tags are benign).
    """
    try:
        page.add_init_script(script=_ANIMATION_FREEZE_INIT_SCRIPT)
    except Exception:
        pass


# Consent banner dismiss selectors — ordered from most specific to most generic
_CONSENT_DISMISS_SELECTORS = [
    "button[id*='accept' i]",
    "button[class*='accept' i]",
    "button[data-testid*='accept' i]",
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Accept cookies')",
    "button:has-text('I accept')",
    "button:has-text('Allow all')",
    "button:has-text('OK')",
    "button:has-text('Got it')",
    "button:has-text('Agree')",
    "[aria-label*='Accept' i][role='button']",
    "[aria-label*='Close cookie' i]",
]

# JS snippet to detect a blocking consent overlay (heuristic: fixed/sticky element
# covering ≥25% of viewport height, containing consent keywords).
_CONSENT_DETECT_SCRIPT = """
() => {
  const keywords = ['cookie', 'consent', 'gdpr', 'privacy policy', 'ccpa', 'we use cookies'];
  const els = Array.from(document.querySelectorAll('*'));
  for (const el of els) {
    const style = window.getComputedStyle(el);
    if (style.position !== 'fixed' && style.position !== 'sticky') continue;
    const rect = el.getBoundingClientRect();
    const vpH = window.innerHeight || 600;
    if (rect.height < vpH * 0.15) continue;
    const text = (el.innerText || el.textContent || '').toLowerCase();
    if (keywords.some(k => text.includes(k))) return true;
  }
  return false;
}
"""


def check_and_dismiss_consent_banner(page: Any) -> str:
    """Detect and attempt to dismiss a GDPR/CCPA consent banner.

    Returns:
        "none"      — no consent banner detected
        "dismissed" — banner detected and successfully dismissed
        "blocked"   — banner detected, all dismiss attempts failed
    """
    try:
        has_banner = page.evaluate(_CONSENT_DETECT_SCRIPT)
    except Exception:
        return "none"

    if not has_banner:
        return "none"

    for sel in _CONSENT_DISMISS_SELECTORS:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click(timeout=2000)
                page.wait_for_timeout(500)
                still_visible = page.evaluate(_CONSENT_DETECT_SCRIPT)
                if not still_visible:
                    return "dismissed"
        except Exception:
            continue

    return "blocked"
# ─────────────────────────────────────────────────────────────────────────────

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

          // Images missing meaningful alt text (empty alt="" is intentional; absence is a gap)
          const imgs = [...document.querySelectorAll('img')];
          const missingAlt = imgs.filter(img => {
            const alt = img.getAttribute('alt');
            return alt === null;  // no alt attribute at all (not even empty)
          }).length;

          // Low-opacity text estimate — catches text faded below readable threshold.
          // We sample visible text nodes and flag those whose nearest element has
          // computed opacity < 0.45 or color with lightness > 0.85 on white bg.
          let lowContrastEstimate = 0;
          try {
            const textEls = [...document.querySelectorAll('p,span,label,li,td,th,a')]
              .filter(el => el.offsetParent !== null && (el.innerText || '').trim().length > 0)
              .slice(0, 60);
            for (const el of textEls) {
              const style = window.getComputedStyle(el);
              const opacity = parseFloat(style.opacity || '1');
              if (opacity < 0.45) { lowContrastEstimate++; continue; }
              // Parse color lightness via RGB
              const color = style.color || '';
              const m = color.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
              if (m) {
                const [r, g, b] = [+m[1]/255, +m[2]/255, +m[3]/255];
                const lightness = (Math.max(r,g,b) + Math.min(r,g,b)) / 2;
                if (lightness > 0.82) lowContrastEstimate++;
              }
            }
          } catch(e) {}

          return {
            unlabeledButtons,
            linkCount: links,
            headingCount: headings,
            inputCount: inputs.length,
            labeledInputCount: labeledInputs,
            missingAltCount: missingAlt,
            lowContrastEstimate,
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


def _dom_fingerprint(page: Page) -> str | None:
    """Lightweight DOM fingerprint — 12-char hex hash of element counts + title.

    Used by C4 regression check: if the fingerprint is unchanged between two
    consecutive interaction steps in the same journey, the action likely had no
    visible DOM effect, which is a UX signal.
    """
    try:
        counts = page.evaluate("""() => {
            const tags = ['a','button','input','select','form','h1','h2','h3','p','li','img','svg'];
            return tags.map(t => document.querySelectorAll(t).length).join(',')
                + '|' + (document.title || '')
                + '|' + document.querySelectorAll('[role]').length;
        }""")
        return hashlib.md5(counts.encode()).hexdigest()[:12]  # noqa: S324
    except Exception:
        return None


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


def _origin(url: str) -> str:
    """Return scheme + host only: https://example.com"""
    parts = url.split("//", 1)
    if len(parts) < 2:
        return url.rstrip("/")
    return parts[0] + "//" + parts[1].split("/")[0]


def _absolute_url(base: str, href: str) -> str:
    """Resolve href against the ORIGIN of base (not the full path)."""
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        # Always resolve root-relative paths from the origin
        return _origin(base) + href
    # Relative path — resolve from base directory (strip last segment)
    base_dir = base.rstrip("/").rsplit("/", 1)[0] if "/" in base.split("//", 1)[-1] else base.rstrip("/")
    return f"{base_dir}/{href}"


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
            try:
                page.wait_for_load_state("domcontentloaded", timeout=min(timeout, 3000))
            except Exception:
                pass

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


def _collect_resource_timing(page: Page, *, top_n: int = 10) -> list[dict[str, Any]]:
    """Return the top-N slowest resources from the Navigation Timing API."""
    try:
        entries: list[dict] = page.evaluate(
            "() => performance.getEntriesByType('resource').map(e => ({"
            "  name: e.name.split('?')[0].slice(-80),"
            "  type: e.initiatorType,"
            "  durationMs: Math.round(e.duration),"
            "  transferSize: e.transferSize || 0"
            "}))"
        )
        return sorted(entries, key=lambda e: -e.get("durationMs", 0))[:top_n]
    except Exception:
        return []


def _capture_storage_keys(page: Page) -> list[str]:
    """Return localStorage + sessionStorage keys, auth-pattern keys first to survive the cap."""
    try:
        keys: list[str] = page.evaluate(
            "() => {"
            "  const AUTH = /token|session|auth|jwt|user_id|access|refresh|credential|bearer|sid/i;"
            "  const lsAuth = Object.keys(localStorage).filter(k => AUTH.test(k)).map(k => 'ls:' + k);"
            "  const lsRest = Object.keys(localStorage).filter(k => !AUTH.test(k)).map(k => 'ls:' + k);"
            "  const ss = Object.keys(sessionStorage).map(k => 'ss:' + k);"
            "  return [...lsAuth, ...lsRest, ...ss];"
            "}"
        )
        return keys[:100]  # cap to avoid huge evidence blobs; auth keys are always first
    except Exception:
        return []


def _capture_seo_meta(page: Page) -> dict[str, Any]:
    """Capture SEO signals after a navigate step — meta description, canonical, robots."""
    try:
        return page.evaluate(
            "() => ({"
            "  metaDescription: document.querySelector('meta[name=\"description\"]')?.content || null,"
            "  canonical: document.querySelector('link[rel=\"canonical\"]')?.href || null,"
            "  robots: document.querySelector('meta[name=\"robots\"]')?.content || null,"
            "  h1Count: document.querySelectorAll('h1').length,"
            "  h1Text: (document.querySelector('h1')?.textContent || '').trim().slice(0, 120) || null,"
            "  hasOgTitle: !!document.querySelector('meta[property=\"og:title\"]'),"
            "})"
        )
    except Exception:
        return {}


def _save_aria_artifact(artifacts_dir: Path, step_id: str, tree: dict[str, Any]) -> str:
    path = artifacts_dir / f"{_safe_filename(step_id)}-aria.json"
    path.write_text(json.dumps(tree, indent=2)[:80000])
    return str(path)


_ARIA_INTERACTIVE_ROLES = {"button", "link", "textbox", "combobox", "checkbox", "radio", "menuitem"}


def _find_aria_node_by_name(tree: dict[str, Any] | None, intent: str) -> str | None:
    """Walk the ARIA snapshot tree to find a node whose name fuzzy-matches intent.

    Returns the node's role string, or None if not found.
    Tree-first lookup lets us skip the 6-role sequential timeout scan.
    """
    if not tree or not intent:
        return None
    intent_lower = intent.lower()
    role = (tree.get("role") or "").lower()
    name = (tree.get("name") or "").lower()
    if role in _ARIA_INTERACTIVE_ROLES and (intent_lower in name or name in intent_lower):
        return role
    for child in tree.get("children") or []:
        found = _find_aria_node_by_name(child, intent)
        if found:
            return found
    return None


def _resolve_locator_by_aria(page: Page, step: Step, timeout: int = 30000) -> tuple[Locator, str]:
    """Resolve element via ARIA role/label for screen-reader persona.

    Uses ARIA snapshot tree to pick the exact role first (avoids 6-role sequential scan).
    Fallback chain: get_by_label → tree-guided get_by_role → get_by_text → standard locator.
    """
    intent = step.intent or step.selector or ""
    tried: list[str] = []

    # 1. Try label — covers <label for=...> and aria-label
    if intent:
        try:
            loc = page.get_by_label(intent, exact=False).first
            loc.wait_for(state="visible", timeout=min(timeout, 5000))
            return loc, f"aria:label={intent!r}"
        except Exception as e:
            tried.append(f"label({e!s:.40})")

    # 2. Use ARIA snapshot tree to identify the correct role, then try only that role.
    #    Falls back to full sequential scan only when tree lookup fails.
    tree_role: str | None = None
    try:
        tree = page.accessibility.snapshot()
        tree_role = _find_aria_node_by_name(tree, intent)
    except Exception:
        pass

    roles_to_try = [tree_role] if tree_role else list(_ARIA_INTERACTIVE_ROLES)
    for role in roles_to_try:
        if intent:
            try:
                loc = page.get_by_role(role, name=intent).first  # type: ignore[arg-type]
                loc.wait_for(state="visible", timeout=min(timeout, 3000))
                suffix = "" if tree_role else " [tree-miss: sequential scan]"
                return loc, f"aria:role={role},name={intent!r}{suffix}"
            except Exception as e:
                tried.append(f"role:{role}({e!s:.30})")

    # 3. Try visible text match
    if intent:
        try:
            loc = page.get_by_text(intent, exact=False).first
            loc.wait_for(state="visible", timeout=min(timeout, 3000))
            return loc, f"aria:text={intent!r} [no accessible name — unlabelled]"
        except Exception as e:
            tried.append(f"text({e!s:.40})")

    # 4. Fallback — standard selector path; note the a11y gap
    loc, note = _resolve_locator(page, step)
    return loc, f"[screen-reader-fallback: ARIA resolution failed ({'; '.join(tried[:3])})] {note}"


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


# ── Behavioral-profile-driven execution ───────────────────────────────────────
# tech_literacy / patience / trust_level previously only biased LLM severity
# grading after the fact. These three functions make the same traits change
# what actually happens in the browser, so a "low patience" persona produces a
# genuinely different StepSnapshot (timeout, abandon) rather than the same
# snapshot with a harsher label glued on afterward.

_LOW_PATIENCE_TIMEOUT_FACTOR = 0.6
_HIGH_PATIENCE_TIMEOUT_FACTOR = 1.3

_SENSITIVE_ACTION_KEYWORDS = (
    "pay", "purchase", "buy", "subscribe", "checkout", "delete", "remove",
    "confirm", "submit", "upgrade", "billing", "card", "cancel",
)


def _resolve_persona(config, persona_id: str):
    return next((p for p in config.personas if p.id == persona_id), None)


def _behavioral_timeout(base_timeout_ms: int, persona) -> int:
    """Scale the step timeout by patience.

    Low-patience personas give up sooner on a slow step — the timeout fires
    earlier, producing a real "abandoned" outcome instead of a relabeled pass.
    High-patience personas tolerate more latency before failing.
    """
    patience = getattr(persona, "patience", "medium") if persona else "medium"
    if patience == "low":
        return int(base_timeout_ms * _LOW_PATIENCE_TIMEOUT_FACTOR)
    if patience == "high":
        return int(base_timeout_ms * _HIGH_PATIENCE_TIMEOUT_FACTOR)
    return base_timeout_ms


def _behavioral_pre_action_pause_ms(persona, step: Step) -> int:
    """Hesitation before a sensitive click/fill.

    Skeptical personas pause to re-read pricing, payment, or destructive
    actions before committing; trusting personas act immediately.
    """
    if persona is None:
        return 0
    if step.action not in ("click", "fill"):
        return 0
    trust_level = getattr(persona, "trust_level", "neutral")
    if trust_level != "skeptical":
        return 0
    blob = f"{step.intent or ''} {step.selector or ''} {step.value or ''}".lower()
    if any(k in blob for k in _SENSITIVE_ACTION_KEYWORDS):
        return 1200
    return 0


def _behavioral_settle_pause_ms(persona) -> int:
    """Post-navigate read pause for novice users — they scan a new page before acting."""
    if persona is None:
        return 0
    if getattr(persona, "tech_literacy", "intermediate") == "novice":
        return 800
    return 0


class BrowserSession:
    def __init__(
        self,
        config: RunConfig,
        artifacts_dir: Path,
        record_video: bool = False,
        record_traces: bool = False,
    ) -> None:
        self.config = config
        self.artifacts_dir = artifacts_dir
        self.record_video = record_video
        self.record_traces = record_traces
        self.console_errors: list[str] = []
        self.console_warnings: list[str] = []
        self.network_failures: list[str] = []
        self.network_log: list[dict[str, Any]] = []
        self.silent_api_failures: list[str] = []
        self._pw = None
        self._browser = None
        self._context = None
        self.page: Page | None = None
        self._viewport = "desktop"
        self.video_path: str | None = None
        self.trace_path: str | None = None
        self._persona_reset_count: int = 0

    def __enter__(self) -> BrowserSession:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._browser = _launch_browser(self._pw, self.config.browser_engine)
        first = normalize_viewports(self.config.viewports)[0]

        context_opts: dict[str, Any] = {
            "viewport": VIEWPORT_PROFILES[first],
            # B2: block service workers so cached responses from prior runs can't
            # bleed into this context and produce non-deterministic step outcomes.
            "service_workers": "block",
        }
        if self.record_video:
            video_dir = self.artifacts_dir / "videos"
            video_dir.mkdir(parents=True, exist_ok=True)
            context_opts["record_video_dir"] = str(video_dir)

        state_path = getattr(self.config.auth, "storage_state_path", None) if self.config.auth else None
        if state_path and Path(state_path).is_file():
            context_opts["storage_state"] = state_path

        self._context = self._browser.new_context(**context_opts)
        _block_analytics_routes(self._context)
        self.page = self._context.new_page()
        setup_page_for_run(self.page)
        self._viewport = first
        self.page.on("console", self._on_console)
        self.page.on("pageerror", self._on_pageerror)
        self.page.on("response", self._on_response)
        if self.record_traces:
            try:
                self._context.tracing.start(screenshots=True, snapshots=True, sources=False)
            except Exception:
                pass
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
        if self.record_traces and self._context:
            try:
                trace_path = self.artifacts_dir / "trace.zip"
                self._context.tracing.stop(path=str(trace_path))
                self.trace_path = str(trace_path)
            except Exception:
                pass
        if self.record_video and self.page:
            try:
                self.page.close()  # finalize webm before context.close()
                if self.page.video:
                    self.video_path = self.page.video.path()
            except Exception:
                pass
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def reset_context_for_persona(
        self, auth_state: dict | None = None, persona_locale: str | None = None
    ) -> None:
        """Destroy and recreate the browser context to eliminate cross-persona state bleed.

        Called in sequential mode between personas so cookies, localStorage, and
        service-worker caches from one persona can never leak into the next.
        """
        # Drain pending XHR before tearing down so in-flight requests don't corrupt the next context
        try:
            if self.page:
                self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass
        # Stop tracing for this persona before destroying its context
        if self.record_traces and self._context:
            try:
                trace_path = self.artifacts_dir / f"trace-persona{self._persona_reset_count}.zip"
                self._context.tracing.stop(path=str(trace_path))
                self._persona_reset_count += 1
            except Exception:
                pass
        # Close existing page
        try:
            if self.page:
                self.page.close()
        except Exception:
            pass
        # Close existing context (removes all cookies / storage / SW registrations)
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        # Restart the browser process to release accumulated JS-engine heap between personas
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._browser = _launch_browser(self._pw, self.config.browser_engine)
        except Exception:
            pass
        # Reset accumulated run errors so per-persona signals are clean
        self.console_errors = []
        self.console_warnings = []
        self.network_failures = []
        self.network_log = []
        self.silent_api_failures = []
        # Rebuild context with same base options, optionally restoring auth state
        context_opts: dict[str, Any] = {
            "viewport": VIEWPORT_PROFILES[self._viewport],
            "service_workers": "block",
        }
        if auth_state:
            context_opts["storage_state"] = auth_state
        if persona_locale:
            context_opts["locale"] = persona_locale
            context_opts["extra_http_headers"] = {"Accept-Language": persona_locale.replace("_", "-")}
        self._context = self._browser.new_context(**context_opts)
        _block_analytics_routes(self._context)
        self.page = self._context.new_page()
        setup_page_for_run(self.page)
        self.page.on("console", self._on_console)
        self.page.on("pageerror", self._on_pageerror)
        self.page.on("response", self._on_response)

    def _on_console(self, msg: Any) -> None:
        text = (msg.text or "")[:300]
        if msg.type == "error":
            self.console_errors.append(text)
        elif msg.type == "warning":
            self.console_warnings.append(text)

    def _on_pageerror(self, exc: Any) -> None:
        self.console_errors.append(f"[uncaught] {str(exc)[:280]}")

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
        # C8: detect silent API failures — 2xx POST/XHR with error body
        try:
            req = response.request
            if (
                req.method in ("POST", "PUT", "PATCH")
                and 200 <= response.status < 300
                and req.resource_type in ("xhr", "fetch")
                and len(self.silent_api_failures) < 20
            ):
                body = response.body()
                if len(body) < 10_000:
                    text = body.decode("utf-8", errors="replace")
                    if re.search(
                        r'"success"\s*:\s*false|"ok"\s*:\s*false|"status"\s*:\s*"error"|"error"\s*:\s*true',
                        text,
                        re.IGNORECASE,
                    ):
                        snippet = text[:300].replace("\n", " ")
                        self.silent_api_failures.append(
                            f"{req.method} {response.url[:200]} → {response.status}: {snippet}"
                        )
        except Exception:
            pass

    def reset_run_errors(self) -> None:
        self.console_errors = []
        self.console_warnings = []
        self.network_failures = []
        self.silent_api_failures = []

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

        page = self.page
        assert page is not None

        # A pre-captured session (SSO/SAML/MFA — completed once by a human via
        # `rehearse capture-session`, not something we can automate) was loaded
        # into this context's cookies/localStorage at context-creation time.
        # Navigate to the target and check whether it's actually still valid
        # before touching a login form that may not even exist for SSO-only apps.
        if getattr(auth, "storage_state_path", None):
            try:
                page.goto(self.config.target_url, wait_until="domcontentloaded", timeout=self.config.budgets.step_timeout_ms)
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            if self._auth_session_ok():
                return "success_from_storage_state"
            # Session expired — fall through to email/password automation only
            # if that fallback is actually configured; otherwise fail clearly
            # rather than pretend a login form we can't find will work.
            if not (os.environ.get(auth.email_env) and os.environ.get(auth.password_env)):
                return "failed_storage_state_expired_no_fallback"

        email = os.environ.get(auth.email_env)
        password = os.environ.get(auth.password_env)
        if not email or not password:
            return "skipped_missing_credentials"

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
                _inject_animation_freeze(page)

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
                _inject_animation_freeze(page)

                if self._auth_session_ok():
                    return "success"
                last_outcome = "failed_still_on_login"
            except Exception as exc:
                last_outcome = f"failed_attempt_{attempt + 1}"
                if attempt < 2:
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except Exception:
                        pass
                    continue
                return last_outcome

        return last_outcome

    def observe_page_state(self) -> dict:
        """Return a lightweight snapshot of the current page for adaptive step generation.

        Reads URL, title, visible headings, nav labels, button labels, and input
        placeholders. All JS evals are wrapped so a page crash / timeout returns
        empty lists rather than raising.
        """
        page = self.page
        if page is None:
            return {}

        def _safe_eval(selector: str, expr: str) -> list[str]:
            try:
                result = page.eval_on_selector_all(selector, expr)
                return [str(v).strip() for v in (result or []) if str(v).strip()][:12]
            except Exception:
                return []

        try:
            url = page.url
        except Exception:
            url = ""
        try:
            title = page.title()
        except Exception:
            title = ""

        return {
            "url": url,
            "title": title,
            "headings": _safe_eval("h1,h2,h3", "els=>els.map(e=>e.innerText.trim()).filter(Boolean)"),
            "nav_labels": _safe_eval("nav a,nav button", "els=>els.map(e=>e.innerText.trim()).filter(Boolean)"),
            "buttons": _safe_eval("button,[role='button']", "els=>els.map(e=>e.innerText.trim()).filter(Boolean)"),
            "inputs": _safe_eval("input,textarea,select", "els=>els.map(e=>e.placeholder||e.getAttribute('aria-label')||e.name||'').filter(Boolean)"),
        }

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
        persona_obj = _resolve_persona(self.config, persona_id)
        timeout = _behavioral_timeout(self.config.budgets.step_timeout_ms, persona_obj)
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
                nav_url = _absolute_url(self.config.target_url, step.url)
                response = page.goto(nav_url, wait_until="domcontentloaded", timeout=timeout)
                page.wait_for_load_state("networkidle", timeout=min(timeout, 15000))
                _inject_animation_freeze(page)
                _settle_ms = _behavioral_settle_pause_ms(persona_obj)
                if _settle_ms:
                    page.wait_for_timeout(_settle_ms)
                _consent = check_and_dismiss_consent_banner(page)
                if _consent != "none":
                    snap.note = (snap.note or "") + f"[consent-banner:{_consent}]"
            elif step.action == "wait":
                ms = int(step.value or step.url or "1000")
                page.wait_for_timeout(ms)
            elif step.action == "fill":
                value = step.resolve_value() if step.value else ""
                if persona_obj and getattr(persona_obj, "screen_reader", False):
                    loc, resolution_note = _resolve_locator_by_aria(page, step, timeout)
                else:
                    loc, resolution_note = _resolve_locator(page, step)
                focus_locator = loc
                _pause_ms = _behavioral_pre_action_pause_ms(persona_obj, step)
                if _pause_ms:
                    page.wait_for_timeout(_pause_ms)
                loc.fill(value or "", timeout=timeout)
            elif step.action == "click":
                if persona_obj and getattr(persona_obj, "screen_reader", False):
                    loc, resolution_note = _resolve_locator_by_aria(page, step, timeout)
                else:
                    loc, resolution_note = _resolve_locator(page, step)
                focus_locator = loc
                if loc.is_disabled(timeout=3000):
                    snap.outcome = "partial"
                    snap.note = "Target control is disabled"
                else:
                    _pause_ms = _behavioral_pre_action_pause_ms(persona_obj, step)
                    if _pause_ms:
                        page.wait_for_timeout(_pause_ms)
                    if persona_obj and getattr(persona_obj, "keyboard_only", False):
                        loc.focus(timeout=timeout)
                        # Check focus-visible before activation
                        _focus_visible = page.evaluate(
                            "() => { const el = document.activeElement; if (!el) return false; "
                            "const s = window.getComputedStyle(el); "
                            "return s.outlineWidth !== '0px' || s.boxShadow !== 'none'; }"
                        )
                        if not _focus_visible:
                            snap.note = (snap.note or "") + "[keyboard-only: focus not visible]"
                        loc.press("Enter", timeout=timeout)
                        snap.note = (snap.note or "") + "[keyboard-only: Enter activation]"
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
            snap.missing_alt_count = int(metrics.get("missingAltCount", 0))
            snap.low_contrast_estimate = int(metrics.get("lowContrastEstimate", 0))
            snap.error_phrases_found = _find_error_phrases(snap.body_text_excerpt)
            snap.console_errors = list(self.console_errors)
            snap.console_warnings = list(self.console_warnings)
            snap.network_failures = list(self.network_failures)
            snap.silent_api_failures = list(self.silent_api_failures)
            snap.dom_hash = _dom_fingerprint(page)
            if step.action == "navigate":
                # Wait for load event so all subresource timing entries are complete.
                # networkidle already fired above; this short wait is a safety margin
                # for resources that finished between domcontentloaded and networkidle.
                try:
                    page.wait_for_load_state("load", timeout=min(timeout, 5000))
                except Exception:
                    pass  # page may never reach "load" (SPA, SSE) — proceed with what we have
                snap.web_vitals = collect_web_vitals(page)
                snap.resource_timing = _collect_resource_timing(page)
                snap.seo_meta = _capture_seo_meta(page)
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
                _aria = _compact_aria_tree(page)
                aria_path = _save_aria_artifact(self.artifacts_dir, step_id, _aria)
                snap.artifact_paths.append(aria_path)
                snap.aria_snapshot = _aria
                snap.storage_keys = _capture_storage_keys(page)

            # Playwright's screenshot() only supports png/jpeg — webp is not a valid
            # `type` value (confirmed by Playwright raising on it). jpeg+quality still
            # gets the smaller-file-size goal this was added for.
            shot = self.artifacts_dir / f"{_safe_filename(step_id)}.jpg"
            page.screenshot(path=str(shot), full_page=True, type="jpeg", quality=80)
            snap.artifact_paths.append(str(shot))

            text_path = self.artifacts_dir / f"{_safe_filename(step_id)}.txt"
            text_path.write_text(snap.body_text_excerpt)
            snap.artifact_paths.append(str(text_path))

            if snap.outcome != "fail":
                snap.outcome = _grade_step(snap, step)

            # offline_intermittent: after a fill step, briefly go offline then reconnect to
            # test whether the app preserves form state and surfaces an offline indicator.
            if step.action == "fill":
                _persona_obj = next(
                    (p for p in self.config.personas if p.id == persona_id), None
                )
                if _persona_obj and getattr(_persona_obj, "network_throttle", None) == "offline_intermittent":
                    _offline_note = _offline_blip(self._context, page, timeout=min(timeout, 8000))
                    snap.note = (snap.note or "") + _offline_note

            # rage_mode: after a visible failure (error phrases in DOM), retry the same
            # click 3× rapidly to surface duplicate-submission and race-condition bugs.
            if (
                snap.outcome == "fail"
                and step.action == "click"
                and snap.error_phrases_found
            ):
                _persona_obj = next(
                    (p for p in self.config.personas if p.id == persona_id), None
                )
                if _persona_obj and getattr(_persona_obj, "rage_mode", False):
                    _rage_note = _rage_retry(page, loc, timeout=min(timeout, 5000))
                    snap.note = (snap.note or "") + _rage_note
        except Exception as exc:
            snap.outcome = "fail"
            snap.error_type = classify_step_error(exc)
            snap.note = str(exc)[:500]

            # rage_mode: also retry after exception (e.g. button click raised timeout)
            if step.action == "click" and focus_locator is not None:
                _persona_obj = next(
                    (p for p in self.config.personas if p.id == persona_id), None
                )
                if _persona_obj and getattr(_persona_obj, "rage_mode", False):
                    try:
                        _rage_note = _rage_retry(page, focus_locator, timeout=min(timeout, 5000))
                        snap.note = (snap.note or "") + _rage_note
                    except Exception:
                        pass

            try:
                shot = self.artifacts_dir / f"{_safe_filename(step_id)}-error.jpg"
                page.screenshot(path=str(shot), full_page=True, type="jpeg", quality=80)
                snap.artifact_paths.append(str(shot))
            except Exception:
                pass

        snap.duration_ms = int((time.perf_counter() - started) * 1000)
        return snap


def _offline_blip(context: "BrowserContext", page: "Page", *, timeout: int = 8000) -> str:
    """Go offline for 1.5s then reconnect; observe whether the UI shows an offline indicator."""
    try:
        context.set_offline(True)
        page.wait_for_timeout(1500)
        body_offline = _body_excerpt(page)
        context.set_offline(False)
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        body_online = _body_excerpt(page)
        offline_indicator = any(
            kw in body_offline.lower()
            for kw in ("offline", "no internet", "connection lost", "reconnecting")
        )
        form_preserved = any(
            kw in body_online.lower() for kw in ("your changes", "draft saved", "auto-save")
        )
        parts: list[str] = []
        if offline_indicator:
            parts.append("offline indicator shown")
        else:
            parts.append("no offline indicator")
        if form_preserved:
            parts.append("draft/auto-save detected")
        return f" [offline-blip: {', '.join(parts)}]"
    except Exception as exc:
        try:
            context.set_offline(False)
        except Exception:
            pass
        return f" [offline-blip: failed ({exc!s:.80})]"


def _rage_retry(page: "Page", locator: "Locator", *, timeout: int = 5000) -> str:
    """Click the same target 3× with 100ms gaps to surface duplicate-submit bugs."""
    from playwright.sync_api import Error as PlaywrightError

    duplicates_detected: list[str] = []
    for _ in range(3):
        try:
            page.wait_for_timeout(100)
            locator.click(timeout=timeout)
            page.wait_for_load_state("domcontentloaded", timeout=timeout)
            body = _body_excerpt(page)
            if any(p in body.lower() for p in ("order confirmed", "submitted", "success", "thank you")):
                duplicates_detected.append("possible duplicate submission")
        except PlaywrightError:
            break
    tag = (
        f" [rage: {', '.join(set(duplicates_detected))}]"
        if duplicates_detected
        else " [rage: 3× retry, no duplicate detected]"
    )
    return tag


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
