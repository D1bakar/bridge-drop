"""Settings (device name, auto-accept, visibility) + save rules CRUD."""

import db
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def setup_function(_):
    db.set_setting("device_name", "My PC")
    db.set_setting("auto_accept", "1")
    db.set_setting("visibility", "visible")
    db.set_setting("rules", "[]")


def teardown_function(_):
    setup_function(_)


def test_settings_roundtrip_and_info_mirror():
    s = client.get("/v1/settings").json()
    assert s["device_name"] == "My PC" and s["auto_accept"] is True
    assert client.get("/v1/info").json()["name"] == "My PC"
    p = client.patch("/v1/settings", json={"device_name": "Studio", "auto_accept": False,
                                           "visibility": "hidden"}).json()
    assert p == {"device_name": "Studio", "auto_accept": False, "visibility": "hidden"}
    assert client.get("/v1/info").json()["name"] == "Studio"
    assert client.patch("/v1/settings", json={"device_name": "  "}).status_code == 422
    assert client.patch("/v1/settings", json={"visibility": "nope"}).status_code == 422


def test_rules_crud():
    assert client.get("/v1/rules").json() == {"rules": []}
    r = client.post("/v1/rules", json={"ext": ".mp4", "dir": "Videos"}).json()
    assert r["rules"] == [{"ext": ".mp4", "dir": "Videos"}]
    # replace same ext
    r2 = client.post("/v1/rules", json={"ext": ".MP4", "dir": "Clips"}).json()
    assert r2["rules"] == [{"ext": ".mp4", "dir": "Clips"}]
    assert client.post("/v1/rules", json={"ext": "mp4", "dir": "x"}).status_code == 422
    assert client.post("/v1/rules", json={"ext": ".mp4", "dir": "../evil"}).json()["rules"][0]["dir"] == "evil"
    d = client.delete("/v1/rules", params={"ext": ".mp4"}).json()
    assert d["rules"] == []
