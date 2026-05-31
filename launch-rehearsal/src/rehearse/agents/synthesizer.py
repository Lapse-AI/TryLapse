"""Synthesizer agent — merges multi-agent reports into unified analysis."""

from __future__ import annotations

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.heuristics import AnalysisResult, _overall_readiness


class SynthesizerAgent(BaseAgent):
    agent_id = "synthesizer"
    agent_role = "Cross-agent synthesis"
    phase = "synthesize"

    def execute(self, ctx: RunContext) -> AgentReport:
        from rehearse.heuristics import analyze_run

        base = analyze_run(ctx.config, ctx.evidence, sitemap=ctx.sitemap)

        # Merge persona-specific journey matrix
        matrix: dict[str, dict[str, str]] = {}
        for journey in ctx.config.journeys:
            matrix[journey.id] = {}
            for persona in ctx.config.personas:
                statuses = []
                for report in ctx.agent_reports:
                    if report.journey_grades.get(journey.id, {}).get(persona.id):
                        statuses.append(report.journey_grades[journey.id][persona.id])
                if statuses:
                    # Most pessimistic grade wins
                    if "fail" in statuses:
                        matrix[journey.id][persona.id] = "fail"
                    elif "partial" in statuses:
                        matrix[journey.id][persona.id] = "partial"
                    else:
                        matrix[journey.id][persona.id] = "pass"
                else:
                    matrix[journey.id][persona.id] = base.journey_matrix.get(journey.id, {}).get(persona.id, "pass")

        base.journey_matrix = matrix

        # Merge findings/delights from all agents (dedupe by title)
        seen_f: set[str] = {f.title for f in base.issues}
        seen_d: set[str] = {d.title for d in base.delights}
        for report in ctx.agent_reports:
            for f in report.findings:
                if f.title not in seen_f:
                    base.issues.append(f)
                    seen_f.add(f.title)
            for d in report.delights:
                if d.title not in seen_d:
                    base.delights.append(d)
                    seen_d.add(d.title)

        # Re-number issue/delight IDs
        for i, issue in enumerate(base.issues, 1):
            issue.id = f"I{i}"
        for i, delight in enumerate(base.delights, 1):
            delight.id = f"D{i}"

        base.readiness = _overall_readiness(base)
        if base.issues:
            base.top_blocker = base.issues[0].title
        if base.delights:
            base.top_delight = base.delights[0].title

        ctx.synthesis = base

        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary=f"Synthesized {len(base.issues)} issues, {len(base.delights)} delights from {len(ctx.agent_reports)} agent reports",
            findings=[],
            delights=[],
            metadata={
                "agents_merged": len(ctx.agent_reports),
                "readiness": base.readiness,
            },
        )
        return report
