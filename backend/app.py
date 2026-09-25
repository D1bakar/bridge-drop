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

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import db

db.init_db()  # idempotent; keeps tests + first boot on the same schema


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


def get_rules() -> list:
    # Save rules (PRD FR-16): [{ext: ".mp4", dir: "Videos"}]. Stored as JSON.
    import json

    try:
        rules = json.loads(db.get_setting("rules", "[]") or "[]")
        return [r for r in rules if isinstance(r, dict) and r.get("ext") and r.get("dir")]
    except Exception:
        return []


def rule_dir_for(filename: str) -> str:
    # First matching rule wins; dir sanitized to a single safe segment.
    ext = "." + filename.rpartition(".")[2].lower() if "." in filename else ""
    for r in get_rules():
        if str(r.get("ext", "")).lower() == ext:
            seg = sanitize_filename(str(r.get("dir", ""))) or "Files"
            return seg[:60]
    return ""


def sanitize_relpath(rel: str) -> str:
    # Folder sends (PRD FR-9): keep structure, resolve ".." inward, never escape.
    # "a/b/../../c" -> "c". Segments sanitized after traversal is resolved.
    parts: list[str] = []
    for raw in (rel or "").replace("\\", "/").split("/"):
        seg = raw.strip()
        if not seg or seg == ".":
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        clean = sanitize_filename(seg)
        if not clean or clean == "file" and seg not in ("file", "File"):
            # sanitize_filename falls back to "file" for dot-only names — drop those
            if seg.strip(". ") == "":
                continue
        parts.append(clean[:80])
    if len(parts) > 20:  # absurd depth guard
        parts = parts[-20:]
    return "/".join(parts)


def _strip_trailing_filename(rel: str, filename: str) -> str:
    # Clients send webkitRelativePath ("trip/img.jpg") as relPath; the name
    # travels separately, so drop a trailing segment that IS the filename.
    if rel and "/" in rel and rel.rpartition("/")[2] == filename:
        return rel.rpartition("/")[0]
    if rel == filename:
        return ""
    return rel


