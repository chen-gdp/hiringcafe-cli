import json

import pytest

from hiringcafe_cli import search
from hiringcafe_cli.search_state import InvalidSearchState

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 2 of 30 matches)

### [First](https://hiringcafe.com/job/first?utm_source=claude)
- Job ID: `job-one`

### [Second](https://hiringcafe.com/job/second?utm_source=claude)
- Job ID: `job-two`
"""


def args(pages=1, jsonl=False, page=0):
    """Build the namespace consumed by the search command."""
    return type(
        "Args", (), {"query": "python", "page": page, "pages": pages, "jsonl": jsonl, "raw_search_state": None}
    )()


def test_search_rejects_unsupported_pages_without_http(monkeypatch):
    """Condition: caller requests multiple pages. Expected: fail before constructing an HTTP client."""

    def fail_client():
        raise AssertionError("unsupported pagination must not make a request")

    monkeypatch.setattr(search, "WebClient", fail_client)
    with pytest.raises(InvalidSearchState, match="does not provide pagination"):
        search.run(args(pages=2), False)


def test_search_jsonl_emits_one_valid_job_per_line(monkeypatch, capsys):
    """Condition: caller requests JSONL. Expected: each MCP result is an independent JSON line."""

    class FakeClient:
        def __init__(self):
            self.calls = []

        def call_mcp_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return SEARCH_RESPONSE

    client = FakeClient()
    monkeypatch.setattr(search, "WebClient", lambda: client)

    assert search.run(args(jsonl=True), False) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["job-one", "job-two"]
    assert client.calls == [("search_jobs", {"search": "python", "limit": 10})]
