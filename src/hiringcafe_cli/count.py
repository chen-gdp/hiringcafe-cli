"""Anonymous result-count command."""

import json

from hiringcafe_cli.search import search
from hiringcafe_cli.search_state import SEARCH_FILTER_KEYS


def count(
    query: str | None,
    raw_search_state: str | None = None,
    no_cache: bool = False,
    cache_ttl: int | None = None,
    filters: dict | None = None,
) -> dict:
    """Count results using the supported public search response.

    Args:
        query: Query-text mode.
        raw_search_state: Raw JSON object mode.
        no_cache: Bypass anonymous cache reads and writes.
        cache_ttl: Optional cache age and lifetime override in seconds.
        filters: Optional verified filter arguments using canonical MCP names.

    Returns:
        Stable count envelope.
    """
    envelope = search(query, 0, raw_search_state, no_cache=no_cache, cache_ttl=cache_ttl, filters=filters)
    total_count = envelope["result"]["totalCount"]
    return {"version": 1, "query": envelope["query"], "count": total_count}


def run(argv: object, json_output: bool) -> int:
    """Execute count with CLI arguments."""
    envelope = count(
        argv.query,
        argv.raw_search_state,
        no_cache=getattr(argv, "no_cache", False),
        cache_ttl=getattr(argv, "cache_ttl", None),
        filters={key: getattr(argv, key) for key in SEARCH_FILTER_KEYS if getattr(argv, key, None) is not None},
    )
    if json_output:
        print(json.dumps(envelope, separators=(",", ":")))
    else:
        print(envelope["count"])
    return 0
