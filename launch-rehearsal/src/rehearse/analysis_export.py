"""Export structured analysis.json for dashboard API (Frontend_V1 contract)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from rehearse.context import AgentReport, RunContext
from rehearse.dsl import ExperimentSpec, RunConfig, Persona
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import AnalysisResult, Finding
from rehearse.sitemap import SiteMap
from rehearse.workflows import WorkflowGraph

READINESS_SCORE = {"Green": 85, "Amber": 72, "Red": 38}
STATUS_MAP = {"Green": "ready", "Amber": "warn", "Red": "danger"}
EXTRA_DIMENSIONS = ["Performance", "Accessibility", "Trust", "Onboarding", "Recovery"]


def _screenshot_path(artifacts_root: Path | None, run_id: str, step_id: str) -> str:
    """Return the relative artifact path for a step screenshot.

    Prefers the plain .png; falls back to -error.png when a step timed out or
    failed (the runner saves those with an -error suffix). Returns the plain
    path when artifacts_root is unknown (frontend will get a 404 rather than
    a wrong filename).
    """
    rel_plain = f"artifacts/{run_id}/{step_id}.png"
    rel_error = f"artifacts/{run_id}/{step_id}-error.png"
    if artifacts_root is not None:
        plain = artifacts_root / "artifacts" / run_id / f"{step_id}.png"
        error = artifacts_root / "artifacts" / run_id / f"{step_id}-error.png"
        if not plain.is_file() and error.is_file():
            return rel_error
    return rel_plain
# Heuristic run cost when LLM token usage is unavailable (USD)
_HEURISTIC_BASE_USD = 0.05
_HEURISTIC_PER_AGENT_USD = 0.02
_HEURISTIC_PER_MINUTE_USD = 0.08
_HEURISTIC_LLM_PERSONA_USD = 0.12


def _agents_run_count(ctx: RunContext | None) -> int:
    if not ctx:
        return 0
    return len(ctx.agent_reports)


def _compute_cost_estimate(
    ctx: RunContext | None,
    evidence: RunEvidence,
    *,
    llm_enabled: bool,
    persona_count: int,
) -> dict[str, Any]:
    """Derive run cost from agent token metadata when present, else duration/heuristic."""
    agent_cost = 0.0
    input_tokens = 0
    output_tokens = 0
    source = "heuristic"

    if ctx:
        for report in ctx.agent_reports:
            meta = report.metadata or {}
            agent_cost += float(meta.get("cost_usd") or 0)
            input_tokens += int(meta.get("input_tokens") or 0)
            output_tokens += int(meta.get("output_tokens") or 0)

    total_tokens = input_tokens + output_tokens
    if total_tokens > 0:
        source = "llm_tokens"
    elif agent_cost > 0:
        source = "agent_metadata"

    if source == "heuristic":
        duration_min = max(evidence.duration_ms, 0) / 60_000
        agents = _agents_run_count(ctx)
        agent_cost = (
            _HEURISTIC_BASE_USD
            + agents * _HEURISTIC_PER_AGENT_USD
            + duration_min * _HEURISTIC_PER_MINUTE_USD
            + (persona_count * _HEURISTIC_LLM_PERSONA_USD if llm_enabled else 0)
        )

    return {
        "usd": round(agent_cost, 4),
        "source": source,
        "inputTokens": input_tokens or None,
        "outputTokens": output_tokens or None,
        "totalTokens": total_tokens or None,
        "durationSec": evidence.duration_ms // 1000,
        "agentsRun": _agents_run_count(ctx),
    }


def _named_error_issues(
    config: RunConfig, evidence: RunEvidence, existing_step_ids: set[str],
    artifacts_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Surface failed steps with named error types as bundle issues."""
    issues: list[dict[str, Any]] = []
    idx = len(existing_step_ids) + 1
    for step in evidence.steps:
        if step.outcome != "fail" or not step.error_type or step.step_id in existing_step_ids:
            continue
        issues.append(
            {
                "id": f"E{idx}",
                "runId": evidence.run_id,
                "severity": "P1" if step.error_type in ("BrowserStepTimeout", "RunBudgetExceeded") else "P2",
                "title": f"{step.error_type}: {step.journey_name}",
                "detail": step.note or f"Step failed with {step.error_type}",
                "persona": _persona_name(config, step.persona_id),
                "personaId": step.persona_id,
                "journey": step.journey_name,
                "journeyId": step.journey_id,
                "stepId": step.step_id,
                "dimension": _dimension_for_finding(step.error_type, step.note or ""),
                "confidence": "high",
                "owner": _owner_heuristic(step.error_type, step.note or ""),
                "recurring": 1,
                "evidence": step.note or step.error_type,
                "errorType": step.error_type,
                "severityReason": f"Named error {step.error_type}",
                "suggestion": None,
                "screenshotPath": _screenshot_path(artifacts_root, evidence.run_id, step.step_id),
            }
        )
        existing_step_ids.add(step.step_id)
        idx += 1
    return issues


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


