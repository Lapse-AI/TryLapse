"""TryLapse MCP server — exposes run data via Model Context Protocol.

Runs as a stdio JSON-RPC server. Connect from Claude Code via:

    # .claude/mcp.json
    {
      "mcpServers": {
        "trylapse": {
          "command": "python",
          "args": ["-m", "rehearse.mcp_server"],
          "env": { "TRYLAPSE_ARTIFACTS": "/path/to/launch-rehearsal/artifacts" }
        }
      }
    }

Tools:
    get_readiness_score   — score + band for a run
    get_blockers          — P0/P1 findings for a run
    list_runs             — recent runs with metadata
    compare_runs          — delta between two runs
    trigger_run           — enqueue a new rehearsal run
    get_run_status        — poll status of a running job
    explain_finding       — full detail for a specific finding ID
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# ── Protocol ─────────────────────────────────────────────────────────────────

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "trylapse", "version": "0.1.0"}


def _ok(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


# ── Artifact root resolution ──────────────────────────────────────────────────

def _artifacts_root() -> Path:
    env = os.environ.get("TRYLAPSE_ARTIFACTS")
    if env:
        return Path(env)
    # Walk up from CWD looking for an artifacts/ dir
    cwd = Path.cwd()
    for candidate in [cwd, cwd.parent, cwd.parent.parent]:
        p = candidate / "artifacts"
        if p.is_dir():
            return candidate
    return cwd


# ── Tool definitions (MCP schema) ────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "get_readiness_score",
        "description": (
            "Return the readiness score, band (Green/Amber/Red), verdict, "
            "and summary for a specific TryLapse run."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Run ID (e.g. 'myapp-20260618-143022'). Pass 'latest' for the most recent run.",
                }
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "get_blockers",
        "description": (
            "Return P0 and P1 findings for a run — the issues that must be fixed "
            "before shipping. Each finding includes title, detail, severity, "
            "affected personas, and evidence step ID."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Run ID or 'latest'."},
                "max_severity": {
                    "type": "string",
                    "description": "Maximum severity to include: 'P0', 'P1', 'P2', or 'P3'. Default 'P1'.",
                    "enum": ["P0", "P1", "P2", "P3"],
                },
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "list_runs",
        "description": "List recent TryLapse runs with their status, readiness band, and timestamp.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max number of runs to return (default 10).",
                },
                "config_prefix": {
                    "type": "string",
                    "description": "Filter runs by config prefix (e.g. 'myapp').",
                },
            },
        },
    },
    {
        "name": "compare_runs",
        "description": (
            "Compare two runs and return the delta: new issues, resolved issues, "
            "readiness band change, and score trajectory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id_a": {"type": "string", "description": "Baseline run ID."},
                "run_id_b": {"type": "string", "description": "Comparison run ID (the newer one)."},
            },
            "required": ["run_id_a", "run_id_b"],
        },
    },
    {
        "name": "trigger_run",
        "description": (
            "Enqueue a new TryLapse rehearsal run for a given config file. "
            "Returns a job ID you can poll with get_run_status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "config_path": {
                    "type": "string",
                    "description": "Absolute path to the YAML config file.",
                },
                "use_llm": {
                    "type": "boolean",
                    "description": "Enable LLM-powered narrative generation (requires API key).",
                },
            },
            "required": ["config_path"],
        },
    },
    {
        "name": "get_run_status",
        "description": "Check the status of a running or completed rehearsal job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Run ID or job ID from trigger_run."},
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "explain_finding",
        "description": (
            "Return the full detail for a specific finding, including the evidence "
            "step, screenshots path, persona context, and suggested fix."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Run ID containing this finding."},
                "finding_id": {
                    "type": "string",
                    "description": "Finding ID (e.g. 'I3') from get_blockers output.",
                },
            },
            "required": ["run_id", "finding_id"],
        },
    },
]


# ── Tool handlers ─────────────────────────────────────────────────────────────

def _resolve_run_id(artifacts_root: Path, run_id: str) -> str:
    if run_id != "latest":
        return run_id
    from rehearse.dashboard.store import list_run_summaries
    summaries = list_run_summaries(artifacts_root)
    if not summaries:
        raise ValueError("No runs found in artifacts directory.")
    return summaries[0]["id"]


def _load(artifacts_root: Path, run_id: str) -> dict[str, Any]:
    from rehearse.dashboard.store import load_bundle
    bundle = load_bundle(artifacts_root, run_id, rebuild=False)
    if bundle is None:
        raise ValueError(f"Run '{run_id}' not found in {artifacts_root}.")
    return bundle


def handle_get_readiness_score(args: dict, artifacts_root: Path) -> dict:
    run_id = _resolve_run_id(artifacts_root, args["run_id"])
    bundle = _load(artifacts_root, run_id)
    summary = bundle.get("summary", {})
    narrative = bundle.get("narrative", {})
    return {
        "run_id": run_id,
        "readiness_band": summary.get("readiness") or summary.get("readinessBand"),
        "score": summary.get("score"),
        "issue_count": summary.get("issueCount") or summary.get("issue_count"),
        "delight_count": summary.get("delightCount") or summary.get("delight_count"),
        "verdict": (narrative.get("layer1Verdict") or {}).get("decision"),
        "verdict_headline": (narrative.get("layer1Verdict") or {}).get("headline"),
        "story": narrative.get("layer2Story"),
        "forward": narrative.get("layer4Forward"),
        "target_url": summary.get("targetUrl") or summary.get("target_url"),
        "started_at": summary.get("startedAt") or summary.get("started_at"),
        "duration_ms": summary.get("durationMs") or summary.get("duration_ms"),
    }


def handle_get_blockers(args: dict, artifacts_root: Path) -> dict:
    run_id = _resolve_run_id(artifacts_root, args["run_id"])
    max_sev = args.get("max_severity", "P1")
    sev_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    max_rank = sev_order.get(max_sev, 1)

    bundle = _load(artifacts_root, run_id)
    all_issues = bundle.get("findings", {}).get("issues", [])
    blockers = [
        {
            "id": i.get("id"),
            "severity": i.get("severity"),
            "title": i.get("title"),
            "detail": i.get("detail"),
            "confidence": i.get("confidence"),
            "personas": i.get("persona_ids") or i.get("personaIds"),
            "step_id": i.get("step_id") or i.get("stepId"),
        }
        for i in all_issues
        if sev_order.get(i.get("severity", "P3"), 3) <= max_rank
    ]
    return {
        "run_id": run_id,
        "count": len(blockers),
        "max_severity_filter": max_sev,
        "blockers": blockers,
    }


def handle_list_runs(args: dict, artifacts_root: Path) -> dict:
    from rehearse.dashboard.store import list_run_summaries
    limit = int(args.get("limit") or 10)
    prefix = args.get("config_prefix")
    summaries = list_run_summaries(artifacts_root, config_prefix=prefix)[:limit]
    return {
        "count": len(summaries),
        "runs": [
            {
                "id": s.get("id"),
                "readiness": s.get("readiness") or s.get("readinessBand"),
                "score": s.get("score"),
                "issue_count": s.get("issueCount") or s.get("issue_count"),
                "target_url": s.get("targetUrl") or s.get("target_url"),
                "started_at": s.get("startedAt") or s.get("started_at"),
                "duration_ms": s.get("durationMs") or s.get("duration_ms"),
                "outcome": s.get("outcome"),
            }
            for s in summaries
        ],
    }


def handle_compare_runs(args: dict, artifacts_root: Path) -> dict:
    from rehearse.dashboard.store import get_run_diff
    run_a = _resolve_run_id(artifacts_root, args["run_id_a"])
    run_b = _resolve_run_id(artifacts_root, args["run_id_b"])
    try:
        diff = get_run_diff(artifacts_root, run_a, run_b)
        return diff
    except Exception:
        # Fallback: manual diff
        bundle_a = _load(artifacts_root, run_a)
        bundle_b = _load(artifacts_root, run_b)
        issues_a = {i["title"] for i in bundle_a.get("findings", {}).get("issues", [])}
        issues_b = {i["title"] for i in bundle_b.get("findings", {}).get("issues", [])}
        band_a = bundle_a.get("summary", {}).get("readiness")
        band_b = bundle_b.get("summary", {}).get("readiness")
        return {
            "run_id_a": run_a,
            "run_id_b": run_b,
            "readiness_a": band_a,
            "readiness_b": band_b,
            "band_changed": band_a != band_b,
            "new_issues": sorted(issues_b - issues_a),
            "resolved_issues": sorted(issues_a - issues_b),
            "common_issues": sorted(issues_a & issues_b),
        }


def handle_trigger_run(args: dict, artifacts_root: Path) -> dict:
    import subprocess
    config_path = Path(args["config_path"])
    if not config_path.is_file():
        raise ValueError(f"Config file not found: {config_path}")
    use_llm = bool(args.get("use_llm", False))
    cmd = [
        sys.executable, "-m", "rehearse", "run",
        "-c", str(config_path),
        "-o", str(artifacts_root),
    ]
    if use_llm:
        cmd.append("--llm")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(artifacts_root.parent),
    )
    return {
        "status": "enqueued",
        "pid": proc.pid,
        "config_path": str(config_path),
        "note": f"Run started as PID {proc.pid}. Poll get_run_status with the run_id from output.",
    }


def handle_get_run_status(args: dict, artifacts_root: Path) -> dict:
    run_id = args["run_id"]
    # Check progress file first
    progress_path = artifacts_root / "runs" / f"{run_id}-progress.json"
    if progress_path.is_file():
        try:
            progress = json.loads(progress_path.read_text())
            return {
                "run_id": run_id,
                "status": progress.get("phase") or progress.get("status") or "running",
                "progress": progress,
            }
        except Exception:
            pass
    # Fall back to evidence file
    evidence_path = artifacts_root / "runs" / f"{run_id}.json"
    if evidence_path.is_file():
        try:
            data = json.loads(evidence_path.read_text())
            return {
                "run_id": run_id,
                "status": data.get("outcome") or "complete",
                "started_at": data.get("started_at"),
                "finished_at": data.get("finished_at"),
                "duration_ms": data.get("duration_ms"),
            }
        except Exception:
            pass
    return {"run_id": run_id, "status": "not_found"}


def handle_explain_finding(args: dict, artifacts_root: Path) -> dict:
    run_id = _resolve_run_id(artifacts_root, args["run_id"])
    finding_id = args["finding_id"].upper()
    bundle = _load(artifacts_root, run_id)
    issues = bundle.get("findings", {}).get("issues", [])
    finding = next(
        (i for i in issues if (i.get("id") or "").upper() == finding_id),
        None,
    )
    if finding is None:
        raise ValueError(f"Finding '{finding_id}' not found in run '{run_id}'.")

    # Locate screenshot in artifact paths
    step_id = finding.get("step_id") or finding.get("stepId")
    artifacts_dir = artifacts_root / "artifacts" / run_id
    screenshot = None
    if step_id and artifacts_dir.is_dir():
        candidates = list(artifacts_dir.glob(f"*{step_id}*.png")) + list(artifacts_dir.glob(f"*{step_id}*.jpg")) + list(artifacts_dir.glob(f"*{step_id}*.webp"))
        if candidates:
            screenshot = str(candidates[0])

    return {
        "run_id": run_id,
        "finding": finding,
        "step_id": step_id,
        "screenshot_path": screenshot,
        "artifacts_dir": str(artifacts_dir),
        "suggested_fix": (
            "Review the evidence step artifacts at the path above. "
            f"Severity {finding.get('severity')}: "
            + {
                "P0": "Fix immediately — this journey is completely blocked.",
                "P1": "Fix before launch — significant user impact.",
                "P2": "Fix before GA — noticeable degradation.",
                "P3": "Track in backlog — polish item.",
            }.get(finding.get("severity", "P2"), "Prioritize appropriately.")
        ),
    }


# ── Dispatch table ────────────────────────────────────────────────────────────

HANDLERS = {
    "get_readiness_score": handle_get_readiness_score,
    "get_blockers": handle_get_blockers,
    "list_runs": handle_list_runs,
    "compare_runs": handle_compare_runs,
    "trigger_run": handle_trigger_run,
    "get_run_status": handle_get_run_status,
    "explain_finding": handle_explain_finding,
}


# ── MCP request processing ────────────────────────────────────────────────────

def process_request(req: dict, artifacts_root: Path) -> dict | None:
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {"tools": {}},
        })

    if method == "initialized":
        return None  # notification — no response

    if method == "ping":
        return _ok(req_id, {})

    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}
        handler = HANDLERS.get(tool_name)
        if handler is None:
            return _err(req_id, -32601, f"Unknown tool: {tool_name}")
        try:
            result = handler(tool_args, artifacts_root)
            return _ok(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as exc:
            return _ok(req_id, {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            })

    return _err(req_id, -32601, f"Method not found: {method}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    artifacts_root = _artifacts_root()
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            _send(_err(None, -32700, f"Parse error: {exc}"))
            continue
        response = process_request(req, artifacts_root)
        if response is not None:
            _send(response)


if __name__ == "__main__":
    main()
