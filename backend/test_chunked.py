"""Chunked resumable uploads: init/chunk/status/complete, resume, hash, cancel."""

import hashlib

import db
from fastapi.testclient import TestClient

from app import UPLOAD_ROOT, app

client = TestClient(app)


def setup_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM chunked")
        conn.execute("DELETE FROM transfers")
        conn.commit()


def teardown_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM chunked")
        conn.execute("DELETE FROM transfers")
        conn.commit()
    for p in UPLOAD_ROOT.rglob("*"):
        if p.is_file() and (p.suffix == ".part" or p.name.startswith(".up-")):
            try:
                p.unlink()
            except OSError:
                pass


def _put(uid, data, offset):
    return client.put(f"/v1/uploads/{uid}/chunk", params={"offset": offset},
                      content=data,
                      headers={"Content-Type": "application/octet-stream"})


def test_full_flow_with_hash():
    data = b"chunked hello " * 5000  # 70KB
    sha = hashlib.sha256(data).hexdigest()
    uid = client.post("/v1/uploads/init", json={
        "name": "big.bin", "size": len(data), "sha256": sha}).json()["uploadId"]
    # two chunks
    assert _put(uid, data[:30000], 0).json()["offset"] == 30000
    assert client.get(f"/v1/uploads/{uid}/status").json()["offset"] == 30000
    assert _put(uid, data[30000:], 30000).json()["offset"] == len(data)
    r = client.post(f"/v1/uploads/{uid}/complete", json={"sha256": sha})
    assert r.status_code == 200
    assert r.json()["sha256"] == sha
    assert (UPLOAD_ROOT / "big.bin").read_bytes() == data
    (UPLOAD_ROOT / "big.bin").unlink()


def test_offset_mismatch_then_resume():
    data = b"resume-me Roman"
    uid = client.post("/v1/uploads/init", json={"name": "res.txt", "size": len(data)}).json()["uploadId"]
    assert _put(uid, data[:6], 0).status_code == 200
    bad = _put(uid, data, 0)
    assert bad.status_code == 409  # stale offset rejected
    # resume from confirmed offset
    assert _put(uid, data[6:], 6).json()["offset"] == len(data)
    assert client.post(f"/v1/uploads/{uid}/complete").status_code == 200
    assert (UPLOAD_ROOT / "res.txt").read_bytes() == data
    (UPLOAD_ROOT / "res.txt").unlink()


def test_hash_mismatch_rejected_and_cancel():
    data = b"tampered bytes here"
    uid = client.post("/v1/uploads/init", json={"name": "tamper.txt", "size": len(data)}).json()["uploadId"]
    _put(uid, data, 0)
    r = client.post(f"/v1/uploads/{uid}/complete", json={"sha256": "0" * 64})
    assert r.status_code == 422
    assert client.delete(f"/v1/uploads/{uid}").status_code == 200
    assert client.get(f"/v1/uploads/{uid}/status").json()["status"] == "cancelled"


def test_relpath_preserved_and_traversal_blocked():
    data = b"nested"
    uid = client.post("/v1/uploads/init", json={
        "name": "n.txt", "size": len(data), "relPath": "a/b/../../c"}).json()["uploadId"]
    _put(uid, data, 0)
    out = client.post(f"/v1/uploads/{uid}/complete").json()
    assert out["path"] == "c/n.txt", out
    assert (UPLOAD_ROOT / "c" / "n.txt").exists()
    import shutil
    shutil.rmtree(UPLOAD_ROOT / "c")


def test_rules_route_by_extension():
    db.set_setting("rules", '[{"ext": ".mp4", "dir": "Videos"}]')
    try:
        data = b"fake-video"
        uid = client.post("/v1/uploads/init", json={"name": "clip.mp4", "size": len(data)}).json()["uploadId"]
        _put(uid, data, 0)
        out = client.post(f"/v1/uploads/{uid}/complete").json()
        assert out["path"] == "Videos/clip.mp4", out
        assert (UPLOAD_ROOT / "Videos" / "clip.mp4").exists()
        import shutil
        shutil.rmtree(UPLOAD_ROOT / "Videos")
    finally:
        db.set_setting("rules", "[]")


def test_init_reattaches_interrupted_upload():
    data = b"interrupt me please...."
    first = client.post("/v1/uploads/init", json={
        "name": "big.iso", "size": len(data), "client_key": "fp-1"}).json()
    assert first["resumed"] is False
    uid = first["uploadId"]
    assert _put(uid, data[:8], 0).json()["offset"] == 8
    # Tab killed, tab reopened: same key re-attaches at confirmed bytes.
    again = client.post("/v1/uploads/init", json={
        "name": "big.iso", "size": len(data), "client_key": "fp-1"}).json()
    assert again["uploadId"] == uid
    assert again["offset"] == 8
    assert again["resumed"] is True
    assert _put(uid, data[8:], 8).json()["offset"] == len(data)
    assert client.post(f"/v1/uploads/{uid}/complete").status_code == 200
    assert (UPLOAD_ROOT / "big.iso").read_bytes() == data
    (UPLOAD_ROOT / "big.iso").unlink()


def test_resume_key_ignores_size_change():
    data = b"changed file!!"
    uid = client.post("/v1/uploads/init", json={
        "name": "edit.bin", "size": len(data), "client_key": "fp-2"}).json()["uploadId"]
    assert _put(uid, data[:4], 0).status_code == 200
    other = client.post("/v1/uploads/init", json={
        "name": "edit.bin", "size": len(data) + 10, "client_key": "fp-2"}).json()
    assert other["uploadId"] != uid
    assert other["resumed"] is False
    assert client.delete(f"/v1/uploads/{uid}").status_code == 200
    assert client.delete(f"/v1/uploads/{other['uploadId']}").status_code == 200


def test_send_page_sends_stable_key():
    js = client.get("/js/batch.js").text
    assert "client_key" in js
    assert "Resumed" in js
