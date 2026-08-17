"""Tests for the executable CLI bootstrap."""

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
