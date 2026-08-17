"""Tests for the executable CLI bootstrap."""

from types import SimpleNamespace

from hiringcafe_cli import __version__


def test_cli_version_prints_package_semantic_version(capsys):
    """Condition: version is requested. Expected: package version and no error output."""
    from hiringcafe_cli import main

    try:
        main(["--version"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("version should request process exit")

    captured = capsys.readouterr()
    assert captured.out == f"hiringcafe {__version__}\n"
    assert captured.err == ""


def test_cli_help_documents_exit_contract(capsys):
    """Condition: help is requested. Expected: the exit-code contract is documented."""
    from hiringcafe_cli import main

    try:
        main(["--help"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("help should request process exit")

    captured = capsys.readouterr()
    assert "Exit codes:" in captured.out
    assert "5 stored credential rejected" in captured.out
    assert captured.err == ""


def test_cli_probe_writes_no_credentials_or_personal_data(capsys):
    """Condition: endpoint probe is disabled. Expected: safe skip message and exit code 0."""
    import os

    from hiringcafe_cli import main

    old_live = os.environ.pop("LIVE", None)
    try:
        main(["probe"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("probe should return a process exit code")
    finally:
        if old_live is not None:
            os.environ["LIVE"] = old_live

    captured = capsys.readouterr()
    assert "skipped: set LIVE=1" in captured.out


def test_cli_firestore_failure_exits_one(monkeypatch, capsys):
    """Condition: saved-job list receives a Firestore API failure. Expected: exit 1 without a traceback."""
    from hiringcafe_cli import main, saved_jobs_list
    from hiringcafe_cli.saved_jobs_list import FirestoreError

    monkeypatch.setattr(
        saved_jobs_list.FirebaseClient,
        "refresh",
        lambda *_: {"idToken": "id-token", "refreshToken": "refresh-token", "userId": "uid"},
    )
    monkeypatch.setattr(
        saved_jobs_list, "store", lambda: SimpleNamespace(load=lambda: SimpleNamespace(refresh_token="refresh-token"))
    )
    monkeypatch.setattr(
        saved_jobs_list,
        "FirestoreClient",
        lambda *_: (_ for _ in ()).throw(FirestoreError("Firestore returned HTTP 403")),
    )
    try:
        main(["saved-jobs", "list"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("Firestore failure should return an exit code")

    captured = capsys.readouterr()
    assert "HTTP 403" in captured.err


def test_cli_rate_limit_exits_three(monkeypatch, capsys):
    """Condition: search ultimately receives HTTP 429. Expected: exit code 3 and a diagnostic."""
    from hiringcafe_cli import main, search
    from hiringcafe_cli.http_client import HireCafeHTTPError

    class FakeClient:
        @staticmethod
        def search_page(state, page):
            raise HireCafeHTTPError("search", 429)

    monkeypatch.setattr(search, "WebClient", FakeClient)
    try:
        main(["search", "engineer"])
    except SystemExit as error:
        assert error.code == 3
    else:
        raise AssertionError("HTTP failure should return a process exit code")

    captured = capsys.readouterr()
    assert "HTTP 429" in captured.err