def save_root_for(filename: str, rel_path: str) -> Path:
    root = UPLOAD_ROOT
    sub = rule_dir_for(filename)
    if sub:
        root = root / sub
    rel = _strip_trailing_filename(sanitize_relpath(rel_path), filename)
    if rel:
        root = root / Path(*rel.split("/"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _chunk_tmp(upload_id: str) -> Path:
    return UPLOAD_ROOT / f".up-{upload_id}.part"


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


def unique_path(name: str, root: Path | None = None) -> Path:
    base = root or UPLOAD_ROOT
    safe = sanitize_filename(name)
    target = base / safe
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


_PAGES = {"send.html", "history.html", "pair.html", "settings.html"}


@app.get("/{page}")
def page(page: str):
    # App screens as separate pages (no SPA router — works in any phone browser).
    from fastapi.responses import FileResponse

    name = page.strip().replace("\\", "/").split("/")[-1]
    if name not in _PAGES:
        raise HTTPException(status_code=404, detail="not found")
    target = (WEB_ROOT / name).resolve()
    if WEB_ROOT.resolve() not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path=str(target), media_type="text/html")


@app.get("/v1/info")
def info():
    # Mirrors js/mock.js MOCK_DEVICES[0] shape (PRD §9 Device). No auth yet (M0 LAN only).
    return {
        "id": "pc-1",
        "name": db.get_setting("device_name", "My PC") or "My PC",
        "platform": "Windows",
        "version": "0.1.0",
        "capabilities": ["info", "files", "snippets", "chunked", "pair"],
        "trusted": True,
    }


@app.post("/v1/files", status_code=201)
async def upload_file(request: Request, file: UploadFile = File(...), relPath: str = ""):
    # PRD §7 reliability: stream to .part, rename on success — no partials in destination.
    # Save rules (FR-16) + folder structure (FR-9) apply here too.
    peer_id, _known = resolve_peer(request)
    raw_name = file.filename or "file"
    safe_name = sanitize_filename(raw_name.rpartition("/")[2].rpartition("\\")[2])
    root = save_root_for(safe_name, relPath or "")
    target = unique_path(safe_name, root)
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
    try:
        saved_rel = target.relative_to(UPLOAD_ROOT).as_posix()
    except ValueError:
        saved_rel = target.name
    tid = record_transfer(peer_id, "in", "file", target.name, size, mime,
                          digest.hexdigest(), "done", saved_rel)
    return {"name": target.name, "size": size, "sha256": digest.hexdigest(),
            "id": tid, "path": saved_rel}


@app.get("/v1/files")
def list_files():
    # Recent feed source: name + size + mtime + kind, newest first (recursive:
    # rule folders + preserved structure show up too). No auth yet (LAN only).
    items = []
    for p in UPLOAD_ROOT.rglob("*"):
        if not p.is_file() or p.suffix == ".part":
            continue
        if p.name == ".gitkeep" or p.name.startswith(".up-"):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        try:
            rel = p.relative_to(UPLOAD_ROOT).as_posix()
        except ValueError:
            continue
        mime = mimetypes.guess_type(p.name)[0] or ""
        items.append(
            {
                "name": p.name,
                "path": rel,
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


def _resolve_upload_path(fpath: str) -> Path | None:
    # Shared guard for file access by path: traversal-safe, inside save root,
    # never .part staging files, never the .gitkeep marker.
    if not fpath or fpath.strip() in (".", "/"):
        return None
    segs = [sanitize_filename(s) for s in fpath.replace("\\", "/").split("/")]
    segs = [s for s in segs if s and s not in (".", "..")]
    if not segs or ".gitkeep" in segs or any(s.startswith(".up-") for s in segs):
        return None
    try:
        target = (UPLOAD_ROOT.joinpath(*segs)).resolve()
    except (OSError, ValueError):
        return None
    if UPLOAD_ROOT.resolve() not in target.parents:
        return None
    if target.suffix == ".part" or not target.is_file():
        return None
    return target


@app.delete("/v1/files/{fpath:path}")
def delete_file(fpath: str):
    # Delete anything you shared or received: removes the file from disk AND
    # every history row pointing at it, so it never haunts the feed.
    target = _resolve_upload_path(fpath)
    if target is None:
        raise HTTPException(status_code=404, detail="not found")
    try:
        rel = target.relative_to(UPLOAD_ROOT).as_posix()
    except ValueError:
        raise HTTPException(status_code=404, detail="not found")
    try:
        target.unlink()
    except OSError as exc:
        raise HTTPException(status_code=500, detail="delete failed") from exc
    with db.connect() as conn:
        conn.execute("DELETE FROM transfers WHERE saved_path=?", (rel,))
        conn.execute("DELETE FROM transfers WHERE saved_path=?", (target.name,))
        conn.commit()
    return {"ok": True}


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
            segs = [s for s in Path(row["saved_path"]).parts if s not in (".", "..", "/")]
            p = (UPLOAD_ROOT.joinpath(*segs)).resolve() if segs else None
            if p and UPLOAD_ROOT.resolve() in p.parents and p.is_file():
                p.unlink()
        except (OSError, ValueError):
            pass
    return {"ok": True}


@app.get("/v1/files/{fpath:path}")
def download_file(fpath: str):
    # Access path: open/download what was shared. Traversal-safe per PRD §10.
    # Accepts plain names ("a.jpg") and relative paths ("Videos/a.mp4").
    target = _resolve_upload_path(fpath)
    if target is None:
        raise HTTPException(status_code=404, detail="not found")
    from fastapi.responses import FileResponse

    return FileResponse(path=str(target), filename=target.name)


def _snippet_kind(body: str, hint: str) -> str:
    hint = (hint or "").lower()
    if hint in ("text", "link", "clipboard"):
        return hint
    s = body.strip().lower()
    if s.startswith(("http://", "https://")) and " " not in s and len(s) < 4096:
        return "link"
    return "text"


@app.post("/v1/snippets", status_code=201)
def post_snippet(payload: dict, request: Request):
    # Text / links / clipboard pushes (PRD FR-10, FR-26). Stored, feed-listed.
    body = str(payload.get("body", "") or "")
    if not body.strip():
        raise HTTPException(status_code=422, detail="empty snippet")
    if len(body) > 100_000:
        raise HTTPException(status_code=413, detail="snippet too large")
    kind = _snippet_kind(body, str(payload.get("kind", "") or ""))
    peer_id, _known = resolve_peer(request)
    sid = uuid.uuid4().hex[:12]
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO snippets(id, peer_id, direction, kind, body, created_at)"
            " VALUES(?,?,?,?,?,?)",
            (sid, peer_id, "in", kind, body, db.now()),
        )
        conn.commit()
    return {"id": sid, "kind": kind}


@app.get("/v1/snippets")
def list_snippets(limit: int = 100):
    limit = max(1, min(limit, 500))
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, peer_id, direction, kind, body, created_at FROM snippets"
            " ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"snippets": db.dicts(rows)}


@app.delete("/v1/feed/snippet/{sid}")
def delete_snippet(sid: str):
    with db.connect() as conn:
        row = conn.execute("SELECT id FROM snippets WHERE id=?", (sid,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute("DELETE FROM snippets WHERE id=?", (sid,))
        conn.commit()
    return {"ok": True}


# --- Chunked resumable uploads (PRD FR-18/20/21) ---------------------------
# init → PUT chunks with ?offset=N → complete (hash-verified, .part → final).
# Survives drops: status reports confirmed bytes, client resumes from there.

_CHUNK_MAX = 8 * 1024 * 1024


def _get_upload(uid: str) -> dict:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM chunked WHERE id=?", (uid,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="unknown upload")
        return dict(row)


@app.post("/v1/uploads/init", status_code=201)
def uploads_init(payload: dict, request: Request):
    peer_id, _known = resolve_peer(request)
    name = sanitize_filename(str(payload.get("name", "") or ""))
    if not name or name == "file" and not payload.get("name"):
        raise HTTPException(status_code=422, detail="name required")
    try:
        size = int(payload.get("size", -1))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="size required")
    if size < 0 or size > 100 * 1024**3:
        raise HTTPException(status_code=422, detail="bad size")
    rel = _strip_trailing_filename(
        sanitize_relpath(str(payload.get("relPath", "") or "")), name)
    mime = str(payload.get("mime", "") or mimetypes.guess_type(name)[0] or "")
    sha_exp = str(payload.get("sha256", "") or "")
    if sha_exp and (len(sha_exp) != 64 or any(c not in "0123456789abcdefABCDEF" for c in sha_exp)):
        raise HTTPException(status_code=422, detail="bad sha256")
    uid = uuid.uuid4().hex[:12]
    save_dir = ""
    sub = rule_dir_for(name)
    if sub:
        save_dir = sub
    if rel:
        save_dir = f"{save_dir}/{rel}" if save_dir else rel
    tmp = _chunk_tmp(uid)
    try:
        tmp.touch(exist_ok=False)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="cannot stage upload") from exc
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO chunked(id, peer_id, name, rel_path, save_dir, size, mime,"
            " sha256_expected, bytes_done, tmp_name, final_name, status, created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, peer_id, name, rel, save_dir, size, mime, sha_exp.lower(),
             0, tmp.name, "", "uploading", db.now()),
        )
        conn.commit()
    return {"uploadId": uid, "offset": 0, "size": size}


@app.get("/v1/uploads/{uid}/status")
def upload_status(uid: str):
    u = _get_upload(uid)
    return {"uploadId": uid, "offset": u["bytes_done"], "size": u["size"],
            "status": u["status"]}


@app.put("/v1/uploads/{uid}/chunk")
async def upload_chunk(uid: str, request: Request, offset: int = 0):
    u = _get_upload(uid)
    if u["status"] != "uploading":
        raise HTTPException(status_code=409, detail=f"upload {u['status']}")
    if offset != u["bytes_done"]:
        raise HTTPException(status_code=409, detail="offset mismatch")
    # Raw bytes body; bounded per request so RAM never holds the whole file.
    body = await request.body()
    if len(body) > _CHUNK_MAX:
        raise HTTPException(status_code=413, detail="chunk too large")
    if not body:
        return {"offset": u["bytes_done"]}
    if u["bytes_done"] + len(body) > u["size"]:
        raise HTTPException(status_code=422, detail="exceeds declared size")
    tmp = UPLOAD_ROOT / u["tmp_name"]
    try:
        with tmp.open("ab") as out:
            out.write(body)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="write failed") from exc
    new_off = u["bytes_done"] + len(body)
    with db.connect() as conn:
        conn.execute("UPDATE chunked SET bytes_done=? WHERE id=?", (new_off, uid))
        conn.commit()
    return {"offset": new_off}


