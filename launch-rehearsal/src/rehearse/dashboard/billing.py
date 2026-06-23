"""Billing — Stripe checkout, webhooks, and plan-tier quota enforcement.

Plan tiers match the pricing set during the deployment-readiness review:
  design_partner — free/$99, 90-day cap, unlimited runs (traded for outcome
                   data + a testimonial + a weekly call). The default for
                   every workspace until it converts.
  starter        — $299/mo, 8 runs/mo
  growth         — $799/mo, 30 runs/mo
  scale          — custom pricing, unlimited, contract negotiated outside
                   Stripe — not self-serve, no checkout session for it.

Gracefully no-ops when STRIPE_SECRET_KEY isn't set. Nothing in this module
ever raises just because billing isn't configured — same degrade-without-key
pattern already used for LLM providers (rehearse.llm.llm_enabled()). Zero
paying customers exist yet; this module enforces quota and is checkout-ready
the moment a Stripe account is connected.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from rehearse.dashboard.usage_store import usage_for_workspace

PLAN_LIMITS: dict[str, int | None] = {
    "design_partner": None,
    "starter": 8,
    "growth": 30,
    "scale": None,
}

# Self-serve plans only — scale is sales-assisted, no Stripe Price ID expected.
PLAN_PRICES_USD: dict[str, int] = {
    "starter": 299,
    "growth": 799,
}

DEFAULT_PLAN = "design_partner"


def billing_enabled() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY"))


def normalize_plan(plan: str | None) -> str:
    return plan if plan in PLAN_LIMITS else DEFAULT_PLAN


def check_quota(artifacts_root: Path, workspace_slug: str, plan: str | None) -> dict[str, Any]:
    """Return usage + whether another run is allowed under the current plan."""
    plan = normalize_plan(plan)
    limit = PLAN_LIMITS[plan]
    usage = usage_for_workspace(artifacts_root, workspace_slug)
    used = usage["runsThisMonth"]
    allowed = limit is None or used < limit
    return {**usage, "plan": plan, "limit": limit, "allowed": allowed}


def _stripe():
    import stripe  # local import — optional dependency, see pyproject.toml [billing]
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    return stripe


def create_checkout_session(
    plan: str, workspace_slug: str, success_url: str, cancel_url: str
) -> dict[str, Any]:
    """Create a Stripe Checkout session for a self-serve plan upgrade."""
    if not billing_enabled():
        return {"error": "Billing not configured — set STRIPE_SECRET_KEY"}
    plan = normalize_plan(plan)
    if plan not in PLAN_PRICES_USD:
        return {"error": f"'{plan}' is not self-serve — contact sales for the Scale plan"}
    price_env = f"STRIPE_PRICE_{plan.upper()}"
    price_id = os.environ.get(price_env)
    if not price_id:
        return {"error": f"{price_env} is not configured"}
    try:
        stripe = _stripe()
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=workspace_slug,
            metadata={"workspaceSlug": workspace_slug, "plan": plan},
        )
        return {"url": session.url, "sessionId": session.id}
    except Exception as exc:
        return {"error": str(exc)[:300]}


def handle_webhook_event(artifacts_root: Path, payload: bytes, sig_header: str) -> dict[str, Any]:
    """Verify and process a Stripe webhook event.

    On checkout.session.completed, promotes the workspace to the plan paid
    for. On subscription cancellation, demotes back to design_partner
    (which is unlimited during the trial window, not a hard cutoff — billing
    failure should never silently brick someone's rehearsals).
    """
    if not billing_enabled():
        return {"handled": False, "error": "Billing not configured"}

    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    try:
        stripe = _stripe()
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as exc:
        return {"handled": False, "error": str(exc)[:300]}

    from rehearse.dashboard.workspace_store import set_workspace_plan

    etype = event["type"]
    data_object = event["data"]["object"]

    if etype == "checkout.session.completed":
        slug = data_object.get("client_reference_id") or (data_object.get("metadata") or {}).get(
            "workspaceSlug"
        )
        plan = (data_object.get("metadata") or {}).get("plan")
        if slug and plan:
            set_workspace_plan(artifacts_root, slug, normalize_plan(plan))
        return {"handled": True, "type": etype}

    if etype in ("customer.subscription.deleted", "customer.subscription.updated"):
        slug = (data_object.get("metadata") or {}).get("workspaceSlug")
        status = data_object.get("status")
        if slug and (etype == "customer.subscription.deleted" or status in ("canceled", "unpaid")):
            set_workspace_plan(artifacts_root, slug, DEFAULT_PLAN)
        return {"handled": True, "type": etype}

    return {"handled": False, "type": etype}
