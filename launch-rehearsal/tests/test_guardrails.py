"""Guardrails — workspace-configurable extra destructive-action keywords.

Settings/Profile audit found the destructive-action blocklist was entirely
hardcoded (deep_crawler._DESTRUCTIVE) with no payment guardrail and no way
for a customer to add product-specific terms (e.g. "downgrade my plan",
"terminate account"). extend_destructive_keywords() is the opt-in mechanism —
deliberately not pre-loaded with payment terms, since many products'
legitimate happy-path journeys include checkout testing.

_DESTRUCTIVE is process-global mutable state, so every test here snapshots
and restores it to avoid leaking keywords into other tests.
"""

from __future__ import annotations

import pytest

from rehearse.deep_crawler import _DESTRUCTIVE, _is_destructive, extend_destructive_keywords


@pytest.fixture(autouse=True)
def _restore_destructive_set():
    snapshot = set(_DESTRUCTIVE)
    yield
    _DESTRUCTIVE.clear()
    _DESTRUCTIVE.update(snapshot)


def test_baseline_destructive_keywords_still_block():
    assert _is_destructive("Delete account")
    assert _is_destructive("Sign out")


def test_payment_labels_not_blocked_by_default():
    """Confirms the deliberate design choice: payment terms aren't baked in."""
    assert not _is_destructive("Pay now")
    assert not _is_destructive("Place order")
    assert not _is_destructive("Complete purchase")


def test_extend_adds_custom_keyword():
    extend_destructive_keywords(["downgrade my plan"])
    assert _is_destructive("Downgrade My Plan")


def test_extend_is_case_insensitive():
    extend_destructive_keywords(["Terminate Account"])
    assert _is_destructive("please terminate account now")


def test_extend_ignores_blank_entries():
    before = set(_DESTRUCTIVE)
    extend_destructive_keywords(["", "   ", "\t"])
    assert _DESTRUCTIVE == before


def test_extend_does_not_remove_existing_keywords():
    extend_destructive_keywords(["custom-term"])
    assert _is_destructive("delete")
    assert _is_destructive("custom-term")


def test_unrelated_labels_still_pass():
    extend_destructive_keywords(["downgrade"])
    assert not _is_destructive("Continue")
    assert not _is_destructive("Learn more")
