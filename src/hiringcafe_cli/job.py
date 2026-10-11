"""Anonymous job-description command."""

import json
import os
import sys

from hiringcafe_cli.cache import active_cache_root, cache_read, cache_write
from hiringcafe_cli.http_client import WebClient, configured_base_url
from hiringcafe_cli.mcp import parse_job_details

JOB_TTL = 86400


def show(object_id: str, no_cache: bool = False, cache_ttl: int | None = None) -> dict:
    """Fetch and normalize a job description.

    Args:
        object_id: Nonempty HiringCafe object ID.

    Returns:
        Stable version-1 job-detail envelope.
    """
    cache_root = active_cache_root()
    client = WebClient()
    key = ("mcp-job-v1", configured_base_url(), object_id)
    ttl = JOB_TTL if cache_ttl is None else cache_ttl
    enabled = no_cache is False and not os.environ.get("HIRINGCAFE_NO_CACHE")
    raw = cache_read(key, ttl, cache_root, enabled=enabled)
    if raw is not None:
        job = raw
    else:
        response = client.call_mcp_tool("get_job_details", {"job_id": object_id})
        job = parse_job_details(response, object_id)
        cache_write(key, job, ttl, cache_root, enabled=enabled)
    if not job:
        raise ValueError("HiringCafe MCP response has no job details")
    return {
        "version": 1,
        "job": {
            "id": job["id"],
            "title": job["title"],
            "description": job["description"],
            "url": job["url"],
            "hiringCafeUrl": job["hiringCafeUrl"],
        },
    }


def run(argv: object, json_output: bool) -> int:
    """Execute job show with CLI arguments."""
    if not argv.object_id:
        print("hiringcafe: object ID must not be empty", file=sys.stderr)
        return 2
    envelope = show(
        argv.object_id,
        no_cache=getattr(argv, "no_cache", False),
        cache_ttl=getattr(argv, "cache_ttl", None),
    )
    if json_output:
        print(json.dumps(envelope, separators=(",", ":")))
    else:
        job = envelope["job"]
        print(f"{job['title'] or 'Untitled'}\n{job['url'] or job['hiringCafeUrl']}\n\n{job['description'] or ''}")
    return 0
