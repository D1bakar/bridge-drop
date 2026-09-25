"""Persistent feed: uploads recorded with hash, feed lists/searches, delete works."""

import db
from fastapi.testclient import TestClient

from app import UPLOAD_ROOT, app

client = TestClient(app)


def _clean_db():
    with db.connect() as conn:
        conn.execute("DELETE FROM transfers")
        conn.commit()


def _clean_disk(*names):
    for n in names:
        for p in (UPLOAD_ROOT / n, UPLOAD_ROOT / (n + ".part")):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass


def test_upload_recorded_with_hash_and_feed():
    _clean_db()
    _clean_disk("feed1.txt")
    data = b"feed me " * 200
    r = client.post("/v1/files", files={"file": ("feed1.txt", data)})
    assert r.status_code == 201
    body = r.json()
    assert len(body["sha256"]) == 64
    assert body["id"]
    f = client.get("/v1/feed").json()["items"]
    assert any(i["type"] == "file" and i["name"] == "feed1.txt" for i in f)
    assert any(i.get("sha256") == body["sha256"] for i in f if i["type"] == "file")
    # search finds it, nonsense doesn't
    assert any(i["name"] == "feed1.txt" for i in client.get("/v1/feed", params={"q": "feed1"}).json()["items"])
    assert not client.get("/v1/feed", params={"q": "zzz-no-such-zzz"}).json()["items"]
    _clean_disk("feed1.txt")
    _clean_db()


def test_delete_transfer_removes_row_and_optionally_file():
    _clean_db()
    _clean_disk("del1.txt")
    tid = client.post("/v1/files", files={"file": ("del1.txt", b"bye")}).json()["id"]
    assert (UPLOAD_ROOT / "del1.txt").exists()
    r = client.delete(f"/v1/feed/file/{tid}")
    assert r.status_code == 200
    assert (UPLOAD_ROOT / "del1.txt").exists()  # history gone, file kept
    assert client.delete(f"/v1/feed/file/{tid}").status_code == 404
    tid2 = client.post("/v1/files", files={"file": ("del1.txt", b"bye2")}).json()["id"]
    row = client.get("/v1/feed").json()["items"]
    name2 = next(i["name"] for i in row if i["id"] == tid2)
    client.delete(f"/v1/feed/file/{tid2}", params={"delete_file": True})
    assert not (UPLOAD_ROOT / name2).exists()
    _clean_disk("del1.txt", "del1 (1).txt")
    _clean_db()
