"""URL route template normalization and deduplication.

Provides a single canonical implementation of URL-to-template mapping used by
both crawler.py and deep_crawler.py, plus a RouteTemplateGraph that merges
semantically similar templates (e.g. /api/v1/users/{id} ≈ /api/v2/users/{id}).

Two templates are considered equivalent if their Jaccard similarity on path
tokens (excluding {id} placeholders) exceeds TEMPLATE_MERGE_THRESHOLD.  This
is deliberately simpler than full TF-IDF: URL segments are 1–5 tokens each and
IDF on a handful of paths produces noisy weights.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse

# --- thresholds -----------------------------------------------------------

TEMPLATE_MERGE_THRESHOLD = 0.85   # Jaccard similarity to merge two templates
MAX_SAMPLES_PER_TEMPLATE = 2      # default cap: visit at most 2 pages per template

# --- regexes for segment classification ----------------------------------

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)
_NUMERIC_RE = re.compile(r'^\d+$')
_HASH_RE = re.compile(r'^[0-9a-f]{16,}$', re.I)
_SEMVER_RE = re.compile(r'^v\d+(\.\d+)*$', re.I)   # v1, v2, v1.0 → {version}
_ID_SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{7,}$', re.I)


def _classify_segment(part: str) -> str:
    """Return a canonical placeholder or the original segment."""
    if _UUID_RE.match(part) or _NUMERIC_RE.match(part) or _HASH_RE.match(part):
        return "{id}"
    if _SEMVER_RE.match(part):
        return "{version}"
    if _ID_SLUG_RE.match(part) and (re.search(r'\d', part) or len(part) > 20):
        return "{id}"
    return part.lower()


def url_to_template(url: str) -> str:
    """Normalize a full URL to a structural template string.

    Examples
    --------
    /profiles/12345           → /profiles/{id}
    /api/v2/products/abc-001  → /api/{version}/products/{id}
    /admin/settings            → /admin/settings
    """
    try:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        normed = [_classify_segment(p) for p in parts]
        template_path = "/" + "/".join(normed) if normed else "/"
        return urlunparse(("", "", template_path, "", "", ""))
    except Exception:
        return url


def path_to_template(path: str) -> str:
    """Normalize a bare path (no scheme/host) to a structural template."""
    try:
        parts = [p for p in path.split("/") if p]
        normed = [_classify_segment(p) for p in parts]
        return "/" + "/".join(normed) if normed else "/"
    except Exception:
        return path


def _template_tokens(template: str) -> frozenset[str]:
    """Token bag: path segments excluding {id}/{version} placeholders."""
    return frozenset(
        p for p in template.replace("{id}", "").replace("{version}", "").split("/")
        if p
    )


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


class RouteTemplateGraph:
    """Track visited URL templates with semantic dedup and sample capping.

    Usage
    -----
    g = RouteTemplateGraph()
    for url in crawl_queue:
        canonical, should_skip = g.record(url)
        if should_skip:
            continue
        # visit url ...

    After the crawl:
        g.templates    → {template: visit_count}
        g.skipped      → {template: skip_count}
        g.canonical_of → {raw_template: canonical_template}
    """

    def __init__(self, max_samples: int = MAX_SAMPLES_PER_TEMPLATE) -> None:
        self.max_samples = max_samples
        self.templates: dict[str, int] = {}      # canonical template → visit count
        self.skipped: dict[str, int] = {}        # canonical template → skip count
        self.canonical_of: dict[str, str] = {}  # raw template → resolved canonical
        self._token_cache: dict[str, frozenset[str]] = {}

    def _tokens(self, template: str) -> frozenset[str]:
        if template not in self._token_cache:
            self._token_cache[template] = _template_tokens(template)
        return self._token_cache[template]

    def _resolve_canonical(self, raw: str) -> str:
        """Find an existing canonical template that is semantically equivalent.

        Returns raw itself if no match exists, creating a new canonical entry.
        """
        if raw in self.canonical_of:
            return self.canonical_of[raw]

        raw_tokens = self._tokens(raw)
        best_score = 0.0
        best_canonical: str | None = None

        for existing in self.templates:
            score = _jaccard(raw_tokens, self._tokens(existing))
            if score >= TEMPLATE_MERGE_THRESHOLD and score > best_score:
                best_score = score
                best_canonical = existing

        canonical = best_canonical if best_canonical is not None else raw
        self.canonical_of[raw] = canonical
        return canonical

    def record(self, url: str, *, root_template: str = "/") -> tuple[str, bool]:
        """Record a URL and decide whether it should be skipped.

        Parameters
        ----------
        url:
            Full URL (including scheme+host) or a bare path.
        root_template:
            Template string that should never be capped (default "/").

        Returns
        -------
        (canonical_template, should_skip)
            canonical_template — the resolved template for this URL
            should_skip       — True if the sample cap has been reached
        """
        raw = url_to_template(url)
        canonical = self._resolve_canonical(raw)

        current = self.templates.get(canonical, 0)
        if current >= self.max_samples and canonical not in (root_template, "/", "/{id}"):
            self.skipped[canonical] = self.skipped.get(canonical, 0) + 1
            return canonical, True

        self.templates[canonical] = current + 1
        return canonical, False

    def coverage_pct(self) -> float:
        """Fraction of discovered templates that were actually visited."""
        total = len(self.templates) + len(self.skipped)
        return round(len(self.templates) / total * 100, 1) if total else 0.0

    def summary(self) -> dict[str, object]:
        return {
            "urlPatterns": self.templates,
            "skippedPatterns": self.skipped,
            "skippedPatternCount": sum(self.skipped.values()),
            "graphCoveragePct": self.coverage_pct(),
        }
