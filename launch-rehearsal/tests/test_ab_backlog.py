"""Tests for A+B backlog features: streaming synthesis, B2/B4, A4, A1, B1."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call


# ── A1: CrawlResult / coverage metric / XHR paths ─────────────────────────────

def test_crawl_result_dataclass():
    from rehearse.crawler import CrawlResult, CrawlPage
    pages = [CrawlPage(url="https://x/", path="/", title="Home", depth=0)]
    result = CrawlResult(pages=pages, coverage_pct=100.0, xhr_paths=[])
    assert result.pages is pages
    assert result.coverage_pct == 100.0
    assert result.xhr_paths == []


def test_crawl_result_coverage_partial():
    from rehearse.crawler import CrawlResult, CrawlPage
    pages = [CrawlPage(url="https://x/", path="/", title="Home", depth=0)]
    result = CrawlResult(pages=pages, coverage_pct=50.0, xhr_paths=["/api/users"])
    assert result.coverage_pct == 50.0
    assert "/api/users" in result.xhr_paths


def test_crawl_site_returns_crawl_result():
    """crawl_site() must return a CrawlResult, not a bare list."""
    from rehearse.crawler import crawl_site, CrawlResult

    mock_page = MagicMock()
    mock_page.goto.return_value = MagicMock(status=200)
    mock_page.url = "https://example.com/"
    mock_page.title.return_value = "Home"
    mock_page.locator.return_value.inner_text.return_value = "body text"
    mock_page.locator.return_value.count.return_value = 1
    mock_page.evaluate.return_value = {
        "linkCount": 0, "formCount": 0, "inputCount": 0, "buttonCount": 0, "links": []
    }
    mock_page.wait_for_load_state.return_value = None

    from rehearse.dsl import CrawlConfig
    cfg = CrawlConfig(enabled=True, max_pages=1, max_depth=0)
    result = crawl_site(mock_page, "https://example.com", cfg, timeout_ms=5000)

    assert isinstance(result, CrawlResult)
    assert isinstance(result.coverage_pct, float)
    assert isinstance(result.xhr_paths, list)
    assert len(result.pages) >= 1


def test_crawl_site_registers_and_removes_request_listener():
    """XHR listener must be registered on entry and removed on exit."""
    from rehearse.crawler import crawl_site
    from rehearse.dsl import CrawlConfig

    mock_page = MagicMock()
    mock_page.goto.return_value = MagicMock(status=200)
    mock_page.url = "https://example.com/"
    mock_page.title.return_value = "Home"
    mock_page.locator.return_value.inner_text.return_value = "text"
    mock_page.locator.return_value.count.return_value = 0
    mock_page.evaluate.return_value = {
        "linkCount": 0, "formCount": 0, "inputCount": 0, "buttonCount": 0, "links": []
    }

    cfg = CrawlConfig(enabled=True, max_pages=1, max_depth=0)
    crawl_site(mock_page, "https://example.com", cfg)

    # on() called once to register the XHR listener
    on_calls = [c for c in mock_page.on.call_args_list if c.args[0] == "request"]
    assert len(on_calls) == 1

    # remove_listener() called once to clean up
    remove_calls = [c for c in mock_page.remove_listener.call_args_list if c.args[0] == "request"]
    assert len(remove_calls) == 1


def test_crawl_agent_exposes_coverage_in_metadata():
    """CrawlAgent must store coverage_pct and xhr_paths in report.metadata."""
    from rehearse.agents.crawl_agent import CrawlAgent
    from rehearse.crawler import CrawlResult, CrawlPage
    from rehearse.dsl import Budgets, CrawlConfig, Journey, Persona, RunConfig, Step
    from rehearse.evidence import RunEvidence
    from rehearse.context import RunContext

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=[Journey(id="j1", name="J", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
        crawl=CrawlConfig(enabled=True, max_pages=2),
    )
    ev = RunEvidence(run_id="t-001", target_url="https://x.com",
                     product_name="T", started_at="2026-06-19T00:00:00Z")
    ctx = RunContext(config=cfg, evidence=ev)

    mock_page = MagicMock()
    ctx.metadata = {"page": mock_page, "output_dir": "/tmp"}

    fake_result = CrawlResult(
        pages=[CrawlPage(url="https://x/", path="/", title="Home", depth=0)],
        coverage_pct=75.0,
        xhr_paths=["/api/data"],
    )

    with patch("rehearse.agents.crawl_agent.crawl_site", return_value=fake_result), \
         patch("rehearse.agents.crawl_agent.SiteMap") as MockSiteMap:
        mock_sitemap = MagicMock()
        mock_sitemap.auth_gated_paths = []
        mock_sitemap.orphan_paths = []
        mock_sitemap.hub_paths = []
        MockSiteMap.from_pages.return_value = mock_sitemap

        agent = CrawlAgent()
        report = agent.execute(ctx)

    assert report.metadata["coverage_pct"] == 75.0
    assert "/api/data" in report.metadata["xhr_paths"]
    assert "coverage 75.0%" in report.summary


# ── B1: Pre-run cleanup ────────────────────────────────────────────────────────

def test_cleanup_stale_artifacts_removes_orphans(tmp_path):
    """_cleanup_stale_artifacts() must delete artifact dirs with no matching state file."""
    from rehearse.runner import _cleanup_stale_artifacts

    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    # Known run — has a state file
    (runs_dir / "run-001.json").write_text('{"status": "COMPLETE"}')
    known_art = artifacts_dir / "run-001"
    known_art.mkdir()
    (known_art / "screenshot.jpg").write_text("fake")

    # Orphan run — no matching state file
    orphan_art = artifacts_dir / "run-999"
    orphan_art.mkdir()
    (orphan_art / "screenshot.jpg").write_text("fake")

    _cleanup_stale_artifacts(tmp_path)

    assert known_art.exists(), "Known artifact dir must be preserved"
    assert not orphan_art.exists(), "Orphan artifact dir must be removed"


def test_cleanup_stale_artifacts_noop_when_no_artifacts_dir(tmp_path):
    """_cleanup_stale_artifacts() must not raise when artifacts/ does not exist."""
    from rehearse.runner import _cleanup_stale_artifacts
    # Should not raise
    _cleanup_stale_artifacts(tmp_path)


def test_cleanup_stale_artifacts_preserves_all_when_no_runs_dir(tmp_path):
    """Without a runs/ dir, all artifact subdirs are treated as orphans and removed."""
    from rehearse.runner import _cleanup_stale_artifacts

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    some_art = artifacts_dir / "run-abc"
    some_art.mkdir()

    _cleanup_stale_artifacts(tmp_path)
    # runs_dir absent → known_run_ids is empty → orphan removed
    assert not some_art.exists()


# ── A4: Playwright tracing flag wired in BrowserSession ───────────────────────

def test_browser_session_record_traces_default_false():
    from rehearse.browser import BrowserSession
    from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=[Journey(id="j1", name="J", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
    )
    session = BrowserSession(cfg, Path("/tmp/art"))
    assert session.record_traces is False
    assert session.trace_path is None


def test_browser_session_record_traces_true():
    from rehearse.browser import BrowserSession
    from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=[Journey(id="j1", name="J", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
    )
    session = BrowserSession(cfg, Path("/tmp/art"), record_traces=True)
    assert session.record_traces is True


def test_browser_session_persona_reset_count_initialises_to_zero():
    from rehearse.browser import BrowserSession
    from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=[Journey(id="j1", name="J", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
    )
    session = BrowserSession(cfg, Path("/tmp/art"))
    assert session._persona_reset_count == 0


# ── B4: screenshot format ──────────────────────────────────────────────────────
# "webp" is NOT a valid Playwright screenshot `type` (only png/jpeg are) — using it
# made every single page.screenshot() call raise, which failed every step in every
# journey of a real run. This test asserts against Playwright's actual accepted
# values instead of just grepping for a string, so a typo'd format can't slip
# through again without a real failure surfacing here first.

import re as _re


def test_screenshot_type_is_a_value_playwright_actually_accepts():
    import inspect
    import rehearse.browser as browser_mod
    src = inspect.getsource(browser_mod)
    types_used = {
        m.group(1)
        for line in src.splitlines() if "screenshot(" in line
        for m in [_re.search(r'type="(\w+)"', line)] if m
    }
    assert types_used, "expected at least one page.screenshot(..., type=...) call"
    assert types_used <= {"png", "jpeg"}, (
        f"Found screenshot type(s) not supported by Playwright: {types_used - {'png', 'jpeg'}}"
    )


# ── Streaming synthesis: _analyzed_personas skip logic ────────────────────────

def test_analyzed_personas_initialised_empty():
    """AgentOrchestrator._analyzed_personas must start empty."""
    from rehearse.agents.orchestrator import AgentOrchestrator
    from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
    from rehearse.evidence import RunEvidence
    from rehearse.context import RunContext
    from rehearse.browser import BrowserSession
    from pathlib import Path

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=[Journey(id="j1", name="J", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
    )
    ev = RunEvidence(run_id="t-001", target_url="https://x.com",
                     product_name="T", started_at="2026-06-19T00:00:00Z")
    ctx = RunContext(config=cfg, evidence=ev)
    session = MagicMock(spec=BrowserSession)

    orch = AgentOrchestrator(ctx, session, Path("/tmp/art"))
    assert orch._analyzed_personas == set()


def test_screenshot_path_finds_jpg_on_disk(tmp_path):
    """analysis_export._screenshot_path must locate the actual .jpg file the
    runner saves — a prior hardcoded '.png' here made every finding's
    screenshot in the dashboard's Action Plan / Overview modal 404."""
    from rehearse.analysis_export import _screenshot_path

    run_dir = tmp_path / "artifacts" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "step-1.jpg").write_bytes(b"fake")

    result = _screenshot_path(tmp_path, "run-1", "step-1")
    assert result == "artifacts/run-1/step-1.jpg"


