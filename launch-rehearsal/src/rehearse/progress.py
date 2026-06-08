"""Live run progress tracker — written during execution, polled by dashboard."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class StepProgress:
    step_id: str
    action: str
    intent: str = ""
    status: str = "pending"   # pending | running | pass | fail | skip
    started_at: float = 0.0
    duration_ms: int = 0
    note: str = ""


@dataclass
class JourneyProgress:
    journey_id: str
    journey_name: str
    persona_id: str
    status: str = "pending"   # pending | running | pass | fail
    steps: list[StepProgress] = field(default_factory=list)
    started_at: float = 0.0
    duration_ms: int = 0


@dataclass
class PersonaProgress:
    persona_id: str
    persona_name: str
    status: str = "pending"   # pending | running | done
    journeys: list[JourneyProgress] = field(default_factory=list)


@dataclass
class RunProgress:
    run_id: str
    config_id: str = ""
    product_name: str = ""
    target_url: str = ""
    phase: str = "starting"   # starting | crawling | discovering | executing | done | failed
    started_at: float = field(default_factory=time.time)
    personas: list[PersonaProgress] = field(default_factory=list)
    total_journeys: int = 0
    completed_journeys: int = 0
    total_steps: int = 0
    completed_steps: int = 0
    current_persona: str = ""
    current_journey: str = ""
    current_step: str = ""
    error: str = ""


class ProgressTracker:
    """Writes live progress JSON to a file during run execution."""

    def __init__(self, artifacts_root: Path, run_id: str) -> None:
        self._path = artifacts_root / "runs" / f"{run_id}-progress.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._progress = RunProgress(run_id=run_id)
        self._flush()

    def set_config(self, config_id: str, product_name: str, target_url: str) -> None:
        self._progress.config_id = config_id
        self._progress.product_name = product_name
        self._progress.target_url = target_url
        self._flush()

    def set_phase(self, phase: str) -> None:
        self._progress.phase = phase
        self._flush()

    def set_personas(self, personas: list[dict[str, Any]], journeys_per_persona: dict[str, list[dict[str, Any]]]) -> None:
        self._progress.personas = []
        total_j = 0
        for p in personas:
            pid = p.get("id", "")
            pjourneys = journeys_per_persona.get(pid, [])
            total_j += len(pjourneys)
            self._progress.personas.append(PersonaProgress(
                persona_id=pid,
                persona_name=p.get("name", pid),
                journeys=[
                    JourneyProgress(
                        journey_id=j.get("id", ""),
                        journey_name=j.get("name", j.get("id", "")),
                        persona_id=pid,
                        steps=[
                            StepProgress(
                                step_id=f"{j.get('id')}-{i}",
                                action=s.get("action", ""),
                                intent=s.get("intent", s.get("url", "")),
                            )
                            for i, s in enumerate(j.get("steps", []))
                        ],
                    )
                    for j in pjourneys
                ],
            ))
        self._progress.total_journeys = total_j
        self._flush()

    def start_persona(self, persona_id: str) -> None:
        self._progress.current_persona = persona_id
        for p in self._progress.personas:
            if p.persona_id == persona_id:
                p.status = "running"
        self._flush()

    def done_persona(self, persona_id: str) -> None:
        for p in self._progress.personas:
            if p.persona_id == persona_id:
                p.status = "done"
        self._flush()

    def start_journey(self, persona_id: str, journey_id: str) -> None:
        self._progress.current_journey = journey_id
        for p in self._progress.personas:
            if p.persona_id == persona_id:
                for j in p.journeys:
                    if j.journey_id == journey_id:
                        j.status = "running"
                        j.started_at = time.time()
        self._flush()

    def done_journey(self, persona_id: str, journey_id: str, status: str) -> None:
        self._progress.completed_journeys += 1
        for p in self._progress.personas:
            if p.persona_id == persona_id:
                for j in p.journeys:
                    if j.journey_id == journey_id:
                        j.status = status
                        j.duration_ms = int((time.time() - j.started_at) * 1000)
        self._flush()

    def start_step(self, persona_id: str, journey_id: str, step_id: str, action: str) -> None:
        self._progress.current_step = f"{action}"
        for p in self._progress.personas:
            if p.persona_id == persona_id:
                for j in p.journeys:
                    if j.journey_id == journey_id:
                        for s in j.steps:
                            if s.step_id == step_id:
                                s.status = "running"
                                s.started_at = time.time()
        self._flush()

    def done_step(self, persona_id: str, journey_id: str, step_id: str, status: str, note: str = "") -> None:
        self._progress.completed_steps += 1
        for p in self._progress.personas:
            if p.persona_id == persona_id:
                for j in p.journeys:
                    if j.journey_id == journey_id:
                        for s in j.steps:
                            if s.step_id == step_id:
                                s.status = status
                                s.duration_ms = int((time.time() - s.started_at) * 1000)
                                s.note = note[:100]
        self._flush()

    def set_error(self, error: str) -> None:
        self._progress.error = error
        self._progress.phase = "failed"
        self._flush()

    def finish(self) -> None:
        self._progress.phase = "done"
        self._flush()

    def _flush(self) -> None:
        try:
            self._path.write_text(json.dumps(asdict(self._progress), indent=2))
        except Exception:
            pass


def load_progress(artifacts_root: Path, run_id: str) -> dict[str, Any] | None:
    path = artifacts_root / "runs" / f"{run_id}-progress.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def latest_running_progress(artifacts_root: Path) -> dict[str, Any] | None:
    """Find the most recent in-progress run."""
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir():
        return None
    candidates = sorted(runs_dir.glob("*-progress.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in candidates:
        try:
            data = json.loads(f.read_text())
            if data.get("phase") not in ("done", "failed"):
                return data
        except Exception:
            continue
    # Return latest even if done
    if candidates:
        try:
            return json.loads(candidates[0].read_text())
        except Exception:
            pass
    return None
