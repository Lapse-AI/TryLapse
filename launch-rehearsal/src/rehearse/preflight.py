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


def _is_blocked_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    for net in _BLOCKED_NETWORKS:
        if addr in net:
            return True
    return addr.is_private or addr.is_loopback or addr.is_link_local


def assert_url_allowed(url: str) -> urlparse:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(f"Only http/https allowed, got: {parsed.scheme!r}")
    if not parsed.hostname:
        raise PreflightError(f"Missing hostname in URL: {url}")
    host = parsed.hostname.lower()
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
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(f"Hostname {host} resolves to blocked address {resolved}")

    return parsed


def preflight_head(url: str, timeout: float = 15.0) -> dict:
    """HEAD/GET probe after SSRF checks. Returns status metadata."""
    assert_url_allowed(url)
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        try:
            resp = client.head(url)
            if resp.status_code >= 400:
                resp = client.get(url)
        except httpx.HTTPError as e:
            raise PreflightError(f"HTTP probe failed for {url}: {e}") from e
        return {
            "url": str(resp.url),
            "status_code": resp.status_code,
            "ok": resp.status_code < 400,
        }
