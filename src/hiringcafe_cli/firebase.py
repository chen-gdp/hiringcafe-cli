"""Firebase Identity Toolkit REST adapter."""

import json
import urllib.error
import urllib.parse
import urllib.request
from urllib.request import urlopen

FIREBASE_WEB_API_KEY = "AIzaSyBggiJ0ZSnwXoh1JILiairK8I3_BzI1V1E"
PROJECT_ID = "hiringcafe-ec4d6"


class FirebaseAuthError(RuntimeError):
    """Firebase rejected the credential."""


class FirebaseTransportError(RuntimeError):
    """Firebase could not be reached."""


class FirebaseClient:
    """Client for the public Firebase Identity Toolkit endpoints."""

    post = staticmethod(urlopen)

    def refresh(self, refresh_token: str) -> dict:
        """Exchange a refresh token for fresh credentials.

        Args:
            refresh_token: Stored Firebase refresh token.

        Returns:
            Firebase token response containing an ephemeral ID token.
        """
        query = urllib.parse.urlencode({"key": FIREBASE_WEB_API_KEY})
        body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}).encode()
        payload = self._post(
            f"https://securetoken.googleapis.com/v1/token?{query}",
            body,
        )
        if "id_token" not in payload or "refresh_token" not in payload:
            raise ValueError("Firebase token response is missing required fields")
        return {
            "idToken": payload["id_token"],
            "refreshToken": payload["refresh_token"],
            "userId": payload.get("user_id"),
        }

    def login_with_password(self, email: str, password: str) -> dict:
        """Exchange Firebase email/password credentials once.

        Args:
            email: User's Firebase account email.
            password: Password used in memory for exactly this request.

        Returns:
            Firebase sign-in response containing the durable refresh token.
        """
        query = urllib.parse.urlencode({"key": FIREBASE_WEB_API_KEY})
        body = json.dumps({"email": email, "password": password, "returnSecureToken": True}).encode()
        payload = self._post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?{query}",
            body,
            {"Content-Type": "application/json"},
        )
        if "refreshToken" not in payload:
            raise ValueError("Firebase sign-in response has no refresh token")
        return payload

    def _post(self, url: str, body: bytes, extra_headers: dict | None = None, timeout: float = 30) -> dict:
        """POST JSON or form data and parse a JSON object response."""
        headers = {"Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with self.post(request, timeout=timeout) as response:
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            if error.code == 400:
                raise FirebaseAuthError("Firebase rejected the credential") from error
            raise FirebaseTransportError(f"Firebase returned HTTP {error.code}") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise FirebaseTransportError("Firebase transport failed") from error
        try:
            value = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError("invalid Firebase JSON response") from error
        if not isinstance(value, dict):
            raise ValueError("Firebase response is not an object")
        return value
