"""Save a HiringCafe job to the signed-in user's tracker."""

import sys
from datetime import datetime, timezone

from hiringcafe_cli.auth import store
from hiringcafe_cli.firebase import FirebaseClient, FirebaseAuthError
from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.saved_jobs import VALID_STAGES
from hiringcafe_cli.saved_jobs_list import FirestoreClient

TRACKING_ARRAYS = ("stageHistory", "counted_milestones", "bookmarks", "notes")


def _clean_job(job: dict) -> dict:
    """Remove private user-tracking arrays before copying hydrated fields."""
    return {key: value for key, value in job.items() if key not in TRACKING_ARRAYS}


def save(object_id: str, stage: str) -> None:
    """Hydrate, merge-write Firestore, then sync the marketplace stage."""
    credentials = FirebaseClient().refresh(store().load().refresh_token)
    hydrated = WebClient().job_description(object_id)
    saved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    values = {
        "objectID": object_id,
        "isHidden": stage == "hidden",
        "owner": credentials["userId"],
        "dateSaved": saved_at,
        "stage": stage,
        "stageHistory": {"appendMissingElements": [{"stage": stage, "at": saved_at}]},
        "counted_milestones": {},
        **_clean_job(hydrated),
    }
    FirestoreClient(credentials["idToken"]).save(f"{credentials['userId']}_{object_id}", values)
    if hydrated.get("source") != "import":
        WebClient().marketplace_stage(object_id, credentials["idToken"], stage)


def run(argv, json_output: bool = False) -> int:
    """Execute the save command."""
    object_id = argv.object_id.strip()
    if not object_id or argv.stage not in VALID_STAGES:
        print("hiringcafe: invalid object ID or stage", file=sys.stderr)
        return 2
    session = store().load()
    if session is None:
        print("hiringcafe: no stored credential", file=sys.stderr)
        return 4
    try:
        save(object_id, argv.stage)
    except FirebaseAuthError as error:
        print(f"hiringcafe: {error}", file=sys.stderr)
        return 5
    except Exception as error:
        print(f"hiringcafe: save completed partially: {error}", file=sys.stderr)
        return 1
    except (FirebaseAuthError, ValueError, FirestoreError, HireCafeHTTPError, HireCafeTransportError) as error:
        print(f"hiringcafe: save failed: {error}", file=sys.stderr)
        return 1
    print(f"Saved {object_id} as {argv.stage}")
    return 0
