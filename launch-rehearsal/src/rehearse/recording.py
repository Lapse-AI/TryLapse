"""Recording storage and playback for rrweb + Playwright video."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_rrweb_recording(
    artifacts_root: Path,
    run_id: str,
    journey_id: str,
    events: list[dict[str, Any]],
) -> Path:
    """Save rrweb event recording to JSON."""
    recording_dir = artifacts_root / "artifacts" / run_id / "recordings"
    recording_dir.mkdir(parents=True, exist_ok=True)

    path = recording_dir / f"{journey_id}-events.json"
    path.write_text(json.dumps({
        "journeyId": journey_id,
        "eventCount": len(events),
        "events": events,
    }, indent=2))
    return path


def load_rrweb_recording(artifacts_root: Path, run_id: str, journey_id: str) -> dict[str, Any] | None:
    """Load rrweb event recording from JSON."""
    path = artifacts_root / "artifacts" / run_id / "recordings" / f"{journey_id}-events.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def get_video_path(artifacts_root: Path, run_id: str, journey_id: str) -> Path | None:
    """Get path to Playwright video recording if it exists."""
    video_dir = artifacts_root / "artifacts" / run_id / "videos"
    if not video_dir.is_dir():
        return None

    # Look for video files: {journey_id}-*.webm or {journey_id}-*.mp4
    for ext in ["webm", "mp4"]:
        for video in video_dir.glob(f"{journey_id}*.{ext}"):
            if video.is_file():
                return video

    return None


def list_recordings_for_run(artifacts_root: Path, run_id: str) -> list[dict[str, Any]]:
    """List all recordings available for a run."""
    recording_dir = artifacts_root / "artifacts" / run_id / "recordings"
    if not recording_dir.is_dir():
        return []

    recordings = []
    for event_file in recording_dir.glob("*-events.json"):
        try:
            data = json.loads(event_file.read_text())
            video_path = get_video_path(artifacts_root, run_id, data.get("journeyId", ""))
            recordings.append({
                "journeyId": data.get("journeyId"),
                "eventCount": data.get("eventCount", 0),
                "hasVideo": video_path is not None,
                "videoPath": str(video_path) if video_path else None,
                "eventsPath": str(event_file),
            })
        except json.JSONDecodeError:
            continue

    return recordings
