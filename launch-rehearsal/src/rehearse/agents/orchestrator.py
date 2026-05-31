"""Multi-agent orchestration entrypoint."""

from __future__ import annotations

from pathlib import Path

from rehearse.agents.crawl_agent import CrawlAgent
from rehearse.agents.journey_agent import JourneyAgent
from rehearse.agents.llm_persona_agent import LLMPersonaAgent
from rehearse.agents.persona_agent import PersonaAgent
from rehearse.agents.synthesizer import SynthesizerAgent
from rehearse.agents.workflow_agent import WorkflowAgent
from rehearse.llm import llm_enabled
from rehearse.browser import BrowserSession
from rehearse.context import RunContext
from rehearse.heuristics import AnalysisResult


class AgentOrchestrator:
    def __init__(
        self,
        ctx: RunContext,
        session: BrowserSession,
        artifacts_root: Path,
        *,
        use_llm: bool = False,
    ) -> None:
        self.ctx = ctx
        self.session = session
        self.artifacts_root = artifacts_root
        self._crawl_agents = [CrawlAgent(), WorkflowAgent()]
        self._journey_agent = JourneyAgent(session, artifacts_root)
        self._persona_agents = [PersonaAgent(p) for p in ctx.config.personas]
        self._llm_agents: list[LLMPersonaAgent] = []
        if use_llm or llm_enabled():
            ctx.metadata["force_llm"] = use_llm
            self._llm_agents = [LLMPersonaAgent(p) for p in ctx.config.personas]
        self._synthesizer = SynthesizerAgent()

    def run_crawl_phase(self) -> None:
        crawl_on = self.ctx.config.crawl and self.ctx.config.crawl.enabled
        if not crawl_on:
            return
        for agent in self._crawl_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))

    def run_journey_phase(self) -> None:
        self.ctx.agent_reports.append(self._journey_agent.execute(self.ctx))

    def run_analysis_phase(self) -> AnalysisResult:
        for agent in self._persona_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))
        for agent in self._llm_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))
        self.ctx.agent_reports.append(self._synthesizer.execute(self.ctx))
        assert self.ctx.synthesis is not None
        return self.ctx.synthesis
