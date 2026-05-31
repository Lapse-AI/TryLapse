"""Workflow agent — infer E2E patterns and supplement journeys."""

from __future__ import annotations

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.heuristics import Finding, Delight
from rehearse.journey_gen import supplement_journeys
from rehearse.workflows import detect_workflows


class WorkflowAgent(BaseAgent):
    agent_id = "workflow"
    agent_role = "Workflow & journey planning"
    phase = "crawl"

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary="No sitemap to analyze",
        )
        if not ctx.sitemap:
            return report

        ctx.workflows = detect_workflows(ctx.sitemap)
        types_found = sorted({w.workflow_type for w in ctx.workflows.workflows})

        if ctx.config.crawl and ctx.config.crawl.supplement_journeys:
            _, added = supplement_journeys(ctx.config, ctx.workflows)
            ctx.auto_journey_ids = added

        report.summary = f"Detected workflow types: {', '.join(types_found) or 'none'}"
        report.metadata = {
            "workflow_types": types_found,
            "suggested_journeys": len(ctx.workflows.suggested_journeys),
            "auto_journeys_added": ctx.auto_journey_ids,
        }

        if "authentication" not in types_found and ctx.sitemap.auth_gated_paths:
            report.findings.append(
                Finding(
                    id="W1",
                    severity="P2",
                    title="Auth-gated routes without login surface in crawl",
                    detail="Some paths redirect to login but no /login-style route was classified — wayfinding gap.",
                    persona_ids=[ctx.config.personas[0].id],
                    step_id="workflow-graph",
                )
            )

        if len(types_found) >= 3:
            report.delights.append(
                Delight(
                    id="W-D1",
                    title="Multi-workflow product surface",
                    detail=f"Discovered workflow types: {', '.join(types_found)}.",
                    persona_ids=[p.id for p in ctx.config.personas],
                    step_id="workflow-graph",
                )
            )

        missing = [t for t in ("pricing", "documentation") if t not in types_found]
        if missing and ctx.config.crawl and ctx.config.crawl.strict_enterprise:
            report.findings.append(
                Finding(
                    id="W2",
                    severity="P3",
                    title="Expected enterprise paths not found in crawl",
                    detail=f"No crawl match for: {', '.join(missing)}.",
                    persona_ids=[ctx.config.personas[-1].id],
                    step_id="workflow-graph",
                    confidence="hypothesis",
                )
            )

        return report
