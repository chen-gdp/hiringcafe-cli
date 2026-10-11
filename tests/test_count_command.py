"""Integration tests for the count command."""

import json

from hiringcafe_cli import main


def test_count_default_prints_one_integer(monkeypatch, capsys):
    """Condition: count succeeds. Expected: exactly the MCP result count and newline."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            assert name == "search_jobs"
            assert arguments == {"search": "python", "limit": 10}
            return (
                "## HiringCafe job results (showing 1 of 17 matches)\n\n"
                "### [Role](https://hiringcafe.com/job/role)\n- Job ID: `job-one`"
            )

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: FakeClient())
    try:
        main(["count", "python"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("count should return an exit code")
    assert capsys.readouterr().out == "17\n"


def test_count_json_includes_request_and_count(monkeypatch, capsys):
    """Condition: JSON mode succeeds. Expected: page is always zero and count is emitted."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return (
                "## HiringCafe job results (showing 1 of 3 matches)\n\n"
                "### [Role](https://hiringcafe.com/job/role)\n- Job ID: `job-one`"
            )

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: FakeClient())
    try:
        main(["count", "python", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("count should return an exit code")
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"version": 1, "query": {"searchState": {"searchQuery": "python"}, "page": 0}, "count": 3}


def test_count_prints_zero_for_explicit_no_results(monkeypatch, capsys):
    """Condition: MCP returns its documented no-results message. Expected: count prints zero."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return "No jobs matched that search on HiringCafe. Try broadening the location."

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: FakeClient())
    try:
        main(["count", "python"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("count should return an exit code")
    assert capsys.readouterr().out == "0\n"


def test_count_missing_total_is_api_failure(monkeypatch, capsys):
    """Condition: MCP response omits its count. Expected: exit 1 rather than zero."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return "unexpected HiringCafe response"

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: FakeClient())
    try:
        main(["count", "python"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("missing count should exit")
    assert capsys.readouterr().out == ""