@app.post("/v1/uploads/{uid}/complete")
def upload_complete(uid: str, payload: dict | None = None):
    return _finalize_upload(uid, payload, force=False)


def _finalize_upload(uid: str, payload: dict | None, force: bool):
    u = _get_upload(uid)
    if u["status"] != "uploading":
        raise HTTPException(status_code=409, detail=f"upload {u['status']}")
    if u["bytes_done"] != u["size"]:
        raise HTTPException(status_code=409, detail="incomplete")
    tmp = UPLOAD_ROOT / u["tmp_name"]
    digest = hashlib.sha256()
    try:
        with tmp.open("rb") as f:
            while True:
                b = f.read(1024 * 1024)
                if not b:
                    break
                digest.update(b)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="read failed") from exc
    want = (u["sha256_expected"] or "").lower()
    if payload and payload.get("sha256"):
        want = str(payload["sha256"]).lower()
    got = digest.hexdigest()
    if want and want != got:
        raise HTTPException(status_code=422, detail="hash mismatch — re-send the file")
    if u["peer_id"].startswith("guest:") and not _auto_accept() and not force:
        # FR-13: unknown sender waits for an explicit Accept in the UI.
        tid = record_transfer(u["peer_id"], "in", "file", u["name"], u["size"],
                              u["mime"], got, "pending", "")
        with db.connect() as conn:
            conn.execute("UPDATE chunked SET status='pending', transfer_id=? WHERE id=?",
                         (tid, uid))
            conn.commit()
        return {"pending": True, "id": tid, "name": u["name"], "size": u["size"]}
    root = UPLOAD_ROOT
    if u["save_dir"]:
        root = root / Path(*u["save_dir"].split("/"))
        root.mkdir(parents=True, exist_ok=True)
    target = unique_path(u["name"], root)
    try:
        tmp.replace(target)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="finalize failed") from exc
    try:
        saved_rel = target.relative_to(UPLOAD_ROOT).as_posix()
    except ValueError:
        saved_rel = target.name
    tid = record_transfer(u["peer_id"], "in", "file", target.name, u["size"],
                          u["mime"] or mimetypes.guess_type(target.name)[0] or "",
                          got, "done", saved_rel)
    with db.connect() as conn:
        conn.execute("UPDATE chunked SET status='done', final_name=? WHERE id=?",
                     (target.name, uid))
        conn.commit()
    return {"id": tid, "name": target.name, "path": saved_rel, "size": u["size"],
            "sha256": got}


