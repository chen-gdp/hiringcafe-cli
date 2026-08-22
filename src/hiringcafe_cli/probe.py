"""Opt-in endpoint regression probe for verified anonymous HiringCafe routes."""

import json
import os
import urllib.parse
from html.parser import HTMLParser
from urllib.request import urlopen

from hiringcafe_cli.http_client import configured_base_url
from hiringcafe_cli.io_limits import read_limited

BASE_URL = configured_base_url()
SEARCH_STATE = {"searchQuery": "python developer"}
TIMEOUT_SECONDS = 30


class _NextDataParser(HTMLParser):
    """HTML parser that captures the ``__NEXT_DATA__`` script body."""

    def __init__(self) -> None:
        """Initialize parser state."""
        super().__init__()
        self.payload: str | None = None
        self._capture = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Begin capturing the sole Next.js data script.

        Args:
            tag: Current HTML tag.
            attrs: Tag attributes.
        """
        if tag == "script" and dict(attrs).get("id") == "__NEXT_DATA__":
            self._capture = True

    def handle_data(self, data: str) -> None:
        """Collect script text.

        Args:
            data: Current text node.
        """
        if self._capture:
            self.payload = (self.payload or "") + data

    def handle_endtag(self, tag: str) -> None:
        """Stop capturing at the closing script tag.

        Args:
            tag: Current HTML tag.
        """
        if tag == "script" and self._capture:
            self._capture = False


def extract_next_data(html: str) -> dict:
    """Extract the Next.js payload from search HTML.

    Args:
        html: Complete SSR HTML response.

    Returns:
        The parsed ``__NEXT_DATA__`` object.

    Raises:
        ValueError: If the script is missing or contains invalid JSON.
    """
    parser = _NextDataParser()
    parser.feed(html)
    if parser.payload is None:
        raise ValueError("missing __NEXT_DATA__")
    try:
        payload = json.loads(parser.payload)
    except json.JSONDecodeError as error:
        raise ValueError("invalid __NEXT_DATA__ JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("__NEXT_DATA__ is not an object")
    return payload


def _get(url: str) -> dict | str:
    """GET a verified anonymous endpoint and return decoded JSON or HTML."""
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 hiringcafe-cli/0.1 endpoint-probe",
        },
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = read_limited(response, "endpoint probe").decode("utf-8")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def _page(page: int) -> dict:
    """Fetch and validate one SSR search page."""
    query = urllib.parse.urlencode({"searchState": json.dumps(SEARCH_STATE), "page": page})
    result = _get(f"{BASE_URL}/?{query}")
    html = result if isinstance(result, str) else ""
    properties = extract_next_data(html).get("props", {}).get("pageProps", {})
    required = ("ssrHits", "ssrTotalCount", "ssrPage", "ssrIsLastPage")
    for key in required:
        if key not in properties:
            raise ValueError(f"missing SSR key: {key}")
    initial_state = properties.get("initialSearchState", {})
    if initial_state.get("searchQuery") != SEARCH_STATE["searchQuery"]:
        raise ValueError("page metadata lost search state")
    return properties


def main(argv: object | None = None, json_output: bool = False) -> int:
    """Run the endpoint probe only when explicitly enabled.

    Args:
        argv: Reserved for future CLI options.

    Returns:
        Process exit code.
    """
    del argv
    if os.environ.get("LIVE") != "1":
        print("skipped: set LIVE=1 to probe HiringCafe")
        return 0

    pages = [_page(0), _page(1)]
    hits = pages[0]["ssrHits"]
    if not hits or not isinstance(hits[0].get("objectID"), str):
        raise ValueError("search page 0 has no usable objectID")
    object_id = hits[0]["objectID"]
    detail_query = urllib.parse.urlencode({"id": object_id})
    detail = _get(f"{BASE_URL}/api/job-description?{detail_query}")
    if not isinstance(detail, dict) or not isinstance(detail.get("job"), dict):
        raise ValueError("job response has no job object")

    for index in range(len(pages)):
        print(f"search page {index}: ok")
    print(f"job description {object_id}: ok")
    return 0
