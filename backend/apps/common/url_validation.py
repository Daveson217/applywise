"""URL validation utilities for preventing SSRF.

Any time we fetch a user-supplied URL server-side (Playwright cover-letter
fetcher, ATS detector, future webhooks), we MUST run it through
`validate_external_url()` first. Otherwise an attacker can:

  - Read cloud metadata: http://169.254.169.254/latest/meta-data/
  - Hit internal admin APIs: http://localhost:8000/admin/
  - Probe internal services: http://10.0.0.1:6379/
  - Exfiltrate files: file:///etc/passwd, gopher://, dict://
  - Map internal network via timing / error responses
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}

# IPv4 ranges that must NEVER be reachable from user-supplied URLs.
# Includes loopback, link-local (AWS/GCP/Azure metadata), private RFC1918,
# carrier-grade NAT, multicast, broadcast, reserved.
_FORBIDDEN_IPV4_NETS = [
    ipaddress.IPv4Network("0.0.0.0/8"),       # "this host"
    ipaddress.IPv4Network("10.0.0.0/8"),      # Private
    ipaddress.IPv4Network("100.64.0.0/10"),   # Carrier-grade NAT
    ipaddress.IPv4Network("127.0.0.0/8"),     # Loopback
    ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local (AWS/GCP metadata!)
    ipaddress.IPv4Network("172.16.0.0/12"),   # Private
    ipaddress.IPv4Network("192.0.0.0/24"),    # IETF protocol assignments
    ipaddress.IPv4Network("192.0.2.0/24"),    # TEST-NET
    ipaddress.IPv4Network("192.168.0.0/16"),  # Private
    ipaddress.IPv4Network("198.18.0.0/15"),   # Benchmarking
    ipaddress.IPv4Network("198.51.100.0/24"),
    ipaddress.IPv4Network("203.0.113.0/24"),
    ipaddress.IPv4Network("224.0.0.0/4"),     # Multicast
    ipaddress.IPv4Network("240.0.0.0/4"),     # Reserved
    ipaddress.IPv4Network("255.255.255.255/32"),
]

_FORBIDDEN_IPV6_NETS = [
    ipaddress.IPv6Network("::1/128"),         # loopback
    ipaddress.IPv6Network("fc00::/7"),        # unique local
    ipaddress.IPv6Network("fe80::/10"),       # link-local
    ipaddress.IPv6Network("ff00::/8"),        # multicast
    # IPv4-mapped IPv6 — block them too (otherwise attacker uses ::ffff:127.0.0.1)
    ipaddress.IPv6Network("::ffff:0:0/96"),
]

# Hostnames that must always be rejected even before DNS resolution.
_FORBIDDEN_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
    "metadata.azure.com",
    "ip-ranges.amazonaws.com",  # not metadata but suspicious in context
}


class URLValidationError(ValueError):
    """Raised when a user-supplied URL fails SSRF checks."""


def _ip_is_forbidden(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv4Address):
        return any(ip in net for net in _FORBIDDEN_IPV4_NETS)
    return any(ip in net for net in _FORBIDDEN_IPV6_NETS)


def validate_external_url(url: str, *, max_length: int = 2048) -> str:
    """Validate that `url` is a safe external HTTP(S) URL.

    Returns the normalized URL. Raises URLValidationError on any failure.

    DNS is resolved here; the caller should use the SAME hostname when fetching.
    To prevent DNS-rebinding (TTL=0 trick where DNS returns 1.2.3.4 then
    127.0.0.1 on the next lookup), callers should resolve once and connect
    by IP — but most callers won't, so we at least validate the resolved IPs
    are public at validation time, which catches naive SSRF.
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL is required")
    if len(url) > max_length:
        raise URLValidationError(f"URL exceeds {max_length} chars")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise URLValidationError(
            f"Scheme '{parsed.scheme}' not allowed (must be http or https)"
        )

    host = (parsed.hostname or "").lower().strip()
    if not host:
        raise URLValidationError("URL has no host")
    if host in _FORBIDDEN_HOSTS:
        raise URLValidationError(f"Host '{host}' is forbidden")

    # If host is a literal IP, validate directly
    try:
        ip = ipaddress.ip_address(host)
        if _ip_is_forbidden(ip):
            raise URLValidationError(
                f"IP {host} is in a private/reserved range"
            )
        return url
    except ValueError:
        pass  # not a literal IP, fall through to DNS resolution

    # Resolve hostname and check each returned IP
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise URLValidationError(f"DNS lookup failed: {e}") from e

    if not infos:
        raise URLValidationError("DNS returned no addresses")

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _ip_is_forbidden(ip):
            raise URLValidationError(
                f"Host '{host}' resolves to private/reserved IP {addr}"
            )

    return url
