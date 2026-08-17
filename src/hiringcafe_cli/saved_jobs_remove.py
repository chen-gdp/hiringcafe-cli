"""Remove a saved HiringCafe job."""

import sys

from hiringcafe_cli.auth import store
from hiringcafe_cli.firebase import FirebaseAuthError, FirebaseClient
from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.saved_jobs import decode_firestore_fields
from hiringcafe_cli.saved_jobs_list import FirestoreClient


def remove(object_id: str) -> None:
    """Read the current stage and delegate deletion to the marketplace."""
    credentials = FirebaseClient().refresh(store().load().refresh_token)
    document = FirestoreClient(credentials["idToken"]).get(f"{credentials['userId']}_{object_id}")
    if document is None:
        raise LookupError(f"saved job not found: {object_id}")
    fields = decode_firestore_fields(document.get("fields", {}))
    WebClient().remove_job(object_id, credentials["idToken"], fields["stage"])


def run(argv, json_output: bool = False) -> int:
    """Execute removal after confirmation."""
    object_id = argv.object_id.strip()
    if not object_id:
        print("hiringcafe: invalid object ID", file=sys.stderr)
        return 2
    if not argv.yes:
        answer = input(f"Remove {object_id} from saved jobs? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("Removal canceled", file=sys.stderr)
            return 2
    if store().load() is None:
        print("hiringcafe: no stored credential", file=sys.stderr)
        return 4
    try:
        remove(object_id)
    except FirebaseAuthError as error:
        print(f"hiringcafe: {error}", file=sys.stderr)
        return 5
    except LookupError as error:
        print(f"hiringcafe: {error}", file=sys.stderr)
        return 6
    except Exception as error:
        print(f"hiringcafe: removal failed: {error}", file=sys.stderr)
        return 1
    print(f"Removed {object_id}")
    return 0
