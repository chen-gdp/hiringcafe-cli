"""Tests for the opt-in HiringCafe endpoint regression probe."""

import io
import json
from contextlib import redirect_stdout

import pytest

from hiringcafe_cli.probe import extract_next_data, main


def test_probe_extracts_minimized_next_data():
    """Condition: HTML contains one minimized Next.js data script. Expected: its JSON is parsed."""
    payload = {"props": {"pageProps": {"ssrHits": []}}}
    html = f'<html><script id="__NEXT_DATA__">{json.dumps(payload)}</script></html>'

    assert extract_next_data(html) == payload


def test_live_probe_reports_safe_page_and_detail_results(monkeypatch):
    """Condition: LIVE=1 and both pages plus detail succeed. Expected: safe summary and one object ID."""
    pages = []
    for page in (0, 1):
        payload = {
            "props": {
                "pageProps": {
                    "ssrHits": [{"objectID": "job-one"}],
                    "ssrPage": page,
                    "ssrTotalCount": 1,
                    "ssrIsLastPage": True,
                    "initialSearchState": {"searchQuery": "python developer"},
                }
            }
        }
        pages.append(f'<html><script id="__NEXT_DATA__">{json.dumps(payload)}</script></html>'.encode())
    detail = json.dumps({"job": {"job_information": {"description": "<p>Role</p>"}}}).encode()
    responses = [io.BytesIO(body) for body in (*pages, detail)]

    def fake_urlopen(request, timeout):
        return responses.pop(0)

    monkeypatch.setattr("hiringcafe_cli.probe.urlopen", fake_urlopen)
    monkeypatch.setenv("LIVE", "1")
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = main([])

    assert exit_code == 0
    assert "search page 0: ok" in output.getvalue()
    assert "search page 1: ok" in output.getvalue()
    assert "job description job-one: ok" in output.getvalue()


def test_live_probe_does_not_use_network_when_disabled(monkeypatch):
    """Condition: LIVE is unset. Expected: probe skips without opening a URL."""

    def fail_urlopen(request, timeout):
        raise AssertionError("disabled probe must not use the network")

    monkeypatch.setattr("hiringcafe_cli.probe.urlopen", fail_urlopen)
    monkeypatch.delenv("LIVE", raising=False)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = main([])

    assert exit_code == 0
    assert "skipped: set LIVE=1" in output.getvalue()


def test_live_probe_fails_when_required_ssr_key_is_missing(monkeypatch):
    """Condition: live payload omits ssrIsLastPage. Expected: probe fails rather than passing."""
    payload = {
        "props": {
            "pageProps": {
                "ssrHits": [],
                "ssrPage": 0,
                "ssrTotalCount": 0,
            }
        }
    }
    body = f'<html><script id="__NEXT_DATA__">{json.dumps(payload)}</script></html>'.encode()
    monkeypatch.setattr("hiringcafe_cli.probe.urlopen", lambda request, timeout: io.BytesIO(body))
    monkeypatch.setenv("LIVE", "1")

    with pytest.raises(ValueError, match="missing SSR key: ssrIsLastPage"):
        main([])
