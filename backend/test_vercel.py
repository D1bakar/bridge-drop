"""Vercel deploy config stays valid: rewrites hit the function, entry is serverless-safe."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_vercel_rewrites_api():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    assert any("/api/index" in r["destination"] for r in cfg["rewrites"])
    assert any("/v1/" in r["source"] for r in cfg["rewrites"])


def test_api_entry_points_at_backend():
    src = (ROOT / "api" / "index.py").read_text()
    assert "/tmp/bridge.db" in src and "BRIDGE_UPLOAD_DIR" in src
    assert "from app import app" in src


def test_root_requirements_pinned():
    txt = (ROOT / "requirements.txt").read_text()
    assert "fastapi==" in txt and "qrcode" in txt
