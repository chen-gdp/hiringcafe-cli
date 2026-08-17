"""Tests for normalized saved-job models."""

from hiringcafe_cli.saved_jobs import VALID_STAGES, SavedJobError, normalize_saved_job


def test_normalize_saved_job_converts_timestamps_and_preserves_history():
    """Condition: synthetic Firestore document is complete. Expected: stable normalized output."""
    document = {
        "name": "projects/test/databases/(default)/documents/savedJobs/owner-one_job-one",
        "fields": {
            "objectID": {"stringValue": "job-one"},
            "owner": {"stringValue": "owner-one"},
            "dateSaved": {"timestampValue": "2026-08-17T01:02:03Z"},
            "stage": {"stringValue": "applied"},
            "stageHistory": {
                "arrayValue": {
                    "values": [
                        {"mapValue": {"fields": {
                            "stage": {"stringValue": "saved"},
                            "at": {"timestampValue": "2026-08-17T01:02:03Z"},
                        }}}
                    ]
                }
            },
            "isHidden": {"booleanValue": False},
            "job_information": {"mapValue": {"fields": {"title": {"stringValue": "Engineer"}}}},
            "enriched_company_data": {"mapValue": {"fields": {"name": {"stringValue": "Example"}}}},
            "v5_processed_job_data": {
                "mapValue": {
                    "fields": {"formatted_workplace_location": {"stringValue": "Remote"}}
                }
            },
            "apply_url": {"stringValue": "https://example.test/job"},
        },
    }

    result = normalize_saved_job(document)

    assert result == {
        "id": "job-one",
        "savedAt": "2026-08-17T01:02:03+00:00",
        "stage": "applied",
        "stageHistory": [{"stage": "saved", "at": "2026-08-17T01:02:03+00:00"}],
        "hidden": False,
        "documentId": "owner-one_job-one",
        "title": "Engineer",
        "company": "Example",
        "location": "Remote",
        "url": "https://example.test/job",
    }


def test_normalize_saved_job_rejects_missing_identity_and_invalid_stage():
    """Condition: owner/objectID/stage invalid. Expected: explicit model errors."""
    base = {"name": "documents/savedJobs/owner-one_job-one", "fields": {"owner": {"stringValue": "owner-one"}}}
    for document, message in (
        (base, "objectID"),
        (base | {"fields": base["fields"] | {"objectID": {"stringValue": ""}}}, "objectID"),
        (base | {"fields": base["fields"] | {"objectID": {"stringValue": "job"}, "stage": {"stringValue": "bad"}}}, "stage"),
    ):
        try:
            normalize_saved_job(document)
        except SavedJobError as error:
            assert message in str(error)
        else:
            raise AssertionError("invalid saved job should fail")


def test_valid_stage_order_is_verified_tracker_order():
    """Condition: stage constant is inspected. Expected: captured web-app order."""
    assert VALID_STAGES == ("saved", "applied", "interviewing", "offer", "rejected", "ghosted", "hidden")
