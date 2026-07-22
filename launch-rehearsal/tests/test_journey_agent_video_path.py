"""Regression test for a real bug: parallel journey workers were computing video_dir
as artifacts_root / "artifacts" / run_id / "videos", but artifacts_root passed into
JourneyAgent is already output_dir/artifacts/run_id (see orchestrator.py). That doubled
the path (e.g. .../artifacts/run-1/artifacts/run-1/videos/) so recordings never showed
up where the recordings API looked for them. Found by inspecting `ps aux` output for a
real running container during a live-Docker diagnostic and confirmed against the actual
ffmpeg command line writing to the doubled path.
"""
from pathlib import Path

from rehearse.agents.journey_agent import _video_dir_for_run


def test_video_dir_matches_browser_session_convention():
    # BrowserSession.__enter__ (browser.py) computes video_dir as
    # self.artifacts_dir / "videos" where artifacts_dir is the same
    # already-run-scoped root. Parallel workers must produce the identical path.
    artifacts_root = Path("/data/artifacts/artifacts/my-run-20260101-000000")
    video_dir = _video_dir_for_run(artifacts_root)
    assert video_dir == artifacts_root / "videos"


def test_video_dir_does_not_double_append_run_id():
    # artifacts_root already ends in .../artifacts/{run_id} (orchestrator.py) — the
    # buggy version appended "artifacts"/run_id AGAIN on top of that, producing
    # .../artifacts/{run_id}/artifacts/{run_id}/videos.
    run_id = "my-run-20260101-000000"
    artifacts_root = Path("/data/artifacts/artifacts") / run_id
    video_dir = _video_dir_for_run(artifacts_root)
    assert video_dir.parts.count(run_id) == 1
    assert video_dir == artifacts_root / "videos"
