"""Authenticated saved-job listing."""

import json
import urllib.error
import urllib.parse
import urllib.request
import sys
from urllib.request import urlopen

from hiringcafe_cli.auth import store
from hiringcafe_cli.firebase import FirebaseClient, FirebaseAuthError
from hiringcafe_cli.saved_jobs import PIPELINE_STAGES, VALID_STAGES, normalize_saved_job
from hiringcafe_cli.session import SessionStore

FIRESTORE_BASE = "https://firestore.googleapis.com/v1/projects/hiringcafe-ec4d/databases/(default)/documents/savedJobs"


class FirestoreError(RuntimeError):
    """Firestore returned a non-success response."""


class FirestoreClient:
    """Client for the captured savedJobs REST query."""

    urlopen = staticmethod(urlopen)

    def __init__(self, id_token: str) -> None:
        self.id_token = id_token

    def list(self, owner: str, stage: str | None = None) -> list[dict]:
        """List the owner's pipeline saved jobs, newest first."""
        filters = [f"owner=={owner}"]
        filters.append(f"stage in [{','.join(PIPELINE_STAGES)}]" if stage is None else f"stage=={stage}")
        query = urllib.parse.urlencode(
            {
                "filter": " AND ".join(filters),
                "orderBy": "dateSaved desc",
                "pageSize": 20,
            }
        )
        request = urllib.request.Request(
            f"{FIRESTORE_BASE}?{query}",
            headers={"Authorization": f"Bearer {self.id_token}", "Accept": "application/json"},
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
        if not isinstance(payload, dict):
            raise ValueError("Firestore response is not an object")
        documents = payload.get("documents", [])
        if not isinstance(documents, list):
            raise ValueError("Firestore documents is not an array")
        jobs = [normalize_saved_job(document) for document in documents]
        return sorted(jobs, key=lambda job: (job["savedAt"], job["documentId"]), reverse=True)


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
