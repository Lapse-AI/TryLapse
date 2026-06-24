"""Product intelligence — pageCount must reflect the deep crawl that just ran,
not just the sitemap (which is empty on a workspace's first-ever analysis,
since there's no prior rehearsal run to pull a sitemap from yet).

Found via a real incident: a brand-new workspace's analysis successfully
logged in and visited 8 pages (interaction_map["pageCount"] == 8), but the
saved product model reported pageCount: 0 because that field only ever
counted sitemap_pages, which was empty. Made a real, successful crawl look
broken.
"""

from __future__ import annotations

from unittest.mock import patch

from rehearse.product_intelligence import analyze_product


def test_page_count_falls_back_to_interaction_map_when_sitemap_empty():
    """The exact incident: no sitemap yet, but the deep crawl visited 8 pages."""
    with patch("rehearse.product_intelligence._call_llm", return_value=None):
        model = analyze_product(
            "https://faculty-dashboard-eight.vercel.app",
            product_name="Argyle Trainer Dashboard",
            sitemap_pages=[],
            interaction_map={"pageCount": 8, "pagesVisited": list(range(8))},
        )
    assert model["pageCount"] == 8


def test_page_count_uses_sitemap_when_larger():
    """Once a real rehearsal run exists, its sitemap can be richer than
    whatever a single onboarding-time deep crawl saw — use the larger count."""
    with patch("rehearse.product_intelligence._call_llm", return_value=None):
        model = analyze_product(
            "https://example.com",
            sitemap_pages=[{"path": f"/p{i}"} for i in range(20)],
            interaction_map={"pageCount": 8},
        )
    assert model["pageCount"] == 20


def test_page_count_zero_when_both_empty():
    with patch("rehearse.product_intelligence._call_llm", return_value=None):
        model = analyze_product("https://example.com", sitemap_pages=[], interaction_map={})
    assert model["pageCount"] == 0


def test_page_count_handles_missing_interaction_map():
    with patch("rehearse.product_intelligence._call_llm", return_value=None):
        model = analyze_product("https://example.com", sitemap_pages=[{"path": "/"}])
    assert model["pageCount"] == 1
