"""Tests for the anonymous HiringCafe HTTP and SSR client."""

import io
import json

import pytest

from hiringcafe_cli.http_client import HireCafeHTTPError, HireCafeTransportError, WebClient, parse_ssr_page


def _search_response(properties: dict) -> io.BytesIO:
    raise NotImplementedError


def test_web_client_parses_and_validates_ssr_page(monkeypatch):
    """Condition: valid HTML contains all required SSR properties. Expected: pageProps is returned."""
    properties = {
        "ssrHits": [],
        "ssrPage": 1,
        "ssrTotalCount": 0,
        "ssrPageSize": 40,
        "ssrIsLastPage": True,
    }
    payload = {"props": {"pageProps": properties}}
    html = f'<script id="__NEXT_DATA__">{json.dumps(payload)}</script>'
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout))
        return io.BytesIO(html.encode())

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(fake_urlopen))
    client = WebClient(base_url="https://example.test", timeout=7)

    result = client.search_page({"searchQuery": "python"}, 1)

    assert result == properties
    assert len(calls) == 1
    assert calls[0][0].startswith("https://example.test/?searchState=")
    assert "%7B%22searchQuery%22%3A+%22python%22%7D" in calls[0][0]
    assert calls[0][0].endswith("&page=1")
    assert calls[0][1] == 7


def test_web_client_rejects_missing_next_data(monkeypatch):
    """Condition: HTML lacks __NEXT_DATA__. Expected: parse error, not an empty success."""
    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda request, timeout: io.BytesIO(b"<html></html>")))
    client = WebClient(base_url="https://example.test")

    with pytest.raises(ValueError, match="__NEXT_DATA__"):
        client.search_page({}, 0)


def test_web_client_rejects_oversized_response(monkeypatch):
    """Condition: an anonymous GET response exceeds the read limit.

    Expected: parsing fails with a bounded-response error rather than reading without a limit.
    """

    class OversizedResponse(io.BytesIO):
        def read(self, size=-1):
            if size < 0:
                raise AssertionError("response must be read with a bounded size")
            return b"x" * size

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda request, timeout: OversizedResponse()))
    client = WebClient(base_url="https://example.test")

    with pytest.raises(ValueError, match="search response exceeds"):
        client.search_page({}, 0)


def test_web_client_rejects_non_https_configured_base_url(monkeypatch):
    """Condition: the configured base URL uses a non-HTTPS or credential-bearing form.

    Expected: configuration fails before a request can leak authority material or send a token to that URL.
    """
    monkeypatch.setenv("HIRINGCAFE_BASE_URL", "http://example.test")
    with pytest.raises(ValueError, match="HIRINGCAFE_BASE_URL must use HTTPS"):
        WebClient()
    monkeypatch.setenv("HIRINGCAFE_BASE_URL", "https://user:secret@example.test")
    with pytest.raises(ValueError, match="HIRINGCAFE_BASE_URL must use HTTPS"):
        WebClient()


def test_web_client_rejects_missing_required_page_property(monkeypatch):
    """Condition: payload omits ssrPage. Expected: parse error identifies the field."""
    payload = {"props": {"pageProps": {"ssrHits": [], "ssrTotalCount": 0, "ssrIsLastPage": True}}}
    html = f'<script id="__NEXT_DATA__">{json.dumps(payload)}</script>'
    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda request, timeout: io.BytesIO(html.encode())))

    with pytest.raises(ValueError, match="ssrPage"):
        parse_ssr_page(html)


def test_web_client_distinguishes_http_and_transport_failures(monkeypatch):
    """Condition: request raises wrapped HTTP and transport errors. Expected: typed errors carry endpoint/status."""
    client = WebClient(base_url="https://example.test")

    def http_error(request, timeout):
        raise HireCafeHTTPError("search", 429)

    def transport_error(request, timeout):
        raise HireCafeTransportError("search", TimeoutError("timed out"))

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(http_error))
    with pytest.raises(HireCafeHTTPError) as search_error:
        client.search_page({}, 0)
    assert search_error.value.endpoint == "search"
    assert search_error.value.status == 429

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(transport_error))
    with pytest.raises(HireCafeTransportError) as transport:
        client.search_page({}, 0)
    assert transport.value.endpoint == "search"
