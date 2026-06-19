"""Human-readable run narratives — template baseline + optional LLM enrichment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rehearse.context import RunContext
from rehearse.dsl import RunConfig, Persona
from rehearse.evidence import RunEvidence
from rehearse.heuristics import AnalysisResult, _canonical_steps


def build_template_narrative(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    *,
    ctx: RunContext | None = None,
) -> dict[str, Any]:
    """Deterministic plain-language summary (always available, no API key)."""
    band = analysis.readiness
    p1 = [i for i in analysis.issues if i.severity == "P1"]
    p2 = [i for i in analysis.issues if i.severity == "P2"]
    steps = _canonical_steps(evidence.steps)
    passed = sum(1 for s in steps if s.outcome == "pass")
    total = len(steps) or 1
    pass_pct = int(100 * passed / total)

    matrix = analysis.journey_matrix
    fail_journeys = [
        jid for jid, row in matrix.items() if any(v == "fail" for v in row.values())
    ]
    partial_journeys = [
        jid
        for jid, row in matrix.items()
        if any(v == "partial" for v in row.values()) and jid not in fail_journeys
    ]

    journey_names = {j.id: j.name for j in config.journeys}
    top_blocker = analysis.top_blocker or (p1[0].title if p1 else None)
    top_delight = analysis.top_delight or (
        analysis.delights[0].title if analysis.delights else None
    )

    executive = (
        f"{config.product_name} at {config.target_url} rehearsed as **{band}** readiness. "
        f"{passed}/{total} canonical steps passed ({pass_pct}%). "
        f"{len(analysis.issues)} issue(s) and {len(analysis.delights)} delight(s) recorded."
    )
    if top_blocker:
        executive += f" Primary concern: {top_blocker}."
    if top_delight:
        executive += f" Bright spot: {top_delight}."

    founder_lines = [
        f"**Launch readiness: {band}** — suitable for "
        + (
            "design-partner demos with known caveats."
            if band == "Amber"
            else "a confident partner readout."
            if band == "Green"
            else "internal review before external calls."
        ),
    ]
    if fail_journeys:
        names = ", ".join(journey_names.get(j, j) for j in fail_journeys[:4])
        founder_lines.append(f"Broken journeys: {names}.")
    if partial_journeys:
        names = ", ".join(journey_names.get(j, j) for j in partial_journeys[:4])
        founder_lines.append(f"Friction journeys: {names}.")
    if p1:
        founder_lines.append(
            "Blockers to discuss: " + "; ".join(i.title for i in p1[:3]) + "."
        )

    eng_lines = [
        f"Run `{evidence.run_id}` · {evidence.duration_ms // 1000}s · "
        f"{len(evidence.steps)} step records (incl. viewport/seed replays).",
    ]
    if ctx and ctx.sitemap:
        eng_lines.append(
            f"Crawl: {len(ctx.sitemap.pages)} pages, "
            f"{len(ctx.sitemap.error_paths)} error paths, "
            f"{len(ctx.sitemap.orphan_paths)} orphans."
        )
    if evidence.network_log_path:
        eng_lines.append(f"Network log: `{evidence.network_log_path}`.")
    if ctx and ctx.metadata.get("web_vitals_path"):
        eng_lines.append(f"Web Vitals: `{ctx.metadata['web_vitals_path']}`.")
    if p2:
        eng_lines.append("Notable P2: " + "; ".join(i.title for i in p2[:4]) + ".")

    questions = [
        "What is the single blocker we should fix before the next partner call?",
        "Which journey had the worst persona × path outcome?",
        "Did any step show flaky behavior across seeds or viewports?",
    ]
    if band == "Green":
        questions[0] = "What polish items (P3) are worth doing before GA?"
    if fail_journeys:
        questions[1] = f"Why did {journey_names.get(fail_journeys[0], fail_journeys[0])} fail?"

    # ── Layer 1: The Verdict ─────────────────────────────────────────────────
    # Single go/no-go signal with a plain-language reason. The only thing a
    # non-technical founder needs to read to make the ship/hold decision.
    p0 = [i for i in analysis.issues if i.severity == "P0"]
    if band == "Red" or p0 or (band == "Amber" and len(p1) >= 3):
        decision = "no_ship"
        verdict_headline = "Do not ship this build."
        verdict_reason = (
            f"{len(p0) + len(p1)} blocker(s) will break user journeys in production. "
            + (f"Worst: {p0[0].title}." if p0 else f"Worst: {p1[0].title}." if p1 else "")
        )
    elif band == "Amber":
        decision = "caution"
        verdict_headline = "Ship with caution — fix blockers first."
        verdict_reason = (
            f"{len(p1)} issue(s) will affect some users. Resolve before wide launch. "
            + (f"Priority fix: {p1[0].title}." if p1 else "")
        )
    else:
        decision = "ship"
        verdict_headline = "Ready to ship."
        verdict_reason = (
            f"{pass_pct}% of canonical steps passed with no journey-breaking failures. "
            + (f"Polish opportunity: {p2[0].title}." if p2 else "No critical gaps found.")
        )

    layer1 = {
        "decision": decision,
        "headline": verdict_headline,
        "reason": verdict_reason,
        "band": band,
    }

    # ── Layer 2: The Story ────────────────────────────────────────────────────
    # 2–3 sentences a product manager or investor can read cold.
    journey_count = len(matrix)
    fail_count = len(fail_journeys)
    story_parts = [
        f"TryLapse sent {len(config.personas)} AI personas through "
        f"{journey_count} product journey{'s' if journey_count > 1 else ''} "
        f"and scored **{passed}/{total}** steps as passing."
    ]
    if fail_count:
        names = ", ".join(journey_names.get(j, j) for j in fail_journeys[:2])
        story_parts.append(
            f"{fail_count} journey{'s' if fail_count > 1 else ''} — {names} — "
            "failed completely, meaning users would be blocked before completing their goal."
        )
    elif partial_journeys:
        names = ", ".join(journey_names.get(j, j) for j in partial_journeys[:2])
        story_parts.append(
            f"No journeys broke outright, but {len(partial_journeys)} — {names} — "
            "had significant friction that could drive users to abandon."
        )
    else:
        story_parts.append(
            "All journeys completed successfully across all tested personas."
        )
    if analysis.delights:
        story_parts.append(
            f"{len(analysis.delights)} genuine product strength(s) found: {analysis.delights[0].title}."
        )

    layer2_story = " ".join(story_parts)

    # ── Layer 3: The Fix Hierarchy ────────────────────────────────────────────
    # Actionable sorted list with effort tags so an engineer can start immediately.
    _effort_map = {
        "P0": "large",
        "P1": "medium",
        "P2": "small",
        "P3": "tiny",
    }
    _what_map = {
        "P0": "Fix immediately — journey is blocked.",
        "P1": "Fix before launch — significant user impact.",
        "P2": "Fix before GA — noticeable but not blocking.",
        "P3": "Track in backlog — polish item.",
    }
    layer3_fixes = [
        {
            "priority": i.severity,
            "title": i.title,
            "detail": i.detail,
            "effort": _effort_map.get(i.severity, "medium"),
            "action": _what_map.get(i.severity, "Review and prioritize."),
            "step_id": i.step_id,
            "confidence": i.confidence,
        }
        for i in sorted(
            analysis.issues,
            key=lambda x: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(x.severity, 4),
        )
    ]

    # ── Layer 4: The Forward ──────────────────────────────────────────────────
    # 3 concrete next-sprint actions, not generic advice.
    forward_actions: list[str] = []
    if p0:
        forward_actions.append(f"Fix P0: {p0[0].title} — blocks the {fail_journeys[0] if fail_journeys else 'primary'} journey.")
    if p1:
        forward_actions.append(f"Fix P1 before launch: {p1[0].title}.")
    if not fail_journeys and not p1:
        forward_actions.append("Expand coverage: add edge-case journeys for error states and empty states.")
    if analysis.delights:
        forward_actions.append(f"Double down on strength: {analysis.delights[0].title} — amplify in onboarding.")
    if len(forward_actions) < 3:
        forward_actions.append("Run again after fixes to confirm the score moved — track trend across builds.")

    layer4_forward = forward_actions[:4]

    # ── Layer 5: Trend ────────────────────────────────────────────────────────
    # Populated externally when compare data is available; placeholder here.
    layer5_trend: dict = {
        "available": False,
        "note": "Run a second build to see score trajectory.",
    }

    return {
        "executiveSummary": executive,
        "forFounders": "\n".join(founder_lines),
        "forEngineering": "\n".join(eng_lines),
        "suggestedQuestions": questions,
        "source": "template",
        "readinessBand": band,
        "issueCount": len(analysis.issues),
        "delightCount": len(analysis.delights),
        # 5-layer non-technical UX output
        "layer1Verdict": layer1,
        "layer2Story": layer2_story,
        "layer3FixHierarchy": layer3_fixes,
        "layer4Forward": layer4_forward,
        "layer5Trend": layer5_trend,
    }


def merge_llm_narrative(template: dict[str, Any], llm_data: dict[str, Any]) -> dict[str, Any]:
    """Overlay LLM prose when present; keep template as fallback fields."""
    out = dict(template)
    out["source"] = "llm+template"
    for key in (
        "executiveSummary",
        "forFounders",
        "forEngineering",
        "suggestedQuestions",
    ):
        if llm_data.get(key):
            out[key] = llm_data[key]
    if llm_data.get("chatReadySummary"):
        out["chatReadySummary"] = llm_data["chatReadySummary"]
    return out


def build_run_narrative(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    *,
    ctx: RunContext | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    template = build_template_narrative(config, evidence, analysis, ctx=ctx)
    if not use_llm:
        return template
    from rehearse.llm import generate_run_narrative_llm, llm_enabled

    if not llm_enabled():
        return template
    llm_data = generate_run_narrative_llm(config, evidence, analysis, ctx=ctx, template=template)
    if not llm_data or llm_data.get("error"):
        template["llmNote"] = llm_data.get("error") if llm_data else "LLM unavailable"
        return template
    return merge_llm_narrative(template, llm_data)


def narrative_from_bundle(bundle: dict[str, Any]) -> dict[str, Any] | None:
    n = bundle.get("narrative")
    return n if isinstance(n, dict) else None


def build_template_compare_narrative(
    diff: dict[str, Any],
    *,
    bundle_a: dict[str, Any] | None = None,
    bundle_b: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Plain-language diff between two runs (NLU-2)."""
    run_a = diff.get("runA") or diff.get("run_a") or "A"
    run_b = diff.get("runB") or diff.get("run_b") or "B"
    ra = diff.get("readinessA") or diff.get("readiness_a") or "?"
    rb = diff.get("readinessB") or diff.get("readiness_b") or "?"
    ia = diff.get("issuesA") or diff.get("issues_a") or 0
    ib = diff.get("issuesB") or diff.get("issues_b") or 0
    pa = diff.get("pagesA") or diff.get("pages_a") or 0
    pb = diff.get("pagesB") or diff.get("pages_b") or 0

    readiness_delta = (
        "unchanged"
        if ra == rb
        else f"**{ra} → {rb}**"
        + (
            " (improved)"
            if _readiness_rank(rb) > _readiness_rank(ra)
            else " (regressed)" if _readiness_rank(rb) < _readiness_rank(ra) else ""
        )
    )

    headline = (
        f"From `{run_a}` to `{run_b}`: readiness {readiness_delta}, "
        f"issues {ia} → {ib}, pages crawled {pa} → {pb}."
    )

    new_issues = diff.get("newIssues") or diff.get("new_issues") or []
    resolved = diff.get("resolvedIssues") or diff.get("resolved_issues") or []
    changed = diff.get("changedSteps") or diff.get("changed_steps") or []

    founder_lines = [headline.replace("**", "")]
    if _readiness_rank(rb) > _readiness_rank(ra):
        founder_lines.append("Trend: rehearsal signals are stronger for the newer run.")
    elif _readiness_rank(rb) < _readiness_rank(ra):
        founder_lines.append("Trend: the newer run looks riskier — review before external demos.")

    if new_issues:
        founder_lines.append("New concerns: " + "; ".join(new_issues[:4]) + ".")
    if resolved:
        founder_lines.append("Cleared since prior run: " + "; ".join(resolved[:4]) + ".")

    eng_lines = [
        f"Changed steps: {len(changed)} · only in A: {len(diff.get('stepsOnlyInA') or [])} · "
        f"only in B: {len(diff.get('stepsOnlyInB') or [])}",
    ]
    new_pages = diff.get("newPages") or diff.get("new_pages") or []
    removed_pages = diff.get("removedPages") or diff.get("removed_pages") or []
    if new_pages:
        eng_lines.append(f"New crawl paths ({len(new_pages)}): " + ", ".join(new_pages[:6]))
    if removed_pages:
        eng_lines.append(f"Removed paths ({len(removed_pages)}): " + ", ".join(removed_pages[:6]))
    if changed:
        sample = changed[0]
        eng_lines.append(
            f"Example step change: {sample.get('stepId')} "
            f"{sample.get('outcomeA')} → {sample.get('outcomeB')}"
        )

    na = (bundle_a or {}).get("narrative") or {}
    nb = (bundle_b or {}).get("narrative") or {}
    if na.get("executiveSummary") and nb.get("executiveSummary"):
        eng_lines.append(f"Prior run summary: {na['executiveSummary'][:160]}…")
        eng_lines.append(f"Latest run summary: {nb['executiveSummary'][:160]}…")

    verdict = "neutral"
    if _readiness_rank(rb) > _readiness_rank(ra) and len(new_issues) <= len(resolved):
        verdict = "improved"
    elif _readiness_rank(rb) < _readiness_rank(ra) or len(new_issues) > len(resolved) + 2:
        verdict = "regressed"

    return {
        "headline": headline,
        "forFounders": "\n".join(founder_lines),
        "forEngineering": "\n".join(eng_lines),
        "verdict": verdict,
        "readinessDelta": readiness_delta,
        "source": "template",
        "suggestedQuestions": [
            f"Why did readiness move from {ra} to {rb}?",
            "Which new issue should we fix first?",
            "Did any flaky or changed steps drive the diff?",
        ],
    }


