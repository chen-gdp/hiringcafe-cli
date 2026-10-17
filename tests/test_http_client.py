"""Tests for the bounded HiringCafe HTTP and MCP client."""

import io
import json
import socket
import ssl
from threading import Event, Thread
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest

from hiringcafe_cli.http_client import HireCafeHTTPError, HireCafeTransportError, WebClient


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    """Keep public-read time and jitter deterministic without sleeping or patching the global clock."""
    state = SimpleNamespace(now=100.0, sleeps=[])

    def sleep(seconds):
        state.sleeps.append(seconds)
        state.now += seconds

    monkeypatch.setattr("hiringcafe_cli.http_client.time", SimpleNamespace(monotonic=lambda: state.now, sleep=sleep))
    monkeypatch.setattr("hiringcafe_cli.http_client.random.uniform", lambda start, end: end)
    return state


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
def test_web_client_rejects_mcp_errors_and_nontext_results(monkeypatch, clock, result):
    """Condition: tool returns an error or unsupported content. Expected: no response text is exposed."""
    calls = []

    def invalid_response(request, timeout):
        calls.append(request)
        return _mcp_response(result)

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(invalid_response))

    with pytest.raises(ValueError) as error:
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})
    assert len(calls) == 1
    assert clock.sleeps == []
    assert "private error content" not in str(error.value)


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


@pytest.mark.parametrize("status", [400, 403, 404, 429])
def test_web_client_surfaces_nonretryable_http_without_retry(monkeypatch, clock, status):
    """Condition: MCP returns a permanent error or rate limit. Expected: one request and no backoff."""
    calls = []

    def rate_limited(request, timeout):
        calls.append(request)
        raise HTTPError(request.full_url, status, "private response reason", hdrs=None, fp=None)

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(rate_limited))
    with pytest.raises(HireCafeHTTPError) as error:
        WebClient().call_mcp_tool("search_jobs", {"search": "python developer", "limit": 10})
    assert error.value.endpoint == "mcp"
    assert error.value.status == status
    assert str(error.value) == f"mcp returned HTTP {status}"
    assert len(calls) == 1
    assert clock.sleeps == []


def test_web_client_wraps_opaque_transport_failure_once(monkeypatch, clock):
    """Condition: transport returns arbitrary error text. Expected: safe generic diagnostic without retry."""
    calls = []

    def failed(request, timeout):
        calls.append(request)
        raise URLError("https://example.test/?private=query\nAuthorization: synthetic-secret")

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(failed))
    with pytest.raises(HireCafeTransportError) as error:
        WebClient().call_mcp_tool("search_jobs", {"search": "private query", "limit": 10})
    assert error.value.endpoint == "mcp"
    assert "connection failed" in str(error.value)
    assert "actual execution environment" in str(error.value)
    assert "https://" not in str(error.value)
    assert "private" not in str(error.value)
    assert "synthetic-secret" not in str(error.value)
    assert len(calls) == 1
    assert clock.sleeps == []


@pytest.mark.parametrize("tool", ["search_jobs", "get_job_details"])
def test_web_client_recovers_from_temporary_dns_failure(monkeypatch, clock, tool):
    """Condition: verified public tool has a temporary DNS failure. Expected: identical read retries and succeeds."""
    calls = []

    def dns_then_success(request, timeout):
        calls.append((request, timeout))
        if len(calls) == 1:
            raise URLError(socket.gaierror(socket.EAI_AGAIN, "private DNS details"))
        return _mcp_response({"content": [{"type": "text", "text": "recovered"}]})

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(dns_then_success))
    client = WebClient()

    assert client.call_mcp_tool(tool, {}) == "recovered"
    assert calls[0][0] is calls[1][0]
    assert [timeout for _, timeout in calls] == [30, 29.5]
    assert clock.sleeps == [0.5]


def test_web_client_exhausts_temporary_dns_retries_with_safe_diagnostic(monkeypatch, clock):
    """Condition: DNS fails persistently. Expected: three attempts, bounded jitter, and a sanitized DNS diagnostic."""
    calls = []

    def dns_failure(request, timeout):
        calls.append(request)
        raise URLError(socket.gaierror(socket.EAI_AGAIN, "https://example.test/?private=synthetic-secret"))

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(dns_failure))

    with pytest.raises(HireCafeTransportError) as error:
        WebClient().call_mcp_tool("search_jobs", {"search": "private query"})

    assert str(error.value) == (
        "mcp transport failed: DNS resolution failed. Check the same command in the actual execution environment."
    )
    assert len(calls) == 3
    assert clock.sleeps == [0.5, 1.0]
    assert clock.now == 101.5


@pytest.mark.parametrize("status", [408, 500, 503, 599])
def test_web_client_recovers_from_transient_http_failure(monkeypatch, clock, status):
    """Condition: public MCP read receives 408 or 5xx then succeeds. Expected: one bounded retry."""
    calls = []

    def http_then_success(request, timeout):
        calls.append(request)
        if len(calls) == 1:
            raise HTTPError(request.full_url, status, "temporary", hdrs=None, fp=None)
        return _mcp_response({"content": [{"type": "text", "text": "recovered"}]})

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(http_then_success))

    assert WebClient().call_mcp_tool("search_jobs", {}) == "recovered"
    assert len(calls) == 2
    assert clock.sleeps == [0.5]


