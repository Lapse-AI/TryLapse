"""Site crawler — same-origin BFS with Playwright."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page

from rehearse.dsl import CrawlConfig

# Title/H1 only — avoid flagging pages that mention "error" in issue/history copy
_HEADING_ERROR_PATTERNS = (
    "404",
    "page not found",
    "not found",
    "500 internal",
    "internal server error",
    "access denied",
    "forbidden",
    "unauthorized",
)


@dataclass
class CrawlPage:
    url: str
    path: str
    title: str
    depth: int
    status: int | None = None
    h1: str = ""
    link_count: int = 0
    form_count: int = 0
    input_count: int = 0
    button_count: int = 0
    word_count: int = 0
    outbound_paths: list[str] = field(default_factory=list)
    redirected_to_login: bool = False
    error_phrases: list[str] = field(default_factory=list)
    duration_ms: int = 0


def _same_origin(base: str, url: str) -> bool:
    b = urlparse(base)
    u = urlparse(url)
    return u.netloc == b.netloc and u.scheme in ("http", "https")


def _normalize_url(base: str, href: str) -> str | None:
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    full = urljoin(base, href)
    parsed = urlparse(full)
    return parsed._replace(fragment="").geturl()


def _path_excluded(path: str, prefixes: list[str]) -> bool:
    if not prefixes:
        return False
    norm = path if path.startswith("/") else f"/{path}"
    for prefix in prefixes:
        p = prefix if prefix.startswith("/") else f"/{prefix}"
        if norm == p.rstrip("/") or norm.startswith(p):
            return True
    return False


def _heading_error_signals(title: str, h1: str) -> list[str]:
    head = f"{title} {h1}".lower().strip()
    if not head:
        return []
    for pattern in _HEADING_ERROR_PATTERNS:
        if pattern in head:
            return [pattern]
    if re.match(r"^(error|oops|something went wrong)\b", head):
        return ["error_page_title"]
    return []


def page_has_crawl_error(page: CrawlPage) -> bool:
    """True when the page is an HTTP or dedicated error surface (not body substring noise)."""
    if page.status is not None and page.status >= 400:
        return True
    if page.error_phrases and any(
        p.startswith("http_") or p.startswith("nav_failed") for p in page.error_phrases
    ):
        return True
    return bool(_heading_error_signals(page.title, page.h1))


def _extract_page_data(page: Page, url: str, depth: int, started: float) -> CrawlPage:
    path = urlparse(url).path or "/"
    title = page.title()
    body = ""
    try:
        body = page.locator("body").inner_text(timeout=5000)
    except Exception:
        pass
    words = len(body.split())
    h1 = ""
    try:
        if page.locator("h1").count() > 0:
            h1 = page.locator("h1").first.inner_text(timeout=3000)[:200]
    except Exception:
        pass

    metrics = page.evaluate(
        """() => {
          const links = [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'));
          return {
            linkCount: links.length,
            formCount: document.querySelectorAll('form').length,
            inputCount: document.querySelectorAll('input,textarea,select').length,
            buttonCount: document.querySelectorAll('button').length,
            links,
          };
        }"""
    )
    outbound = []
    for href in metrics.get("links", []):
        norm = _normalize_url(url, href)
        if norm:
            outbound.append(urlparse(norm).path or "/")

    redirected = "/login" in page.url.lower() or "/signin" in page.url.lower()
    status: int | None = None

    return CrawlPage(
        url=page.url,
        path=path,
        title=title[:200],
        depth=depth,
        h1=h1,
        link_count=int(metrics.get("linkCount", 0)),
        form_count=int(metrics.get("formCount", 0)),
        input_count=int(metrics.get("inputCount", 0)),
        button_count=int(metrics.get("buttonCount", 0)),
        word_count=words,
        outbound_paths=sorted(set(outbound)),
        redirected_to_login=redirected and path not in ("/login", "/signin"),
        error_phrases=[],
        duration_ms=int((time.perf_counter() - started) * 1000),
    )


def crawl_site(
    page: Page,
    start_url: str,
    config: CrawlConfig,
    *,
    timeout_ms: int = 30000,
) -> list[CrawlPage]:
    origin = start_url.rstrip("/")
    parsed = urlparse(start_url)
    seed = f"{origin}{parsed.path or '/'}"
    excludes = list(config.exclude_path_prefixes)

    queue: list[tuple[str, int]] = [(seed, 0)]
    seen: set[str] = set()
    pages: list[CrawlPage] = []
    # Pattern-based sampling: track how many pages per URL template
    pattern_samples: dict[str, int] = {}
    max_samples_per_pattern = 2

    def _path_pattern(path: str) -> str:
        parts = [p for p in path.split("/") if p]
        normed = []
        for p in parts:
            if re.match(r'^\d+$', p) or re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}', p, re.I):
                normed.append("{id}")
            elif re.match(r'^[a-z0-9][a-z0-9_-]{7,}$', p, re.I) and (re.search(r'\d', p) or len(p) > 20):
                normed.append("{id}")
            else:
                normed.append(p)
        return "/" + "/".join(normed) if normed else "/"

    while queue and len(pages) < config.max_pages:
        url, depth = queue.pop(0)
        norm = urlparse(url)
        key = (norm.path or "/").rstrip("/") or "/"
        if key in seen or _path_excluded(key, excludes):
            continue

        # Skip structurally redundant pages
        pat = _path_pattern(key)
        if pattern_samples.get(pat, 0) >= max_samples_per_pattern and pat not in ("/", "/{id}"):
            continue
        pattern_samples[pat] = pattern_samples.get(pat, 0) + 1

        seen.add(key)

        started = time.perf_counter()
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 12000))
            cp = _extract_page_data(page, url, depth, started)
            cp.status = resp.status if resp else None
            cp.error_phrases = _heading_error_signals(cp.title, cp.h1)
            if cp.status is not None and cp.status >= 400:
                cp.error_phrases = [f"http_{cp.status}", *cp.error_phrases]
        except Exception as exc:
            cp = CrawlPage(
                url=url,
                path=key,
                title="",
                depth=depth,
                status=None,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
            cp.error_phrases = [f"nav_failed:{str(exc)[:60]}"]
            pages.append(cp)
            continue

        pages.append(cp)

        if depth >= config.max_depth:
            continue
        for href in cp.outbound_paths:
            if _path_excluded(href, excludes):
                continue
            full = urljoin(origin, href)
            if config.same_origin_only and not _same_origin(origin, full):
                continue
            p = urlparse(full).path or "/"
            if p not in seen:
                queue.append((full, depth + 1))

    return pages
