"""Experiment spec in DSL and config API."""

from pathlib import Path

import yaml

from rehearse.analysis_export import build_run_bundle
from rehearse.dashboard.config_yaml import get_config_yaml, set_config_experiment, validate_config_yaml
from rehearse.dsl import load_config
from rehearse.evidence import RunEvidence
from rehearse.heuristics import analyze_run


def test_load_experiment_block(tmp_path: Path):
    path = tmp_path / "exp.yaml"
    path.write_text(
        """
run:
  target_url: https://example.com
  run_id_prefix: exp
  product_name: Exp
experiment:
  hypothesis: Shorter onboarding increases completion
  user_goal: Finish signup without support
  variant_label: variant-b
personas:
  - {id: p1, name: A, role: r, goals: [g]}
  - {id: p2, name: B, role: r, goals: [g]}
  - {id: p3, name: C, role: r, goals: [g]}
journeys:
  - {id: j1, name: J1, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j2, name: J2, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j3, name: J3, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j4, name: J4, steps: [{action: navigate, url: "https://example.com"}]}
  - {id: j5, name: J5, steps: [{action: navigate, url: "https://example.com"}]}
"""
    )
    cfg = load_config(path)
    assert cfg.experiment is not None
    assert "onboarding" in cfg.experiment.hypothesis
    assert cfg.experiment.variant_label == "variant-b"


def test_bundle_includes_experiment(tmp_path: Path):
    path = tmp_path / "exp.yaml"
    path.write_text(
        (Path(__file__).parent / "fixtures" / "minimal-valid.yaml").read_text()
        + """
experiment:
  hypothesis: Test hypothesis
  user_goal: Reach dashboard
"""
    )
    cfg = load_config(path)
    evidence = RunEvidence(
        run_id="exp-20260601-120000",
        target_url=cfg.target_url,
        product_name=cfg.product_name,
        started_at="2026-06-01T12:00:00Z",
        finished_at="2026-06-01T12:01:00Z",
        duration_ms=30_000,
        outcome="complete",
        steps=[],
    )
    analysis = analyze_run(cfg, evidence)
    bundle = build_run_bundle(cfg, evidence, analysis, tmp_path)
    assert bundle["summary"]["experiment"]["hypothesis"] == "Test hypothesis"
    assert bundle["summary"]["experiment"]["userGoal"] == "Reach dashboard"


def test_set_config_experiment_api(tmp_path: Path):
    src = Path(__file__).parent / "fixtures" / "minimal-valid.yaml"
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    (cfg_dir / "demo.yaml").write_text(src.read_text())
    set_config_experiment(
        tmp_path,
        config_id="demo",
        hypothesis="Users hesitate at pricing",
        user_goal="Select a plan",
        variant_label="control",
    )
    meta = get_config_yaml(tmp_path, "demo")
    assert meta["experiment"]["hypothesis"].startswith("Users hesitate")
    data = yaml.safe_load(meta["yaml"])
    assert data["experiment"]["variant_label"] == "control"
    check = validate_config_yaml(meta["yaml"])
    assert check["valid"]
