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


def parse_value(raw: Any) -> tuple[Any, str]:
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
    else:
        value = raw
    text = json.dumps(value, sort_keys=True) if not isinstance(value, str) else value
    return value, text


def http_json(path: str, query: dict[str, Any] | None = None, timeout: float = 3.0) -> Any:
    url = f"{api_url()}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def tool_status(_: dict[str, Any]) -> dict[str, Any]:
    conn = connect_store()
    row = conn.execute("SELECT COUNT(*), MAX(updated_at_ms) FROM memories").fetchone()
    api = {"ok": False, "url": api_url()}
    try:
        api = http_json("/health")
        api["url"] = api_url()
    except Exception as exc:  # local status should not fail the MCP call
        api["error"] = f"{type(exc).__name__}: {exc}"

    sync_bin = os.environ.get(
        "ENE_SESSION_SYNC_BIN",
        str(Path.cwd() / "4-Infrastructure/infra/ene-rds/target/release/ene-sync"),
    )
    return {
        "ok": True,
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "api": api,
        "local_store": {
            "path": str(store_path()),
            "memory_count": row[0],
            "last_updated_ms": row[1],
        },
        "session_sync": {
            "path": sync_bin,
            "exists": Path(sync_bin).exists(),
        },
        "candidate_import_root": str(
            Path(os.environ.get("ENE_CONTEXT_CANDIDATE_ROOT", str(DEFAULT_CANDIDATE_ROOT)))
        ),
    }


def tool_remember(args: dict[str, Any]) -> dict[str, Any]:
    agent = str(args.get("agent") or "codex")
    key = str(args["key"])
    value, value_text = parse_value(args.get("value"))
    tags = args.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    kind = str(args.get("kind") or "note")
    source = str(args.get("source") or "mcp")
    ts = now_ms()

    conn = connect_store()
    prev = conn.execute(
        "SELECT receipt_hash FROM memories WHERE agent = ? ORDER BY updated_at_ms DESC LIMIT 1",
        (agent,),
    ).fetchone()
    prev_hash = prev[0] if prev else None
    payload = json.dumps(
        {
            "agent": agent,
            "key": key,
            "value": value,
            "tags": tags,
            "kind": kind,
            "source": source,
            "prev_hash": prev_hash,
            "updated_at_ms": ts,
        },
        sort_keys=True,
    )
    receipt = sha256_text(payload)
    conn.execute(
        """
        INSERT INTO memories
          (agent, key, value_json, value_text, tags_json, kind, source,
           prev_hash, receipt_hash, created_at_ms, updated_at_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(agent, key) DO UPDATE SET
          value_json = excluded.value_json,
          value_text = excluded.value_text,
          tags_json = excluded.tags_json,
          kind = excluded.kind,
          source = excluded.source,
          prev_hash = excluded.prev_hash,
          receipt_hash = excluded.receipt_hash,
          updated_at_ms = excluded.updated_at_ms
        """,
        (
            agent,
            key,
            json.dumps(value, sort_keys=True),
            value_text,
            json.dumps(tags, sort_keys=True),
            kind,
            source,
            prev_hash,
            receipt,
            ts,
            ts,
        ),
    )
    conn.commit()
    return {
        "ok": True,
        "agent": agent,
        "key": key,
        "kind": kind,
        "tags": tags,
        "receipt_hash": receipt,
        "prev_hash": prev_hash,
        "store": str(store_path()),
    }


def row_to_memory(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "agent": row["agent"],
        "key": row["key"],
        "value": json.loads(row["value_json"]),
        "tags": json.loads(row["tags_json"]),
        "kind": row["kind"],
        "source": row["source"],
        "receipt_hash": row["receipt_hash"],
        "prev_hash": row["prev_hash"],
        "created_at_ms": row["created_at_ms"],
        "updated_at_ms": row["updated_at_ms"],
    }


