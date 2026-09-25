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

from app import app as _app  # noqa: E402
from urllib.parse import parse_qsl


class VercelPathRestoreMiddleware:
    """Vercel invokes the function with the rewritten path (/api/index).

    vercel.json forwards the original path as ?__route=/v1/..., so restore
    it before routing. Local runs never set __route — untouched there.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            try:
                qs = parse_qsl((scope.get("query_string") or b"").decode("utf-8"))
            except Exception:
                qs = []
            for key, value in qs:
                if key == "__route" and value.startswith("/"):
                    scope["path"] = value
                    scope["raw_path"] = value.encode("utf-8")
                    break
        await self.inner(scope, receive, send)


app = VercelPathRestoreMiddleware(_app)
