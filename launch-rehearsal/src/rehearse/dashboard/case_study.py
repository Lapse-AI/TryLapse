"""Auto-generated before/after case study — turns the outcome feedback loop
into a sales asset, not just a calibration mechanism.

Compares a workspace's earliest rehearsal against its latest, pairs the
latest with a recorded launch outcome when one exists, and renders a
shareable markdown one-pager. Needs at least two runs to say anything —
returns None otherwise rather than a thin, unconvincing "case study" off a
single run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _run_brief(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "runId": summary.get("id"),
        "readiness": summary.get("readiness"),
        "launchGate": summary.get("launchGate"),
        "blockers": summary.get("blockers", 0),
        "delights": summary.get("delights", 0),
        "startedAt": summary.get("startedAt"),
    }


def generate_case_study(artifacts_root: Path, workspace_slug: str) -> dict[str, Any] | None:
    """Build the before/after structure for a workspace, or None if there
    isn't yet a meaningful before/after to show (fewer than 2 runs)."""
    from rehearse.dashboard.store import list_run_summaries
    from rehearse.dashboard.outcome_store import list_outcomes

    summaries = list_run_summaries(artifacts_root, workspace_slug)
    if len(summaries) < 2:
        return None

    by_time = sorted(summaries, key=lambda s: s.get("startedAt") or "")
    before, after = by_time[0], by_time[-1]

    outcomes_by_run = {o["runId"]: o for o in list_outcomes(artifacts_root)}
    after_outcome = outcomes_by_run.get(after.get("id"))

    before_readiness = before.get("readiness") or 0
    after_readiness = after.get("readiness") or 0
    before_blockers = before.get("blockers") or 0
    after_blockers = after.get("blockers") or 0

    return {
        "workspaceSlug": workspace_slug,
        "productName": after.get("productName") or before.get("productName"),
        "before": _run_brief(before),
        "after": _run_brief(after),
        "readinessDelta": after_readiness - before_readiness,
        "blockersResolved": max(0, before_blockers - after_blockers),
        "totalRuns": len(summaries),
        "outcome": after_outcome,
    }


def render_case_study_markdown(case_study: dict[str, Any]) -> str:
    """Render a generate_case_study() result as a shareable markdown one-pager."""
    product = case_study.get("productName") or "this product"
    before, after = case_study["before"], case_study["after"]
    delta = case_study["readinessDelta"]
    delta_str = f"+{delta}" if delta > 0 else str(delta)
    outcome = case_study.get("outcome")

    lines = [
        f"# {product} — Launch Readiness, Before & After",
        "",
        f"Across **{case_study['totalRuns']} rehearsals**, readiness moved from "
        f"**{before['readiness']}** ({before['launchGate']}) to "
        f"**{after['readiness']}** ({after['launchGate']}) — a **{delta_str} point** change.",
        "",
        "| | Before | After |",
        "|---|---|---|",
        f"| Readiness | {before['readiness']} | {after['readiness']} |",
        f"| Launch gate | {before['launchGate']} | {after['launchGate']} |",
        f"| Blockers | {before['blockers']} | {after['blockers']} |",
        f"| Delights | {before['delights']} | {after['delights']} |",
        "",
    ]

    if case_study["blockersResolved"] > 0:
        lines.append(
            f"**{case_study['blockersResolved']} blocker"
            f"{'s' if case_study['blockersResolved'] != 1 else ''} resolved** between the first "
            "and most recent rehearsal."
        )
        lines.append("")

    if outcome:
        if outcome.get("launchSucceeded") is True:
            lines.append("✅ **The launch succeeded.**")
        elif outcome.get("launchSucceeded") is False:
            lines.append("⚠️ **The launch did not go as planned** — see notes below.")
        if outcome.get("notes"):
            lines.append("")
            lines.append(f"> {outcome['notes']}")
    else:
        lines.append(
            "_Launch outcome not yet recorded — this case study will update once it is._"
        )

    lines.append("")
    lines.append(f"Run IDs: `{before['runId']}` → `{after['runId']}`")
    return "\n".join(lines)
