"""Bridge M0 backend skeleton — PRD §9 contract starts here.

Run (single terminal, from backend/):
  python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
  open http://127.0.0.1:8000/ on PC, http://<LAN-IP>:8000/ on phone (same Wi-Fi).
Contract (frontend untouched, still on mock.js):
  GET /v1/info — device info + capabilities
"""

from pathlib import Path
import hashlib
import mimetypes
import socket
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import db


def get_lan_ip() -> str:
    # M0 LAN run: phone browsers need the PC's LAN IP, not localhost (prd §4 M0).
    # UDP trick — no packets sent. Falls back to localhost when offline.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return "127.0.0.1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # M0 gate (prd §4): print what the phone browser must open.
    # --host 0.0.0.0 required; localhost alone is unreachable from the phone.
    import db

    db.init_db()
    # Defaults for a fresh install (PRD FR-30). Never overwrite user choices.
    if not db.get_setting("device_name"):
        db.set_setting("device_name", "My PC")
    if not db.get_setting("auto_accept"):
        db.set_setting("auto_accept", "1")
    ip = get_lan_ip()
    print("Bridge M0 up — PC:   http://127.0.0.1:8000/", flush=True)
    print(f"Bridge M0 up — Phone (same Wi-Fi): http://{ip}:8000/", flush=True)
    yield


app = FastAPI(title="Bridge M0", lifespan=lifespan)

# M0 LAN-only: allow Live Server + phone browsers. TODO(prd §10): pin origins + TLS + auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)


UPLOAD_ROOT = Path(__file__).parent / "uploads"
UPLOAD_ROOT.mkdir(exist_ok=True)

# Single-terminal M0: serve the web-mode UI from the backend so the phone
# opens one URL (no Live Server, no CORS, no host guessing). PRD §4 M0.
WEB_ROOT = Path(__file__).parent.parent

try:
    from fastapi.staticfiles import StaticFiles

    for _dirname in ("css", "js"):
        _d = WEB_ROOT / _dirname
        if _d.is_dir():
            app.mount(f"/{_dirname}", StaticFiles(directory=str(_d)), name=_dirname)
except Exception:
    pass


_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

# Unknown-sender rate limit (PRD §10): per-IP failed-auth timestamps.
_FAILS: dict[str, list[float]] = {}
_FAIL_WINDOW = 600.0
_FAIL_MAX = 20


def _client_ip(request) -> str:
    try:
        return request.client.host if request.client else "unknown"
    except Exception:
        return "unknown"


def _note_fail(ip: str) -> None:
    import time

    now = time.time()
    lst = [t for t in _FAILS.get(ip, []) if now - t < _FAIL_WINDOW]
    lst.append(now)
    _FAILS[ip] = lst


def _fail_count(ip: str) -> int:
    import time

    now = time.time()
    return sum(1 for t in _FAILS.get(ip, []) if now - t < _FAIL_WINDOW)


def resolve_peer(request, db_conn=None) -> tuple[str, bool]:
    """Return (peer_id, known). Known = paired device token or live pair code.

    Credentials: X-Device-Token header (paired) or ?code=/X-Bridge-Code (guest).
    """
    import time

    token = request.headers.get("x-device-token", "") if hasattr(request, "headers") else ""
    code = ""
    try:
        code = request.query_params.get("code", "") or request.headers.get("x-bridge-code", "")
    except Exception:
        code = ""
    close = False
    conn = db_conn or db.connect()
    close = db_conn is None
    try:
        if token:
            row = conn.execute(
                "SELECT id FROM devices WHERE token=? AND trusted=1", (token,)
            ).fetchone()
            if row:
                return row["id"], True
        if code:
            row = conn.execute(
                "SELECT code, expires_at, used FROM pair_codes WHERE code=?", (code,)
            ).fetchone()
            if row and not row["used"] and row["expires_at"] > time.time():
                return f"guest:{code}", True
        return "local", True  # same-machine / open LAN (M0); auto-accept gate applies
    finally:
        if close:
            conn.close()


def _auto_accept() -> bool:
    return db.get_setting("auto_accept", "1") == "1"


def record_transfer(peer_id, direction, kind, name, size, mime, sha256, status, saved_path):
    tid = uuid.uuid4().hex[:12]
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO transfers(id, peer_id, direction, kind, name, size, mime,"
            " sha256, status, saved_path, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (tid, peer_id, direction, kind, name, size, mime, sha256, status,
             saved_path, db.now()),
        )
        conn.commit()
    return tid


def sanitize_filename(name: str) -> str:
    # PRD §10: never write outside save root, handle .., reserved names, controls.
    base = (name or "").replace("\\", "/").split("/")[-1].strip()
    base = "".join(c for c in base if ord(c) >= 32 and c != "/")
    base = base.lstrip(". ")
    if not base:
        base = "file"
    stem, dot, ext = base.rpartition(".")
    if not stem:  # no ext or leading-dot name
        stem, ext = base, ""
    else:
        ext = "." + ext[:10]
    if stem.lower() in _RESERVED:
        stem = "_" + stem
    stem = stem[:120] or "file"
    return f"{stem}{ext}" if ext else stem


