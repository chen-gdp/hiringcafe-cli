"""Anonymous search command and normalized output contract."""

import json
import sys

from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.search_state import InvalidSearchState, build_search_state


def normalize_job(hit: dict) -> dict:
    """Normalize one SSR hit without user-tracking arrays.

    Args:
        hit: Raw ssrHits item.

    Returns:
        Stable job representation with nullable optional fields.
    """
    job_information = hit.get("job_information") or {}
    company = hit.get("enriched_company_data") or {}
    processed = hit.get("v5_processed_job_data") or {}
    object_id = hit.get("objectID")
    if not isinstance(object_id, str) or not object_id:
        raise ValueError("ssr hit has no objectID")
    return {
        "id": object_id,
        "title": job_information.get("title"),
        "company": company.get("name", processed.get("company_name")),
        "location": processed.get("formatted_workplace_location"),
        "url": hit.get("apply_url"),
        "source": hit.get("source"),
        "workplaceType": processed.get("workplace_type"),
        "commitment": processed.get("commitment"),
        "publishedAt": processed.get("estimated_publish_date"),
        "expired": hit.get("is_expired"),
    }


def search(query: str, page: int, raw_search_state: str | None = None) -> dict:
    """Fetch and normalize one search page.

    Args:
        query: Query-text mode.
        page: Nonnegative SSR page.
        raw_search_state: Optional raw JSON object mode.

    Returns:
        Stable version-1 search envelope.
    """
    state = build_search_state(query=query, raw_search_state=raw_search_state)
    properties = fetch_page(state, page)
    if properties.get("ssrError") is not None:
        raise ValueError(f"HiringCafe search error: {properties['ssrError']}")
    jobs = [normalize_job(hit) for hit in properties["ssrHits"]]
    return {
        "version": 1,
        "query": {"searchState": state, "page": page},
        "result": {
            "totalCount": properties["ssrTotalCount"],
            "companyCount": properties.get("ssrCompanyCount"),
            "pageSize": properties["ssrPageSize"],
            "page": properties["ssrPage"],
            "isLastPage": properties["ssrIsLastPage"],
            "jobs": jobs,
        },
    }


def fetch_page(state: dict, page: int) -> dict:
    """Fetch and validate one raw SSR page."""
    return WebClient().search_page(state, page)


def search_pages(query: str, pages: int, raw_search_state: str | None = None) -> list[dict]:
    """Fetch sequential pages and return normalized jobs in source order."""
    if pages < 1:
        raise InvalidSearchState("pages must be positive")
    state = build_search_state(query=query, raw_search_state=raw_search_state)
    jobs = []
    seen = set()
    for page in range(pages):
        properties = fetch_page(state, page)
        if properties.get("ssrError") is not None:
            raise ValueError(f"HiringCafe search error: {properties['ssrError']}")
        for hit in properties["ssrHits"]:
            job = normalize_job(hit)
            if job["id"] in seen:
                raise ValueError(f"duplicate objectID across search pages: {job['id']}")
            seen.add(job["id"])
            jobs.append(job)
        if properties["ssrIsLastPage"]:
            break
    return jobs


def run(argv: list[str], json_output: bool) -> int:
    """Execute search with CLI arguments."""
    if argv.page < 0:
        raise InvalidSearchState("page must be nonnegative")
    if getattr(argv, "pages", 1) < 1:
        raise InvalidSearchState("pages must be positive")
    if getattr(argv, "jsonl", False):
        for job in search_pages(argv.query, argv.pages, argv.raw_search_state):
            print(json.dumps(job, separators=(",", ":")))
        return 0
    envelope = search(argv.query, argv.page, argv.raw_search_state)
    if json_output:
        print(json.dumps(envelope, separators=(",", ":")))
    else:
        for job in envelope["result"]["jobs"]:
            print(f"{job['id']}\t{job['title'] or 'Untitled'}\t{job['company'] or 'Unknown company'}")
    return 0
