"""Billing — plan-tier quota enforcement + Stripe checkout/webhook.

Zero paying customers exist yet, so this is built to be checkout-ready the
moment a Stripe account is connected, but must never raise or break runs
just because STRIPE_SECRET_KEY isn't set — same degrade-without-key pattern
already used for LLM providers.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from rehearse.dashboard.billing import (
    DEFAULT_PLAN,
    PLAN_LIMITS,
    billing_enabled,
    check_quota,
    create_checkout_session,
    handle_webhook_event,
    normalize_plan,
)
from rehearse.dashboard.job_store import save_job


# ── billing_enabled / normalize_plan ─────────────────────────────────────────


def test_billing_disabled_without_key(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    assert billing_enabled() is False


def test_billing_enabled_with_key(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    assert billing_enabled() is True


def test_normalize_plan_known():
    assert normalize_plan("growth") == "growth"


def test_normalize_plan_unknown_falls_back_to_default():
    assert normalize_plan("nonexistent-tier") == DEFAULT_PLAN
    assert normalize_plan(None) == DEFAULT_PLAN


# ── check_quota ───────────────────────────────────────────────────────────────


def test_design_partner_plan_is_unlimited(tmp_path: Path):
    quota = check_quota(tmp_path, "acme", "design_partner")
    assert quota["limit"] is None
    assert quota["allowed"] is True


def test_scale_plan_is_unlimited(tmp_path: Path):
    quota = check_quota(tmp_path, "acme", "scale")
    assert quota["limit"] is None
    assert quota["allowed"] is True


def test_starter_plan_blocks_after_limit(tmp_path: Path):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    for i in range(PLAN_LIMITS["starter"]):
        save_job(
            tmp_path,
            {"id": f"j{i}", "status": "done", "config": "/configs/acme.yaml",
             "startedAt": now, "finishedAt": now},
        )
    quota = check_quota(tmp_path, "acme", "starter")
    assert quota["runsThisMonth"] == PLAN_LIMITS["starter"]
    assert quota["allowed"] is False


def test_starter_plan_allows_under_limit(tmp_path: Path):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    save_job(
        tmp_path,
        {"id": "j1", "status": "done", "config": "/configs/acme.yaml",
         "startedAt": now, "finishedAt": now},
    )
    quota = check_quota(tmp_path, "acme", "starter")
    assert quota["runsThisMonth"] == 1
    assert quota["allowed"] is True


def test_check_quota_normalizes_unknown_plan(tmp_path: Path):
    quota = check_quota(tmp_path, "acme", "made-up-plan")
    assert quota["plan"] == DEFAULT_PLAN


# ── create_checkout_session ──────────────────────────────────────────────────


def test_checkout_session_fails_without_stripe_key(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    result = create_checkout_session("growth", "acme", "https://x/success", "https://x/cancel")
    assert "error" in result


def test_checkout_session_rejects_non_self_serve_plan(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    result = create_checkout_session("scale", "acme", "https://x/success", "https://x/cancel")
    assert "error" in result
    assert "contact sales" in result["error"]


def test_checkout_session_fails_without_price_id(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.delenv("STRIPE_PRICE_GROWTH", raising=False)
    result = create_checkout_session("growth", "acme", "https://x/success", "https://x/cancel")
    assert "error" in result
    assert "STRIPE_PRICE_GROWTH" in result["error"]


def test_checkout_session_success(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_123")

    mock_session = MagicMock(url="https://checkout.stripe.com/abc", id="cs_test_abc")
    with patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        result = create_checkout_session("growth", "acme", "https://x/success", "https://x/cancel")

    assert result == {"url": "https://checkout.stripe.com/abc", "sessionId": "cs_test_abc"}
    mock_create.assert_called_once()
    assert mock_create.call_args.kwargs["client_reference_id"] == "acme"
    assert mock_create.call_args.kwargs["metadata"] == {"workspaceSlug": "acme", "plan": "growth"}


def test_checkout_session_handles_stripe_exception(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_STARTER", "price_456")
    with patch("stripe.checkout.Session.create", side_effect=RuntimeError("network down")):
        result = create_checkout_session("starter", "acme", "https://x/success", "https://x/cancel")
    assert "error" in result


# ── handle_webhook_event ──────────────────────────────────────────────────────


def test_webhook_disabled_without_key(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    result = handle_webhook_event(tmp_path, b"{}", "sig")
    assert result["handled"] is False


def test_webhook_invalid_signature(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    with patch("stripe.Webhook.construct_event", side_effect=ValueError("bad sig")):
        result = handle_webhook_event(tmp_path, b"{}", "bad-sig")
    assert result["handled"] is False
    assert "error" in result


def test_webhook_checkout_completed_upgrades_plan(tmp_path: Path, monkeypatch):
    from rehearse.dashboard.auth_store import create_user, ensure_users_table
    from rehearse.dashboard.workspace_store import (
        create_workspace, ensure_workspaces_table, ensure_membership_tables, get_workspace_by_slug,
    )

    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)
    owner = create_user(tmp_path, email="o@example.com", password="pw123456", name="Owner")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Acme", target_url="https://acme.com",
        product_name="Acme", team_role="founder",
    )
    ws = get_workspace_by_slug(tmp_path, "acme")
    assert ws["plan"] == "design_partner"

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    fake_event = {
        "type": "checkout.session.completed",
        "data": {"object": {"client_reference_id": "acme", "metadata": {"workspaceSlug": "acme", "plan": "growth"}}},
    }
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        result = handle_webhook_event(tmp_path, b"{}", "sig")

    assert result == {"handled": True, "type": "checkout.session.completed"}
    updated = get_workspace_by_slug(tmp_path, "acme")
    assert updated["plan"] == "growth"


def test_webhook_subscription_deleted_demotes_to_default(tmp_path: Path, monkeypatch):
    from rehearse.dashboard.auth_store import create_user, ensure_users_table
    from rehearse.dashboard.workspace_store import (
        create_workspace, ensure_workspaces_table, ensure_membership_tables,
        get_workspace_by_slug, set_workspace_plan,
    )

    ensure_users_table(tmp_path)
    ensure_workspaces_table(tmp_path)
    ensure_membership_tables(tmp_path)
    owner = create_user(tmp_path, email="o2@example.com", password="pw123456", name="Owner")
    create_workspace(
        tmp_path, owner_id=owner["id"], name="Acme2", target_url="https://acme2.com",
        product_name="Acme2", team_role="founder",
    )
    set_workspace_plan(tmp_path, "acme2", "growth")

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    fake_event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"metadata": {"workspaceSlug": "acme2"}, "status": "canceled"}},
    }
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        result = handle_webhook_event(tmp_path, b"{}", "sig")

    assert result["handled"] is True
    updated = get_workspace_by_slug(tmp_path, "acme2")
    assert updated["plan"] == DEFAULT_PLAN


def test_webhook_unrelated_event_not_handled(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    fake_event = {"type": "invoice.paid", "data": {"object": {}}}
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        result = handle_webhook_event(tmp_path, b"{}", "sig")
    assert result == {"handled": False, "type": "invoice.paid"}
