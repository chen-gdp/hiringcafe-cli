"""Anonymous HiringCafe web and SSR HTTP client."""

import json
import os
import random
import time
import urllib.parse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from hiringcafe_cli.io_limits import read_limited

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 hiringcafe-cli/0.1"
    ),
}
RETRYABLE_STATUSES = {408, 429, *range(500, 600)}
MCP_URL_PATH = "/api/mcp"
MCP_TOOLS = {"search_jobs", "get_job_details"}


class HireCafeHTTPError(RuntimeError):
    """A non-success HTTP response from a HiringCafe endpoint."""

    def __init__(self, endpoint: str, status: int, reason: str = "") -> None:
        """Initialize the HTTP error.

        Args:
            endpoint: Stable endpoint name for diagnostics.
            status: HTTP response status.
            reason: Optional response reason.
        """
        self.endpoint = endpoint
        self.status = status
        self.reason = reason
        super().__init__(f"{endpoint} returned HTTP {status}")


class HireCafeTransportError(RuntimeError):
    """A transport failure before an HTTP response completed."""

    def __init__(self, endpoint: str, cause: Exception) -> None:
        """Initialize the transport error.

        Args:
            endpoint: Stable endpoint name for diagnostics.
            cause: Original exception.
        """
        self.endpoint = endpoint
        self.cause = cause
        super().__init__(f"{endpoint} transport failed: {cause}")


def configured_base_url() -> str:
    """Return the configured HTTPS anonymous web base URL without a trailing slash.

    Raises:
        ValueError: If the configured URL is not HTTPS.
    """
    base_url = os.environ.get("HIRINGCAFE_BASE_URL", "https://hiringcafe.com").rstrip("/")
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username is not None or parsed.password is not None:
        raise ValueError("HIRINGCAFE_BASE_URL must use HTTPS")
    return base_url


def retryable(error: Exception) -> bool:
    """Classify whether an anonymous GET error may be retried."""
    return isinstance(error, HireCafeTransportError) or (
        isinstance(error, HireCafeHTTPError) and error.status in RETRYABLE_STATUSES
    )


class RetryPolicy:
    """Bounded exponential backoff with full jitter."""

    def __init__(self, count: int = 2, base: float = 0.5, timeout: float = 30) -> None:
        self.count = count
        self.base = base
        self.timeout = timeout
        self.sleep = time.sleep

    def delay(self, attempt: int) -> float:
        """Return the bounded backoff for a zero-based attempt."""
        return random.uniform(0, self.base * (2**attempt))


