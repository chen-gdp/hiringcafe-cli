"""Shared Firebase response doubles."""

import io


class BytesResponse(io.BytesIO):
    """BytesIO context manager shaped like urlopen's response."""

    def __enter__(self):
        """Return the response body."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Close after the request."""
        self.close()
