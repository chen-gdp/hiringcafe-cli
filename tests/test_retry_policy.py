"""Tests for public-read retry classification and bounded jitter."""

import errno
import socket
import ssl
from urllib.error import URLError

import pytest

from hiringcafe_cli.http_client import HireCafeHTTPError, HireCafeTransportError, RetryPolicy, retryable


@pytest.mark.parametrize("status", [408, 500, 503, 599])
def test_retryable_classification_accepts_transient_http_statuses(status):
    """Condition: public read receives 408 or 5xx. Expected: the failure is eligible for retry."""
    assert retryable(HireCafeHTTPError("mcp", status))


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429])
def test_retryable_classification_rejects_permanent_and_rate_limit_statuses(status):
    """Condition: public read receives a permanent error or 429. Expected: no automatic retry."""
    assert not retryable(HireCafeHTTPError("mcp", status))


@pytest.mark.parametrize(
    "cause",
    [
        socket.gaierror(socket.EAI_AGAIN, "temporary resolution failure"),
        TimeoutError("timed out"),
        ConnectionResetError("connection reset"),
        ConnectionRefusedError("connection refused"),
        OSError(errno.ENETUNREACH, "network unreachable"),
        OSError(errno.EHOSTUNREACH, "host unreachable"),
        OSError(errno.EAGAIN, "try again"),
    ],
)
@pytest.mark.parametrize("wrapped", [False, True])
def test_retryable_classification_accepts_typed_transient_transport(cause, wrapped):
    """Condition: transport reports a typed temporary failure. Expected: direct and URL-wrapped errors retry."""
    error = HireCafeTransportError("mcp", URLError(cause) if wrapped else cause)
    assert retryable(error)


@pytest.mark.parametrize(
    "cause",
    [
        ssl.SSLCertVerificationError(1, "certificate verification failed"),
        ssl.SSLError(1, "TLS failure"),
        socket.gaierror(socket.EAI_NONAME, "invalid hostname"),
        OSError(errno.EINVAL, "invalid configuration"),
        PermissionError(errno.EACCES, "permission denied"),
        URLError("opaque failure containing https://example.test/?private=query"),
    ],
)
@pytest.mark.parametrize("wrapped", [False, True])
def test_retryable_classification_rejects_permanent_and_opaque_transport(cause, wrapped):
    """Condition: transport error is permanent or unclassified. Expected: no speculative retry."""
    error = HireCafeTransportError("mcp", URLError(cause) if wrapped else cause)
    assert not retryable(error)


def test_retryable_classification_rejects_parse_errors():
    """Condition: response parsing fails. Expected: retry policy never retries a content failure."""
    assert not retryable(ValueError("invalid JSON response"))


def test_retry_policy_is_bounded_and_jittered(monkeypatch):
    """Condition: policy calculates bounded backoff.

    Expected: at most two retries use the existing full-jitter exponential bounds.
    """
    monkeypatch.setattr("hiringcafe_cli.http_client.random.uniform", lambda start, end: end)
    policy = RetryPolicy(count=3, base=0.1)
    delays = [policy.delay(attempt) for attempt in range(policy.count)]
    assert delays == [0.1, 0.2]
    assert policy.count == 2
    assert policy.timeout == 30
    assert policy.sleep is not None
