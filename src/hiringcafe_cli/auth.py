"""Firebase authentication commands."""

import getpass
import json
import os
import sys
from pathlib import Path

from hiringcafe_cli.firebase import FirebaseClient
from hiringcafe_cli.session import SessionStore


def default_session_path() -> Path:
    """Return the platform user config session path."""
    config_home = os.environ.get("HIRINGCAFE_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "session.json"
    return Path.home() / ".config" / "hiringcafe-cli" / "session.json"


def store() -> SessionStore:
    """Create the session store using the selected configuration root."""
    return SessionStore(default_session_path())


def import_token(argv: object, json_output: bool = False) -> int:
    """Import a refresh token through stdin or the nonprinting environment."""
    token = sys.stdin.readline().strip() or os.environ.get("HIRINGCAFE_REFRESH_TOKEN", "")
    if not token:
        print("hiringcafe: no refresh token provided on stdin or HIRINGCAFE_REFRESH_TOKEN", file=sys.stderr)
        return 2
    credentials = FirebaseClient().refresh(token)
    store().save(credentials["refreshToken"])
    print("Authenticated Firebase session saved")
    return 0


def login_email(argv: object, json_output: bool = False) -> int:
    """Exchange Firebase email/password credentials once and save only the refresh token."""
    password = os.environ.get("HIRINGCAFE_PASSWORD") or getpass.getpass("Firebase password: ")
    credentials = FirebaseClient().login_with_password(argv.email, password)
    del password
    store().save(credentials["refreshToken"])
    print("Authenticated Firebase session saved")
    return 0


def status(argv: object, json_output: bool = False) -> int:
    """Report whether the stored Firebase credential can obtain an ID token.

    Args:
        argv: Unused CLI namespace.
        json_output: Whether stdout must be machine-readable.

    Returns:
        Exit code 0 when usable, 4 when no session exists.
    """
    session = store().load()
    if session is None:
        if json_output:
            print(json.dumps({"version": 1, "authenticated": False}, separators=(",", ":")))
        else:
            print("No stored credential", file=sys.stderr)
        return 4
    credentials = FirebaseClient().refresh(session.refresh_token)
    if json_output:
        payload = json.dumps(
            {"version": 1, "authenticated": True},
            separators=(",", ":"),
        )
        print(payload)
    else:
        print("Authenticated")
    return 0
