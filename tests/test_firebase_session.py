"""Integration tests for Firebase session storage and token exchange."""

import io
import json
import stat

from firebase_doubles import BytesResponse

from hiringcafe_cli.firebase import FIREBASE_WEB_API_KEY, FirebaseClient
from hiringcafe_cli.session import SessionStore


def fake_firebase(monkeypatch, response):
    """Install a recording Firebase transport fake."""
    calls = []

    def post(request, timeout):
        calls.append((request.full_url, request.data, request.headers, timeout))
        return response

    monkeypatch.setattr(FirebaseClient, "post", staticmethod(post))
    return calls


def test_firebase_refresh_exchanges_refresh_token_without_leaking_it(monkeypatch):
    """Condition: refresh succeeds. Expected: metadata and bearer-ready token are returned only in memory."""
    response = BytesResponse(json.dumps({"id_token": "id", "refresh_token": "refresh", "user_id": "uid"}).encode())
    calls = fake_firebase(monkeypatch, response)

    result = FirebaseClient().refresh("refresh-token")

    assert result == {"idToken": "id", "refreshToken": "refresh", "userId": "uid"}
    assert f"key={FIREBASE_WEB_API_KEY}" in calls[0][0]
    assert b"refresh_token=refresh-token" in calls[0][1]
    assert "Authorization" not in calls[0][2]


def test_session_store_writes_owner_only_file_and_loads_session(tmp_path):
    """Condition: a token is imported. Expected: atomic versioned owner-only session."""
    path = tmp_path / "private" / "session.json"
    store = SessionStore(path)

    store.save("refresh-token")

    assert json.loads(path.read_text()) == {"version": 1, "refreshToken": "refresh-token"}
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert store.load().refresh_token == "refresh-token"


def test_session_store_cleans_temporary_file_after_write_failure(tmp_path, monkeypatch):
    """Condition: writing the session fails. Expected: no token-bearing temporary file remains."""
    path = tmp_path / "private" / "session.json"
    store = SessionStore(path)
    monkeypatch.setattr("json.dump", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")))

    try:
        store.save("refresh-token")
    except OSError:
        pass
    else:
        raise AssertionError("write failure should propagate")

    assert list(path.parent.iterdir()) == []


def test_session_store_missing_file_is_none(tmp_path):
    """Condition: session is absent. Expected: no credential and no fabricated session."""
    assert SessionStore(tmp_path / "session.json").load() is None


def test_session_store_rejects_wrong_version_and_corrupt_file(tmp_path):
    """Condition: session is corrupt or future-version. Expected: error rather than token reuse."""
    path = tmp_path / "session.json"
    path.write_text("{}")
    store = SessionStore(path)
    try:
        store.load()
    except ValueError as error:
        assert "invalid session" in str(error)
    else:
        raise AssertionError("invalid session should fail")


def test_import_reads_stdin_and_never_accepts_visible_argv(monkeypatch, tmp_path):
    """Condition: token arrives on stdin. Expected: owner-only session and no partial credential files."""
    fake_firebase(
        monkeypatch,
        BytesResponse(json.dumps({"id_token": "id", "refresh_token": "refresh-token", "user_id": "uid"}).encode()),
    )
    monkeypatch.setattr("sys.stdin", io.StringIO("refresh-token\n"))
    path = tmp_path / "session.json"
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))

    from hiringcafe_cli import main

    try:
        main(["auth", "import"])
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError("auth import should return an exit code")
    assert json.loads(path.read_text())["refreshToken"] == "refresh-token"
    assert len(list(tmp_path.iterdir())) == 1
