"""Passive security surface scan — no navigation required, runs once after crawl."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlparse

if TYPE_CHECKING:
    from rehearse.dsl import RunConfig
    from rehearse.heuristics import Finding


def scan_security_surface(page: Any, config: "RunConfig") -> "list[Finding]":
    """Check the current page state for common security issues without navigating."""
    from rehearse.heuristics import Finding

    findings: list[Finding] = []
    fid = 0

    def add(severity: str, title: str, detail: str) -> None:
        nonlocal fid
        fid += 1
        p_admin = [
            p.id for p in config.personas
            if any(kw in p.role.lower() for kw in ("admin", "security", "it", "buyer"))
        ]
        personas = p_admin or [config.personas[0].id]
        findings.append(Finding(
            id=f"SEC{fid}",
            severity=severity,
            title=title,
            detail=detail,
            persona_ids=personas,
            step_id="security-scan",
            confidence="high",
        ))

    _check_exposed_globals(page, add)
    _check_csp(page, add)
    _check_mixed_content(page, config.target_url, add)
    _check_cookies(page, config.target_url, add)
    return findings


def _check_exposed_globals(page: Any, add: Callable[..., None]) -> None:
    try:
        exposed = page.evaluate("""() => {
            const hits = [];
            const sensitivePattern = /secret|password|passwd|api[_\\-]?key|token|private|credential|auth[_\\-]?secret/i;
            const globals = ['__ENV__', 'ENV', '__APP_CONFIG__', '__CONFIG__', '__APP__'];
            for (const g of globals) {
                try {
                    const val = window[g];
                    if (val && typeof val === 'object') {
                        const dangerous = Object.keys(val).filter(k => sensitivePattern.test(k));
                        if (dangerous.length) hits.push('window.' + g + ' exposes: ' + dangerous.slice(0, 4).join(', '));
                    }
                } catch (_) {}
            }
            // __NEXT_DATA__ often serialises server-side props
            try {
                if (window.__NEXT_DATA__) {
                    const nd = JSON.stringify(window.__NEXT_DATA__);
                    if (sensitivePattern.test(nd)) hits.push('__NEXT_DATA__ contains sensitive-sounding keys');
                }
            } catch (_) {}
            return hits;
        }""")
        if exposed:
            add(
                "P1",
                "Sensitive config exposed in window globals",
                f"{len(exposed)} potential exposure(s): {'; '.join(exposed[:3])}. "
                "These values are readable by any third-party script on the page.",
            )
    except Exception:
        pass


def _check_csp(page: Any, add: Callable[..., None]) -> None:
    try:
        url = page.url
        if not url.startswith("https://"):
            return
        has_csp = page.evaluate("""() => {
            return !!document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        }""")
        if not has_csp:
            add(
                "P2",
                "No Content-Security-Policy detected",
                "No CSP meta tag found on this HTTPS page. Without a CSP, reflected XSS attacks can "
                "inject and execute arbitrary scripts. Add a Content-Security-Policy response header.",
            )
    except Exception:
        pass


def _check_mixed_content(page: Any, target_url: str, add: Callable[..., None]) -> None:
    try:
        if not target_url.startswith("https://"):
            return
        mixed = page.evaluate("""() => {
            const http = [];
            document.querySelectorAll('script[src], link[href], img[src]').forEach(el => {
                const u = el.src || el.href || '';
                if (typeof u === 'string' && u.startsWith('http://')) http.push(u.slice(0, 120));
            });
            return http.slice(0, 5);
        }""")
        if mixed:
            add(
                "P1",
                "Mixed content on HTTPS page",
                f"{len(mixed)} HTTP resource(s) loaded on an HTTPS page: {', '.join(mixed[:3])}. "
                "Browsers block or warn users, and the resource can be intercepted.",
            )
    except Exception:
        pass


def _check_cookies(page: Any, target_url: str, add: Callable[..., None]) -> None:
    try:
        context = page.context
        cookies = context.cookies()
    except Exception:
        return

    is_https = target_url.startswith("https://")
    domain = urlparse(target_url).hostname or ""

    relevant = [c for c in cookies if domain and domain in (c.get("domain") or "")]
    if not relevant:
        relevant = cookies[:30]

    def _auth_like(name: str) -> bool:
        return any(kw in name.lower() for kw in ("session", "auth", "token", "csrf", "sid", "jwt", "login"))

    auth_no_httponly = [c["name"] for c in relevant if _auth_like(c["name"]) and not c.get("httpOnly")]
    auth_no_secure = [c["name"] for c in relevant if _auth_like(c["name"]) and is_https and not c.get("secure")]

    if auth_no_httponly:
        add(
            "P1",
            "Session cookies missing HttpOnly flag",
            f"Cookie(s) {', '.join(repr(n) for n in auth_no_httponly[:5])} lack HttpOnly. "
            "JavaScript on the page can read these, enabling XSS-based session hijack.",
        )

    if auth_no_secure and is_https:
        add(
            "P1",
            "Session cookies missing Secure flag",
            f"Cookie(s) {', '.join(repr(n) for n in auth_no_secure[:5])} lack the Secure flag on "
            "an HTTPS site. They may be sent over plain HTTP, enabling interception.",
        )
