"""Bounded, manually triggered HTML fetching with basic SSRF protection.

DNS is checked before every hop. Production also needs egress restrictions and
DNS pinning to close the validation-to-connection DNS rebinding window.
"""

import ipaddress
import logging
import socket
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import requests

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)
REDIRECT_CODES = {301, 302, 303, 307, 308}


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int | None = None
    reachable: bool = False
    content_type: str | None = None
    html: str = ""
    error: str | None = None
    error_kind: str | None = None


def validate_public_url(url: str) -> str:
    """Reject non-public destinations, including mixed public/private DNS."""
    if len(url) > 2048 or any(ord(char) < 33 for char in url) or "\\" in url:
        raise ValueError("Malformed source URL")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP and HTTPS URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials in source URLs are not allowed")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in {80, 443}:
        raise ValueError("Only standard web ports 80 and 443 are allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(
        (".localhost", ".local", ".internal", ".lan", ".home", ".test", ".invalid")
    ):
        raise ValueError("Internal or reserved hostnames are not allowed")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
        if "." not in hostname:
            raise ValueError("Single-label internal hostnames are not allowed")
    addresses = (
        [literal]
        if literal
        else [
            ipaddress.ip_address(info[4][0])
            for info in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        ]
    )
    if not addresses or any(
        not address.is_global
        or address.is_multicast
        or (
            isinstance(address, ipaddress.IPv6Address)
            and address.ipv4_mapped is not None
            and not address.ipv4_mapped.is_global
        )
        for address in addresses
    ):
        raise ValueError("Source must resolve exclusively to public unicast IP addresses")
    return url


def fetch_source(url: str, settings: Settings | None = None) -> FetchResult:
    """One request per hop, no retries, no crawling, no automatic redirects."""
    settings = settings or get_settings()
    result = FetchResult(url=url, final_url=url)
    deadline = time.monotonic() + settings.request_timeout
    try:
        with requests.Session() as client:
            # Ignore ambient proxy settings and .netrc credentials.
            client.trust_env = False
            client.headers.update(
                {
                    "User-Agent": "AleharResourceIntelligence/0.1 (manual public-source verification)",
                    "Accept": "text/html,application/xhtml+xml",
                }
            )
            current_url = url
            for hop in range(settings.max_redirects + 1):
                validate_public_url(current_url)
                result.final_url = current_url
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise requests.Timeout("Source request time budget exceeded")
                with client.get(
                    current_url, timeout=remaining, allow_redirects=False, stream=True
                ) as response:
                    result.status_code = response.status_code
                    result.content_type = response.headers.get("Content-Type", "").lower()
                    if response.status_code in REDIRECT_CODES:
                        if hop == settings.max_redirects:
                            raise ValueError("Source redirect limit exceeded")
                        location = response.headers.get("Location")
                        if not location:
                            raise ValueError("Source redirect has no Location header")
                        current_url = urljoin(current_url, location)
                        continue
                    if not 200 <= response.status_code < 300:
                        result.error = f"Source returned HTTP {response.status_code}"
                        result.error_kind = "http"
                        return result
                    result.reachable = True
                    media_type = result.content_type.split(";", 1)[0].strip()
                    if media_type not in {"text/html", "application/xhtml+xml"}:
                        result.error = "Source is reachable but is not supported HTML"
                        result.error_kind = "unsupported_content"
                        return result
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_content(chunk_size=16384):
                        if time.monotonic() > deadline:
                            raise requests.Timeout("Source read time budget exceeded")
                        size += len(chunk)
                        if size > settings.max_source_bytes:
                            result.error = "Source exceeds the configured download size limit"
                            result.error_kind = "content_limit"
                            return result
                        chunks.append(chunk)
                    encoding = response.encoding or "utf-8"
                    try:
                        result.html = b"".join(chunks).decode(encoding, errors="replace")
                    except LookupError:
                        result.html = b"".join(chunks).decode("utf-8", errors="replace")
                    logger.info("Source fetched: HTTP %s, %s bytes", result.status_code, size)
                    return result
    except requests.exceptions.SSLError:
        result.error = "Source TLS certificate validation failed"
        result.error_kind = "ssl"
    except requests.Timeout:
        result.error = "Source request timed out"
        result.error_kind = "timeout"
    except (requests.RequestException, socket.gaierror, OSError):
        result.error = "Could not connect to the public source"
        result.error_kind = "connection"
    except (ValueError, UnicodeError) as exc:
        result.error = str(exc)
        result.error_kind = "invalid_url"
    result.reachable = False
    result.html = ""
    logger.info("Source unavailable: %s", result.error_kind)
    return result
