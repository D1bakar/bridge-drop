"""Bridge M0 backend skeleton — PRD §9 contract starts here.

Run: uvicorn app:app --reload --port 8000  (from backend/)
Contract (frontend untouched, still on mock.js):
  GET /v1/info — device info + capabilities
"""

from pathlib import Path
import socket

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bridge M0")

# M0 LAN-only: allow Live Server + phone browsers. TODO(prd §10): pin origins + TLS + auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

UPLOAD_ROOT = Path(__file__).parent / "uploads"
UPLOAD_ROOT.mkdir(exist_ok=True)


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


_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


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
    try:
        with part.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
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
    return {"name": target.name, "size": size}


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
