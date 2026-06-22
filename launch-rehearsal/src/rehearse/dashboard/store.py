"""Load run artifacts for the monitoring dashboard."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from rehearse.analysis_export import rebuild_bundle_from_artifacts
from rehearse.init_config import build_config, build_self_dashboard_config, write_config
from rehearse.preflight import preflight_head

READINESS_SCORE = {"Green": 85, "Amber": 72, "Red": 38}
STATUS_MAP = {"Green": "ready", "Amber": "warn", "Red": "danger"}


def _parse_readiness(scorecard_text: str | None) -> str | None:
    if not scorecard_text:
        return None
    match = re.search(r"\*\*Readiness\*\*\s*\|\s*\*\*(\w+)\*\*", scorecard_text)
    return match.group(1) if match else None


def _parse_counts(scorecard_text: str | None) -> tuple[int | None, int | None]:
    if not scorecard_text:
        return None, None
    issues = delights = None
    im = re.search(r"\*\*Issues\*\*\s*\|\s*(\d+)", scorecard_text)
    dm = re.search(r"\*\*Delights\*\*\s*\|\s*(\d+)", scorecard_text)
    if im:
        issues = int(im.group(1))
    if dm:
        delights = int(dm.group(1))
    return issues, delights


def _analysis_path(artifacts_root: Path, run_id: str) -> Path:
    return artifacts_root / "analysis" / f"{run_id}.json"


def _workspace_path(artifacts_root: Path) -> Path:
    return artifacts_root / "workspace.json"


def _default_workspace(artifacts_root: Path) -> dict[str, Any]:
    runs = list_runs(artifacts_root)
    target = runs[0]["target_url"] if runs else "https://example.com"
    host = urlparse(target).netloc or target
    return {
        "id": "ws_default",
        "name": host.split(".")[0].title() + " Workspace",
        "slug": host.replace(".", "-"),
        "targetUrl": target,
        "members": 1,
        "products": 1,
        "configVersion": "1.0",
        "configHash": "000000",
        "strictEnterpriseMode": True,
        "retentionDays": 90,
        "piiRedaction": False,
        "env": "staging",
        "slackWebhookUrl": None,
        "webhookUrl": None,
        "guardrails": {"extraBlockedKeywords": []},
    }


def load_bundle(artifacts_root: Path, run_id: str, *, rebuild: bool = True) -> dict[str, Any] | None:
    path = _analysis_path(artifacts_root, run_id)
    if path.is_file():
        return json.loads(path.read_text())
    if rebuild:
        return rebuild_bundle_from_artifacts(artifacts_root, run_id)
    return None


def _is_run_evidence(path: Path) -> str | None:
    """Return run_id if path is a run evidence JSON; None for progress/graph/other files."""
    # Skip non-evidence files by name pattern
    name = path.stem
    if name.endswith("-progress") or name.endswith("-crawl-graph") or name.endswith("-control") or name.endswith("-state"):
        return None
    try:
        data = json.loads(path.read_text())
        return data.get("run_id") or None
    except Exception:
        return None


def backfill_all(artifacts_root: Path) -> list[str]:
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir():
        return []
    rebuilt: list[str] = []
    for path in sorted(runs_dir.glob("*.json")):
        run_id = _is_run_evidence(path)
        if not run_id:
            continue
        if not _analysis_path(artifacts_root, run_id).is_file():
            if rebuild_bundle_from_artifacts(artifacts_root, run_id):
                rebuilt.append(run_id)
    return rebuilt


def summary_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    return bundle["summary"]


def list_run_summaries(artifacts_root: Path, config_prefix: str | None = None) -> list[dict[str, Any]]:
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        run_id = _is_run_evidence(path)
        if not run_id:
            continue
        # Filter by config prefix (e.g. "argyle" matches "argyle-20260608-143022")
        if config_prefix and not run_id.startswith(config_prefix):
            continue
        bundle = load_bundle(artifacts_root, run_id, rebuild=True)
        if bundle:
            items.append(bundle["summary"])
            continue
        data = json.loads(path.read_text())
        scorecard_path = artifacts_root / "scorecards" / f"{run_id}-scorecard.md"
        scorecard_text = scorecard_path.read_text() if scorecard_path.is_file() else None
        band = _parse_readiness(scorecard_text) or "Amber"
        issues, delights = _parse_counts(scorecard_text)
        sitemap_path = artifacts_root / "sitemaps" / f"{run_id}-sitemap.json"
        pages = 0
        if sitemap_path.is_file():
            pages = len(json.loads(sitemap_path.read_text()).get("pages", []))
        items.append(
            {
                "id": run_id,
                "productName": data.get("product_name"),
                "target": urlparse(data.get("target_url", "")).netloc,
                "targetUrl": data.get("target_url"),
                "env": "staging",
                "workspaceId": "ws_default",
                "startedAt": data.get("started_at"),
                "finishedAt": data.get("finished_at"),
                "durationSec": (data.get("duration_ms") or 0) // 1000,
                "readiness": READINESS_SCORE.get(band, 50),
                "readinessBand": band,
                "status": STATUS_MAP.get(band, "neutral"),
                "blockers": issues or 0,
                "issues": issues or 0,
                "delights": delights or 0,
                "pages": pages,
                "stepCount": len(data.get("steps", [])),
                "agentCost": 0.0,
                "outcome": data.get("outcome", "complete"),
                "configHash": "000000",
            }
        )
    return items


def list_runs(artifacts_root: Path) -> list[dict[str, Any]]:
    runs_dir = artifacts_root / "runs"
    scorecards_dir = artifacts_root / "scorecards"
    if not runs_dir.is_dir():
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        data = json.loads(path.read_text())
        run_id = data["run_id"]
        scorecard_path = scorecards_dir / f"{run_id}-scorecard.md"
        scorecard_text = scorecard_path.read_text() if scorecard_path.is_file() else None
        readiness = _parse_readiness(scorecard_text)
        issues, delights = _parse_counts(scorecard_text)
        sitemap_path = artifacts_root / "sitemaps" / f"{run_id}-sitemap.json"
        pages_crawled = None
        if sitemap_path.is_file():
            sm = json.loads(sitemap_path.read_text())
            pages_crawled = len(sm.get("pages", []))

        items.append(
            {
                "run_id": run_id,
                "product_name": data.get("product_name"),
                "target_url": data.get("target_url"),
                "started_at": data.get("started_at"),
                "finished_at": data.get("finished_at"),
                "duration_ms": data.get("duration_ms"),
                "outcome": data.get("outcome"),
                "step_count": len(data.get("steps", [])),
                "readiness": readiness,
                "issues": issues,
                "delights": delights,
                "pages_crawled": pages_crawled,
                "has_scorecard": scorecard_text is not None,
                "has_sitemap": sitemap_path.is_file(),
                "has_analysis": _analysis_path(artifacts_root, run_id).is_file(),
            }
        )
    return items


def get_run_detail(artifacts_root: Path, run_id: str) -> dict[str, Any] | None:
    bundle = load_bundle(artifacts_root, run_id)
    if bundle:
        return {"bundle": bundle, "format": "bundle"}

    run_path = artifacts_root / "runs" / f"{run_id}.json"
    if not run_path.is_file():
        return None

    data = json.loads(run_path.read_text())
    scorecard_path = artifacts_root / "scorecards" / f"{run_id}-scorecard.md"
    sitemap_md_path = artifacts_root / "sitemaps" / f"{run_id}-sitemap.md"
    sitemap_json_path = artifacts_root / "sitemaps" / f"{run_id}-sitemap.json"

    screenshots: list[str] = []
    shot_dir = artifacts_root / "artifacts" / run_id
    if shot_dir.is_dir():
        screenshots = sorted(str(p.relative_to(artifacts_root)) for p in shot_dir.glob("*.png"))

    return {
        "run": data,
        "scorecard_md": scorecard_path.read_text() if scorecard_path.is_file() else None,
        "sitemap_md": sitemap_md_path.read_text() if sitemap_md_path.is_file() else None,
        "sitemap_json": json.loads(sitemap_json_path.read_text()) if sitemap_json_path.is_file() else None,
        "screenshots": screenshots,
        "format": "legacy",
    }


def _step_primary_screenshot(step: dict[str, Any], artifacts_root: Path | None = None) -> str | None:
    # JSON stores snake_case (artifact_paths); camelCase is a legacy key — check both
    paths = step.get("artifact_paths") or step.get("artifactPaths") or []
    for path in paths:
        if path.endswith(".png") and "-error" not in path:
            p = path.replace("\\", "/")
            # Relativize absolute paths so the frontend can build a /files/ URL
            if artifacts_root and Path(p).is_absolute():
                try:
                    p = str(Path(p).relative_to(artifacts_root)).replace("\\", "/")
                except ValueError:
                    pass
            return p
    return None


def _step_focus_region(step: dict[str, Any]) -> dict[str, Any] | None:
    return step.get("focusRegion") or step.get("focus_region")


def _diff_changed_step_entry(sa: dict[str, Any], sb: dict[str, Any], sid: str) -> dict[str, Any]:
    out_a = sa.get("outcome")
    out_b = sb.get("outcome")
    url_a = sa.get("finalUrl") or sa.get("final_url")
    url_b = sb.get("finalUrl") or sb.get("final_url")
    return {
        "step_id": sid,
        "stepId": sid,
        "journeyId": sa.get("journeyId") or sb.get("journeyId"),
        "action": sa.get("action") or sb.get("action"),
        "outcome_a": out_a,
        "outcome_b": out_b,
        "outcomeA": out_a,
        "outcomeB": out_b,
        "url_a": url_a,
        "url_b": url_b,
        "urlA": url_a,
        "urlB": url_b,
        "screenshotPathA": _step_primary_screenshot(sa),
        "screenshotPathB": _step_primary_screenshot(sb),
        "focusRegionA": _step_focus_region(sa),
        "focusRegionB": _step_focus_region(sb),
    }


def diff_runs(artifacts_root: Path, run_a: str, run_b: str, *, refresh: bool = False) -> dict[str, Any]:
    detail_a = get_run_detail(artifacts_root, run_a)
    detail_b = get_run_detail(artifacts_root, run_b)
    if not detail_a or not detail_b:
        missing = [r for r, d in ((run_a, detail_a), (run_b, detail_b)) if not d]
        return {"error": f"Run not found: {', '.join(missing)}"}

    bundle_a = detail_a.get("bundle")
    bundle_b = detail_b.get("bundle")
    run_a_data = bundle_a or detail_a
    run_b_data = bundle_b or detail_b

    steps_a_list = (
        run_a_data.get("steps", [])
        if bundle_a
        else run_a_data["run"].get("steps", [])
    )
    steps_b_list = (
        run_b_data.get("steps", [])
        if bundle_b
        else run_b_data["run"].get("steps", [])
    )
    sid_key = "stepId" if bundle_a else "step_id"
    steps_a = {s[sid_key]: s for s in steps_a_list}
    steps_b = {s[sid_key]: s for s in steps_b_list}
    only_a = sorted(set(steps_a) - set(steps_b))
    only_b = sorted(set(steps_b) - set(steps_a))
    changed: list[dict[str, Any]] = []
    for sid in sorted(set(steps_a) & set(steps_b)):
        sa, sb = steps_a[sid], steps_b[sid]
        out_a = sa.get("outcome")
        out_b = sb.get("outcome")
        url_a = sa.get("finalUrl") or sa.get("final_url")
        url_b = sb.get("finalUrl") or sb.get("final_url")
        if out_a != out_b or url_a != url_b:
            changed.append(_diff_changed_step_entry(sa, sb, sid))

    visual_diffs: list[dict[str, Any]] = list(changed)
    for sid in only_b:
        sb = steps_b[sid]
        visual_diffs.append(
            {
                "step_id": sid,
                "stepId": sid,
                "journeyId": sb.get("journeyId"),
                "action": sb.get("action"),
                "outcomeA": None,
                "outcomeB": sb.get("outcome"),
                "screenshotPathA": None,
                "screenshotPathB": _step_primary_screenshot(sb),
                "focusRegionA": None,
                "focusRegionB": _step_focus_region(sb),
                "onlyInB": True,
            }
        )

    pages_a = set()
    pages_b = set()
    if bundle_a:
        pages_a = {p["path"] for p in bundle_a.get("sitemapPages", [])}
        pages_b = {p["path"] for p in bundle_b.get("sitemapPages", [])} if bundle_b else set()
    else:
        if detail_a.get("sitemap_json"):
            pages_a = {p["path"] for p in detail_a["sitemap_json"].get("pages", [])}
        if detail_b.get("sitemap_json"):
            pages_b = {p["path"] for p in detail_b["sitemap_json"].get("pages", [])}

    readiness_a = (
        bundle_a["summary"]["readinessBand"]
        if bundle_a
        else _parse_readiness(detail_a.get("scorecard_md"))
    )
    readiness_b = (
        bundle_b["summary"]["readinessBand"]
        if bundle_b
        else _parse_readiness(detail_b.get("scorecard_md"))
    )
    issues_a = bundle_a["summary"]["issues"] if bundle_a else _parse_counts(detail_a.get("scorecard_md"))[0]
    issues_b = bundle_b["summary"]["issues"] if bundle_b else _parse_counts(detail_b.get("scorecard_md"))[0]

    new_issues: list[str] = []
    resolved_issues: list[str] = []
    if bundle_a and bundle_b:
        titles_a = {i["title"] for i in bundle_a.get("issues", [])}
        titles_b = {i["title"] for i in bundle_b.get("issues", [])}
        new_issues = sorted(titles_b - titles_a)
        resolved_issues = sorted(titles_a - titles_b)

    from rehearse.llm import llm_enabled
    from rehearse.narrative import build_compare_narrative

    result: dict[str, Any] = {
        "run_a": run_a,
        "run_b": run_b,
        "runA": run_a,
        "runB": run_b,
        "readiness_a": readiness_a,
        "readiness_b": readiness_b,
        "readinessA": readiness_a,
        "readinessB": readiness_b,
        "issues_a": issues_a,
        "issues_b": issues_b,
        "issuesA": issues_a,
        "issuesB": issues_b,
        "pages_a": len(pages_a),
        "pages_b": len(pages_b),
        "pagesA": len(pages_a),
        "pagesB": len(pages_b),
        "new_pages": sorted(pages_b - pages_a),
        "removed_pages": sorted(pages_a - pages_b),
        "newPages": sorted(pages_b - pages_a),
        "removedPages": sorted(pages_a - pages_b),
        "steps_only_in_a": only_a,
        "steps_only_in_b": only_b,
        "stepsOnlyInA": only_a,
        "stepsOnlyInB": only_b,
        "changed_steps": changed,
        "changedSteps": changed,
        "visualDiffs": visual_diffs,
        "newIssues": new_issues,
        "resolvedIssues": resolved_issues,
    }
    from rehearse.dashboard.narrative_cache import (
        diff_fingerprint,
        load_cached,
        save_cached,
    )

    fp = diff_fingerprint(run_a, run_b)
    cache_name = f"diff-{run_a}--{run_b}"
    cached_narr = None if refresh else load_cached(artifacts_root, cache_name, fp)
    if cached_narr:
        result["narrative"] = cached_narr
    else:
        result["narrative"] = build_compare_narrative(
            result,
            bundle_a=bundle_a if isinstance(bundle_a, dict) else None,
            bundle_b=bundle_b if isinstance(bundle_b, dict) else None,
            use_llm=llm_enabled(),
        )
        if result["narrative"].get("source") == "llm+template":
            save_cached(artifacts_root, cache_name, fp, result["narrative"])
    return result


def _build_issue_recurrence(artifacts_root: Path, summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate issue titles across runs (newest-first summaries)."""
    if not summaries:
        return []
    chron = list(reversed(summaries))
    title_runs: dict[str, list[str]] = {}
    title_first: dict[str, str] = {}
    title_last: dict[str, str] = {}

    for s in chron:
        bundle = load_bundle(artifacts_root, s["id"], rebuild=False)
        if not bundle:
            continue
        seen_titles: set[str] = set()
        for issue in bundle.get("issues", []):
            title = (issue.get("title") or "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            title_runs.setdefault(title, []).append(s["id"])
            if title not in title_first:
                started = s.get("startedAt") or s["id"]
                title_first[title] = started[:10] if isinstance(started, str) else str(started)
            title_last[title] = s["id"]

    latest_id = summaries[0]["id"]
    items: list[dict[str, Any]] = []
    for title, run_ids in sorted(title_runs.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(run_ids)
        if count >= 2 and title_last.get(title) == latest_id:
            status = "regression" if run_ids[-2] != latest_id else "open"
        elif count == 1 and run_ids[0] == latest_id:
            status = "new"
        else:
            status = "open"
        items.append(
            {
                "name": title,
                "runs": count,
                "status": status,
                "first": title_first.get(title, ""),
                "runIds": run_ids,
            }
        )
    return items[:15]


def get_trends(artifacts_root: Path, *, refresh: bool = False, config_prefix: str | None = None) -> dict[str, Any]:
    summaries = list_run_summaries(artifacts_root, config_prefix=config_prefix)
    summaries = list(reversed(summaries))
    readiness = [s["readiness"] for s in summaries]
    pages = [s["pages"] for s in summaries]
    flake_rates: list[float] = []
    blocker_counts: list[int] = []
    for s in summaries:
        bundle = load_bundle(artifacts_root, s["id"], rebuild=False)
        if bundle:
            flaky = sum(1 for step in bundle.get("steps", []) if step.get("flaky"))
            total = len(bundle.get("steps", [])) or 1
            flake_rates.append(round(flaky / total * 100, 1))
            blockers = sum(
                1
                for issue in bundle.get("issues", [])
                if issue.get("severity") in ("P0", "P1")
            )
            blocker_counts.append(blockers)
        else:
            flake_rates.append(0.0)
            blocker_counts.append(int(s.get("blockers") or s.get("issues") or 0))

    recurrence = _build_issue_recurrence(artifacts_root, list_run_summaries(artifacts_root, config_prefix=config_prefix))
    issues_opened = sum(1 for r in recurrence if r["status"] == "new")
    issues_resolved = 0
    if len(summaries) >= 2:
        latest = load_bundle(artifacts_root, summaries[-1]["id"], rebuild=False)
        prior = load_bundle(artifacts_root, summaries[-2]["id"], rebuild=False)
        if latest and prior:
            prior_titles = {i["title"] for i in prior.get("issues", [])}
            latest_titles = {i["title"] for i in latest.get("issues", [])}
            issues_resolved = len(prior_titles - latest_titles)

    payload = {
        "readiness": readiness,
        "pages": pages,
        "flakeRate": flake_rates,
        "runIds": [s["id"] for s in summaries],
        "labels": [str(s["startedAt"])[:10] if s.get("startedAt") else s["id"] for s in summaries],
        "issueRecurrence": recurrence,
        "issuesOpened": issues_opened,
        "issuesResolved": issues_resolved,
        "blockerCounts": blocker_counts,
    }
    from rehearse.dashboard.narrative_cache import (
        load_cached,
        save_cached,
        trends_fingerprint,
    )
    from rehearse.llm import llm_enabled
    from rehearse.narrative import build_trends_narrative

    all_summaries = list_run_summaries(artifacts_root)
    fp = trends_fingerprint(all_summaries)
    cached_narr = None if refresh else load_cached(artifacts_root, "trends", fp)
    if cached_narr:
        payload["narrative"] = cached_narr
    else:
        payload["narrative"] = build_trends_narrative(payload, use_llm=llm_enabled())
        if payload["narrative"].get("source") == "llm+template":
            save_cached(artifacts_root, "trends", fp, payload["narrative"])
    return payload


def get_command_digest(artifacts_root: Path, *, limit: int = 7, refresh: bool = False) -> dict[str, Any]:
    from rehearse.dashboard.narrative_cache import (
        digest_fingerprint,
        load_cached,
        save_cached,
    )
    from rehearse.llm import llm_enabled
    from rehearse.narrative import build_command_digest

    summaries = list_run_summaries(artifacts_root)[:limit]
    fp = digest_fingerprint(summaries, limit=limit)
    if not refresh:
        cached = load_cached(artifacts_root, "command-digest", fp)
        if cached:
            return cached
    digest = build_command_digest(artifacts_root, limit=limit, use_llm=llm_enabled())
    if digest.get("source") == "llm+template":
        save_cached(artifacts_root, "command-digest", fp, digest)
    return digest


def search_artifacts(artifacts_root: Path, query: str) -> dict[str, Any]:
    q = query.strip().lower()
    if not q:
        return {"runs": [], "issues": [], "pages": []}
    runs: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    for summary in list_run_summaries(artifacts_root):
        if q in summary["id"].lower() or q in (summary.get("productName") or "").lower():
            runs.append(summary)
        bundle = load_bundle(artifacts_root, summary["id"], rebuild=False)
        if not bundle:
            continue
        for issue in bundle.get("issues", []):
            blob = f"{issue.get('title', '')} {issue.get('detail', '')}".lower()
            if q in blob or q in issue.get("stepId", "").lower():
                issues.append({**issue, "runId": summary["id"]})
        for page in bundle.get("sitemapPages", []):
            if q in page.get("path", "").lower() or q in page.get("title", "").lower():
                pages.append({**page, "runId": summary["id"]})
    return {"runs": runs[:20], "issues": issues[:30], "pages": pages[:30], "query": query}


def get_workspace(artifacts_root: Path) -> dict[str, Any]:
    path = _workspace_path(artifacts_root)
    if path.is_file():
        return json.loads(path.read_text())
    ws = _default_workspace(artifacts_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ws, indent=2))
    return ws


def save_workspace(artifacts_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    path = _workspace_path(artifacts_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return data


def get_annotations(artifacts_root: Path, run_id: str) -> list[dict[str, Any]]:
    path = artifacts_root / "annotations" / f"{run_id}.json"
    if path.is_file():
        return json.loads(path.read_text())
    bundle = load_bundle(artifacts_root, run_id, rebuild=False)
    return bundle.get("annotations", []) if bundle else []


def save_annotation(artifacts_root: Path, run_id: str, annotation: dict[str, Any]) -> list[dict[str, Any]]:
    ann_dir = artifacts_root / "annotations"
    ann_dir.mkdir(parents=True, exist_ok=True)
    path = ann_dir / f"{run_id}.json"
    existing = get_annotations(artifacts_root, run_id)
    existing.append(annotation)
    path.write_text(json.dumps(existing, indent=2))
    analysis_path = _analysis_path(artifacts_root, run_id)
    if analysis_path.is_file():
        bundle = json.loads(analysis_path.read_text())
        bundle["annotations"] = existing
        analysis_path.write_text(json.dumps(bundle, indent=2))
    return existing


def save_config(artifacts_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    target_url = (body.get("targetUrl") or "").strip()
    if not target_url:
        raise ValueError("targetUrl required")

    self_test = bool(body.get("selfTest"))
    allow_localhost = bool(body.get("allowLocalhost")) or self_test
    from rehearse.viewports import normalize_viewports

    exclude_raw = body.get("excludePathPrefixes")
    exclude_prefixes: list[str] | None = None
    if exclude_raw is not None:
        if isinstance(exclude_raw, str):
            exclude_prefixes = [p.strip() for p in exclude_raw.split(",") if p.strip()]
        elif isinstance(exclude_raw, list):
            exclude_prefixes = [str(p).strip() for p in exclude_raw if str(p).strip()]

    viewport_raw = body.get("viewports")
    viewport_list: list[str] | None = None
    if viewport_raw is not None:
        if isinstance(viewport_raw, str):
            viewport_list = normalize_viewports(
                [v.strip() for v in viewport_raw.split(",") if v.strip()]
            )
        elif isinstance(viewport_raw, list):
            viewport_list = normalize_viewports([str(v) for v in viewport_raw])

    if self_test:
        config = build_self_dashboard_config(
            target_url,
            product_name=body.get("productName") or "Launch Rehearsal Dashboard",
        )
    else:
        config = build_config(
            target_url,
            product_name=body.get("productName"),
            with_auth=bool(body.get("withAuth")),
            exclude_path_prefixes=exclude_prefixes,
            viewports=viewport_list,
        )
        if allow_localhost:
            config["run"]["allow_localhost"] = True
    if exclude_prefixes is not None:
        config.setdefault("crawl", {})["exclude_path_prefixes"] = exclude_prefixes
    if viewport_list is not None:
        config["run"]["viewports"] = viewport_list
    if bool(body.get("executeAllPersonasInBrowser")):
        config["run"]["execute_all_personas_in_browser"] = True
    if "personaLens" in body:
        config["run"]["persona_lens"] = bool(body.get("personaLens"))

    # Core persona enable toggles from Init persona studio
    enabled_map = body.get("personaEnabled") or {}
    if isinstance(enabled_map, dict) and config.get("personas"):
        for p in config["personas"]:
            pid = p.get("id")
            if pid in enabled_map:
                p["enabled"] = bool(enabled_map[pid])

    extra = body.get("extraPersonas") or []
    if isinstance(extra, list) and extra:
        from rehearse.dashboard.persona_draft import persona_to_yaml_entry

        existing_ids = {p.get("id") for p in config.get("personas") or []}
        for raw in extra:
            if not isinstance(raw, dict):
                continue
            entry = persona_to_yaml_entry(raw)
            if entry["id"] in existing_ids:
                config["personas"] = [
                    entry if p.get("id") == entry["id"] else p for p in config["personas"]
                ]
            else:
                config.setdefault("personas", []).append(entry)
                existing_ids.add(entry["id"])

    # Copy personas, journeys, and budget settings from the existing config if provided
    existing_config_id = str(body.get("existingConfigId") or "").strip()
    if existing_config_id:
        try:
            import yaml as _yaml2
            from rehearse.dashboard.config_yaml import get_config_yaml as _get_cfg
            _meta = _get_cfg(artifacts_root, existing_config_id)
            _existing = _yaml2.safe_load(_meta["yaml"]) or {}

            # Merge budget settings — take the LARGER value for time/step limits so we
            # never accidentally propagate a too-small value from an old config.
            # Other fields (parallel_journeys, step_timeout_ms) are copied as-is.
            _FLOORS = {"max_run_seconds": 28800, "max_steps_per_journey": 20}
            existing_budgets = _existing.get("budgets") or {}
            if existing_budgets:
                current_budgets = config.setdefault("budgets", {})
                for k, v in existing_budgets.items():
                    floor = _FLOORS.get(k)
                    if floor is not None:
                        current_budgets[k] = max(int(v), floor)
                    else:
                        current_budgets[k] = v

            # Merge personas from existing config (preserves imported ones not in build_config defaults)
            existing_personas = _existing.get("personas") or []
            if existing_personas:
                from rehearse.dashboard.persona_draft import persona_to_yaml_entry
                current_p_ids = {p.get("id") for p in config.get("personas") or []}
                for p in existing_personas:
                    if p.get("id") not in current_p_ids:
                        config.setdefault("personas", []).append(persona_to_yaml_entry(p))
                        current_p_ids.add(p.get("id"))

            # Merge journeys
            existing_journeys = _existing.get("journeys") or []
            if existing_journeys:
                current_j_ids = {j.get("id") for j in config.get("journeys") or []}
                for j in existing_journeys:
                    if j.get("id") not in current_j_ids:
                        config.setdefault("journeys", []).append(j)
                        current_j_ids.add(j.get("id"))

            # If existing config has persona-specific journeys, strip the generic
            # build_config placeholders (j1-land, j2-core, etc.) — they're redundant
            _DEFAULT_J_IDS = {"j1-land", "j2-core", "j3-depth", "j4-search", "j5-admin"}
            all_journeys = config.get("journeys") or []
            has_persona_specific = any(j.get("persona_ids") for j in all_journeys)
            if has_persona_specific:
                config["journeys"] = [
                    j for j in all_journeys
                    if j.get("id") not in _DEFAULT_J_IDS or j.get("persona_ids")
                ]

            # build_config() always creates p1-evaluator/p2-operator/p3-admin enabled by
            # default. Once the user has imported their own discovered personas (signaled
            # by persona-specific journeys existing), those generic templates are dead
            # weight that silently runs alongside whatever the user actually selected —
            # disable them unless the request explicitly re-enables one via personaEnabled.
            _GENERIC_PERSONA_IDS = {"p1-evaluator", "p2-operator", "p3-admin"}
            if has_persona_specific:
                explicit_enabled = body.get("personaEnabled") or {}
                for p in config.get("personas") or []:
                    if p.get("id") in _GENERIC_PERSONA_IDS and p.get("id") not in explicit_enabled:
                        p["enabled"] = False
        except Exception:
            pass

    slug = config["run"]["run_id_prefix"]
    # Scope configs to owner when authenticated; flat dir in local dev
    owner_id = str(body.get("_owner_id") or "").strip()
    cfg_dir = artifacts_root / "configs" / owner_id if owner_id else artifacts_root / "configs"
    # Use local timestamp from frontend (user's timezone) if provided, else UTC
    local_ts = str(body.get("localTimestamp") or "").strip()
    import re as _re
    if local_ts and _re.fullmatch(r"\d{8}-\d{6}", local_ts):
        ts = local_ts
    else:
        # Fall back to local system time (not UTC) so filenames match user's clock
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{slug}-{ts}.yaml"
    path = cfg_dir / filename
    write_config(path, config)

    # Always update workspace with the latest saved config path
    ws = get_workspace(artifacts_root)
    ws["targetUrl"] = target_url
    ws["config_path"] = str(path.resolve())
    if "piiRedaction" in body:
        ws["piiRedaction"] = bool(body["piiRedaction"])
    save_workspace(artifacts_root, ws)

    return {
        "id": path.stem,
        "path": str(path.resolve()),
        "name": config["run"]["product_name"],
    }


def list_configs(artifacts_root: Path, owner_id: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cfg_dir = artifacts_root / "configs"

    if cfg_dir.is_dir():
        # User-scoped directory (new layout)
        if owner_id:
            user_dir = cfg_dir / owner_id
            if user_dir.is_dir():
                for p in sorted(user_dir.glob("*.yaml"), key=lambda x: x.stat().st_mtime, reverse=True):
                    items.append({"id": p.stem, "path": str(p), "name": p.stem, "source": "saved", "mtime": p.stat().st_mtime})

        # Collect workspace-linked config IDs (works for both owner and anonymous local dev)
        linked_paths: dict[str, str] = {}  # stem → absolute path
        if owner_id:
            from rehearse.dashboard.workspace_store import get_workspaces_for_user
            try:
                workspaces = get_workspaces_for_user(artifacts_root, owner_id)
                for ws in workspaces:
                    cp = ws.get("configPath") or ws.get("config_path") or ""
                    if cp:
                        linked_paths[Path(cp).stem] = cp
            except Exception:
                pass
        else:
            # Local dev: pick up config_path from workspace.json
            try:
                import json as _json
                ws_file = artifacts_root / "workspace.json"
                if ws_file.is_file():
                    ws_data = _json.loads(ws_file.read_text())
                    cp = ws_data.get("configPath") or ws_data.get("config_path") or ""
                    if cp:
                        linked_paths[Path(cp).stem] = cp
            except Exception:
                pass

        # Include workspace-linked configs from subdirectories (e.g. local/)
        seen = {i["id"] for i in items}
        for stem, path_str in linked_paths.items():
            if stem not in seen:
                p = Path(path_str)
                if p.is_file():
                    items.append({"id": p.stem, "path": str(p), "name": p.stem, "source": "saved", "mtime": p.stat().st_mtime})
                    seen.add(stem)

        # Legacy flat configs
        for p in sorted(cfg_dir.glob("*.yaml"), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.stem not in {i["id"] for i in items}:
                if not owner_id or p.stem in linked_paths:
                    items.append({"id": p.stem, "path": str(p), "name": p.stem, "source": "saved", "mtime": p.stat().st_mtime})

    examples = Path(__file__).resolve().parents[2] / "examples"
    if examples.is_dir():
        for p in sorted(examples.glob("*.yaml")):
            items.append({"id": p.stem, "path": str(p), "name": p.stem, "source": "example"})
    return items


def get_journey_library(artifacts_root: Path) -> dict[str, Any]:
    summaries = list_run_summaries(artifacts_root)
    templates: list[dict[str, Any]] = []
    examples = Path(__file__).resolve().parents[2] / "examples"
    for p in examples.glob("*.yaml"):
        templates.append(
            {
                "id": f"tpl_{p.stem}",
                "title": p.stem.replace("-", " ").title(),
                "category": "dashboard",
                "reason": f"Example config: {p.name}",
                "configPath": str(p),
            }
        )
    suggested: list[dict[str, Any]] = []
    if summaries:
        bundle = load_bundle(artifacts_root, summaries[0]["id"], rebuild=False)
        if bundle:
            for j in bundle.get("suggestedJourneys", []):
                suggested.append(j)
            for j in bundle.get("journeys", []):
                templates.append(
                    {
                        "id": f"run_{j['id']}",
                        "title": j["name"],
                        "category": j.get("category", "dashboard"),
                        "reason": f"From run {summaries[0]['id']}",
                        "steps": j.get("steps", 0),
                    }
                )
    return {"templates": templates, "suggested": suggested, "parallelSeeds": True, "flakyConfig": True}


def get_init_wizard(artifacts_root: Path) -> dict[str, Any]:
    configs = list_configs(artifacts_root)
    ws = get_workspace(artifacts_root)
    return {
        "steps": [
            {"id": "target", "title": "Target URL", "description": "Production or staging surface to observe"},
            {"id": "auth", "title": "Auth (optional)", "description": "Credentials for auth-gated journeys"},
            {"id": "personas", "title": "Personas", "description": "Who evaluates the product"},
            {"id": "journeys", "title": "Journeys", "description": "Paths to rehearse (parallel seeds supported)"},
            {"id": "crawl", "title": "Crawl", "description": "Sitemap, orphans, workflow detection"},
            {"id": "viewport", "title": "Viewports", "description": "Desktop, tablet, mobile profiles"},
            {"id": "review", "title": "Review & run", "description": "Preflight then rehearse"},
        ],
        "defaults": {
            "targetUrl": ws.get("targetUrl"),
            "env": ws.get("env", "staging"),
            "crawlEnabled": True,
            "llmEnabled": False,
            "repeatMicroLoop": 3,
            "viewports": ["desktop", "tablet", "mobile"],
            "piiRedaction": ws.get("piiRedaction", False),
        },
        "configs": configs,
        "cliHint": "rehearse init -c config.yaml && rehearse run -c config.yaml",
        "writeHint": "POST /api/configs with { targetUrl, productName?, withAuth?, piiRedaction?, allowLocalhost?, selfTest? }",
        "dogfood": {
            "targetUrl": "http://127.0.0.1:8081",
            "configId": "lr-self",
            "hint": "Paste this dashboard URL to rehearse Launch Rehearsal with Launch Rehearsal (sets allow_localhost).",
        },
    }


def get_integrations() -> list[dict[str, Any]]:
    return [
        {"id": "github", "name": "GitHub Actions", "desc": "Run on PR / deploy", "status": "available", "category": "ci"},
        {"id": "slack", "name": "Slack", "desc": "Alert on Red readiness", "status": "available", "category": "alert"},
        {"id": "datadog", "name": "Datadog", "desc": "Correlate traces with run_id", "status": "phase 2", "category": "observability"},
        {"id": "sentry", "name": "Sentry", "desc": "Link issues to rehearsal findings", "status": "phase 2", "category": "observability"},
        {"id": "linear", "name": "Linear", "desc": "Export fix-before-launch backlog", "status": "available", "category": "export"},
        {"id": "sso", "name": "Dashboard SSO", "desc": "OIDC for team access", "status": "phase 2", "category": "auth"},
    ]


_ALERT_DEFAULTS: list[dict[str, Any]] = [
    {"id": "al_red", "name": "Red readiness", "kind": "slack", "trigger": "readiness == Red", "enabled": True},
    {"id": "al_p0", "name": "New P0 issue", "kind": "email", "trigger": "issue.severity == P0", "enabled": True},
    {"id": "al_flake", "name": "Flake rate spike", "kind": "webhook", "trigger": "flake_rate > 5%", "enabled": False},
    {"id": "al_ws", "name": "Run complete", "kind": "slack", "trigger": "run.complete", "enabled": True},
]


def get_alerts(artifacts_root: Path) -> list[dict[str, Any]]:
    """Alert definitions merged with persisted enabled/disabled state from workspace.json.

    The id/kind/trigger/name are fixed; only `enabled` is user-editable today.
    """
    ws = get_workspace(artifacts_root)
    overrides: dict[str, bool] = ws.get("alerts") or {}
    alerts = []
    for a in _ALERT_DEFAULTS:
        entry = dict(a)
        if a["id"] in overrides:
            entry["enabled"] = bool(overrides[a["id"]])
        if a["id"] == "al_ws":
            entry["name"] = f"Workspace {ws.get('slug', 'default')}"
        alerts.append(entry)
    return alerts


def update_alert(artifacts_root: Path, alert_id: str, enabled: bool) -> list[dict[str, Any]]:
    """Toggle an alert's enabled state, persisted on the workspace record."""
    if alert_id not in {a["id"] for a in _ALERT_DEFAULTS}:
        raise ValueError(f"Unknown alert id: {alert_id}")
    ws = get_workspace(artifacts_root)
    alerts_state: dict[str, bool] = dict(ws.get("alerts") or {})
    alerts_state[alert_id] = enabled
    ws["alerts"] = alerts_state
    save_workspace(artifacts_root, ws)
    return get_alerts(artifacts_root)


def run_preflight(url: str, *, allow_localhost: bool = False) -> dict[str, Any]:
    try:
        result = preflight_head(url, allow_localhost=allow_localhost)
        return {"ok": True, **result}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}


def get_backlog(artifacts_root: Path) -> list[dict[str, Any]]:
    summaries = list_run_summaries(artifacts_root)
    if not summaries:
        return []
    bundle = load_bundle(artifacts_root, summaries[0]["id"], rebuild=False)
    if not bundle:
        return []
    items: list[dict[str, Any]] = []
    for issue in bundle.get("issues", []):
        if issue.get("severity") in ("P0", "P1"):
            items.append(
                {
                    "id": issue["id"],
                    "title": issue["title"],
                    "severity": issue["severity"],
                    "owner": issue.get("owner", "frontend"),
                    "fixBeforeLaunch": issue.get("severity") == "P0",
                    "exportTargets": ["linear", "github"],
                }
            )
    return items
