"""Integration tests for the anonymous search command."""

import json

from hiringcafe_cli import main


def make_client(monkeypatch, properties):
    """Create a recording fake client."""

    class FakeClient:
        def __init__(self):
            self.calls = []

        def search_page(self, state, page):
            self.calls.append((state, page))
            return properties

    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    return client


def test_search_json_emits_one_envelope_and_preserves_order(monkeypatch, capsys):
    """Condition: SSR returns two valid hits in source order. Expected: one version-1 JSON document."""
    make_client(
        monkeypatch,
        {
            "ssrHits": [
                {"objectID": "job-2", "job_information": {"title": "Second"}},
                {"objectID": "job-1", "job_information": {"title": "First"}},
            ],
            "ssrPage": 1,
            "ssrTotalCount": 2,
            "ssrCompanyCount": 2,
            "ssrPageSize": 40,
            "ssrIsLastPage": True,
        },
    )

    try:
        main(["search", "python", "--page", "1", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("search should return an exit code")

    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == 1
    assert payload["query"] == {"searchState": {"searchQuery": "python"}, "page": 1}
    assert [job["id"] for job in payload["result"]["jobs"]] == ["job-2", "job-1"]
    assert payload["result"]["totalCount"] == 2


def test_search_rejects_invalid_page_before_network(monkeypatch, capsys):
    """Condition: page is negative. Expected: exit 2 and no request."""

    def fail_client():
        raise AssertionError("invalid state must not construct a client")

    monkeypatch.setattr("hiringcafe_cli.search.WebClient", fail_client)
    try:
        main(["search", "python", "--page", "-1"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("invalid arguments should exit")
    assert capsys.readouterr().out == ""


def test_search_ssr_error_and_missing_id_are_api_failures(monkeypatch, capsys):
    """Condition: SSR reports error or hit lacks objectID. Expected: exit 1 and no JSON stdout."""
    make_client(monkeypatch, {"ssrError": "upstream"})
    try:
        main(["search", "python", "--json"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("API failure should exit")
    assert capsys.readouterr().out == ""
