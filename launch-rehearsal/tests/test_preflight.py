"""SSRF and preflight guard tests."""

from unittest.mock import patch

import pytest

from rehearse.errors import SSRFBlockedError
from rehearse.preflight import assert_url_allowed, _looks_like_auth_wall, preflight_head


def test_blocks_localhost():
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://localhost/dashboard")


def test_blocks_private_ip_literal():
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://127.0.0.1/")


def test_blocks_metadata_hostname():
    with pytest.raises(SSRFBlockedError):
        assert_url_allowed("http://metadata.google.internal/")


def test_allows_public_https_example():
    parsed = assert_url_allowed("https://example.com/path")
    assert parsed.hostname == "example.com"


def test_allows_localhost_when_opt_in():
    parsed = assert_url_allowed("http://127.0.0.1:8081/", allow_localhost=True)
    assert parsed.hostname == "127.0.0.1"
    assert parsed.port == 8081


def test_allows_localhost_hostname_when_opt_in():
    parsed = assert_url_allowed("http://localhost:8081/", allow_localhost=True)
    assert parsed.hostname == "localhost"


# ── auth-wall detection ───────────────────────────────────────────────────────
# Built after a real incident: a workspace's target URL resolved to
# /login with no auth configured, and the crawl found almost nothing —
# this is the safeguard so it's flagged before the workspace is created.


def test_detects_login_path():
    assert _looks_like_auth_wall("https://example.com/login")


def test_detects_signin_variants():
    assert _looks_like_auth_wall("https://example.com/signin")
    assert _looks_like_auth_wall("https://example.com/sign-in")
    assert _looks_like_auth_wall("https://example.com/log-in")


def test_detects_sso_and_auth_paths():
    assert _looks_like_auth_wall("https://example.com/sso/start")
    assert _looks_like_auth_wall("https://example.com/auth/callback")


def test_does_not_flag_ordinary_paths():
    assert not _looks_like_auth_wall("https://example.com/dashboard")
    assert not _looks_like_auth_wall("https://example.com/")
    assert not _looks_like_auth_wall("https://example.com/pricing")


def test_is_case_insensitive():
    assert _looks_like_auth_wall("https://example.com/LOGIN")


def test_preflight_head_flags_when_requested_url_is_login_path():
    """The exact incident scenario: the user-entered URL itself is /login,
    with no redirect involved at all."""
    class _FakeResponse:
        status_code = 200
        url = "https://faculty-dashboard-eight.vercel.app/login"

    with patch("rehearse.preflight._follow_redirect_safe", return_value=_FakeResponse()):
        result = preflight_head("https://faculty-dashboard-eight.vercel.app/login")

    assert result["looks_like_auth_wall"] is True
    assert result["redirected"] is False


def test_preflight_head_flags_when_redirected_to_login():
    class _FakeResponse:
        status_code = 200
        url = "https://example.com/login"

    with patch("rehearse.preflight._follow_redirect_safe", return_value=_FakeResponse()):
        result = preflight_head("https://example.com/dashboard")

    assert result["looks_like_auth_wall"] is True
    assert result["redirected"] is True


def test_preflight_head_does_not_flag_ordinary_url():
    class _FakeResponse:
        status_code = 200
        url = "https://example.com/dashboard"

    with patch("rehearse.preflight._follow_redirect_safe", return_value=_FakeResponse()):
        result = preflight_head("https://example.com/dashboard")

    assert result["looks_like_auth_wall"] is False
    assert result["redirected"] is False
