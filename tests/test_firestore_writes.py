"""Transport regression tests for collection paths and atomic saved-job writes."""

import io
import json
from datetime import datetime, timezone
from urllib.error import HTTPError

import pytest

from hiringcafe_cli import saved_jobs_stage
from hiringcafe_cli.saved_jobs import SavedJobError, encode_firestore_value
from hiringcafe_cli.saved_jobs_list import FIRESTORE_DOCUMENTS, FirestoreClient, FirestoreConflict


def test_firestore_get_qualifies_and_encodes_document_id(monkeypatch):
    """Condition: an ID includes URL metacharacters. Expected: one encoded savedJobs document GET."""
    requests = []

    def get(request, timeout):
        requests.append(request)
        return io.BytesIO(b'{"fields":{}}')

    monkeypatch.setattr(FirestoreClient, "urlopen", staticmethod(get))
    assert FirestoreClient("synthetic-token").get("uid_job?#") == {"fields": {}}
    assert requests[0].full_url == f"{FIRESTORE_DOCUMENTS}/savedJobs/uid_job%3F%23"
    assert requests[0].method == "GET"


@pytest.mark.parametrize("document_id", ["", ".", "..", "other/job", "job\n", "a" * 1501])
def test_firestore_rejects_invalid_document_paths_before_http(monkeypatch, document_id):
    """Condition: an ID is not one valid segment. Expected: no read or mutation request."""
    monkeypatch.setattr(FirestoreClient, "urlopen", staticmethod(lambda *_: pytest.fail("unexpected HTTP")))
    client = FirestoreClient("synthetic-token")
    for operation in (lambda: client.get(document_id), lambda: client.save(document_id, {"stage": "saved"})):
        with pytest.raises(ValueError, match="document ID"):
            operation()


def test_firestore_save_atomically_merges_and_appends_typed_history(monkeypatch):
    """Condition: a saved job has prior history. Expected: merge fields and atomically append history."""
    requests = []
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def commit(request, timeout):
        requests.append(request)
        return io.BytesIO(b'{"writeResults":[{"updateTime":"2026-01-01T00:00:01Z"}]}')

    monkeypatch.setattr(FirestoreClient, "urlopen", staticmethod(commit))
    FirestoreClient("synthetic-token").save(
        "uid_job", {"stage": "saved", "dateSaved": at, "stageHistory": [{"stage": "saved", "at": at}]}
    )
    assert len(requests) == 1
    request = requests[0]
    assert request.full_url == f"{FIRESTORE_DOCUMENTS}:commit"
    assert request.method == "POST"
    write = json.loads(request.data)["writes"][0]
    assert write["update"]["name"].endswith("/documents/savedJobs/uid_job")
    assert write["update"]["fields"] == {
        "stage": {"stringValue": "saved"},
        "dateSaved": {"timestampValue": "2026-01-01T00:00:00Z"},
    }
    assert set(write["updateMask"]["fieldPaths"]) == {"`stage`", "`dateSaved`"}
    assert write["updateTransforms"] == [
        {
            "fieldPath": "stageHistory",
            "appendMissingElements": {
                "values": [
                    {
                        "mapValue": {
                            "fields": {
                                "stage": {"stringValue": "saved"},
                                "at": {"timestampValue": "2026-01-01T00:00:00Z"},
                            }
                        }
                    }
                ]
            },
        }
    ]
    assert "currentDocument" not in write


@pytest.mark.parametrize("update_time", [None, "2026-01-01T00:00:00Z"])
def test_firestore_update_requires_existing_read_version(monkeypatch, update_time):
    """Condition: a stage document can change concurrently. Expected: server enforces existence/read version."""
    requests = []

    def commit(request, timeout):
        requests.append(request)
        return io.BytesIO(b'{"writeResults":[{}]}')

    monkeypatch.setattr(FirestoreClient, "urlopen", staticmethod(commit))
    FirestoreClient("synthetic-token").update("uid_job", {"stage": "hidden", "isHidden": True}, update_time)
    write = json.loads(requests[0].data)["writes"][0]
    assert write["currentDocument"] == ({"updateTime": update_time} if update_time else {"exists": True})


@pytest.mark.parametrize("status", [400, 404, 409, 412, 403])
def test_firestore_write_failures_never_retry(monkeypatch, status):
    """Condition: a commit fails. Expected: a single attempt; concurrency errors have a distinct type."""
    requests = []

    def fail(request, timeout):
        requests.append(request)
        body = io.BytesIO(b'{"error":{"status":"FAILED_PRECONDITION"}}')
        raise HTTPError(request.full_url, status, "synthetic failure", None, body)

    monkeypatch.setattr(FirestoreClient, "urlopen", staticmethod(fail))
    with pytest.raises(Exception) as error:
        FirestoreClient("synthetic-token").update("uid_job", {"stage": "hidden"})
    assert isinstance(error.value, FirestoreConflict) is (status in {400, 404, 409, 412})
    assert len(requests) == 1


def test_firestore_404_is_missing_document(monkeypatch):
    """Condition: the collection-qualified GET returns 404. Expected: missing prerequisite, not an empty document."""

    def missing(request, timeout):
        raise HTTPError(request.full_url, 404, "Not Found", None, None)

    monkeypatch.setattr(FirestoreClient, "urlopen", staticmethod(missing))
    assert FirestoreClient("synthetic-token").get("uid_job") is None


def test_firestore_timestamp_requires_timezone():
    """Condition: a timestamp lacks timezone. Expected: reject ambiguous data before writing."""
    with pytest.raises(SavedJobError, match="timezone"):
        encode_firestore_value(datetime(2026, 1, 1))


@pytest.mark.parametrize("stage", ["hidden", "saved"])
def test_stage_transition_updates_visibility_and_passes_read_version(monkeypatch, stage):
    """Condition: a job is hidden/unhidden. Expected: visibility agrees with stage and version guards the write."""
    from types import SimpleNamespace

    document = {
        "updateTime": "2026-01-01T00:00:00Z",
        "fields": {"stage": {"stringValue": "offer"}, "dateSaved": {"timestampValue": "2025-01-01T00:00:00Z"}},
    }
    calls = []
    monkeypatch.setattr(
        saved_jobs_stage, "store", lambda: SimpleNamespace(load=lambda: SimpleNamespace(refresh_token="x"))
    )
    monkeypatch.setattr(saved_jobs_stage.FirebaseClient, "refresh", lambda *_: {"idToken": "x", "userId": "uid"})
    monkeypatch.setattr(FirestoreClient, "get", lambda *_: document)
    monkeypatch.setattr(
        FirestoreClient, "update", lambda self, doc_id, values, version: calls.append((values, version))
    )
    monkeypatch.setattr(saved_jobs_stage.WebClient, "marketplace_stage", lambda *_: None)
    saved_jobs_stage.change_stage("job", stage)
    assert calls[0][0]["isHidden"] is (stage == "hidden")
    assert calls[0][1] == document["updateTime"]


def test_stage_conflict_exits_six(monkeypatch, capsys):
    """Condition: a guarded Firestore write conflicts. Expected: CLI reports prerequisite/conflict exit 6."""
    from types import SimpleNamespace

    monkeypatch.setattr(saved_jobs_stage, "store", lambda: SimpleNamespace(load=lambda: object()))
    monkeypatch.setattr(
        saved_jobs_stage, "change_stage", lambda *_: (_ for _ in ()).throw(FirestoreConflict("changed"))
    )
    assert saved_jobs_stage.run(SimpleNamespace(object_id="job", stage="saved")) == 6
    assert "completed partially" in capsys.readouterr().err
