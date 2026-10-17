"""Authenticated saved-job listing."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from urllib.request import urlopen

from hiringcafe_cli.auth import store
from hiringcafe_cli.firebase import FirebaseClient
from hiringcafe_cli.io_limits import read_limited
from hiringcafe_cli.saved_jobs import PIPELINE_STAGES, VALID_STAGES, encode_firestore_value, normalize_saved_job

FIRESTORE_DOCUMENTS = "https://firestore.googleapis.com/v1/projects/hiringcafe-ec4d6/databases/(default)/documents"
FIRESTORE_RUN_QUERY = f"{FIRESTORE_DOCUMENTS}:runQuery"
FIRESTORE_RESOURCE = "projects/hiringcafe-ec4d6/databases/(default)/documents"


class FirestoreError(RuntimeError):
    """Firestore returned a non-success response."""


class FirestoreConflict(FirestoreError):
    """A saved job changed or disappeared before the write completed."""


def _saved_job_path(document_id: str) -> str:
    """Validate a single document ID and qualify it with its collection."""
    if (
        not isinstance(document_id, str)
        or not document_id
        or document_id in {".", ".."}
        or "/" in document_id
        or any(ord(character) < 32 for character in document_id)
        or len(document_id.encode("utf-8")) > 1500
    ):
        raise ValueError("invalid saved-job document ID")
    return f"savedJobs/{document_id}"


def _json_object(text: str) -> dict:
    """Parse a required Firestore JSON object."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("invalid Firestore JSON response") from error
    if not isinstance(value, dict):
        raise ValueError("Firestore response is not an object")
    return value


