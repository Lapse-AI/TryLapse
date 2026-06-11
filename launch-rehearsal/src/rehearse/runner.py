"""Orchestrate multi-agent crawl, journeys, analysis, and scorecard."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from rehearse.agents.orchestrator import AgentOrchestrator
from rehearse.browser import BrowserSession
from rehearse.context import RunContext
from rehearse.dsl import RunConfig
from rehearse.evidence import RunEvidence, StepSnapshot, new_run_id
from rehearse.heuristics import analyze_run
from rehearse.scorecard import write_scorecard


def run_rehearsal(
    config: RunConfig,
    *,
    output_dir: Path,
    dry_run: bool = False,
    use_llm: bool = False,
    config_path: Path | None = None,
    run_id: str | None = None,
) -> tuple[RunEvidence, Path | None, RunContext | None]:
    run_id = run_id or new_run_id(config.run_id_prefix)
    started = time.perf_counter()
    deadline = started + config.budgets.max_run_seconds

    evidence = RunEvidence(
        run_id=run_id,
        target_url=config.target_url,
        product_name=config.product_name,
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    if dry_run:
        primary_persona = config.personas[0].id
        for journey in config.journeys:
            for i, step in enumerate(journey.steps):
                evidence.add_step(
                    StepSnapshot(
                        step_id=f"{journey.id}-{primary_persona}-s{i+1}",
                        journey_id=journey.id,
                        journey_name=journey.name,
                        persona_id=primary_persona,
                        action=step.action,
                        requested_url=step.url,
                        outcome="skipped",
                        note="dry-run: browser not invoked",
                    )
                )
        evidence.outcome = "dry_run_complete"
        evidence.duration_ms = int((time.perf_counter() - started) * 1000)
        evidence.save(output_dir / "runs")
        return evidence, None, None

    artifacts_root = output_dir / "artifacts" / run_id
    ctx = RunContext(config=config, evidence=evidence)
    ctx.metadata = {"output_dir": str(output_dir), "deadline": deadline}

    # Live progress tracker — written to runs/{run_id}-progress.json
    from rehearse.progress import ProgressTracker
    tracker = ProgressTracker(output_dir, run_id)
    tracker.set_config(
        config_id=config.run_id_prefix,
        product_name=config.product_name,
        target_url=config.target_url,
    )
    personas_data = [{"id": p.id, "name": p.name} for p in config.personas]
    journeys_per_persona = {
        p.id: [
            {"id": j.id, "name": j.name, "steps": [{"action": s.action, "intent": s.intent or s.url or ""} for s in j.steps]}
            for j in config.journeys
            if not j.persona_ids or p.id in j.persona_ids
        ]
        for p in config.personas
    }
    tracker.set_personas(personas_data, journeys_per_persona)
    tracker.set_phase("crawling")
    ctx.metadata["progress_tracker"] = tracker

    # Enable video recording for journey execution
    with BrowserSession(config, artifacts_root, record_video=True) as session:
        ctx.metadata["page"] = session.page

        if config.auth:
            evidence.auth_attempted = True
            evidence.auth_outcome = session.perform_auth(config.auth)
            # Capture auth cookies so parallel journey workers can reuse the session
            if evidence.auth_outcome and "success" in (evidence.auth_outcome or ""):
                try:
                    ctx.metadata["auth_storage_state"] = session.page.context.storage_state()
                except Exception:
                    pass

        orchestrator = AgentOrchestrator(ctx, session, artifacts_root, use_llm=use_llm)
        orchestrator.run_crawl_phase()
        tracker.set_phase("executing")
        orchestrator.run_journey_phase()
        tracker.set_phase("analysing")
        net_path = session.flush_network_log()
        if net_path:
            evidence.network_log_path = net_path
            ctx.metadata["network_log_path"] = net_path
        analysis = orchestrator.run_analysis_phase()

        from rehearse.narrative import build_run_narrative

        ctx.metadata["narrative"] = build_run_narrative(
            config, evidence, analysis, ctx=ctx, use_llm=use_llm
        )

    evidence.finished_at = datetime.now(timezone.utc).isoformat()
    evidence.duration_ms = int((time.perf_counter() - started) * 1000)
    evidence.outcome = "complete"
    evidence.save(output_dir / "runs")
    tracker.finish()

    scorecard_path = write_scorecard(config, evidence, analysis, output_dir, ctx=ctx)
    from rehearse.analysis_export import build_run_bundle, write_analysis_bundle

    scorecard_md = scorecard_path.read_text() if scorecard_path else None
    crawl_on = config.crawl and config.crawl.enabled
    bundle = build_run_bundle(
        config,
        evidence,
        analysis,
        output_dir,
        ctx=ctx,
        scorecard_md=scorecard_md,
        llm_enabled=use_llm,
        crawl_enabled=bool(crawl_on),
    )
    if config_path and config_path.is_file():
        bundle["summary"]["configId"] = config_path.stem
    config_yaml = config_path.read_text() if config_path and config_path.is_file() else None
    write_analysis_bundle(bundle, output_dir, config_yaml=config_yaml)
    return evidence, scorecard_path, ctx
