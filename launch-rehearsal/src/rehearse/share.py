"""Build shareable payloads: LLM-generated message + signed URLs for P0 video evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rehearse.recording import get_video_path
from rehearse.signing import build_signed_file_url


def build_share_payload(
    bundle: dict[str, Any],
    artifacts_root: Path,
    run_id: str,
    *,
    base_url: str = "",
    ttl_seconds: int = 86400,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Build a share payload: LLM-generated message + signed URLs for P0 video evidence.

    Falls back to a template message when the LLM is unavailable or returns
    nothing usable, so the share feature always returns something.
    """
    summary = bundle.get("summary", {})
    issues = bundle.get("issues", [])
    p0_issues = [i for i in issues if i.get("severity") == "P0"]

    videos: list[dict[str, Any]] = []
    seen_journeys: set[str] = set()
    for issue in p0_issues:
        jid = issue.get("journeyId")
        if not jid or jid in seen_journeys:
            continue
        seen_journeys.add(jid)
        video_path = get_video_path(artifacts_root, run_id, jid)
        if video_path is None:
            continue
        try:
            rel_path = str(video_path.relative_to(artifacts_root)).replace("\\", "/")
        except ValueError:
            continue
        url = build_signed_file_url(artifacts_root, rel_path, base_url=base_url, ttl_seconds=ttl_seconds)
        videos.append(
            {
                "findingTitle": issue.get("title"),
                "journeyId": jid,
                "url": url,
                "expiresInSeconds": ttl_seconds,
            }
        )

    p0_titles = [i.get("title", "") for i in p0_issues]
    readiness = summary.get("readiness")
    product_name = summary.get("productName") or ""
    target_url = summary.get("targetUrl") or ""

    message: str | None = None
    if use_llm and p0_titles:
        from rehearse.llm import generate_share_message_llm

        llm_result = generate_share_message_llm(product_name, readiness, p0_titles, target_url=target_url)
        if llm_result and llm_result.get("message") and not llm_result.get("error"):
            message = llm_result["message"]

    if message is None:
        label = product_name or target_url or "this run"
        if p0_titles:
            message = (
                f"Ran a launch rehearsal on {label} — found {len(p0_titles)} P0 issue(s) "
                f"before they hit production (readiness {readiness}/100). Video evidence attached."
            )
        else:
            message = f"Ran a launch rehearsal on {label} — no P0 issues found (readiness {readiness}/100)."

    return {
        "message": message,
        "p0Count": len(p0_titles),
        "videos": videos,
        "readiness": readiness,
    }
