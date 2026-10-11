"""Parse public job data returned by HiringCafe's documented MCP tools."""

import html
import re
import urllib.parse
from typing import Any

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TOTAL_RE = re.compile(
    r"^## HiringCafe job results \(showing (?P<shown>[\d,]+) of (?P<total>[\d,]+) matches\)$", re.IGNORECASE
)
SEARCH_LINK_RE = re.compile(r"^### \[(?P<title>.+?)\]\((?P<url>https://[^)]+)\)$")
DETAIL_LINK_RE = re.compile(r"^# \[(?P<title>.+?)\]\((?P<url>https://[^)]+)\)$")
FIELD_RE = re.compile(r"^- \*\*(?P<name>[^:*]+):\*\*\s*(?P<value>.*)$")
PLAIN_FIELD_RE = re.compile(r"^- (?P<name>[^:]+):\s*(?P<value>.*)$")
LINK_RE = re.compile(r"\[[^]]*\]\((https://[^)]+)\)")
RAW_URL_RE = re.compile(r"https://\S+")


def _safe_text(text: str) -> str:
    """Remove email-address strings before parsed public content is cached or printed."""
    return CONTROL_RE.sub("", EMAIL_RE.sub("[email redacted]", html.unescape(text)))


def _value(text: str) -> str | None:
    """Normalize an optional Markdown value without changing its meaning."""
    value = html.unescape(text.strip()).strip("`").strip()
    return None if not value or value.casefold() in {"n/a", "not specified", "unknown"} else value


def _https_url(value: str) -> str:
    """Validate and return an HTTPS URL from untrusted tool output."""
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        raise ValueError("invalid HTTPS link in HiringCafe response") from None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("invalid HTTPS link in HiringCafe response")
    return value


def _link_value(value: str) -> str | None:
    """Extract a Markdown or plain HTTPS link from a field value."""
    markdown_link = LINK_RE.search(value)
    raw_url = markdown_link.group(1) if markdown_link else None
    if raw_url is None:
        raw_link = RAW_URL_RE.search(value)
        raw_url = raw_link.group(0).rstrip(".,;") if raw_link else None
    return _https_url(raw_url) if raw_url else None


def parse_search_response(text: str) -> dict[str, Any]:
    """Normalize one `search_jobs` Markdown result.

    Args:
        text: Text content returned by the MCP tool.

    Returns:
        A mapping containing the total match count and normalized jobs.

    Raises:
        ValueError: If the response does not match the verified result format.
    """
    text = _safe_text(text).strip()
    if text.startswith("No jobs matched that search on HiringCafe."):
        return {"totalCount": 0, "jobs": []}
    lines = text.splitlines()
    shown_count = None
    total_count = None
    for line in lines:
        match = TOTAL_RE.match(line.strip())
        if match:
            shown_count = int(match.group("shown").replace(",", ""))
            total_count = int(match.group("total").replace(",", ""))
            break
    if total_count is None:
        raise ValueError("unrecognized HiringCafe search response")

    jobs = []
    current = None
    for line in lines:
        heading = SEARCH_LINK_RE.match(line.strip())
        if heading:
            if current is not None:
                jobs.append(_search_job(current))
            current = {
                "title": html.unescape(heading.group("title")),
                "hiringCafeUrl": _https_url(heading.group("url")),
                "company": None,
                "fields": {},
            }
            continue
        if current is None:
            continue
        stripped = line.strip()
        strong = re.fullmatch(r"\*\*(.+)\*\*", stripped)
        if strong and current["company"] is None:
            current["company"] = html.unescape(strong.group(1).strip())
            continue
        field = FIELD_RE.match(stripped) or PLAIN_FIELD_RE.match(stripped)
        if field:
            current["fields"][field.group("name").strip().casefold()] = _value(field.group("value"))
    if current is not None:
        jobs.append(_search_job(current))
    if total_count > 0 and not jobs:
        raise ValueError("HiringCafe search response omitted its job results")
    if shown_count != len(jobs) or shown_count > total_count:
        raise ValueError("HiringCafe search result count does not match its header")
    return {"totalCount": total_count, "jobs": jobs}


def _search_job(entry: dict[str, Any]) -> dict[str, Any]:
    """Convert one parsed search block to the version-1 job representation."""
    fields = entry["fields"]
    object_id = fields.get("job id")
    if not object_id:
        raise ValueError("HiringCafe search result has no job ID")
    return {
        "id": object_id,
        "title": entry["title"],
        "company": entry["company"],
        "location": fields.get("location"),
        "url": None,
        "hiringCafeUrl": entry["hiringCafeUrl"],
        "source": None,
        "workplaceType": fields.get("workplace"),
        "commitment": fields.get("employment type"),
        "publishedAt": fields.get("posted"),
        "expired": None,
    }


def parse_job_details(text: str, object_id: str) -> dict[str, Any]:
    """Normalize one `get_job_details` Markdown result.

    Args:
        text: Text content returned by the MCP tool.
        object_id: The requested HiringCafe job ID.

    Returns:
        A safe version-1 job-detail mapping.

    Raises:
        ValueError: If title, links, ID, or full description are missing or invalid.
    """
    text = _safe_text(text)
    lines = text.splitlines()
    heading = next(
        (match for line in lines if (match := DETAIL_LINK_RE.match(line.strip())) is not None),
        None,
    )
    if heading is None:
        raise ValueError("unrecognized HiringCafe job-detail response")
    metadata_end = next((index for index, line in enumerate(lines) if line.strip().startswith("## ")), len(lines))
    fields = {}
    for line in lines[:metadata_end]:
        match = FIELD_RE.match(line.strip()) or PLAIN_FIELD_RE.match(line.strip())
        if match:
            fields[match.group("name").strip().casefold()] = match.group("value").strip()
    returned_id = _value(fields.get("job id", ""))
    if returned_id != object_id:
        raise ValueError("HiringCafe job-detail response ID does not match the requested ID")
    description_start = next(
        (index + 1 for index, line in enumerate(lines) if line.strip().casefold() == "## full description"), None
    )
    if description_start is None:
        raise ValueError("HiringCafe job-detail response has no full description")
    description = "\n".join(lines[description_start:]).strip()
    if not description:
        raise ValueError("HiringCafe job-detail response has no full description")
    return {
        "id": returned_id,
        "title": html.unescape(heading.group("title")),
        "description": description,
        "url": _link_value(fields.get("view & apply", "")),
        "hiringCafeUrl": _https_url(heading.group("url")),
    }
