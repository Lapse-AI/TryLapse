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
