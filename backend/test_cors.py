"""CORS preflight cover for M0 web mode (Live Server + phone browsers)."""

from fastapi.testclient import TestClient

from app import app, get_lan_ip

client = TestClient(app)


def test_info_ok():
    r = client.get("/v1/info")
    assert r.status_code == 200
    assert r.json()["id"] == "pc-1"


def test_cors_preflight():
    r = client.options(
        "/v1/info",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"


def test_get_lan_ip_returns_ipv4():
    ip = get_lan_ip()
    parts = ip.split(".")
    assert len(parts) == 4
    assert all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def test_serves_web_ui_single_terminal():
    # M0 single-terminal: backend serves the page — no Live Server needed.
    r = client.get("/")
    assert r.status_code == 200
    assert "Bridge" in r.text
    assert "dropzone" in r.text.lower()
    for path in ("/css/tokens.css", "/js/mock.js", "/js/upload.js"):
        s = client.get(path)
        assert s.status_code == 200, path