@app.delete("/v1/uploads/{uid}")
def upload_cancel(uid: str):
    u = _get_upload(uid)
    tmp = UPLOAD_ROOT / u["tmp_name"]
    try:
        if tmp.exists():
            tmp.unlink()
    except OSError:
        pass
    with db.connect() as conn:
        conn.execute("UPDATE chunked SET status='cancelled' WHERE id=?", (uid,))
        conn.commit()
    return {"ok": True}


# --- Pairing: one-time codes + QR + trusted devices (PRD FR-2/FR-3/FR-13) ---
# PC shows QR → phone scans → opens URL with ?code= → claims → trusted device.
# Codes expire in 5 min, single use. Unknown senders without a live code get
# nothing; with auto-accept OFF, guest uploads wait in "pending" for Accept.

_PAIR_TTL = 300.0


def _new_code() -> str:
    import secrets

    return f"{secrets.randbelow(900000) + 100000}"


@app.post("/v1/pair/code", status_code=201)
def pair_new_code():
    import time

    code = _new_code()
    token = uuid.uuid4().hex
    with db.connect() as conn:
        # one live code at a time keeps the UX unambiguous
        conn.execute("DELETE FROM pair_codes")
        conn.execute(
            "INSERT INTO pair_codes(code, token, expires_at, used) VALUES(?,?,?,0)",
            (code, token, time.time() + _PAIR_TTL),
        )
        conn.commit()
    url = f"http://{get_lan_ip()}:8000/?code={code}"
    return {"code": code, "expires_in": int(_PAIR_TTL), "url": url}


