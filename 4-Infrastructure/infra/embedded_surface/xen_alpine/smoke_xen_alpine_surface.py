#!/usr/bin/env python3
"""HTTP smoke check for the Alpine/Xen rs-surface carrier."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def fetch_json(url: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = response.read()
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{url} did not return a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    base = f"http://{args.host}:{args.port}"
    paths = ["/health", "/status", "/metrics", "/primitives"]
    receipt: dict[str, Any] = {
        "ok": True,
        "checked_at": time.time(),
        "base_url": base,
        "checks": {},
    }

    for path in paths:
        try:
            receipt["checks"][path] = fetch_json(base + path, args.timeout)
        except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
            receipt["ok"] = False
            receipt["checks"][path] = {"ok": False, "error": str(exc)}

    health = receipt["checks"].get("/health", {})
    receipt["node"] = health.get("node")
    receipt["surface_version"] = health.get("surface_version")

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
