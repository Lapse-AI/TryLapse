"""Tests for D4: LLM-generated share message + signed URLs for P0 video clips."""
from __future__ import annotations

import time
from unittest.mock import patch


# ── signing.py: HMAC signed URLs ──────────────────────────────────────────────

def test_sign_and_verify_round_trip(tmp_path):
    from rehearse.signing import sign_path, verify_signature

    sig, exp = sign_path(tmp_path, "artifacts/run1/videos/j1.webm", ttl_seconds=3600)
    assert verify_signature(tmp_path, "artifacts/run1/videos/j1.webm", sig, exp)


def test_verify_rejects_wrong_path(tmp_path):
    from rehearse.signing import sign_path, verify_signature

    sig, exp = sign_path(tmp_path, "artifacts/run1/videos/j1.webm", ttl_seconds=3600)
    assert not verify_signature(tmp_path, "artifacts/run1/videos/OTHER.webm", sig, exp)


def test_verify_rejects_tampered_signature(tmp_path):
    from rehearse.signing import sign_path, verify_signature

    sig, exp = sign_path(tmp_path, "artifacts/run1/videos/j1.webm", ttl_seconds=3600)
    bad_sig = sig[:-1] + ("0" if sig[-1] != "0" else "1")
    assert not verify_signature(tmp_path, "artifacts/run1/videos/j1.webm", bad_sig, exp)


def test_verify_rejects_expired_signature(tmp_path):
    from rehearse.signing import sign_path, verify_signature

    # ttl in the past — already expired
    sig, exp = sign_path(tmp_path, "artifacts/run1/videos/j1.webm", ttl_seconds=-10)
    assert not verify_signature(tmp_path, "artifacts/run1/videos/j1.webm", sig, exp)


def test_verify_rejects_missing_sig_or_exp(tmp_path):
    from rehearse.signing import verify_signature

    assert not verify_signature(tmp_path, "x.webm", None, int(time.time()) + 100)
    assert not verify_signature(tmp_path, "x.webm", "deadbeef", None)


def test_build_signed_file_url_contains_sig_and_exp(tmp_path):
    from rehearse.signing import build_signed_file_url

    url = build_signed_file_url(tmp_path, "artifacts/run1/videos/j1.webm", ttl_seconds=600)
    assert url.startswith("/files/artifacts/run1/videos/j1.webm?sig=")
    assert "exp=" in url


def test_secret_persists_across_calls(tmp_path):
    """Two signatures for the same path/exp must match — secret must be stable, not regenerated each call."""
    from rehearse.signing import sign_path, _get_secret

    secret_a = _get_secret(tmp_path)
    secret_b = _get_secret(tmp_path)
    assert secret_a == secret_b


def test_env_secret_overrides_persisted_file(tmp_path, monkeypatch):
    from rehearse.signing import _get_secret

    monkeypatch.setenv("REHEARSE_SIGNING_SECRET", "my-test-secret")
    assert _get_secret(tmp_path) == b"my-test-secret"


# ── share.py: build_share_payload ─────────────────────────────────────────────

def _bundle_with_p0(run_id="run1", journey_id="j1"):
    return {
        "summary": {"readiness": 62, "productName": "Acme", "targetUrl": "https://acme.test"},
        "issues": [
            {"severity": "P0", "title": "Checkout button fails", "journeyId": journey_id},
            {"severity": "P2", "title": "Minor styling issue", "journeyId": "j2"},
        ],
    }


def test_share_payload_template_fallback_with_p0(tmp_path):
    from rehearse.share import build_share_payload

    bundle = _bundle_with_p0()
    payload = build_share_payload(bundle, tmp_path, "run1", use_llm=False)

    assert payload["p0Count"] == 1
    assert "1 P0" in payload["message"]
    assert payload["readiness"] == 62
    assert payload["videos"] == []  # no video file on disk in this test


def test_share_payload_no_p0_message(tmp_path):
    from rehearse.share import build_share_payload

    bundle = {
        "summary": {"readiness": 95, "productName": "Acme", "targetUrl": "https://acme.test"},
        "issues": [{"severity": "P2", "title": "Minor issue", "journeyId": "j1"}],
    }
    payload = build_share_payload(bundle, tmp_path, "run1", use_llm=False)
    assert payload["p0Count"] == 0
    assert "no P0 issues found" in payload["message"]


def test_share_payload_finds_signed_video_for_p0(tmp_path):
    from rehearse.share import build_share_payload

    run_id = "run1"
    video_dir = tmp_path / "artifacts" / run_id / "videos"
    video_dir.mkdir(parents=True)
    (video_dir / "j1-recording.webm").write_bytes(b"fake video")

    bundle = _bundle_with_p0(run_id=run_id, journey_id="j1")
    payload = build_share_payload(bundle, tmp_path, run_id, use_llm=False)

    assert len(payload["videos"]) == 1
    video = payload["videos"][0]
    assert video["journeyId"] == "j1"
    assert video["findingTitle"] == "Checkout button fails"
    assert video["url"].startswith("/files/")
    assert "sig=" in video["url"]


def test_share_payload_dedupes_videos_per_journey(tmp_path):
    """Two P0s in the same journey should produce one video entry, not two."""
    from rehearse.share import build_share_payload

    run_id = "run1"
    video_dir = tmp_path / "artifacts" / run_id / "videos"
    video_dir.mkdir(parents=True)
    (video_dir / "j1-recording.webm").write_bytes(b"fake video")

    bundle = {
        "summary": {"readiness": 40, "productName": "Acme", "targetUrl": "https://acme.test"},
        "issues": [
            {"severity": "P0", "title": "Checkout fails", "journeyId": "j1"},
            {"severity": "P0", "title": "Cart total wrong", "journeyId": "j1"},
        ],
    }
    payload = build_share_payload(bundle, tmp_path, run_id, use_llm=False)
    assert len(payload["videos"]) == 1


def test_share_payload_uses_llm_message_when_enabled(tmp_path):
    from rehearse.share import build_share_payload

    bundle = _bundle_with_p0()
    with patch("rehearse.llm.generate_share_message_llm", return_value={"message": "Custom LLM message"}):
        payload = build_share_payload(bundle, tmp_path, "run1", use_llm=True)
    assert payload["message"] == "Custom LLM message"


def test_share_payload_falls_back_when_llm_errors(tmp_path):
    from rehearse.share import build_share_payload

    bundle = _bundle_with_p0()
    with patch("rehearse.llm.generate_share_message_llm", return_value={"error": "timeout"}):
        payload = build_share_payload(bundle, tmp_path, "run1", use_llm=True)
    assert "P0" in payload["message"]
    assert payload["message"] != "Custom LLM message"


# ── llm.py: generate_share_message_llm ────────────────────────────────────────

def test_generate_share_message_llm_returns_none_without_api_key(monkeypatch):
    from rehearse.llm import generate_share_message_llm

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = generate_share_message_llm("Acme", 80, ["Checkout fails"])
    assert result is None
