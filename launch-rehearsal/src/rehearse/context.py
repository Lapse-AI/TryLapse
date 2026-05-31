"""Shared run context for multi-agent collaboration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rehearse.dsl import RunConfig
from rehearse.evidence import RunEvidence
from rehearse.heuristics import AnalysisResult, Delight, Finding
from rehearse.sitemap import SiteMap
from rehearse.workflows import WorkflowGraph


@dataclass
class AgentReport:
    agent_id: str
    agent_role: str
    summary: str
    findings: list[Finding] = field(default_factory=list)
    delights: list[Delight] = field(default_factory=list)
    journey_grades: dict[str, dict[str, str]] = field(default_factory=dict)  # journey -> persona -> status
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunContext:
    config: RunConfig
    evidence: RunEvidence
    sitemap: SiteMap | None = None
    workflows: WorkflowGraph | None = None
    agent_reports: list[AgentReport] = field(default_factory=list)
    synthesis: AnalysisResult | None = None
    auto_journey_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
