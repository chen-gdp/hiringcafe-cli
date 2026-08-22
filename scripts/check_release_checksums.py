#!/usr/bin/env python3
"""Verify downloaded release artifact checksums."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def check_checksums(dist_dir: Path) -> None:
    """Verify every checksum entry against its artifact.

    Args:
        dist_dir: Directory containing ``hiringcafe-cli.sha256`` and artifacts.

    Raises:
        ValueError: If the checksum file is missing, malformed, or does not match.
    """
    checksum_path = dist_dir / "hiringcafe-cli.sha256"
    if not checksum_path.is_file():
        raise ValueError("missing hiringcafe-cli.sha256")
    entries = 0
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if not separator or not digest or not name:
            raise ValueError(f"malformed checksum line: {line}")
        path = dist_dir / name
        if not path.is_file():
            raise ValueError(f"missing checksum artifact: {name}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"checksum mismatch: {name}")
        entries += 1
    if entries != 2:
        raise ValueError(f"expected exactly 2 checksum entries, found {entries}")


def main() -> int:
    """Run the checksum verifier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", type=Path)
    args = parser.parse_args()
    try:
        check_checksums(args.dist_dir)
    except (OSError, ValueError) as error:
        print(f"checksum verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