def test_screenshot_path_falls_back_to_error_jpg(tmp_path):
    from rehearse.analysis_export import _screenshot_path

    run_dir = tmp_path / "artifacts" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "step-1-error.jpg").write_bytes(b"fake")

    result = _screenshot_path(tmp_path, "run-1", "step-1")
    assert result == "artifacts/run-1/step-1-error.jpg"


def test_screenshot_path_still_finds_legacy_png(tmp_path):
    """Older runs captured before the jpeg switch saved .png — must still resolve."""
    from rehearse.analysis_export import _screenshot_path

    run_dir = tmp_path / "artifacts" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "step-1.png").write_bytes(b"fake")

    result = _screenshot_path(tmp_path, "run-1", "step-1")
    assert result == "artifacts/run-1/step-1.png"


def test_write_partial_bundle_is_non_blocking(tmp_path):
    """_write_partial_bundle must not raise even when analysis helpers fail."""
    from rehearse.agents.orchestrator import AgentOrchestrator
    from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
    from rehearse.evidence import RunEvidence
    from rehearse.context import RunContext
    from rehearse.browser import BrowserSession

    cfg = RunConfig(
        target_url="https://x.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="r", goals=[])],
        journeys=[Journey(id="j1", name="J", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
    )
    ev = RunEvidence(run_id="t-001", target_url="https://x.com",
                     product_name="T", started_at="2026-06-19T00:00:00Z")
    ctx = RunContext(config=cfg, evidence=ev)
    session = MagicMock(spec=BrowserSession)

    orch = AgentOrchestrator(ctx, session, tmp_path)

    # Should not raise even though analysis helpers will fail (no real browser data)
    orch._write_partial_bundle(tmp_path, personas_complete=1, total=2)
