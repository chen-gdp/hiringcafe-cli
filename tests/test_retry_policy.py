import urllib.error

from hiringcafe_cli.http_client import HireCafeHTTPError, HireCafeTransportError, RetryPolicy, retryable


class BytesResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b"{}"


def test_retryable_classification_covers_verified_statuses():
    """Condition: anonymous GET receives a transport or HTTP error.

    Expected: 408, 429, and 5xx are retryable; other HTTP errors are not.
    """
    assert retryable(HireCafeTransportError("search", urllib.error.URLError("offline")))
    for status in (408, 429, 500):
        assert retryable(HireCafeHTTPError("search", status))
    assert not retryable(HireCafeHTTPError("search", 404))


def test_retry_policy_is_bounded_and_jittered(monkeypatch):
    """Condition: policy calculates bounded backoff.

    Expected: delays stay below twice the exponential base across retries.
    """
    monkeypatch.setattr("hiringcafe_cli.http_client.random.uniform", lambda start, end: end)
    policy = RetryPolicy(count=3, base=0.1)
    delays = [policy.delay(attempt) for attempt in range(policy.count)]
    assert delays == [0.1, 0.2, 0.4]
    assert policy.sleep is not None
