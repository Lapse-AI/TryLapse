"""SSRF and preflight guard tests."""

import pytest

from rehearse.errors import SSRFBlockedError
from rehearse.preflight import assert_url_allowed


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
