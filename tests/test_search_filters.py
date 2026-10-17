"""Offline transport, CLI, and cache contracts for verified structured filters."""

import io
import json

import pytest

from hiringcafe_cli import count, main, search
from hiringcafe_cli.cache import CacheStore, active_cache_root, cache_write
from hiringcafe_cli.http_client import WebClient
from hiringcafe_cli.search_state import InvalidSearchState, build_search_arguments

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 1 of 27 matches)

### [Engineer](https://hiringcafe.com/job/fixture-job?utm_source=claude)
**Example Systems**
- Location: Worldwide
- Workplace: Hybrid
- Employment type: Full Time
- Job ID: `fixture-job`
"""

FILTER_CASES = [
    (["--location", " Germany "], {"location": "Germany"}),
    (["--location", "remote"], {"location": "remote"}),
    *[(["--workplace", value], {"workplace_types": [value]}) for value in ("Remote", "Hybrid", "Onsite")],
    *[
        (["--employment-type", value], {"employment_types": [value]})
        for value in ("Full Time", "Part Time", "Contract", "Internship", "Temporary", "Seasonal", "Volunteer")
    ],
    *[(["--limit", str(value)], {"limit": value}) for value in (1, 10, 25)],
]


@pytest.fixture
def requests(monkeypatch):
    """Record real MCP request construction while replacing all HTTP with synthetic responses."""
    calls = []
    monkeypatch.setenv("HIRINGCAFE_BASE_URL", "https://example.test")
    monkeypatch.delenv("HIRINGCAFE_NO_CACHE", raising=False)

    def urlopen(request, timeout):
        calls.append(request)
        return io.BytesIO(
            json.dumps(
                {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": SEARCH_RESPONSE}]}}
            ).encode()
        )

    monkeypatch.setattr(WebClient, "urlopen", staticmethod(urlopen))
    return calls


@pytest.fixture
def no_io(monkeypatch):
    """Fail if invalid input reaches cache configuration, storage, or client construction."""

    def fail(*args, **kwargs):
        pytest.fail("invalid filter input reached cache or network")

    for name in ("active_cache_root", "configured_base_url", "cache_read", "cache_write", "WebClient"):
        monkeypatch.setattr(search, name, fail)


def cli_json(capsys, argv):
    """Run a successful CLI command and return its JSON envelope."""
    with pytest.raises(SystemExit) as error:
        main([*argv, "--json"])
    assert error.value.code == 0
    return json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("command", ["search", "count"])
@pytest.mark.parametrize(("flags", "filters"), FILTER_CASES)
def test_cli_filters_use_verified_mcp_arguments_and_canonical_envelopes(requests, capsys, command, flags, filters):
    """Condition: a verified filter or result limit is supplied to search or count.

    Expected: an exact structured MCP request and canonical version-1 state, without client-side filtering.
    """
    payload = cli_json(capsys, [command, "engineer", *flags])

    expected_arguments = {"search": "engineer", "limit": 10, **filters}
    expected_state = {"searchQuery": "engineer", **filters}
    if expected_state.get("limit") == 10:
        del expected_state["limit"]
    assert len(requests) == 1
    assert requests[0].get_method() == "POST"
    assert requests[0].full_url == "https://example.test/api/mcp"
    assert json.loads(requests[0].data) == {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "search_jobs", "arguments": expected_arguments},
    }
    assert payload["version"] == 1
    assert payload["query"] == {"searchState": expected_state, "page": 0}
    if command == "search":
        assert payload["result"]["pageSize"] == expected_arguments["limit"]
        assert payload["result"]["paginationSupported"] is False
        assert payload["result"]["totalCount"] == 27
        assert [job["id"] for job in payload["result"]["jobs"]] == ["fixture-job"]
    else:
        assert payload["count"] == 27


@pytest.mark.parametrize("command", ["search", "count"])
@pytest.mark.parametrize(
    ("flags", "filters"),
    [
        (["--location", "Germany"], {"location": "Germany"}),
        (["--workplace", "Remote"], {"workplace_types": ["Remote"]}),
        (["--employment-type", "Contract"], {"employment_types": ["Contract"]}),
        (["--limit", "1"], {"limit": 1}),
    ],
)
def test_cli_filters_only_searches_allow_omitted_query(requests, capsys, command, flags, filters):
    """Condition: a filter is supplied without positional query text.

    Expected: empty search text is sent and the filter is echoed canonically.
    """
    payload = cli_json(capsys, [command, *flags])

    assert json.loads(requests[0].data)["params"]["arguments"] == {"search": "", "limit": 10, **filters}
    assert payload["query"]["searchState"] == {"searchQuery": "", **filters}


def test_cli_raw_and_flag_alternatives_share_canonical_search_and_count_cache(requests, capsys):
    """Condition: combined raw and flag requests differ only in array order, duplicates, or location whitespace.

    Expected: one canonical envelope and cache entry serve both search and count with one HTTP request.
    """
    flags = [
        "--location",
        " Germany ",
        "--workplace",
        "Remote",
        "--workplace",
        "Hybrid",
        "--workplace",
        "Remote",
        "--employment-type",
        "Full Time",
        "--employment-type",
        "Contract",
        "--employment-type",
        "Full Time",
        "--limit",
        "25",
    ]
    canonical = {
        "searchQuery": "engineer",
        "location": "Germany",
        "workplace_types": ["Hybrid", "Remote"],
        "employment_types": ["Contract", "Full Time"],
        "limit": 25,
    }
    first = cli_json(capsys, ["search", "engineer", *flags])
    raw = json.dumps(
        {
            "limit": 25,
            "employment_types": ["Full Time", "Contract", "Contract"],
            "workplace_types": ["Remote", "Hybrid"],
            "location": "Germany",
            "searchQuery": "engineer",
        }
    )
    result_count = cli_json(capsys, ["count", "--raw-search-state", raw])
    repeated = cli_json(capsys, ["search", "--raw-search-state", raw])

    assert first == repeated
    assert first["query"] == result_count["query"] == {"searchState": canonical, "page": 0}
    assert result_count["count"] == 27
    assert len(requests) == 1
    assert json.loads(requests[0].data)["params"]["arguments"] == {
        "search": "engineer",
        **{key: value for key, value in canonical.items() if key != "searchQuery"},
    }
    assert len(list(active_cache_root().glob("*.json"))) == 1


def test_search_arguments_canonicalize_raw_state_without_mutating_input():
    """Condition: raw and flag inputs differ in key order, duplicates, whitespace, and integral numeric limit.

    Expected: identical serialized canonical state/arguments with integer limit and unchanged caller data.
    """
    raw = {
        "limit": 5.0,
        "employment_types": ["Full Time", "Contract", "Contract"],
        "workplace_types": ["Remote", "Hybrid", "Remote"],
        "location": " Germany ",
        "searchQuery": "engineer",
    }
    original = json.dumps(raw)
    filters = {
        "location": "Germany",
        "workplace_types": ["Hybrid", "Remote"],
        "employment_types": ["Contract", "Full Time"],
        "limit": 5,
    }

    state, arguments = build_search_arguments(raw_search_state=raw)
    flag_result = build_search_arguments("engineer", filters=filters)

    assert json.dumps((state, arguments)) == json.dumps(flag_result)
    assert type(arguments["limit"]) is int
    assert json.dumps(raw) == original


@pytest.mark.parametrize("limit", [10, 10.0])
def test_cli_raw_default_limit_uses_existing_default_state_and_cache(requests, capsys, limit):
    """Condition: equivalent raw input explicitly supplies the effective default limit.

    Expected: its state omits limit and shares the default flag-mode request cache.
    """
    first = cli_json(capsys, ["search", "engineer"])
    raw = json.dumps({"searchQuery": "engineer", "limit": limit})
    repeated = cli_json(capsys, ["search", "--raw-search-state", raw])

    assert first == repeated
    assert repeated["query"]["searchState"] == {"searchQuery": "engineer"}
    assert len(requests) == 1


@pytest.mark.parametrize(
    ("flags_a", "flags_b"),
    [
        ([], ["--location", "Germany"]),
        (["--location", "Germany"], ["--location", "Netherlands"]),
        ([], ["--workplace", "Remote"]),
        (["--workplace", "Remote"], ["--workplace", "Onsite"]),
        (["--workplace", "Remote"], ["--workplace", "Remote", "--workplace", "Hybrid"]),
        ([], ["--employment-type", "Contract"]),
        (["--employment-type", "Contract"], ["--employment-type", "Full Time"]),
        (["--employment-type", "Contract"], ["--employment-type", "Contract", "--employment-type", "Temporary"]),
        ([], ["--limit", "25"]),
        (["--limit", "1"], ["--limit", "25"]),
    ],
)
def test_cli_cache_distinguishes_every_verified_argument(requests, capsys, flags_a, flags_b):
    """Condition: search/count requests differ in any verified filter or effective limit.

    Expected: distinct requests fetch separately, while a repeated search shares its count entry.
    """
    cli_json(capsys, ["search", "engineer", *flags_a])
    result_count = cli_json(capsys, ["count", "engineer", *flags_b])
    repeated = cli_json(capsys, ["search", "engineer", *flags_b])

    assert repeated["query"] == result_count["query"]
    assert len(requests) == 2
    assert len(list(active_cache_root().glob("*.json"))) == 2


def test_search_filters_use_new_namespace_and_full_argument_cache_key(requests):
    """Condition: an unfiltered cache entry exists in the old transport namespace.

    Expected: it cannot serve the new contract, whose key includes the full effective MCP arguments.
    """
    root = active_cache_root()
    cache_write(("mcp-search-v1", "https://example.test", "engineer", 10), {"obsolete": True}, 900, root)

    result = search.search("engineer", 0)

    assert result["result"]["totalCount"] == 27
    assert len(requests) == 1
    key = ("mcp-search-v2", "https://example.test", {"search": "engineer", "limit": 10})
    assert CacheStore(root).read(key, 900) == result


INVALID_STATES = [
    {},
    *[{"searchQuery": value} for value in (None, True, 1, [], {})],
    *[{"searchQuery": "", key: "unsupported"} for key in ("search", "workplaceTypes", "employmentTypes", "technology")],
    *[{"searchQuery": "", "location": value} for value in (None, True, 1, 1.5, [], {}, "", " \n ")],
    *[
        {"searchQuery": "", family: value}
        for family in ("workplace_types", "employment_types")
        for value in (None, True, 1, {}, "Remote", [], [None], [True], [1], [[]], [{}], [""], ["remote"], ["bogus"])
    ],
    *[
        {"searchQuery": "", "limit": value}
        for value in (None, True, False, "10", [], {}, 0, -1, 26, 1.5, float("nan"), float("inf"))
    ],
]


@pytest.mark.parametrize("command", ["search", "count"])
@pytest.mark.parametrize("state", INVALID_STATES)
def test_cli_invalid_raw_filter_states_fail_before_io(no_io, capsys, command, state):
    """Condition: raw state contains an unknown key, missing query, invalid type, enum, or limit.

    Expected: invalid-input exit 2 before cache access or client construction, with no partial JSON.
    """
    with pytest.raises(SystemExit) as error:
        main([command, "--raw-search-state", json.dumps(state), "--json"])

    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err


@pytest.mark.parametrize("command", ["search", "count"])
@pytest.mark.parametrize("raw", ["{", "[]", "null", "true", "1", '"text"'])
def test_cli_malformed_or_nonobject_raw_filters_fail_before_io(no_io, capsys, command, raw):
    """Condition: raw state is malformed JSON or does not encode an object.

    Expected: exit 2 before cache or client construction.
    """
    with pytest.raises(SystemExit) as error:
        main([command, "--raw-search-state", raw])
    assert error.value.code == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("command", ["search", "count"])
@pytest.mark.parametrize(
    "flags",
    [
        ["--location", ""],
        ["--location", " "],
        ["--workplace", "remote"],
        ["--workplace", "Remote,Hybrid"],
        ["--employment-type", "full time"],
        ["--employment-type", "Unknown"],
        ["--limit", "0"],
        ["--limit", "26"],
        ["--limit", "-1"],
        ["--limit", "true"],
        ["--limit", "1.5"],
    ],
)
def test_cli_invalid_filter_flags_fail_before_io(no_io, capsys, command, flags):
    """Condition: a filter flag is empty, unsupported, or has an invalid limit.

    Expected: exit 2 before any cache/network work.
    """
    with pytest.raises(SystemExit) as error:
        main([command, *flags])
    assert error.value.code == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("command", ["search", "count"])
@pytest.mark.parametrize(
    "other_input",
    [
        ["engineer"],
        [""],
        ["--location", "Germany"],
        ["--workplace", "Remote"],
        ["--employment-type", "Contract"],
        ["--limit", "10"],
    ],
)
def test_cli_raw_filters_cannot_combine_with_query_or_explicit_flags(no_io, capsys, command, other_input):
    """Condition: raw state accompanies a positional query or explicitly supplied filter/limit flag.

    Expected: exit 2 even for an empty positional query or an explicit default limit.
    """
    with pytest.raises(SystemExit) as error:
        main([command, *other_input, "--raw-search-state", '{"searchQuery":"engineer"}'])
    assert error.value.code == 2
    assert capsys.readouterr().out == ""


def test_python_filter_arguments_preserve_positional_ttl_and_bypass_parameters(requests):
    """Condition: existing Python positional arguments precede the new optional filters dictionary.

    Expected: search/count forward filters and still bypass cache with zero TTL/no-cache.
    """
    filters = {"workplace_types": ["Remote", "Remote"], "limit": 1}

    result = search.search("engineer", 0, None, True, 0, filters)
    result_count = count.count("engineer", None, True, 0, filters)

    assert result["query"] == result_count["query"]
    assert result["result"]["pageSize"] == 1
    assert len(requests) == 2
    assert list(active_cache_root().glob("*.json")) == []
    assert filters == {"workplace_types": ["Remote", "Remote"], "limit": 1}


@pytest.mark.parametrize("extra", [{}, {"workplace_types": ["Remote"], "limit": 5}])
def test_python_raw_state_preserves_empty_query_sentinel(requests, extra):
    """Condition: existing Python search/count callers pass an empty query alongside raw state.

    Expected: both APIs preserve raw mode, canonical output, and their shared cache.
    """
    raw = json.dumps({"searchQuery": "engineer", **extra})

    result = search.search("", 0, raw)
    result_count = count.count("", raw)

    assert result["query"] == result_count["query"]
    assert result["query"]["searchState"] == {"searchQuery": "engineer", **extra}
    assert result_count["count"] == 27
    assert len(requests) == 1


@pytest.mark.parametrize("query", [False, 0, [], {}])
def test_python_invalid_query_types_fail_before_io(no_io, query):
    """Condition: a Python caller supplies nonstring query text.

    Expected: the shared boundary rejects it before any cache or client work.
    """
    with pytest.raises(InvalidSearchState):
        search.search(query, 0)


@pytest.mark.parametrize("filters", [[], "Remote", {"searchQuery": "override"}, {"workplace_types": ["bogus"]}])
def test_python_invalid_filter_dicts_fail_before_io(no_io, filters):
    """Condition: a Python caller supplies malformed filter options or tries to replace the query.

    Expected: shared validation rejects it before IO.
    """
    with pytest.raises(InvalidSearchState):
        search.search("engineer", 0, filters=filters)
