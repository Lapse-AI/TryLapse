"""End-to-end integration tests — dry_run pipeline, SSRF redirect chain, bundle structure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.errors import SSRFBlockedError
from rehearse.preflight import _follow_redirect_safe, assert_url_allowed
from rehearse.runner import run_rehearsal


# ── helpers ──────────────────────────────────────────────────────────────────


def _minimal_config(target_url: str = "https://example.com") -> RunConfig:
    return RunConfig(
        target_url=target_url,
        run_id_prefix="test",
        product_name="Test Product",
        personas=[
            Persona(
                id="p1",
                name="First-Time Evaluator",
                role="evaluator",
                goals=["explore the product"],
            )
        ],
        journeys=[
            Journey(
                id="j-smoke",
                name="Smoke check",
                steps=[
                    Step(action="navigate", url="/"),
                    Step(action="wait", value="500"),
                ],
            )
        ],
        budgets=Budgets(),
    )


# ── dry_run pipeline ─────────────────────────────────────────────────────────


def test_dry_run_returns_evidence(tmp_path: Path) -> None:
    config = _minimal_config()
    evidence, scorecard_path, ctx = run_rehearsal(
        config, output_dir=tmp_path, dry_run=True
    )
    assert evidence.outcome == "dry_run_complete"
    assert evidence.run_id.startswith("test-")
    assert scorecard_path is None
    assert ctx is None


def test_dry_run_produces_steps(tmp_path: Path) -> None:
    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    # One journey × one persona × two steps
    assert len(evidence.steps) == 2
    assert all(s.outcome == "skipped" for s in evidence.steps)
    assert all("dry-run" in (s.note or "") for s in evidence.steps)


def test_dry_run_step_ids_are_namespaced(tmp_path: Path) -> None:
    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    for step in evidence.steps:
        assert step.journey_id == "j-smoke"
        assert step.persona_id == "p1"
        assert step.step_id.startswith("j-smoke-p1-")


def test_dry_run_writes_evidence_file(tmp_path: Path) -> None:
    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    run_file = tmp_path / "runs" / f"{evidence.run_id}.json"
    assert run_file.exists(), f"evidence file not found: {run_file}"
    payload = json.loads(run_file.read_text())
    assert payload["run_id"] == evidence.run_id
    assert payload["outcome"] == "dry_run_complete"


def test_dry_run_records_duration(tmp_path: Path) -> None:
    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    assert evidence.duration_ms >= 0


def test_dry_run_no_phase_timings_in_dry_mode(tmp_path: Path) -> None:
    # phase_timings only populated in live mode — should be empty in dry_run
    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    assert evidence.phase_timings == {}


def test_dry_run_multi_journey(tmp_path: Path) -> None:
    config = _minimal_config()
    config.journeys.append(
        Journey(
            id="j-second",
            name="Second journey",
            steps=[Step(action="navigate", url="/about")],
        )
    )
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    # 2 journeys × 1 persona: 2 + 1 = 3 steps total
    assert len(evidence.steps) == 3
    journey_ids = {s.journey_id for s in evidence.steps}
    assert journey_ids == {"j-smoke", "j-second"}


# ── SSRF redirect chain ───────────────────────────────────────────────────────


def test_ssrf_blocks_private_ip_literal() -> None:
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://192.168.1.1/admin")


def test_ssrf_blocks_link_local() -> None:
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://169.254.169.254/latest/meta-data/")


def test_ssrf_blocks_localhost() -> None:
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://localhost:8080/internal")


def test_ssrf_allows_localhost_with_flag() -> None:
    parsed = assert_url_allowed("http://localhost:3000/", allow_localhost=True)
    assert parsed.hostname == "localhost"


def test_ssrf_rejects_non_http_scheme() -> None:
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("file:///etc/passwd")


def test_ssrf_rejects_dotlocal() -> None:
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://myprinter.local/admin")


def test_ssrf_redirect_chain_blocks_private_hop(monkeypatch: pytest.MonkeyPatch) -> None:
    """A redirect chain that ends at a private IP must be blocked on that hop."""
    import httpx

    call_log: list[str] = []

    class FakeResponse:
        def __init__(self, is_redirect: bool, location: str | None, url: str) -> None:
            self.is_redirect = is_redirect
            self.headers = {"location": location} if location else {}
            self.url = url
            self.status_code = 302 if is_redirect else 200

    def fake_send(req, *, follow_redirects: bool = False):
        url = str(req.url)
        call_log.append(url)
        if "public-site.com" in url:
            return FakeResponse(True, "http://192.168.1.1/secret", url)
        return FakeResponse(False, None, url)

    with httpx.Client(follow_redirects=False) as client:
        monkeypatch.setattr(client, "send", fake_send)
        with pytest.raises(SSRFBlockedError, match="192.168.1.1"):
            _follow_redirect_safe(client, "http://public-site.com/resource")

    assert any("public-site.com" in u for u in call_log), "should have called the first hop"


def test_ssrf_redirect_chain_blocks_metadata_hop(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    class FakeResponse:
        def __init__(self, is_redirect: bool, location: str | None, url: str) -> None:
            self.is_redirect = is_redirect
            self.headers = {"location": location} if location else {}
            self.url = url
            self.status_code = 302 if is_redirect else 200

    def fake_send(req, *, follow_redirects: bool = False):
        url = str(req.url)
        if "safe.example.com" in url:
            return FakeResponse(True, "http://169.254.169.254/latest/meta-data/", url)
        return FakeResponse(False, None, url)

    with httpx.Client(follow_redirects=False) as client:
        monkeypatch.setattr(client, "send", fake_send)
        with pytest.raises(SSRFBlockedError):
            _follow_redirect_safe(client, "http://safe.example.com/page")


# ── bundle output structure ───────────────────────────────────────────────────


def test_dry_run_bundle_has_required_keys(tmp_path: Path) -> None:
    from rehearse.analysis_export import build_run_bundle
    from rehearse.heuristics import analyze_run

    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    analysis = analyze_run(config, evidence)
    bundle = build_run_bundle(config, evidence, analysis, tmp_path)

    assert "summary" in bundle
    summary = bundle["summary"]
    assert "id" in summary
    assert "readiness" in summary
    assert "launchGate" in summary
    assert "durationSec" in summary
    assert "phaseTimings" in summary


def test_dry_run_bundle_phase_timings_keys(tmp_path: Path) -> None:
    from rehearse.analysis_export import build_run_bundle
    from rehearse.heuristics import analyze_run

    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    analysis = analyze_run(config, evidence)
    bundle = build_run_bundle(config, evidence, analysis, tmp_path)

    pt = bundle["summary"]["phaseTimings"]
    assert set(pt.keys()) == {"crawlSec", "journeySec", "analysisSec"}
    # In dry_run all phase timings are 0 (phases don't run)
    assert all(isinstance(v, int) for v in pt.values())


def test_dry_run_bundle_issues_is_list(tmp_path: Path) -> None:
    from rehearse.analysis_export import build_run_bundle
    from rehearse.heuristics import analyze_run

    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    analysis = analyze_run(config, evidence)
    bundle = build_run_bundle(config, evidence, analysis, tmp_path)

    assert isinstance(bundle.get("issues", []), list)


def test_dry_run_bundle_run_id_matches_evidence(tmp_path: Path) -> None:
    from rehearse.analysis_export import build_run_bundle
    from rehearse.heuristics import analyze_run

    config = _minimal_config()
    evidence, _, _ = run_rehearsal(config, output_dir=tmp_path, dry_run=True)
    analysis = analyze_run(config, evidence)
    bundle = build_run_bundle(config, evidence, analysis, tmp_path)

    assert bundle["summary"]["id"] == evidence.run_id
