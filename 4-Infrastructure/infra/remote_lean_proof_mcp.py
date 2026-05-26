#!/usr/bin/env python3
"""MCP client shim for the Netcup Lean proof server."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SERVER_NAME = "remote-lean-proof"
SERVER_VERSION = "0.1.0"
DEFAULT_URL = "http://54.236.176.28:8787"
DEFAULT_TOKEN_FILE = Path.home() / ".config/ene/language-proof-server.token"


def json_text(data: Any) -> list[dict[str, str]]:
    return [{"type": "text", "text": json.dumps(data, indent=2, sort_keys=True)}]


def token() -> str:
    direct = os.environ.get("PROOF_SERVER_TOKEN")
    if direct:
        return direct.strip()
    path = Path(os.environ.get("PROOF_SERVER_TOKEN_FILE", str(DEFAULT_TOKEN_FILE))).expanduser()
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        return ""


def base_url() -> str:
    return os.environ.get("PROOF_SERVER_URL", DEFAULT_URL).rstrip("/")


def request_json(path: str, payload: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": f"{SERVER_NAME}/{SERVER_VERSION}"}
    body = None
    method = "GET"
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
        auth = token()
        if auth:
            headers["Authorization"] = f"Bearer {auth}"
    req = urllib.request.Request(f"{base_url()}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"error": text}
        data["http_status"] = exc.code
        data["ok"] = False
        return data
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def tool_status(_: dict[str, Any]) -> dict[str, Any]:
    health = request_json("/health", timeout=10)
    return {
        "ok": bool(health.get("ok")),
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "proof_server_url": base_url(),
        "token_configured": bool(token()),
        "health": health,
    }


def tool_check(args: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": args.get("name") or "agent_check",
        "code": args.get("code") or "",
        "timeout_s": args.get("timeout_s", 120),
        "agent": args.get("agent") or "hermes",
    }
    return request_json("/lean/check", payload, timeout=int(payload["timeout_s"]) + 15)


def tool_build(args: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "target": args.get("target") or "",
        "timeout_s": args.get("timeout_s", 300),
        "agent": args.get("agent") or "hermes",
    }
    return request_json("/lake/build", payload, timeout=int(payload["timeout_s"]) + 15)


TOOLS = {
    "proof_status": {
        "description": "Return health and token status for the remote Lean proof server.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_status,
    },
    "lean_check": {
        "description": "Check an inline Lean file on the remote proof server and return its receipt.",
        "inputSchema": {
            "type": "object",
            "required": ["code"],
            "properties": {
                "code": {"type": "string"},
                "name": {"type": "string"},
                "timeout_s": {"type": "integer", "minimum": 1, "maximum": 900},
                "agent": {"type": "string"},
            },
        },
        "handler": tool_check,
    },
    "lake_build": {
        "description": "Run an allowlisted lake build target on the remote proof server.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "timeout_s": {"type": "integer", "minimum": 1, "maximum": 1800},
                "agent": {"type": "string"},
            },
        },
        "handler": tool_build,
    },
}


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": name,
                        "description": data["description"],
                        "inputSchema": data["inputSchema"],
                    }
                    for name, data in TOOLS.items()
                ]
            },
        }
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in TOOLS:
            result = {"ok": False, "error": f"unknown tool: {name}"}
        else:
            result = TOOLS[name]["handler"](args)
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": json_text(result)}}
    if method and method.startswith("notifications/"):
        return None
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = handle(json.loads(line))
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": f"{type(exc).__name__}: {exc}"},
            }
        if response is not None:
            print(json.dumps(response, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
