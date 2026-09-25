"""Vercel deploy config stays valid: rewrites hit the function, entry is serverless-safe."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_vercel_rewrites_api():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    assert any("/api/index" in r["destination"] for r in cfg["rewrites"])
    assert any("/v1/" in r["source"] for r in cfg["rewrites"])
    # Original path must survive the rewrite or every call 404s as /api/index.
    assert any("__route=/v1/" in r["destination"] for r in cfg["rewrites"])


def test_api_entry_points_at_backend():
    src = (ROOT / "api" / "index.py").read_text()
    assert "/tmp/bridge.db" in src and "BRIDGE_UPLOAD_DIR" in src
    assert "from app import app" in src


def test_pair_url_echoes_request_host():
    # Cloud QR must encode the public host, never the container's 169.254 IP.
    import app as backend_app
    from fastapi.testclient import TestClient

    c = TestClient(backend_app.app)
    body = c.post("/v1/pair/code", headers={
        "host": "bridge-demo.vercel.app", "x-forwarded-proto": "https"}).json()
    assert body["url"] == f"https://bridge-demo.vercel.app/?code={body['code']}"
    assert "169.254" not in body["url"]


def test_root_requirements_pinned():
    txt = (ROOT / "requirements.txt").read_text()
    assert "fastapi==" in txt and "qrcode" in txt


def test_path_restore_middleware_routes_rewritten_calls():
    """Simulate Vercel: function sees /api/index?__route=/v1/info → 200."""
    import importlib.util
    import os
    import tempfile

    tmp = tempfile.mkdtemp(prefix="bridge-rewrite-")
    os.environ["BRIDGE_DB"] = os.path.join(tmp, "bridge.db")
    os.environ["BRIDGE_UPLOAD_DIR"] = os.path.join(tmp, "uploads")
    try:
        spec = importlib.util.spec_from_file_location(
            "bridge_api_index", str(ROOT / "api" / "index.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        from fastapi.testclient import TestClient

        c = TestClient(mod.app)
        assert c.get("/api/index", params={"__route": "/v1/info"}).status_code == 200
        assert c.get("/api/index").status_code == 404  # no route, no restore
    finally:
        os.environ.pop("BRIDGE_DB", None)
        os.environ.pop("BRIDGE_UPLOAD_DIR", None)
