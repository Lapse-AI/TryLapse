"""Regression coverage for crawl-phase progress visibility.

A live-Docker diagnostic (self-testing the hosted dashboard, which never goes
network-idle because it polls its own job status) showed a run stuck at
phase="crawling", completed_journeys=0 for 25+ minutes with zero visible
progress — indistinguishable from a hang even though it was slowly working
through the crawl page budget. progress.py now tracks pages_crawled/pages_budget
so this state is observable instead of opaque.
"""
import json

from rehearse.progress import ProgressTracker


def test_set_crawl_progress_written_to_file(tmp_path):
    tracker = ProgressTracker(tmp_path, "run-1")
    tracker.set_phase("crawling")
    tracker.set_crawl_progress(3, 40)

    data = json.loads((tmp_path / "runs" / "run-1-progress.json").read_text())
    assert data["phase"] == "crawling"
    assert data["pages_crawled"] == 3
    assert data["pages_budget"] == 40


def test_crawl_progress_defaults_to_zero(tmp_path):
    tracker = ProgressTracker(tmp_path, "run-1")
    data = json.loads((tmp_path / "runs" / "run-1-progress.json").read_text())
    assert data["pages_crawled"] == 0
    assert data["pages_budget"] == 0
