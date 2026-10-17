"""Construction and validation for verified HiringCafe search state."""

import json

SEARCH_LIMIT = 10
FILTER_CHOICES = {
    "workplace_types": ("Remote", "Hybrid", "Onsite"),
    "employment_types": ("Full Time", "Part Time", "Contract", "Internship", "Temporary", "Seasonal", "Volunteer"),
}
SEARCH_FILTER_KEYS = ("location", *FILTER_CHOICES, "limit")


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


def build_search_arguments(
    query: str | None = None, raw_search_state: str | dict | None = None, filters: dict | None = None
) -> tuple[dict, dict[str, str | int | list[str]]]:
    """Validate and canonicalize state and MCP arguments for verified public searches.

    Args:
        query: Optional query text, mutually exclusive with raw state.
        raw_search_state: Complete JSON state containing string searchQuery.
        filters: Explicit structured filter flags, mutually exclusive with raw state.

    Returns:
        Canonical echoed search state and complete MCP arguments including the effective limit.

    Raises:
        InvalidSearchState: If input modes conflict or a key, type, enum, or limit is invalid.
    """
    if query is not None and not isinstance(query, str):
        raise InvalidSearchState("searchQuery must be a string")
    if filters is not None and (not isinstance(filters, dict) or set(filters) - set(SEARCH_FILTER_KEYS)):
        raise InvalidSearchState("filters must be an object containing only supported filter keys")
    if raw_search_state is not None and filters:
        raise InvalidSearchState("raw search state cannot be combined with filter or limit flags")
    state = {**build_search_state(query, raw_search_state), **(filters or {})}
    if set(state) - {"searchQuery", *SEARCH_FILTER_KEYS}:
        raise InvalidSearchState("raw search state contains unsupported keys")
    if "searchQuery" not in state:
        raise InvalidSearchState("raw search state must contain searchQuery")
    if not isinstance(state["searchQuery"], str):
        raise InvalidSearchState("searchQuery must be a string")
    state = {key: state[key] for key in ("searchQuery", *SEARCH_FILTER_KEYS) if key in state}
    if "location" in state:
        if not isinstance(state["location"], str) or not state["location"].strip():
            raise InvalidSearchState("location must be a nonempty string")
        state["location"] = state["location"].strip()
    for family, choices in FILTER_CHOICES.items():
        if family not in state:
            continue
        values = state[family]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or value not in choices for value in values)
        ):
            raise InvalidSearchState(f"{family} must be a nonempty array of supported values")
        state[family] = sorted(set(values))
    limit = state.pop("limit", SEARCH_LIMIT)
    if type(limit) not in (int, float) or not 1 <= limit <= 25 or limit != int(limit):
        raise InvalidSearchState("limit must be an integer from 1 to 25")
    limit = int(limit)
    arguments = {"search": state["searchQuery"], "limit": limit}
    arguments.update({key: value for key, value in state.items() if key != "searchQuery"})
    if limit != SEARCH_LIMIT:
        state["limit"] = limit
    return state, arguments
