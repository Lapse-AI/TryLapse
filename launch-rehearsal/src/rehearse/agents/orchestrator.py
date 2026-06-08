"""Multi-agent orchestration entrypoint."""

from __future__ import annotations

from pathlib import Path

from rehearse.agents.crawl_agent import CrawlAgent
from rehearse.agents.journey_agent import JourneyAgent
from rehearse.agents.llm_persona_agent import LLMPersonaAgent
from rehearse.agents.performance_agent import PerformanceAgent
from rehearse.agents.persona_agent import PersonaAgent
from rehearse.agents.synthesizer import SynthesizerAgent
from rehearse.agents.workflow_agent import WorkflowAgent
from rehearse.dsl import active_personas
from rehearse.llm import llm_enabled
from rehearse.dsl import active_personas
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
        lens_personas = active_personas(ctx.config)
        self._persona_agents = [PersonaAgent(p) for p in lens_personas]
        self._llm_agents: list[LLMPersonaAgent] = []
        if use_llm or llm_enabled():
            ctx.metadata["force_llm"] = use_llm
            self._llm_agents = [LLMPersonaAgent(p) for p in lens_personas]
        self._synthesizer = SynthesizerAgent()

    def run_crawl_phase(self) -> None:
        crawl_on = self.ctx.config.crawl and self.ctx.config.crawl.enabled
        if not crawl_on:
            return
        for agent in self._crawl_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))

        # Deep interactive crawl — buttons, forms, APIs, modals (runs after standard BFS)
        self._run_deep_crawl()

    def _run_deep_crawl(self) -> None:
        """Run exhaustive interactive discovery and feed into product intelligence."""
        try:
            from rehearse.deep_crawler import run_deep_crawl, interaction_map_to_dict, save_interaction_map
            from rehearse.product_intelligence import analyze_product, load_product_model, save_product_model

            page = self.ctx.metadata.get("page")
            if page is None:
                return
            target_url = self.ctx.config.target_url

            screenshots_dir = self.artifacts_root / "screenshots" / "discovery"
            imap = run_deep_crawl(
                page, target_url,
                product_name=self.ctx.config.product_name or "",
                max_pages=15,
                max_buttons_per_page=12,
                use_vision=True,
                screenshots_dir=screenshots_dir,
            )
            imap_dict = interaction_map_to_dict(imap)
            save_interaction_map(self.artifacts_root, self.ctx.evidence.run_id, imap)
            self.ctx.metadata["interaction_map"] = imap_dict

            # Always rebuild product model from fresh crawl data
            sitemap_pages = []
            if self.ctx.sitemap:
                sitemap_pages = [
                    {"path": p.path, "title": p.title, "type": p.page_type,
                     "linkCount": p.link_count, "formCount": p.form_count, "wordCount": p.word_count}
                    for p in self.ctx.sitemap.pages
                ]
            model = analyze_product(
                target_url,
                product_name=self.ctx.config.product_name or "",
                sitemap_pages=sitemap_pages,
                interaction_map=imap_dict,
                api_calls=imap.api_calls,
            )
            save_product_model(self.artifacts_root, model)
            self.ctx.metadata["product_model"] = model

            # Run per-persona journey discovery and store for behavioral judge
            product_model = self.ctx.metadata.get("product_model") or existing_model or {}
            if product_model and (llm_enabled() or self.ctx.metadata.get("force_llm")):
                from rehearse.persona_journey_discovery import discover_journeys_for_all_personas
                from rehearse.dsl import active_personas
                personas = [
                    {"id": p.id, "name": p.name, "role": p.role, "goals": list(p.goals)}
                    for p in active_personas(self.ctx.config)
                ]
                discoveries = discover_journeys_for_all_personas(personas, product_model)
                discovered: dict = {}
                for disc in discoveries:
                    pid = disc.get("persona_id", "")
                    if pid:
                        discovered[pid] = disc
                self.ctx.metadata["discovered_journeys"] = discovered
        except Exception:
            pass  # deep crawl is non-blocking — standard execution continues

    def run_journey_phase(self) -> None:
        self.ctx.agent_reports.append(self._journey_agent.execute(self.ctx))

    def run_analysis_phase(self) -> AnalysisResult:
        self.ctx.agent_reports.append(
            PerformanceAgent(self.artifacts_root).execute(self.ctx)
        )
        for agent in self._persona_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))
        for agent in self._llm_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))
        self.ctx.agent_reports.append(self._synthesizer.execute(self.ctx))
        assert self.ctx.synthesis is not None
        return self.ctx.synthesis
