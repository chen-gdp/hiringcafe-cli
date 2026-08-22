"""Move a saved HiringCafe job between tracker stages."""

import sys
from datetime import datetime, timezone

from hiringcafe_cli.auth import store
from hiringcafe_cli.firebase import FirebaseAuthError, FirebaseClient
from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.saved_jobs import VALID_STAGES, decode_firestore_fields
from hiringcafe_cli.saved_jobs_list import FirestoreClient

OLD_LIST_STAGES = {"saved", "applied", "hidden"}


def change_stage(object_id: str, stage: str) -> None:
    """Apply the captured marketplace-first stage transition."""
    credentials = FirebaseClient().refresh(store().load().refresh_token)
    document_id = f"{credentials['userId']}_{object_id}"
    firestore = FirestoreClient(credentials["idToken"])
    document = firestore.get(document_id)
    if document is None:
        raise LookupError(f"saved job not found: {object_id}")
    fields = decode_firestore_fields(document.get("fields", {}))
    old_stage = fields.get("stage")
    web = WebClient()
    web.marketplace_stage(object_id, credentials["idToken"], stage)
    saved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    values = {
        "stage": stage,
        "dateSaved": saved_at,
        "stageHistory": {"appendMissingElements": [{"stage": stage, "at": saved_at}]},
    }
    if fields.get("firstSavedAt") is None:
        values["firstSavedAt"] = fields.get("dateSaved", saved_at)
    firestore.update(document_id, values)
    if old_stage in OLD_LIST_STAGES and old_stage != stage:
        web.remove_from_list(object_id, credentials["idToken"], old_stage)


def run(argv, json_output: bool = False) -> int:
    """Execute the stage command."""
    object_id = argv.object_id.strip()
    if not object_id or argv.stage not in VALID_STAGES:
        print("hiringcafe: invalid object ID or stage", file=sys.stderr)
        return 2
    session = store().load()
    if session is None:
        print("hiringcafe: no stored credential", file=sys.stderr)
        return 4
    try:
        change_stage(object_id, argv.stage)
    except FirebaseAuthError as error:
        print(f"hiringcafe: {error}", file=sys.stderr)
        return 5
    except LookupError as error:
        print(f"hiringcafe: {error}", file=sys.stderr)
        return 6
    except Exception as error:
        print(f"hiringcafe: stage change completed partially: {error}", file=sys.stderr)
        return 1
    print(f"Set {object_id} to {argv.stage}")
    return 0
