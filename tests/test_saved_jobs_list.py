import contextlib
import io
import json
import urllib.error

from hiringcafe_cli import saved_jobs_list
from hiringcafe_cli.saved_jobs import PIPELINE_STAGES
from hiringcafe_cli.saved_jobs_list import FirestoreClient, FirestoreError
from hiringcafe_cli.session import SessionStore


class BytesResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body


def document(document_id, object_id, saved_at, stage):
    return {
        "name": f"projects/p/databases/(default)/documents/savedJobs/{document_id}",
        "fields": {
            "objectID": {"stringValue": object_id},
            "owner": {"stringValue": "uid"},
            "dateSaved": {"timestampValue": saved_at},
            "stage": {"stringValue": stage},
            "isHidden": {"booleanValue": stage == "hidden"},
        },
    }


def args(stage=None, as_json=False):
    return type("Args", (), {"stage": stage, "json": as_json})()


def test_list_requires_a_session(tmp_path, monkeypatch):
    """Condition: no stored credential.

    Expected: list exits 4 without refreshing a token or querying Firestore.
    """
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(FirestoreClient, "list", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()) as errors:
        assert saved_jobs_list.run(args(), False) == 4
    assert "no stored credential" in errors.getvalue()


def test_list_rejects_invalid_stage_before_auth(tmp_path, monkeypatch):
    """Condition: caller supplies an unsupported stage.

    Expected: list exits 2 before reading the session or using the network.
    """
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(saved_jobs_list.FirebaseClient, "refresh", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()) as errors:
        assert saved_jobs_list.run(args("invalid"), False) == 2
    assert "invalid stage" in errors.getvalue()


def test_list_queries_firestore_and_orders_deterministically(tmp_path, monkeypatch):
    """Condition: an authenticated user has two jobs saved at the same time.

    Expected: the captured owner/pipeline query is used and document ID breaks ties.
    """
    config = tmp_path / "config"
    config.mkdir()
    SessionStore(config / "session.json").save("refresh-token")
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(config))
    monkeypatch.setattr(
        saved_jobs_list.FirebaseClient,
        "refresh",
        lambda *_: {"idToken": "id-token", "refreshToken": "refresh-token", "userId": "uid"},
    )
    requests = []

    def urlopen(request, timeout=None):
        requests.append(request)
        return BytesResponse(
            json.dumps(
                [
                    {"document": document("uid_b", "b", "2024-01-01T00:00:00Z", "applied")},
                    {"document": document("uid_a", "a", "2024-01-01T00:00:00Z", "saved")},
                ]
            ).encode()
        )

    FirestoreClient.urlopen = staticmethod(urlopen)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert saved_jobs_list.run(args(as_json=True), True) == 0
    assert requests[0].full_url == saved_jobs_list.FIRESTORE_RUN_QUERY
    assert requests[0].method == "POST"
    body = json.loads(requests[0].data.decode())
    filters = body["structuredQuery"]["where"]["compositeFilter"]["filters"]
    assert filters[0] == {
        "fieldFilter": {
            "field": {"fieldPath": "owner"},
            "op": "EQUAL",
            "value": {"stringValue": "uid"},
        }
    }
    assert filters[1] == {
        "fieldFilter": {
            "field": {"fieldPath": "stage"},
            "op": "IN",
            "value": {"arrayValue": {"values": [{"stringValue": stage} for stage in PIPELINE_STAGES]}},
        }
    }
    assert body["structuredQuery"]["orderBy"] == [{"field": {"fieldPath": "dateSaved"}, "direction": "DESCENDING"}]
    assert body["structuredQuery"]["limit"] == 20
    payload = json.loads(output.getvalue())
    assert [job["id"] for job in payload["jobs"]] == ["a", "b"]
    assert payload["jobs"][0]["documentId"] == "uid_a"


def test_list_permission_denial_is_an_api_failure(tmp_path, monkeypatch):
    """Condition: Firestore rejects the authenticated query.

    Expected: permission denial exits 1 rather than returning an empty list.
    """
    config = tmp_path / "config"
    config.mkdir()
    SessionStore(config / "session.json").save("refresh-token")
    monkeypatch.setenv("HIRINGCAFE_CONFIG_HOME", str(config))
    monkeypatch.setattr(
        saved_jobs_list.FirebaseClient,
        "refresh",
        lambda *_: {"idToken": "id-token", "refreshToken": "refresh-token", "userId": "uid"},
    )

    def urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", None, None)

    FirestoreClient.urlopen = staticmethod(urlopen)
    try:
        saved_jobs_list.run(args(), False)
    except FirestoreError as error:
        assert "HTTP 403" in str(error)
    else:
        raise AssertionError("permission denial must not be treated as an empty list")
