import contextlib
import io
import json
import os

import pytest

from hiringcafe_cli import main, search
from hiringcafe_cli.cache import VERSION, CacheStore, cache_read, cache_write, default_cache_root

SEARCH_RESPONSE = """\
## HiringCafe job results (showing 1 of 1 matches)

### [Engineer](https://hiringcafe.com/job/job-one?utm_source=claude)
- Job ID: `job-one`
"""

DETAIL_RESPONSE = """\
# [Engineer](https://hiringcafe.com/job/job-one?utm_source=claude)
- **Job ID:** `job-one`
## Full description
Build reliable systems.
"""


def test_cache_write_records_verifiable_lifetime(tmp_path, monkeypatch):
    """Condition: an entry is written with a positive TTL and a fractional timestamp.

    Expected: schema 2 records the exact write time and original expiry.
    """
    key = ("search", "base", "state", 0)
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: 1_000_000.25)

    cache_write(key, {"value": 1}, ttl=60, root=tmp_path)

    payload = json.loads(CacheStore(tmp_path).path(key).read_text(encoding="utf-8"))
    assert payload == {"version": 2, "writtenAt": 1_000_000.25, "expiresAt": 1_000_060.25, "value": {"value": 1}}


@pytest.mark.parametrize(
    ("stored_ttl", "requested_ttl", "age", "fresh"),
    [(900, 60, 59.999, True), (900, 60, 60, False), (60, 900, 59.999, True), (60, 900, 60, False)],
)
def test_cache_read_respects_requested_age_and_original_expiry(
    tmp_path, monkeypatch, stored_ttl, requested_ttl, age, fresh
):
    """Condition: an entry is read with a shorter or longer TTL override.

    Expected: both the requested age limit and original expiry are strict freshness limits.
    """
    key = ("search", "base", "state", 0)
    current_time = 1_000_000.25
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: current_time)
    cache_write(key, {"value": 1}, ttl=stored_ttl, root=tmp_path)
    current_time += age

    result = cache_read(key, ttl=requested_ttl, root=tmp_path)

    assert result == ({"value": 1} if fresh else None)
    assert CacheStore(tmp_path).path(key).exists() is fresh


def test_cache_zero_ttl_bypasses_existing_entry_and_skips_writes(tmp_path, monkeypatch):
    """Condition: zero TTL is used with an absent cache root and an existing fresh entry.

    Expected: reads always miss and writes neither create a root nor replace reusable entries.
    """
    key = ("search", "base", "state", 0)
    root = tmp_path / "cache"
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: 1_000_000.25)

    cache_write(key, {"value": 1}, ttl=0, root=root)
    assert cache_read(key, ttl=0, root=root) is None
    assert not root.exists()

    cache_write(key, {"value": 1}, ttl=60, root=root)
    path = CacheStore(root).path(key)
    original = path.read_bytes()
    assert cache_read(key, ttl=0, root=root) is None
    cache_write(key, {"value": 2}, ttl=0, root=root)

    assert path.read_bytes() == original
    assert cache_read(key, ttl=60, root=root) == {"value": 1}


@pytest.mark.parametrize("version", [1, VERSION])
def test_cache_schema_without_write_time_is_discarded_even_before_expiry(tmp_path, monkeypatch, version):
    """Condition: a legacy or current-schema entry has a future expiry but no verifiable write time.

    Expected: it is deleted and returned as a miss even with a longer requested TTL.
    """
    key = ("search", "base", "state", 0)
    path = CacheStore(tmp_path).path(key)
    path.write_text(json.dumps({"version": version, "expiresAt": 1_000_060, "value": {"value": 1}}), encoding="utf-8")
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: 1_000_000.25)

    assert cache_read(key, ttl=900, root=tmp_path) is None
    assert not path.exists()


