"""Integration tests for the count command."""

import json

from hiringcafe_cli import main


def test_count_default_prints_one_integer(monkeypatch, capsys):
    """Condition: count succeeds. Expected: exactly ssrTotalCount and newline."""

    class FakeClient:
        def search_page(self, state, page):
            assert state == {"searchQuery": "python"}
            assert page == 0
            return {"ssrTotalCount": 17}

    monkeypatch.setattr("hiringcafe_cli.count.WebClient", lambda: FakeClient())
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
        def search_page(self, state, page):
            return {"ssr_total_count_unused": True, "ssrTotalCount": 3}

    monkeypatch.setattr("hiringcafe_cli.count.WebClient", lambda: FakeClient())
    try:
        main(["count", "python", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("count should return an exit code")
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"version": 1, "query": {"searchState": {"searchQuery": "python"}, "page": 0}, "count": 3}


def test_count_missing_total_is_api_failure(monkeypatch, capsys):
    """Condition: SSR response omits ssrTotalCount. Expected: exit 1 rather than zero."""

    class FakeClient:
        def search_page(self, state, page):
            return {}

    monkeypatch.setattr("hiringcafe_cli.count.WebClient", lambda: FakeClient())
    try:
        main(["count", "python"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("missing count should exit")
    assert capsys.readouterr().out == ""
