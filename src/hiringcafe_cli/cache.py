"""Owner-only anonymous-read TTL cache."""

import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

VERSION = 2


def default_cache_root(base: Path) -> Path:
    """Return the versioned cache root under a configuration base."""
    return base / "cache" / "v1"


def active_cache_root() -> Path:
    """Return the configured or user-default cache root."""
    configured = os.environ.get("HIRINGCAFE_CACHE_HOME")
    if configured:
        return default_cache_root(Path(configured))
    return default_cache_root(Path.home() / ".cache" / "hiringcafe-cli")


class CacheStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, key: tuple) -> Path:
        raw = json.dumps(key, separators=(",", ":"), sort_keys=True)
        name = hashlib.sha256(raw.encode()).hexdigest()
        return self.root / f"{name}.json"

    def read(self, key: tuple, ttl: int) -> dict | None:
        """Read an entry only within its original lifetime and requested age limit.

        Args:
            key: Anonymous request cache key.
            ttl: Maximum age in seconds; zero always misses.

        Returns:
            The fresh normalized value, or None for an absent or invalid entry.
        """
        if ttl <= 0:
            print("cache miss", file=sys.stderr)
            return None
        path = self.path(key)
        if not path.exists():
            print("cache miss", file=sys.stderr)
            return None
        payload = None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if not (
            isinstance(payload, dict)
            and payload.get("version") == VERSION
            and type(payload.get("writtenAt")) in (int, float)
            and type(payload.get("expiresAt")) in (int, float)
            and isinstance(payload.get("value"), dict)
        ):
            path.unlink(missing_ok=True)
            print("cache miss", file=sys.stderr)
            return None
        now = time.time()
        written_at = payload["writtenAt"]
        expires_at = payload["expiresAt"]
        if not (0 <= written_at <= now < expires_at < math.inf and now - written_at < ttl):
            path.unlink(missing_ok=True)
            print("cache miss", file=sys.stderr)
            return None
        print("cache hit", file=sys.stderr)
        return payload["value"]

    def write(self, key: tuple, value: dict, ttl: int) -> None:
        """Atomically write an owner-only cache entry with a verifiable lifetime.

        Args:
            key: Anonymous request cache key.
            value: Normalized anonymous response.
            ttl: Lifetime in seconds; zero skips writing.
        """
        if ttl <= 0:
            return
        written_at = time.time()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.exists():
            os.chmod(self.root, 0o700)
        destination = self.path(key)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f"{destination.name}.", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                os.chmod(temporary_name, 0o600)
                json.dump(
                    {"version": VERSION, "writtenAt": written_at, "expiresAt": written_at + ttl, "value": value},
                    output,
                    separators=(",", ":"),
                )
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary_name, destination)
        except BaseException:
            Path(temporary_name).unlink(missing_ok=True)
            raise

    def purge(self) -> None:
        if not self.root.exists():
            return
        for entry in self.root.iterdir():
            if entry.is_file():
                entry.unlink()


def cache_read(key: tuple, ttl: int, root: Path, enabled: bool = True) -> dict | None:
    return CacheStore(root).read(key, ttl) if enabled else None


def cache_write(key: tuple, value: dict, ttl: int, root: Path, enabled: bool = True) -> None:
    if enabled:
        CacheStore(root).write(key, value, ttl)
