"""Anonymous search command and normalized output contract."""

import json
import os

from hiringcafe_cli.cache import active_cache_root, cache_read, cache_write
from hiringcafe_cli.http_client import WebClient, configured_base_url
from hiringcafe_cli.mcp import parse_search_response
from hiringcafe_cli.search_state import InvalidSearchState, build_search_state

SEARCH_TTL = 900
SEARCH_LIMIT = 10


def search(
    query: str,
    page: int,
    raw_search_state: str | None = None,
    no_cache: bool = False,
    cache_ttl: int | None = None,
) -> dict:
    """Fetch and normalize the supported public search response.

    Args:
        query: Query-text mode.
        page: Compatibility page number; only page zero is supported.
        raw_search_state: Optional raw JSON object mode.

    Returns:
        Stable version-1 search envelope.
    """
    state = build_search_state(
        query=query if raw_search_state is None or query else None,
        raw_search_state=raw_search_state,
    )
    if set(state) - {"searchQuery"}:
        raise InvalidSearchState(
            "HiringCafe's supported search interface accepts query text only; filters are not supported"
        )
    search_query = state.get("searchQuery", "")
    if not isinstance(search_query, str):
        raise InvalidSearchState("searchQuery must be a string")
    if page != 0:
        raise InvalidSearchState("HiringCafe's supported search interface does not provide pagination; use --page 0")
    cache_root = active_cache_root()
    base_url = configured_base_url()
    key = ("mcp-search-v1", base_url, search_query, SEARCH_LIMIT)
    enabled = no_cache is False and not os.environ.get("HIRINGCAFE_NO_CACHE")
    ttl = SEARCH_TTL if cache_ttl is None else cache_ttl
    cached = cache_read(key, ttl, cache_root, enabled=enabled)
    if cached is not None:
        return cached
    parsed = parse_search_response(
        WebClient().call_mcp_tool("search_jobs", {"search": search_query, "limit": SEARCH_LIMIT})
    )
    jobs = parsed["jobs"]
    total_count = parsed["totalCount"]
    envelope = {
        "version": 1,
        "query": {"searchState": state, "page": page},
        "result": {
            "totalCount": total_count,
            "companyCount": None,
            "pageSize": SEARCH_LIMIT,
            "page": 0,
            "isLastPage": total_count <= len(jobs),
            "paginationSupported": False,
            "jobs": jobs,
        },
    }
    cache_write(key, envelope, ttl, cache_root, enabled=enabled)
    return envelope


def run(argv: list[str], json_output: bool) -> int:
    """Execute search with CLI arguments."""
    if argv.page < 0:
        raise InvalidSearchState("page must be nonnegative")
    if argv.page != 0 or getattr(argv, "pages", 1) != 1:
        raise InvalidSearchState(
            "HiringCafe's supported search interface does not provide pagination; use --page 0 and --pages 1"
        )
    envelope = search(
        argv.query,
        0,
        argv.raw_search_state,
        no_cache=getattr(argv, "no_cache", False),
        cache_ttl=getattr(argv, "cache_ttl", None),
    )
    if getattr(argv, "jsonl", False):
        for job in envelope["result"]["jobs"]:
            print(json.dumps(job, separators=(",", ":")))
        return 0
    if json_output:
        print(json.dumps(envelope, separators=(",", ":")))
    else:
        for job in envelope["result"]["jobs"]:
            print(f"{job['id']}\t{job['title'] or 'Untitled'}\t{job['company'] or 'Unknown company'}")
    return 0
