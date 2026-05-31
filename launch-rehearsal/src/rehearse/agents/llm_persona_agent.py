"""LLM persona agent — optional deep narrative analysis."""

from __future__ import annotations

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.llm import analyze_persona_llm, llm_enabled, llm_to_findings


class LLMPersonaAgent(BaseAgent):
    phase = "persona"

    def __init__(self, persona) -> None:
        self.persona = persona
        self.agent_id = f"llm-{persona.id}"
        self.agent_role = f"LLM evaluator: {persona.name}"

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary="LLM analysis skipped (no API key)",
        )
        if not llm_enabled() and not ctx.metadata.get("force_llm"):
            return report

        data = analyze_persona_llm(ctx, self.persona)
        if not data:
            report.summary = "LLM analysis unavailable"
            return report
        if data.get("error"):
            report.summary = data.get("summary", "LLM error")
            report.metadata = {"error": data.get("error")}
            return report

        findings, delights, grades = llm_to_findings(data, self.persona.id)
        report.findings = findings
        report.delights = delights
        report.journey_grades = {jid: {self.persona.id: st} for jid, st in grades.items()}
        report.summary = data.get("summary", f"LLM analysis for {self.persona.name}")
        from rehearse.llm import _model, llm_provider

        report.metadata = {
            "provider": llm_provider(),
            "model": _model(),
            "issues": len(findings),
            "delights": len(delights),
        }
        return report
