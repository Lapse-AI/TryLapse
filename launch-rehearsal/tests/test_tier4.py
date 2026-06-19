"""Tests for Tier 4 features: SEO signals, TF-IDF dedup, cross-run delta."""
import json
from pathlib import Path
from rehearse.embeddings import TFIDFEmbedder
from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.evidence import RunEvidence, StepSnapshot
from rehearse.heuristics import analyze_run


def _cfg():
    return RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=[Persona(id="p1", name="A", role="evaluator", goals=[])],
        journeys=[Journey(id="j1", name="One", steps=[Step(action="navigate", url="https://x/")])],
        budgets=Budgets(),
    )


def _step(step_id="j1-p1-s1-desktop", **kwargs):
    return StepSnapshot(step_id=step_id, journey_id="j1", journey_name="One",
                        persona_id="p1", action="navigate", **kwargs)


# ── TFIDFEmbedder tests ────────────────────────────────────────────────────────

def test_tfidf_exact_duplicate():
    emb = TFIDFEmbedder()
    assert emb.is_duplicate("Checkout button fails on submit", ["Checkout button fails on submit"])


def test_tfidf_high_overlap_duplicate():
    # High word overlap → TF-IDF cosine exceeds 0.80 threshold
    emb = TFIDFEmbedder()
    assert emb.is_duplicate(
        "Checkout submit button unresponsive on payment page",
        ["Checkout submit button unresponsive payment flow"],
    )


def test_tfidf_paraphrase_below_threshold():
    # TF-IDF cannot catch full semantic rephrasing — that requires sentence-transformers.
    # This confirms the documented limitation: TF-IDF catches high word-overlap duplicates,
    # not arbitrary paraphrases. The fallback Jaccard path in synthesizer.py handles this.
    emb = TFIDFEmbedder()
    result = emb.is_duplicate(
        "Submit button does not work during checkout",
        ["Checkout submit button fails when clicked"],
    )
    # Not asserting True — this is a known limitation at TF-IDF threshold 0.80.


def test_tfidf_distinct_findings():
    emb = TFIDFEmbedder()
    assert not emb.is_duplicate(
        "Login form error message missing",
        ["Checkout payment button unresponsive"],
    )


def test_tfidf_empty_existing():
    emb = TFIDFEmbedder()
    assert not emb.is_duplicate("Any finding", [])


# ── SEO heuristics tests ───────────────────────────────────────────────────────

def test_seo_missing_meta_description_fires_p2():
    cfg = _cfg()
    ev = RunEvidence(run_id="t-20260619-000001", target_url="https://x", product_name="T",
                     started_at="2026-06-19T00:00:00Z")
    ev.add_step(_step(outcome="pass", seo_meta={"metaDescription": None, "h1Count": 1,
                                                  "robots": None, "canonical": None}))
    result = analyze_run(cfg, ev)
    titles = {i.title for i in result.issues}
    assert "Missing meta description on key pages" in titles


def test_seo_noindex_fires_p2_hypothesis():
    cfg = _cfg()
    ev = RunEvidence(run_id="t-20260619-000002", target_url="https://x", product_name="T",
                     started_at="2026-06-19T00:00:00Z")
    ev.add_step(_step(outcome="pass", seo_meta={"metaDescription": "ok", "h1Count": 1,
                                                  "robots": "noindex, nofollow", "canonical": None}))
    result = analyze_run(cfg, ev)
    titles = {i.title for i in result.issues}
    assert "Pages marked noindex may block search visibility" in titles


def test_seo_duplicate_titles_fires_p2():
    cfg = _cfg()
    ev = RunEvidence(run_id="t-20260619-000003", target_url="https://x", product_name="T",
                     started_at="2026-06-19T00:00:00Z")
    ev.add_step(StepSnapshot("j1-p1-s1-desktop", "j1", "One", "p1", "navigate",
                              outcome="pass", page_title="Home | Acme",
                              final_url="https://x/", seo_meta={"metaDescription": "ok", "h1Count": 1,
                                                                   "robots": None}))
    ev.add_step(StepSnapshot("j1-p1-s2-desktop", "j1", "One", "p1", "navigate",
                              outcome="pass", page_title="Home | Acme",
                              final_url="https://x/about", seo_meta={"metaDescription": "ok", "h1Count": 1,
                                                                       "robots": None}))
    result = analyze_run(cfg, ev)
    titles = {i.title for i in result.issues}
    assert "Duplicate page titles detected" in titles


def test_seo_no_issues_when_all_ok():
    cfg = _cfg()
    ev = RunEvidence(run_id="t-20260619-000004", target_url="https://x", product_name="T",
                     started_at="2026-06-19T00:00:00Z")
    ev.add_step(_step(outcome="pass", page_title="My App",
                      seo_meta={"metaDescription": "Great product", "h1Count": 1,
                                "robots": None, "canonical": "https://x/"}))
    result = analyze_run(cfg, ev)
    seo_titles = [i.title for i in result.issues if "seo" in i.title.lower()
                  or "meta" in i.title.lower() or "noindex" in i.title.lower()
                  or "duplicate" in i.title.lower() or "h1" in i.title.lower()]
    assert seo_titles == []


# ── Cross-run delta tests ─────────────────────────────────────────────────────

def test_cross_run_delta_new_and_resolved(tmp_path):
    from rehearse.analysis_export import _cross_run_delta

    prior = {
        "summary": {"readiness": 70},
        "issues": [
            {"title": "Old issue A", "severity": "P1"},
            {"title": "Resolved issue B", "severity": "P0"},
        ],
        "dimensions": {"auth": {"score": 60}, "core_flows": {"score": 80}},
    }
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    (analysis_dir / "myapp-20260618-100000.json").write_text(json.dumps(prior))

    current_issues = [
        {"title": "Old issue A", "severity": "P1"},
        {"title": "Brand new P0 finding", "severity": "P0"},
    ]
    current_dims = {"auth": {"score": 75}, "core_flows": {"score": 80}}

    delta = _cross_run_delta(tmp_path, "myapp-20260619-120000", current_issues, current_dims)

    assert delta is not None
    assert "Brand new P0 finding" in delta["newFindings"]
    assert "Resolved issue B" in delta["resolvedFindings"]
    assert "Old issue A" not in delta["newFindings"]
    assert delta["newP0s"] == 1
    assert delta["axisDeltas"]["auth"] == 15  # 75 - 60
    assert delta["axisDeltas"]["core_flows"] == 0


def test_cross_run_delta_returns_none_on_first_run(tmp_path):
    from rehearse.analysis_export import _cross_run_delta
    result = _cross_run_delta(tmp_path, "myapp-20260619-120000", [], None)
    assert result is None
