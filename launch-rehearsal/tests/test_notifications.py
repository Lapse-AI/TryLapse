"""Real Slack/webhook dispatch on run completion — Carmack/Schneier's board finding.

The settings UI advertised Slack alerts ("status": "available") since the
integration catalog was first seeded, but no outbound HTTP request ever
existed. These tests cover the actual dispatcher, alert enable/disable
persistence, and the decision logic for when to fire.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from rehearse.dashboard.notifications import (
    format_email_message,
    format_outcome_follow_up_message,
    format_slack_message,
    notify_run_complete,
    send_email_notification,
    send_generic_webhook,
    send_outcome_follow_up_email,
    send_slack_notification,
)
from rehearse.dashboard.store import get_alerts, get_workspace, save_workspace, update_alert


def _bundle(gate: str = "BLOCKED", flake_rate: float = 0.0) -> dict:
    return {
        "summary": {
            "id": "run-1",
            "productName": "Test Product",
            "launchGate": gate,
            "verdict": f"verdict for {gate}",
            "readiness": 40,
            "flakeRate": flake_rate,
            "targetUrl": "https://example.com",
        }
    }


# ── message formatting ───────────────────────────────────────────────────────


def test_slack_message_includes_gate_and_product():
    payload = format_slack_message(_bundle("BLOCKED"))
    assert "BLOCKED" in payload["text"]
    assert "Test Product" in payload["text"]


def test_slack_message_has_run_id_context():
    payload = format_slack_message(_bundle())
    context_text = payload["blocks"][1]["elements"][0]["text"]
    assert "run-1" in context_text


# ── dispatch (mocked HTTP) ───────────────────────────────────────────────────


def test_send_slack_notification_posts_to_webhook_url():
    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        ok = send_slack_notification("https://hooks.slack.com/x", _bundle())
    assert ok is True
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://hooks.slack.com/x"


def test_send_slack_notification_returns_false_on_http_error():
    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        mock_post.return_value.status_code = 500
        ok = send_slack_notification("https://hooks.slack.com/x", _bundle())
    assert ok is False


def test_send_slack_notification_returns_false_on_exception():
    with patch("rehearse.dashboard.notifications.httpx.post", side_effect=Exception("network down")):
        ok = send_slack_notification("https://hooks.slack.com/x", _bundle())
    assert ok is False


def test_send_generic_webhook_payload_shape():
    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_generic_webhook("https://example.com/hook", _bundle("CAUTION", flake_rate=0.2))
    payload = mock_post.call_args.kwargs["json"]
    assert payload["event"] == "run.complete"
    assert payload["launchGate"] == "CAUTION"
    assert payload["flakeRate"] == 0.2


# ── alert persistence ─────────────────────────────────────────────────────────


def test_get_alerts_default_state(tmp_path: Path):
    alerts = get_alerts(tmp_path)
    by_id = {a["id"]: a for a in alerts}
    assert by_id["al_ws"]["enabled"] is True
    assert by_id["al_flake"]["enabled"] is False


def test_update_alert_persists(tmp_path: Path):
    update_alert(tmp_path, "al_flake", True)
    alerts = get_alerts(tmp_path)
    by_id = {a["id"]: a for a in alerts}
    assert by_id["al_flake"]["enabled"] is True
    # unrelated alert unaffected
    assert by_id["al_ws"]["enabled"] is True


def test_update_alert_rejects_unknown_id(tmp_path: Path):
    import pytest
    with pytest.raises(ValueError):
        update_alert(tmp_path, "al_does_not_exist", True)


def test_update_alert_disable_persists_across_calls(tmp_path: Path):
    update_alert(tmp_path, "al_ws", False)
    alerts = get_alerts(tmp_path)
    by_id = {a["id"]: a for a in alerts}
    assert by_id["al_ws"]["enabled"] is False


def test_workspace_has_webhook_url_fields(tmp_path: Path):
    ws = get_workspace(tmp_path)
    assert "slackWebhookUrl" in ws
    assert "webhookUrl" in ws
    assert ws["slackWebhookUrl"] is None


# ── notify_run_complete orchestration ────────────────────────────────────────


def _setup_workspace_with_slack(tmp_path: Path, *, al_ws_enabled: bool = True) -> None:
    ws = get_workspace(tmp_path)
    ws["slackWebhookUrl"] = "https://hooks.slack.com/services/x"
    save_workspace(tmp_path, ws)
    update_alert(tmp_path, "al_ws", al_ws_enabled)


def _write_analysis_bundle(tmp_path: Path, run_id: str, gate: str, flake_rate: float = 0.0) -> None:
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / f"{run_id}.json").write_text(json.dumps(_bundle(gate, flake_rate) | {
        "summary": {**_bundle(gate, flake_rate)["summary"], "id": run_id}
    }))


def test_notify_run_complete_fires_slack_when_enabled(tmp_path: Path):
    _setup_workspace_with_slack(tmp_path, al_ws_enabled=True)
    _write_analysis_bundle(tmp_path, "run-x", "BLOCKED")

    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        results = notify_run_complete(tmp_path, "run-x")

    assert results.get("slack") is True
    mock_post.assert_called_once()


def test_notify_run_complete_skips_when_alert_disabled(tmp_path: Path):
    _setup_workspace_with_slack(tmp_path, al_ws_enabled=False)
    update_alert(tmp_path, "al_red", False)
    _write_analysis_bundle(tmp_path, "run-y", "PASS")

    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        notify_run_complete(tmp_path, "run-y")

    mock_post.assert_not_called()


def test_notify_run_complete_fires_on_blocked_even_if_only_red_alert_enabled(tmp_path: Path):
    """al_ws off, but al_red on + gate is BLOCKED — should still fire."""
    _setup_workspace_with_slack(tmp_path, al_ws_enabled=False)
    update_alert(tmp_path, "al_red", True)
    _write_analysis_bundle(tmp_path, "run-z", "BLOCKED")

    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        results = notify_run_complete(tmp_path, "run-z")

    assert results.get("slack") is True


def test_notify_run_complete_no_webhook_url_means_no_dispatch(tmp_path: Path):
    update_alert(tmp_path, "al_ws", True)
    _write_analysis_bundle(tmp_path, "run-w", "BLOCKED")

    with patch("rehearse.dashboard.notifications.httpx.post") as mock_post:
        results = notify_run_complete(tmp_path, "run-w")

    assert results == {}
    mock_post.assert_not_called()


def test_notify_run_complete_missing_bundle_does_not_raise(tmp_path: Path):
    _setup_workspace_with_slack(tmp_path, al_ws_enabled=True)
    results = notify_run_complete(tmp_path, "nonexistent-run")
    assert results == {}


# ── email ─────────────────────────────────────────────────────────────────────


def test_email_message_includes_gate_readiness_verdict():
    subject, body = format_email_message(_bundle("BLOCKED"))
    assert "BLOCKED" in subject
    assert "Test Product" in subject
    assert "verdict for BLOCKED" in body
    assert "run-1" in body


def test_send_email_without_smtp_host_logs_instead_of_sending(monkeypatch, capsys):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    ok = send_email_notification("team@example.com", _bundle())
    assert ok is False
    captured = capsys.readouterr()
    assert "team@example.com" in captured.out


def test_send_email_with_smtp_configured_sends_via_smtplib(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "bot@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")

    with patch("rehearse.dashboard.notifications.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = mock_smtp_cls.return_value.__enter__.return_value
        ok = send_email_notification("team@example.com", _bundle("BLOCKED"))

    assert ok is True
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("bot@example.com", "secret")
    mock_smtp.send_message.assert_called_once()
    sent_msg = mock_smtp.send_message.call_args.args[0]
    assert sent_msg["To"] == "team@example.com"


def test_send_email_returns_false_on_smtp_exception(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    with patch("rehearse.dashboard.notifications.smtplib.SMTP", side_effect=Exception("connection refused")):
        ok = send_email_notification("team@example.com", _bundle())
    assert ok is False


def test_notify_run_complete_fires_email_when_notify_email_set(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    ws = get_workspace(tmp_path)
    ws["notifyEmail"] = "stakeholder@example.com"
    save_workspace(tmp_path, ws)
    update_alert(tmp_path, "al_ws", True)
    _write_analysis_bundle(tmp_path, "run-email", "BLOCKED")

    with patch("rehearse.dashboard.notifications.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value
        results = notify_run_complete(tmp_path, "run-email")

    assert results.get("email") is True


def test_notify_run_complete_skips_email_when_not_configured(tmp_path: Path):
    update_alert(tmp_path, "al_ws", True)
    _write_analysis_bundle(tmp_path, "run-noemail", "BLOCKED")
    results = notify_run_complete(tmp_path, "run-noemail")
    assert "email" not in results


def test_workspace_has_notify_email_field(tmp_path: Path):
    ws = get_workspace(tmp_path)
    assert "notifyEmail" in ws
    assert ws["notifyEmail"] is None


# ── T+7 outcome follow-up email ──────────────────────────────────────────────


def test_outcome_follow_up_message_includes_run_and_link():
    subject, body = format_outcome_follow_up_message(
        "run-1", "https://example.com", "https://dash.example.com/runs/run-1"
    )
    assert "run-1" in body or "run-1" in subject
    assert "https://example.com" in subject
    assert "https://dash.example.com/runs/run-1" in body


def test_send_outcome_follow_up_email_without_smtp_logs_instead(monkeypatch, capsys):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    ok = send_outcome_follow_up_email("owner@acme.com", "run-1", "https://example.com", "https://dash/x")
    assert ok is False
    assert "owner@acme.com" in capsys.readouterr().out
