"""Integration tests for auth logout."""

from hiringcafe_cli import main


def test_logout_removes_existing_session(monkeypatch, tmp_path, capsys):
    """Condition: session exists. Expected: local-only removal succeeds."""
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    path = tmp_path / "session.json"
    path.write_text('{"version":1,"refreshToken":"stored-refresh"}')
    try:
        main(["auth", "logout"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("logout should return an exit code")
    assert not path.exists()
    assert "Local Firebase session removed" in capsys.readouterr().out


def test_logout_is_idempotent_without_session(monkeypatch, tmp_path, capsys):
    """Condition: session already absent. Expected: logout still succeeds."""
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    try:
        main(["auth", "logout"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("logout should return an exit code")
    assert "No local Firebase session" in capsys.readouterr().out


def test_logout_removal_failure_exits_one(monkeypatch, tmp_path):
    """Condition: deleting an existing session raises OSError. Expected: exit 1."""
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    path = tmp_path / "session.json"
    path.write_text('{"version":1,"refreshToken":"stored-refresh"}')

    def fail_delete():
        raise OSError("read-only filesystem")

    monkeypatch.setattr("hiringcafe_cli.auth.store", lambda: FailingStore(path, fail_delete))
    try:
        main(["auth", "logout"])
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("failed removal should exit")


class FailingStore:
    """SessionStore test double."""

    def __init__(self, path, delete):
        self.path = path
        self._delete = delete

    def load(self):
        """Report an existing session without reading credential data."""
        return object()

    def delete(self):
        """Apply the configured failure."""
        self._delete()
