"""Product-agnostic heuristics — derive issues and delights from step evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from rehearse.dsl import Persona, RunConfig
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.sitemap import SiteMap

JOURNEY_STATUS = {"pass": 3, "partial": 2, "fail": 1}


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
    """Seed 1 only — avoids triple-counting parallel seed replays in matrix/heuristics."""
    return [s for s in steps if s.seed_index == 1]


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
        for persona in config.personas:
            result.journey_matrix[journey.id][persona.id] = status

    for step in canonical_steps:
        _analyze_step(config, step, result, seen_titles, issue_counter, delight_counter)
        issue_counter = len(result.issues)
        delight_counter = len(result.delights)

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

    result.dimensions = _score_dimensions(evidence, result, sitemap)
    result.readiness = _overall_readiness(result)
    if result.issues:
        p1 = next((i for i in result.issues if i.severity == "P1"), result.issues[0])
        result.top_blocker = p1.title
    if result.delights:
        result.top_delight = result.delights[0].title
    return result


def _analyze_step(
    config: RunConfig,
    step: StepSnapshot,
    result: AnalysisResult,
    seen: set[str],
    _ic: int,
    _dc: int,
) -> None:
    def add_issue(
        severity: str,
        title: str,
        detail: str,
        personas: list[str],
        confidence: str = "high",
    ) -> None:
        if title in seen:
            return
        seen.add(title)
        result.issues.append(
            Finding(
                id=f"I{len(result.issues)+1}",
                severity=severity,
                title=title,
                detail=detail,
                persona_ids=personas,
                step_id=step.step_id,
                confidence=confidence,
            )
        )

    def add_delight(title: str, detail: str, personas: list[str]) -> None:
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
            )

    if step.unlabeled_button_count > 0:
        add_issue(
            "P2",
            "Icon-only or unlabeled buttons",
            f"{step.unlabeled_button_count} button(s) lack accessible name on page.",
            p_power + p_admin,
        )

    if step.input_count > 0 and step.labeled_input_count < step.input_count:
        missing = step.input_count - step.labeled_input_count
        add_issue(
            "P2",
            "Form inputs missing labels",
            f"{missing} of {step.input_count} inputs lack label, aria-label, or placeholder.",
            p_first + p_admin,
        )

    if step.duration_ms > 8000:
        add_issue(
            "P3",
            "Slow step completion",
            f"Step took {step.duration_ms}ms (>8s perceived delay threshold).",
            p_power,
            confidence="high",
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
    sparse = sum(1 for s in steps if len(s.body_text_excerpt) < 80)

    func = 5 if pass_rate >= 0.9 and fail_count == 0 else 4 if pass_rate >= 0.7 else 3 if pass_rate >= 0.5 else 2
    ui = 5 if unlabeled == 0 and avg_duration < 4000 else 4 if unlabeled <= 2 else 3 if unlabeled <= 5 else 2
    info = 5 if sparse == 0 else 4 if sparse <= 1 else 3 if sparse <= 2 else 2
    if sitemap and sitemap.orphan_paths:
        info = max(2, info - 1)

    return {
        "Functionality": (func, f"{pass_rate:.0%} steps pass; {fail_count} failures"),
        "UI/UX": (ui, f"{unlabeled} unlabeled buttons; ~{int(avg_duration)}ms avg step"),
        "Information clarity": (info, f"{sparse} sparse-content pages"),
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