class FirestoreClient:
    """Client for the captured savedJobs REST query."""

    urlopen = staticmethod(urlopen)

    def __init__(self, id_token: str) -> None:
        self.id_token = id_token

    def list(self, owner: str, stage: str | None = None) -> list[dict]:
        """List the owner's pipeline saved jobs, newest first."""
        stage_filter = {
            "field": {"fieldPath": "stage"},
            "op": "IN",
            "value": {"arrayValue": {"values": [{"stringValue": stage} for stage in PIPELINE_STAGES]}},
        }
        if stage is not None:
            stage_filter = {"field": {"fieldPath": "stage"}, "op": "EQUAL", "value": {"stringValue": stage}}
        body = json.dumps(
            {
                "structuredQuery": {
                    "from": [{"collectionId": "savedJobs"}],
                    "where": {
                        "compositeFilter": {
                            "op": "AND",
                            "filters": [
                                {
                                    "fieldFilter": {
                                        "field": {"fieldPath": "owner"},
                                        "op": "EQUAL",
                                        "value": {"stringValue": owner},
                                    }
                                },
                                {"fieldFilter": stage_filter},
                            ],
                        }
                    },
                    "orderBy": [{"field": {"fieldPath": "dateSaved"}, "direction": "DESCENDING"}],
                    "limit": 20,
                }
            },
            separators=(",", ":"),
        ).encode()
        request = urllib.request.Request(
            FIRESTORE_RUN_QUERY,
            data=body,
            headers={
                "Authorization": f"Bearer {self.id_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.urlopen(request, timeout=30) as response:
                text = read_limited(response, "Firestore list").decode("utf-8")
        except urllib.error.HTTPError as error:
            raise FirestoreError(f"Firestore returned HTTP {error.code}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise FirestoreError("Firestore transport failed") from error
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError("invalid Firestore JSON response") from error
        if not isinstance(payload, list):
            raise ValueError("Firestore runQuery response is not an array")
        documents = [entry.get("document", {}) for entry in payload if isinstance(entry, dict) and "document" in entry]
        if any(not isinstance(document, dict) for document in documents):
            raise ValueError("Firestore runQuery document is not an object")
        jobs = [normalize_saved_job(document) for document in documents]
        jobs.sort(key=lambda job: job["documentId"])
        return sorted(jobs, key=lambda job: job["savedAt"], reverse=True)

    def _request(self, method: str, path: str, body: bytes | None = None) -> dict:
        """Issue a Firestore REST request and return its JSON object response."""
        headers = {"Authorization": f"Bearer {self.id_token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        suffix = path if path == ":commit" else f"/{path}"
        request = urllib.request.Request(f"{FIRESTORE_DOCUMENTS}{suffix}", data=body, headers=headers, method=method)
        try:
            with self.urlopen(request, timeout=30) as response:
                text = read_limited(response, "Firestore").decode("utf-8")
        except urllib.error.HTTPError as error:
            status = None
            if error.code == 400:
                try:
                    failure = _json_object(read_limited(error, "Firestore error").decode("utf-8"))
                    detail = failure.get("error")
                    status = detail.get("status") if isinstance(detail, dict) else None
                except (ValueError, OSError):
                    pass
            if error.code in {409, 412} or status == "FAILED_PRECONDITION":
                raise FirestoreConflict("saved job changed; refresh state before retrying") from error
            raise FirestoreError(f"Firestore returned HTTP {error.code}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise FirestoreError("Firestore transport failed") from error
        return _json_object(text)

    def save(self, document_id: str, values: dict) -> dict:
        """Merge-write one savedJobs document."""
        return self._write(document_id, values)

    def _write(self, document_id: str, values: dict, precondition: dict | None = None) -> dict:
        """Commit a field merge and history union as one atomic Firestore write."""
        path = _saved_job_path(document_id)
        fields = {
            key: encode_firestore_value(value)
            for key, value in values.items()
            if value is not None and key != "stageHistory"
        }
        write = {
            "update": {"name": f"{FIRESTORE_RESOURCE}/{path}", "fields": fields},
            "updateMask": {"fieldPaths": ["`" + key.replace("\\", "\\\\").replace("`", "\\`") + "`" for key in fields]},
        }
        history = values.get("stageHistory")
        if history is not None:
            if not isinstance(history, list) or not history:
                raise ValueError("stage history append must be a nonempty list")
            write["updateTransforms"] = [
                {"fieldPath": "stageHistory", "appendMissingElements": encode_firestore_value(history)["arrayValue"]}
            ]
        if precondition is not None:
            write["currentDocument"] = precondition
        try:
            payload = self._request("POST", ":commit", json.dumps({"writes": [write]}, separators=(",", ":")).encode())
        except FirestoreError as error:
            if precondition is not None and getattr(error.__cause__, "code", None) == 404:
                raise FirestoreConflict("saved job disappeared; refresh state before retrying") from error
            raise
        if not isinstance(payload.get("writeResults"), list) or len(payload["writeResults"]) != 1:
            raise ValueError("invalid Firestore commit response")
        return payload

    def get(self, document_id: str) -> dict | None:
        """Read one savedJobs document, returning None when absent."""
        try:
            return self._request("GET", urllib.parse.quote(_saved_job_path(document_id), safe="/"))
        except FirestoreError as error:
            if getattr(error, "__cause__", None) and getattr(error.__cause__, "code", None) == 404:
                return None
            raise

    def update(self, document_id: str, values: dict, update_time: str | None = None) -> dict:
        """Merge-update an existing saved job, optionally guarded by its read version.

        Args:
            document_id: Single savedJobs document ID.
            values: Fields to merge; stageHistory is appended atomically.
            update_time: Version from the preceding GET, when available.

        Returns:
            Validated commit response.

        Raises:
            FirestoreConflict: If the document changed or no longer exists.
        """
        precondition = {"updateTime": update_time} if update_time is not None else {"exists": True}
        return self._write(document_id, values, precondition)


def run(argv, json_output: bool = False) -> int:
    """Execute the saved-jobs list command."""
    stage = argv.stage
    if stage is not None and stage not in VALID_STAGES:
        print("hiringcafe: invalid stage", file=sys.stderr)
        return 2
    session = store().load()
    if session is None:
        print("hiringcafe: no stored credential", file=sys.stderr)
        return 4
    credentials = FirebaseClient().refresh(session.refresh_token)
    jobs = FirestoreClient(credentials["idToken"]).list(credentials["userId"], stage)
    if json_output:
        print(json.dumps({"version": 1, "jobs": jobs}, separators=(",", ":")))
    else:
        for job in jobs:
            print(f"{job['id']}\t{job['savedAt']}\t{job['stage']}")
    return 0
