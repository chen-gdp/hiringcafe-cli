"""Bounded reads for external HTTP responses."""

RESPONSE_LIMIT_BYTES = 8 * 1024 * 1024


def read_limited(response, endpoint: str, limit: int = RESPONSE_LIMIT_BYTES) -> bytes:
    """Read an HTTP response without trusting its size.

    Args:
        response: An open ``http.client.HTTPResponse``-compatible object.
        endpoint: Stable endpoint name used in diagnostics.
        limit: Maximum accepted response size in bytes.

    Returns:
        The complete response body when it is within ``limit``.

    Raises:
        ValueError: If the response exceeds ``limit``.
    """
    body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError(f"{endpoint} response exceeds {limit} bytes")
    return body
