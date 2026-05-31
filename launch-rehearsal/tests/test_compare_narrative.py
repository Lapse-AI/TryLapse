"""NLU-2 compare narratives."""

from rehearse.narrative import build_template_compare_narrative, _readiness_rank


def test_compare_improved_verdict():
    diff = {
        "runA": "old-run",
        "runB": "new-run",
        "readinessA": "Amber",
        "readinessB": "Green",
        "issuesA": 5,
        "issuesB": 2,
        "pagesA": 10,
        "pagesB": 12,
        "newIssues": [],
        "resolvedIssues": ["Auth wall on deep link", "Sparse page content"],
        "changedSteps": [],
        "stepsOnlyInA": [],
        "stepsOnlyInB": [],
    }
    n = build_template_compare_narrative(diff)
    assert n["verdict"] == "improved"
    assert "Green" in n["headline"]
    assert _readiness_rank("Green") > _readiness_rank("Amber")
