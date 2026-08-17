"""Integration tests for auth status."""

import json

from hiringcafe_cli import auth, main
from hiringcafe_cli.firebase import FirebaseAuthError, FirebaseTransportError


class FakeFirebaseClient:
    """Configurable FirebaseClient test double."""

    result = None
    calls: list[str] = []

    def refresh(self, token: str) -> dict:
        """Record and apply the configured refresh result."""
        self.calls.append(token)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def fake_refresh(monkeypatch, result):
    """Install the fake client and reset its recording state."""
    FakeFirebaseClient.result = result
    FakeFirebaseClient.calls = []
    monkeypatch.setattr(auth, "FirebaseClient", FakeFirebaseClient)
    return FakeFirebaseClient.calls


def test_auth_status_valid_credential_outputs_metadata_without_tokens(monkeypatch, tmp_path, capsys):
    """Condition: refresh succeeds. Expected: status 0 and no token fields."""
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    (tmp_path / "session.json").write_text(json.dumps({"version": 1, "refreshToken": "stored-refresh"}))
    calls = fake_refresh(monkeypatch, {"idToken": "id-token", "refreshToken": "stored-refresh", "userId": "uid"})

    try:
        main(["auth", "status", "--json"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("status should return an exit code")
    assert calls == ["stored-refresh"]
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"version": 1, "authenticated": True, "userId": "uid"}


def test_auth_status_missing_session_exits_four(monkeypatch, tmp_path, capsys):
    """Condition: no local session exists. Expected: exit 4 without network."""
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    fake_refresh(monkeypatch, AssertionError("must not refresh"))
    try:
        main(["auth", "status"])
    except SystemExit as error:
        assert error.code == 4
    else:
        raise AssertionError("missing session should exit")
    assert "No stored credential" in capsys.readouterr().err


def test_auth_status_distinguishes_rejection_and_transport(monkeypatch, tmp_path, capsys):
    """Condition: Firebase rejects or is unreachable. Expected: exit 5 versus exit 1."""
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    path = tmp_path / "session.json"
    path.write_text(json.dumps({"version": 1, "refreshToken": "stored-refresh"}))
    cases = ((FirebaseAuthError("rejected"), 5), (FirebaseTransportError("offline"), 1))
    for exception, expected in cases:
        fake_refresh(monkeypatch, exception)
        try:
            main(["auth", "status"])
        except SystemExit as error:
            assert error.code == expected
        else:
            raise AssertionError("status should return an exit code")
