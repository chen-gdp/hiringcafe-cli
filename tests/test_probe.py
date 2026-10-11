"""Tests for the opt-in HiringCafe MCP integration probe."""

import io
from contextlib import redirect_stdout

import pytest

from hiringcafe_cli.probe import main

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 1 of 1 matches)

### [Example role](https://hiringcafe.com/job/example?utm_source=claude)
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
    assert output.getvalue() == "search_jobs: ok\nget_job_details: ok\n"
    assert client.calls == [
        ("search_jobs", {"search": "python developer", "limit": 1}),
        ("get_job_details", {"job_id": "job-one"}),
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