@pytest.mark.parametrize(
    ("field", "timestamp"),
    [
        ("writtenAt", None),
        ("writtenAt", "1000000"),
        ("writtenAt", True),
        ("writtenAt", -1),
        ("writtenAt", 1_000_002),
        ("writtenAt", float("nan")),
        ("writtenAt", float("inf")),
        ("writtenAt", float("-inf")),
        ("writtenAt", 10**400),
        ("expiresAt", None),
        ("expiresAt", "1000060"),
        ("expiresAt", True),
        ("expiresAt", -1),
        ("expiresAt", 1_000_000),
        ("expiresAt", float("nan")),
        ("expiresAt", float("inf")),
        ("expiresAt", float("-inf")),
    ],
)
def test_cache_invalid_timestamps_recover_as_a_miss(tmp_path, monkeypatch, field, timestamp):
    """Condition: a cache timestamp is malformed, nonfinite, reversed, or ahead of the clock.

    Expected: the unverifiable entry is deleted and never returned as fresh.
    """
    key = ("search", "base", "state", 0)
    path = CacheStore(tmp_path).path(key)
    payload = {"version": VERSION, "writtenAt": 1_000_000, "expiresAt": 1_000_060, "value": {"value": 1}}
    payload[field] = timestamp
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: 1_000_001)

    assert cache_read(key, ttl=900, root=tmp_path) is None
    assert not path.exists()


def test_cache_hit_repeats_search_without_http(tmp_path, monkeypatch, capsys):
    """Condition: identical search key is read twice before TTL expiry.

    Expected: normalized envelope is returned once from disk and no HTTP call runs on hit.
    """
    key = ("search", "https://hiringcafe.com", '{"query":"python"}', 0)
    cache_write(key, {"version": 1}, ttl=900, root=tmp_path)
    monkeypatch.setattr(search, "search", lambda *_: (_ for _ in ()).throw(AssertionError()))
    with contextlib.redirect_stderr(io.StringIO()) as errors:
        assert cache_read(key, ttl=900, root=tmp_path) == {"version": 1}
    assert "cache hit" in errors.getvalue()


def test_cache_expiry_and_no_cache_bypass(tmp_path, monkeypatch):
    """Condition: entry expired or bypass requested.

    Expected: both return None and bypass performs neither read nor write.
    """
    key = ("job", "https://hiringcafe.com", "job-id")
    current_time = 1_000_000.25
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: current_time)
    cache_write(key, {"version": 1}, ttl=1, root=tmp_path)
    current_time += 1
    assert cache_read(key, ttl=1, root=tmp_path) is None
    assert cache_read(key, ttl=1, root=tmp_path, enabled=False) is None


def test_corrupt_cache_entry_recovers_as_a_miss(tmp_path):
    """Condition: a cache file contains invalid JSON.

    Expected: the entry is deleted and the same key reports a miss without raising.
    """
    key = ("search", "https://hiringcafe.com", '{"query":"python"}', 0)
    path = CacheStore(tmp_path).path(key)
    path.write_text("{", encoding="utf-8")
    assert cache_read(key, ttl=900, root=tmp_path) is None
    assert not path.exists()


def test_wrong_schema_cache_entry_recovers_as_a_miss(tmp_path):
    """Condition: a cache file has valid JSON but an incompatible schema.

    Expected: the entry is deleted rather than repeatedly failing the same key.
    """
    key = ("search", "https://hiringcafe.com", '{"query":"python"}', 0)
    path = CacheStore(tmp_path).path(key)
    path.write_text(json.dumps({"version": 99, "expiresAt": 1, "value": []}), encoding="utf-8")
    assert cache_read(key, ttl=900, root=tmp_path) is None
    assert not path.exists()


def test_cache_keys_and_purge(tmp_path, monkeypatch):
    """Condition: different command keys are stored under hashed names.

    Expected: base/state/page/object keys do not collide and purge is idempotent.
    """
    search_key = ("search", "base", "state", 0)
    job_key = ("job", "base", "id")
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: 1_000_000.25)
    cache_write(search_key, {"kind": "search"}, ttl=120, root=tmp_path)
    cache_write(job_key, {"kind": "job"}, ttl=120, root=tmp_path)
    assert cache_read(search_key, ttl=1, root=tmp_path)["kind"] == "search"
    assert cache_read(job_key, ttl=1, root=tmp_path)["kind"] == "job"
    CacheStore(tmp_path).purge()
    CacheStore(tmp_path).purge()
    assert cache_read(search_key, ttl=1, root=tmp_path) is None


def test_cache_root_is_versioned_and_owner_only(tmp_path):
    """Condition: cache initializes under a versioned root.

    Expected: directory mode is owner-only and nested entries can be written atomically.
    """
    root = default_cache_root(tmp_path)
    cache_write(("search", "base", "state", 0), {}, ttl=1, root=root)
    assert root.stat().st_mode & 0o700 == 0o700


