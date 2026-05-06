#!/usr/bin/env python3
"""Tiny JSON-RPC tool surface for the repo-local Substack helper.

This implements just enough MCP-style JSON-RPC for future local plugin use.
The CLI helper remains the canonical path in normal shell workflows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from prepare_substack_post import prepare


TOOLS = [
    {
        "name": "prepare_substack_post",
        "description": "Prepare a local Markdown draft and assets for Substack import.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "markdown_path": {"type": "string"},
                "output_dir": {"type": "string"},
            },
            "required": ["markdown_path"],
        },
    }
]


def respond(request_id, result=None, error=None) -> None:
    payload = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = {"code": -32000, "message": str(error)}
    else:
        payload["result"] = result
    print(json.dumps(payload), flush=True)


def handle(message: dict) -> None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    try:
        if method == "initialize":
            respond(request_id, {"protocolVersion": "2024-11-05", "serverInfo": {"name": "substack-connector", "version": "0.1.0"}, "capabilities": {"tools": {}}})
        elif method == "tools/list":
            respond(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            if name != "prepare_substack_post":
                raise ValueError(f"unknown tool: {name}")
            output_dir = Path(args["output_dir"]) if args.get("output_dir") else None
            data = prepare(Path(args["markdown_path"]), output_dir)
            respond(request_id, {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]})
        else:
            respond(request_id, {})
    except Exception as exc:
        respond(request_id, error=exc)


def main() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        handle(json.loads(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
