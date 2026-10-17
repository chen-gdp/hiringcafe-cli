"""Opt-in regression probe for HiringCafe's documented MCP read tools."""

import os

from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.mcp import parse_job_details, parse_search_response

SEARCH_QUERY = "python developer"


def main(argv: object | None = None, json_output: bool = False) -> int:
    """Probe public search and detail reads only when explicitly enabled.

    Args:
        argv: Reserved for future probe options.
        json_output: Reserved for the CLI handler contract.

    Returns:
        Process exit code.

    Raises:
        ValueError: If HiringCafe's verified MCP result contract has regressed.
    """
    del argv, json_output
    if os.environ.get("LIVE") != "1":
        print("skipped: set LIVE=1 to probe HiringCafe")
        return 0

    client = WebClient()
    result = parse_search_response(client.call_mcp_tool("search_jobs", {"search": SEARCH_QUERY, "limit": 1}))
    jobs = result["jobs"]
    if not jobs:
        raise ValueError("HiringCafe MCP probe search returned no jobs")
    parse_job_details(client.call_mcp_tool("get_job_details", {"job_id": jobs[0]["id"]}), jobs[0]["id"])
    filtered = parse_search_response(
        client.call_mcp_tool(
            "search_jobs",
            {
                "search": "software engineer",
                "location": "Germany",
                "workplace_types": ["Remote"],
                "employment_types": ["Full Time"],
                "limit": 1,
            },
        )
    )["jobs"]
    if len(filtered) != 1 or any(
        job.get("workplaceType") != "Remote"
        or "Full Time" not in {item.strip() for item in (job.get("commitment") or "").split(",")}
        for job in filtered
    ):
        raise ValueError("HiringCafe structured-filter probe returned missing or contradictory metadata")
    print("search_jobs: ok")
    print("get_job_details: ok")
    print("structured_filters: ok; location uses upstream geographic matching")
    return 0
