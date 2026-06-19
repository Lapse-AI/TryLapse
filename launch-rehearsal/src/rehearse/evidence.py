"""Evidence store — run_id, step_id, artifact paths."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StepSnapshot:
    step_id: str
    journey_id: str
    journey_name: str
    persona_id: str
    action: str
    requested_url: str | None = None
    final_url: str | None = None
    page_title: str | None = None
    http_status: int | None = None
    outcome: str = "pending"
    duration_ms: int = 0
    body_text_excerpt: str = ""
    unlabeled_button_count: int = 0
    link_count: int = 0
    heading_count: int = 0
    input_count: int = 0
    labeled_input_count: int = 0
    missing_alt_count: int = 0
    low_contrast_estimate: int = 0
    error_phrases_found: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    console_warnings: list[str] = field(default_factory=list)
    network_failures: list[str] = field(default_factory=list)
    web_vitals: dict[str, float | None] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    note: str | None = None
    error_type: str | None = None
    flaky: bool = False
    flake_rate: float = 1.0   # fraction of seeds that produced a failing outcome (1.0 = always fails)
    seed_index: int = 1
    viewport: str = "desktop"
    resolved_selector: str | None = None
    focus_region: dict[str, Any] | None = None
    explore_log: list[dict[str, Any]] = field(default_factory=list)
    explore_summary: str | None = None
    # Behavioral judge verdict (L3 deep analysis)
    behavioral_verdict: str | None = None        # pass | partial | fail
    behavioral_friction: list[str] = field(default_factory=list)
    behavioral_ux_concerns: list[str] = field(default_factory=list)
    chatbot_quality: dict[str, Any] | None = None
    # C8: silent API failures — POST/XHR responses with 2xx status but error body
    silent_api_failures: list[str] = field(default_factory=list)
    # C4: lightweight DOM fingerprint (element counts hash) for step-to-step diff
    dom_hash: str | None = None
    # A4: accessibility tree snapshot — compact ARIA tree captured after each step
    aria_snapshot: dict[str, Any] | None = None
    # A4: storage state snapshot — localStorage + sessionStorage keys captured after step
    storage_keys: list[str] | None = None
    # A4: top slow resources from performance.getEntriesByType("resource") after navigate
    resource_timing: list[dict[str, Any]] | None = None
    # A5: SEO signals captured after navigate — meta description, canonical, robots
    seo_meta: dict[str, Any] | None = None


@dataclass
class RunEvidence:
    run_id: str
    target_url: str
    product_name: str
    started_at: str
    finished_at: str | None = None
    duration_ms: int = 0
    auth_attempted: bool = False
    auth_outcome: str | None = None
    steps: list[StepSnapshot] = field(default_factory=list)
    outcome: str = "running"
    network_log_path: str | None = None
    phase_timings: dict[str, int] = field(default_factory=dict)
    video_paths: list[str] = field(default_factory=list)

    def add_step(self, record: StepSnapshot) -> None:
        self.steps.append(record)

    def save(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        out = root / f"{self.run_id}.json"
        tmp = root / f"{self.run_id}.tmp.json"
        tmp.write_text(json.dumps(asdict(self), indent=2))
        tmp.replace(out)  # atomic rename — reader never sees a partial write
        return out

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_run_id(prefix: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{ts}"