def _dimension_for_finding(title: str, detail: str) -> str:
    """Map heuristic finding text to dashboard dimension rollup names."""
    blob = f"{title} {detail}".lower()
    if any(k in blob for k in ("form input", "inputs lack label", "missing label", "aria-label")):
        return "Accessibility"
    if any(k in blob for k in ("unlabeled", "icon-only", "duplicate primary cta", "duplicate cta")):
        return "UI/UX"
    if any(k in blob for k in ("slow step", "perceived delay", "avg step", "vitals", "lcp")):
        return "Performance"
    if any(k in blob for k in ("sparse page", "sparse content", "deep navigation", "depth reaches")):
        return "Information"
    if any(k in blob for k in ("auth wall", "auth attempted", "auth fail")):
        return "Trust"
    if any(
        k in blob
        for k in (
            "http ",
            "loading state",
            "console",
            "crawl found error",
            "browserstep",
            "preflight",
            "runbudget",
            "step failed",
            "timeout",
        )
    ):
        return "Functionality"
    return "Functionality"


def _related_dimensions_for_finding(title: str, detail: str, primary: str) -> list[str]:
    """Cross-cutting findings that should appear under multiple dimension filters."""
    blob = f"{title} {detail}".lower()
    related: list[str] = []
    if primary == "UI/UX" and any(k in blob for k in ("unlabeled", "icon-only", "accessible name")):
        related.append("Accessibility")
    if primary == "Accessibility" and any(k in blob for k in ("button", "label")):
        related.append("UI/UX")
    if primary == "Performance" and "slow step" in blob:
        related.append("UI/UX")
    return related


def issue_matches_dimension(issue: dict[str, Any], dimension: str) -> bool:
    if issue.get("dimension") == dimension:
        return True
    return dimension in (issue.get("relatedDimensions") or [])


def _rollup_issue(
    *,
    issue_id: str,
    run_id: str,
    config: RunConfig,
    severity: str,
    title: str,
    detail: str,
    dimension: str,
    related: list[str] | None = None,
    step_id: str = "run-rollup",
) -> dict[str, Any]:
    pid = config.personas[0].id if config.personas else "unknown"
    return {
        "id": issue_id,
        "runId": run_id,
        "severity": severity,
        "title": title,
        "detail": detail,
        "persona": _persona_name(config, pid),
        "personaId": pid,
        "journey": "Run rollup",
        "journeyId": "rollup",
        "stepId": step_id,
        "dimension": dimension,
        "relatedDimensions": related or [],
        "confidence": "high",
        "owner": _owner_heuristic(title, detail),
        "recurring": 1,
        "evidence": detail,
        "severityReason": f"{severity} from automated dimension rollup",
        "suggestion": None,
    }


def _enrich_unlabeled_issue_totals(issues: list[dict[str, Any]], evidence: RunEvidence) -> None:
    total = sum(s.unlabeled_button_count for s in evidence.steps)
    step_count = sum(1 for s in evidence.steps if s.unlabeled_button_count > 0)
    if total <= 0:
        return
    for issue in issues:
        if "unlabeled" not in issue.get("title", "").lower():
            continue
        issue["detail"] = (
            f"{total} button(s) lack accessible name across {step_count} step(s)."
        )
        issue["evidence"] = issue["detail"]
        issue["recurring"] = step_count


