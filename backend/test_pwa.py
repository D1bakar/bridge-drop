"""PWA installable: manifest, service worker, icons served with correct types."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_manifest_served():
    r = client.get("/manifest.webmanifest")
    assert r.status_code == 200
    body = r.json()
    assert body["name"].startswith("Bridge")
    assert body["start_url"] == "/"
    assert body["display"] == "standalone"
    sizes = {i["sizes"] for i in body["icons"]}
    assert "192x192" in sizes and "512x512" in sizes


def test_service_worker_served():
    r = client.get("/sw.js")
    assert r.status_code == 200
    assert "const CACHE = 'bridge-v" in r.text
    assert "/v1/" in r.text  # API stays network-only
    assert "/css/apple.css" in r.text  # new layers must reach phones, not stale cache


def test_icons_served():
    for path in ("/icons/bridge-192.png", "/icons/bridge-512.png"):
        r = client.get(path)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/png")
        assert len(r.content) > 500


def test_pages_link_manifest():
    for page in ("/", "/send.html", "/history.html", "/pair.html", "/settings.html"):
        html = client.get(page).text
        assert "/manifest.webmanifest" in html, page
        assert "js/pwa.js" in html, page
