"""Workflow detection from crawl graph — product-agnostic patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rehearse.sitemap import SiteMap

WORKFLOW_PATTERNS: dict[str, re.Pattern[str]] = {
    "authentication": re.compile(r"login|signin|sign-in|auth", re.I),
    "signup": re.compile(r"signup|sign-up|register|join", re.I),
    "pricing": re.compile(r"pricing|plans|billing|subscribe", re.I),
    "search": re.compile(r"search|find|query|discover", re.I),
    "admin": re.compile(r"admin|settings|manage|console", re.I),
    "dashboard": re.compile(r"dashboard|app|home|workspace", re.I),
    "documentation": re.compile(r"docs|documentation|help|guide", re.I),
    "integration": re.compile(r"integrat|api|webhook|connect", re.I),
}


@dataclass
class WorkflowNode:
    workflow_type: str
    path: str
    title: str
    confidence: float
    signals: list[str] = field(default_factory=list)


@dataclass
class WorkflowGraph:
    workflows: list[WorkflowNode] = field(default_factory=list)
    suggested_journeys: list[dict] = field(default_factory=list)

    def by_type(self, wtype: str) -> list[WorkflowNode]:
        return [w for w in self.workflows if w.workflow_type == wtype]


def detect_workflows(sitemap: SiteMap) -> WorkflowGraph:
    graph = WorkflowGraph()
    for page in sitemap.pages:
        blob = f"{page.path} {page.title} {page.h1}".lower()
        for wtype, pattern in WORKFLOW_PATTERNS.items():
            if pattern.search(blob):
                signals = []
                if page.form_count > 0:
                    signals.append(f"{page.form_count} forms")
                if page.input_count > 2:
                    signals.append(f"{page.input_count} inputs")
                if page.redirected_to_login:
                    signals.append("auth-gated")
                graph.workflows.append(
                    WorkflowNode(
                        workflow_type=wtype,
                        path=page.path,
                        title=page.title,
                        confidence=0.7 + (0.1 if signals else 0),
                        signals=signals,
                    )
                )

    # Build suggested E2E journeys from discovered workflows
    origin = sitemap.origin.rstrip("/")
    seen_types: set[str] = set()

    def add_journey(jid: str, name: str, path: str) -> None:
        graph.suggested_journeys.append(
            {
                "id": jid,
                "name": name,
                "steps": [{"action": "navigate", "url": f"{origin}{path}"}],
            }
        )

    priority = ["dashboard", "authentication", "pricing", "search", "admin", "documentation"]
    idx = 1
    for wtype in priority:
        nodes = graph.by_type(wtype)
        if not nodes or wtype in seen_types:
            continue
        seen_types.add(wtype)
        node = nodes[0]
        add_journey(f"auto-j{idx}-{wtype}", f"Auto: {wtype.replace('_', ' ').title()}", node.path)
        idx += 1

    # Hub exploration journey
    if sitemap.hub_paths:
        hub = sitemap.hub_paths[0]
        add_journey(f"auto-j{idx}-hub", "Auto: Navigation hub", hub)
        idx += 1

    # Fill to 5 with high-link pages not yet covered
    covered = {j["steps"][0]["url"] for j in graph.suggested_journeys}
    for page in sorted(sitemap.pages, key=lambda p: p.link_count, reverse=True):
        if len(graph.suggested_journeys) >= 5:
            break
        url = f"{origin}{page.path}"
        if url in covered:
            continue
        add_journey(f"auto-j{idx}-explore", f"Auto: Explore {page.path}", page.path)
        covered.add(url)
        idx += 1

    return graph