def _append_dimension_rollup_issues(
    issues: list[dict[str, Any]],
    evidence: RunEvidence,
    dimensions: list[dict[str, Any]],
    config: RunConfig,
) -> None:
    """Add run-level findings when dimension scores flag gaps with no tagged issues."""
    existing_ids = {i["id"] for i in issues}
    unlabeled = sum(s.unlabeled_button_count for s in evidence.steps)
    missing_labels = sum(max(0, s.input_count - s.labeled_input_count) for s in evidence.steps)
    avg_ms = sum(s.duration_ms for s in evidence.steps) / max(len(evidence.steps), 1)
    sparse = sum(1 for s in evidence.steps if len(s.body_text_excerpt) < 80)

    def has_dimension(name: str) -> bool:
        return any(issue_matches_dimension(i, name) for i in issues)

    if unlabeled > 0 and not has_dimension("UI/UX") and "DIM-UI-ROLLUP" not in existing_ids:
        issues.append(
            _rollup_issue(
                issue_id="DIM-UI-ROLLUP",
                run_id=evidence.run_id,
                config=config,
                severity="P2" if unlabeled > 5 else "P3",
                title="Unlabeled controls across run",
                detail=(
                    f"{unlabeled} button(s) without accessible name across "
                    f"{sum(1 for s in evidence.steps if s.unlabeled_button_count > 0)} step(s)."
                ),
                dimension="UI/UX",
                related=["Accessibility"],
            )
        )

    if (missing_labels > 0 or unlabeled > 5) and not has_dimension("Accessibility"):
        if "DIM-A11Y-ROLLUP" not in existing_ids:
            parts = []
            if unlabeled > 5:
                parts.append(f"{unlabeled} unlabeled button(s)")
            if missing_labels > 0:
                parts.append(f"{missing_labels} input(s) missing labels")
            issues.append(
                _rollup_issue(
                    issue_id="DIM-A11Y-ROLLUP",
                    run_id=evidence.run_id,
                    config=config,
                    severity="P2",
                    title="Accessibility gaps across run",
                    detail="; ".join(parts) + ".",
                    dimension="Accessibility",
                    related=["UI/UX"] if unlabeled > 5 else [],
                )
            )

    if avg_ms > 3000 and not has_dimension("Performance") and "DIM-PERF-ROLLUP" not in existing_ids:
        issues.append(
            _rollup_issue(
                issue_id="DIM-PERF-ROLLUP",
                run_id=evidence.run_id,
                config=config,
                severity="P3",
                title="Slow average step time",
                detail=f"Average step duration ~{int(avg_ms)}ms across {len(evidence.steps)} steps.",
                dimension="Performance",
            )
        )

    if sparse > 0 and not has_dimension("Information") and "DIM-INFO-ROLLUP" not in existing_ids:
        issues.append(
            _rollup_issue(
                issue_id="DIM-INFO-ROLLUP",
                run_id=evidence.run_id,
                config=config,
                severity="P2" if sparse > 2 else "P3",
                title="Sparse content across run",
                detail=f"{sparse} step(s) with very little body text.",
                dimension="Information",
            )
        )

    for dim in dimensions:
        if dim["name"] in ("Functionality", "UI/UX", "Information", "Performance", "Accessibility"):
            continue
        if dim.get("score", 100) >= 85 or has_dimension(dim["name"]):
            continue
        rid = f"DIM-{dim['name'].upper().replace('/', '')}-ROLLUP"
        if rid in existing_ids:
            continue
        signal = dim.get("signal") or "Phase 2 heuristic from step evidence"
        issues.append(
            _rollup_issue(
                issue_id=rid,
                run_id=evidence.run_id,
                config=config,
                severity="P3",
                title=f"{dim['name']} signal from run evidence",
                detail=signal,
                dimension=dim["name"],
            )
        )


