"""Scorecard export — PDF and CSV.

Prior export options were JSON and GraphML (sitemap) only — no format a
person could open and read without dashboard access, or attach to an exec
email/Jira ticket. Covers the generation functions directly, plus the
/api/runs/{runId}/export.{pdf,csv} endpoints against a real running
server (auth-gated, same as /api/bundle/).
"""
from __future__ import annotations

import csv
import http.client
import importlib
import io
import json
import threading
import time
from pathlib import Path

import pytest

import rehearse.dashboard.server as server_module
from rehearse.dashboard.scorecard_export import generate_scorecard_csv, generate_scorecard_pdf


def _bundle(n_issues: int = 2) -> dict:
    return {
        "summary": {
            "id": "run-1",
            "productName": "Test Product",
            "targetUrl": "https://example.com",
            "launchGate": "BLOCKED",
            "verdict": "Do not launch — critical issues found.",
            "readiness": 42,
        },
        "dimensions": [
            {"name": "Functionality", "score": 80, "signal": "some signal text"},
            {"name": "Accessibility", "score": 60, "signal": "another signal"},
        ],
        "issues": [
            {
                "severity": ["P0", "P1", "P2", "P3"][i % 4],
                "title": f"Issue {i}",
                "persona": "Power user",
                "journey": "Checkout",
                "dimension": "Functionality",
                "recurring": i,
                "evidence": f"evidence text {i}",
            }
            for i in range(n_issues)
        ],
        "delights": [
            {"title": "Fast load", "quote": "Page loaded in under a second."},
        ],
    }


# ── PDF generation ───────────────────────────────────────────────────────────


def test_pdf_starts_with_valid_header():
    pdf_bytes = generate_scorecard_pdf(_bundle())
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_handles_unicode_content_without_crashing():
    """Regression: fpdf2's core Helvetica font is Latin-1 only — real verdict/
    narrative text contains em-dashes and similar characters that crashed
    generation before the bundled DejaVu Unicode font was wired in."""
    bundle = _bundle()
    bundle["summary"]["verdict"] = "Do not launch — critical issues — found across personas."
    pdf_bytes = generate_scorecard_pdf(bundle)
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_caps_pathologically_large_issue_counts():
    """Regression: a real historical bundle had 9066 duplicated issues —
    rendering all of them would produce a multi-thousand-page PDF."""
    bundle = _bundle(n_issues=5000)
    pdf_bytes = generate_scorecard_pdf(bundle)
    assert pdf_bytes.startswith(b"%PDF-")
    # Capped output should stay well under what 5000 uncapped issues would produce
    assert len(pdf_bytes) < 200_000


def test_pdf_handles_empty_bundle_gracefully():
    pdf_bytes = generate_scorecard_pdf({"summary": {}})
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_handles_missing_dimensions_and_delights():
    bundle = _bundle()
    del bundle["dimensions"]
    del bundle["delights"]
    pdf_bytes = generate_scorecard_pdf(bundle)
    assert pdf_bytes.startswith(b"%PDF-")


# ── CSV generation ───────────────────────────────────────────────────────────


def test_csv_is_well_formed_and_round_trips():
    csv_text = generate_scorecard_csv(_bundle(n_issues=3))
    rows = list(csv.reader(io.StringIO(csv_text)))
    header_idx = rows.index(
        ["Severity", "Title", "Persona", "Journey", "Dimension", "Recurring", "Evidence"]
    )
    issue_rows = rows[header_idx + 1:]
    assert len(issue_rows) == 3
    assert issue_rows[0][1] == "Issue 0"


def test_csv_includes_summary_header_block():
    csv_text = generate_scorecard_csv(_bundle())
    assert "Test Product" in csv_text
    assert "BLOCKED" in csv_text


def test_csv_is_not_capped_unlike_pdf():
    """CSV is a full data dump for filtering/analysis — the PDF cap
    (readability) doesn't apply here."""
    csv_text = generate_scorecard_csv(_bundle(n_issues=500))
    rows = list(csv.reader(io.StringIO(csv_text)))
    header_idx = rows.index(
        ["Severity", "Title", "Persona", "Journey", "Dimension", "Recurring", "Evidence"]
    )
    assert len(rows) - header_idx - 1 == 500


def test_csv_handles_embedded_commas_and_quotes():
    bundle = _bundle(n_issues=1)
    bundle["issues"][0]["evidence"] = 'Text with, a comma and "quoted" content'
    csv_text = generate_scorecard_csv(bundle)
    rows = list(csv.reader(io.StringIO(csv_text)))
    evidence_cell = rows[-1][-1]
    assert evidence_cell == 'Text with, a comma and "quoted" content'


# ── API endpoints (real running server) ──────────────────────────────────────


@pytest.fixture
def live_server_with_bundle(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REHEARSE_DISABLE_AUTH", "1")
    importlib.reload(server_module)

    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir(parents=True)
    (analysis_dir / "run-export-test.json").write_text(json.dumps(_bundle(n_issues=3)))

    srv, _ = server_module._bind_server("127.0.0.1", 0, tmp_path)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    try:
        yield port
    finally:
        srv.shutdown()
        monkeypatch.delenv("REHEARSE_DISABLE_AUTH", raising=False)
        importlib.reload(server_module)


def _get_raw(port: int, path: str) -> tuple[int, dict, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    headers = dict(resp.getheaders())
    data = resp.read()
    conn.close()
    return resp.status, headers, data


def test_export_pdf_endpoint_returns_valid_pdf(live_server_with_bundle):
    status, headers, data = _get_raw(live_server_with_bundle, "/api/runs/run-export-test/export.pdf")
    assert status == 200
    assert headers.get("Content-Type") == "application/pdf"
    assert data.startswith(b"%PDF-")
    assert "run-export-test-scorecard.pdf" in headers.get("Content-Disposition", "")


def test_export_csv_endpoint_returns_valid_csv(live_server_with_bundle):
    status, headers, data = _get_raw(live_server_with_bundle, "/api/runs/run-export-test/export.csv")
    assert status == 200
    assert headers.get("Content-Type") == "text/csv"
    assert b"Severity,Title" in data


def test_export_endpoint_404s_for_unknown_run(live_server_with_bundle):
    status, _, _ = _get_raw(live_server_with_bundle, "/api/runs/does-not-exist/export.pdf")
    assert status == 404


def test_export_endpoint_rejects_path_traversal_run_id(live_server_with_bundle):
    status, _, _ = _get_raw(live_server_with_bundle, "/api/runs/..%2F..%2Fetc%2Fpasswd/export.pdf")
    assert status in (400, 404)
