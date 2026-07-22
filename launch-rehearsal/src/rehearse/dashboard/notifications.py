"""Real outbound notification dispatch — Slack, generic webhook, and email.

The settings UI has advertised Slack/webhook alerts since the integration
catalog was first seeded (store.py get_integrations/get_alerts), but nothing
ever sent an HTTP request. This module is the part that was missing: actual
delivery, triggered when a run finishes.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import httpx

_TIMEOUT_S = 8.0

_GATE_EMOJI = {
    "PASS": "✅",
    "REVIEW": "🔎",
    "CAUTION": "⚠️",
    "BLOCKED": "⛔",
}


def _post_json(url: str, payload: dict[str, Any]) -> bool:
    """POST a JSON payload; return True on 2xx, False otherwise. Never raises."""
    try:
        resp = httpx.post(url, json=payload, timeout=_TIMEOUT_S)
        return 200 <= resp.status_code < 300
    except Exception:
        return False


def format_slack_message(bundle: dict[str, Any]) -> dict[str, Any]:
    """Build a Slack incoming-webhook payload from a run's analysis bundle."""
    summary = bundle.get("summary", {})
    gate = summary.get("launchGate", "REVIEW")
    emoji = _GATE_EMOJI.get(gate, "")
    product = summary.get("productName", "Unknown product")
    readiness = summary.get("readiness")
    verdict = summary.get("verdict", "")
    run_id = summary.get("id", "")

    text = f"{emoji} *{gate}* — {product} — readiness {readiness}\n{verdict}"
    return {
        "text": text,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Run `{run_id}`"}],
            },
        ],
    }


def send_slack_notification(webhook_url: str, bundle: dict[str, Any]) -> bool:
    return _post_json(webhook_url, format_slack_message(bundle))


def send_generic_webhook(webhook_url: str, bundle: dict[str, Any]) -> bool:
    """POST the raw summary fields a downstream system would need to act on a run."""
    summary = bundle.get("summary", {})
    payload = {
        "event": "run.complete",
        "runId": summary.get("id"),
        "productName": summary.get("productName"),
        "launchGate": summary.get("launchGate"),
        "verdict": summary.get("verdict"),
        "readiness": summary.get("readiness"),
        "flakeRate": summary.get("flakeRate"),
        "targetUrl": summary.get("targetUrl"),
    }
    return _post_json(webhook_url, payload)


def format_email_message(bundle: dict[str, Any]) -> tuple[str, str]:
    """Build (subject, body) for a run-complete email — stdlib-only, plain text."""
    summary = bundle.get("summary", {})
    gate = summary.get("launchGate", "REVIEW")
    emoji = _GATE_EMOJI.get(gate, "")
    product = summary.get("productName", "Unknown product")
    readiness = summary.get("readiness")
    verdict = summary.get("verdict", "")
    run_id = summary.get("id", "")
    target_url = summary.get("targetUrl", "")

    subject = f"{emoji} {gate} — {product} readiness {readiness}"
    body = (
        f"{product} — {gate}\n"
        f"Readiness: {readiness}\n"
        f"Target: {target_url}\n\n"
        f"{verdict}\n\n"
        f"Run: {run_id}"
    )
    return subject, body


def send_email_notification(to_email: str, bundle: dict[str, Any]) -> bool:
    """Send a run-complete email via SMTP. stdlib only (smtplib), matching the
    rest of the auth/notification stack's no-external-dependencies approach.

    Requires SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM in the
    environment. Without SMTP_HOST configured, this logs the message to the
    console instead of sending (same mock-mode pattern as password reset)
    and returns False — the caller should not treat that as a delivery
    failure worth surfacing, just as "email isn't wired up in this
    environment yet."
    """
    host = os.environ.get("SMTP_HOST")
    subject, body = format_email_message(bundle)

    if not host:
        print(f"\n📧 EMAIL NOTIFICATION (SMTP_HOST not set — logging instead)\n"
              f"   To: {to_email}\n   Subject: {subject}\n   {body}\n", flush=True)
        return False

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    from_addr = os.environ.get("SMTP_FROM", user or "noreply@trylapse.dev")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=_TIMEOUT_S) as smtp:
            smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def notify_run_complete(artifacts_root: Path, run_id: str) -> dict[str, bool]:
    """Dispatch all enabled alerts for a completed run. Returns {channel: delivered}.

    Reads workspace config for webhook URLs and which alerts are enabled —
    never raises; a notification failure must never fail the run itself.
    """
    from rehearse.dashboard.store import get_alerts, get_workspace, load_bundle

    results: dict[str, bool] = {}
    try:
        bundle = load_bundle(artifacts_root, run_id, rebuild=False)
        if not bundle:
            return results

        ws = get_workspace(artifacts_root)
        alerts = get_alerts(artifacts_root)
        alerts_by_id = {a["id"]: a for a in alerts}

        gate = bundle.get("summary", {}).get("launchGate")
        run_complete_enabled = alerts_by_id.get("al_ws", {}).get("enabled", False)
        red_alert_enabled = alerts_by_id.get("al_red", {}).get("enabled", False)
        flake_alert_enabled = alerts_by_id.get("al_flake", {}).get("enabled", False)

        slack_url = ws.get("slackWebhookUrl")
        webhook_url = ws.get("webhookUrl")
        notify_email = ws.get("notifyEmail")

        should_slack = run_complete_enabled or (red_alert_enabled and gate in ("BLOCKED", "CAUTION"))
        if slack_url and should_slack:
            results["slack"] = send_slack_notification(slack_url, bundle)

        should_email = run_complete_enabled or (red_alert_enabled and gate in ("BLOCKED", "CAUTION"))
        if notify_email and should_email:
            results["email"] = send_email_notification(notify_email, bundle)

        flake_rate = bundle.get("summary", {}).get("flakeRate", 0) or 0
        should_webhook = flake_alert_enabled and flake_rate > 0.05
        if webhook_url and should_webhook:
            results["webhook"] = send_generic_webhook(webhook_url, bundle)
    except Exception:
        pass
    return results
