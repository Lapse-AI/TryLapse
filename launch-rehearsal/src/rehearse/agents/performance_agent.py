"""Performance agent — Web Vitals on last navigate per journey."""

from __future__ import annotations

import json
from pathlib import Path

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.heuristics import Finding, _canonical_steps, _pick_personas
from rehearse.web_vitals import vitals_issues


class PerformanceAgent(BaseAgent):
    agent_id = "performance-v1"
    agent_role = "Web Vitals (lab)"
    phase = "analysis"

    def __init__(self, artifacts_root: Path) -> None:
        self.artifacts_root = artifacts_root

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary="Web Vitals collection",
        )
        canonical = _canonical_steps(ctx.evidence.steps)
        by_journey: dict[str, list] = {}
        for step in canonical:
            by_journey.setdefault(step.journey_id, []).append(step)

        summary: dict[str, dict] = {}
        poor_journeys: list[str] = []

        for journey_id, steps in by_journey.items():
            nav_steps = [s for s in steps if s.action == "navigate"]
            if not nav_steps:
                continue
            last = nav_steps[-1]
            vitals = getattr(last, "web_vitals", None) or {}
            if not vitals:
                continue
            summary[journey_id] = {
                "stepId": last.step_id,
                "finalUrl": last.final_url,
                "viewport": getattr(last, "viewport", "desktop"),
                "vitals": vitals,
                "issues": vitals_issues(vitals),
            }
            if summary[journey_id]["issues"]:
                poor_journeys.append(journey_id)

        if summary:
            path = self.artifacts_root / "web-vitals.json"
            path.write_text(json.dumps(summary, indent=2))
            report.metadata["web_vitals_path"] = str(path)
            report.metadata["web_vitals_by_journey"] = summary

        if poor_journeys:
            p_power = _pick_personas(ctx.config, "operator", "power", "daily")
            for jid in poor_journeys:
                issues = summary[jid]["issues"]
                report.findings.append(
                    Finding(
                        id=f"perf-{jid}",
                        severity="P2",
                        title=f"Poor Web Vitals on {jid}",
                        detail="; ".join(issues),
                        persona_ids=p_power,
                        step_id=summary[jid]["stepId"],
                        confidence="high",
                    )
                )
            report.summary = f"Web Vitals issues on {len(poor_journeys)} journey(s)"
        else:
            report.summary = (
                f"Web Vitals captured for {len(summary)} journey(s); no threshold breaches"
                if summary
                else "No navigate steps with vitals"
            )

        ctx.metadata["web_vitals_by_journey"] = summary
        return report
