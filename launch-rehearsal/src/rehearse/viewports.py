"""Viewport profiles for multi-device rehearsal."""

from __future__ import annotations

VIEWPORT_PROFILES: dict[str, dict[str, int]] = {
    "desktop": {"width": 1280, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}

DEFAULT_VIEWPORTS = ("desktop",)


def normalize_viewports(names: list[str] | None) -> list[str]:
    if not names:
        return list(DEFAULT_VIEWPORTS)
    out: list[str] = []
    for n in names:
        key = str(n).strip().lower()
        if key in VIEWPORT_PROFILES and key not in out:
            out.append(key)
    return out or list(DEFAULT_VIEWPORTS)
