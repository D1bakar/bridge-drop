"""Device info carries the pair hint: exact LAN URL the phone must open."""

from fastapi.testclient import TestClient

import app as backend_app

client = TestClient(backend_app.app)


def test_info_has_lan_url():
    body = client.get("/v1/info").json()
    assert body["lan_url"].startswith("http://")
    assert body["lan_url"].endswith(":8000/")
