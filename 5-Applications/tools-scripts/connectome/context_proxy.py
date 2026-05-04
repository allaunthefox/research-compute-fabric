# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

from __future__ import annotations

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""Local proxy that applies context compression to Anthropic API requests.

Sits between Cline (or any API client) and the Anthropic API.
Intercepts tool_result content blocks in conversation messages,
compresses them through the context gate, and caches API responses.

Usage:
    python 5-Applications/scripts/context_proxy.py --port 8090

Then configure Cline to use http://localhost:8090 as the API base URL.

Response caching: identical compressed requests return cached responses
without hitting the upstream API. Cache TTL: 2 hours (configurable).
"""


import hashlib
import json
import os
import sqlite3
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from context_gate import ContextGate, GateMode

try:
    from pbacs.kimi_context_optimizer import KimiContextOptimizer
    _kimi_compressor = KimiContextOptimizer(token_budget=16000)
except Exception:
    _kimi_compressor = None

UPSTREAM_URL = "https://api.anthropic.com"
RESPONSE_CACHE_TTL = int(os.environ.get("PROXY_CACHE_TTL_SECS", 7200))
COMPRESS_THRESHOLD = 2048  # bytes — only compress large tool results

_HOT_TERMS = [
    "soliton", "omnitoken", "tardygrada", "waveprobe", "ptos",
    "hyperlut", "neuromorphic", "geomtree", "kolmogorov",
    "metafoam", "hyperfluid", "cognitivesmoother",
]

_gate = ContextGate(
    warden_db_path=_ROOT / "warden_attestation.db",
    substrate_db_path=_ROOT / "substrate_index.db",
    hot_terms=_HOT_TERMS,
    compressor=_kimi_compressor,
)

# Response cache in substrate_index.db
_CACHE_DB = _ROOT / "substrate_index.db"


def _ensure_response_cache():
    if not _CACHE_DB.exists():
        return
    try:
        conn = sqlite3.connect(str(_CACHE_DB))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS response_cache ("
            "  request_hash TEXT PRIMARY KEY,"
            "  response_json TEXT NOT NULL,"
            "  created_ts REAL,"
            "  hits INTEGER DEFAULT 0"
            ")"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _cache_lookup(request_hash: str) -> str | None:
    if not _CACHE_DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(_CACHE_DB))
        row = conn.execute(
            "SELECT response_json, created_ts FROM response_cache "
            "WHERE request_hash = ?",
            (request_hash,),
        ).fetchone()
        if row:
            age = time.time() - row[1]
            if age < RESPONSE_CACHE_TTL:
                conn.execute(
                    "UPDATE response_cache SET hits = hits + 1 "
                    "WHERE request_hash = ?",
                    (request_hash,),
                )
                conn.commit()
                conn.close()
                return row[0]
            else:
                conn.execute(
                    "DELETE FROM response_cache WHERE request_hash = ?",
                    (request_hash,),
                )
                conn.commit()
        conn.close()
    except Exception:
        pass
    return None


def _cache_store(request_hash: str, response_json: str):
    if not _CACHE_DB.exists():
        return
    try:
        conn = sqlite3.connect(str(_CACHE_DB))
        conn.execute(
            "INSERT OR REPLACE INTO response_cache "
            "(request_hash, response_json, created_ts, hits) "
            "VALUES (?, ?, ?, 0)",
            (request_hash, response_json, time.time()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def compress_messages(messages: list) -> list:
    """Compress tool_result content blocks in the message list."""
    compressed = []
    for msg in messages:
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            new_content = []
            for block in msg["content"]:
                if (
                    block.get("type") == "tool_result"
                    and isinstance(block.get("content"), str)
                    and len(block["content"]) > COMPRESS_THRESHOLD
                ):
                    result = _gate.process(
                        block["content"], mode=GateMode.COMPRESS
                    )
                    block = dict(block)
                    block["content"] = result.safe_text
                new_content.append(block)
            msg = dict(msg)
            msg["content"] = new_content
        compressed.append(msg)
    return compressed


def request_hash(body: dict) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        # Parse and compress
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._forward_raw(raw_body)
            return

        # Only intercept messages endpoint
        if self.path == "/v1/messages":
            if "messages" in body:
                body["messages"] = compress_messages(body["messages"])

            # Check response cache
            req_hash = request_hash(body)
            cached = _cache_lookup(req_hash)
            if cached and not body.get("stream", False):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Cache", "HIT")
                cached_bytes = cached.encode()
                self.send_header("Content-Length", str(len(cached_bytes)))
                self.end_headers()
                self.wfile.write(cached_bytes)
                return

        # Forward to upstream
        compressed_body = json.dumps(body).encode()
        self._forward(compressed_body, req_hash if self.path == "/v1/messages" else None)

    def _forward(self, body: bytes, cache_key: str | None):
        url = UPSTREAM_URL + self.path
        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in ("host", "content-length")
        }
        headers["Content-Length"] = str(len(body))

        req = Request(url, data=body, headers=headers, method="POST")
        try:
            resp = urlopen(req)
            resp_body = resp.read()

            self.send_response(resp.status)
            for key, val in resp.getheaders():
                if key.lower() not in ("transfer-encoding",):
                    self.send_header(key, val)
            self.send_header("X-Cache", "MISS")
            self.end_headers()
            self.wfile.write(resp_body)

            # Cache non-streaming responses
            if cache_key and not json.loads(body).get("stream", False):
                _cache_store(cache_key, resp_body.decode(errors="replace"))

        except HTTPError as e:
            self.send_response(e.code)
            resp_body = e.read()
            self.end_headers()
            self.wfile.write(resp_body)

    def _forward_raw(self, body: bytes):
        self._forward(body, None)

    def do_GET(self):
        url = UPSTREAM_URL + self.path
        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() != "host"
        }
        req = Request(url, headers=headers, method="GET")
        try:
            resp = urlopen(req)
            resp_body = resp.read()
            self.send_response(resp.status)
            for key, val in resp.getheaders():
                if key.lower() not in ("transfer-encoding",):
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(resp_body)
        except HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())

    def log_message(self, format, *args):
        # Minimal logging
        if "cache" in str(args).lower() or "error" in str(args).lower():
            super().log_message(format, *args)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Context compression proxy")
    p.add_argument("--port", type=int, default=8090)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args()

    _ensure_response_cache()

    server = HTTPServer((args.host, args.port), ProxyHandler)
    print(f"Context proxy listening on {args.host}:{args.port}")
    print(f"  Upstream: {UPSTREAM_URL}")
    print(f"  Cache TTL: {RESPONSE_CACHE_TTL}s")
    print(f"  Substrate DB: {_CACHE_DB}")
    print(f"  Hot terms: {len(_HOT_TERMS)}")
    print()
    print("Configure Cline API base URL: http://localhost:8090")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()



if __name__ == "__main__":
    main()
