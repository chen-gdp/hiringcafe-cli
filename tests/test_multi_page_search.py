import json

from hiringcafe_cli import search


class BytesResponse:
    def __init__(self, page, last):
        self.body = json.dumps(_page_props(page, last)).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def _hit(object_id):
    return {"objectID": object_id}


def _page_props(page, last, hits=None):
    return {
        "ssrHits": hits if hits is not None else [_hit(str(page * 2)), _hit(str(page * 2 + 1))],
        "ssrPage": page,
        "ssrTotalCount": 10,
        "ssrPageSize": 2,
        "ssrIsLastPage": last,
    }


def args(pages=1, jsonl=False, page=0):
    return type(
        "Args", (), {"query": "python", "page": page, "pages": pages, "jsonl": jsonl, "raw_search_state": None}
    )()


def test_search_pages_fetches_exactly_requested_pages(monkeypatch):
    """Condition: caller requests two pages.

    Expected: pages 0 and 1 are fetched in order, with no page beyond the count.
    """
    calls = []

    def fetch(state, page):
        calls.append(page)
        return _page_props(page, False)

    monkeypatch.setattr(search, "fetch_page", fetch)
    result = search.search_pages("python", 2)
    assert calls == [0, 1]
    assert [job["id"] for job in result] == ["0", "1", "2", "3"]


def test_search_pages_stops_on_last_page(monkeypatch):
    """Condition: first response is already the last page.

    Expected: no second request is made.
    """
    calls = []

    def fetch(state, page):
        calls.append(page)
        return _page_props(page, True, [_hit("only")])

    monkeypatch.setattr(search, "fetch_page", fetch)
    assert [job["id"] for job in search.search_pages("python", 3)] == ["only"]
    assert calls == [0]


def test_search_jsonl_emits_one_valid_job_per_line(monkeypatch, capsys):
    """Condition: JSONL multi-page output.

    Expected: each line is independent valid JSON and source order is preserved.
    """
    monkeypatch.setattr(search, "fetch_page", lambda state, page: _page_props(page, page == 1))
    assert search.run(args(pages=2, jsonl=True), False) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["0", "1", "2", "3"]
