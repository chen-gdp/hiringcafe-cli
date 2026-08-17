"""Tests for the verified search-state contract."""

import pytest

from hiringcafe_cli.search_state import InvalidSearchState, build_search_state


def test_query_mode_builds_only_search_query():
    """Condition: a text query is supplied. Expected: object contains only searchQuery."""
    assert build_search_state(query="python developer") == {"searchQuery": "python developer"}


def test_raw_mode_preserves_supplied_object_and_types():
    """Condition: complete raw JSON is supplied. Expected: keys and values are unchanged."""
    state = {"searchQuery": "python", "custom": [1, {"nested": True}]}

    assert build_search_state(query=None, raw_search_state=state) == state


def test_malformed_raw_json_is_rejected_without_transform():
    """Condition: parser is given malformed JSON. Expected: invalid-state error and no guess."""
    with pytest.raises(InvalidSearchState, match="invalid raw search-state JSON"):
        build_search_state(query=None, raw_search_state='{"searchQuery":')


def test_non_object_raw_state_is_rejected():
    """Condition: parsed raw JSON is an array. Expected: invalid-state error."""
    with pytest.raises(InvalidSearchState, match="must be an object"):
        build_search_state(query=None, raw_search_state="[]")


def test_simultaneous_query_and_raw_modes_are_rejected():
    """Condition: both verified input modes are supplied. Expected: invalid-state error."""
    with pytest.raises(InvalidSearchState, match="not both"):
        build_search_state(query="python", raw_search_state={"searchQuery": "python"})
