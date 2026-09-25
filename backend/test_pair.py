"""Pairing: one-time codes, QR art, claim → trusted device, rename/revoke."""

import io
import time

import db
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def setup_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM pair_codes")
        conn.execute("DELETE FROM devices")
        conn.commit()


def teardown_function(_):
    with db.connect() as conn:
        conn.execute("DELETE FROM pair_codes")
        conn.execute("DELETE FROM devices")
        conn.execute("DELETE FROM chunked")
        conn.execute("DELETE FROM transfers WHERE name='g.txt'")
        conn.commit()
    from app import UPLOAD_ROOT

    for n in ("g.txt",):
        try:
            (UPLOAD_ROOT / n).unlink(missing_ok=True)
        except OSError:
            pass


def test_code_qr_claim_list_rename_revoke():
    c = client.post("/v1/pair/code").json()
    assert len(c["code"]) == 6 and c["code"].isdigit()
    assert c["url"].endswith(f"?code={c['code']}")
    qr = client.get("/v1/pair/qr")
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert qr.content[:8] == b"\x89PNG\r\n\x1a\n"
    # explicit code param also works
    assert client.get("/v1/pair/qr", params={"code": c["code"]}).status_code == 200
    claim = client.post("/v1/pair/claim", json={
        "code": c["code"], "name": "Test Phone", "platform": "Android"}).json()
    assert claim["deviceToken"] and claim["fingerprint"]
    # single use: second claim fails
    assert client.post("/v1/pair/claim", json={"code": c["code"]}).status_code == 403
    devs = client.get("/v1/devices").json()["devices"]
    assert len(devs) == 1 and devs[0]["name"] == "Test Phone"
    did = devs[0]["id"]
    assert client.patch(f"/v1/devices/{did}", json={"name": "Pixel"}).json()["name"] == "Pixel"
    assert client.patch("/v1/devices/nope", json={"name": "x"}).status_code == 404
    assert client.delete(f"/v1/devices/{did}").status_code == 200
    assert client.get("/v1/devices").json()["devices"] == []


def test_bad_and_expired_codes_rejected():
    assert client.post("/v1/pair/claim", json={"code": "000000"}).status_code == 403
    c = client.post("/v1/pair/code").json()["code"]
    with db.connect() as conn:
        conn.execute("UPDATE pair_codes SET expires_at=? WHERE code=?", (time.time() - 1, c))
        conn.commit()
    assert client.post("/v1/pair/claim", json={"code": c}).status_code == 403
    assert client.get("/v1/pair/qr").status_code == 404


def test_guest_upload_pending_then_accepted_when_auto_accept_off():
    db.set_setting("auto_accept", "0")
    try:
        code = client.post("/v1/pair/code").json()["code"]
        data = b"guest file bytes"
        uid = client.post("/v1/uploads/init", json={"name": "g.txt", "size": len(data)},
                          params={"code": code}).json()["uploadId"]
        assert uid
        from test_chunked import _put
        _put(uid, data, 0)
        out = client.post(f"/v1/uploads/{uid}/complete").json()
        assert out.get("pending") is True
        feed = client.get("/v1/feed").json()["items"]
        assert any(i["id"] == out["id"] and i["status"] == "pending" for i in feed)
        acc = client.post(f"/v1/uploads/{uid}/accept").json()
        assert acc["name"] == "g.txt"
        from app import UPLOAD_ROOT
        assert (UPLOAD_ROOT / "g.txt").read_bytes() == data
        (UPLOAD_ROOT / "g.txt").unlink()
    finally:
        db.set_setting("auto_accept", "1")
