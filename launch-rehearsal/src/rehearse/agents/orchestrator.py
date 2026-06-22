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
        self._analyzed_personas: set[str] = set()  # personas already processed in streaming mode

    def run_crawl_phase(self) -> None:
        crawl_on = self.ctx.config.crawl and self.ctx.config.crawl.enabled
        if not crawl_on:
            return
        for agent in self._crawl_agents:
            self.ctx.agent_reports.append(agent.execute(self.ctx))

        # Deep interactive crawl — buttons, forms, APIs, modals (runs after standard BFS)
        self._run_deep_crawl()

        # Passive security surface scan (non-blocking)
        self._run_security_scan()

    def _run_deep_crawl(self) -> None:
        """Run exhaustive interactive discovery and feed into product intelligence."""
        try:
            from rehearse.deep_crawler import (
                run_deep_crawl, interaction_map_to_dict, save_interaction_map,
                extend_destructive_keywords,
            )
            from rehearse.product_intelligence import analyze_product, load_product_model, save_product_model

            page = self.ctx.metadata.get("page")
            if page is None:
                return
            target_url = self.ctx.config.target_url

            # Workspace-level guardrails — extra keywords a customer wants
            # blocked beyond the built-in destructive-action list (e.g. their
            # own product's "downgrade", "terminate account" labels). Opt-in
            # only; never pre-loaded with payment terms since many products'
            # real journeys legitimately test checkout.
            try:
                import json as _json
                workspace_path = self.artifacts_root.parent.parent / "workspace.json"
                if workspace_path.is_file():
                    ws = _json.loads(workspace_path.read_text())
                    extra = (ws.get("guardrails") or {}).get("extraBlockedKeywords") or []
                    if extra:
                        extend_destructive_keywords(extra)
            except Exception:
                pass

            screenshots_dir = self.artifacts_root / "screenshots" / "discovery"
            run_id = self.ctx.evidence.run_id
            # Write crawl graph to server-root/runs/ (same location as progress + evidence files)
            # artifacts_root = output_dir / "artifacts" / run_id  →  parent.parent = output_dir
            server_runs_dir = self.artifacts_root.parent.parent / "runs"
            graph_path = server_runs_dir / f"{run_id}-crawl-graph.json"
            imap = run_deep_crawl(
                page, target_url,
                product_name=self.ctx.config.product_name or "",
                max_pages=40,
                max_buttons_per_page=12,
                use_vision=True,
                screenshots_dir=screenshots_dir,
                graph_output_path=graph_path,
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
                discoveries = discover_journeys_for_all_personas(
                    personas, product_model, interaction_map=imap_dict
                )
                discovered: dict = {}
                for disc in discoveries:
                    pid = disc.get("persona_id", "")
                    if pid:
                        discovered[pid] = disc
                self.ctx.metadata["discovered_journeys"] = discovered
        except Exception:
            pass  # deep crawl is non-blocking — standard execution continues

    def _run_security_scan(self) -> None:
        """Passive one-time security surface scan — uses the current page state."""
        try:
            from rehearse.security import scan_security_surface
            from rehearse.context import AgentReport

            page = self.ctx.metadata.get("page")
            if page is None:
                return

            findings = scan_security_surface(page, self.ctx.config)
            if findings:
                report = AgentReport(
                    agent_id="security-scanner",
                    agent_role="Security surface scan",
                    summary=f"Security scan found {len(findings)} issue(s)",
                    findings=findings,
                    delights=[],
                    metadata={"scan_type": "passive"},
                )
                self.ctx.agent_reports.append(report)
        except Exception:
            pass  # non-blocking

    def run_journey_phase(self) -> None:
        from rehearse.dsl import active_personas

        run_all = self.ctx.config.execute_all_personas_in_browser
        enabled = active_personas(self.ctx.config)
        personas = (
            enabled if (run_all is None or run_all)
            else enabled[:1]
        )
        workers = self.ctx.config.budgets.parallel_journeys

        # Streaming only helps in multi-persona sequential mode. Parallel mode
        # has no ordering guarantee so all personas must finish before synthesis.
        if len(personas) <= 1 or workers > 1:
            self.ctx.agent_reports.append(self._journey_agent.execute(self.ctx))
            return

        output_dir = Path(self.ctx.metadata.get("output_dir", "."))
        total = len(personas)
        for i, persona in enumerate(personas):
            report = self._journey_agent.execute_for_persona(self.ctx, persona.id)
            self.ctx.agent_reports.append(report)

            # Immediately analyze this persona's evidence while the next persona runs
            for agent in self._persona_agents:
                if agent.persona.id == persona.id:
                    self.ctx.agent_reports.append(agent.execute(self.ctx))
                    self._analyzed_personas.add(persona.id)
            for agent in self._llm_agents:
                if agent.persona.id == persona.id:
                    self.ctx.agent_reports.append(agent.execute(self.ctx))

            # Write partial bundle so the dashboard shows early findings
            if i < total - 1:
                self._write_partial_bundle(output_dir, personas_complete=i + 1, total=total)

    def run_analysis_phase(self) -> AnalysisResult:
        self.ctx.agent_reports.append(
            PerformanceAgent(self.artifacts_root).execute(self.ctx)
        )
        # Skip persona/LLM agents already fired in streaming journey phase
        for agent in self._persona_agents:
            if agent.persona.id not in self._analyzed_personas:
                self.ctx.agent_reports.append(agent.execute(self.ctx))
        for agent in self._llm_agents:
            if agent.persona.id not in self._analyzed_personas:
                self.ctx.agent_reports.append(agent.execute(self.ctx))
        self.ctx.agent_reports.append(self._synthesizer.execute(self.ctx))
        assert self.ctx.synthesis is not None
        return self.ctx.synthesis

    def _write_partial_bundle(self, output_dir: Path, personas_complete: int, total: int) -> None:
        """Write a partial analysis bundle after each persona completes in streaming mode.

        The dashboard polls the analysis/{run_id}.json file — this gives users
        early signal on P0/P1 findings from persona 1 before persona 2 finishes.
        The final bundle always overwrites this file when synthesis completes.
        """
        import json
        from rehearse.analysis_export import build_run_bundle
        from rehearse.heuristics import analyze_run
        from rehearse.agents.synthesizer import _is_duplicate, _load_embedder

        try:
            partial_analysis = analyze_run(
                self.ctx.config, self.ctx.evidence, sitemap=self.ctx.sitemap
            )
            embedder = _load_embedder()
            existing_titles = [f.title for f in partial_analysis.issues]
            for rep in self.ctx.agent_reports:
                for f in rep.findings:
                    if not _is_duplicate(f.title, existing_titles, embedder):
                        partial_analysis.issues.append(f)
                        existing_titles.append(f.title)
            for idx, issue in enumerate(partial_analysis.issues, 1):
                issue.id = f"I{idx}"

            bundle = build_run_bundle(
                self.ctx.config, self.ctx.evidence, partial_analysis, output_dir, ctx=self.ctx
            )
            bundle["summary"]["partial"] = True
            bundle["summary"]["personasComplete"] = personas_complete
            bundle["summary"]["personasTotal"] = total

            analysis_dir = output_dir / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            run_id = self.ctx.evidence.run_id
            (analysis_dir / f"{run_id}.json").write_text(json.dumps(bundle, indent=2))
        except Exception:
            pass  # non-blocking; final bundle always overwrites