def test_cache_entries_are_owner_only_and_leave_no_temporary_files(tmp_path):
    """Condition: a cache entry is written successfully.

    Expected: the final file is owner-only and no temporary file remains.
    """
    key = ("search", "base", "state", 0)
    cache_write(key, {"value": 1}, ttl=1, root=tmp_path)
    entries = list(tmp_path.iterdir())
    assert len(entries) == 1
    assert entries[0].stat().st_mode & 0o777 == 0o600


def test_failed_cache_replace_preserves_entry_and_removes_temporary_file(tmp_path, monkeypatch):
    """Condition: writing a valid entry fails during atomic replacement.

    Expected: the old entry remains and the temporary file is removed.
    """
    key = ("search", "base", "state", 0)
    current_time = 1_000_000.0
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: current_time)
    cache_write(key, {"value": 1}, ttl=60, root=tmp_path)

    def fail_replace(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr("hiringcafe_cli.cache.os.replace", fail_replace)
    try:
        cache_write(key, {"value": 2}, ttl=60, root=tmp_path)
    except OSError:
        pass
    else:
        raise AssertionError("write should fail")
    assert cache_read(key, ttl=60, root=tmp_path) == {"value": 1}
    assert list(tmp_path.iterdir()) == [CacheStore(tmp_path).path(key)]


def test_cache_purge_command_removes_entries(tmp_path, monkeypatch, capsys):
    """Condition: cache command purge runs against configured root.

    Expected: stored entry is removed and command succeeds when already empty.
    """
    from hiringcafe_cli import main
    from hiringcafe_cli.cache import active_cache_root

    monkeypatch.setenv("HIRINGCAFE_CACHE_HOME", str(tmp_path))
    cache_write(("search", "base", "state", 0), {}, ttl=1, root=active_cache_root())
    try:
        main(["cache", "purge"])
    except SystemExit as error:
        assert error.code == 0
    assert cache_read(("search", "base", "state", 0), ttl=1, root=active_cache_root()) is None


class FakeClient:
    def __init__(self):
        self.base_url = "https://hiringcafe.com"
        self.calls = []

    def call_mcp_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return DETAIL_RESPONSE if name == "get_job_details" else SEARCH_RESPONSE


@pytest.mark.parametrize("command", [("search", "python"), ("count", "python"), ("job", "show", "job-one")])
def test_cli_cache_freshness_overrides_reach_all_anonymous_reads(monkeypatch, capsys, command):
    """Condition: each anonymous command receives shorter, longer, and zero TTL overrides.

    Expected: fresh entries hit, both expiry limits trigger fetches, and every zero TTL fetches.
    """
    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    monkeypatch.setattr("hiringcafe_cli.job.WebClient", lambda: client)
    current_time = 1_000_000.25
    monkeypatch.setattr("hiringcafe_cli.cache.time.time", lambda: current_time)

    for age, ttl, expected_calls in [(0, 60, 1), (20, 30, 1), (30, 30, 2), (60, 900, 3), (60, 0, 4), (60, 0, 5)]:
        current_time = 1_000_000.25 + age
        with pytest.raises(SystemExit) as error:
            main([*command, "--json", "--cache-ttl", str(ttl)])

        assert error.value.code == 0
        captured = capsys.readouterr()
        assert json.loads(captured.out)["version"] == 1
        assert len(client.calls) == expected_calls
        assert ("cache hit" if age == 20 else "cache miss") in captured.err


@pytest.mark.parametrize("command", [("search", "python"), ("count", "python"), ("job", "show", "job-one")])
@pytest.mark.parametrize("bypass", ["none", "flag", "environment"])
def test_cli_negative_cache_ttl_fails_before_cache_or_network(monkeypatch, capsys, command, bypass):
    """Condition: search, count, or job show receives a negative TTL, including with cache bypass.

    Expected: exit 2 and a useful argument diagnostic precede any cache access or client construction.
    """

    def fail_access():
        raise AssertionError("negative TTL must fail before cache or network access")

    for module in ("search", "job"):
        monkeypatch.setattr(f"hiringcafe_cli.{module}.active_cache_root", fail_access)
        monkeypatch.setattr(f"hiringcafe_cli.{module}.WebClient", fail_access)
    monkeypatch.delenv("HIRINGCAFE_NO_CACHE", raising=False)
    if bypass == "environment":
        monkeypatch.setenv("HIRINGCAFE_NO_CACHE", "1")
    options = ["--no-cache"] if bypass == "flag" else []

    with pytest.raises(SystemExit) as error:
        main([*command, "--cache-ttl", "-1", *options])

    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "--cache-ttl must be nonnegative" in captured.err


def test_cli_repeat_search_uses_cache_without_http(tmp_path, monkeypatch, capsys):
    """Condition: identical anonymous search command runs twice before TTL expiry.

    Expected: the second CLI invocation makes no HTTP request and reports a cache hit.
    """
    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    for _ in range(2):
        try:
            main(["search", "python", "--json"])
        except SystemExit as error:
            assert error.code == 0
        else:
            raise AssertionError("CLI should exit")
    captured = capsys.readouterr()
    assert client.calls == [("search_jobs", {"search": "python", "limit": 10})]
    assert "cache miss" in captured.err
    assert "cache hit" in captured.err


def test_search_cache_is_isolated_by_configured_base_url(tmp_path, monkeypatch):
    """Condition: identical searches run against two configured base URLs.

    Expected: each URL gets its own cache entry and HTTP fetch sequence.
    """
    clients = []
    calls = []

    class BaseUrlClient:
        def __init__(self, base_url):
            self.base_url = base_url

        def call_mcp_tool(self, name, arguments):
            object_id = f"{self.base_url.removeprefix('https://')}-job"
            calls.append((self.base_url, name, arguments))
            return (
                "## HiringCafe job results (showing 1 of 1 matches)\n\n"
                f"### [Engineer](https://hiringcafe.com/job/{object_id})\n- Job ID: `{object_id}`"
            )

    monkeypatch.setenv("HIRINGCAFE_CACHE_HOME", str(tmp_path))
    monkeypatch.setattr(
        search,
        "WebClient",
        lambda: clients.append(BaseUrlClient(os.environ["HIRINGCAFE_BASE_URL"])) or clients[-1],
    )
    for base_url in ("https://one.test", "https://two.test"):
        monkeypatch.setenv("HIRINGCAFE_BASE_URL", base_url)
        for _ in range(2):
            result = search.search("python", 0)
            assert result["result"]["jobs"][0]["id"] == f"{base_url.removeprefix('https://')}-job"
    assert len(calls) == 2


def test_cli_count_reuses_cached_search_and_custom_ttl(tmp_path, monkeypatch, capsys):
    """Condition: count follows search with matching state and custom TTL.

    Expected: count reads the normalized search envelope without HTTP.
    """
    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    try:
        main(["search", "python", "--json", "--cache-ttl", "60"])
    except SystemExit as error:
        assert error.code == 0
    capsys.readouterr()
    try:
        main(["count", "python", "--json", "--cache-ttl", "60"])
    except SystemExit as error:
        assert error.code == 0
    captured = capsys.readouterr()
    assert client.calls == [("search_jobs", {"search": "python", "limit": 10})]
    assert json.loads(captured.out)["count"] == 1
    assert "cache hit" in captured.err


@pytest.mark.parametrize("command", [("search", "python"), ("count", "python"), ("job", "show", "job-one")])
@pytest.mark.parametrize("bypass", ["flag", "environment"])
def test_cli_no_cache_bypasses_read_and_write(tmp_path, monkeypatch, capsys, command, bypass):
    """Condition: two anonymous read invocations use --no-cache or HIRINGCAFE_NO_CACHE.

    Expected: both requests reach HTTP and no cache entry is written.
    """
    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    monkeypatch.setattr("hiringcafe_cli.job.WebClient", lambda: client)
    if bypass == "environment":
        monkeypatch.setenv("HIRINGCAFE_NO_CACHE", "1")
    options = ["--no-cache"] if bypass == "flag" else []
    for _ in range(2):
        try:
            main([*command, "--json", *options])
        except SystemExit as error:
            assert error.code == 0
    capsys.readouterr()
    assert len(client.calls) == 2
    assert list(tmp_path.rglob("*.json")) == []