def test_web_client_exhausts_transient_http_retries(monkeypatch, clock):
    """Condition: public MCP read repeatedly receives 503. Expected: HTTP error after exactly three attempts."""
    calls = []

    def unavailable(request, timeout):
        calls.append(request)
        raise HTTPError(request.full_url, 503, "private response", hdrs=None, fp=None)

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(unavailable))

    with pytest.raises(HireCafeHTTPError) as error:
        WebClient().call_mcp_tool("search_jobs", {})

    assert str(error.value) == "mcp returned HTTP 503"
    assert len(calls) == 3
    assert clock.sleeps == [0.5, 1.0]


def test_web_client_shares_deadline_across_requests_and_backoff(monkeypatch, clock):
    """Condition: slow timeouts exhaust the total budget. Expected: socket timeouts shrink and total time is 30s."""
    timeouts = []

    def timed_out(request, timeout):
        timeouts.append(timeout)
        clock.now += min(12, timeout)
        raise TimeoutError("private timeout details")

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(timed_out))

    with pytest.raises(HireCafeTransportError, match="mcp transport failed: request timed out"):
        WebClient().call_mcp_tool("search_jobs", {})

    assert timeouts == [30, 17.5, 4.5]
    assert clock.sleeps == [0.5, 1.0]
    assert clock.now == 130


def test_web_client_does_not_retry_after_request_consumes_deadline(monkeypatch, clock):
    """Condition: the first socket timeout consumes a custom budget. Expected: no further request or sleep."""
    timeouts = []

    def timed_out(request, timeout):
        timeouts.append(timeout)
        clock.now += timeout
        raise TimeoutError()

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(timed_out))

    with pytest.raises(HireCafeTransportError, match="request timed out"):
        WebClient(timeout=7).call_mcp_tool("search_jobs", {})

    assert timeouts == [7]
    assert clock.sleeps == []
    assert clock.now == 107


def test_web_client_caps_backoff_at_deadline(monkeypatch, clock):
    """Condition: less than one backoff remains. Expected: sleep is capped and no request starts after expiry."""
    calls = []

    def slow_dns_failure(request, timeout):
        calls.append(request)
        clock.now += 29.75
        raise URLError(socket.gaierror(socket.EAI_AGAIN, "temporary"))

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(slow_dns_failure))

    with pytest.raises(HireCafeTransportError, match="request timed out"):
        WebClient().call_mcp_tool("search_jobs", {})

    assert len(calls) == 1
    assert clock.sleeps == [0.25]
    assert clock.now == 130


def test_web_client_counts_response_read_time_against_deadline(monkeypatch, clock):
    """Condition: reading a response exhausts the budget. Expected: late content is rejected without retry."""
    calls = []

    class SlowResponse(io.BytesIO):
        def read(self, size=-1):
            clock.now += 30
            return super().read(size)

    def slow_response(request, timeout):
        calls.append(request)
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "late"}]}})
        return SlowResponse(body.encode())

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(slow_response))

    with pytest.raises(HireCafeTransportError, match="request timed out"):
        WebClient().call_mcp_tool("search_jobs", {})

    assert len(calls) == 1
    assert clock.sleeps == []
    assert clock.now == 130


def test_web_client_deadline_returns_while_dns_is_still_blocked(monkeypatch, clock):
    """Condition: DNS ignores the socket timeout. Expected: caller times out and the late read cannot retry."""
    entered = Event()
    release = Event()
    threads = []
    calls = []

    def track_thread(**kwargs):
        thread = Thread(**kwargs)
        threads.append(thread)
        return thread

    def blocked_dns(request, timeout):
        calls.append(timeout)
        entered.set()
        release.wait(timeout=1)
        raise URLError(socket.gaierror(socket.EAI_AGAIN, "temporary"))

    monkeypatch.setattr("hiringcafe_cli.http_client.Thread", track_thread)
    monkeypatch.setattr(WebClient, "urlopen", staticmethod(blocked_dns))

    try:
        with pytest.raises(HireCafeTransportError, match="request timed out"):
            WebClient(timeout=0.1).call_mcp_tool("search_jobs", {})
        assert entered.is_set()
        assert threads[0].is_alive()
    finally:
        clock.now += 1
        release.set()
        for thread in threads:
            thread.join(timeout=1)

    assert calls == pytest.approx([0.1])
    assert clock.sleeps == []
    assert all(thread.daemon and not thread.is_alive() for thread in threads)


@pytest.mark.parametrize("wrapped", [False, True])
def test_web_client_does_not_retry_certificate_validation_failure(monkeypatch, clock, wrapped):
    """Condition: TLS rejects a certificate. Expected: direct and URL-wrapped failures get one safe attempt."""
    calls = []

    def invalid_certificate(request, timeout):
        calls.append(request)
        cause = ssl.SSLCertVerificationError(1, "https://example.test/?private=synthetic-secret")
        raise URLError(cause) if wrapped else cause

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(invalid_certificate))

    with pytest.raises(HireCafeTransportError) as error:
        WebClient().call_mcp_tool("search_jobs", {})

    assert "connection failed" in str(error.value)
    assert "synthetic-secret" not in str(error.value)
    assert "https://" not in str(error.value)
    assert len(calls) == 1
    assert clock.sleeps == []


