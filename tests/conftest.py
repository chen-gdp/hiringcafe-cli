"""Shared pytest isolation."""

import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Give every test an isolated cache root."""
    monkeypatch.setenv("HIRINGCAFE_CACHE_HOME", str(tmp_path))
