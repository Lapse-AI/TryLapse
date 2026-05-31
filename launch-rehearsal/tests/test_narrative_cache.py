from pathlib import Path

from rehearse.dashboard.narrative_cache import (
    digest_fingerprint,
    load_cached,
    save_cached,
)


def test_narrative_cache_roundtrip(tmp_path: Path):
    root = tmp_path / "artifacts"
    fp = digest_fingerprint([{"id": "run-a"}, {"id": "run-b"}], limit=7)
    narr = {"headline": "test", "source": "llm+template"}
    save_cached(root, "command-digest", fp, narr)
    assert load_cached(root, "command-digest", fp) == narr
    assert load_cached(root, "command-digest", "wrong") is None
