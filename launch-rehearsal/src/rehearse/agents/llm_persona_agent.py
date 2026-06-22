"""LLM persona agent — optional deep narrative analysis."""

from __future__ import annotations

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.llm import analyze_persona_llm, llm_enabled, llm_to_findings, template_persona_analysis


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
        degraded = False
        llm_error: str | None = None
        if not data:
            data = template_persona_analysis(ctx, self.persona)
            degraded = True
            llm_error = "no_response"
        elif data.get("error"):
            llm_error = data.get("error")
            data = template_persona_analysis(ctx, self.persona)
            degraded = True

        findings, delights, grades = llm_to_findings(data, self.persona.id)
        report.findings = findings
        report.delights = delights
        report.journey_grades = {jid: {self.persona.id: st} for jid, st in grades.items()}
        report.summary = data.get("summary", f"LLM analysis for {self.persona.name}")
        from rehearse.llm import _model, llm_provider

        usage = data.pop("_usage", None) or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = input_tokens + output_tokens
        # Rough USD estimate (DeepSeek-class pricing ~$0.14/$0.28 per 1M tokens)
        cost_usd = (input_tokens * 0.14 + output_tokens * 0.28) / 1_000_000 if total_tokens else 0.0
        report.metadata = {
            "provider": "heuristic_fallback" if degraded else llm_provider(),
            "model": None if degraded else _model(),
            "degraded": degraded,
            "llmError": llm_error,
            "issues": len(findings),
            "delights": len(delights),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(cost_usd, 6),
            "duration_sec": 0,
        }
        return report
