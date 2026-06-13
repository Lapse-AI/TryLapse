"""Journey agent — executes E2E steps in browser with optional parallel workers."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rehearse.agents.base import BaseAgent
from rehearse.browser import BrowserSession
from rehearse.context import AgentReport, RunContext
from rehearse.dsl import Journey, Step
from rehearse.errors import RunBudgetExceeded
from rehearse.evidence import StepSnapshot
from rehearse.progress import check_and_handle_signals
from rehearse.viewports import normalize_viewports

_results_lock = threading.Lock()


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
    viewport: str,
) -> list[StepSnapshot]:
    """Run all steps for one journey; return snapshots for this seed/loop/viewport."""
    from rehearse.llm import llm_enabled

    # Look up the persona dict for the behavioral judge
    persona_obj = next(
        ({"id": p.id, "name": p.name, "role": p.role, "goals": list(p.goals)}
         for p in ctx.config.personas if p.id == primary),
        {"id": primary, "name": primary, "role": "user", "goals": []},
    )
    # Try to get discovered journey metadata (behavioral intent, failure signals)
    discovered = ctx.metadata.get("discovered_journeys", {}).get(primary, {})
    journey_meta = next(
        (j for j in (discovered.get("journeys") or []) if j.get("id") == journey.id),
        {"name": journey.name, "behavioral_intent": "", "failure_signals": []},
    )

    use_behavioral_judge = llm_enabled() or ctx.metadata.get("force_llm")
    tracker = ctx.metadata.get("progress_tracker")
    snaps: list[StepSnapshot] = []
    step_dicts: list[dict] = []

    # ── Adaptive execution (Phase 2) ─────────────────────────────────────────
    # Triggered when the journey has no pre-planned steps and LLM is available.
    # The loop generates one step at a time, executes it, observes the result,
    # and appends to a scratchpad until "done" is returned or max steps reached.
    # Gate: only on seed=1, loop=1, desktop — adaptive runs are not parallelised.
    adaptive = (
        not journey.steps
        and use_behavioral_judge
        and seed == 1
        and loop == 1
        and viewport == "desktop"
    )
    if adaptive:
        from rehearse.persona_journey_discovery import generate_next_step
        scratchpad: list[dict] = []
        max_adaptive_steps = journey_meta.get("expected_steps", 14)
        consecutive_failures = 0

        for i in range(max_adaptive_steps):
            if time.perf_counter() > deadline:
                break
            page_state = session.observe_page_state()
            next_step_dict = generate_next_step(
                journey_meta, persona_obj, {}, scratchpad, page_state
            )
            if next_step_dict is None or next_step_dict.get("action") == "done":
                break

            # Convert the generated dict into a DSL Step
            from rehearse.dsl import Step as _Step
            gen_step = _Step(
                action=next_step_dict["action"],
                url=next_step_dict.get("url"),
                selector=next_step_dict.get("selector"),
                value=next_step_dict.get("value"),
                intent=next_step_dict.get("intent", ""),
            )
            step_id = f"{journey.id}-{primary}-s{i+1}-adaptive"
            snap = session.execute_step(
                gen_step,
                step_id=step_id,
                journey_id=journey.id,
                journey_name=journey.name,
                persona_id=primary,
                viewport=viewport,
            )
            snap.seed_index = seed

            # Append to scratchpad for next iteration
            obs = {**page_state, "step": i + 1, "action": gen_step.action,
                   "intent": gen_step.intent or "", "outcome": snap.outcome,
                   "final_url": snap.final_url or ""}
            scratchpad.append(obs)
            step_dicts.append({"action": gen_step.action, "outcome": snap.outcome})
            snaps.append(snap)
            ctx.evidence.add_step(snap)

            if snap.outcome == "fail":
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    break
            else:
                consecutive_failures = 0

        # Store scratchpad in evidence metadata for debugging
        ctx.metadata.setdefault("adaptive_scratchpads", {})[f"{journey.id}:{primary}"] = scratchpad

        # Journey-level synthesis on adaptive run
        if use_behavioral_judge and step_dicts:
            try:
                from rehearse.behavioral_judge import judge_journey
                step_verdicts = [{"behavioral_verdict": "pass", "note": ""} for _ in step_dicts]
                jverdict = judge_journey(step_dicts, step_verdicts, persona=persona_obj, journey=journey_meta)
                ctx.metadata.setdefault("behavioral_journeys", {})[f"{journey.id}:{primary}"] = jverdict
            except Exception:
                pass

        return snaps
    # ── End adaptive execution ────────────────────────────────────────────────

    for i, step in enumerate(journey.steps):
        if time.perf_counter() > deadline:
            raise RunBudgetExceeded("max_run_seconds exceeded")
        step_id = f"{journey.id}-{primary}-s{i+1}-{viewport}-seed{seed}-loop{loop}"
        # Tracker uses simple index-based ID: "{journey.id}-{i}"
        tracker_step_id = f"{journey.id}-{i}"
        # Update live progress — step starting
        if tracker and seed == 1 and loop == 1:
            try:
                tracker.start_step(primary, journey.id, tracker_step_id, step.action)
            except Exception:
                pass
        snap = session.execute_step(
            step,
            step_id=step_id,
            journey_id=journey.id,
            journey_name=journey.name,
            persona_id=primary,
            viewport=viewport,
        )
        snap.seed_index = seed
        # Update live progress — step done
        if tracker and seed == 1 and loop == 1:
            try:
                tracker.done_step(primary, journey.id, tracker_step_id, snap.outcome, snap.note or "")
            except Exception:
                pass

        # Behavioral judge: LLM evaluates each step from persona's perspective
        if use_behavioral_judge and seed == 1 and loop == 1 and viewport == "desktop":
            try:
                from rehearse.behavioral_judge import judge_step
                step_dict = {
                    "action": step.action,
                    "finalUrl": snap.final_url,
                    "requestedUrl": snap.requested_url,
                    "outcome": snap.outcome,
                    "bodyTextExcerpt": snap.body_text_excerpt,
                    "durationMs": snap.duration_ms,
                    "consoleErrors": snap.console_errors,
                    "networkFailures": snap.network_failures,
                    "headingCount": snap.heading_count,
                    "linkCount": snap.link_count,
                    "unlabeledButtonCount": snap.unlabeled_button_count,
                    "expected_outcome": getattr(step, "expected_outcome", ""),
                }
                verdict = judge_step(step_dict, persona=persona_obj, journey=journey_meta)
                snap.behavioral_verdict = verdict.get("behavioral_verdict")
                snap.behavioral_friction = verdict.get("friction_signals") or []
                snap.behavioral_ux_concerns = verdict.get("ux_concerns") or []
                snap.chatbot_quality = verdict.get("chatbot_quality")
                step_dicts.append({**step_dict, **verdict})
            except Exception:
                step_dicts.append({"action": step.action, "outcome": snap.outcome})
        else:
            step_dicts.append({"action": step.action, "outcome": snap.outcome})

        snaps.append(snap)
        ctx.evidence.add_step(snap)

        if step.action == "navigate" and step.url and i == 0 and seed > 1:
            pass

    # Journey-level behavioral synthesis (first seed, desktop only)
    if use_behavioral_judge and seed == 1 and loop == 1 and viewport == "desktop" and step_dicts:
        try:
            from rehearse.behavioral_judge import judge_journey
            step_verdicts = [{"behavioral_verdict": s.get("behavioral_verdict", "pass"),
                              "note": s.get("note", "")} for s in step_dicts]
            jverdict = judge_journey(step_dicts, step_verdicts, persona=persona_obj, journey=journey_meta)
            ctx.metadata.setdefault("behavioral_journeys", {})[f"{journey.id}:{primary}"] = jverdict
        except Exception:
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


class _ThreadSession:
    """Session wrapper for parallel worker threads — owns its own page.

    Delegates execute_step to the same BrowserSession implementation so that
    parallel workers produce real StepSnapshot records.
    """
    def __init__(self, page: object, config: object) -> None:
        self.page = page
        self.config = config
        self.console_errors: list[str] = []
        self.console_warnings: list[str] = []
        self.network_failures: list[str] = []
        self.network_log: list[dict] = []
        self.record_video = False
        self._viewport = "desktop"  # execute_step reads this
        self.artifacts_dir = Path(".")   # execute_step writes screenshots here; overridden by caller

    def set_viewport(self, profile: str) -> None:
        from rehearse.viewports import VIEWPORT_PROFILES
        key = profile.strip().lower()
        if key not in VIEWPORT_PROFILES:
            key = "desktop"
        self._viewport = key
        try:
            self.page.set_viewport_size(VIEWPORT_PROFILES[key])  # type: ignore[attr-defined]
        except Exception:
            pass

    def reset_run_errors(self) -> None:
        self.console_errors = []
        self.network_failures = []

    def execute_step(self, step, **kwargs):
        """Delegate to BrowserSession.execute_step bound to this thread's page."""
        from rehearse.browser import BrowserSession
        return BrowserSession.execute_step(self, step, **kwargs)  # type: ignore[arg-type]

    def observe_page_state(self) -> dict:
        """Delegate to BrowserSession.observe_page_state bound to this thread's page."""
        from rehearse.browser import BrowserSession
        return BrowserSession.observe_page_state(self)  # type: ignore[arg-type]


