"""Load run artifacts for the monitoring dashboard."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from rehearse.analysis_export import rebuild_bundle_from_artifacts
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
    }


def load_bundle(artifacts_root: Path, run_id: str, *, rebuild: bool = True) -> dict[str, Any] | None:
    path = _analysis_path(artifacts_root, run_id)
    if path.is_file():
        return json.loads(path.read_text())
    if rebuild:
        return rebuild_bundle_from_artifacts(artifacts_root, run_id)
    return None


def backfill_all(artifacts_root: Path) -> list[str]:
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir():
        return []
    rebuilt: list[str] = []
    for path in sorted(runs_dir.glob("*.json")):
        run_id = json.loads(path.read_text())["run_id"]
        if not _analysis_path(artifacts_root, run_id).is_file():
            if rebuild_bundle_from_artifacts(artifacts_root, run_id):
                rebuilt.append(run_id)
    return rebuilt


def summary_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    return bundle["summary"]


def list_run_summaries(artifacts_root: Path) -> list[dict[str, Any]]:
    runs_dir = artifacts_root / "runs"
    if not runs_dir.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        run_id = json.loads(path.read_text())["run_id"]
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


def diff_runs(artifacts_root: Path, run_a: str, run_b: str) -> dict[str, Any]:
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
            changed.append(
                {
                    "step_id": sid,
                    "stepId": sid,
                    "outcome_a": out_a,
                    "outcome_b": out_b,
                    "outcomeA": out_a,
                    "outcomeB": out_b,
                    "url_a": url_a,
                    "url_b": url_b,
                    "urlA": url_a,
                    "urlB": url_b,
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

    return {
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
        "newIssues": new_issues,
        "resolvedIssues": resolved_issues,
    }


def get_trends(artifacts_root: Path) -> dict[str, Any]:
    summaries = list_run_summaries(artifacts_root)
    summaries = list(reversed(summaries))
    readiness = [s["readiness"] for s in summaries]
    pages = [s["pages"] for s in summaries]
    flake_rates: list[float] = []
    for s in summaries:
        bundle = load_bundle(artifacts_root, s["id"], rebuild=False)
        if bundle:
            flaky = sum(1 for step in bundle.get("steps", []) if step.get("flaky"))
            total = len(bundle.get("steps", [])) or 1
            flake_rates.append(round(flaky / total * 100, 1))
        else:
            flake_rates.append(0.0)
    return {
        "readiness": readiness,
        "pages": pages,
        "flakeRate": flake_rates,
        "runIds": [s["id"] for s in summaries],
        "labels": [s["startedAt"][:10] if s.get("startedAt") else s["id"] for s in summaries],
    }


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


def list_configs(artifacts_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cfg_dir = artifacts_root / "configs"
    if cfg_dir.is_dir():
        for p in sorted(cfg_dir.glob("*.yaml"), key=lambda x: x.stat().st_mtime, reverse=True):
            items.append({"id": p.stem, "path": str(p), "name": p.stem, "source": "saved"})
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


def get_alerts(artifacts_root: Path) -> list[dict[str, Any]]:
    ws = get_workspace(artifacts_root)
    return [
        {"id": "al_red", "name": "Red readiness", "kind": "slack", "trigger": "readiness == Red", "enabled": True},
        {"id": "al_p0", "name": "New P0 issue", "kind": "email", "trigger": "issue.severity == P0", "enabled": True},
        {"id": "al_flake", "name": "Flake rate spike", "kind": "webhook", "trigger": "flake_rate > 5%", "enabled": False},
        {"id": "al_ws", "name": f"Workspace {ws.get('slug', 'default')}", "kind": "slack", "trigger": "run.complete", "enabled": True},
    ]


def run_preflight(url: str) -> dict[str, Any]:
    try:
        result = preflight_head(url)
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
