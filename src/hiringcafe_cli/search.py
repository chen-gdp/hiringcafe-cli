"""Anonymous search command and normalized output contract."""

import json
import os

from hiringcafe_cli.cache import active_cache_root, cache_read, cache_write
from hiringcafe_cli.http_client import WebClient, configured_base_url
from hiringcafe_cli.mcp import parse_search_response
from hiringcafe_cli.search_state import SEARCH_FILTER_KEYS, InvalidSearchState, build_search_arguments
from hiringcafe_cli.search_state import SEARCH_LIMIT as SEARCH_LIMIT

SEARCH_TTL = 900


def search(
    query: str | None,
    page: int,
    raw_search_state: str | None = None,
    no_cache: bool = False,
    cache_ttl: int | None = None,
    filters: dict | None = None,
) -> dict:
    """Fetch and normalize the supported public search response.

    Args:
        query: Query-text mode.
        page: Compatibility page number; only page zero is supported.
        raw_search_state: Optional raw JSON object mode.
        no_cache: Bypass anonymous cache reads and writes.
        cache_ttl: Optional cache age and lifetime override in seconds.
        filters: Optional verified filter arguments using canonical MCP names.

    Returns:
        Stable version-1 search envelope.
    """
    state, arguments = build_search_arguments(query, raw_search_state, filters)
    if page != 0:
        raise InvalidSearchState("HiringCafe's supported search interface does not provide pagination; use --page 0")
    cache_root = active_cache_root()
    base_url = configured_base_url()
    key = ("mcp-search-v2", base_url, arguments)
    enabled = no_cache is False and not os.environ.get("HIRINGCAFE_NO_CACHE")
    ttl = SEARCH_TTL if cache_ttl is None else cache_ttl
    cached = cache_read(key, ttl, cache_root, enabled=enabled)
    if cached is not None:
        return cached
    parsed = parse_search_response(WebClient().call_mcp_tool("search_jobs", arguments))
    jobs = parsed["jobs"]
    total_count = parsed["totalCount"]
    envelope = {
        "version": 1,
        "query": {"searchState": state, "page": page},
        "result": {
            "totalCount": total_count,
            "companyCount": None,
            "pageSize": arguments["limit"],
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
        filters={key: getattr(argv, key) for key in SEARCH_FILTER_KEYS if getattr(argv, key, None) is not None},
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
