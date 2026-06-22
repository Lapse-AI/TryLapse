"""Real outbound notification dispatch — Slack + generic webhook.

The settings UI has advertised Slack/webhook alerts since the integration
catalog was first seeded (store.py get_integrations/get_alerts), but nothing
ever sent an HTTP request. This module is the part that was missing: actual
delivery, triggered when a run finishes.
"""

from __future__ import annotations

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

        should_slack = run_complete_enabled or (red_alert_enabled and gate in ("BLOCKED", "CAUTION"))
        if slack_url and should_slack:
            results["slack"] = send_slack_notification(slack_url, bundle)

        flake_rate = bundle.get("summary", {}).get("flakeRate", 0) or 0
        should_webhook = flake_alert_enabled and flake_rate > 0.05
        if webhook_url and should_webhook:
            results["webhook"] = send_generic_webhook(webhook_url, bundle)
    except Exception:
        pass
    return results
