"""Synthesizer agent — merges multi-agent reports into unified analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path

from rehearse.agents.base import BaseAgent
from rehearse.context import AgentReport, RunContext
from rehearse.heuristics import AnalysisResult, Finding, _overall_readiness


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", title.lower())).strip()


def _is_duplicate(candidate: str, existing: list[str], embedder: object | None = None) -> bool:
    """Return True if candidate is semantically similar to any title in existing.

    Primary path: sentence-transformer cosine similarity (requires optional dep).
    Fallback path: token-Jaccard + prefix match — no extra dependencies needed.

    Upgrade path: install sentence-transformers and call with a loaded model to
    get embedding-quality dedup. Until then, the stdlib fallback catches rephrases
    with >60% word overlap and common truncation variants.
    """
    norm_cand = _normalize_title(candidate)
    cand_tokens = set(norm_cand.split())

    if embedder is not None:
        try:
            import numpy as np  # type: ignore[import]
            existing_embs = embedder.encode(existing)
            cand_emb = embedder.encode([candidate])[0]
            norms = np.linalg.norm(existing_embs, axis=1) * np.linalg.norm(cand_emb)
            sims = np.dot(existing_embs, cand_emb) / np.where(norms == 0, 1, norms)
            if float(sims.max()) > 0.85:
                return True
        except Exception:
            pass  # fall through to stdlib path

    for title in existing:
        norm_ex = _normalize_title(title)
        if norm_ex == norm_cand:
            return True
        # One is a prefix of the other (same bug, slightly different qualifier)
        if len(norm_cand) > 15 and (norm_ex.startswith(norm_cand) or norm_cand.startswith(norm_ex)):
            return True
        # High token overlap — same word cloud, different phrasing
        ex_tokens = set(norm_ex.split())
        if cand_tokens and ex_tokens:
            union = len(cand_tokens | ex_tokens)
            if union > 0 and len(cand_tokens & ex_tokens) / union >= 0.6:
                return True
    return False


def _load_embedder() -> object | None:
    """Try to load the sentence-transformer model; return None if unavailable."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import]
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


class SynthesizerAgent(BaseAgent):
    agent_id = "synthesizer"
    agent_role = "Cross-agent synthesis"
    phase = "synthesize"

    def execute(self, ctx: RunContext) -> AgentReport:
        from rehearse.heuristics import analyze_run

        base = analyze_run(ctx.config, ctx.evidence, sitemap=ctx.sitemap)

        # Merge persona-specific journey matrix
        matrix: dict[str, dict[str, str]] = {}
        for journey in ctx.config.journeys:
            matrix[journey.id] = {}
            for persona in ctx.config.personas:
                statuses = []
                for report in ctx.agent_reports:
                    if report.journey_grades.get(journey.id, {}).get(persona.id):
                        statuses.append(report.journey_grades[journey.id][persona.id])
                if statuses:
                    # Most pessimistic grade wins
                    if "fail" in statuses:
                        matrix[journey.id][persona.id] = "fail"
                    elif "partial" in statuses:
                        matrix[journey.id][persona.id] = "partial"
                    else:
                        matrix[journey.id][persona.id] = "pass"
                else:
                    matrix[journey.id][persona.id] = base.journey_matrix.get(journey.id, {}).get(persona.id, "pass")

        base.journey_matrix = matrix

        # Merge findings/delights from all agents — semantic dedup (not just exact title match)
        embedder = _load_embedder()
        existing_f_titles: list[str] = [f.title for f in base.issues]
        existing_d_titles: list[str] = [d.title for d in base.delights]
        for report in ctx.agent_reports:
            for f in report.findings:
                if not _is_duplicate(f.title, existing_f_titles, embedder):
                    base.issues.append(f)
                    existing_f_titles.append(f.title)
            for d in report.delights:
                if not _is_duplicate(d.title, existing_d_titles, embedder):
                    base.delights.append(d)
                    existing_d_titles.append(d.title)

        # Re-number issue/delight IDs
        for i, issue in enumerate(base.issues, 1):
            issue.id = f"I{i}"
        for i, delight in enumerate(base.delights, 1):
            delight.id = f"D{i}"

        base.readiness = _overall_readiness(base)
        if base.issues:
            base.top_blocker = base.issues[0].title
        if base.delights:
            base.top_delight = base.delights[0].title

        # C5: cross-run regression detection
        _detect_regressions(ctx, base, existing_f_titles, embedder)

        ctx.synthesis = base

        report = AgentReport(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            summary=f"Synthesized {len(base.issues)} issues, {len(base.delights)} delights from {len(ctx.agent_reports)} agent reports",
            findings=[],
            delights=[],
            metadata={
                "agents_merged": len(ctx.agent_reports),
                "readiness": base.readiness,
            },
        )
        return report


def _detect_regressions(
    ctx: RunContext,
    base: AnalysisResult,
    existing_titles: list[str],
    embedder: object | None,
) -> None:
    """C5: Compare current findings against previous run — flag genuinely new issues.

    Only P0/P1 regressions are filed; lower-severity new findings are expected
    churn and are not annotated to avoid noise.
    """
    output_dir_str = ctx.metadata.get("output_dir")
    if not output_dir_str:
        return

    try:
        output_dir = Path(output_dir_str)
        current_run_id = ctx.evidence.run_id

        m = re.match(r"^(.*)-\d{8}-\d{6}$", current_run_id)
        config_prefix = m.group(1) if m else current_run_id

        analysis_dir = output_dir / "analysis"
        if not analysis_dir.is_dir():
            return

        prior_files = sorted(
            [f for f in analysis_dir.glob(f"{config_prefix}-*.json") if f.stem != current_run_id],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if not prior_files:
            return

        prev_data = json.loads(prior_files[0].read_text())
        prev_titles = [i.get("title", "") for i in prev_data.get("issues", [])]
        if not prev_titles:
            return

        # Find issues in current run that weren't in the previous run
        regressions: list[Finding] = []
        for issue in base.issues:
            if issue.severity not in ("P0", "P1"):
                continue
            if not _is_duplicate(issue.title, prev_titles, embedder):
                regressions.append(issue)

        # Annotate regressed issues (don't double-file; just mark them)
        for issue in regressions:
            issue.detail = f"[Regression: first seen in this run] {issue.detail}"

        if regressions:
            ctx.metadata["regression_count"] = len(regressions)
    except Exception:
        pass  # regression detection is non-blocking
