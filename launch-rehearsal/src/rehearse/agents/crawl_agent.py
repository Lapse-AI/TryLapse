"""Crawl agent — discovers site structure before journey execution."""

from __future__ import annotations

from pathlib import Path

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.crawler import crawl_site
from rehearse.heuristics import Finding
from rehearse.sitemap import SiteMap


class CrawlAgent(BaseAgent):
    agent_id = "crawler"
    agent_role = "Site structure discovery"
    phase = "crawl"

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary="Crawl skipped",
        )
        crawl_cfg = ctx.config.crawl
        if not crawl_cfg or not crawl_cfg.enabled:
            return report

        page = ctx.metadata.get("page")  # type: ignore[attr-defined]
        if page is None:
            report.summary = "No browser page available for crawl"
            return report

        pages = crawl_site(
            page,
            ctx.config.target_url,
            crawl_cfg,
            timeout_ms=ctx.config.budgets.step_timeout_ms,
        )
        ctx.sitemap = SiteMap.from_pages(ctx.config.target_url, pages)
        run_id = ctx.evidence.run_id
        out_base = Path(ctx.metadata.get("output_dir", "artifacts"))  # type: ignore[attr-defined]
        ctx.sitemap.save_json(out_base / "sitemaps" / f"{run_id}-sitemap.json")
        ctx.sitemap.save_markdown(out_base / "sitemaps" / f"{run_id}-sitemap.md")

        report.summary = (
            f"Crawled {len(pages)} pages; "
            f"{len(ctx.sitemap.auth_gated_paths)} auth-gated; "
            f"{len(ctx.sitemap.orphan_paths)} orphans"
        )
        report.metadata = {
            "page_count": len(pages),
            "hub_paths": ctx.sitemap.hub_paths[:5],
        }

        if ctx.sitemap.orphan_paths:
            report.findings.append(
                Finding(
                    id="C1",
                    severity="P2",
                    title="Orphan pages in crawl graph",
                    detail=f"{len(ctx.sitemap.orphan_paths)} pages had no inbound links from crawl (may be hard to discover).",
                    persona_ids=[ctx.config.personas[0].id],
                    step_id="crawl-graph",
                    confidence="high",
                )
            )
        if len(pages) >= crawl_cfg.max_pages:
            report.findings.append(
                Finding(
                    id="C2",
                    severity="P3",
                    title="Crawl budget reached",
                    detail=f"Stopped at max_pages={crawl_cfg.max_pages}; site may be larger.",
                    persona_ids=[ctx.config.personas[-1].id],
                    step_id="crawl-graph",
                    confidence="high",
                )
            )
        return report
