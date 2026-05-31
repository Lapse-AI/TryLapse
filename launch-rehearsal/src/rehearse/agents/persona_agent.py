"""Persona agent — evaluates evidence from a specific user lens."""

from __future__ import annotations

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.dsl import Persona
from rehearse.heuristics import Delight, Finding, _journey_status


class PersonaAgent(BaseAgent):
    phase = "persona"

    def __init__(self, persona: Persona) -> None:
        self.persona = persona
        self.agent_id = f"persona-{persona.id}"
        self.agent_role = f"Evaluator: {persona.name} ({persona.role})"

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary=f"Analysis from {self.persona.role} perspective",
        )

        role = self.persona.role.lower()
        goals = " ".join(self.persona.goals).lower()

        # Re-grade journeys for this persona lens
        by_journey: dict[str, list] = {}
        for step in ctx.evidence.steps:
            by_journey.setdefault(step.journey_id, []).append(step)

        for jid, steps in by_journey.items():
            status = _journey_status(steps)
            if "admin" in role or "it" in role:
                if any(s.network_failures for s in steps):
                    status = "partial" if status == "pass" else status
                if ctx.sitemap and ctx.sitemap.auth_gated_paths and jid.startswith("auto-j") and "admin" in jid:
                    status = "partial"
            if "first" in role or "prospect" in role or "evaluator" in role:
                if any(len(s.body_text_excerpt) < 100 for s in steps if s.action == "navigate"):
                    status = "partial" if status == "pass" else status
            if "operator" in role or "power" in role or "daily" in role:
                if any(s.duration_ms > 6000 for s in steps):
                    status = "partial" if status == "pass" else status
                if any(s.unlabeled_button_count > 2 for s in steps):
                    status = "partial" if status == "pass" else status
            report.journey_grades[jid] = {self.persona.id: status}

        # Persona-specific findings from crawl
        if ctx.sitemap:
            if ("admin" in role or "buyer" in role) and ctx.sitemap.error_paths:
                report.findings.append(
                    Finding(
                        id=f"PA-{self.persona.id[:4]}-1",
                        severity="P2",
                        title="Error paths reachable in crawl",
                        detail=f"Paths with errors: {', '.join(ctx.sitemap.error_paths[:5])}",
                        persona_ids=[self.persona.id],
                        step_id="crawl-graph",
                    )
                )
            if ("first" in role or "prospect" in role) and ctx.sitemap.orphan_paths:
                report.findings.append(
                    Finding(
                        id=f"PA-{self.persona.id[:4]}-2",
                        severity="P3",
                        title="Hidden pages for new users",
                        detail="Orphan pages may be unreachable without direct links.",
                        persona_ids=[self.persona.id],
                        step_id="crawl-graph",
                        confidence="hypothesis",
                    )
                )

        # Goal-aligned delight
        if "efficient" in goals or "quick" in goals:
            fast = [s for s in ctx.evidence.steps if s.duration_ms < 3000 and s.outcome == "pass"]
            if len(fast) >= 3:
                report.delights.append(
                    Delight(
                        id=f"PD-{self.persona.id[:4]}-1",
                        title="Fast interactions for repeat tasks",
                        detail=f"{len(fast)} steps completed under 3s.",
                        persona_ids=[self.persona.id],
                        step_id=fast[0].step_id,
                    )
                )

        report.metadata = {"persona_id": self.persona.id, "journeys_graded": len(report.journey_grades)}
        return report
