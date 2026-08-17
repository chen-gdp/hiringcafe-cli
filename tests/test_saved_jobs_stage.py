import contextlib
import io

from hiringcafe_cli import saved_jobs_stage
from hiringcafe_cli.firebase import FirebaseAuthError
from hiringcafe_cli.session import SessionStore


class BytesResponse:
    def __init__(self, body=b"{}"):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def args(stage="interviewing"):
    return type("Args", (), {"object_id": "job-id", "stage": stage})()


def authenticate(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    SessionStore(config / "session.json").save("refresh-token")
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(config))
    monkeypatch.setattr(
        saved_jobs_stage.FirebaseClient,
        "refresh",
        lambda *_: {"idToken": "id-token", "refreshToken": "refresh-token", "userId": "uid"},
    )


def firestore_document(stage="saved", first_saved_at=None):
    fields = {
        "objectID": {"stringValue": "job-id"},
        "owner": {"stringValue": "uid"},
        "dateSaved": {"timestampValue": "2024-01-01T00:00:00Z"},
        "stage": {"stringValue": stage},
        "isHidden": {"booleanValue": False},
    }
    if first_saved_at is not None:
        fields["firstSavedAt"] = {"timestampValue": first_saved_at}
    return {"name": "projects/p/databases/(default)/documents/savedJobs/uid_job-id", "fields": fields}


def test_stage_rejects_invalid_stage_and_missing_session(tmp_path, monkeypatch):
    """Condition: invalid stage or no stored credential.

    Expected: exits 2/4 respectively before Firestore or marketplace network use.
    """
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(saved_jobs_stage.FirestoreClient, "get", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_stage.run(args("invalid")) == 2
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_stage.run(args()) == 4


def test_stage_unknown_job_exits_six(tmp_path, monkeypatch):
    """Condition: no savedJobs document exists.

    Expected: stage exits 6 as a missing prerequisite.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(saved_jobs_stage.FirestoreClient, "get", lambda *_: None)
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_stage.run(args()) == 6


def test_stage_rejected_credential_exits_five(tmp_path, monkeypatch):
    """Condition: Firebase rejects the stored refresh token.

    Expected: stage exits 5 before Firestore or marketplace mutation.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(
        saved_jobs_stage.FirebaseClient,
        "refresh",
        lambda *_: (_ for _ in ()).throw(FirebaseAuthError("rejected")),
    )
    monkeypatch.setattr(saved_jobs_stage.FirestoreClient, "get", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_stage.run(args()) == 5


def test_stage_orders_marketplace_firestore_then_old_list_cleanup(tmp_path, monkeypatch):
    """Condition: saved job moves from saved to interviewing without firstSavedAt.

    Expected: marketplace sync runs first, Firestore updates history and firstSavedAt,
    then old-list cleanup runs for the saved stage.
    """
    authenticate(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(saved_jobs_stage.FirestoreClient, "get", lambda *_: firestore_document())

    def update(self, document_id, values):
        calls.append(("firestore", document_id, values))

    monkeypatch.setattr(saved_jobs_stage.FirestoreClient, "update", update)

    def marketplace(self, object_id, id_token, stage):
        calls.append(("marketplace", object_id, id_token, stage))

    monkeypatch.setattr(saved_jobs_stage.WebClient, "marketplace_stage", marketplace)

    def remove(self, object_id, id_token, stage):
        calls.append(("remove", object_id, id_token, stage))

    monkeypatch.setattr(saved_jobs_stage.WebClient, "remove_from_list", remove)
    assert saved_jobs_stage.run(args()) == 0
    assert calls[0] == ("marketplace", "job-id", "id-token", "interviewing")
    document_id, values = calls[1][1:]
    assert document_id == "uid_job-id"
    assert values["stage"] == "interviewing"
    assert values["stageHistory"] == {"appendMissingElements": [{"stage": "interviewing", "at": values["dateSaved"]}]}
    assert values["firstSavedAt"] == "2024-01-01T00:00:00Z"
    assert calls[2] == ("remove", "job-id", "id-token", "saved")


def test_stage_skips_old_list_cleanup_for_nonlegacy_stage(tmp_path, monkeypatch):
    """Condition: old stage is interviewing and new stage is offer.

    Expected: marketplace and Firestore update run, but removeJobFromList is skipped.
    """
    authenticate(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(
        saved_jobs_stage.FirestoreClient, "get", lambda *_: firestore_document("interviewing", "2023-01-01T00:00:00Z")
    )
    monkeypatch.setattr(
        saved_jobs_stage.FirestoreClient,
        "update",
        lambda self, document_id, values: calls.append(("firestore", document_id, values)),
    )
    monkeypatch.setattr(
        saved_jobs_stage.WebClient,
        "marketplace_stage",
        lambda self, object_id, token, stage: calls.append(("marketplace", stage)),
    )
    monkeypatch.setattr(
        saved_jobs_stage.WebClient,
        "remove_from_list",
        lambda *_: (_ for _ in ()).throw(AssertionError()),
    )
    assert saved_jobs_stage.run(args("offer")) == 0
    assert calls[0] == ("marketplace", "offer")
    assert calls[1][2].get("firstSavedAt") is None
