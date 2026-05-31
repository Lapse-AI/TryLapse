"""Focus region capture helpers."""

from __future__ import annotations

from rehearse.browser import capture_focus_region


class _BoxLocator:
    def __init__(self, box: dict | None) -> None:
        self._box = box

    @property
    def first(self) -> "_BoxLocator":
        return self

    def bounding_box(self) -> dict | None:
        return self._box


class _FakePage:
    def __init__(self, box: dict | None) -> None:
        self.viewport_size = {"width": 1280, "height": 900}
        self._box = box

    def locator(self, _sel: str) -> _BoxLocator:
        return _BoxLocator(self._box)


def test_capture_focus_region_returns_percent_friendly_box() -> None:
    page = _FakePage({"x": 100, "y": 200, "width": 50, "height": 30})
    loc = page.locator("button")
    region = capture_focus_region(page, loc, label="Submit")  # type: ignore[arg-type]
    assert region is not None
    assert region["x"] == 100.0
    assert region["label"] == "Submit"
    assert region["viewportWidth"] == 1280


def test_capture_focus_region_skips_tiny_box() -> None:
    page = _FakePage({"x": 0, "y": 0, "width": 1, "height": 1})
    loc = page.locator("x")
    assert capture_focus_region(page, loc) is None  # type: ignore[arg-type]
