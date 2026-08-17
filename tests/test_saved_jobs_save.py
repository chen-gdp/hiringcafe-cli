import contextlib
import io
import json
import urllib.error

from hiringcafe_cli import saved_jobs_save
from hiringcafe_cli.firebase import FirebaseAuthError
from hiringcafe_cli.saved_jobs_list import FirestoreClient
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


def args(object_id="job-id", stage="saved"):
    return type("Args", (), {"object_id": object_id, "stage": stage})()


def authenticate(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    SessionStore(config / "session.json").save("refresh-token")
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(config))
    monkeypatch.setattr(
        saved_jobs_save.FirebaseClient,
        "refresh",
        lambda *_: {"idToken": "id-token", "refreshToken": "refresh-token", "userId": "uid"},
    )


def test_save_rejects_invalid_arguments_without_network(tmp_path, monkeypatch):
    """Condition: object ID or stage is invalid.

    Expected: save exits 2 before authentication, hydration, or mutation.
    """
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(saved_jobs_save.FirebaseClient, "refresh", lambda *_: (_ for _ in ()).throw(AssertionError()))
    for value in (args(object_id=" "), args(stage="invalid")):
        with contextlib.redirect_stderr(io.StringIO()):
            assert saved_jobs_save.run(value) == 2


def test_save_requires_a_session(tmp_path, monkeypatch):
    """Condition: no stored credential.

    Expected: save exits 4 without a network mutation.
    """
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(FirestoreClient, "save", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_save.run(args()) == 4


def test_save_rejected_credential_exits_five(tmp_path, monkeypatch):
    """Condition: Firebase rejects the stored refresh token.

    Expected: save exits 5 before hydration or mutation.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(
        saved_jobs_save.FirebaseClient,
        "refresh",
        lambda *_: (_ for _ in ()).throw(FirebaseAuthError("rejected")),
    )
    monkeypatch.setattr(
        saved_jobs_save.WebClient, "job_description", lambda *_: (_ for _ in ()).throw(AssertionError())
    )
    with contextlib.redirect_stderr(io.StringIO()):
        assert saved_jobs_save.run(args()) == 5


def test_save_hydrates_writes_firestore_then_marketplace(tmp_path, monkeypatch):
    """Condition: a valid job is saved for the first time.

    Expected: job-description hydration precedes the Firestore merge, marketplace sync follows,
    tracking arrays are removed, and the ID token never reaches output.
    """
    authenticate(tmp_path, monkeypatch)
    calls = []
    detail = BytesResponse(
        json.dumps(
            {
                "job": {
                    "objectID": "job-id",
                    "apply_url": "https://example.invalid/job",
                    "description": "Job description",
                    "job_information": {"title": "Engineer"},
                    "userTrackingArray": [1],
                }
            }
        ).encode()
    )
    marketplace = BytesResponse()

    def firestore_save(self, document_id, values):
        calls.append(("firestore", document_id, values))
        return BytesResponse()

    monkeypatch.setattr(FirestoreClient, "save", firestore_save)

    def urlopen(request, timeout=None):
        calls.append((request.get_method(), request.full_url, request.data))
        if request.full_url.startswith("https://hiringcafe.com/api/job-description"):
            return detail
        if request.full_url == "https://hiringcafe.com/api/updateMarketplaceJobStageForUser":
            return marketplace
        raise AssertionError(request.full_url)

    saved_jobs_save.WebClient.urlopen = staticmethod(urlopen)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert saved_jobs_save.run(args()) == 0
    assert calls[0][0] == "GET"
    assert calls[1][0] == "firestore"
    assert calls[1][1] == "uid_job-id"
    values = calls[1][2]
    assert values["objectID"] == "job-id"
    assert values["owner"] == "uid"
    assert values["stage"] == "saved"
    assert values["isHidden"] is False
    assert values["counted_milestones"] == {}
    assert values["job_information"] == {"title": "Engineer"}
    assert "userTrackingArray" not in values["job_information"]
    assert values["stageHistory"] == {"appendMissingElements": [{"stage": "saved", "at": values["dateSaved"]}]}
    assert calls[2][0] == "POST"
    assert json.loads(calls[2][2]) == {"job_id": "job-id", "user_token": "id-token", "stage": "saved"}
    assert "id-token" not in output.getvalue()


def test_save_skips_marketplace_for_imported_jobs(tmp_path, monkeypatch):
    """Condition: hydrated job has source import.

    Expected: marketplace stage sync is skipped.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(saved_jobs_save.FirestoreClient, "save", lambda *_: BytesResponse())
    monkeypatch.setattr(
        saved_jobs_save.WebClient,
        "job_description",
        lambda self, object_id: {"objectID": object_id, "source": "import"},
    )
    monkeypatch.setattr(
        saved_jobs_save.WebClient, "marketplace_stage", lambda *_: (_ for _ in ()).throw(AssertionError())
    )
    assert saved_jobs_save.run(args()) == 0


def test_save_reports_marketplace_partial_failure(tmp_path, monkeypatch):
    """Condition: Firestore succeeds and marketplace sync fails.

    Expected: save exits 1 and reports a partial failure rather than silent success.
    """
    authenticate(tmp_path, monkeypatch)
    monkeypatch.setattr(FirestoreClient, "save", lambda *_: BytesResponse())

    def urlopen(request, timeout=None):
        if request.full_url.startswith("https://hiringcafe.com/api/job-description"):
            return BytesResponse(json.dumps({"job": {"objectID": "job-id", "description": "Job"}}).encode())
        raise urllib.error.HTTPError(request.full_url, 500, "Server Error", None, None)

    saved_jobs_save.WebClient.urlopen = staticmethod(urlopen)
    errors = io.StringIO()
    with contextlib.redirect_stderr(errors):
        assert saved_jobs_save.run(args()) == 1
    assert "partially" in errors.getvalue()
