"""Portable scorecard export — PDF and CSV.

Prior export options were JSON and GraphML (sitemap) only — no format a
person could open and read without dashboard access, or attach to an exec
email/Jira ticket. This is the part that was missing.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

_GATE_LABEL = {
    "PASS": "PASS",
    "REVIEW": "REVIEW",
    "CAUTION": "CAUTION",
    "BLOCKED": "BLOCKED",
}

# A run with a runaway/duplicated issue count (seen in practice: one old
# analysis bundle had 9066 "issues") would otherwise generate a
# multi-thousand-page PDF. Cap and point to the CSV/JSON export instead of
# either truncating silently or trying to render everything.
_MAX_ISSUES_IN_PDF = 200

# Bundled Unicode font — real content (LLM verdicts/narratives, issue titles,
# international product/persona names) routinely contains characters outside
# fpdf2's built-in core-font Latin-1 range (em-dashes, curly quotes, accented
# characters). Shipping DejaVu Sans avoids depending on whatever fonts happen
# to be installed on the machine/container running the export — it must work
# identically on a fresh Docker image as it does locally. DejaVu fonts are
# Bitstream Vera-licensed, free for embedding/redistribution (the same font
# matplotlib bundles for the same reason).
_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
_FONT_NAME = "DejaVu"


def generate_scorecard_csv(bundle: dict[str, Any]) -> str:
    """One row per issue — severity, title, persona, journey, evidence.

    Deliberately issue-centric rather than a single summary row: the CSV's
    job is "let me filter/sort/pivot the findings in a spreadsheet," which a
    one-row summary can't do. Summary fields are still included via a header
    block so the file is self-describing without needing the dashboard open.
    """
    summary = bundle.get("summary", {})
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Product", summary.get("productName", "")])
    writer.writerow(["Target URL", summary.get("targetUrl", "")])
    writer.writerow(["Run ID", summary.get("id", "")])
    writer.writerow(["Readiness", summary.get("readiness", "")])
    writer.writerow(["Launch Gate", summary.get("launchGate", "")])
    writer.writerow(["Verdict", summary.get("verdict", "")])
    writer.writerow([])

    writer.writerow(
        ["Severity", "Title", "Persona", "Journey", "Dimension", "Recurring", "Evidence"]
    )
    for issue in bundle.get("issues", []):
        writer.writerow([
            issue.get("severity", ""),
            issue.get("title", ""),
            issue.get("persona", ""),
            issue.get("journey", ""),
            issue.get("dimension", ""),
            issue.get("recurring", ""),
            (issue.get("evidence") or issue.get("detail") or "")[:500],
        ])

    return buf.getvalue()


def generate_scorecard_pdf(bundle: dict[str, Any]) -> bytes:
    """A one-shareable-document readiness scorecard: score, gate, dimension
    breakdown, issues (sorted by severity), delights.
    """
    from fpdf import FPDF

    summary = bundle.get("summary", {})
    gate = summary.get("launchGate", "REVIEW")
    readiness = summary.get("readiness")
    product = summary.get("productName") or "Unknown product"

    pdf = FPDF()
    pdf.add_font(_FONT_NAME, "", str(_FONTS_DIR / "DejaVuSans.ttf"))
    pdf.add_font(_FONT_NAME, "B", str(_FONTS_DIR / "DejaVuSans-Bold.ttf"))
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def line(text: str, *, size: int = 10, bold: bool = False, gray: bool = False, gap: float = 6) -> None:
        """Render one left-margin-anchored, word-wrapped line and advance Y.

        Deliberately avoids cell()'s new_x/new_y auto-advance and any bare
        multi_cell(0, ...) relying on the cursor already being at the left
        margin — both produced wrong X positions after the first iteration
        of a loop in testing (dimension rows rendered stacked at the far
        right margin instead of each starting a fresh line). Always setting
        (x, y) explicitly before writing is slower to write but can't drift.
        """
        pdf.set_xy(pdf.l_margin, pdf.get_y())
        pdf.set_font(_FONT_NAME, "B" if bold else "", size)
        pdf.set_text_color(120, 120, 120) if gray else pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, gap, text)

    line("TryLapse Readiness Scorecard", size=18, bold=True, gap=8)
    line(product, size=11, gray=True, gap=6)
    line(summary.get("targetUrl", ""), size=11, gray=True, gap=6)
    pdf.ln(3)

    line(f"{readiness if readiness is not None else '--'}/100  —  Gate: {_GATE_LABEL.get(gate, gate)}", size=20, bold=True, gap=10)

    verdict = summary.get("verdict", "")
    if verdict:
        line(verdict, size=10, gap=6)
    pdf.ln(3)

    dims = bundle.get("dimensions") or []
    if dims:
        line("Dimension breakdown", size=13, bold=True, gap=8)
        for d in dims:
            name = d.get("name", "")
            score = d.get("score", "")
            signal = d.get("signal", "")
            line(f"{name}: {score}", size=10, bold=True, gap=6)
            if signal:
                line(signal, size=9, gray=True, gap=5)
        pdf.ln(3)

    all_issues = sorted(
        bundle.get("issues", []),
        key=lambda i: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(i.get("severity"), 4),
    )
    issues = all_issues[:_MAX_ISSUES_IN_PDF]
    if issues:
        line(f"Issues ({len(issues)} of {len(all_issues)})" if len(all_issues) > len(issues)
             else f"Issues ({len(issues)})", size=13, bold=True, gap=8)
        for issue in issues:
            line(f"[{issue.get('severity', '?')}] {issue.get('title', '')}", size=10, bold=True, gap=6)
            meta = f"{issue.get('persona', '')} · {issue.get('journey', '')}"
            line(meta, size=9, gray=True, gap=5)
            pdf.ln(2)
        if len(all_issues) > len(issues):
            line(
                f"…and {len(all_issues) - len(issues)} more — see the full CSV/JSON export for the complete list.",
                size=9, gray=True, gap=6,
            )
        pdf.ln(2)

    delights = bundle.get("delights") or []
    if delights:
        line(f"Delights ({len(delights)})", size=13, bold=True, gap=8)
        for d in delights:
            line(f"- {d.get('title', '')}: {d.get('quote', '')}", size=10, gap=6)

    return bytes(pdf.output())
