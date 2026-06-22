"""CI/CD gate exit-code contract — `rehearse run --fail-on-gate`.

Before this, `rehearse run` exited 0 even when the launch gate was BLOCKED —
a CI pipeline had no way to fail a deploy on a bad verdict. These tests cover
the contract: the CLI reads the gate back from the written analysis bundle,
prints it, and exits non-zero only when --fail-on-gate is passed AND the gate
is CAUTION or BLOCKED.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from rehearse.cli import main
from rehearse.context import RunContext
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import AnalysisResult


def _fake_config_file(tmp_path: Path) -> Path:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
run:
  target_url: https://example.com
  run_id_prefix: t
  product_name: T
personas:
  - id: p1
    name: Evaluator
    role: evaluator
    goals: ["evaluate"]
  - id: p2
    name: Operator
    role: operator
    goals: ["operate"]
  - id: p3
    name: Admin
    role: admin
    goals: ["administer"]
journeys:
  - id: j1
    name: Onboarding
    steps:
      - action: navigate
        url: /
  - id: j2
    name: Journey 2
    steps:
      - action: navigate
        url: /a
  - id: j3
    name: Journey 3
    steps:
      - action: navigate
        url: /b
  - id: j4
    name: Journey 4
    steps:
      - action: navigate
        url: /c
  - id: j5
    name: Journey 5
    steps:
      - action: navigate
        url: /d
"""
    )
    return cfg_path


def _write_bundle(output: Path, run_id: str, launch_gate: str) -> None:
    analysis_dir = output / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "summary": {
            "id": run_id,
            "launchGate": launch_gate,
            "verdict": f"test verdict for {launch_gate}",
            "readiness": 80,
            "flakeRate": 0.0,
        }
    }
    (analysis_dir / f"{run_id}.json").write_text(json.dumps(bundle))


def _run_cli(tmp_path: Path, launch_gate: str, *, fail_on_gate: bool) -> "CliRunner.invoke":
    config_path = _fake_config_file(tmp_path)
    output = tmp_path / "artifacts"
    run_id = "t-20260622-000000"

    evidence = RunEvidence(
        run_id=run_id,
        target_url="https://example.com",
        product_name="T",
        started_at="2026-06-22T00:00:00+00:00",
        outcome="complete",
    )
    evidence.add_step(
        StepSnapshot(
            step_id="j1-p1-s1", journey_id="j1", journey_name="Onboarding",
            persona_id="p1", action="navigate", outcome="pass",
        )
    )
    config = RunConfig(
        target_url="https://example.com", run_id_prefix="t", product_name="T",
        personas=[Persona(id="p1", name="Evaluator", role="evaluator", goals=["evaluate"])],
        journeys=[Journey(id="j1", name="Onboarding", steps=[Step(action="navigate", url="/")])],
        budgets=Budgets(),
    )
    ctx = RunContext(config=config, evidence=evidence)
    ctx.synthesis = AnalysisResult(journey_matrix={})

    _write_bundle(output, run_id, launch_gate)

    runner = CliRunner()
    args = ["run", "--config", str(config_path), "--output", str(output)]
    if fail_on_gate:
        args.append("--fail-on-gate")

    with patch("rehearse.env_loader.load_dotenv_files"):
        with patch("rehearse.cli.preflight_head", return_value={"url": "https://example.com", "status_code": 200}):
            with patch("rehearse.cli.run_rehearsal", return_value=(evidence, None, ctx)):
                return runner.invoke(main, args)


def test_blocked_gate_exits_nonzero_with_fail_on_gate(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "BLOCKED", fail_on_gate=True)
    assert result.exit_code == 2
    assert "BLOCKED" in result.output


def test_caution_gate_exits_nonzero_with_fail_on_gate(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "CAUTION", fail_on_gate=True)
    assert result.exit_code == 2


def test_pass_gate_exits_zero_with_fail_on_gate(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "PASS", fail_on_gate=True)
    assert result.exit_code == 0


def test_review_gate_exits_zero_with_fail_on_gate(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "REVIEW", fail_on_gate=True)
    assert result.exit_code == 0


def test_blocked_gate_exits_zero_without_fail_on_gate_flag(tmp_path: Path) -> None:
    """Without --fail-on-gate, exit code stays 0 — backwards compatible default."""
    result = _run_cli(tmp_path, "BLOCKED", fail_on_gate=False)
    assert result.exit_code == 0


def test_gate_and_verdict_printed_to_stdout(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "CAUTION", fail_on_gate=False)
    json_start = result.output.index("{")
    json_end = result.output.index("\n}") + 2
    payload = json.loads(result.output[json_start:json_end])
    assert payload["launch_gate"] == "CAUTION"
    assert payload["verdict"] == "test verdict for CAUTION"
    assert payload["readiness_score"] == 80
    assert "Launch Gate: CAUTION" in result.output


def test_last_run_result_file_is_pure_json(tmp_path: Path) -> None:
    """CI tooling must be able to read this file without scraping stdout —
    stdout has log lines (preflight, Launch Gate echo) mixed in with the JSON."""
    _run_cli(tmp_path, "BLOCKED", fail_on_gate=False)
    result_path = tmp_path / "artifacts" / "last-run-result.json"
    assert result_path.is_file()
    payload = json.loads(result_path.read_text())
    assert payload["launch_gate"] == "BLOCKED"
    assert payload["run_id"] == "t-20260622-000000"