@pytest.mark.parametrize(
    "body",
    [
        b"not JSON: private content",
        b"[]",
        b'{"jsonrpc":"2.0","id":1,"error":{"message":"private content"}}',
        b'{"jsonrpc":"1.0","id":1,"result":{}}',
    ],
)
def test_web_client_does_not_retry_invalid_json_or_rpc(monkeypatch, clock, body):
    """Condition: public read returns invalid JSON or RPC. Expected: one attempt and no content in diagnostics."""
    calls = []

    def malformed(request, timeout):
        calls.append(request)
        return io.BytesIO(body)

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(malformed))

    with pytest.raises(ValueError) as error:
        WebClient().call_mcp_tool("search_jobs", {})

    assert len(calls) == 1
    assert clock.sleeps == []
    assert "private content" not in str(error.value)


@pytest.mark.parametrize(
    ("method", "arguments"),
    [
        ("marketplace_stage", ("fixture-job", "synthetic-token", "saved")),
        ("marketplace_mutation", ("removeJobFromList", {"user_token": "synthetic-token"})),
        ("remove_from_list", ("fixture-job", "synthetic-token", "saved")),
        ("remove_job", ("fixture-job", "synthetic-token", "saved")),
    ],
)
@pytest.mark.parametrize(
    "failure",
    [
        URLError(socket.gaierror(socket.EAI_AGAIN, "temporary")),
        TimeoutError(),
        HTTPError("https://example.test", 503, "temporary", hdrs=None, fp=None),
    ],
)
def test_web_client_marketplace_mutations_make_one_attempt(monkeypatch, clock, method, arguments, failure):
    """Condition: a marketplace mutation encounters a retryable read failure. Expected: exactly one mutation call."""
    calls = []

    def failed(request, timeout):
        calls.append(request)
        raise failure

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(failed))

    with pytest.raises((HireCafeHTTPError, HireCafeTransportError)) as error:
        getattr(WebClient(), method)(*arguments)

    assert len(calls) == 1
    assert clock.sleeps == []
    assert "synthetic-token" not in str(error.value)


def test_web_client_public_get_uses_same_retry_budget(monkeypatch, clock):
    """Condition: existing anonymous GET temporarily fails DNS. Expected: shared read policy recovers safely."""
    calls = []

    def dns_then_success(request, timeout):
        calls.append((request, timeout))
        if len(calls) == 1:
            raise URLError(socket.gaierror(socket.EAI_AGAIN, "temporary"))
        return io.BytesIO(b'{"job":{"objectID":"fixture-job"}}')

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(dns_then_success))

    assert WebClient().job_description("fixture-job") == {"objectID": "fixture-job"}
    assert all(request.get_method() == "GET" for request, _ in calls)
    assert [timeout for _, timeout in calls] == [30, 29.5]
    assert clock.sleeps == [0.5]


@pytest.mark.parametrize("status", [403, 429])
def test_web_client_public_get_does_not_retry_access_denial_or_rate_limit(monkeypatch, clock, status):
    """Condition: existing anonymous GET receives 403 or 429. Expected: one call under the shared read policy."""
    calls = []

    def denied(request, timeout):
        calls.append(request)
        raise HTTPError(request.full_url, status, "private response", hdrs=None, fp=None)

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(denied))

    with pytest.raises(HireCafeHTTPError) as error:
        WebClient().job_description("fixture-job")

    assert error.value.status == status
    assert len(calls) == 1
    assert clock.sleeps == []


@pytest.mark.parametrize(
    ("failure", "exit_code", "attempts"),
    [
        (URLError(socket.gaierror(socket.EAI_AGAIN, "https://example.test/?synthetic-secret")), 1, 3),
        (HTTPError("https://example.test/?synthetic-secret", 429, "private content", hdrs=None, fp=None), 3, 1),
    ],
)
def test_web_client_failure_preserves_cli_exit_and_safe_stderr(monkeypatch, capsys, failure, exit_code, attempts):
    """Condition: a fresh CLI read fails DNS or hits 429. Expected: exit 1 or 3 with bounded calls and safe stderr."""
    from hiringcafe_cli import main

    calls = []

    def failed(request, timeout):
        calls.append(request)
        raise failure

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(failed))
    monkeypatch.setenv("HIRINGCAFE_BASE_URL", "https://example.test")

    with pytest.raises(SystemExit) as error:
        main(["search", "synthetic-query", "--no-cache"])

    output = capsys.readouterr()
    assert error.value.code == exit_code
    assert len(calls) == attempts
    assert output.out == ""
    assert "mcp" in output.err
    assert "synthetic-secret" not in output.err
    assert "private content" not in output.err
    assert "synthetic-query" not in output.err
    assert "https://" not in output.err
