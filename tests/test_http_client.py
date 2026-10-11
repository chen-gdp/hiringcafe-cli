"""Tests for the bounded HiringCafe HTTP and MCP client."""

import io
import json
from urllib.error import HTTPError, URLError

import pytest

from hiringcafe_cli.http_client import HireCafeHTTPError, HireCafeTransportError, WebClient


def _mcp_response(result):
    return io.BytesIO(json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode())


def test_web_client_calls_documented_tool_over_json_rpc(monkeypatch):
    """Condition: valid tool response. Expected: bounded POST with the verified JSON-RPC contract."""
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return _mcp_response({"content": [{"type": "text", "text": "first"}, {"type": "text", "text": "second"}]})

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(fake_urlopen))
    client = WebClient(base_url="https://example.test", timeout=7)

    result = client.call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})

    request, timeout = calls[0]
    assert result == "first\nsecond"
    assert len(calls) == 1
    assert timeout == 7
    assert request.full_url == "https://example.test/api/mcp"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json"
    assert request.get_header("Accept") == "application/json, text/event-stream"
    assert request.get_header("User-agent") == "hiringcafe-cli"
    assert json.loads(request.data) == {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "search_jobs", "arguments": {"search": "python developer", "limit": 10}},
    }


def test_web_client_rejects_unsupported_tool_before_network(monkeypatch):
    """Condition: caller names an unverified MCP tool. Expected: no HTTP request is made."""
    monkeypatch.setattr(
        WebClient,
        "urlopen",
        staticmethod(lambda *_: (_ for _ in ()).throw(AssertionError("unsupported tool must not make a request"))),
    )

    with pytest.raises(ValueError, match="unsupported HiringCafe MCP tool"):
        WebClient().call_mcp_tool("write_saved_job", {})


@pytest.mark.parametrize(
    "result",
    [
        {"isError": True, "content": [{"type": "text", "text": "private error content"}]},
        {"content": [{"type": "image", "data": "opaque"}]},
        {"content": [{"type": "text"}]},
    ],
)
def test_web_client_rejects_mcp_errors_and_nontext_results(monkeypatch, result):
    """Condition: tool returns an error or unsupported content. Expected: no response text is exposed."""
    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda *_, **__: _mcp_response(result)))

    with pytest.raises(ValueError):
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})


def test_web_client_rejects_mismatched_json_rpc_id(monkeypatch):
    """Condition: JSON-RPC response has a different request ID. Expected: response fails validation."""
    body = json.dumps({"jsonrpc": "2.0", "id": 9, "result": {"content": [{"type": "text", "text": "ok"}]}})
    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda *_, **__: io.BytesIO(body.encode())))

    with pytest.raises(ValueError, match="invalid HiringCafe MCP response"):
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})


@pytest.mark.parametrize("response_id", [True, 1.0])
def test_web_client_rejects_noninteger_json_rpc_id(monkeypatch, response_id):
    """Condition: JSON-RPC ID is a boolean or float. Expected: response fails exact ID validation."""
    body = json.dumps({"jsonrpc": "2.0", "id": response_id, "result": {"content": [{"type": "text", "text": "ok"}]}})
    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda *_, **__: io.BytesIO(body.encode())))

    with pytest.raises(ValueError, match="invalid HiringCafe MCP response"):
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})


def test_web_client_rejects_oversized_mcp_response(monkeypatch):
    """Condition: MCP response exceeds the read limit. Expected: no unbounded body read."""

    class OversizedResponse(io.BytesIO):
        def read(self, size=-1):
            if size < 0:
                raise AssertionError("response must be read with a bound")
            return b"x" * size

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(lambda *_, **__: OversizedResponse()))
    with pytest.raises(ValueError, match="mcp response exceeds"):
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})


def test_web_client_rejects_non_https_configured_base_url(monkeypatch):
    """Condition: base URL is insecure or credential-bearing. Expected: configuration fails before HTTP."""
    monkeypatch.setenv("HIRINGCAFE_BASE_URL", "http://example.test")
    with pytest.raises(ValueError, match="HIRINGCAFE_BASE_URL must use HTTPS"):
        WebClient()
    monkeypatch.setenv("HIRINGCAFE_BASE_URL", "https://user:secret@example.test")
    with pytest.raises(ValueError, match="HIRINGCAFE_BASE_URL must use HTTPS"):
        WebClient()


def test_web_client_surfaces_rate_limit_without_retry(monkeypatch):
    """Condition: the official MCP endpoint rate-limits a call. Expected: one request and HTTP 429."""
    calls = []

    def rate_limited(request, timeout):
        calls.append(request)
        raise HTTPError(request.full_url, 429, "Too Many Requests", hdrs=None, fp=None)

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(rate_limited))
    with pytest.raises(HireCafeHTTPError) as error:
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})
    assert error.value.endpoint == "mcp"
    assert error.value.status == 429
    assert len(calls) == 1


def test_web_client_wraps_transport_failure(monkeypatch):
    """Condition: HTTP transport fails. Expected: typed error contains no request payload."""
    monkeypatch.setattr(
        WebClient,
        "urlopen",
        staticmethod(lambda *_, **__: (_ for _ in ()).throw(URLError("offline"))),
    )
    with pytest.raises(HireCafeTransportError) as error:
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})
    assert error.value.endpoint == "mcp"
