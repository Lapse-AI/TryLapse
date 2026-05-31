"""Sitemap model and export."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class SiteMap:
    origin: str
    pages: list  # list[CrawlPage]
    hub_paths: list[str] = field(default_factory=list)
    orphan_paths: list[str] = field(default_factory=list)
    auth_gated_paths: list[str] = field(default_factory=list)
    error_paths: list[str] = field(default_factory=list)

    @classmethod
    def from_pages(cls, origin: str, pages: list) -> SiteMap:
        paths = {p.path for p in pages}
        inbound: Counter[str] = Counter()
        outbound_map: dict[str, list[str]] = {}

        for p in pages:
            outbound_map[p.path] = p.outbound_paths
            for out in p.outbound_paths:
                if out in paths:
                    inbound[out] += 1

        hub_paths = sorted(
            [p.path for p in pages],
            key=lambda x: len(outbound_map.get(x, [])),
            reverse=True,
        )[:10]

        home = "/" if "/" in paths else (pages[0].path if pages else "/")
        orphan_paths = [
            p.path
            for p in pages
            if p.path != home and inbound.get(p.path, 0) == 0
        ]
        auth_gated = [p.path for p in pages if p.redirected_to_login]
        error_paths = [p.path for p in pages if p.error_phrases or (p.status and p.status >= 400)]

        return cls(
            origin=origin,
            pages=pages,
            hub_paths=hub_paths,
            orphan_paths=orphan_paths,
            auth_gated_paths=auth_gated,
            error_paths=error_paths,
        )

    @classmethod
    def from_json_dict(cls, data: dict) -> SiteMap:
        from rehearse.crawler import CrawlPage

        pages = [CrawlPage(**p) for p in data.get("pages", [])]
        return cls(
            origin=data.get("origin", ""),
            pages=pages,
            hub_paths=data.get("hub_paths", []),
            orphan_paths=data.get("orphan_paths", []),
            auth_gated_paths=data.get("auth_gated_paths", []),
            error_paths=data.get("error_paths", []),
        )

    @classmethod
    def load_json(cls, path: Path) -> SiteMap | None:
        if not path.is_file():
            return None
        return cls.from_json_dict(json.loads(path.read_text()))

    def save_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "origin": self.origin,
            "page_count": len(self.pages),
            "hub_paths": self.hub_paths,
            "orphan_paths": self.orphan_paths,
            "auth_gated_paths": self.auth_gated_paths,
            "error_paths": self.error_paths,
            "pages": [asdict(p) for p in self.pages],
        }
        path.write_text(json.dumps(data, indent=2))
        return path

    def render_markdown(self) -> str:
        lines = [
            "# Site map",
            "",
            f"**Origin:** {self.origin}  ",
            f"**Pages crawled:** {len(self.pages)}  ",
            "",
            "## Hub pages (most outbound links)",
            "",
        ]
        for p in self.hub_paths[:8]:
            page = next((x for x in self.pages if x.path == p), None)
            title = page.title if page else ""
            lines.append(f"- `{p}` — {title}")
        if self.auth_gated_paths:
            lines.extend(["", "## Auth-gated (redirect to login)", ""])
            for p in self.auth_gated_paths[:15]:
                lines.append(f"- `{p}`")
        if self.orphan_paths:
            lines.extend(["", "## Orphan pages (no inbound links from crawl)", ""])
            for p in self.orphan_paths[:15]:
                lines.append(f"- `{p}`")
        lines.extend(["", "## All pages", "", "| Path | Title | Depth | Links | Forms | Words |", "|------|-------|-------|-------|-------|-------|"])
        for p in sorted(self.pages, key=lambda x: x.path):
            lines.append(
                f"| `{p.path}` | {p.title[:40]} | {p.depth} | {p.link_count} | {p.form_count} | {p.word_count} |"
            )
        return "\n".join(lines)

    def save_markdown(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_markdown())
        return path
