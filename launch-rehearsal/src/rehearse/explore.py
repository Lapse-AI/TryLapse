"""LLM-guided explore loop for a single DSL step (BRW-C1 + NLU-6 evidence)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rehearse.browser import _compact_aria_tree, _resolve_locator
from rehearse.dsl import Step
from rehearse.evidence import StepSnapshot
from rehearse.llm import _llm_json_call, llm_enabled

EXPLORE_PROMPT = """You propose the next browser actions for a launch rehearsal explore step.
Evidence-bound only — use intents matching ARIA roles/names in the snapshot.

Respond JSON only:
{
  "done": false,
  "rationale": "short plain-language explanation for auditors",
  "actions": [
    {"action": "click|fill|wait|navigate", "intent": "button name", "value": "optional"}
  ]
}
Max 3 actions per round. Set done true when goal is met or no safe action."""


EXPLORE_SUMMARY_PROMPT = """Summarize an explore step for a launch rehearsal scorecard.
Use only the explore log JSON. One paragraph, past tense, evidence-bound.

Respond JSON only: {"summary": "2-4 sentences" }"""


def _safe_filename(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-")[:80] or "step"


def build_template_explore_summary(goal: str, rounds: list[dict[str, Any]]) -> str:
    if not rounds:
        return f"Explore step for goal “{goal}” produced no recorded rounds."
    action_bits: list[str] = []
    for rnd in rounds:
        for act in rnd.get("actions") or []:
            label = act.get("intent") or act.get("action") or "action"
            outcome = act.get("outcome", "ok")
            if outcome == "ok":
                action_bits.append(str(label))
    rationale = (rounds[-1].get("rationale") or "").strip()
    actions_text = ", ".join(action_bits[:6]) if action_bits else "no successful actions"
    done = rounds[-1].get("done", False)
    status = "Goal marked complete." if done else "Stopped before explicit completion."
    summary = (
        f"Explore (“{goal}”): {len(rounds)} round(s), actions: {actions_text}. {status}"
    )
    if rationale:
        summary += f" Last rationale: {rationale[:200]}"
    return summary


def enrich_explore_summary(
    goal: str,
    rounds: list[dict[str, Any]],
    *,
    template: str | None = None,
) -> str:
    base = template or build_template_explore_summary(goal, rounds)
    if not llm_enabled() or not rounds:
        return base
    blob = {"goal": goal, "rounds": rounds, "template": base}
    llm_data = _llm_json_call(
        EXPLORE_SUMMARY_PROMPT,
        f"Summarize explore evidence:\n{json.dumps(blob, indent=2)[:6000]}",
        max_tokens=400,
    )
    if llm_data and llm_data.get("summary"):
        return str(llm_data["summary"]).strip()
    return base


def save_explore_artifact(artifacts_dir: Path, step_id: str, payload: dict[str, Any]) -> str:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    path = artifacts_dir / f"explore-{_safe_filename(step_id)}.json"
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def run_explore_loop(
    session: Any,
    step: Step,
    snap: StepSnapshot,
    *,
    max_rounds: int = 3,
) -> None:
    """Execute explore step: LLM proposes actions from page snapshot."""
    page = session.page
    goal = step.intent or "Explore the page and reach a stable, testable state"
    rounds: list[dict[str, Any]] = []

    if not llm_enabled():
        snap.outcome = "partial"
        snap.note = "explore: LLM not configured (set DEEPSEEK_API_KEY)"
        snap.explore_log = rounds
        snap.explore_summary = build_template_explore_summary(goal, rounds)
        return

    for round_idx in range(max(1, max_rounds)):
        tree = _compact_aria_tree(page, max_nodes=80)
        round_entry: dict[str, Any] = {
            "round": round_idx + 1,
            "url": page.url,
            "ariaRootRole": tree.get("role"),
            "actions": [],
            "done": False,
            "rationale": None,
            "error": None,
        }
        blob = {
            "goal": goal,
            "url": page.url,
            "round": round_idx + 1,
            "aria": tree,
        }
        proposal = _llm_json_call(
            EXPLORE_PROMPT,
            f"Propose next actions:\n{json.dumps(blob, indent=2)[:8000]}",
            max_tokens=512,
        )
        if not proposal or proposal.get("error"):
            round_entry["error"] = (proposal or {}).get("error", "LLM unavailable")
            rounds.append(round_entry)
            break
        round_entry["rationale"] = proposal.get("rationale")
        round_entry["done"] = bool(proposal.get("done"))
        if proposal.get("done"):
            rounds.append(round_entry)
            break
        actions = proposal.get("actions") or []
        if not actions:
            round_entry["error"] = "no actions proposed"
            rounds.append(round_entry)
            break
        for act in actions[:3]:
            sub = Step(
                action=str(act.get("action") or "click"),
                intent=act.get("intent"),
                value=act.get("value"),
                url=act.get("url"),
            )
            action_record: dict[str, Any] = {
                "action": sub.action,
                "intent": sub.intent,
                "value": sub.value,
                "outcome": "ok",
            }
            try:
                _execute_mini_action(session, sub, timeout=session.config.budgets.step_timeout_ms)
            except Exception as exc:
                action_record["outcome"] = "fail"
                action_record["error"] = str(exc)[:200]
                round_entry["actions"].append(action_record)
                rounds.append(round_entry)
                break
            round_entry["actions"].append(action_record)
        rounds.append(round_entry)
        if round_entry.get("error") or any(a.get("outcome") == "fail" for a in round_entry["actions"]):
            break

    snap.explore_log = rounds
    template_summary = build_template_explore_summary(goal, rounds)
    snap.explore_summary = enrich_explore_summary(goal, rounds, template=template_summary)
    snap.note = (snap.explore_summary or template_summary)[:500]

    payload = {
        "stepId": snap.step_id,
        "goal": goal,
        "maxRounds": max_rounds,
        "rounds": rounds,
        "summary": snap.explore_summary,
        "finalUrl": page.url,
    }
    artifact_path = save_explore_artifact(session.artifacts_dir, snap.step_id, payload)
    snap.artifact_paths.append(artifact_path)

    if snap.outcome == "pass" and any(
        r.get("error") or any(a.get("outcome") == "fail" for a in r.get("actions") or [])
        for r in rounds
    ):
        snap.outcome = "partial"
    if not rounds:
        snap.outcome = "partial"


def _execute_mini_action(session: Any, step: Step, *, timeout: int) -> None:
    page = session.page
    if step.action == "wait":
        page.wait_for_timeout(int(step.value or "500"))
        return
    if step.action == "navigate" and step.url:
        page.goto(step.url, wait_until="domcontentloaded", timeout=timeout)
        return
    if step.action == "fill":
        loc, _ = _resolve_locator(page, step)
        value = step.value or ""
        if value and "${" in value:
            value = step.resolve_value() or ""
        loc.fill(value, timeout=timeout)
        return
    if step.action == "click":
        loc, _ = _resolve_locator(page, step)
        loc.click(timeout=timeout)
        return
    raise ValueError(f"explore unsupported action: {step.action}")
