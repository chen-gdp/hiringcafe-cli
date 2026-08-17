"""Anonymous job-description command."""

import json
import sys

from hiringcafe_cli.http_client import WebClient


def show(object_id: str) -> dict:
    """Fetch and normalize a job description.

    Args:
        object_id: Nonempty HiringCafe object ID.

    Returns:
        Stable version-1 job-detail envelope.
    """
    job = WebClient().job_description(object_id)
    if not job:
        raise ValueError("job-description response has no job object")
    information = job.get("job_information") or {}
    description = information.get("description")
    return {
        "version": 1,
        "job": {
            "id": job.get("objectID", object_id),
            "title": information.get("title"),
            "description": " ".join(str(description).split()) if description is not None else None,
            "url": job.get("apply_url"),
        },
    }


def run(argv: object, json_output: bool) -> int:
    """Execute job show with CLI arguments."""
    if not argv.object_id:
        print("hiringcafe: object ID must not be empty", file=sys.stderr)
        return 2
    envelope = show(argv.object_id)
    if json_output:
        print(json.dumps(envelope, separators=(",", ":")))
    else:
        job = envelope["job"]
        print(f"{job['title'] or 'Untitled'}\n{job['url'] or ''}\n\n{job['description'] or ''}")
    return 0
