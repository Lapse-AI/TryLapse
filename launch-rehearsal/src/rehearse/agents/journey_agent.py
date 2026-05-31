"""Journey agent — executes E2E steps in browser with optional parallel seeds."""

from __future__ import annotations

import time
from pathlib import Path

from rehearse.agents.base import BaseAgent
from rehearse.browser import BrowserSession
from rehearse.context import AgentReport, RunContext
from rehearse.dsl import Journey, Step
from rehearse.errors import RunBudgetExceeded
from rehearse.evidence import StepSnapshot


def _replay_journey_from_start(
    session: BrowserSession,
    journey: Journey,
    *,
    primary: str,
    seed: int,
    loop: int,
    artifacts_root: Path,
    deadline: float,
    ctx: RunContext,
) -> list[StepSnapshot]:
    """Run all steps for one journey; return snapshots for this seed/loop."""
    config = ctx.config
    timeout = config.budgets.step_timeout_ms
    snaps: list[StepSnapshot] = []

    for i, step in enumerate(journey.steps):
        if time.perf_counter() > deadline:
            raise RunBudgetExceeded("max_run_seconds exceeded")
        step_id = f"{journey.id}-{primary}-s{i+1}-seed{seed}-loop{loop}"
        snap = session.execute_step(
            step,
            step_id=step_id,
            journey_id=journey.id,
            journey_name=journey.name,
            persona_id=primary,
        )
        snap.seed_index = seed
        snaps.append(snap)
        ctx.evidence.add_step(snap)

        if step.action == "navigate" and step.url and i == 0 and seed > 1:
            pass
    return snaps


def _navigate_journey_entry(session: BrowserSession, journey: Journey) -> None:
    """Reset to first navigate URL between seeds."""
    first_nav = next((s for s in journey.steps if s.action == "navigate" and s.url), None)
    if first_nav and first_nav.url:
        session.page.goto(
            first_nav.url,
            wait_until="domcontentloaded",
            timeout=session.config.budgets.step_timeout_ms,
        )
        session.page.wait_for_timeout(500)


def _mark_flaky_steps(seed_runs: list[list[StepSnapshot]]) -> None:
    if len(seed_runs) < 2:
        return
    step_count = len(seed_runs[0])
    for idx in range(step_count):
        outcomes = {seed_runs[s][idx].outcome for s in range(len(seed_runs))}
        if len(outcomes) > 1:
            for run in seed_runs:
                run[idx].flaky = True
                note = run[idx].note or ""
                run[idx].note = f"FLAKY: outcomes differ across seeds ({', '.join(sorted(outcomes))}). {note}".strip()


def _journey_status_from_snaps(snaps: list[StepSnapshot]) -> str:
    if any(s.outcome == "fail" for s in snaps):
        return "fail"
    if any(s.outcome == "partial" for s in snaps):
        return "partial"
    if any(s.flaky for s in snaps):
        return "partial"
    return "pass"


class JourneyAgent(BaseAgent):
    agent_id = "journey-runner"
    agent_role = "E2E journey execution"
    phase = "journey"

    def __init__(self, session: BrowserSession, artifacts_root: Path) -> None:
        self.session = session
        self.artifacts_root = artifacts_root
        self._deadline: float = 0

    def _run_journey_once(
        self,
        ctx: RunContext,
        journey: Journey,
        *,
        primary: str,
        seed: int,
        loop: int,
    ) -> list[StepSnapshot]:
        if seed > 1 or loop > 1:
            _navigate_journey_entry(self.session, journey)
        return _replay_journey_from_start(
            self.session,
            journey,
            primary=primary,
            seed=seed,
            loop=loop,
            artifacts_root=self.artifacts_root,
            deadline=self._deadline,
            ctx=ctx,
        )

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary="Journey execution",
        )
        self._deadline = ctx.metadata.get("deadline", time.perf_counter() + 9999)
        primary = ctx.config.personas[0].id
        seeds = ctx.config.budgets.parallel_seeds
        loops = ctx.config.budgets.repeat_micro_loop
        executed = 0
        failed = 0
        flaky_count = 0

        for journey in ctx.config.journeys:
            per_journey_budget = len(journey.steps) * seeds * loops
            if per_journey_budget > ctx.config.budgets.max_steps_per_journey:
                raise RunBudgetExceeded(
                    f"Journey {journey.id} exceeds step budget "
                    f"({per_journey_budget} > {ctx.config.budgets.max_steps_per_journey})"
                )

        for journey in ctx.config.journeys:
            seed_runs: list[list[StepSnapshot]] = []
            for loop in range(1, loops + 1):
                for seed in range(1, seeds + 1):
                    snaps = self._run_journey_once(ctx, journey, primary=primary, seed=seed, loop=loop)
                    seed_runs.append(snaps)
                    executed += len(snaps)
                    failed += sum(1 for s in snaps if s.outcome == "fail")

            _mark_flaky_steps(seed_runs)
            flaky_count += sum(1 for run in seed_runs for s in run if s.flaky)

            # Grade journey from seed 1 loop 1 (canonical)
            canonical = seed_runs[0] if seed_runs else []
            journey_status = _journey_status_from_snaps(canonical)
            for persona in ctx.config.personas:
                report.journey_grades.setdefault(journey.id, {})[persona.id] = journey_status

        ctx.metadata["flaky_steps"] = flaky_count
        ctx.metadata["parallel_seeds"] = seeds
        report.summary = (
            f"Executed {executed} steps across {len(ctx.config.journeys)} journeys "
            f"({failed} failures, {flaky_count} flaky steps, seeds={seeds})"
        )
        report.metadata = {
            "steps_executed": executed,
            "step_failures": failed,
            "flaky_steps": flaky_count,
            "parallel_seeds": seeds,
        }
        return report
