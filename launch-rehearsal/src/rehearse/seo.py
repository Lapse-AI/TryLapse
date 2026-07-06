"""SEO health signal scanner — runs post-crawl on page snapshots.

Checks each visited page for common SEO defects that are launch-blockers
for products expecting organic traffic. All findings are deterministic
(no LLM): check the DOM, file the finding.

Findings produced:
  P2  missing_meta_description    — page has no <meta name="description">
  P2  duplicate_page_title        — same <title> found on 2+ pages
  P2  noindex_on_indexable_page   — page has noindex but is not /admin/ or a draft
  P2  images_missing_alt          — <img> without alt attribute on a page
  P2  broken_canonical            — <link rel="canonical"> points to a different domain
"""

from __future__ import annotations

import re
from typing import Any


# Pages whose noindex is expected and should not be filed as a finding
_NOINDEX_EXPECTED_PATTERNS = [
    re.compile(r"/admin(?:/|$)", re.I),
    re.compile(r"/draft(?:/|$)", re.I),
    re.compile(r"/preview(?:/|$)", re.I),
    re.compile(r"/internal(?:/|$)", re.I),
    re.compile(r"[?&]preview=", re.I),
    re.compile(r"[?&]draft=", re.I),
]


def _noindex_expected(url: str) -> bool:
    return any(p.search(url) for p in _NOINDEX_EXPECTED_PATTERNS)


def _dom_text(snapshot: dict[str, Any], key: str) -> str:
    """Safely extract a text field from a DOM snapshot dict."""
    v = snapshot.get(key)
    if isinstance(v, str):
        return v.strip()
    return ""