_HESITATE_DURATION_MS = 5_000   # steps slower than this are "hesitating"
_PASSIVE_ACTIONS = {"navigate", "wait", "scroll"}


def _step_behavior(step: StepSnapshot) -> str:
    """Classify step as continue / hesitate / abandon (L3-PRED-07)."""
    outcome = (step.outcome or "").lower()
    if outcome == "fail" or step.error_type:
        return "abandon"
    duration = step.duration_ms or 0
    action = (step.action or "").lower()
    if action not in _PASSIVE_ACTIONS and duration > _HESITATE_DURATION_MS:
        return "hesitate"
    if outcome == "partial":
        return "hesitate"
    return "continue"


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


def _performance_dimension_bump_from_steps(steps: list) -> tuple[int, str]:
    from rehearse.web_vitals import vitals_issues

    avg = sum(s.duration_ms for s in steps) / max(len(steps), 1)
    bump = -10 if avg > 3000 else 5
    poor = 0
    lcp_samples: list[float] = []
    for s in steps:
        vitals = getattr(s, "web_vitals", None) or {}
        if vitals:
            lcp = vitals.get("lcp")
            if lcp is not None:
                lcp_samples.append(float(lcp))
            if vitals_issues(vitals):
                poor += 1
    if poor:
        bump -= min(25, 12 * poor)
    signal = f"~{int(avg)}ms avg step"
    if lcp_samples:
        signal += f"; LCP ~{int(sum(lcp_samples) / len(lcp_samples))}ms (lab)"
    if poor:
        signal += f"; {poor} journey(s) over vitals threshold"
    return bump, signal


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
        signal = "Phase 2 heuristic from step evidence"
        if extra == "Performance":
            bump, signal = _performance_dimension_bump_from_steps(evidence.steps)
        elif extra == "Accessibility":
            unlabeled = sum(s.unlabeled_button_count for s in evidence.steps)
            bump = -15 if unlabeled > 5 else 0
        elif extra == "Trust":
            bump = -20 if evidence.auth_outcome and "fail" in evidence.auth_outcome else 5
        items.append(
            {
                "name": extra,
                "score": max(20, min(95, int(base + bump))),
                "signal": signal,
                "automated": extra == "Performance" and bool(evidence.steps),
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
                "errorType": s.error_type,
                "flaky": _step_flaky(s, evidence.steps),
                "behavior": _step_behavior(s),
                "consoleErrors": s.console_errors,
                "consoleWarnings": getattr(s, "console_warnings", None) or [],
                "networkFailures": s.network_failures,
                "webVitals": getattr(s, "web_vitals", None) or {},
                "bodyTextExcerpt": s.body_text_excerpt[:200] if s.body_text_excerpt else None,
                "artifactPaths": rel_shots,
                "exploreLog": getattr(s, "explore_log", None) or [],
                "exploreSummary": getattr(s, "explore_summary", None),
                "focusRegion": getattr(s, "focus_region", None),
            }
        )
    return out


def _serialize_issues(config: RunConfig, evidence: RunEvidence, analysis: AnalysisResult, artifacts_root: Path | None = None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for i, f in enumerate(analysis.issues):
        sev = _severity_to_ui(f.severity, f, evidence)
        pid = f.persona_ids[0] if f.persona_ids else config.personas[0].id
        step = next((s for s in evidence.steps if s.step_id == f.step_id), None)
        jid = step.journey_id if step else "unknown"
        primary_dimension = _dimension_for_finding(f.title, f.detail)
        issue: dict[str, Any] = {
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
                "dimension": primary_dimension,
                "relatedDimensions": _related_dimensions_for_finding(f.title, f.detail, primary_dimension),
                "confidence": f.confidence,
                "owner": _owner_heuristic(f.title, f.detail),
                "recurring": 1,
                "evidence": f.detail,
                "severityReason": f"P{sev[-1]} from automated heuristics" if sev.startswith("P") else None,
                "suggestion": None,
                "screenshotPath": _screenshot_path(artifacts_root, evidence.run_id, f.step_id),
            }
        if step and step.error_type:
            issue["errorType"] = step.error_type
        if step and getattr(step, "focus_region", None):
            issue["focusRegion"] = step.focus_region
        issues.append(issue)
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
                "confidence": d.confidence or "high",
            }
        )
    return out


