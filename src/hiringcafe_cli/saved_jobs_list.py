"""Authenticated saved-job listing."""

import json
import urllib.error
import urllib.request
import sys
from urllib.request import urlopen

from hiringcafe_cli.auth import store
from hiringcafe_cli.firebase import FirebaseClient, FirebaseAuthError
from hiringcafe_cli.saved_jobs import PIPELINE_STAGES, VALID_STAGES, normalize_saved_job
from hiringcafe_cli.session import SessionStore

FIRESTORE_RUN_QUERY = "https://firestore.googleapis.com/v1/projects/hiringcafe-ec4d6/databases/(default)/documents:runQuery"


class FirestoreError(RuntimeError):
    """Firestore returned a non-success response."""


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
                text = response.read().decode("utf-8")
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