class WebClient:
    """Client that owns every anonymous HiringCafe web URL."""

    urlopen = staticmethod(urlopen)

    def __init__(self, base_url: str | None = None, timeout: float = 30) -> None:
        """Initialize the client.

        Args:
            base_url: HTTPS base URL; defaults to ``HIRINGCAFE_BASE_URL`` or production.
            timeout: Per-request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/") if base_url else configured_base_url()
        self.timeout = timeout
        self.retry_policy = RetryPolicy(timeout=timeout)

    def call_mcp_tool(self, name: str, arguments: dict[str, str | int]) -> str:
        """Call a documented read-only HiringCafe MCP tool and return its text content.

        Args:
            name: Supported public tool name.
            arguments: Tool arguments encoded as JSON.

        Returns:
            Joined textual content from the MCP result.

        Raises:
            ValueError: If the tool name or JSON-RPC response is invalid.
            HireCafeHTTPError: If HiringCafe returns an HTTP error.
            HireCafeTransportError: If the request cannot complete.
        """
        if name not in MCP_TOOLS:
            raise ValueError("unsupported HiringCafe MCP tool")
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
            separators=(",", ":"),
        ).encode()
        request = Request(
            f"{self.base_url}{MCP_URL_PATH}",
            data=body,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "User-Agent": "hiringcafe-cli",
            },
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=self.timeout) as response:
                response_body = read_limited(response, "mcp").decode("utf-8")
        except HTTPError as error:
            raise HireCafeHTTPError("mcp", error.code, error.reason) from error
        except (URLError, TimeoutError, OSError) as error:
            raise HireCafeTransportError("mcp", error) from error
        payload = self._json(response_body)
        if payload.get("jsonrpc") != "2.0" or type(payload.get("id")) is not int or payload["id"] != 1:
            raise ValueError("invalid HiringCafe MCP response")
        result = payload.get("result")
        if "error" in payload or not isinstance(result, dict) or result.get("isError"):
            raise ValueError("HiringCafe MCP tool call failed")
        content = result.get("content")
        if not isinstance(content, list):
            raise ValueError("HiringCafe MCP response has no text content")
        texts = []
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "text":
                continue
            text = item.get("text")
            if not isinstance(text, str):
                raise ValueError("HiringCafe MCP response has invalid text content")
            texts.append(text)
        if not texts:
            raise ValueError("HiringCafe MCP response has no text content")
        return "\n".join(texts)

    def job_description(self, object_id: str) -> dict:
        """Fetch a job-description JSON object.

        Args:
            object_id: Nonempty HiringCafe object ID.

        Returns:
            The response's ``job`` object.
        """
        query = urllib.parse.urlencode({"id": object_id})
        payload = self._json(self._get(f"{self.base_url}/api/job-description?{query}", "job-description"))
        job = payload.get("job")
        if not isinstance(job, dict):
            raise ValueError("job-description response has no job object")
        return job

    def marketplace_stage(self, object_id: str, id_token: str, stage: str) -> None:
        """Sync a saved-job stage through the verified marketplace endpoint."""
        body = json.dumps(
            {"job_id": object_id, "user_token": id_token, "stage": stage},
            separators=(",", ":"),
        ).encode()
        request = urllib.request.Request(
            f"{self.base_url}/api/updateMarketplaceJobStageForUser",
            data=body,
            headers={**BROWSER_HEADERS, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=self.timeout) as response:
                read_limited(response, "marketplace-stage")
        except HTTPError as error:
            raise HireCafeHTTPError("marketplace-stage", error.code, error.reason) from error
        except (URLError, TimeoutError, OSError) as error:
            raise HireCafeTransportError("marketplace-stage", error) from error

    def marketplace_mutation(self, endpoint: str, body: dict) -> None:
        """POST a marketplace saved-job mutation and require success."""
        request = urllib.request.Request(
            f"{self.base_url}/api/{endpoint}",
            data=json.dumps(body, separators=(",", ":")).encode(),
            headers={**BROWSER_HEADERS, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=self.timeout) as response:
                read_limited(response, endpoint)
        except HTTPError as error:
            raise HireCafeHTTPError(endpoint, error.code, error.reason) from error
        except (URLError, TimeoutError, OSError) as error:
            raise HireCafeTransportError(endpoint, error) from error

    def remove_from_list(self, object_id: str, id_token: str, stage: str) -> None:
        """Remove a job from its old marketplace stage list."""
        self.marketplace_mutation(
            "removeJobFromList",
            {"job_id": object_id, "user_token": id_token, "stage": stage, "should_delete": False},
        )

    def remove_job(self, object_id: str, id_token: str, stage: str) -> None:
        """Delete a job through the marketplace owner endpoint."""
        self.marketplace_mutation(
            "removeJobFromList",
            {"job_id": object_id, "user_token": id_token, "stage": stage, "should_delete": True},
        )

    def _get(self, url: str, endpoint: str) -> str:
        """GET a URL and return its decoded body."""
        request = Request(url, headers=BROWSER_HEADERS)
        for attempt in range(self.retry_policy.count + 1):
            try:
                with self.urlopen(request, timeout=self.timeout) as response:
                    return read_limited(response, endpoint).decode("utf-8")
            except HTTPError as error:
                wrapped = HireCafeHTTPError(endpoint, error.code, error.reason)
            except (URLError, TimeoutError, OSError) as error:
                wrapped = HireCafeTransportError(endpoint, error)
            if attempt == self.retry_policy.count or not retryable(wrapped):
                raise wrapped
            self.retry_policy.sleep(self.retry_policy.delay(attempt))
        raise AssertionError("unreachable")

    def _json(self, body: str) -> dict:
        """Parse a JSON object response."""
        try:
            value = json.loads(body)
        except json.JSONDecodeError as error:
            raise ValueError("invalid JSON response") from error
        if not isinstance(value, dict):
            raise ValueError("JSON response is not an object")
        return value
