"""Integration tests for the anonymous job-description command."""

import json

from hiringcafe_cli import main


def test_job_show_json_normalizes_description_and_safe_metadata(monkeypatch, capsys):
    """Condition: detail response contains job metadata and description. Expected: safe JSON output."""

    class FakeClient:
        def job_description(self, object_id):
            assert object_id == "job-one"
            return {
                "objectID": "job-one",
                "job_information": {"title": "Engineer", "description": "  <p>Build</p>  "},
                "apply_url": "https://example.test/apply",
            }

    monkeypatch.setattr("hiringcafe_cli.job.WebClient", lambda: FakeClient())
    try:
        main(["job", "show", "job-one", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("job show should return an exit code")
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "version": 1,
        "job": {
            "id": "job-one",
            "title": "Engineer",
            "description": "<p>Build</p>",
            "url": "https://example.test/apply",
        },
    }


def test_job_show_missing_id_is_invalid_argument(monkeypatch, capsys):
    """Condition: object ID is omitted. Expected: argparse exits 2 and no network is attempted."""

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


def test_job_show_empty_job_object_is_api_failure(monkeypatch, capsys):
    """Condition: response job is empty. Expected: exit 1 and no JSON stdout."""

    class FakeClient:
        def job_description(self, object_id):
                return {}

    monkeypatch.setenv("HIRINGCAFE_CACHE_HOME", "/tmp/hiringcafe-empty-cache-test")

    monkeypatch.setattr("hiringcafe_cli.job.WebClient", lambda: FakeClient())
    try:
        main(["job", "show", "job-one", "--json"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("empty job should exit")
    assert capsys.readouterr().out == ""
