"""Construction and validation for verified HiringCafe search state."""

import json


class InvalidSearchState(ValueError):
    """A CLI search state violates the verified contract."""


def build_search_state(query: str | None = None, raw_search_state: str | dict | None = None) -> dict:
    """Build one complete search state from the two verified input modes.

    Args:
        query: Query-text mode.
        raw_search_state: Raw JSON object mode.

    Returns:
        The complete search-state object.

    Raises:
        InvalidSearchState: If both modes are supplied or raw JSON is malformed/non-object.
    """
    if query is not None and raw_search_state is not None:
        raise InvalidSearchState("use query or raw search state, not both")
    if raw_search_state is not None:
        if isinstance(raw_search_state, str):
            try:
                value = json.loads(raw_search_state)
            except json.JSONDecodeError as error:
                raise InvalidSearchState("invalid raw search-state JSON") from error
        else:
            value = raw_search_state
        if not isinstance(value, dict):
            raise InvalidSearchState("raw search state must be an object")
        return value
    return {"searchQuery": query or ""}
