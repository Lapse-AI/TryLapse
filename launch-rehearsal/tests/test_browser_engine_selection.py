"""Browser engine selection — chromium/firefox/webkit, not chromium-only.

Chromium-only was a real, named competitive gap: a "mobile Safari" persona
was actually desktop Chromium with a mobile viewport, never real WebKit
rendering — a meaningfully different engine from what real iOS Safari
users hit. `_launch_browser` centralizes engine selection so it's a single
config field (run.browser_engine) rather than three independent hardcoded
`pw.chromium.launch()` call sites that could drift.

Real WebKit launch + page load was verified manually (not in this suite —
consistent with the rest of the test suite, which mocks Playwright rather
than launching real browsers in CI): `playwright install webkit` then
`pw.webkit.launch(headless=True)` successfully loaded example.com and
returned its title.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from rehearse.browser import _launch_browser
from rehearse.dsl import ConfigError, load_config


def _mock_playwright():
    # SimpleNamespace (not MagicMock) so an unknown engine name genuinely
    # misses via getattr(..., None) instead of MagicMock auto-vivifying a
    # fresh mock attribute for any name accessed.
    return SimpleNamespace(
        chromium=MagicMock(), firefox=MagicMock(), webkit=MagicMock(),
    )


@pytest.mark.parametrize("engine", ["chromium", "firefox", "webkit"])
def test_launch_browser_dispatches_to_correct_engine(engine):
    pw = _mock_playwright()
    _launch_browser(pw, engine)
    getattr(pw, engine).launch.assert_called_once_with(headless=True)
    for other in {"chromium", "firefox", "webkit"} - {engine}:
        getattr(pw, other).launch.assert_not_called()


def test_launch_browser_respects_headless_false():
    pw = _mock_playwright()
    _launch_browser(pw, "chromium", headless=False)
    pw.chromium.launch.assert_called_once_with(headless=False)


def test_launch_browser_rejects_unknown_engine():
    pw = _mock_playwright()
    with pytest.raises(ConfigError):
        _launch_browser(pw, "internet-explorer")


def test_config_defaults_to_chromium(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(
        "run:\n  target_url: https://example.com\n  run_id_prefix: t\n"
        "personas:\n- {id: p1, name: A, role: r}\n- {id: p2, name: B, role: r}\n"
        "- {id: p3, name: C, role: r}\n"
        "journeys:\n" + "".join(
            f"- id: j{i}\n  name: J{i}\n  steps:\n  - action: navigate\n    url: '{{target_url}}/'\n"
            for i in range(5)
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.browser_engine == "chromium"


def test_config_accepts_webkit(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(
        "run:\n  target_url: https://example.com\n  run_id_prefix: t\n  browser_engine: webkit\n"
        "personas:\n- {id: p1, name: A, role: r}\n- {id: p2, name: B, role: r}\n"
        "- {id: p3, name: C, role: r}\n"
        "journeys:\n" + "".join(
            f"- id: j{i}\n  name: J{i}\n  steps:\n  - action: navigate\n    url: '{{target_url}}/'\n"
            for i in range(5)
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.browser_engine == "webkit"


def test_config_rejects_invalid_engine(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(
        "run:\n  target_url: https://example.com\n  run_id_prefix: t\n  browser_engine: netscape\n"
        "personas:\n- {id: p1, name: A, role: r}\n- {id: p2, name: B, role: r}\n"
        "- {id: p3, name: C, role: r}\n"
        "journeys:\n" + "".join(
            f"- id: j{i}\n  name: J{i}\n  steps:\n  - action: navigate\n    url: '{{target_url}}/'\n"
            for i in range(5)
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(p)
