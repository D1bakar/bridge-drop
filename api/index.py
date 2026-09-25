"""Vercel serverless entry — re-exports the Bridge FastAPI app.

Storage is ephemeral (/tmp): uploads + SQLite vanish between cold starts.
Good for try-anywhere demo + PWA install; the LAN run stays the real product.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("BRIDGE_DB", "/tmp/bridge.db")
os.environ.setdefault("BRIDGE_UPLOAD_DIR", "/tmp/bridge-uploads")

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app import app  # noqa: E402
