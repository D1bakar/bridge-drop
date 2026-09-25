"""Release stays shippable: VERSION matches /v1/info, bundle script stays clean."""

from pathlib import Path

from fastapi.testclient import TestClient

import app as backend_app

ROOT = Path(__file__).resolve().parent.parent
client = TestClient(backend_app.app)


def test_version_file_matches_info():
    want = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert want
    assert client.get("/v1/info").json()["version"] == want


def test_bundle_script_includes_boot_excludes_local():
    # Allowlist design: backend stage copies exactly three runtime files, so
    # tests, caches, and the local DB can never leak into the zip.
    src = (ROOT / "build-release.ps1").read_text(encoding="utf-8")
    for keep in ("start-bridge.bat", "backend/app.py", "index.html", "sw.js"):
        assert keep in src, keep
    for runtime in ("backend/app.py", "backend/db.py", "backend/requirements.txt"):
        assert runtime in src, runtime
    assert "test_" not in src and "__pycache__" not in src and "bridge.db" not in src


def test_bundle_boot_files_present():
    for p in ("VERSION", "README.md", "start-bridge.bat", "manifest.webmanifest",
              "sw.js", "index.html", "backend/app.py", "backend/db.py",
              "backend/requirements.txt"):
        assert (ROOT / p).is_file(), p
