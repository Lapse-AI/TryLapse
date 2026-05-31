"""Crawler error detection and path excludes."""

from rehearse.crawler import CrawlPage, _path_excluded, page_has_crawl_error


def test_page_error_requires_http_or_heading_not_body_noise():
    ok = CrawlPage(
        url="http://127.0.0.1:8081/trends",
        path="/trends",
        title="Trends — Launch Rehearsal",
        depth=1,
        status=200,
        h1="Trends & monitoring",
        error_phrases=[],
    )
    assert not page_has_crawl_error(ok)

    noisy = CrawlPage(
        url="http://127.0.0.1:8081/runs/foo",
        path="/runs/foo",
        title="Run detail",
        depth=2,
        status=200,
        h1="Run detail",
        error_phrases=["error"],
    )
    assert not page_has_crawl_error(noisy)

    http_err = CrawlPage(
        url="http://example.com/missing",
        path="/missing",
        title="",
        depth=1,
        status=404,
        error_phrases=["http_404"],
    )
    assert page_has_crawl_error(http_err)


def test_path_excluded_prefixes():
    assert _path_excluded("/runs/abc", ["/runs/"])
    assert _path_excluded("/api/sitemap/x", ["/api/"])
    assert not _path_excluded("/compare", ["/runs/", "/api/"])
