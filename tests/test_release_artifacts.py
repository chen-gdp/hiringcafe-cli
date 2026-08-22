"""Tests for release artifact verification."""

from __future__ import annotations

import importlib.util
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path


def _load_verifier():
    path = Path(__file__).parents[1] / "scripts" / "verify_release_artifacts.py"
    spec = importlib.util.spec_from_file_location("verify_release_artifacts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load release artifact verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify


verify = _load_verifier()


def _write_archive(root: Path, *, include_secret: bool = False) -> None:
    secret = b"refresh_token=synthetic-secret\n" if include_secret else b""
    with zipfile.ZipFile(root / "hiringcafe_cli-0.1.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("hiringcafe_cli/__init__.py", secret)
        wheel.writestr(
            "hiringcafe_cli-0.1.0.dist-info/METADATA",
            "Name: hiringcafe-cli\nVersion: 0.1.0\n",
        )
        wheel.writestr("hiringcafe_cli-0.1.0.dist-info/REQUIRES-DIST", b"")
    with tarfile.open(root / "hiringcafe_cli-0.1.0.tar.gz", "w:gz") as source:
        info = tarfile.TarInfo("hiringcafe_cli-0.1.0/PKG-INFO")
        payload = b"Name: hiringcafe-cli\nVersion: 0.1.0\n" + secret
        info.size = len(payload)
        source.addfile(info, BytesIO(payload))


def test_verify_release_artifacts_accepts_safe_package(tmp_path: Path) -> None:
    """Condition: one wheel and one sdist with matching metadata.

    Expected: verification succeeds.
    """
    _write_archive(tmp_path)

    verify(tmp_path, "0.1.0")


def test_verify_release_artifacts_rejects_credential_text(tmp_path: Path) -> None:
    """Condition: an archive text member contains a credential-shaped token.

    Expected: verification fails without publishing.
    """
    _write_archive(tmp_path, include_secret=True)

    try:
        verify(tmp_path, "0.1.0")
    except ValueError as error:
        assert "credential-shaped" in str(error)
    else:
        raise AssertionError("secret-bearing artifact passed verification")
