"""Tests for the opt-in HiringCafe MCP integration probe."""

import io
from contextlib import redirect_stdout

import pytest

from hiringcafe_cli.probe import main

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 1 of 1 matches)

### [Example role](https://hiringcafe.com/job/example?utm_source=claude)
- Workplace: Remote
- Employment type: Full Time
- Job ID: `job-one`
"""

DETAIL_RESPONSE = """\
# [Example role](https://hiringcafe.com/job/example?utm_source=claude)
- **Job ID:** `job-one`
## Full description
Example description.
"""


def test_live_probe_reports_safe_search_and_detail_results(monkeypatch):
    """Condition: LIVE=1 and both tools succeed. Expected: safe summary without job data."""

    class FakeClient:
        def __init__(self):
            self.calls = []

        def call_mcp_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return SEARCH_RESPONSE if name == "search_jobs" else DETAIL_RESPONSE

    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.probe.WebClient", lambda: client)
    monkeypatch.setenv("LIVE", "1")
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = main([])

    assert exit_code == 0
    assert output.getvalue() == (
        "search_jobs: ok\nget_job_details: ok\nstructured_filters: ok; location uses upstream geographic matching\n"
    )
    assert client.calls == [
        ("search_jobs", {"search": "python developer", "limit": 1}),
        ("get_job_details", {"job_id": "job-one"}),
        (
            "search_jobs",
            {
                "search": "software engineer",
                "location": "Germany",
                "workplace_types": ["Remote"],
                "employment_types": ["Full Time"],
                "limit": 1,
            },
        ),
    ]


def test_live_probe_does_not_construct_client_when_disabled(monkeypatch):
    """Condition: LIVE is unset. Expected: probe skips without using the network."""

    def fail_client():
        raise AssertionError("disabled probe must not create a client")

    monkeypatch.setattr("hiringcafe_cli.probe.WebClient", fail_client)
    monkeypatch.delenv("LIVE", raising=False)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = main([])

    assert exit_code == 0
    assert "skipped: set LIVE=1" in output.getvalue()


def test_live_probe_fails_when_search_response_is_unrecognized(monkeypatch):
    """Condition: endpoint returns an unknown search shape. Expected: probe refuses a false pass."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return "unrecognized response"

    monkeypatch.setattr("hiringcafe_cli.probe.WebClient", FakeClient)
    monkeypatch.setenv("LIVE", "1")

    with pytest.raises(ValueError, match="unrecognized HiringCafe search response"):
        main([])


@pytest.mark.parametrize("field,value", [("Remote", "Onsite"), ("Full Time", "Contract")])
def test_live_probe_rejects_contradictory_filter_metadata(monkeypatch, field, value):
    """Condition: filtered results contradict the requested type. Expected: no false success or job output."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            if name == "get_job_details":
                return DETAIL_RESPONSE
            if "workplace_types" in arguments:
                return SEARCH_RESPONSE.replace(field, value)
            return SEARCH_RESPONSE

    monkeypatch.setattr("hiringcafe_cli.probe.WebClient", FakeClient)
    monkeypatch.setenv("LIVE", "1")
    with pytest.raises(ValueError, match="contradictory metadata"):
        main([])


def test_live_probe_requires_evidence_from_a_filtered_result(monkeypatch, capsys):
    """Condition: structured search has no sample result. Expected: no false metadata verification."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            if name == "get_job_details":
                return DETAIL_RESPONSE
            if "workplace_types" in arguments:
                return "No jobs matched that search on HiringCafe."
            return SEARCH_RESPONSE

    monkeypatch.setattr("hiringcafe_cli.probe.WebClient", FakeClient)
    monkeypatch.setenv("LIVE", "1")
    with pytest.raises(ValueError, match="missing or contradictory metadata"):
        main([])
    assert capsys.readouterr().out == ""