def tool_recall(args: dict[str, Any]) -> dict[str, Any]:
    agent = str(args.get("agent") or "codex")
    key = args.get("key")
    query = str(args.get("query") or "")
    limit = int(args.get("limit") or 10)
    conn = connect_store()

    if key is not None:
        row = conn.execute(
            "SELECT * FROM memories WHERE agent = ? AND key = ?",
            (agent, str(key)),
        ).fetchone()
        return {"ok": True, "found": row is not None, "memory": row_to_memory(row) if row else None}

    needle = f"%{query}%"
    rows = conn.execute(
        """
        SELECT * FROM memories
        WHERE agent = ? AND (? = '' OR key LIKE ? OR value_text LIKE ? OR tags_json LIKE ?)
        ORDER BY updated_at_ms DESC
        LIMIT ?
        """,
        (agent, query, needle, needle, needle, limit),
    ).fetchall()
    return {"ok": True, "count": len(rows), "memories": [row_to_memory(r) for r in rows]}


def tool_search(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args["query"])
    limit = int(args.get("limit") or 10)
    semantic = bool(args.get("semantic") or False)
    sources = args.get("sources") or ["ene_api", "local_memory"]
    out: dict[str, Any] = {"ok": True, "query": query, "results": {}}

    if "ene_api" in sources:
        try:
            out["results"]["ene_api"] = http_json(
                "/search",
                {"q": query, "limit": limit, "semantic": str(semantic).lower()},
            )
        except Exception as exc:
            out["results"]["ene_api"] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "url": api_url(),
            }

    if "local_memory" in sources:
        out["results"]["local_memory"] = tool_recall(
            {"agent": args.get("agent", "codex"), "query": query, "limit": limit}
        )
    return out


def tool_context(args: dict[str, Any]) -> dict[str, Any]:
    """One-call session-start context packet for agents.

    This mirrors ContextStream's common startup habit while staying ENE-first:
    status + search + optional recall + optional transcript save.
    """
    user_message = str(args.get("user_message") or args.get("query") or "")
    agent = str(args.get("agent") or "codex")
    save_exchange = bool(args.get("save_exchange") or False)
    session_id = args.get("session_id")
    result: dict[str, Any] = {
        "ok": True,
        "policy": "ENE first. ContextStream is fallback only.",
        "status": tool_status({}),
        "search": None,
        "recall": None,
        "saved": None,
    }
    if user_message:
        result["search"] = tool_search({"query": user_message, "agent": agent, "limit": args.get("limit", 10)})
        result["recall"] = tool_recall({"agent": agent, "query": user_message, "limit": args.get("limit", 10)})
    if save_exchange and user_message:
        key = f"session:{session_id or now_ms()}:user:{now_ms()}"
        result["saved"] = tool_remember(
            {
                "agent": agent,
                "key": key,
                "value": {"user_message": user_message, "session_id": session_id},
                "tags": ["transcript", "user-message"],
                "kind": "conversation",
                "source": "ene_context",
            }
        )
    return result


def tool_sessions(args: dict[str, Any]) -> dict[str, Any]:
    action = str(args.get("action") or "list")
    limit = int(args.get("limit") or 10)
    try:
        if action == "list":
            return http_json("/sessions", {"limit": limit})
        if action == "get":
            return http_json(f"/sessions/{urllib.parse.quote(str(args['session_id']))}")
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "url": api_url()}
    return {"ok": False, "error": f"unknown sessions action: {action}"}


def tool_sync(args: dict[str, Any]) -> dict[str, Any]:
    dry_run = bool(args.get("dry_run", True))
    command = str(args.get("command") or "list")
    sync_bin = os.environ.get(
        "ENE_SESSION_SYNC_BIN",
        str(Path.cwd() / "4-Infrastructure/infra/ene-rds/target/release/ene-sync"),
    )
    cmd = [sync_bin]
    if command == "sync":
        cmd.append("sync")
        if args.get("embed"):
            cmd.insert(1, "--embed")
    elif command == "list":
        cmd.extend(["list", "--limit", str(int(args.get("limit") or 20))])
    elif command == "init-schema":
        cmd.append("init-schema")
    else:
        return {"ok": False, "error": f"unsupported sync command: {command}"}

    if dry_run:
        return {"ok": True, "dry_run": True, "command": cmd, "exists": Path(sync_bin).exists()}
    if not Path(sync_bin).exists():
        return {"ok": False, "error": "ene-session-sync binary not found", "command": cmd}
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
        "command": cmd,
    }