class JourneyAgent(BaseAgent):
    agent_id = "journey-runner"
    agent_role = "E2E journey execution"
    phase = "journey"

    def __init__(self, session: BrowserSession, artifacts_root: Path) -> None:
        self.session = session
        self.artifacts_root = artifacts_root
        self._deadline: float = 0
        self._browser: bool = False  # True when parallel mode active

    def _run_journey_once(
        self,
        ctx: RunContext,
        journey: Journey,
        *,
        primary: str,
        seed: int,
        loop: int,
        viewport: str,
    ) -> list[StepSnapshot]:
        if seed > 1 or loop > 1:
            _navigate_journey_entry(self.session, journey)
        self.session.set_viewport(viewport)
        return _replay_journey_from_start(
            self.session,
            journey,
            primary=primary,
            seed=seed,
            loop=loop,
            artifacts_root=self.artifacts_root,
            deadline=self._deadline,
            ctx=ctx,
            viewport=viewport,
        )

    def _run_journey_worker(
        self,
        ctx: RunContext,
        journey: Journey,
        persona_id: str,
        seeds: int,
        loops: int,
        viewports: list[str],
    ) -> tuple[str, str, list[list[StepSnapshot]]]:
        """Worker that runs one journey for one persona — can run in a thread."""
        tracker = ctx.metadata.get("progress_tracker")
        if tracker:
            try:
                tracker.start_journey(persona_id, journey.id)
            except Exception:
                pass

        persona_runs: list[list[StepSnapshot]] = []
        for loop in range(1, loops + 1):
            for seed in range(1, seeds + 1):
                for viewport in viewports:
                    if time.perf_counter() > self._deadline:
                        break
                    # Each parallel worker needs its own browser context
                    if hasattr(self, "_browser") and self._browser:
                        # Parallel mode: spin up own context with auth cookies from main session
                        try:
                            from playwright.sync_api import sync_playwright
                            with sync_playwright() as pw:
                                browser = pw.chromium.launch(headless=True)
                                context_opts: dict = {"viewport": {"width": 1280, "height": 800}}
                                run_id = getattr(ctx.evidence, "run_id", None)
                                record = getattr(self.session, "record_video", False)
                                video_dir: "Path | None" = None
                                if record and run_id:
                                    # Place under artifacts/{run_id}/videos/ so
                                    # recording.get_video_path() can find by journey_id
                                    video_dir = self.artifacts_root / "artifacts" / run_id / "videos"
                                    video_dir.mkdir(parents=True, exist_ok=True)
                                    context_opts["record_video_dir"] = str(video_dir)
                                # Restore auth cookies so worker starts authenticated
                                auth_state = ctx.metadata.get("auth_storage_state")
                                if auth_state:
                                    context_opts["storage_state"] = auth_state
                                context = browser.new_context(**context_opts)
                                page = context.new_page()
                                tmp_session = _ThreadSession(page, self.session.config)
                                tmp_session.artifacts_dir = self.artifacts_root
                                snaps = _replay_journey_from_start(
                                    tmp_session, journey,
                                    primary=persona_id, seed=seed, loop=loop,
                                    artifacts_root=self.artifacts_root,
                                    deadline=self._deadline, ctx=ctx, viewport=viewport,
                                )
                                # Close context first — Playwright finalises the webm on close
                                context.close()
                                browser.close()
                                # Rename page@UUID.webm → {journey_id}.webm so the recordings
                                # API can locate it by journey_id without a UUID lookup
                                if video_dir and video_dir.is_dir():
                                    newest = sorted(
                                        video_dir.glob("page@*.webm"),
                                        key=lambda p: p.stat().st_mtime,
                                        reverse=True,
                                    )
                                    if newest:
                                        try:
                                            newest[0].rename(video_dir / f"{journey.id}.webm")
                                        except OSError:
                                            pass
                        except Exception as e:
                            import traceback
                            ctx.metadata.setdefault("_parallel_errors", []).append(
                                f"{journey.id}: {type(e).__name__}: {e}\n{traceback.format_exc()[-300:]}"
                            )
                            snaps = []
                    else:
                        # Sequential fallback
                        snaps = self._run_journey_once(
                            ctx, journey, primary=persona_id,
                            seed=seed, loop=loop, viewport=viewport,
                        )
                    persona_runs.append(snaps)

        canonical = next(
            (run for run in persona_runs if run and run[0].viewport == "desktop"),
            persona_runs[0] if persona_runs else [],
        )
        grade = _journey_status_from_snaps(canonical)

        if tracker:
            try:
                tracker.done_journey(persona_id, journey.id, grade)
            except Exception:
                pass

        return journey.id, persona_id, persona_runs

    def execute(self, ctx: RunContext) -> AgentReport:
        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary="Journey execution",
        )
        self._deadline = ctx.metadata.get("deadline", time.perf_counter() + 9999)
        seeds = ctx.config.budgets.parallel_seeds
        loops = ctx.config.budgets.repeat_micro_loop
        viewports = normalize_viewports(ctx.config.viewports)
        workers = ctx.config.budgets.parallel_journeys
        # Default True: run all personas unless explicitly disabled
        run_all = ctx.config.execute_all_personas_in_browser
        if run_all is None:
            run_all = True
        personas_to_run = ctx.config.personas if run_all else [ctx.config.personas[0]]
        executed = 0
        failed = 0
        flaky_count = 0

        # Build work units: (journey, persona)
        # If a journey has persona_ids, only run it for those specific personas
        work_units = [
            (journey, persona)
            for journey in ctx.config.journeys
            for persona in personas_to_run
            if not journey.persona_ids or persona.id in journey.persona_ids
        ]

        # Collect results: {journey_id: {persona_id: [runs]}}
        all_results: dict[str, dict[str, list[list[StepSnapshot]]]] = {}

        if workers > 1:
            # Parallel mode — each work unit gets own Playwright instance in a thread
            self._browser = True  # signal to worker to create own browser
            _artifacts_root = Path(ctx.metadata.get("output_dir", "."))
            _tracker = ctx.metadata.get("progress_tracker")
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="journey") as pool:
                futures = {
                    pool.submit(
                        self._run_journey_worker,
                        ctx, journey, persona.id, seeds, loops, viewports,
                    ): (journey, persona)
                    for journey, persona in work_units
                }
                for future in as_completed(futures):
                    # Check control signals between completed futures
                    sig = check_and_handle_signals(_artifacts_root, ctx.evidence.run_id, _tracker)
                    if sig == "stop":
                        for f in futures:
                            f.cancel()
                        break
                    try:
                        jid, pid, persona_runs = future.result()
                        with _results_lock:
                            all_results.setdefault(jid, {})[pid] = persona_runs
                            executed += sum(len(r) for r in persona_runs)
                            failed += sum(
                                1 for r in persona_runs for s in r if s.outcome == "fail"
                            )
                    except Exception:
                        pass
            self._browser = False
        else:
            # Sequential mode (original behaviour)
            _artifacts_root = Path(ctx.metadata.get("output_dir", "."))
            _tracker = ctx.metadata.get("progress_tracker")
            for journey, persona in work_units:
                if check_and_handle_signals(_artifacts_root, ctx.evidence.run_id, _tracker) == "stop":
                    break
                _, _, persona_runs = self._run_journey_worker(
                    ctx, journey, persona.id, seeds, loops, viewports,
                )
                all_results.setdefault(journey.id, {})[persona.id] = persona_runs
                executed += sum(len(r) for r in persona_runs)
                failed += sum(1 for r in persona_runs for s in r if s.outcome == "fail")

        # Consolidate grades + flaky detection per journey
        for journey in ctx.config.journeys:
            journey_results = all_results.get(journey.id, {})
            seed_runs: list[list[StepSnapshot]] = []
            persona_grades: dict[str, str] = {}

            for persona in personas_to_run:
                persona_runs = journey_results.get(persona.id, [])
                seed_runs.extend(persona_runs)
                canonical = next(
                    (run for run in persona_runs if run and run[0].viewport == "desktop"),
                    persona_runs[0] if persona_runs else [],
                )
                persona_grades[persona.id] = _journey_status_from_snaps(canonical)

            _mark_flaky_steps(seed_runs)
            flaky_count += sum(1 for run in seed_runs for s in run if s.flaky)

            for persona in ctx.config.personas:
                report.journey_grades.setdefault(journey.id, {})[persona.id] = (
                    persona_grades.get(persona.id)
                    or persona_grades.get(personas_to_run[0].id)
                    or "pass"
                )

        ctx.metadata["flaky_steps"] = flaky_count
        ctx.metadata["parallel_seeds"] = seeds
        report.summary = (
            f"Executed {executed} steps across {len(ctx.config.journeys)} journeys "
            f"({failed} failures, {flaky_count} flaky steps, seeds={seeds}, "
            f"viewports={viewports}, personas={len(personas_to_run)})"
        )
        report.metadata = {
            "steps_executed": executed,
            "step_failures": failed,
            "flaky_steps": flaky_count,
            "parallel_seeds": seeds,
            "viewports": viewports,
            "personas_executed": len(personas_to_run),
            "execute_all_personas_in_browser": ctx.config.execute_all_personas_in_browser,
        }
        return report
