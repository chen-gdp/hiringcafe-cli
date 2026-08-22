#!/usr/bin/env python3
"""Verify release artifacts before publication."""

from __future__ import annotations

import argparse
import re
import sys
import tarfile
import zipfile
from pathlib import Path

_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?")
_FORBIDDEN_FILES = {".env", ".gitconfig", "session.json"}
_FORBIDDEN_TEXT_PATTERN = re.compile(r"(?im)^\s*(?:refresh_?token|id_?token)\s*=\s*[^\s*]{8,}\s*$")
_TEXT_SUFFIXES = (".py", ".md", ".toml", ".txt", ".yaml", ".yml")
_MAX_MEMBER_BYTES = 1024 * 1024


def _validate_member(name: str) -> None:
    """Reject unsafe or forbidden archive members."""
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or path.drive:
        raise ValueError(f"unsafe archive member: {name}")
    if path.name in _FORBIDDEN_FILES or any(part in {".git", ".venv", "dist"} for part in path.parts):
        raise ValueError(f"forbidden archive member: {name}")


def _validate_text(name: str, data: bytes) -> None:
    """Scan bounded text payloads for credential-shaped secrets."""
    if len(data) > _MAX_MEMBER_BYTES:
        raise ValueError(f"oversized text member: {name}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"non-UTF-8 text member: {name}") from error
    if _FORBIDDEN_TEXT_PATTERN.search(text):
        raise ValueError(f"credential-shaped content in archive member: {name}")


def _validate_metadata(metadata: str, version: str) -> None:
    """Validate core package metadata."""
    if f"Version: {version}\n" not in metadata:
        raise ValueError("package metadata version mismatch")
    if not metadata.startswith(("Metadata-Version:", "Name:")):
        raise ValueError("invalid package metadata header")


def _validate_sdist(path: Path, version: str) -> None:
    """Validate the source distribution."""
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            _validate_member(member.name)
        metadata = next((member for member in members if member.name.endswith("/PKG-INFO")), None)
        if metadata is None or metadata.size > _MAX_MEMBER_BYTES:
            raise ValueError("sdist is missing valid PKG-INFO")
        pkg_info = archive.extractfile(metadata)
        if pkg_info is None:
            raise ValueError("sdist PKG-INFO cannot be read")
        _validate_metadata(pkg_info.read().decode("utf-8"), version)
        for member in members:
            if not member.isfile() or not member.name.endswith(_TEXT_SUFFIXES):
                continue
            if member.size > _MAX_MEMBER_BYTES:
                raise ValueError(f"oversized text member: {member.name}")
            file = archive.extractfile(member)
            if file is not None:
                _validate_text(member.name, file.read())


def _validate_wheel(path: Path, version: str) -> None:
    """Validate the universal wheel."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for name in names:
            _validate_member(name)
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        if metadata_name is None:
            raise ValueError("wheel is missing METADATA")
        _validate_metadata(archive.read(metadata_name).decode("utf-8"), version)
        requirements = next((name for name in names if name.endswith(".dist-info/REQUIRES-DIST")), None)
        if requirements is not None and archive.read(requirements).strip():
            raise ValueError("runtime dependencies are not allowed")
        for name in names:
            if name.endswith(_TEXT_SUFFIXES):
                _validate_text(name, archive.read(name))


def verify(dist_dir: Path, version: str) -> None:
    """Verify that a release directory contains exactly one safe sdist and wheel.

    Args:
        dist_dir: Directory containing artifacts built by ``uv build``.
        version: Exact release version without the leading ``v``.

    Raises:
        ValueError: If artifact names, metadata, contents, or checksums are invalid.
    """
    if not _VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"invalid release version: {version}")
    sdists = list(dist_dir.glob("*.tar.gz"))
    wheels = list(dist_dir.glob("*.whl"))
    if len(sdists) != 1 or len(wheels) != 1:
        raise ValueError("release must contain exactly one sdist and one wheel")
    if version not in sdists[0].name or version not in wheels[0].name:
        raise ValueError("artifact filename version mismatch")
    _validate_sdist(sdists[0], version)
    _validate_wheel(wheels[0], version)


def main(argv: list[str] | None = None) -> int:
    """Run the artifact verifier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", type=Path)
    parser.add_argument("version")
    args = parser.parse_args(argv)
    try:
        verify(args.dist_dir, args.version)
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"artifact verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
