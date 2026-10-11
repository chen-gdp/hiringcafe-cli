"""Integration tests for the anonymous search command."""

import json

from hiringcafe_cli import main

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 2 of 30 matches)

### [Second](https://hiringcafe.com/job/second?utm_source=claude&utm_campaign=mcp)
**Example Labs**
- Location: Remote
- Workplace: Remote
- Employment type: Full Time
- Seniority: Senior Level
- Posted: 2026-10-01
- Job ID: `job-2`

### [First](https://hiringcafe.com/job/first?utm_source=claude&utm_campaign=mcp)
**Example Systems**
- Location: Austin, TX
- Workplace: Hybrid
- Employment type: Contract
- Seniority: Mid Level
- Posted: 2026-10-02
- Job ID: `job-1`
"""


def make_client(monkeypatch, text):
    """Create a recording fake MCP client."""

    class FakeClient:
        def __init__(self):
            self.calls = []

        def call_mcp_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return text

    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    return client


def test_search_json_emits_one_envelope_and_preserves_order(monkeypatch, capsys):
    """Condition: MCP returns two jobs. Expected: one version-1 JSON envelope in source order."""
    client = make_client(monkeypatch, SEARCH_RESPONSE)

    try:
        main(["search", "python", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("search should return an exit code")

    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == 1
    assert payload["query"] == {"searchState": {"searchQuery": "python"}, "page": 0}
    assert [job["id"] for job in payload["result"]["jobs"]] == ["job-2", "job-1"]
    assert payload["result"]["totalCount"] == 30
    assert payload["result"]["companyCount"] is None
    assert payload["result"]["paginationSupported"] is False
    assert client.calls == [("search_jobs", {"search": "python", "limit": 10})]


def test_search_rejects_invalid_or_unsupported_page_before_network(monkeypatch, capsys):
    """Condition: requested page is unsupported. Expected: exit 2 and no request."""

    def fail_client():
        raise AssertionError("invalid state must not construct a client")

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", fail_client)
    for args in (["search", "python", "--page", "-1"], ["search", "python", "--page", "1"]):
        try:
            main(args)
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError("invalid arguments should exit")
    assert capsys.readouterr().out == ""


def test_search_rejects_multiple_pages_and_raw_filters_before_network(monkeypatch, capsys):
    """Condition: input requests unsupported pagination or filters. Expected: exit 2 without HTTP."""

    def fail_client():
        raise AssertionError("invalid state must not construct a client")

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", fail_client)
    for args in (
        ["search", "python", "--pages", "2"],
        ["search", "--raw-search-state", '{"searchQuery":"python","workplaceTypes":["Remote"]}'],
        ["search", "--raw-search-state", "{}"],
    ):
        try:
            main(args)
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError("unsupported input should exit")
    assert capsys.readouterr().out == ""


def test_search_rejects_unrecognized_mcp_text_without_partial_json(monkeypatch, capsys):
    """Condition: tool returns unexpected Markdown. Expected: exit 1 and no JSON stdout."""
    make_client(monkeypatch, "unrecognized tool response")

    try:
        main(["search", "python", "--json"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("API failure should exit")
    assert capsys.readouterr().out == ""