@app.get("/v1/pair/qr")
def pair_qr(code: str = ""):
    # Design §6: Warm Obsidian modules on Bone White, quiet zone ≥ 4, square.
    import io
    import time

    import qrcode

    with db.connect() as conn:
        row = conn.execute(
            "SELECT code, expires_at, used FROM pair_codes ORDER BY expires_at DESC LIMIT 1"
        ).fetchone()
    live = None
    if code:
        with db.connect() as conn:
            r = conn.execute("SELECT code, expires_at, used FROM pair_codes WHERE code=?",
                             (code,)).fetchone()
            if r and not r["used"] and r["expires_at"] > time.time():
                live = r["code"]
    elif row and not row["used"] and row["expires_at"] > time.time():
        live = row["code"]
    if not live:
        raise HTTPException(status_code=404, detail="no live pair code")
    url = f"http://{get_lan_ip()}:8000/?code={live}"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#262523", back_color="#ececec")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    from fastapi.responses import Response

    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/v1/pair/claim", status_code=201)
def pair_claim(payload: dict, request: Request):
    import time

    ip = _client_ip(request)
    if _fail_count(ip) >= _FAIL_MAX:
        raise HTTPException(status_code=429, detail="too many attempts — wait a while")
    code = str(payload.get("code", "") or "").strip()
    name = str(payload.get("name", "") or "Guest phone")[:60] or "Guest phone"
    platform = str(payload.get("platform", "") or "Browser")[:30] or "Browser"
    with db.connect() as conn:
        row = conn.execute("SELECT code, token, expires_at, used FROM pair_codes WHERE code=?",
                           (code,)).fetchone()
        if not row or row["used"] or row["expires_at"] <= time.time():
            _note_fail(ip)
            raise HTTPException(status_code=403, detail="bad or expired code")
        did = uuid.uuid4().hex[:12]
        fingerprint = uuid.uuid4().hex[:8]  # short code shown on both ends (FR-2)
        conn.execute(
            "INSERT INTO devices(id, name, platform, fingerprint, trusted, token,"
            " created_at, last_seen, last_address) VALUES(?,?,?,?,?,?,?,?,?)",
            (did, name, platform, fingerprint, 1, row["token"], db.now(), db.now(), ip),
        )
        conn.execute("UPDATE pair_codes SET used=1 WHERE code=?", (code,))
        conn.commit()
    return {"deviceId": did, "deviceToken": row["token"], "fingerprint": fingerprint}


@app.get("/v1/devices")
def list_devices():
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, name, platform, fingerprint, trusted, created_at, last_seen"
            " FROM devices ORDER BY created_at").fetchall()
    return {"devices": db.dicts(rows)}


