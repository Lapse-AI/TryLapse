from rehearse.narrative import build_template_trends_narrative, build_trends_narrative


def test_template_trends_empty():
    n = build_template_trends_narrative({})
    assert "No rehearsal runs" in n["headline"]
    assert n["source"] == "template"


def test_template_trends_flake_rising():
    trends = {
        "readiness": ["Green", "Green"],
        "flakeRate": [1.0, 4.5],
        "pages": [10, 12],
        "runIds": ["a", "b"],
        "issueRecurrence": [],
        "issuesOpened": 1,
        "issuesResolved": 0,
        "blockerCounts": [0, 1],
    }
    n = build_template_trends_narrative(trends)
    assert "flake" in n["headline"].lower() or "4.5" in n["forEngineering"]
    assert n["flakeDelta"] == 3.5


def test_build_trends_no_llm_without_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("REHEARSE_LLM_API_KEY", raising=False)
    trends = {"readiness": ["Green"], "flakeRate": [0], "runIds": ["x"]}
    n = build_trends_narrative(trends, use_llm=True)
    assert n["source"] == "template"
