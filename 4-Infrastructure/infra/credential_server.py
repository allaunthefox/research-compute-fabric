"""Credential server — REST + OpenAPI access point for API keys.

Reads credentials from credential_provider (env vars + config file + RDS)
and serves them via HTTP so no script needs direct env var access.

Usage:
  # Standalone
  python3 credential_server.py [--port 8444] [--bind 0.0.0.0]

  # Via existing embedded surface (if RS_CREDENTIAL_SERVER_PORT is set)
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from credential_provider import (
    credential_status,
    provider_manifest,
    resolve_credential,
    _rds_connect,
    _cred_server_url
)

VERSION = "0.4"
OPENAPI_VERSION = "3.0.3"

OPENAPI_SPEC: dict[str, Any] = {
    "openapi": OPENAPI_VERSION,
    "info": {
        "title": "Research Stack Credential Provider",
        "description": "Central API key access point for all stack services. "
                       "Set keys once on the microVM, consume from anywhere.",
        "version": VERSION,
    },
    "servers": [
        {"url": "http://localhost:8444", "description": "Local / Tailnet default"},
    ],
    "paths": {
        "/": {
            "get": {
                "summary": "Service root",
                "responses": {"200": {"description": "Service info + links"}},
            }
        },
        "/health": {
            "get": {
                "summary": "Health check",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/openapi.json": {
            "get": {
                "summary": "OpenAPI 3.0 specification",
                "responses": {"200": {"description": "This document"}},
            }
        },
        "/credentials": {
            "get": {
                "summary": "List all available credential providers",
                "responses": {
                    "200": {
                        "description": "Provider manifest",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "providers": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "description": {"type": "string"},
                                                    "available": {"type": "boolean"},
                                                },
                                            },
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/credentials/{provider}": {
            "get": {
                "summary": "Resolve a specific provider credential",
                "parameters": [
                    {
                        "name": "provider",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Provider name (deepseek, bedrock, etc.)",
                    }
                ],
                "responses": {
                    "200": {"description": "Credential value"},
                    "404": {"description": "Provider not found"},
                },
            }
        },
        "/status": {
            "get": {
                "summary": "Credential provider status",
                "responses": {"200": {"description": "Backend info + counts"}},
            }
        },
    },
}


SERVICE_INFO: dict[str, Any] = {
    "service": "credential-provider",
    "version": VERSION,
    "docs": "/openapi.json",
    "credentials": "/credentials",
    "status": "/status",
    "health": "/health",
}


class CredentialHTTPHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[credential-server] {args[0]} {args[1]} {args[2]}\n")

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str):
        self._send_json({"ok": False, "error": message}, status)

    def do_GET(self):
        path = self.path.rstrip("/") or "/"

        if path in ("/", "/api"):
            return self._send_json(SERVICE_INFO)

        if path in ("/health", "/api/health"):
            return self._send_json({"status": "ok", "version": VERSION})

        if path == "/openapi.json":
            return self._send_json(OPENAPI_SPEC)

        if path in ("/status", "/api/status"):
            return self._send_json(credential_status())

        if path == "/credentials" or path == "/api/credentials":
            return self._send_json(provider_manifest())

        m = re.match(r"^(?:/api)?/credentials/([a-zA-Z0-9_-]+)$", path)
        if m:
            provider = m.group(1).lower()
            cred = resolve_credential(provider)
            if cred is None:
                return self._send_error(404, f"provider '{provider}' not found")
            return self._send_json({
                "ok": True,
                "provider": cred.provider,
                "key": cred.value,
                "key_name": cred.key_name,
            })

        return self._send_error(404, f"not found: {path}")

    def do_POST(self):
        path = self.path.rstrip("/") or "/"

        if path in ("/api/webhooks/linear", "/webhooks/linear"):
            # Read raw body
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            # Node identification logic: proxy or process
            node_id = os.environ.get("RS_SURFACE_NODE_ID", "")
            if node_id != "MicroVM-Racknerd":
                # Act as Proxy: Forward POST request to the central microVM
                target_url = f"{_cred_server_url}/api/webhooks/linear"
                req = urllib.request.Request(target_url, data=raw_body, method="POST")
                for k, v in self.headers.items():
                    if k.lower() in ("content-type", "linear-signature"):
                        req.add_header(k, v)
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        resp_data = json.loads(resp.read().decode("utf-8"))
                        return self._send_json(resp_data, resp.status)
                except urllib.error.HTTPError as e:
                    try:
                        err_data = json.loads(e.read().decode("utf-8"))
                        return self._send_json(err_data, e.code)
                    except Exception:
                        return self._send_error(e.code, f"Forwarding failed: {e}")
                except Exception as e:
                    return self._send_error(500, f"Forwarding connection error: {e}")

            # Act as Server: Process Linear webhook body and upsert into Aurora RDS ENE packages table
            try:
                data = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                return self._send_error(400, f"Invalid JSON payload: {e}")

            action = data.get("action")
            issue_data = data.get("data", {})
            payload_type = data.get("type")

            if payload_type != "Issue":
                return self._send_json({"ok": True, "message": f"Ignored non-Issue payload: {payload_type}"})

            identifier = issue_data.get("identifier")
            if not identifier:
                return self._send_error(400, "Missing issue identifier")

            pkg_id = f"linear/{identifier}"

            if action == "remove":
                try:
                    conn = _rds_connect()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM ene.packages WHERE pkg = %s", (pkg_id,))
                    conn.commit()
                    conn.close()
                    return self._send_json({"ok": True, "action": "delete", "pkg": pkg_id})
                except Exception as e:
                    return self._send_error(500, f"Database delete error: {e}")

            # Extract title and description
            title = issue_data.get("title", "")
            description = issue_data.get("description", "")
            full_text = f"{title}\n\n{description}" if description else title
            url = issue_data.get("url", "")

            # Extract labels
            labels_data = issue_data.get("labels", [])
            labels_list = []
            if isinstance(labels_data, list):
                for l in labels_data:
                    if isinstance(l, dict):
                        labels_list.append(l.get("name"))
                    elif isinstance(l, str):
                        labels_list.append(l)
            tags_json = json.dumps(labels_list)

            import datetime
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            try:
                conn = _rds_connect()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO ene.packages (
                        pkg, version, domain, tier, archetype, 
                        tags, description, source, indexed_utc
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pkg) DO UPDATE SET
                        description = EXCLUDED.description,
                        tags = EXCLUDED.tags,
                        source = EXCLUDED.source,
                        indexed_utc = EXCLUDED.indexed_utc
                """, (
                    pkg_id,
                    "1.0.0",
                    "LINEAR",
                    "INTENT",
                    "issue",
                    tags_json,
                    full_text,
                    url,
                    now_iso
                ))
                conn.commit()
                conn.close()
                return self._send_json({"ok": True, "action": action, "pkg": pkg_id})
            except Exception as e:
                return self._send_error(500, f"Database upsert error: {e}")

        return self._send_error(404, f"not found: {path}")

    do_HEAD = do_GET


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Research Stack Credential Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("RS_CREDENTIAL_PORT", "8444")))
    parser.add_argument("--bind", default=os.environ.get("RS_CREDENTIAL_BIND", "0.0.0.0"))
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.bind, args.port), CredentialHTTPHandler)
    print(f"[credential-server] listening on {args.bind}:{args.port}", flush=True)
    print(f"[credential-server] OpenAPI spec at http://{args.bind}:{args.port}/openapi.json", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[credential-server] shutting down", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()