def unique_path(name: str) -> Path:
    safe = sanitize_filename(name)
    target = UPLOAD_ROOT / safe
    if not target.exists():
        return target
    stem, dot, ext = safe.rpartition(".")
    if not stem:
        stem, ext = safe, ""
    else:
        ext = "." + ext
    i = 1
    while True:
        candidate = UPLOAD_ROOT / f"{stem} ({i}){ext}"
        if not candidate.exists():
            return candidate
        i += 1


@app.get("/")
def root():
    # Web-mode UI. API health stays at GET /v1/info (no auth yet, M0 LAN only).
    from fastapi.responses import FileResponse

    index = WEB_ROOT / "index.html"
    if index.is_file():
        return FileResponse(path=str(index), media_type="text/html")
    return {"ok": True, "service": "bridge-m0"}


@app.get("/v1/info")
def info():
    # Mirrors js/mock.js MOCK_DEVICES[0] shape (PRD §9 Device). No auth yet (M0 LAN only).
    return {
        "id": "pc-1",
        "name": "My PC",
        "platform": "Windows",
        "version": "0.1.0",
        "capabilities": ["info", "files"],
        "trusted": True,
    }


@app.post("/v1/files", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    # PRD §7 reliability: stream to .part, rename on success — no partials in destination.
    target = unique_path(file.filename or "file")
    part = target.with_name(target.name + ".part")
    size = 0
    digest = hashlib.sha256()
    try:
        with part.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                digest.update(chunk)
                out.write(chunk)
        part.replace(target)
    except Exception as exc:
        try:
            if part.exists():
                part.unlink()
        except OSError:
            pass
        raise HTTPException(status_code=500, detail="upload failed") from exc
    finally:
        try:
            await file.close()
        except Exception:
            pass
    mime = mimetypes.guess_type(target.name)[0] or ""
    tid = record_transfer("local", "in", "file", target.name, size, mime,
                          digest.hexdigest(), "done", target.name)
    return {"name": target.name, "size": size, "sha256": digest.hexdigest(), "id": tid}


@app.get("/v1/files")
def list_files():
    # M0 recent feed source: name + size + mtime + kind, newest first. No auth yet (LAN only).
    import mimetypes

    items = []
    for p in UPLOAD_ROOT.iterdir():
        if p.name == ".gitkeep" or not p.is_file() or p.suffix == ".part":
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        mime = mimetypes.guess_type(p.name)[0] or ""
        items.append(
            {
                "name": p.name,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "kind": "image" if mime.startswith("image/") else "file",
            }
        )
    items.sort(key=lambda r: r["mtime"], reverse=True)
    return {"files": items}


@app.get("/v1/feed")
def feed(q: str = "", kind: str = "", limit: int = 100):
    # Persistent chronological feed (PRD FR-23): files + snippets, newest first.
    # Search (FR-24): ?q= matches filename or snippet body. ?kind=file|snippet.
    limit = max(1, min(limit, 500))
    like = f"%{q}%" if q else "%"
    items = []
    with db.connect() as conn:
        if kind in ("", "file"):
            for r in conn.execute(
                "SELECT id, peer_id, direction, name, size, mime, sha256, status,"
                " saved_path, created_at FROM transfers"
                " WHERE (? = '%' OR name LIKE ?) ORDER BY created_at DESC LIMIT ?",
                (like, like, limit),
            ):
                d = dict(r)
                d["type"] = "file"
                items.append(d)
        if kind in ("", "snippet"):
            for r in conn.execute(
                "SELECT id, peer_id, direction, kind, body, created_at FROM snippets"
                " WHERE (? = '%' OR body LIKE ?) ORDER BY created_at DESC LIMIT ?",
                (like, like, limit),
            ):
                d = dict(r)
                d["type"] = "snippet"
                items.append(d)
    items.sort(key=lambda r: r["created_at"], reverse=True)
    return {"items": items[:limit]}


@app.delete("/v1/feed/file/{tid}")
def delete_transfer(tid: str, delete_file: bool = False):
    # Delete history row; optionally remove the file from disk too.
    with db.connect() as conn:
        row = conn.execute("SELECT saved_path FROM transfers WHERE id=?", (tid,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute("DELETE FROM transfers WHERE id=?", (tid,))
        conn.commit()
    if delete_file and row["saved_path"]:
        try:
            p = (UPLOAD_ROOT / Path(row["saved_path"]).name).resolve()
            if UPLOAD_ROOT.resolve() in p.parents and p.is_file():
                p.unlink()
        except OSError:
            pass
    return {"ok": True}


@app.get("/v1/files/{name}")
def download_file(name: str):
    # M0 access path: open/download what was shared. Traversal-safe per PRD §10.
    safe = sanitize_filename(name)
    target = (UPLOAD_ROOT / safe).resolve()
    if UPLOAD_ROOT.resolve() not in target.parents and target != UPLOAD_ROOT.resolve():
        raise HTTPException(status_code=404, detail="not found")
    if safe == ".gitkeep" or target.suffix == ".part" or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    from fastapi.responses import FileResponse

    return FileResponse(path=str(target), filename=target.name)