@app.patch("/v1/devices/{did}")
def rename_device(did: str, payload: dict):
    name = str(payload.get("name", "") or "").strip()[:60]
    if not name:
        raise HTTPException(status_code=422, detail="name required")
    with db.connect() as conn:
        row = conn.execute("SELECT id FROM devices WHERE id=?", (did,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute("UPDATE devices SET name=? WHERE id=?", (name, did))
        conn.commit()
    return {"ok": True, "name": name}


@app.delete("/v1/devices/{did}")
def revoke_device(did: str):
    # Revoke: token dies with the row; that phone must re-pair (PRD §10).
    with db.connect() as conn:
        row = conn.execute("SELECT id FROM devices WHERE id=?", (did,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        conn.execute("DELETE FROM devices WHERE id=?", (did,))
        conn.commit()
    return {"ok": True}


@app.post("/v1/uploads/{uid}/accept")
def upload_accept(uid: str):
    # FR-13: unknown-sender uploads wait here when auto-accept is OFF.
    u = _get_upload(uid)
    if u["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"upload {u['status']}")
    with db.connect() as conn:
        conn.execute("UPDATE chunked SET status='uploading' WHERE id=?", (uid,))
        conn.commit()
    # Reuse the finalize path (hash check + rename + history).
    return _finalize_upload(uid, None, force=True)


@app.post("/v1/uploads/{uid}/decline")
def upload_decline(uid: str):
    u = _get_upload(uid)
    if u["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"upload {u['status']}")
    upload_cancel(uid)
    return {"ok": True, "declined": True}


def _upload_for_transfer(tid: str) -> dict:
    with db.connect() as conn:
        t = conn.execute("SELECT * FROM transfers WHERE id=?", (tid,)).fetchone()
        if not t or t["status"] != "pending" or t["kind"] != "file":
            raise HTTPException(status_code=404, detail="no pending transfer")
        u = conn.execute("SELECT * FROM chunked WHERE transfer_id=?", (tid,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="no staged upload")
        return dict(u)


@app.post("/v1/feed/accept/{tid}")
def feed_accept(tid: str):
    u = _upload_for_transfer(tid)
    with db.connect() as conn:
        conn.execute("UPDATE chunked SET status='uploading' WHERE id=?", (u["id"],))
        conn.commit()
    out = _finalize_upload(u["id"], None, force=True)
    with db.connect() as conn:
        conn.execute("DELETE FROM transfers WHERE id=?", (tid,))
        conn.commit()
    return out


@app.post("/v1/feed/decline/{tid}")
def feed_decline(tid: str):
    u = _upload_for_transfer(tid)
    tmp = UPLOAD_ROOT / u["tmp_name"]
    try:
        if tmp.exists():
            tmp.unlink()
    except OSError:
        pass
    with db.connect() as conn:
        conn.execute("UPDATE chunked SET status='cancelled' WHERE id=?", (u["id"],))
        conn.execute("UPDATE transfers SET status='cancelled' WHERE id=?", (tid,))
        conn.commit()
    return {"ok": True, "declined": True}


# --- Settings + save rules (PRD FR-30, FR-16) --------------------------------

@app.get("/v1/settings")
def get_settings():
    return {
        "device_name": db.get_setting("device_name", "My PC") or "My PC",
        "auto_accept": db.get_setting("auto_accept", "1") == "1",
        "visibility": db.get_setting("visibility", "visible"),
        "save_root": str(UPLOAD_ROOT),
    }


@app.patch("/v1/settings")
def patch_settings(payload: dict):
    out = {}
    if "device_name" in payload:
        name = str(payload["device_name"] or "").strip()[:60]
        if not name:
            raise HTTPException(status_code=422, detail="device name required")
        db.set_setting("device_name", name)
        out["device_name"] = name
    if "auto_accept" in payload:
        val = "1" if payload["auto_accept"] else "0"
        db.set_setting("auto_accept", val)
        out["auto_accept"] = val == "1"
    if "visibility" in payload:
        vis = str(payload["visibility"] or "")
        if vis not in ("visible", "hidden"):
            raise HTTPException(status_code=422, detail="visibility must be visible|hidden")
        db.set_setting("visibility", vis)
        out["visibility"] = vis
    return out


@app.get("/v1/rules")
def list_rules():
    return {"rules": get_rules()}


@app.post("/v1/rules", status_code=201)
def add_rule(payload: dict):
    import json

    ext = str(payload.get("ext", "") or "").strip().lower()
    dest = sanitize_filename(str(payload.get("dir", "") or "").strip())[:60]
    if not ext.startswith(".") or len(ext) < 2 or len(ext) > 12:
        raise HTTPException(status_code=422, detail="ext like .mp4 required")
    if not dest:
        raise HTTPException(status_code=422, detail="dir required")
    rules = [r for r in get_rules() if r.get("ext") != ext]
    rules.append({"ext": ext, "dir": dest})
    db.set_setting("rules", json.dumps(rules))
    return {"ok": True, "rules": rules}


@app.delete("/v1/rules")
def delete_rule(ext: str):
    import json

    ext = ext.strip().lower()
    rules = [r for r in get_rules() if r.get("ext") != ext]
    db.set_setting("rules", json.dumps(rules))
    return {"ok": True, "rules": rules}
