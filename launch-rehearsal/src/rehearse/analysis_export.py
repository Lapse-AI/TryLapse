"""Export structured analysis.json for dashboard API (Frontend_V1 contract)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from rehearse.context import AgentReport, RunContext
from rehearse.dsl import RunConfig, Persona
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import AnalysisResult, Finding
from rehearse.sitemap import SiteMap
from rehearse.workflows import WorkflowGraph

READINESS_SCORE = {"Green": 85, "Amber": 72, "Red": 38}
STATUS_MAP = {"Green": "ready", "Amber": "warn", "Red": "danger"}
EXTRA_DIMENSIONS = ["Performance", "Accessibility", "Trust", "Onboarding", "Recovery"]


def _config_hash(config: RunConfig) -> str:
    blob = f"{config.target_url}|{len(config.journeys)}|{len(config.personas)}"
    return hashlib.sha256(blob.encode()).hexdigest()[:6]


def _readiness_score(band: str, analysis: AnalysisResult) -> int:
    base = READINESS_SCORE.get(band, 50)
    if not analysis.journey_matrix:
        return base
    passes = sum(1 for row in analysis.journey_matrix.values() for s in row.values() if s == "pass")
    total = sum(len(row) for row in analysis.journey_matrix.values()) or 1
    return max(10, min(99, base + int((passes / total - 0.5) * 20)))


def _severity_to_ui(severity: str, finding: Finding, evidence: RunEvidence) -> str:
    if finding.title.lower().startswith("auth") and evidence.auth_outcome and "fail" in evidence.auth_outcome:
        return "P0"
    if "auth wall" in finding.title.lower() or finding.step_id == "auth-setup":
        fails = sum(1 for s in evidence.steps if s.outcome == "fail")
        if fails == 0 and all(s.outcome in ("partial", "fail") for s in evidence.steps[:3] if evidence.steps):
            return "P0"
    return severity if severity in ("P0", "P1", "P2", "P3") else "P2"


def _persona_name(config: RunConfig, persona_id: str) -> str:
    for p in config.personas:
        if p.id == persona_id:
            return p.name
    return persona_id


def _journey_name(config: RunConfig, journey_id: str) -> str:
    for j in config.journeys:
        if j.id == journey_id:
            return j.name
    return journey_id


def _owner_heuristic(title: str, detail: str) -> str:
    blob = f"{title} {detail}".lower()
    if any(k in blob for k in ("auth", "sso", "cookie", "session", "api", "network")):
        return "backend"
    if any(k in blob for k in ("label", "aria", "button", "form", "ui")):
        return "frontend"
    if any(k in blob for k in ("copy", "pricing", "footer", "docs", "search")):
        return "content"
    if any(k in blob for k in ("security", "pii", "compliance")):
        return "security"
    return "frontend"


def _step_flaky(step: StepSnapshot, all_steps: list[StepSnapshot]) -> bool:
    if step.flaky:
        return True
    if step.console_errors:
        return True
    same_journey = [s for s in all_steps if s.journey_id == step.journey_id and s.action == step.action]
    if len(same_journey) > 1:
        outcomes = {s.outcome for s in same_journey}
        if len(outcomes) > 1:
            return True
    durations = [s.duration_ms for s in all_steps if s.duration_ms > 0]
    if durations and step.duration_ms > 0:
        med = sorted(durations)[len(durations) // 2]
        if med > 0 and step.duration_ms > med * 2.5:
            return True
    return False


def _expand_dimensions(raw: dict[str, tuple[int, str]], evidence: RunEvidence) -> list[dict[str, Any]]:
    name_map = {"Information clarity": "Information"}
    items: list[dict[str, Any]] = []
    for name, (score, signal) in raw.items():
        ui_name = name_map.get(name, name)
        items.append({"name": ui_name, "score": score * 20, "signal": signal, "automated": True})
    if not items:
        items = [{"name": "Functionality", "score": 40, "signal": "No steps", "automated": True}]
    base = sum(i["score"] for i in items) / len(items)
    for extra in EXTRA_DIMENSIONS:
        bump = 0
        if extra == "Performance":
            avg = sum(s.duration_ms for s in evidence.steps) / max(len(evidence.steps), 1)
            bump = -10 if avg > 3000 else 5
        elif extra == "Accessibility":
            unlabeled = sum(s.unlabeled_button_count for s in evidence.steps)
            bump = -15 if unlabeled > 5 else 0
        elif extra == "Trust":
            bump = -20 if evidence.auth_outcome and "fail" in evidence.auth_outcome else 5
        items.append(
            {
                "name": extra,
                "score": max(20, min(95, int(base + bump))),
                "signal": f"Phase 2 heuristic from step evidence",
                "automated": False,
            }
        )
    return items


def _serialize_steps(evidence: RunEvidence, artifacts_root: Path, output_dir: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in evidence.steps:
        rel_shots: list[str] = []
        for p in s.artifact_paths:
            path = Path(p)
            try:
                rel = path.relative_to(output_dir)
                rel_shots.append(str(rel).replace("\\", "/"))
            except ValueError:
                if path.name.endswith(".png"):
                    rel_shots.append(f"artifacts/{evidence.run_id}/{path.name}")
        out.append(
            {
                "stepId": s.step_id,
                "journeyId": s.journey_id,
                "journeyName": s.journey_name,
                "personaId": s.persona_id,
                "action": s.action,
                "requestedUrl": s.requested_url,
                "finalUrl": s.final_url,
                "outcome": s.outcome,
                "durationMs": s.duration_ms,
                "note": s.note,
                "flaky": _step_flaky(s, evidence.steps),
                "consoleErrors": s.console_errors,
                "networkFailures": s.network_failures,
                "bodyTextExcerpt": s.body_text_excerpt[:200] if s.body_text_excerpt else None,
                "artifactPaths": rel_shots,
            }
        )
    return out


def _serialize_issues(config: RunConfig, evidence: RunEvidence, analysis: AnalysisResult) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for i, f in enumerate(analysis.issues):
        sev = _severity_to_ui(f.severity, f, evidence)
        pid = f.persona_ids[0] if f.persona_ids else config.personas[0].id
        step = next((s for s in evidence.steps if s.step_id == f.step_id), None)
        jid = step.journey_id if step else "unknown"
        issues.append(
            {
                "id": f.id or f"I{i+1}",
                "runId": evidence.run_id,
                "severity": sev,
                "title": f.title,
                "detail": f.detail,
                "persona": _persona_name(config, pid),
                "personaId": pid,
                "journey": _journey_name(config, jid),
                "journeyId": jid,
                "stepId": f.step_id,
                "dimension": "Functionality",
                "confidence": f.confidence,
                "owner": _owner_heuristic(f.title, f.detail),
                "recurring": 1,
                "evidence": f.detail,
                "severityReason": f"P{sev[-1]} from automated heuristics" if sev.startswith("P") else None,
                "suggestion": None,
                "screenshotPath": f"artifacts/{evidence.run_id}/{f.step_id}.png",
            }
        )
    return issues


def _serialize_delights(config: RunConfig, evidence: RunEvidence, analysis: AnalysisResult) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for d in analysis.delights:
        pid = d.persona_ids[0] if d.persona_ids else config.personas[0].id
        step = next((s for s in evidence.steps if s.step_id == d.step_id), None)
        jid = step.journey_id if step else "unknown"
        out.append(
            {
                "id": d.id,
                "runId": evidence.run_id,
                "title": d.title,
                "quote": d.detail,
                "persona": _persona_name(config, pid),
                "journey": _journey_name(config, jid),
                "stepId": d.step_id,
                "marketingReady": True,
            }
        )
    return out


def _serialize_agents(ctx: RunContext | None, evidence: RunEvidence) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    if not ctx:
        return agents
    phase_map = {
        "crawl": "crawl",
        "workflow": "workflow",
        "journey": "journey",
        "persona": "persona",
        "synthesis": "synthesis",
    }
    for r in ctx.agent_reports:
        phase = "persona"
        if "crawl" in r.agent_id:
            phase = "crawl"
        elif "workflow" in r.agent_id or r.agent_id == "ag_wf":
            phase = "workflow"
        elif "journey" in r.agent_id:
            phase = "journey"
        elif "synth" in r.agent_id:
            phase = "synthesis"
        elif "llm" in r.agent_id:
            phase = "persona"
        agents.append(
            {
                "id": r.agent_id,
                "runId": evidence.run_id,
                "name": r.agent_role.split(":")[-1].strip() if ":" in r.agent_role else r.agent_id,
                "role": r.agent_role,
                "phase": phase_map.get(phase, phase),
                "status": "done",
                "durationSec": int(r.metadata.get("duration_sec", 0)) if r.metadata else 0,
                "costUsd": float(r.metadata.get("cost_usd", 0)) if r.metadata else 0,
                "lastSummary": r.summary[:200],
                "findingsCount": len(r.findings),
                "delightsCount": len(r.delights),
                "handoff": {k: v for k, v in (r.metadata or {}).items() if k not in ("duration_sec", "cost_usd", "error")},
            }
        )
    # Phase 2 placeholder agents
    agents.extend(
        [
            {
                "id": "ag_compl",
                "runId": evidence.run_id,
                "name": "Compliance",
                "role": "PII, auth boundary signals (Phase 2)",
                "phase": "compliance",
                "status": "idle",
                "durationSec": 0,
                "costUsd": 0,
                "lastSummary": "Not enabled for this run.",
            },
            {
                "id": "ag_perf",
                "runId": evidence.run_id,
                "name": "Performance",
                "role": "Latency, Web Vitals (Phase 2)",
                "phase": "performance",
                "status": "idle",
                "durationSec": 0,
                "costUsd": 0,
                "lastSummary": "Not enabled for this run.",
            },
        ]
    )
    return agents


def _serialize_matrix(config: RunConfig, analysis: AnalysisResult) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for jid, row in analysis.journey_matrix.items():
        for pid, grade in row.items():
            cells.append({"personaId": pid, "journeyId": jid, "grade": grade})
    return cells


def _serialize_sitemap(
    sitemap: SiteMap | None, run_id: str, workflows: WorkflowGraph | None
) -> tuple[list[dict[str, Any]], list[dict[str, str]], str]:
    if not sitemap:
        return [], [], "No sitemap — crawl disabled or not run."
    pages: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    path_to_id: dict[str, str] = {}
    for i, p in enumerate(sitemap.pages):
        pid = f"pg_{i+1}"
        path_to_id[p.path] = pid
        ptype = "hub" if p.path in sitemap.hub_paths else "orphan" if p.path in sitemap.orphan_paths else "auth" if p.path in sitemap.auth_gated_paths else "leaf"
        wf = None
        if workflows:
            for w in workflows.workflows:
                if w.path == p.path:
                    wf = w.workflow_type.replace("documentation", "docs").replace("authentication", "auth")
                    break
        pages.append(
            {
                "id": pid,
                "path": p.path,
                "title": p.title or p.path,
                "type": ptype,
                "workflow": wf,
                "errors": 1 if p.path in sitemap.error_paths else 0,
            }
        )
        for out in getattr(p, "outbound_paths", []) or []:
            if out in path_to_id:
                edges.append({"from": pid, "to": path_to_id[out]})
    md = sitemap.render_markdown()
    return pages, edges, md


def _blockers(issues: list[dict[str, Any]]) -> int:
    return sum(1 for i in issues if i["severity"] in ("P0", "P1"))


def build_run_bundle(
    config: RunConfig,
    evidence: RunEvidence,
    analysis: AnalysisResult,
    output_dir: Path,
    *,
    ctx: RunContext | None = None,
    scorecard_md: str | None = None,
    llm_enabled: bool = False,
    crawl_enabled: bool = True,
) -> dict[str, Any]:
    band = analysis.readiness
    status = STATUS_MAP.get(band, "neutral")
    issues = _serialize_issues(config, evidence, analysis)
    delights = _serialize_delights(config, evidence, analysis)
    sitemap_pages, sitemap_edges, sitemap_md = _serialize_sitemap(
        ctx.sitemap if ctx else None, evidence.run_id, ctx.workflows if ctx else None
    )
    steps = _serialize_steps(evidence, output_dir / "artifacts" / evidence.run_id, output_dir)
    screenshots = []
    for s in steps:
        for p in s.get("artifactPaths") or []:
            if p.endswith(".png"):
                screenshots.append({"path": p, "stepId": s["stepId"], "label": s["journeyName"]})

    personas = [
        {"id": p.id, "name": p.name, "role": p.role, "goal": p.goals[0] if p.goals else "", "patience": "medium"}
        for p in config.personas
    ]
    journeys = [
        {"id": j.id, "name": j.name, "steps": len(j.steps), "category": "dashboard"}
        for j in config.journeys
    ]

    return {
        "summary": {
            "id": evidence.run_id,
            "productName": evidence.product_name,
            "target": _host(evidence.target_url),
            "targetUrl": evidence.target_url,
            "env": "staging",
            "workspaceId": "ws_default",
            "startedAt": evidence.started_at,
            "finishedAt": evidence.finished_at,
            "durationSec": evidence.duration_ms // 1000,
            "readiness": _readiness_score(band, analysis),
            "readinessBand": band,
            "status": status,
            "blockers": _blockers(issues),
            "issues": len(issues),
            "delights": len(delights),
            "pages": len(sitemap_pages),
            "stepCount": len(steps),
            "agentCost": 0.0,
            "outcome": evidence.outcome,
            "configHash": _config_hash(config),
            "authAttempted": evidence.auth_attempted,
            "authOutcome": evidence.auth_outcome,
            "llmEnabled": llm_enabled,
            "crawlEnabled": crawl_enabled,
            "orphans": len(ctx.sitemap.orphan_paths) if ctx and ctx.sitemap else 0,
            "authGated": len(ctx.sitemap.auth_gated_paths) if ctx and ctx.sitemap else 0,
        },
        "steps": steps,
        "issues": issues,
        "delights": delights,
        "agents": _serialize_agents(ctx, evidence),
        "matrix": _serialize_matrix(config, analysis),
        "dimensions": _expand_dimensions(analysis.dimensions, evidence),
        "scorecardMd": scorecard_md or "",
        "sitemapMd": sitemap_md,
        "sitemapPages": sitemap_pages,
        "sitemapEdges": sitemap_edges,
        "screenshots": screenshots,
        "annotations": [],
        "personas": personas,
        "journeys": journeys,
        "workflows": _serialize_workflows(ctx),
        "suggestedJourneys": (ctx.workflows.suggested_journeys if ctx and ctx.workflows else []),
    }


def _serialize_workflows(ctx: RunContext | None) -> list[dict[str, Any]]:
    if not ctx or not ctx.workflows:
        return []
    return [
        {
            "category": w.workflow_type.replace("documentation", "docs").replace("authentication", "auth"),
            "path": w.path,
            "title": w.title,
            "confidence": w.confidence,
            "signals": w.signals,
        }
        for w in ctx.workflows.workflows[:30]
    ]


def _host(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc or url


def write_analysis_bundle(
    bundle: dict[str, Any],
    output_dir: Path,
    *,
    config: RunConfig | None = None,
    config_yaml: str | None = None,
) -> Path:
    run_id = bundle["summary"]["id"]
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    path = analysis_dir / f"{run_id}.json"
    path.write_text(json.dumps(bundle, indent=2))
    if config_yaml:
        cfg_dir = output_dir / "configs"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / f"{run_id}.yaml").write_text(config_yaml)
    return path


def _guess_config_path(output_dir: Path, run_id: str, target_url: str) -> Path | None:
    cfg_dir = output_dir / "configs"
    saved = cfg_dir / f"{run_id}.yaml"
    if saved.is_file():
        return saved
    examples = Path(__file__).resolve().parents[2] / "examples"
    prefix = run_id.split("-")[0].lower()
    candidates = {
        "enterprise": examples / "enterprise-authenticated.yaml",
        "cal": examples / "cal-com-phase0.yaml",
        "argyle": examples / "enterprise-authenticated.yaml",
        "phase0": examples / "enterprise-saas.yaml",
    }
    path = candidates.get(prefix)
    if path and path.is_file():
        return path
    for p in examples.glob("*.yaml"):
        return p
    return None


def load_evidence_from_run_json(path: Path) -> RunEvidence:
    import dataclasses

    data = json.loads(path.read_text())
    ev = RunEvidence(
        run_id=data["run_id"],
        target_url=data["target_url"],
        product_name=data.get("product_name", "Unknown"),
        started_at=data["started_at"],
        finished_at=data.get("finished_at"),
        duration_ms=data.get("duration_ms", 0),
        auth_attempted=data.get("auth_attempted", False),
        auth_outcome=data.get("auth_outcome"),
        outcome=data.get("outcome", "complete"),
    )
    fields = {f.name for f in dataclasses.fields(StepSnapshot)}
    steps: list[StepSnapshot] = []
    for s in data.get("steps", []):
        payload = {k: v for k, v in s.items() if k in fields}
        payload.setdefault("journey_name", payload.get("journey_id", "unknown"))
        payload.setdefault("persona_id", "unknown")
        payload.setdefault("action", "navigate")
        payload.setdefault("step_id", s.get("step_id", "unknown"))
        payload.setdefault("journey_id", "unknown")
        steps.append(StepSnapshot(**payload))
    ev.steps = steps
    return ev


def rebuild_bundle_from_artifacts(output_dir: Path, run_id: str) -> dict[str, Any] | None:
    """Rebuild analysis bundle from saved run + scorecard + sitemap (no browser)."""
    from rehearse.context import RunContext
    from rehearse.dsl import load_config
    from rehearse.heuristics import analyze_run
    from rehearse.workflows import detect_workflows

    run_path = output_dir / "runs" / f"{run_id}.json"
    if not run_path.is_file():
        return None

    evidence = load_evidence_from_run_json(run_path)
    config_path = _guess_config_path(output_dir, run_id, evidence.target_url)
    if not config_path:
        return None
    config = load_config(config_path)

    sitemap_path = output_dir / "sitemaps" / f"{run_id}-sitemap.json"
    sitemap = SiteMap.load_json(sitemap_path)
    workflows = detect_workflows(sitemap) if sitemap else None
    ctx = RunContext(config=config, evidence=evidence, sitemap=sitemap, workflows=workflows)

    analysis = analyze_run(config, evidence)
    scorecard_path = output_dir / "scorecards" / f"{run_id}-scorecard.md"
    scorecard_md = scorecard_path.read_text() if scorecard_path.is_file() else None
    crawl_on = sitemap is not None

    bundle = build_run_bundle(
        config,
        evidence,
        analysis,
        output_dir,
        ctx=ctx,
        scorecard_md=scorecard_md,
        llm_enabled=False,
        crawl_enabled=crawl_on,
    )
    ann_path = output_dir / "annotations" / f"{run_id}.json"
    if ann_path.is_file():
        bundle["annotations"] = json.loads(ann_path.read_text())
    write_analysis_bundle(bundle, output_dir)
    return bundle
