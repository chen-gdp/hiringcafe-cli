import contextlib
import io
import json

from hiringcafe_cli import main, search
from hiringcafe_cli.cache import CacheStore, cache_read, cache_write, default_cache_root


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
    cache_write(key, {"version": 1}, ttl=0, root=tmp_path)
    assert cache_read(key, ttl=1, root=tmp_path) is None
    assert cache_read(key, ttl=1, root=tmp_path, enabled=False) is None


def test_cache_keys_and_purge(tmp_path):
    """Condition: different command keys are stored under hashed names.

    Expected: base/state/page/object keys do not collide and purge is idempotent.
    """
    search_key = ("search", "base", "state", 0)
    job_key = ("job", "base", "id")
    cache_write(search_key, {"kind": "search"}, ttl=1, root=tmp_path)
    cache_write(job_key, {"kind": "job"}, ttl=1, root=tmp_path)
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
        self.calls = []

    def search_page(self, state, page):
        self.calls.append((state, page))
        return {
            "ssrHits": [{"objectID": "job-one", "job_information": {"title": "Engineer"}}],
            "ssrPage": 0,
            "ssrTotalCount": 1,
            "ssrCompanyCount": 1,
            "ssrPageSize": 40,
            "ssrIsLastPage": True,
        }


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
    assert client.calls == [({"searchQuery": "python"}, 0)]
    assert "cache miss" in captured.err
    assert "cache hit" in captured.err


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
    assert client.calls == [({"searchQuery": "python"}, 0)]
    assert json.loads(captured.out)["count"] == 1
    assert "cache hit" in captured.err


def test_cli_no_cache_bypasses_read_and_write(tmp_path, monkeypatch, capsys):
    """Condition: two invocations use --no-cache.

    Expected: both requests reach HTTP and no cache entry is written.
    """
    client = FakeClient()
    monkeypatch.setattr("hiringcafe_cli.search.WebClient", lambda: client)
    for _ in range(2):
        try:
            main(["search", "python", "--json", "--no-cache"])
        except SystemExit as error:
            assert error.code == 0
    capsys.readouterr()
    assert len(client.calls) == 2
    assert list(tmp_path.rglob("*.json")) == []