def _serialize_experiment(exp: ExperimentSpec | None) -> dict[str, str] | None:
    if not exp:
        return None
    out: dict[str, str] = {}
    if exp.hypothesis:
        out["hypothesis"] = exp.hypothesis
    if exp.user_goal:
        out["userGoal"] = exp.user_goal
    if exp.variant_label:
        out["variantLabel"] = exp.variant_label
    return out or None


def _sync_agent_flaky_summary(agents: list[dict[str, Any]], flaky_step_count: int) -> list[dict[str, Any]]:
    import re

    for agent in agents:
        if agent.get("phase") != "journey" and "journey" not in str(agent.get("id", "")):
            continue
        summary = agent.get("lastSummary") or ""
        if "flaky steps" in summary:
            agent["lastSummary"] = re.sub(
                r"\d+ flaky steps",
                f"{flaky_step_count} flaky steps",
                summary,
                count=1,
            )
        elif summary and flaky_step_count:
            agent["lastSummary"] = f"{summary.rstrip('.')}; {flaky_step_count} flaky steps in bundle."
    return agents


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
    issues = _serialize_issues(config, evidence, analysis, artifacts_root=output_dir)
    issue_step_ids = {i["stepId"] for i in issues if i.get("stepId")}
    issues.extend(_named_error_issues(config, evidence, issue_step_ids, artifacts_root=output_dir))
    _enrich_unlabeled_issue_totals(issues, evidence)
    dimensions = _expand_dimensions(analysis.dimensions, evidence)
    _append_dimension_rollup_issues(issues, evidence, dimensions, config)
    delights = _serialize_delights(config, evidence, analysis)
    sitemap_pages, sitemap_edges, sitemap_md = _serialize_sitemap(
        ctx.sitemap if ctx else None, evidence.run_id, ctx.workflows if ctx else None
    )
    pages_crawled = len(sitemap_pages)
    agents_run = _agents_run_count(ctx)
    cost_estimate = _compute_cost_estimate(
        ctx,
        evidence,
        llm_enabled=llm_enabled,
        persona_count=len(config.personas),
    )
    steps = _serialize_steps(evidence, output_dir / "artifacts" / evidence.run_id, output_dir)
    flaky_step_count = sum(1 for s in steps if s.get("flaky"))
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
            "pages": pages_crawled,
            "pagesCrawled": pages_crawled,
            "stepCount": len(steps),
            "agentCost": cost_estimate["usd"],
            "costEstimate": cost_estimate,
            "outcome": evidence.outcome,
            "configHash": _config_hash(config),
            "agentsRun": agents_run,
            "authAttempted": evidence.auth_attempted,
            "authOutcome": evidence.auth_outcome,
            "llmEnabled": llm_enabled,
            "crawlEnabled": crawl_enabled,
            "orphans": len(ctx.sitemap.orphan_paths) if ctx and ctx.sitemap else 0,
            "authGated": len(ctx.sitemap.auth_gated_paths) if ctx and ctx.sitemap else 0,
            "networkLogPath": evidence.network_log_path
            or (ctx.metadata.get("network_log_path") if ctx else None),
            "webVitalsPath": (ctx.metadata.get("web_vitals_path") if ctx else None),
            "experiment": _serialize_experiment(config.experiment),
        },
        "steps": steps,
        "issues": issues,
        "delights": delights,
        "agents": _sync_agent_flaky_summary(_serialize_agents(ctx, evidence), flaky_step_count),
        "matrix": _serialize_matrix(config, analysis),
        "dimensions": dimensions,
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
        "narrative": (ctx.metadata.get("narrative") if ctx else None),
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
        payload.setdefault("error_type", s.get("error_type"))
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

    from rehearse.narrative import build_run_narrative

    ctx.metadata["narrative"] = build_run_narrative(
        config, evidence, analysis, ctx=ctx, use_llm=False
    )
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
