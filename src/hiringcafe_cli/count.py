"""Anonymous result-count command."""

import json

from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.search_state import build_search_state


def count(query: str, raw_search_state: str | None = None) -> dict:
    """Count results by requesting page zero.

    Args:
        query: Query-text mode.
        raw_search_state: Raw JSON object mode.

    Returns:
        Stable count envelope.
    """
    state = build_search_state(query=query, raw_search_state=raw_search_state)
    properties = WebClient().search_page(state, 0)
    total_count = properties.get("ssrTotalCount")
    if not isinstance(total_count, int):
        raise ValueError("ssrTotalCount is missing or invalid")
    return {"version": 1, "query": {"searchState": state, "page": 0}, "count": total_count}


def run(argv: object, json_output: bool) -> int:
    """Execute count with CLI arguments."""
    envelope = count(argv.query, argv.raw_search_state)
    if json_output:
        print(json.dumps(envelope, separators=(",", ":")))
    else:
        print(envelope["count"])
    return 0
