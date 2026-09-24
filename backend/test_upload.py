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


def test_list_files():
    _clean("a.txt", "b.txt")
    client.post("/v1/files", files={"file": ("a.txt", b"aaa")})
    client.post("/v1/files", files={"file": ("b.txt", b"bb")})
    r = client.get("/v1/files")
    assert r.status_code == 200
    names = [f["name"] for f in r.json()["files"]]
    assert "a.txt" in names and "b.txt" in names
    assert all(f["size"] >= 0 and "mtime" in f for f in r.json()["files"])
    _clean("a.txt", "b.txt")


def test_download_roundtrip():
    _clean("dl.txt")
    data = b"download me " * 500
    client.post("/v1/files", files={"file": ("dl.txt", data)})
    r = client.get("/v1/files/dl.txt")
    assert r.status_code == 200
    assert r.content == data
    _clean("dl.txt")


def test_download_guards():
    assert client.get("/v1/files/nope-nothing.txt").status_code == 404
    assert client.get("/v1/files/.gitkeep").status_code == 404
    assert client.get("/v1/files/..%2Fapp.py").status_code in (404, 422)
    _clean("app.py")
