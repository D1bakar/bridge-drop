"""M0 upload: bytes intact, traversal blocked, collisions renamed, no .part left."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import UPLOAD_ROOT, app  # noqa: E402

client = TestClient(app)


def _clean(*names):
    for n in names:
        for p in (UPLOAD_ROOT / n, UPLOAD_ROOT / (n + ".part")):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass


def test_upload_roundtrip():
    _clean("hello.txt", "hello (1).txt")
    data = b"hello bridge " * 1000
    r = client.post("/v1/files", files={"file": ("hello.txt", data)})
    assert r.status_code == 201
    assert r.json()["name"] == "hello.txt"
    assert (UPLOAD_ROOT / "hello.txt").read_bytes() == data
    assert not (UPLOAD_ROOT / "hello.txt.part").exists()
    # collision → renamed, original kept
    r2 = client.post("/v1/files", files={"file": ("hello.txt", b"v2")})
    assert r2.json()["name"] == "hello (1).txt"
    assert (UPLOAD_ROOT / "hello (1).txt").read_bytes() == b"v2"
    _clean("hello.txt", "hello (1).txt")


def test_traversal_blocked():
    _clean("evil.txt")
    r = client.post("/v1/files", files={"file": ("../../evil.txt", b"x")})
    assert r.status_code == 201
    assert r.json()["name"] == "evil.txt"
    assert (UPLOAD_ROOT / "evil.txt").exists()
    assert not (UPLOAD_ROOT.parent / "evil.txt").exists()
    _clean("evil.txt")
