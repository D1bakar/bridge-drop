"""Bridge persistent storage — PRD §9 data model (SQLite, local only, no telemetry).

Tables: devices, transfers (file history), snippets, pair_codes, settings.
DB lives at backend/bridge.db (gitignored). Tests wipe rows they create.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(os.environ.get("BRIDGE_DB", str(Path(__file__).parent / "bridge.db")))

_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Guest',
    platform TEXT NOT NULL DEFAULT 'Browser',
    fingerprint TEXT NOT NULL DEFAULT '',
    trusted INTEGER NOT NULL DEFAULT 1,
    token TEXT UNIQUE,
    created_at REAL NOT NULL,
    last_seen REAL NOT NULL,
    last_address TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS transfers (
    id TEXT PRIMARY KEY,
    peer_id TEXT NOT NULL DEFAULT 'local',
    direction TEXT NOT NULL DEFAULT 'in',
    kind TEXT NOT NULL DEFAULT 'file',
    name TEXT NOT NULL,
    size INTEGER NOT NULL DEFAULT 0,
    mime TEXT NOT NULL DEFAULT '',
    sha256 TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'done',
    saved_path TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS snippets (
    id TEXT PRIMARY KEY,
    peer_id TEXT NOT NULL DEFAULT 'local',
    direction TEXT NOT NULL DEFAULT 'in',
    kind TEXT NOT NULL DEFAULT 'text',
    body TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS pair_codes (
    code TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    expires_at REAL NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


def now() -> float:
    return time.time()


def dicts(rows):
    return [dict(r) for r in rows]


def get_setting(key: str, default: str = "") -> str:
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()
