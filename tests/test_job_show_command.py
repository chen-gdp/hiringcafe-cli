"""Integration tests for the anonymous MCP job-detail command."""

import json

from hiringcafe_cli import main

DETAIL_RESPONSE = """\
# [Engineer](https://hiringcafe.com/job/job-one?utm_source=claude)
- **Job ID:** `job-one`
- **View & apply:** [Apply](https://jobs.example.invalid/apply)
## Requirements summary
Build services.
## Full description
  <p>Build reliable systems.</p>
"""


def test_job_show_json_preserves_apply_and_attribution_links(monkeypatch, capsys):
    """Condition: verified detail Markdown is returned. Expected: safe normalized JSON."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            assert name == "get_job_details"
            assert arguments == {"job_id": "job-one"}
            return DETAIL_RESPONSE

    monkeypatch.setattr("hiringcafe_cli.job.WebClient", FakeClient)
    try:
        main(["job", "show", "job-one", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("job show should return an exit code")

    assert json.loads(capsys.readouterr().out) == {
        "version": 1,
        "job": {
            "id": "job-one",
            "title": "Engineer",
            "description": "<p>Build reliable systems.</p>",
            "url": "https://jobs.example.invalid/apply",
            "hiringCafeUrl": "https://hiringcafe.com/job/job-one?utm_source=claude",
        },
    }


def test_job_show_defaults_to_attributed_hiringcafe_link(monkeypatch, capsys):
    """Condition: the detail has no employer apply link. Expected: human output keeps the first-party link."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return DETAIL_RESPONSE.replace("- **View & apply:** [Apply](https://jobs.example.invalid/apply)\n", "")

    monkeypatch.setattr("hiringcafe_cli.job.WebClient", FakeClient)
    try:
        main(["job", "show", "job-one"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("job show should return an exit code")

    assert "https://hiringcafe.com/job/job-one?utm_source=claude" in capsys.readouterr().out


def test_job_show_missing_id_is_invalid_argument(monkeypatch, capsys):
    """Condition: object ID is omitted. Expected: invalid-input exit and no network request."""

    class FailClient:
        def __init__(self):
            raise AssertionError("empty ID must not construct client")

    monkeypatch.setattr("hiringcafe_cli.job.WebClient", FailClient)
    try:
        main(["job", "show", ""])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("missing ID should exit")
    assert capsys.readouterr().out == ""


def test_job_show_rejects_empty_or_malformed_mcp_response(tmp_path, monkeypatch, capsys):
    """Condition: detail text has no verified shape. Expected: exit 1 and no partial JSON."""

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return "unexpected response"

    monkeypatch.setenv("HIRINGCAFE_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr("hiringcafe_cli.job.WebClient", FakeClient)
    try:
        main(["job", "show", "job-one", "--json"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("malformed response should exit")
    assert capsys.readouterr().out == ""


def test_job_show_caches_only_email_scrubbed_content(tmp_path, monkeypatch):
    """Condition: detail includes encoded and plain email strings. Expected: cache stores only scrubbed text."""
    from hiringcafe_cli.job import show

    response = DETAIL_RESPONSE + "\nContact: person@example.invalid\nEncoded: person&#64;example.invalid"

    class FakeClient:
        def call_mcp_tool(self, name, arguments):
            return response

    monkeypatch.setenv("HIRINGCAFE_CACHE_HOME", str(tmp_path))
    monkeypatch.setattr("hiringcafe_cli.job.WebClient", FakeClient)
    show("job-one")

    cached_files = list(tmp_path.rglob("*.json"))
    assert len(cached_files) == 1
    cached_text = cached_files[0].read_text(encoding="utf-8")
    assert "person@example.invalid" not in cached_text
    assert "person&#64;example.invalid" not in cached_text
    assert "[email redacted]" in cached_text