def _readiness_rank(band: str | None) -> int:
    order = {"Green": 3, "Amber": 2, "Red": 1}
    return order.get(str(band or ""), 0)


def build_compare_narrative(
    diff: dict[str, Any],
    *,
    bundle_a: dict[str, Any] | None = None,
    bundle_b: dict[str, Any] | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    template = build_template_compare_narrative(diff, bundle_a=bundle_a, bundle_b=bundle_b)
    if not use_llm:
        return template
    from rehearse.llm import generate_compare_narrative_llm, llm_enabled

    if not llm_enabled():
        return template
    llm_data = generate_compare_narrative_llm(diff, bundle_a=bundle_a, bundle_b=bundle_b, template=template)
    if not llm_data or llm_data.get("error"):
        template["llmNote"] = (llm_data or {}).get("error", "LLM unavailable")
        return template
    out = dict(template)
    out["source"] = "llm+template"
    for key in ("headline", "forFounders", "forEngineering", "verdict", "suggestedQuestions"):
        if llm_data.get(key):
            out[key] = llm_data[key]
    return out


def template_chat_reply(bundle: dict[str, Any], message: str) -> str:
    """Rule-based fallback when LLM chat is unavailable."""
    msg = message.lower().strip()
    summary = bundle.get("summary") or {}
    issues = bundle.get("issues") or []
    narrative = narrative_from_bundle(bundle) or {}

    if any(w in msg for w in ("blocker", "p1", "critical", "worst")):
        blockers = [i for i in issues if i.get("severity") in ("P0", "P1", "blocker")]
        if blockers:
            lines = [f"• {i.get('title')}: {i.get('detail', '')[:200]}" for i in blockers[:5]]
            return "Top blockers:\n" + "\n".join(lines)
        return "No P0/P1 blockers were recorded in this run."

    if any(w in msg for w in ("delight", "positive", "good")):
        delights = bundle.get("delights") or []
        if delights:
            return "Delights:\n" + "\n".join(
                f"• {d.get('title')}" for d in delights[:5]
            )
        return "No delights were recorded."

    if any(w in msg for w in ("readiness", "green", "amber", "red", "launch")):
        return (
            narrative.get("executiveSummary")
            or f"Readiness band: {summary.get('readinessBand', '?')} "
            f"(score {summary.get('readiness', '?')})."
        )

    if any(w in msg for w in ("summary", "overview", "explain", "what happened")):
        parts = [
            narrative.get("executiveSummary"),
            narrative.get("forFounders"),
        ]
        return "\n\n".join(p for p in parts if p) or "See the scorecard tab for full detail."

    return (
        "I can help with blockers, delights, readiness, or a run summary. "
        "Enable REHEARSE_LLM_API_KEY (or DEEPSEEK_API_KEY) for fuller natural-language answers."
    )


def _readiness_score(band: str | None) -> float:
    return {"Green": 85.0, "Amber": 72.0, "Red": 38.0}.get(str(band or ""), 50.0)


def build_template_trends_narrative(trends: dict[str, Any]) -> dict[str, Any]:
    """Plain-language trends across stored runs (NLU-3)."""
    readiness = trends.get("readiness") or []
    flake = trends.get("flakeRate") or []
    pages = trends.get("pages") or []
    blockers = trends.get("blockerCounts") or []
    recurrence = trends.get("issueRecurrence") or []
    run_ids = trends.get("runIds") or []

    n = len(readiness)
    if n == 0:
        return {
            "headline": "No rehearsal runs stored yet — run a crawl or full rehearsal first.",
            "forFounders": "Trends appear after your first scorecard is saved to artifacts.",
            "forEngineering": "POST /api/jobs or `./rehearse run` to populate launch-rehearsal/artifacts.",
            "verdict": "neutral",
            "source": "template",
            "suggestedQuestions": ["When should we schedule the first dogfood self-test?"],
        }

    latest_band = readiness[-1] if readiness else "?"
    prior_band = readiness[-2] if len(readiness) >= 2 else latest_band
    flake_latest = flake[-1] if flake else 0.0
    flake_prior = flake[-2] if len(flake) >= 2 else flake_latest
    flake_delta = round(flake_latest - flake_prior, 1) if len(flake) >= 2 else 0.0

    recurring = [r for r in recurrence if int(r.get("runs") or 0) >= 2]
    new_issues = trends.get("issuesOpened") or 0
    resolved = trends.get("issuesResolved") or 0

    headline_parts = [
        f"Across {n} run(s), latest readiness is **{latest_band}**",
    ]
    if len(readiness) >= 2 and latest_band != prior_band:
        headline_parts.append(f"(was {prior_band})")
    if len(flake) >= 2:
        direction = "rising" if flake_delta > 0.5 else "falling" if flake_delta < -0.5 else "stable"
        headline_parts.append(
            f"; flake rate {direction} ({flake_prior}% → {flake_latest}%)"
        )
    headline = " ".join(headline_parts) + "."

    founder_lines = [headline.replace("**", "")]
    if recurring:
        names = ", ".join(r.get("name", "?") for r in recurring[:3])
        founder_lines.append(f"Recurring themes: {names}.")
    if new_issues or resolved:
        founder_lines.append(
            f"Latest vs prior: {new_issues} new issue(s), {resolved} resolved."
        )
    if flake_delta > 2:
        founder_lines.append(
            "Flake rate is climbing — treat stability before widening partner demos."
        )
    elif flake_latest <= 2:
        founder_lines.append("Flake rate is low — good signal for repeatable rehearsals.")

    eng_lines = [
        f"Runs tracked: {', '.join(run_ids[-5:])}" if run_ids else f"{n} runs in artifacts",
    ]
    if pages:
        eng_lines.append(f"Crawl size: {pages[-2] if len(pages) >= 2 else '?'} → {pages[-1]} pages")
    if blockers:
        eng_lines.append(
            f"P0/P1 blockers latest run: {blockers[-1]} "
            f"(prior {blockers[-2] if len(blockers) >= 2 else '?'})"
        )
    if recurring:
        eng_lines.append(
            "Top recurrence: "
            + "; ".join(f"{r.get('name')} ({r.get('runs')}×)" for r in recurring[:4])
        )

    verdict = "neutral"
    if _readiness_score(latest_band) > _readiness_score(prior_band) and flake_delta <= 0:
        verdict = "improved"
    elif _readiness_score(latest_band) < _readiness_score(prior_band) or flake_delta > 3:
        verdict = "regressed"

    return {
        "headline": headline,
        "forFounders": "\n".join(founder_lines),
        "forEngineering": "\n".join(eng_lines),
        "verdict": verdict,
        "flakeDelta": flake_delta,
        "runCount": n,
        "source": "template",
        "suggestedQuestions": [
            "Which recurring issue should we fix first?",
            "Is flake rate noise or a real stability regression?",
            "Did crawl size growth expose new orphan routes?",
        ],
    }


def build_trends_narrative(trends: dict[str, Any], *, use_llm: bool = False) -> dict[str, Any]:
    template = build_template_trends_narrative(trends)
    if not use_llm:
        return template
    from rehearse.llm import generate_trends_narrative_llm, llm_enabled

    if not llm_enabled():
        return template
    llm_data = generate_trends_narrative_llm(trends, template=template)
    if not llm_data or llm_data.get("error"):
        template["llmNote"] = (llm_data or {}).get("error", "LLM unavailable")
        return template
    out = dict(template)
    out["source"] = "llm+template"
    for key in ("headline", "forFounders", "forEngineering", "verdict", "suggestedQuestions"):
        if llm_data.get(key):
            out[key] = llm_data[key]
    return out


def build_template_command_digest(
    summaries: list[dict[str, Any]],
    *,
    bundles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Cross-run digest for command center (NLU-5)."""
    if not summaries:
        return {
            "headline": "No runs yet.",
            "bullets": ["Start with Init → Dogfood or Runner → Run self-test."],
            "readinessTrend": "unknown",
            "source": "template",
        }
    latest = summaries[0]
    prior = summaries[1] if len(summaries) > 1 else None
    band = latest.get("readiness") or latest.get("readinessBand") or "?"
    bullets = [
        f"Latest `{latest.get('id')}`: **{band}** · {latest.get('issues', 0)} issues · "
        f"{latest.get('pages', 0)} pages",
    ]
    if prior:
        pb = prior.get("readiness") or prior.get("readinessBand")
        bullets.append(
            f"Prior `{prior.get('id')}`: {pb} · issues {prior.get('issues')} → {latest.get('issues')}"
        )
    bundles = bundles or []
    if bundles:
        narrative = (bundles[0] or {}).get("narrative") or {}
        if narrative.get("executiveSummary"):
            bullets.append(narrative["executiveSummary"][:220])
    trend = "stable"
    if prior and _readiness_score(band) > _readiness_score(prior.get("readiness")):
        trend = "improving"
    elif prior and _readiness_score(band) < _readiness_score(prior.get("readiness")):
        trend = "softening"
    return {
        "headline": f"Last {min(len(summaries), 7)} runs — newest is {band}.",
        "bullets": bullets[:6],
        "readinessTrend": trend,
        "latestRunId": latest.get("id"),
        "runCount": len(summaries),
        "source": "template",
    }


def build_command_digest(
    artifacts_root: Path,
    *,
    limit: int = 7,
    use_llm: bool = False,
) -> dict[str, Any]:
    from rehearse.dashboard.store import list_run_summaries, load_bundle

    summaries = list_run_summaries(artifacts_root)[:limit]
    bundles = [
        load_bundle(artifacts_root, s["id"], rebuild=False)
        for s in summaries[:3]
    ]
    bundles = [b for b in bundles if b]
    template = build_template_command_digest(summaries, bundles=bundles)
    if not use_llm:
        return template
    from rehearse.llm import generate_command_digest_llm, llm_enabled

    if not llm_enabled():
        return template
    llm_data = generate_command_digest_llm(summaries, bundles=bundles, template=template)
    if not llm_data or llm_data.get("error"):
        template["llmNote"] = (llm_data or {}).get("error", "LLM unavailable")
        return template
    out = dict(template)
    out["source"] = "llm+template"
    for key in ("headline", "bullets", "readinessTrend"):
        if llm_data.get(key):
            out[key] = llm_data[key]
    return out