def run_seo_checks(
    page_snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run all SEO checks across a list of page DOM snapshots.

    Each snapshot is a dict with at minimum:
        url             str
        title           str | None
        meta_description str | None
        robots_meta     str | None         (content of <meta name="robots">)
        canonical_url   str | None         (href of <link rel="canonical">)
        images_without_alt int | None      (count of <img> lacking alt)
        image_count     int | None         (total <img> count on page)

    The crawl phase (deep_crawler.py / crawler.py) is responsible for
    extracting these fields via Playwright page.evaluate() calls and
    passing them in. If a field is absent from the snapshot it is skipped
    rather than filed as a false positive.

    Returns a list of finding dicts compatible with the heuristics.Finding
    shape expected by analysis_export.py.
    """
    findings: list[dict[str, Any]] = []
    seen_titles: dict[str, list[str]] = {}  # title → [url, ...]

    for snap in page_snapshots:
        url = snap.get("url") or ""

        # ── 1. Missing meta description ────────────────────────────────────
        meta_desc = snap.get("meta_description")
        if meta_desc is not None and not str(meta_desc).strip():
            findings.append({
                "id": f"seo-no-meta-{_url_slug(url)}",
                "severity": "P2",
                "confidence": "high",
                "dimension": "Information",
                "title": f"Missing meta description on {_path(url)}",
                "detail": (
                    f"The page at {url} has no <meta name=\"description\"> tag. "
                    "Search engines use this to generate preview snippets. "
                    "Missing it reduces click-through rates from search results."
                ),
                "url": url,
                "type": "seo_missing_meta_description",
                "automated": True,
            })

        # ── 2. Duplicate page titles ────────────────────────────────────────
        title = snap.get("title")
        if title and str(title).strip():
            title_norm = str(title).strip().lower()
            seen_titles.setdefault(title_norm, []).append(url)

        # ── 3. Noindex on indexable page ────────────────────────────────────
        robots = snap.get("robots_meta")
        if robots and "noindex" in str(robots).lower() and not _noindex_expected(url):
            findings.append({
                "id": f"seo-noindex-{_url_slug(url)}",
                "severity": "P2",
                "confidence": "high",
                "dimension": "Information",
                "title": f"noindex on public page: {_path(url)}",
                "detail": (
                    f"The page at {url} has <meta name=\"robots\" content=\"{robots}\"> "
                    "which tells search engines not to index it. If this page should appear "
                    "in search results, remove the noindex directive before launch."
                ),
                "url": url,
                "type": "seo_noindex_on_indexable_page",
                "automated": True,
            })

        # ── 4. Images missing alt text ──────────────────────────────────────
        img_total = snap.get("image_count")
        img_no_alt = snap.get("images_without_alt")
        if img_no_alt and int(img_no_alt) > 0 and img_total:
            findings.append({
                "id": f"seo-alt-{_url_slug(url)}",
                "severity": "P2",
                "confidence": "high",
                "dimension": "Accessibility",
                "title": f"{img_no_alt} image(s) missing alt text on {_path(url)}",
                "detail": (
                    f"{img_no_alt} of {img_total} images on {url} lack alt attributes. "
                    "Missing alt text harms both accessibility (screen readers) and SEO "
                    "(search engines cannot index image content)."
                ),
                "url": url,
                "type": "seo_images_missing_alt",
                "automated": True,
            })

        # ── 5. Broken canonical ─────────────────────────────────────────────
        canonical = snap.get("canonical_url")
        if canonical and str(canonical).strip():
            canon_str = str(canonical).strip()
            page_domain = _domain(url)
            canon_domain = _domain(canon_str)
            if page_domain and canon_domain and page_domain != canon_domain:
                findings.append({
                    "id": f"seo-canon-{_url_slug(url)}",
                    "severity": "P2",
                    "confidence": "high",
                    "dimension": "Information",
                    "title": f"Canonical points to different domain on {_path(url)}",
                    "detail": (
                        f"The page at {url} has a canonical tag pointing to {canonical}, "
                        f"which is on a different domain ({canon_domain}). "
                        "This tells search engines to attribute the page's authority "
                        "to a different site, not yours."
                    ),
                    "url": url,
                    "type": "seo_broken_canonical",
                    "automated": True,
                })

    # ── 2b. File duplicate-title findings (cross-page, done after loop) ────
    for title_norm, urls in seen_titles.items():
        if len(urls) > 1:
            findings.append({
                "id": f"seo-dup-title-{_url_slug(urls[0])}",
                "severity": "P2",
                "confidence": "high",
                "dimension": "Information",
                "title": f"Duplicate <title> found on {len(urls)} pages",
                "detail": (
                    f"The title \"{title_norm}\" appears on {len(urls)} pages: "
                    + ", ".join(urls[:5])
                    + (f" (and {len(urls) - 5} more)" if len(urls) > 5 else "")
                    + ". Search engines may de-rank or merge duplicate-title pages."
                ),
                "urls": urls,
                "type": "seo_duplicate_page_title",
                "automated": True,
            })

    return findings


# ── Helpers ───────────────────────────────────────────────────────────────────

def _path(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).path or "/"
    except Exception:
        return url


def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _url_slug(url: str) -> str:
    slug = re.sub(r"https?://[^/]+", "", url)
    slug = re.sub(r"[^a-zA-Z0-9]", "-", slug).strip("-")[:40]
    return slug or "root"


# ── Playwright extraction helper ──────────────────────────────────────────────

SEO_EXTRACTION_SCRIPT = """
() => {
  const metaDesc = document.querySelector('meta[name="description"]');
  const metaRobots = document.querySelector('meta[name="robots"]');
  const canonical = document.querySelector('link[rel="canonical"]');
  const imgs = Array.from(document.querySelectorAll('img'));
  return {
    url: location.href,
    title: document.title || '',
    meta_description: metaDesc ? (metaDesc.getAttribute('content') || '') : null,
    robots_meta: metaRobots ? (metaRobots.getAttribute('content') || '') : null,
    canonical_url: canonical ? canonical.getAttribute('href') : null,
    image_count: imgs.length,
    images_without_alt: imgs.filter(img => !img.getAttribute('alt')).length
  };
}
"""
