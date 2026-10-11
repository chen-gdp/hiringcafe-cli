"""Offline tests for the verified HiringCafe MCP response format."""

import pytest

from hiringcafe_cli.mcp import parse_job_details, parse_search_response

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 2 of 30 matches)

### [Data Analyst](https://hiringcafe.com/job/data-analyst?utm_source=claude&utm_campaign=mcp)
**Example Analytics**
- Location: Remote
- Workplace: Remote
- Employment type: Full Time
- Seniority: Mid Level
- Posted: 2026-10-01
- Job ID: `job-one`

### [Research Engineer](https://hiringcafe.com/job/research-engineer?utm_source=claude&utm_campaign=mcp)
**Example Labs**
- Location: Austin, TX
- Workplace: Hybrid
- Employment type: Contract
- Seniority: Senior Level
- Posted: 2026-10-02
- Job ID: `job-two`
"""

DETAIL_RESPONSE = """\
# [Platform Engineer](https://hiringcafe.com/job/platform-engineer?utm_source=claude&utm_campaign=mcp)
- **Location:** Remote
- **Workplace:** Remote
- **Employment type:** Full Time
- **Job ID:** `job-detail`
- **View & apply:** [Apply](https://jobs.example.invalid/platform-engineer)
## Requirements summary
Experience building systems.
## Full description
Design and operate reliable services.
Contact: person@example.invalid
Encoded contact: person&#64;example.invalid
"""


def test_parse_search_response_normalizes_markdown_jobs_and_preserves_attribution():
    """Condition: tool returns two result blocks. Expected: IDs, metadata, and links are normalized."""
    result = parse_search_response(SEARCH_RESPONSE)

    assert result["totalCount"] == 30
    assert [job["id"] for job in result["jobs"]] == ["job-one", "job-two"]
    assert result["jobs"][0]["title"] == "Data Analyst"
    assert result["jobs"][0]["company"] == "Example Analytics"
    assert result["jobs"][0]["workplaceType"] == "Remote"
    assert result["jobs"][0]["commitment"] == "Full Time"
    assert result["jobs"][0]["url"] is None
    assert "utm_source=claude" in result["jobs"][0]["hiringCafeUrl"]


def test_parse_search_response_handles_observed_no_results_message():
    """Condition: MCP returns HiringCafe's no-results text. Expected: a true zero-result response."""
    result = parse_search_response(
        "No jobs matched that search on HiringCafe. Try broadening the location, removing a filter, "
        "or using more general keywords."
    )

    assert result == {"totalCount": 0, "jobs": []}


@pytest.mark.parametrize(
    "text",
    [
        "unrecognized response",
        "## HiringCafe job results (showing 1 of many matches)\n### [Role](https://hiringcafe.com/job/role)",
        "## HiringCafe job results (showing 1 of 1 matches)\n### [Role](https://hiringcafe.com/job/role)",
        (
            "## HiringCafe job results (showing 1 of 1 matches)\n"
            "### [Role](http://hiringcafe.com/job/role)\n- Job ID: `job-one`"
        ),
        (
            "## HiringCafe job results (showing 2 of 2 matches)\n\n"
            "### [Role](https://hiringcafe.com/job/role)\n- Job ID: `job-one`"
        ),
    ],
)
def test_parse_search_response_rejects_unrecognized_or_incomplete_results(text):
    """Condition: count, ID, or secure result URL is invalid. Expected: parsing fails closed."""
    with pytest.raises(ValueError):
        parse_search_response(text)


def test_parse_job_details_sanitizes_email_and_preserves_both_links():
    """Condition: detail text has a public email and attributed links. Expected: no email escapes parsing."""
    job = parse_job_details(DETAIL_RESPONSE, "job-detail")

    assert job["id"] == "job-detail"
    assert job["title"] == "Platform Engineer"
    assert job["url"] == "https://jobs.example.invalid/platform-engineer"
    assert "utm_source=claude" in job["hiringCafeUrl"]
    assert "person@example.invalid" not in job["description"]
    assert "person&#64;example.invalid" not in job["description"]
    assert "[email redacted]" in job["description"]


def test_parse_job_details_rejects_mismatched_id_and_missing_description():
    """Condition: detail response is incomplete or belongs to another ID. Expected: no job is accepted."""
    with pytest.raises(ValueError, match="does not match"):
        parse_job_details(DETAIL_RESPONSE, "another-job")
    with pytest.raises(ValueError, match="full description"):
        parse_job_details(DETAIL_RESPONSE.split("## Full description")[0], "job-detail")
