"""Saved-job domain models and Firestore value conversion."""

from datetime import datetime
from typing import Any

VALID_STAGES = ("saved", "applied", "interviewing", "offer", "rejected", "ghosted", "hidden")
PIPELINE_STAGES = tuple(stage for stage in VALID_STAGES if stage != "hidden")


class SavedJobError(ValueError):
    """A saved-job document violates the verified contract."""


def _document_id(document: dict) -> str:
    """Extract the final Firestore document ID."""
    name = document.get("name", "")
    return name.rsplit("/", 1)[-1]


def _value(value: Any) -> Any:
    """Convert one Firestore typed value recursively."""
    if not isinstance(value, dict):
        return value
    for key in ("stringValue", "integerValue", "doubleValue", "booleanValue"):
        if key in value:
            return value[key]
    if "timestampValue" in value:
        timestamp = datetime.fromisoformat(value["timestampValue"].replace("Z", "+00:00"))
        return timestamp.isoformat()
    if "mapValue" in value:
        return decode_firestore_fields(value["mapValue"].get("fields", {}))
    if "arrayValue" in value:
        return [_value(item) for item in value["arrayValue"].get("values", [])]
    return None


def decode_firestore_fields(fields: dict) -> dict:
    """Decode Firestore typed fields to plain Python values."""
    return {key: _value(value) for key, value in fields.items()}


def normalize_saved_job(document: dict) -> dict:
    """Normalize a Firestore savedJobs document.

    Args:
        document: Firestore REST document.

    Returns:
        Stable saved-job representation.

    Raises:
        SavedJobError: If identity, ownership, or stage is invalid.
    """
    fields = decode_firestore_fields(document.get("fields", {}))
    object_id = fields.get("objectID")
    owner = fields.get("owner")
    if not isinstance(object_id, str) or not object_id:
        raise SavedJobError("saved job has no objectID")
    if not isinstance(owner, str) or not owner:
        raise SavedJobError("saved job has no owner")
    stage = fields.get("stage")
    if stage not in VALID_STAGES:
        raise SavedJobError(f"saved job has invalid stage: {stage}")
    job_information = fields.get("job_information") or {}
    company = fields.get("enriched_company_data") or {}
    processed = fields.get("v5_processed_job_data") or {}
    return {
        "id": object_id,
        "savedAt": fields.get("dateSaved"),
        "stage": stage,
        "stageHistory": fields.get("stageHistory", []),
        "hidden": bool(fields.get("isHidden", False)),
        "documentId": fields.get("docID") or _document_id(document),
        "title": job_information.get("title"),
        "company": company.get("name", processed.get("company_name")),
        "location": processed.get("formatted_workplace_location"),
        "url": fields.get("apply_url"),
    }
