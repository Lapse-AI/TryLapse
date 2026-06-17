"""URL preflight and SSRF guardrails (CEO build order #1)."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from rehearse.errors import PreflightError, SSRFBlockedError

# Private / link-local / metadata ranges — block before fetch
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "169.254.169.254",
    }
)

# Dogfood / self-test only — opt in via run.allow_localhost in config or API flag
_LOCALHOST_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _is_localhost_host(host: str) -> bool:
    h = host.lower().strip("[]")
    return h in _LOCALHOST_HOSTS


def _is_blocked_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    for net in _BLOCKED_NETWORKS:
        if addr in net:
            return True
    return addr.is_private or addr.is_loopback or addr.is_link_local


def assert_url_allowed(url: str, *, allow_localhost: bool = False) -> urlparse:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(f"Only http/https allowed, got: {parsed.scheme!r}")
    if not parsed.hostname:
        raise PreflightError(f"Missing hostname in URL: {url}")
    host = parsed.hostname.lower().strip("[]")
    if allow_localhost and _is_localhost_host(host):
        return parsed
    if host in _BLOCKED_HOSTNAMES or host.endswith(".local"):
        raise SSRFBlockedError(f"Blocked hostname: {host}")

    # Literal IP in URL
    try:
        ip = ipaddress.ip_address(host)
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(f"Blocked IP: {host}")
    except ValueError:
        pass

    # Resolve and check all A/AAAA answers
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        raise PreflightError(f"Cannot resolve {host}: {e}") from e

    for info in infos:
        resolved = info[4][0]
        try:
            ip = ipaddress.ip_address(resolved)
        except ValueError:
            continue
        if allow_localhost and _is_localhost_host(resolved):
            continue
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(f"Hostname {host} resolves to blocked address {resolved}")

    return parsed


def _follow_redirect_safe(
    client: httpx.Client,
    url: str,
    *,
    method: str = "HEAD",
    allow_localhost: bool = False,
    max_hops: int = 5,
) -> httpx.Response:
    """Manually follow redirects, re-running SSRF checks on every hop destination."""
    current = url
    for _ in range(max_hops):
        req = client.build_request(method, current)
        resp = client.send(req, follow_redirects=False)
        if resp.is_redirect:
            location = resp.headers.get("location", "")
            if not location:
                break
            # Resolve relative redirects against the current URL
            next_url = str(httpx.URL(current).copy_with()).rstrip("/")
            try:
                next_url = str(httpx.URL(location)) if location.startswith(("http://", "https://")) else str(httpx.URL(current).copy_with(path=location))
            except Exception:
                next_url = location
            assert_url_allowed(next_url, allow_localhost=allow_localhost)
            current = next_url
            continue
        return resp
    # Last hop — return as-is
    return resp


def preflight_head(url: str, timeout: float = 15.0, *, allow_localhost: bool = False) -> dict:
    """HEAD/GET probe after SSRF checks. Re-validates every redirect hop."""
    assert_url_allowed(url, allow_localhost=allow_localhost)
    with httpx.Client(follow_redirects=False, timeout=timeout) as client:
        try:
            resp = _follow_redirect_safe(client, url, method="HEAD", allow_localhost=allow_localhost)
            if resp.status_code >= 400:
                resp = _follow_redirect_safe(client, url, method="GET", allow_localhost=allow_localhost)
        except (SSRFBlockedError, PreflightError):
            raise
        except httpx.HTTPError as e:
            raise PreflightError(f"HTTP probe failed for {url}: {e}") from e
        return {
            "url": str(resp.url),
            "status_code": resp.status_code,
            "ok": resp.status_code < 400,
        }
