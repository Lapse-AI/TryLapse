"""Product-agnostic heuristics — derive issues and delights from step evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from rehearse.dsl import Persona, RunConfig, active_personas
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.sitemap import SiteMap

JOURNEY_STATUS = {"pass": 3, "partial": 2, "fail": 1}


def _aria_has_live_region(node: dict, *, _depth: int = 0) -> bool:
    """Recursively check if an ARIA tree node or its descendants is a live region."""
    if _depth > 12:
        return False
    role = (node.get("role") or "").lower()
    if role in ("alert", "status", "log", "marquee", "timer", "alertdialog"):
        return True
    for child in node.get("children") or []:
        if _aria_has_live_region(child, _depth=_depth + 1):
            return True
    return False


@dataclass
class Finding:
    id: str
    severity: str  # P1, P2, P3
    title: str
    detail: str
    persona_ids: list[str]
    step_id: str
    confidence: str = "high"  # high | hypothesis


@dataclass
class Delight:
    id: str
    title: str
    detail: str
    persona_ids: list[str]
    step_id: str
    confidence: str = "high"  # high | hypothesis


@dataclass
class AnalysisResult:
    journey_matrix: dict[str, dict[str, str]]  # journey_id -> persona_id -> status
    issues: list[Finding] = field(default_factory=list)
    delights: list[Delight] = field(default_factory=list)
    dimensions: dict[str, tuple[int, str]] = field(default_factory=dict)
    readiness: str = "Amber"
    top_blocker: str | None = None
    top_delight: str | None = None


def _persona_tags(config: RunConfig) -> dict[str, str]:
    return {p.id: p.role.lower() for p in config.personas}


def _pick_personas(config: RunConfig, *keywords: str) -> list[str]:
    ids = []
    for p in config.personas:
        blob = f"{p.role} {' '.join(p.goals)}".lower()
        if any(k in blob for k in keywords):
            ids.append(p.id)
    return ids or [config.personas[0].id]


def _canonical_steps(steps: list[StepSnapshot]) -> list[StepSnapshot]:
    """Seed 1 + desktop viewport — avoids seed/viewport replays in matrix/heuristics."""
    seed1 = [s for s in steps if s.seed_index == 1]
    by_key: dict[tuple[str, int], StepSnapshot] = {}
    for s in seed1:
        m = re.search(r"-s(\d+)-", s.step_id)
        ord_ = int(m.group(1)) if m else 0
        key = (s.journey_id, ord_)
        vp = getattr(s, "viewport", None) or "desktop"
        prev = by_key.get(key)
        if prev is None or (getattr(prev, "viewport", "desktop") != "desktop" and vp == "desktop"):
            by_key[key] = s
    return sorted(by_key.values(), key=lambda x: x.step_id)


def _journey_status(steps: list[StepSnapshot]) -> str:
    if not steps:
        return "fail"
    if any(s.outcome == "fail" for s in steps):
        return "fail"
    if any(s.flaky for s in steps):
        return "partial"
    if any(s.outcome == "partial" for s in steps):
        return "partial"
    return "pass"


def analyze_run(
    config: RunConfig,
    evidence: RunEvidence,
    sitemap: SiteMap | None = None,
) -> AnalysisResult:
    result = AnalysisResult(journey_matrix={})
    issue_counter = 0
    delight_counter = 0
    seen_titles: set[str] = set()

    # Group steps: one browser pass tags persona_id on first persona only in runner;
    # matrix replicated per persona with same technical outcome (persona lens on findings).
    canonical_steps = _canonical_steps(evidence.steps)
    by_journey: dict[str, list[StepSnapshot]] = {}
    for step in canonical_steps:
        by_journey.setdefault(step.journey_id, []).append(step)

    for journey in config.journeys:
        steps = by_journey.get(journey.id, [])
        status = _journey_status(steps)
        result.journey_matrix[journey.id] = {}
        matrix_personas = active_personas(config) or (
            config.personas[:1] if config.personas else []
        )
        for persona in matrix_personas:
            result.journey_matrix[journey.id][persona.id] = status

    for step in canonical_steps:
        _analyze_step(config, step, result, seen_titles, issue_counter, delight_counter)
        issue_counter = len(result.issues)
        delight_counter = len(result.delights)

    _analyze_console_spike(config, canonical_steps, result, seen_titles)
    _analyze_dom_stagnation(config, canonical_steps, result, seen_titles)
    _analyze_storage_continuity(config, canonical_steps, result, seen_titles)

    flaky_seen: set[str] = set()
    for step in canonical_steps:
        if not step.flaky:
            continue
        key = f"{step.journey_id}:{step.action}:{step.note or ''}"
        if key in flaky_seen:
            continue
        flaky_seen.add(key)
        result.issues.append(
            Finding(
                id=f"I{len(result.issues)+1}",
                severity="P2",
                title=f"Flaky step ({step.action})",
                detail=step.note or "Outcomes differed across parallel seeds.",
                persona_ids=_pick_personas(config, "operator", "evaluator"),
                step_id=step.step_id,
                confidence="high",
            )
        )

    if evidence.auth_attempted and evidence.auth_outcome != "success":
        result.issues.append(
            Finding(
                id=f"I{len(result.issues)+1}",
                severity="P1",
                title="Authentication setup failed",
                detail=f"Auth outcome: {evidence.auth_outcome}. Set credentials env vars or fix login path labels in config.",
                persona_ids=_pick_personas(config, "admin", "operator"),
                step_id="auth-setup",
                confidence="high",
            )
        )

    if sitemap:
        _analyze_sitemap(config, sitemap, result, seen_titles)

    _analyze_seo_signals(config, canonical_steps, result, seen_titles)

    result.dimensions = _score_dimensions(evidence, result, sitemap)
    result.readiness = _overall_readiness(result)
    if result.issues:
        p1 = next((i for i in result.issues if i.severity == "P1"), result.issues[0])
        result.top_blocker = p1.title
    if result.delights:
        result.top_delight = result.delights[0].title
    return result


_SEVERITY_DOWNGRADE = {"P0": "P1", "P1": "P2", "P2": "P3", "P3": "P3"}


def _analyze_step(
    config: RunConfig,
    step: StepSnapshot,
    result: AnalysisResult,
    seen: set[str],
    _ic: int,
    _dc: int,
) -> None:
    # Three-run confirmation gate:
    #  - fail_rate ≥ 2/3 across seeds → downgrade severity + hypothesis confidence (filed)
    #  - fail_rate < 2/3 → skip filing entirely (non-reproducible noise)
    #  - Structural findings (a11y, HTTP status) are exempt — valid regardless of timing.
    _flaky = getattr(step, "flaky", False)
    _flake_rate: float = getattr(step, "flake_rate", 1.0)

    def add_issue(
        severity: str,
        title: str,
        detail: str,
        personas: list[str],
        confidence: str = "high",
        *,
        structural: bool = False,  # structural=True exempts from flaky gate
    ) -> None:
        if title in seen:
            return
        seen.add(title)
        eff_severity = severity
        eff_confidence = confidence
        if _flaky and not structural:
            if _flake_rate < 2 / 3:
                # Non-reproducible: appeared in fewer than 2/3 seeds — skip filing
                return
            # Reproducible flake (≥2/3 seeds): downgrade and mark hypothesis
            eff_severity = _SEVERITY_DOWNGRADE.get(severity, severity)
            eff_confidence = "hypothesis"
        result.issues.append(
            Finding(
                id=f"I{len(result.issues)+1}",
                severity=eff_severity,
                title=title,
                detail=detail + (" [confirmed: ≥2/3 seeds]" if _flaky and not structural else ""),
                persona_ids=personas,
                step_id=step.step_id,
                confidence=eff_confidence,
            )
        )

    def add_delight(
        title: str,
        detail: str,
        personas: list[str],
        *,
        confidence: str = "high",
    ) -> None:
        if title in seen:
            return
        seen.add(title)
        result.delights.append(
            Delight(
                id=f"D{len(result.delights)+1}",
                title=title,
                detail=detail,
                persona_ids=personas,
                step_id=step.step_id,
                confidence=confidence,
            )
        )

    p_first = _pick_personas(config, "first", "prospect", "new", "evaluator")
    p_power = _pick_personas(config, "operator", "power", "daily")
    p_admin = _pick_personas(config, "admin", "it", "buyer")

    if step.http_status and step.http_status >= 400:
        add_issue(
            "P1",
            f"HTTP {step.http_status} on navigation",
            f"Requested {step.requested_url or step.final_url} returned status {step.http_status}.",
            p_admin,
            structural=True,  # HTTP error is real regardless of timing
        )

    if step.outcome == "partial" and step.requested_url and step.final_url:
        req_path = urlparse(step.requested_url).path
        final_path = urlparse(step.final_url).path
        if req_path not in ("/login", "/signin") and final_path in ("/login", "/signin"):
            add_issue(
                "P2",
                "Auth wall on deep link",
                f"Navigated to {req_path} but landed on {final_path} — workflow blocked without session.",
                p_first + p_admin,
                structural=True,
            )

    if step.unlabeled_button_count > 0:
        add_issue(
            "P2",
            "Icon-only or unlabeled buttons",
            f"{step.unlabeled_button_count} button(s) lack accessible name on page.",
            p_power + p_admin,
            structural=True,  # a11y structure doesn't change between runs
        )

    if step.input_count > 0 and step.labeled_input_count < step.input_count:
        missing = step.input_count - step.labeled_input_count
        add_issue(
            "P2",
            "Form inputs missing labels",
            f"{missing} of {step.input_count} inputs lack label, aria-label, or placeholder.",
            p_first + p_admin,
            structural=True,
        )

    if step.duration_ms > 8000:
        add_issue(
            "P3",
            "Slow step completion",
            f"Step took {step.duration_ms}ms (>8s perceived delay threshold).",
            p_power,
            confidence="high",
        )

    if step.resource_timing:
        slow = [r for r in step.resource_timing if r.get("durationMs", 0) > 2000]
        if slow:
            worst = slow[0]
            add_issue(
                "P2",
                "Single asset causing page slowdown",
                f"Resource '{worst.get('name', '?')}' (type: {worst.get('type', '?')}) "
                f"took {worst['durationMs']}ms to load — this is the likely cause of slow "
                f"LCP. {len(slow)} resource(s) over 2s threshold.",
                p_power + p_first,
            )

    body_lower = step.body_text_excerpt.lower()
    if step.action == "navigate" and len(body_lower) < 80:
        add_issue(
            "P2",
            "Sparse page content",
            "Page body has very little text — value proposition may be unclear.",
            p_first,
        )

    if "initializing" in body_lower or body_lower.strip() == "loading...":
        add_issue(
            "P1",
            "Page stuck in loading state",
            "Body text suggests incomplete render (Initializing/Loading).",
            p_power,
        )

    cta_count = body_lower.count("sign up") + body_lower.count("get started") + body_lower.count("start free")
    if cta_count >= 4:
        add_issue(
            "P3",
            "Duplicate primary CTAs",
            f"Detected {cta_count} similar signup CTAs — may confuse return visitors.",
            p_power,
            confidence="hypothesis",
        )

    if step.error_phrases_found and step.action == "click":
        add_delight(
            "Visible error feedback after action",
            f"User-visible error language detected: {', '.join(step.error_phrases_found)}.",
            p_first,
        )

    if step.note and "offline-blip:" in step.note and "no offline indicator" in step.note:
        add_issue(
            "p2",
            "No offline indicator during connectivity loss",
            "After a form fill, the intermittent-connection persona lost connectivity for 1.5s. "
            "No offline banner or indicator was detected. Users on flaky connections won't know "
            "their submission is pending.",
            [step.persona_id],
        )

    if step.note and "offline-blip:" in step.note and "no offline indicator" not in step.note:
        add_delight(
            "Offline state communicated to user",
            "App displayed an offline indicator during a simulated connectivity blip — "
            "users on flaky connections will know what's happening.",
            [step.persona_id],
        )

    if step.resolved_selector and "screen-reader-fallback: ARIA resolution failed" in step.resolved_selector:
        add_issue(
            "p1",
            "Interactive element unreachable via ARIA tree",
            "The screen-reader persona could not locate this element by label, role, or "
            "accessible name — it fell back to CSS selector. Screen reader users cannot "
            "reach this element. Ensure the element has an aria-label, aria-labelledby, "
            "or a visible <label> association.",
            [step.persona_id],
            structural=True,
        )
    elif step.resolved_selector and "no accessible name" in step.resolved_selector:
        add_issue(
            "p2",
            "Interactive element has no accessible name",
            "The screen-reader persona matched this element by visible text only — it has "
            "no aria-label or <label> association. Screen readers may not describe it correctly.",
            [step.persona_id],
            structural=True,
        )

    # Check aria_snapshot for missing live regions when error phrases are present
    if step.error_phrases_found and step.aria_snapshot:
        has_live = _aria_has_live_region(step.aria_snapshot)
        if not has_live:
            add_issue(
                "p2",
                "Error state not announced to screen readers",
                f"Error language was detected ({', '.join(step.error_phrases_found[:2])}) "
                "but the ARIA tree has no live region (role=alert, aria-live=polite/assertive). "
                "Screen reader users won't hear the error.",
                [step.persona_id],
                structural=True,
            )

    if step.note and "keyboard-only: focus not visible" in step.note:
        add_issue(
            "p1",
            "Keyboard focus indicator missing",
            "A keyboard-only persona focused an interactive element and no visible focus outline "
            "or box-shadow was detected. Keyboard users cannot see where they are on the page. "
            "This is a WCAG 2.4.7 failure (Focus Visible, Level AA).",
            [step.persona_id],
            structural=True,
        )

    _RTL_LOCALES = {"ar", "ar-SA", "ar-EG", "he", "he-IL", "fa", "ur"}
    _step_persona = next((p for p in config.personas if p.id == step.persona_id), None)
    _step_locale = getattr(_step_persona, "locale", None) if _step_persona else None
    if _step_locale and _step_locale.split("-")[0] in {l.split("-")[0] for l in _RTL_LOCALES}:
        body_lower = step.body_text_excerpt.lower()
        if step.action == "navigate" and step.outcome == "pass":
            if any(kw in body_lower for kw in ("ltr", "text-align: left", "direction: ltr")):
                add_issue(
                    "p2",
                    "RTL locale served LTR layout",
                    f"Persona using locale '{_step_locale}' (RTL language) was served a page "
                    "with LTR direction hints. Layout may be broken for Arabic/Hebrew users.",
                    [step.persona_id],
                    confidence="hypothesis",
                )

    if step.note and "[consent-banner:blocked]" in step.note:
        add_issue(
            "p1",
            "Undismissable consent banner blocks user journey",
            f"A GDPR/CCPA consent banner was detected on {step.final_url or step.requested_url} "
            "and could not be dismissed automatically. This blocks the journey runner from "
            "testing the page — and blocks real users in regulated markets who cannot proceed "
            "past the banner. Ensure the banner can be accepted via a visible 'Accept' button.",
            [step.persona_id],
            confidence="high",
        )
    elif step.note and "[consent-banner:dismissed]" in step.note:
        add_delight(
            "Consent banner dismissible",
            f"A GDPR/CCPA consent banner was detected and successfully dismissed on "
            f"{step.final_url or step.requested_url}. Users can proceed past it.",
            [step.persona_id],
        )

    if step.note and "rage:" in step.note and "possible duplicate submission" in step.note:
        add_issue(
            "p0",
            "Duplicate submission on rage-retry",
            "After a visible error, the frustrated-user persona retried the same action "
            "and triggered what appears to be a duplicate form submission. Duplicate orders, "
            "double-charges, or double-sends are likely.",
            [step.persona_id],
            confidence="hypothesis",
            structural=True,
        )
    elif step.note and "rage:" in step.note and "3× retry" in step.note:
        add_issue(
            "p2",
            "No feedback prevents frustrated re-submission",
            "After a failed action the UI did not disable the submit button or show a "
            "loading state, allowing repeated clicks. A frustrated user will keep retrying.",
            [step.persona_id],
        )

    if step.link_count >= 4 and step.heading_count >= 1:
        add_delight(
            "Clear navigation structure",
            f"Page has {step.link_count} links and {step.heading_count} headings.",
            p_first + p_power,
        )

    if step.input_count >= 2 and step.labeled_input_count == step.input_count:
        add_delight(
            "Accessible form labels",
            f"All {step.input_count} form inputs have labels or placeholders.",
            p_admin,
        )

    if step.heading_count >= 1 and len(step.body_text_excerpt) > 200:
        add_delight(
            "Informative landing content",
            "Page includes headings and substantive body copy for first-time evaluators.",
            p_first,
        )

    if step.console_errors:
        add_issue(
            "P2",
            "Console errors on page",
            f"{len(step.console_errors)} console error(s): {step.console_errors[0][:120]}",
            p_power,
        )

    warnings = getattr(step, "console_warnings", None) or []
    if len(warnings) >= 2:
        add_issue(
            "P3",
            "Console warnings on page",
            f"{len(warnings)} warning(s): {warnings[0][:120]}",
            p_power,
        )

    net_fails = getattr(step, "network_failures", None) or []
    if net_fails and step.action in ("click", "fill", "select", "press"):
        # Network failures during user-action steps indicate API errors on
        # form submission / data mutation — high severity because the user saw
        # no error feedback but the backend request failed.
        sev = "P1" if len(net_fails) >= 2 else "P2"
        add_issue(
            sev,
            "Network request failure during user action",
            f"{len(net_fails)} request(s) failed during '{step.action}': {net_fails[0][:200]}",
            p_power + p_first,
            confidence="high",
        )

    # C8: silent API failure — 200 OK but error body
    silent = getattr(step, "silent_api_failures", None) or []
    if silent and step.action in ("click", "fill", "select", "submit"):
        add_issue(
            "P1",
            "Silent API failure (200 OK but error body)",
            f"{len(silent)} API response(s) returned HTTP 200 but an error body: {silent[0][:200]}. "
            "Users see no error but their action did not succeed.",
            p_power + p_first,
            confidence="high",
        )


def _analyze_dom_stagnation(
    config: RunConfig,
    steps: list[StepSnapshot],
    result: AnalysisResult,
    seen: set[str],
) -> None:
    """C4: Flag steps where DOM fingerprint didn't change after an interaction.

    If the user clicked or submitted a form but the DOM structure is identical
    to the previous step, the action likely had no visible effect — a UX hole
    where feedback is missing.
    """
    INTERACTION_ACTIONS = {"click", "fill", "select", "press", "submit"}
    by_journey: dict[str, list[StepSnapshot]] = {}
    for s in steps:
        by_journey.setdefault(s.journey_id, []).append(s)

    for journey_id, jsteps in by_journey.items():
        sorted_steps = sorted(jsteps, key=lambda s: s.step_id)
        for i in range(1, len(sorted_steps)):
            prev, curr = sorted_steps[i - 1], sorted_steps[i]
            prev_hash = getattr(prev, "dom_hash", None)
            curr_hash = getattr(curr, "dom_hash", None)
            if (
                prev_hash
                and curr_hash
                and prev_hash == curr_hash
                and prev.action in INTERACTION_ACTIONS
                and prev.final_url == curr.final_url  # same page — not a navigation
                and prev.outcome != "fail"
            ):
                title = f"No visible DOM change after '{prev.action}'"
                if title not in seen:
                    seen.add(title)
                    result.issues.append(
                        Finding(
                            id=f"I{len(result.issues)+1}",
                            severity="P2",
                            title=title,
                            detail=(
                                f"DOM fingerprint unchanged between step '{prev.action}' and "
                                f"'{curr.action}' in journey '{prev.journey_name}'. "
                                "The interaction may have had no effect — check for missing "
                                "feedback, broken event handlers, or silent failures."
                            ),
                            persona_ids=_pick_personas(config, "power", "operator", "first"),
                            step_id=prev.step_id,
                            confidence="hypothesis",
                        )
                    )


def _analyze_storage_continuity(
    config: RunConfig,
    steps: list[StepSnapshot],
    result: AnalysisResult,
    seen: set[str],
) -> None:
    """Detect auth token / session key disappearing mid-journey (session expiry bug)."""
    _AUTH_PATTERNS = ("token", "session", "auth", "jwt", "user_id", "access", "refresh")
    by_journey: dict[str, list[StepSnapshot]] = {}
    for s in steps:
        if s.storage_keys is not None:
            by_journey.setdefault(s.journey_id, []).append(s)

    for journey_id, jsteps in by_journey.items():
        if len(jsteps) < 2:
            continue
        # Find auth keys present at step 0
        first_auth = {k for k in jsteps[0].storage_keys or [] if any(p in k.lower() for p in _AUTH_PATTERNS)}
        if not first_auth:
            continue
        for s in jsteps[1:]:
            current_auth = {k for k in s.storage_keys or [] if any(p in k.lower() for p in _AUTH_PATTERNS)}
            vanished = first_auth - current_auth
            if vanished:
                title = "Auth session lost mid-journey"
                if title not in seen:
                    seen.add(title)
                    result.issues.append(
                        Finding(
                            id=f"I{len(result.issues)+1}",
                            severity="P0",
                            title=title,
                            detail=(
                                f"Storage keys {sorted(vanished)} were present at journey "
                                f"start but missing at step '{s.step_id}'. Session may have "
                                "expired or been cleared mid-flow — user gets silently logged out."
                            ),
                            persona_ids=[s.persona_id],
                            step_id=s.step_id,
                            confidence="hypothesis",
                        )
                    )
                break  # one finding per journey


def _analyze_console_spike(
    config: RunConfig,
    steps: list[StepSnapshot],
    result: AnalysisResult,
    seen: set[str],
) -> None:
    """Run-level console spike — attributed to operator persona (BRW-B3)."""
    total_errors = sum(len(s.console_errors) for s in steps)
    total_warnings = sum(len(getattr(s, "console_warnings", None) or []) for s in steps)
    if total_errors < 3 and total_warnings < 8:
        return
    title = "Console noise spike across run"
    if title in seen:
        return
    seen.add(title)
    result.issues.append(
        Finding(
            id=f"I{len(result.issues)+1}",
            severity="P2",
            title=title,
            detail=(
                f"Captured {total_errors} console error(s) and {total_warnings} warning(s) "
                "across canonical steps — review network-log and step artifacts."
            ),
            persona_ids=_pick_personas(config, "operator", "power", "daily"),
            step_id=steps[0].step_id if steps else "run-console",
            confidence="high",
        )
    )


def _analyze_seo_signals(
    config: RunConfig,
    steps: list[StepSnapshot],
    result: AnalysisResult,
    seen: set[str],
) -> None:
    """A5: SEO health signals — filed as P2 findings for navigate steps with seo_meta."""
    navigate_steps = [s for s in steps if s.action == "navigate" and s.seo_meta]
    if not navigate_steps:
        return

    missing_desc = [s for s in navigate_steps if not (s.seo_meta or {}).get("metaDescription")]
    noindex_steps = [
        s for s in navigate_steps
        if "noindex" in ((s.seo_meta or {}).get("robots") or "").lower()
    ]
    no_h1 = [s for s in navigate_steps if (s.seo_meta or {}).get("h1Count", 1) == 0]

    # Duplicate page titles across navigate steps — skip SPA hash-route navigation
    # where URLs share hostname+path and differ only in fragment (same page by design).
    from urllib.parse import urlparse as _urlparse

    def _base_url(url: str) -> str:
        try:
            p = _urlparse(url)
            return f"{p.scheme}://{p.netloc}{p.path}"
        except Exception:
            return url

    title_map: dict[str, list[str]] = {}
    _seen_title_base: set[tuple[str, str]] = set()
    for s in navigate_steps:
        if s.page_title:
            url = s.final_url or s.requested_url or s.step_id
            base = _base_url(url) if isinstance(url, str) and url.startswith("http") else url
            key = (s.page_title.strip(), base)
            if key in _seen_title_base:
                continue
            _seen_title_base.add(key)
            title_map.setdefault(s.page_title.strip(), []).append(url)
    dup_titles = {t: urls for t, urls in title_map.items() if len(urls) > 1}

    personas = _pick_personas(config, "operator", "power", "daily", "admin")
    step_id = navigate_steps[0].step_id

    if missing_desc:
        title = "Missing meta description on key pages"
        if title not in seen:
            seen.add(title)
            urls = [s.final_url or s.requested_url or "" for s in missing_desc[:4]]
            result.issues.append(Finding(
                id=f"I{len(result.issues)+1}",
                severity="P2",
                title=title,
                detail=(
                    f"{len(missing_desc)} page(s) have no <meta name=\"description\"> tag. "
                    f"Search engines display the meta description in results — its absence harms CTR. "
                    f"Affected: {', '.join(u for u in urls if u)[:200]}"
                ),
                persona_ids=personas,
                step_id=step_id,
                confidence="high",
            ))

    if noindex_steps:
        title = "Pages marked noindex may block search visibility"
        if title not in seen:
            seen.add(title)
            urls = [s.final_url or s.requested_url or "" for s in noindex_steps[:4]]
            result.issues.append(Finding(
                id=f"I{len(result.issues)+1}",
                severity="P2",
                title=title,
                detail=(
                    f"{len(noindex_steps)} page(s) have robots noindex directive. "
                    f"Verify these pages should not be indexed. "
                    f"Affected: {', '.join(u for u in urls if u)[:200]}"
                ),
                persona_ids=personas,
                step_id=step_id,
                confidence="hypothesis",
            ))

    if dup_titles:
        title = "Duplicate page titles detected"
        if title not in seen:
            seen.add(title)
            examples = list(dup_titles.items())[:3]
            detail_parts = [f'"{t}" → {", ".join(urls[:2])}' for t, urls in examples]
            result.issues.append(Finding(
                id=f"I{len(result.issues)+1}",
                severity="P2",
                title=title,
                detail=(
                    "Multiple pages share the same <title> tag — search engines may collapse "
                    "or de-rank duplicate-title pages. "
                    + "; ".join(detail_parts)
                ),
                persona_ids=personas,
                step_id=step_id,
                confidence="high",
            ))

    if no_h1:
        title = "Pages missing H1 heading"
        if title not in seen:
            seen.add(title)
            urls = [s.final_url or s.requested_url or "" for s in no_h1[:4]]
            result.issues.append(Finding(
                id=f"I{len(result.issues)+1}",
                severity="P2",
                title=title,
                detail=(
                    f"{len(no_h1)} page(s) have no <h1> element. "
                    "A missing H1 weakens page topic signals for both search engines and screen readers. "
                    f"Affected: {', '.join(u for u in urls if u)[:200]}"
                ),
                persona_ids=personas,
                step_id=step_id,
                confidence="high",
            ))


def _analyze_sitemap(
    config: RunConfig,
    sitemap: SiteMap,
    result: AnalysisResult,
    seen: set[str],
) -> None:
    if sitemap.error_paths:
        title = "Crawl found error pages"
        if title not in seen:
            seen.add(title)
            result.issues.append(
                Finding(
                    id=f"I{len(result.issues)+1}",
                    severity="P1",
                    title=title,
                    detail=f"Paths: {', '.join(sitemap.error_paths[:8])}",
                    persona_ids=_pick_personas(config, "admin"),
                    step_id="crawl-graph",
                )
            )
    if len(sitemap.pages) >= 2:
        depths = {p.path: p.depth for p in sitemap.pages}
        max_depth = max(depths.values())
        if max_depth >= 3:
            title = "Deep navigation required"
            if title not in seen:
                seen.add(title)
                result.issues.append(
                    Finding(
                        id=f"I{len(result.issues)+1}",
                        severity="P3",
                        title=title,
                        detail=f"Site depth reaches {max_depth} clicks from entry — may hurt first-time evaluators.",
                        persona_ids=_pick_personas(config, "first", "evaluator"),
                        step_id="crawl-graph",
                        confidence="hypothesis",
                    )
                )
    form_pages = [p for p in sitemap.pages if p.form_count > 0]
    if form_pages:
        title = "Interactive forms discovered"
        if title not in seen:
            seen.add(title)
            result.delights.append(
                Delight(
                    id=f"D{len(result.delights)+1}",
                    title=title,
                    detail=f"{len(form_pages)} pages with forms — workflow automation candidate.",
                    persona_ids=_pick_personas(config, "operator"),
                    step_id="crawl-graph",
                )
            )


def _score_dimensions(
    evidence: RunEvidence,
    analysis: AnalysisResult,
    sitemap: SiteMap | None = None,
) -> dict[str, tuple[int, str]]:
    steps = evidence.steps
    if not steps:
        return {
            "Functionality": (1, "No steps executed"),
            "UI/UX": (1, "No steps executed"),
            "Information clarity": (1, "No steps executed"),
        }

    pass_rate = sum(1 for s in steps if s.outcome == "pass") / len(steps)
    fail_count = sum(1 for s in steps if s.outcome == "fail")
    unlabeled = sum(s.unlabeled_button_count for s in steps)
    avg_duration = sum(s.duration_ms for s in steps) / len(steps)

    total_inputs = sum(getattr(s, "input_count", 0) for s in steps)
    labeled_inputs = sum(getattr(s, "labeled_input_count", 0) for s in steps)
    total_headings = sum(getattr(s, "heading_count", 0) for s in steps)
    total_links = sum(getattr(s, "link_count", 0) for s in steps)

    # Information clarity — multi-signal content richness (replaces crude 80-char threshold)
    #
    # Signals:
    #  content_depth   — average body text length on navigate steps (longer = richer)
    #  heading_density — headings per navigate step (structure signal)
    #  link_density    — links per navigate step (navigation richness)
    #  sparse_pages    — pages with low text AND no headings AND few links (combined)
    #
    # Scoring rubric:
    #  5 — rich content (avg body > 400 chars, ≥1 heading/page, ≥3 links/page, 0 sparse)
    #  4 — adequate (avg body > 200 chars OR good structure, ≤1 sparse page)
    #  3 — thin content (avg body 80-200 chars, sparse pages, or no heading structure)
    #  2 — very sparse (avg body < 80 chars, no headings, few links)
    nav_steps = [s for s in steps if s.action == "navigate"]
    n_nav = len(nav_steps) or 1
    avg_body_len = sum(len(s.body_text_excerpt or "") for s in nav_steps) / n_nav
    heading_density = total_headings / n_nav
    link_density = total_links / n_nav
    sparse = sum(
        1 for s in nav_steps
        if len(s.body_text_excerpt or "") < 120
        and getattr(s, "heading_count", 0) == 0
        and getattr(s, "link_count", 0) < 3
    )
    has_structure = heading_density >= 0.8 and link_density >= 2

    if avg_body_len >= 400 and has_structure and sparse == 0:
        info = 5
    elif avg_body_len >= 200 or (has_structure and sparse <= 1):
        info = 4
    elif avg_body_len >= 80 or sparse <= 2:
        info = 3
    else:
        info = 2
    if sitemap and sitemap.orphan_paths:
        info = max(2, info - 1)

    func = 5 if pass_rate >= 0.9 and fail_count == 0 else 4 if pass_rate >= 0.7 else 3 if pass_rate >= 0.5 else 2
    ui = 5 if unlabeled == 0 and avg_duration < 4000 else 4 if unlabeled <= 2 else 3 if unlabeled <= 5 else 2

    # Build descriptive signals
    input_label_note = ""
    if total_inputs > 0:
        unlabeled_inputs = total_inputs - labeled_inputs
        if unlabeled_inputs > 0:
            input_label_note = f"; {unlabeled_inputs}/{total_inputs} inputs unlabeled"

    info_note = (
        f"avg body {int(avg_body_len)}ch; {heading_density:.1f} hdg/page; "
        f"{link_density:.1f} links/page; {sparse} sparse pages"
    )

    return {
        "Functionality": (func, f"{pass_rate:.0%} steps pass; {fail_count} failures"),
        "UI/UX": (ui, f"{unlabeled} unlabeled buttons{input_label_note}; ~{int(avg_duration)}ms avg step"),
        "Information clarity": (info, info_note),
    }


def _overall_readiness(analysis: AnalysisResult) -> str:
    p1 = sum(1 for i in analysis.issues if i.severity == "P1")
    pass_cells = sum(
        1
        for row in analysis.journey_matrix.values()
        for status in row.values()
        if status == "pass"
    )
    total_cells = sum(len(row) for row in analysis.journey_matrix.values()) or 1
    pass_ratio = pass_cells / total_cells
    if p1 >= 2 or pass_ratio < 0.4:
        return "Red"
    if p1 >= 1 or pass_ratio < 0.7:
        return "Amber"
    return "Green"
