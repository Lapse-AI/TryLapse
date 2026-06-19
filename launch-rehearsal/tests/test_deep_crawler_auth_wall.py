"""Tests for the hardened auth-wall detector in deep_crawler.py.

A false positive here causes the crawler to abandon a perfectly authenticated
page without capturing any data — exactly the "stopped after login + database"
symptom this fix targets.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from rehearse.deep_crawler import _detect_auth_wall


def _mock_page(url: str, body_text: str = "", password_input=None):
    page = MagicMock()
    page.url = url
    page.query_selector.return_value = password_input
    page.inner_text.return_value = body_text
    return page


def test_login_url_path_segment_is_a_real_signal():
    page = _mock_page("https://app.test/login")
    assert _detect_auth_wall(page) is True


def test_auth_path_segment_is_a_real_signal():
    page = _mock_page("https://app.test/auth")
    assert _detect_auth_wall(page) is True


def test_url_containing_auth_as_substring_not_segment_is_not_a_false_positive():
    """'/dashboard/authors' must not match — 'auth' is a substring, not a path segment."""
    page = _mock_page("https://app.test/dashboard/authors")
    assert _detect_auth_wall(page) is False


def test_visible_password_input_is_a_real_signal():
    pw_input = MagicMock()
    pw_input.is_visible.return_value = True
    page = _mock_page("https://app.test/database", password_input=pw_input)
    assert _detect_auth_wall(page) is True


def test_hidden_password_input_is_not_a_false_positive():
    """A pre-rendered, hidden 'change password' modal must not trigger the auth wall."""
    pw_input = MagicMock()
    pw_input.is_visible.return_value = False
    page = _mock_page("https://app.test/database", password_input=pw_input)
    assert _detect_auth_wall(page) is False


def test_login_phrase_on_sparse_page_is_a_real_signal():
    page = _mock_page("https://app.test/gate", body_text="Please login to continue.")
    assert _detect_auth_wall(page) is True


def test_login_phrase_on_rich_content_page_is_not_a_false_positive():
    """A 'sign in to comment' widget on an otherwise rich, authenticated page must not trigger."""
    rich_body = "Faculty Dashboard " + ("Course schedule and research data. " * 20) + "Sign in to comment on this post."
    page = _mock_page("https://app.test/database", body_text=rich_body)
    assert _detect_auth_wall(page) is False


def test_normal_authenticated_page_has_no_false_positive():
    page = _mock_page("https://app.test/database", body_text="Database overview: 42 records found.")
    assert _detect_auth_wall(page) is False
