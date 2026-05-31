"""Base agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rehearse.context import AgentReport, RunContext


class BaseAgent(ABC):
    agent_id: str = "base"
    agent_role: str = "base"
    phase: str = "analysis"  # crawl | journey | persona | synthesize

    @abstractmethod
    def execute(self, ctx: RunContext) -> AgentReport:
        ...
