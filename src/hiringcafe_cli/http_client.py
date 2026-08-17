"""Anonymous HiringCafe web and SSR HTTP client."""

import json
import os
import urllib.parse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 hiringcafe-cli/0.1"
    ),
}
REQUIRED_SSR_KEYS = ("ssrHits", "ssrPage", "ssrTotalCount", "ssrPageSize", "ssrIsLastPage")


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


def parse_ssr_page(html: str) -> dict:
    """Parse and validate pageProps from a HiringCafe SSR response.

    Args:
        html: Complete SSR HTML document.

    Returns:
        The validated pageProps object.

    Raises:
        ValueError: If __NEXT_DATA__ is missing, malformed, or incomplete.
    """
    marker_start = '<script id="__NEXT_DATA__" type="application/json">'
    fallback_start = '<script id="__NEXT_DATA__">'
    starts = [index for index in (html.find(marker_start), html.find(fallback_start)) if index >= 0]
    if not starts:
        raise ValueError("missing __NEXT_DATA__")
    start = min(starts)
    content_start = html.index(">", start) + 1
    end = html.find("</script>", content_start)
    if end < 0:
        raise ValueError("unterminated __NEXT_DATA__")
    try:
        payload = json.loads(html[content_start:end])
    except json.JSONDecodeError as error:
        raise ValueError("invalid __NEXT_DATA__ JSON") from error
    properties = payload.get("props", {}).get("pageProps", {})
    if not isinstance(properties, dict):
        raise ValueError("__NEXT_DATA__ pageProps is not an object")
    for key in REQUIRED_SSR_KEYS:
        if key not in properties:
            raise ValueError(f"missing SSR key: {key}")
    return properties


class WebClient:
    """Client that owns every anonymous HiringCafe web URL."""

    urlopen = staticmethod(urlopen)

    def __init__(self, base_url: str | None = None, timeout: float = 30) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL; defaults to ``HIRINGCAFE_BASE_URL`` or production.
            timeout: Per-request timeout in seconds.
        """
        self.base_url = (base_url or os.environ.get("HIRINGCAFE_BASE_URL", "https://hiringcafe.com")).rstrip("/")
        self.timeout = timeout

    def search_page(self, search_state: dict, page: int) -> dict:
        """Fetch one SSR search page.

        Args:
            search_state: Complete search state object.
            page: Nonnegative page number.

        Returns:
            Validated ``props.pageProps``.
        """
        query = urllib.parse.urlencode({"searchState": json.dumps(search_state), "page": page})
        return parse_ssr_page(self._get(f"{self.base_url}/?{query}", "search"))

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
                response.read()
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
                response.read()
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

    def _get(self, url: str, endpoint: str) -> str:
        """GET a URL and return its decoded body."""
        request = Request(url, headers=BROWSER_HEADERS)
        try:
            with self.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except HTTPError as error:
            raise HireCafeHTTPError(endpoint, error.code, error.reason) from error
        except (URLError, TimeoutError, OSError) as error:
            raise HireCafeTransportError(endpoint, error) from error

    def _json(self, body: str) -> dict:
        """Parse a JSON object response."""
        try:
            value = json.loads(body)
        except json.JSONDecodeError as error:
            raise ValueError("invalid JSON response") from error
        if not isinstance(value, dict):
            raise ValueError("JSON response is not an object")
        return value
