from unittest.mock import Mock

import pytest
import requests

from app.core.config import Settings
from app.services import source_fetcher
from app.services.source_fetcher import fetch_source, validate_public_url


@pytest.fixture
def public_dns(monkeypatch):
    resolver = Mock(return_value=[(2, 1, 6, "", ("93.184.216.34", 443))])
    monkeypatch.setattr(source_fetcher.socket, "getaddrinfo", resolver)
    return resolver


def response(status=200, body=b"<html>Public source</html>", headers=None):
    item = Mock()
    item.status_code = status
    item.headers = headers if headers is not None else {"Content-Type": "text/html; charset=utf-8"}
    item.encoding = "utf-8"
    item.iter_content.return_value = [body]
    item.__enter__ = Mock(return_value=item)
    item.__exit__ = Mock(return_value=False)
    return item


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "http://localhost/",
        "http://127.0.0.1/",
        "http://0.0.0.0/",
        "http://10.0.0.1/",
        "http://172.16.0.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/",
        "http://[::1]/",
        "http://[fd00::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://224.0.0.1/",
        "http://100.64.0.1/",
        "http://printer/",
        "http://host.internal/",
        "https://user:pass@example.com/",
        "https://example.com:8080/",
        "http://example.com/\n",
        "http://example.com\\@localhost/",
    ],
)
def test_rejects_unsafe_urls(url):
    with pytest.raises(ValueError):
        validate_public_url(url)


def test_mixed_dns_is_rejected(public_dns):
    public_dns.return_value.append((2, 1, 6, "", ("192.168.1.1", 443)))
    with pytest.raises(ValueError, match="public"):
        validate_public_url("https://source.example/")


def test_public_source_single_request(monkeypatch, public_dns):
    request = Mock(return_value=response())
    monkeypatch.setattr(requests.Session, "get", request)
    result = fetch_source("https://source.example/")
    assert result.reachable and result.status_code == 200
    assert result.html == "<html>Public source</html>"
    assert request.call_count == 1
    assert request.call_args.kwargs["allow_redirects"] is False


def test_redirect_to_internal_is_not_fetched(monkeypatch, public_dns):
    request = Mock(return_value=response(302, headers={"Location": "http://127.0.0.1/"}))
    monkeypatch.setattr(requests.Session, "get", request)
    result = fetch_source("https://source.example/")
    assert not result.reachable
    assert result.error_kind == "invalid_url"
    assert request.call_count == 1


def test_public_redirect_is_followed_and_revalidated(monkeypatch, public_dns):
    request = Mock(side_effect=[response(301, headers={"Location": "/about"}), response()])
    monkeypatch.setattr(requests.Session, "get", request)
    result = fetch_source("https://source.example/")
    assert result.reachable
    assert result.final_url == "https://source.example/about"
    assert public_dns.call_count == 2


@pytest.mark.parametrize(
    "exception,kind",
    [
        (requests.Timeout(), "timeout"),
        (requests.ConnectionError(), "connection"),
        (requests.exceptions.SSLError(), "ssl"),
    ],
)
def test_transport_failures(monkeypatch, public_dns, exception, kind):
    request = Mock(side_effect=exception)
    monkeypatch.setattr(requests.Session, "get", request)
    result = fetch_source("https://source.example/")
    assert not result.reachable and result.error_kind == kind
    assert request.call_count == 1


def test_http_error(monkeypatch, public_dns):
    monkeypatch.setattr(requests.Session, "get", Mock(return_value=response(503)))
    result = fetch_source("https://source.example/")
    assert not result.reachable and result.status_code == 503


def test_pdf_is_not_treated_as_html(monkeypatch, public_dns):
    monkeypatch.setattr(
        requests.Session,
        "get",
        Mock(return_value=response(headers={"Content-Type": "application/pdf"})),
    )
    result = fetch_source("https://source.example/")
    assert result.reachable and result.error_kind == "unsupported_content"
    assert not result.html


def test_download_limit(monkeypatch, public_dns):
    monkeypatch.setattr(requests.Session, "get", Mock(return_value=response(body=b"x" * 2048)))
    result = fetch_source("https://source.example/", Settings(max_source_bytes=1024))
    assert result.error_kind == "content_limit" and not result.html


def test_redirect_limit(monkeypatch, public_dns):
    request = Mock(return_value=response(302, headers={"Location": "/loop"}))
    monkeypatch.setattr(requests.Session, "get", request)
    result = fetch_source("https://source.example/", Settings(max_redirects=1))
    assert not result.reachable
    assert "redirect limit" in result.error
    assert request.call_count == 2
