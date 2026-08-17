"""Owner-only local Firebase session storage."""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

SESSION_VERSION = 1


@dataclass(frozen=True)
class Session:
    """Durable Firebase session representation."""

    refresh_token: str


class SessionStore:
    """Atomic JSON file store for a Firebase refresh token."""

    def __init__(self, path: Path) -> None:
        """Initialize with an explicit path for testability."""
        self.path = path

    def load(self) -> Session | None:
        """Load and validate the session.

        Returns:
            Session when present, otherwise None.
        """
        if not self.path.exists():
            return None
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("invalid session file") from error
        if (
            not isinstance(value, dict)
            or value.get("version") != SESSION_VERSION
            or not isinstance(value.get("refreshToken"), str)
            or not value["refreshToken"]
        ):
            raise ValueError("invalid session file")
        return Session(value["refreshToken"])

    def save(self, refresh_token: str) -> None:
        """Atomically save a versioned owner-only session.

        Args:
            refresh_token: Durable Firebase refresh token.
        """
        if not refresh_token:
            raise ValueError("refresh token must not be empty")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f"{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                os.chmod(temporary, 0o600)
                json.dump(
                    {"version": SESSION_VERSION, "refreshToken": refresh_token},
                    output,
                    separators=(",", ":"),
                )
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def delete(self) -> None:
        """Delete the local session when present."""
        try:
            self.path.unlink()
        except FileNotFoundError:
            return
