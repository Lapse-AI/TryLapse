"""Markdown scorecard generator — enterprise-generic output."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rehearse.context import RunContext
from rehearse.dsl import RunConfig
from rehearse.evidence import RunEvidence
from rehearse.heuristics import AnalysisResult


def _persona_header(config: RunConfig, persona_id: str) -> str:
    for i, p in enumerate(config.personas, 1):
        if p.id == persona_id:
            return f"P{i} {p.name.split()[0]}"
    return persona_id


def render_scorecard(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    ctx: RunContext | None = None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = [
        f"# Launch Rehearsal — Scorecard",
        "",
        "| Field | Value |",
        "|-------|--------|",
        f"| **Run ID** | `{evidence.run_id}` |",
        f"| **Date** | {now} |",
        f"| **Target** | {config.target_url} |",
        f"| **Product** | {config.product_name} |",
        f"| **Outcome** | {evidence.outcome} |",
        f"| **Duration** | {evidence.duration_ms // 1000}s |",
        "",
        "---",
        "",
        "## Executive summary",
        "",
        "| | |",
        "|---|---|",
        f"| **Readiness** | **{analysis.readiness}** |",
        f"| **Top blocker** | {analysis.top_blocker or 'None detected'} |",
        f"| **Top delight** | {analysis.top_delight or 'None detected'} |",
        f"| **Issues** | {len(analysis.issues)} |",
        f"| **Delights** | {len(analysis.delights)} |",
        "",
    ]

    if ctx and ctx.sitemap:
        lines.extend(
            [
                f"| **Pages crawled** | {len(ctx.sitemap.pages)} |",
                f"| **Auto journeys added** | {len(ctx.auto_journey_ids)} |",
            ]
        )

    if evidence.auth_attempted:
        lines.append(f"| **Auth** | {evidence.auth_outcome} |")

    seeds = config.budgets.parallel_seeds if config.budgets else 1
    flaky_n = sum(1 for s in evidence.steps if s.flaky)
    if seeds > 1 or flaky_n:
        lines.append(f"| **Parallel seeds** | {seeds} |")
        lines.append(f"| **Flaky steps** | {flaky_n} |")

    lines.extend(["", "---", "", "## Persona × journey matrix", ""])
    persona_ids = [p.id for p in config.personas]
    header = "| Journey | " + " | ".join(_persona_header(config, pid) for pid in persona_ids) + " |"
    sep = "|---------|" + "|".join(["--------"] * len(persona_ids)) + "|"
    lines.extend([header, sep])
    journey_names = {j.id: j.name for j in config.journeys}
    for jid, row in analysis.journey_matrix.items():
        name = journey_names.get(jid, jid)
        cells = " | ".join(f"**{row.get(pid, '—').title()}**" for pid in persona_ids)
        lines.append(f"| **{jid}** {name[:30]} | {cells} |")

    if ctx and ctx.sitemap:
        lines.extend(["", "---", "", "## Site map (crawl)", ""])
        lines.append(ctx.sitemap.render_markdown())

    if ctx and ctx.workflows and ctx.workflows.workflows:
        lines.extend(["", "---", "", "## Detected workflows", ""])
        lines.append("| Type | Path | Title | Signals |")
        lines.append("|------|------|-------|---------|")
        for w in ctx.workflows.workflows[:20]:
            sig = ", ".join(w.signals) or "—"
            lines.append(f"| {w.workflow_type} | `{w.path}` | {w.title[:40]} | {sig} |")

    if ctx and ctx.agent_reports:
        lines.extend(["", "---", "", "## Multi-agent collaboration", ""])
        lines.append("| Agent | Role | Summary |")
        lines.append("|-------|------|---------|")
        for r in ctx.agent_reports:
            lines.append(f"| `{r.agent_id}` | {r.agent_role} | {r.summary[:80]} |")

    lines.extend(["", "---", "", "## Dimension rollup (automated subset)", ""])
    lines.extend(["| Dimension | Score 1–5 | Signal |", "|-----------|-----------|--------|"])
    for dim, (score, signal) in analysis.dimensions.items():
        lines.append(f"| {dim} | {score} | {signal} |")

    lines.extend(["", "---", "", "## Issues (evidence-bound)", ""])
    if not analysis.issues:
        lines.append("*No automated issues detected. Review artifacts manually.*")
    else:
        by_sev: dict[str, list] = {"P1": [], "P2": [], "P3": []}
        for issue in analysis.issues:
            by_sev.setdefault(issue.severity, []).append(issue)
        for sev in ("P1", "P2", "P3"):
            items = by_sev.get(sev) or []
            if not items:
                continue
            lines.append(f"### {sev}")
            lines.append("")
            lines.append("| ID | Finding | Personas | Evidence |")
            lines.append("|----|---------|----------|----------|")
            for item in items:
                personas = ", ".join(item.persona_ids)
                conf = f" ({item.confidence})" if item.confidence != "high" else ""
                lines.append(
                    f"| **{item.id}** | {item.title}{conf} — {item.detail} | {personas} | `{item.step_id}` |"
                )
            lines.append("")

    lines.extend(["---", "", "## Delights & strengths (required)", ""])
    if not analysis.delights:
        lines.append("*No automated delights detected. Manual review recommended.*")
    else:
        lines.append("| ID | Delight | Personas | Evidence |")
        lines.append("|----|---------|----------|----------|")
        for d in analysis.delights:
            lines.append(
                f"| **{d.id}** | {d.title} — {d.detail} | {', '.join(d.persona_ids)} | `{d.step_id}` |"
            )

    lines.extend(["", "---", "", "## Run log", ""])
    lines.append("| Step | Journey | Action | Outcome | URL |")
    lines.append("|------|---------|--------|---------|-----|")
    for step in evidence.steps:
        url = step.final_url or step.requested_url or "—"
        lines.append(
            f"| `{step.step_id}` | {step.journey_id} | {step.action} | {step.outcome} | {url[:60]} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "*Generated by Launch Rehearsal CLI — product-agnostic heuristics. "
            "Findings require human review before production decisions.*",
            "",
        ]
    )
    return "\n".join(lines)


def write_scorecard(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    output_dir: Path,
    ctx: RunContext | None = None,
) -> Path:
    md = render_scorecard(config, evidence, analysis, ctx=ctx)
    out = output_dir / "scorecards" / f"{evidence.run_id}-scorecard.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    return out
