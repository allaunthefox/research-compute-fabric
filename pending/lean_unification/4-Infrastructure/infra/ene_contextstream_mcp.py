#!/usr/bin/env python3
"""ENE Context MCP surface.

Local-first MCP shim that gives ENE a ContextStream-like interface without
depending on ContextStream. It fronts the existing ENE API/session-sync surfaces
when they are running and keeps a small local SQLite memory ledger so writes are
available immediately.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SERVER_NAME = "ene-contextstream"
SERVER_VERSION = "0.1.0"
DEFAULT_API_URL = "http://127.0.0.1:3000"
DEFAULT_STORE = Path.home() / ".local/share/ene/contextstream.sqlite"
DEFAULT_CANDIDATE_ROOT = (
    Path.cwd() / "shared-data/data/germane/research/github-ene-contextstream"
)


def now_ms() -> int:
    return int(time.time() * 1000)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_text(data: Any) -> list[dict[str, str]]:
    return [{"type": "text", "text": json.dumps(data, indent=2, sort_keys=True)}]


def store_path() -> Path:
    return Path(os.environ.get("ENE_CONTEXT_STORE", str(DEFAULT_STORE))).expanduser()


def api_url() -> str:
    return os.environ.get("ENE_API_URL", DEFAULT_API_URL).rstrip("/")


def connect_store() -> sqlite3.Connection:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            key TEXT NOT NULL,
            value_json TEXT NOT NULL,
            value_text TEXT NOT NULL,
            tags_json TEXT NOT NULL DEFAULT '[]',
            kind TEXT NOT NULL DEFAULT 'note',
            source TEXT NOT NULL DEFAULT 'mcp',
            prev_hash TEXT,
            receipt_hash TEXT NOT NULL,
            created_at_ms INTEGER NOT NULL,
            updated_at_ms INTEGER NOT NULL,
            UNIQUE(agent, key)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at_ms DESC)")
    conn.commit()
    return conn

# (full file preserved in pending quarantine)

if __name__ == "__main__":
    raise SystemExit(0)
