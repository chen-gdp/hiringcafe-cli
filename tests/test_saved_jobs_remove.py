import contextlib
import io

from hiringcafe_cli import saved_jobs_remove
from hiringcafe_cli.session import SessionStore
from hiringcafe_cli.firebase import FirebaseAuthError


class BytesResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b"{}"


def args(yes=False):
    return type("Args", (), {"object_id": "job-id", "yes": yes})()


def authenticate(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    SessionStore(config / "session.json").save("refresh-token")
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(config))
    monkeypatch.setattr(
        saved_jobs_remove.FirebaseClient,
        "refresh",
        lambda *_: {"idToken": "id-token", "refreshToken": "refresh-token", "userId": "uid"},
    )


def test_remove_requires_confirmation_before_any_network(tmp_path, monkeypatch):
    """Condition: confirmation is refused.

    Expected: exit 2 with no auth refresh, Firestore read, or mutation.
    """
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(saved_jobs_remove.FirebaseClient, "refresh", lambda *_: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(
        saved_jobs_remove.WebClient, "remove_job", lambda *_: (_ for _ in ()).throw(AssertionError())
    )
    monkeypatch.setattr("sys.stdin", io.StringIO("no\n"))
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_remove.run(args()) == 2


def test_remove_unknown_job_exits_six(tmp_path, monkeypatch):
    """Condition: saved job does not exist.

    Expected: removal exits 6 before marketplace deletion.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(saved_jobs_remove.FirestoreClient, "get", lambda *_: None)
    monkeypatch.setattr(saved_jobs_remove.WebClient, "remove_job", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_remove.run(args(yes=True)) == 6


def test_remove_rejected_credential_exits_five(tmp_path, monkeypatch):
    """Condition: Firebase rejects the stored refresh token.

    Expected: remove exits 5 before Firestore or marketplace use.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(
        saved_jobs_remove.FirebaseClient,
        "refresh",
        lambda *_: (_ for _ in ()).throw(FirebaseAuthError("rejected")),
    )
    monkeypatch.setattr(saved_jobs_remove.FirestoreClient, "get", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_remove.run(args(yes=True)) == 5


def test_remove_reads_stage_then_calls_marketplace_delete(tmp_path, monkeypatch):
    """Condition: --yes removes an existing saved job.

    Expected: current stage is read and only marketplace deletion with should_delete true runs.
    """
    authenticate(tmp_path, monkeypatch)
    document = {
        "fields": {
            "objectID": {"stringValue": "job-id"},
            "owner": {"stringValue": "uid"},
            "stage": {"stringValue": "saved"},
        }
    }
    monkeypatch.setattr(saved_jobs_remove.FirestoreClient, "get", lambda *_: document)
    calls = []
    monkeypatch.setattr(
        saved_jobs_remove.WebClient,
        "remove_job",
        lambda self, object_id, token, stage: calls.append((object_id, token, stage)),
    )
    assert saved_jobs_remove.run(args(yes=True)) == 0
    assert calls == [("job-id", "id-token", "saved")]


def test_remove_marketplace_failure_exits_one(tmp_path, monkeypatch):
    """Condition: marketplace delete fails.

    Expected: removal exits 1 and does not report success.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(
        saved_jobs_remove.FirestoreClient,
        "get",
        lambda *_: {"fields": {"objectID": {"stringValue": "job-id"}, "stage": {"stringValue": "saved"}}},
    )
    monkeypatch.setattr(
        saved_jobs_remove.WebClient,
        "remove_job",
        lambda *_: (_ for _ in ()).throw(ValueError("marketplace failed")),
    )
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_remove.run(args(yes=True)) == 1
