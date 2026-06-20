"""Merge crawl-discovered workflows into executable journeys."""

from __future__ import annotations

from rehearse.dsl import Journey, RunConfig, Step
from rehearse.workflows import WorkflowGraph


def supplement_journeys(config: RunConfig, graph: WorkflowGraph) -> tuple[RunConfig, list[str]]:
    """Add auto-discovered journeys without removing config-defined ones.

    Auto-added journeys have no persona_ids, so they run for every enabled
    persona (see active_personas() filtering). Once the config already has
    persona-scoped journeys, that signals deliberate curation — supplementing
    more generic, persona-agnostic journeys on top would silently run extra
    untargeted work for every persona, which is surprising rather than helpful.
    """
    if any(j.persona_ids for j in config.journeys):
        return config, []

    existing_urls = set()
    for j in config.journeys:
        for s in j.steps:
            if s.url:
                existing_urls.add(s.url.rstrip("/"))

    added_ids: list[str] = []
    for raw in graph.suggested_journeys:
        url = raw["steps"][0]["url"].rstrip("/")
        if url in existing_urls:
            continue
        jid = raw["id"]
        if any(j.id == jid for j in config.journeys):
            continue
        config.journeys.append(
            Journey(
                id=jid,
                name=raw["name"],
                steps=[Step(action=s["action"], url=s.get("url")) for s in raw["steps"]],
            )
        )
        existing_urls.add(url)
        added_ids.append(jid)

    return config, added_ids