def candidate_summary(path: Path) -> dict[str, Any]:
    readme = next(path.glob("README*"), None)
    cargo = path / "Cargo.toml"
    package = path / "package.json"
    pyproject = path / "pyproject.toml"
    return {
        "repo": path.name,
        "path": str(path),
        "readme": str(readme) if readme else None,
        "manifests": [str(p) for p in [cargo, package, pyproject] if p.exists()],
    }


def tool_import_candidates(args: dict[str, Any]) -> dict[str, Any]:
    root = Path(args.get("root") or os.environ.get("ENE_CONTEXT_CANDIDATE_ROOT", str(DEFAULT_CANDIDATE_ROOT)))
    repos = [p for p in sorted(root.iterdir()) if p.is_dir() and (p / ".git").exists()] if root.exists() else []
    map_notes = {
        "Octopoda-OS": "Agent memory API, remember/recall/search/snapshot/audit vocabulary.",
        "llm_wiki": "Source -> wiki -> graph ingest pattern and local API shape.",
        "SurfSense": "Browser/Obsidian/document connectors and team RAG workflows.",
        "forge": "Local tool-calling guardrails and proxy agent loop patterns.",
        "kanbots": "MCP over local HTTP bridge and agent task board semantics.",
        "namidb": "Graph database on object storage; useful for ENE graph persistence.",
        "Vane": "Local answering engine with SearXNG/search history/citation UX.",
    }
    return {
        "ok": True,
        "root": str(root),
        "count": len(repos),
        "candidates": [
            {**candidate_summary(p), "ene_use": map_notes.get(p.name, "Review manually")}
            for p in repos
        ],
    }


TOOLS: dict[str, dict[str, Any]] = {
    "ene_status": {
        "description": "ENE context health: local memory ledger, ENE API, session-sync binary.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_status,
    },
    "ene_remember": {
        "description": "Store a durable ENE memory packet with a hash-chain receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "default": "codex"},
                "key": {"type": "string"},
                "value": {},
                "tags": {"type": "array", "items": {"type": "string"}},
                "kind": {"type": "string", "default": "note"},
                "source": {"type": "string", "default": "mcp"},
            },
            "required": ["key", "value"],
        },
        "handler": tool_remember,
    },
    "ene_context": {
        "description": "ENE-first startup/context packet: status, search, recall, optional transcript save.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_message": {"type": "string"},
                "query": {"type": "string"},
                "agent": {"type": "string", "default": "codex"},
                "session_id": {"type": "string"},
                "save_exchange": {"type": "boolean", "default": False},
                "limit": {"type": "integer", "default": 10},
            },
        },
        "handler": tool_context,
    },
    "ene_recall": {
        "description": "Recall ENE memory by exact key or query over local memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "default": "codex"},
                "key": {"type": "string"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        },
        "handler": tool_recall,
    },
    "ene_search": {
        "description": "Search ENE API chat/session memory plus local ENE memory ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
                "semantic": {"type": "boolean", "default": False},
                "agent": {"type": "string", "default": "codex"},
                "sources": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query"],
        },
        "handler": tool_search,
    },
    "ene_sessions": {
        "description": "List or fetch ENE chat sessions through ene-api.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get"], "default": "list"},
                "session_id": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        },
        "handler": tool_sessions,
    },
    "ene_sync": {
        "description": "Run or dry-run ene-session-sync commands.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "enum": ["list", "sync", "init-schema"], "default": "list"},
                "dry_run": {"type": "boolean", "default": True},
                "limit": {"type": "integer", "default": 20},
                "embed": {"type": "boolean", "default": False},
            },
        },
        "handler": tool_sync,
    },
    "ene_import_candidates": {
        "description": "List GitHub repos pulled as ENE ContextStream-equivalent candidates.",
        "inputSchema": {
            "type": "object",
            "properties": {"root": {"type": "string"}},
        },
        "handler": tool_import_candidates,
    },
}


def mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    req_id = req.get("id")
    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": req.get("params", {}).get("protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": mcp_tools()}}
        if method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            if name not in TOOLS:
                raise ValueError(f"unknown tool: {name}")
            args = params.get("arguments") or {}
            result = TOOLS[name]["handler"](args)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": json_text(result)}}
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": f"{type(exc).__name__}: {exc}"},
        }


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = handle(json.loads(line))
        except json.JSONDecodeError as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(exc)},
            }
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
