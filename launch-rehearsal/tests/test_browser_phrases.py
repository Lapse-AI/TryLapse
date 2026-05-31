"""Body error-phrase detection — avoid job-queue false positives."""

from rehearse.browser import _find_error_phrases


def test_ignores_job_queue_failed_status():
    text = "Job queue job_be0c5814 run failed job_349020f3 run done"
    assert "failed" not in _find_error_phrases(text)


def test_detects_real_failed_outside_job_queue():
    text = "Something failed to load your dashboard"
    assert "failed" in _find_error_phrases(text)


def test_ignores_monitoring_error_vocabulary():
    text = "Flake rate 14% error rate trend top blocker P1 issues"
    assert "error" not in _find_error_phrases(text)
