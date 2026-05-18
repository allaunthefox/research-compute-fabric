#!/usr/bin/env python3
"""
Minimal embedded node surface.

This is a Docker-testable implementation of the surface contract in
docs/specs/EMBEDDED_NODE_SURFACE_SPEC.md. It intentionally uses only Python
stdlib so tiny nodes can run it before the final embedded image exists.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
import time
import zlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_HEALTH = 0
OP_STATUS = 1
OP_METRICS = 2
OP_ATTEST = 3
OP_COMPRESS = 4
OP_RGFLOW = 5
OP_ROUTE = 6
OP_MOUNT_STATUS = 7
OP_SNAPSHOT = 8
OP_ENTER_RECOVERY = 9
OP_PRIMITIVES = 10
OP_PLAN_ROUTE = 11
OP_WIKI = 12
OP_FRACTAL_FOLD = 13
OP_META_AUTOTYPE = 14
OP_CREDENTIALS = 15

CODEC_NONE = 0
CODEC_ZLIB_TEST = 1


def env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default))


PROFILE_PATH = env_path("RS_SURFACE_PROFILE", "/etc/rs-surface/node.json")
STATE_DIR = env_path("RS_SURFACE_STATE", "/var/lib/rs-surface")
MOUNT_DIR = env_path("RS_SURFACE_MOUNT", "/mnt/topological-storage")
STARTED_AT = time.time()


def load_profile() -> dict[str, Any]:
    with PROFILE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


PROFILE = load_profile()


def ensure_state() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    MOUNT_DIR.mkdir(parents=True, exist_ok=True)
    node_id = STATE_DIR / "node-id"
    if not node_id.exists():
        node_id.write_text(PROFILE["node_id"] + "\n", encoding="utf-8")
    last_good = STATE_DIR / "last-good.json"
    if not last_good.exists():
        last_good.write_text(
            json.dumps({"ok": True, "created_at": time.time()}, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def storage_status() -> str:
    marker = MOUNT_DIR / ".rs-surface-mounted"
    if marker.exists():
        return "mounted"
    if MOUNT_DIR.exists():
        return "degraded"
    return "absent"


def health_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "node": PROFILE["node_id"],
        "role": PROFILE["role"],
        "mode": PROFILE.get("mode_default", "normal"),
        "surface_version": PROFILE["surface_version"],
        "storage": storage_status(),
        "last_good": (STATE_DIR / "last-good.json").exists(),
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
    }


def status_payload() -> dict[str, Any]:
    return {
        "profile": PROFILE,
        "state_dir": str(STATE_DIR),
        "mount_dir": str(MOUNT_DIR),
        "hostname": socket.gethostname(),
    }


def metrics_payload() -> dict[str, Any]:
    state_bytes = 0
    for path in STATE_DIR.rglob("*"):
        if path.is_file():
            state_bytes += path.stat().st_size
    return {
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
        "state_bytes": state_bytes,
        "state_budget_mb": PROFILE.get("local_state_budget_mb"),
    }


def primitive_payload() -> dict[str, Any]:
    substrate = PROFILE.get("topological_substrate", {})
    primitives = substrate.get("primitives")
    if primitives is None:
        primitives = [
            "health",
            "status",
            "metrics",
            "attest",
            "compress",
            "rgflow",
            "route",
            "mount_status",
            "snapshot",
            "recovery",
            "plan_route",
            "wiki",
            "fractal_fold",
            "meta_autotype",
            "credentials",
        ]
    return {
        "node": PROFILE["node_id"],
        "role": PROFILE["role"],
        "substrate": substrate,
        "primitives": primitives,
    }


def resolve_bind_host() -> str:
    override = os.environ.get("RS_SURFACE_HOST")
    if override:
        return override

    api = PROFILE.get("api", {})
    bind = api.get("bind", "public")
    if bind == "localhost":
        return "127.0.0.1"
    if bind == "public":
        return "0.0.0.0"
    if bind == "tailscale":
        host = api.get("tailscale_ip") or PROFILE.get("tailscale_ip")
        if not host:
            raise RuntimeError("api.bind=tailscale requires api.tailscale_ip or top-level tailscale_ip")
        return str(host)
    raise RuntimeError(f"unsupported api.bind {bind!r}")


def rgflow_score(data: bytes) -> dict[str, Any]:
    if not data:
        return {"lawful": True, "score": 1.0, "reason": "empty-control-frame"}
    unique = len(set(data))
    density = unique / 256.0
    compressed = zlib.compress(data, level=6)
    ratio = len(compressed) / max(1, len(data))
    lawful = ratio < 0.98 or len(data) < 512
    return {
        "lawful": lawful,
        "score": round(max(0.0, 1.0 - ratio + density), 6),
        "compression_ratio": round(ratio, 6),
        "byte_diversity": round(density, 6),
        "reason": "test-rgflow-heuristic",
    }


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode_payload(codec: int, payload: bytes) -> bytes:
    if codec == CODEC_NONE:
        return payload
    if codec == CODEC_ZLIB_TEST:
        return zlib.decompress(payload)
    raise ValueError(f"unsupported codec {codec}")


def encode_payload(codec: int, payload: bytes) -> bytes:
    if codec == CODEC_NONE:
        return payload
    if codec == CODEC_ZLIB_TEST:
        return zlib.compress(payload, level=6)
    raise ValueError(f"unsupported codec {codec}")


def handle_surface_op(op: int, payload: bytes) -> dict[str, Any]:
    if op == OP_HEALTH:
        return health_payload()
    if op == OP_STATUS:
        return status_payload()
    if op == OP_METRICS:
        return metrics_payload()
    if op == OP_ATTEST:
        return {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "node": PROFILE["node_id"],
        }
    if op == OP_COMPRESS:
        compressed = zlib.compress(payload, level=6)
        return {
            "codec": "zlib-test",
            "raw_bytes": len(payload),
            "compressed_bytes": len(compressed),
            "ratio": round(len(compressed) / max(1, len(payload)), 6),
            "payload_b64": base64.b64encode(compressed).decode("ascii"),
        }
    if op == OP_RGFLOW:
        return rgflow_score(payload)
    if op == OP_ROUTE:
        return {
            "accepted": rgflow_score(payload)["lawful"],
            "route": "local" if len(payload) < 4096 else "atlas",
        }
    if op == OP_MOUNT_STATUS:
        return {
            "storage": storage_status(),
            "mount_point": str(MOUNT_DIR),
            "provider": PROFILE["storage"]["provider"],
            "required_for_boot": PROFILE["storage"]["required_for_boot"],
        }
    if op == OP_SNAPSHOT:
        digest = hashlib.sha256(payload).hexdigest()
        snapshot = STATE_DIR / "snapshot-last.json"
        snapshot.write_text(
            json.dumps({"sha256": digest, "bytes": len(payload), "t": time.time()}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {"snapshotted": True, "sha256": digest}
    if op == OP_ENTER_RECOVERY:
        return {"accepted": False, "reason": "recovery transition disabled in test image"}
    if op == OP_PRIMITIVES:
        return primitive_payload()
    if op == OP_PLAN_ROUTE:
        try:
            from omni_lut.unified_compression_route import choose_route
        except ModuleNotFoundError:
            import sys

            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from omni_lut.unified_compression_route import choose_route

        return choose_route(payload)
    if op == OP_WIKI:
        try:
            request = json.loads(payload.decode("utf-8")) if payload else {"op": "recent"}
            if not isinstance(request, dict):
                raise ValueError("wiki payload must be a JSON object")
            use_rds = os.environ.get("RS_USE_RDS", "").lower() in ("1", "true", "yes")
            if use_rds:
                try:
                    from infra.ene_rds_wiki_layer import ENERDSWikiLayer
                except ModuleNotFoundError:
                    import sys
                    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
                    from infra.ene_rds_wiki_layer import ENERDSWikiLayer

                wiki = ENERDSWikiLayer()
            else:
                try:
                    from infra.ene_wiki_layer import ENEWikiLayer
                except ModuleNotFoundError:
                    import sys
                    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
                    from infra.ene_wiki_layer import ENEWikiLayer

                wiki = ENEWikiLayer(STATE_DIR / "ene-wiki.db")
            return wiki.handle_request(request)
        except Exception as exc:
            return {"ok": False, "op": "wiki", "error": str(exc)}
    if op == OP_FRACTAL_FOLD:
        try:
            request = json.loads(payload.decode("utf-8")) if payload else {"op": "manifest"}
            if not isinstance(request, dict):
                raise ValueError("fractal_fold payload must be a JSON object")
            use_rds = os.environ.get("RS_USE_RDS", "").lower() in ("1", "true", "yes")
            if use_rds:
                try:
                    from infra.ene_rds_fractal_fold import ENERDSFractalFold
                except ModuleNotFoundError:
                    import sys
                    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
                    from infra.ene_rds_fractal_fold import ENERDSFractalFold

                fold = ENERDSFractalFold()
            else:
                try:
                    from infra.ene_fractal_fold import ENEFractalFold
                except ModuleNotFoundError:
                    import sys
                    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
                    from infra.ene_fractal_fold import ENEFractalFold

                fold = ENEFractalFold(STATE_DIR / "ene-fractal-fold.db")
            return fold.handle_request(request)
        except Exception as exc:
            return {"ok": False, "op": "fractal_fold", "error": str(exc)}
    if op == OP_META_AUTOTYPE:
        try:
            request = json.loads(payload.decode("utf-8")) if payload else {"text": ""}
            if not isinstance(request, dict):
                raise ValueError("meta_autotype payload must be a JSON object")
            try:
                from infra.ene_meta_autotype import handle_request
            except ModuleNotFoundError:
                import sys

                sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
                from infra.ene_meta_autotype import handle_request

            return handle_request(request)
        except Exception as exc:
            return {"ok": False, "op": "meta_autotype", "error": str(exc)}
    if op == OP_CREDENTIALS:
        try:
            request = json.loads(payload.decode("utf-8")) if payload else {}
            if not isinstance(request, dict):
                raise ValueError("credentials payload must be a JSON object")
            try:
                from credential_provider import (
                    credential_status,
                    provider_manifest,
                    resolve_credential,
                )
            except ModuleNotFoundError:
                try:
                    from infra.credential_provider import (
                        credential_status,
                        provider_manifest,
                        resolve_credential,
                    )
                except ModuleNotFoundError:
                    import sys

                    sys.path.insert(0, str(Path(__file__).resolve().parent))
                    from credential_provider import (
                        credential_status,
                        provider_manifest,
                        resolve_credential,
                    )

            action = request.get("action", "status")
            if action == "status":
                return credential_status()
            if action == "manifest":
                return provider_manifest()
            if action == "resolve":
                provider = request.get("provider", "")
                if not provider:
                    return {"ok": False, "error": "missing provider name"}
                cred = resolve_credential(provider)
                if cred is None:
                    return {"ok": False, "error": f"provider {provider!r} not available"}
                return {"ok": True, "provider": cred.provider, "value": cred.value}
            return {"ok": False, "error": f"unknown credentials action {action!r}"}
        except Exception as exc:
            return {"ok": False, "op": "credentials", "error": str(exc)}
    return {"error": "unknown-op", "op": op}


def parse_surface_frame(data: bytes) -> tuple[int, int, int, bytes]:
    if len(data) < 16:
        raise ValueError("surface frame too short")
    version, _flags, codec, op = data[:4]
    if version != 1:
        raise ValueError(f"unsupported version {version}")
    request_id, payload_len, crc_expected = struct.unpack("<III", data[4:16])
    payload = data[16 : 16 + payload_len]
    if len(payload) != payload_len:
        raise ValueError("payload length mismatch")
    crc_actual = zlib.crc32(payload) & 0xFFFFFFFF
    if crc_actual != crc_expected:
        raise ValueError("payload crc mismatch")
    return request_id, codec, op, decode_payload(codec, payload)


def build_surface_frame(request_id: int, op: int, payload_obj: Any, codec: int = CODEC_NONE) -> bytes:
    raw_payload = canonical_json(payload_obj)
    payload = encode_payload(codec, raw_payload)
    header = struct.pack(
        "<BBBBIII",
        1,
        0,
        codec,
        op,
        request_id,
        len(payload),
        zlib.crc32(payload) & 0xFFFFFFFF,
    )
    return header + payload


def read_exact(sock: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise EOFError("socket closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_ws_message(sock: socket.socket) -> bytes:
    b1, b2 = read_exact(sock, 2)
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F
    if opcode == 0x8:
        raise EOFError("websocket close")
    if length == 126:
        length = struct.unpack("!H", read_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", read_exact(sock, 8))[0]
    mask = read_exact(sock, 4) if masked else b""
    payload = bytearray(read_exact(sock, length))
    if masked:
        for i in range(length):
            payload[i] ^= mask[i % 4]
    return bytes(payload)


def write_ws_message(sock: socket.socket, payload: bytes) -> None:
    header = bytearray([0x82])
    length = len(payload)
    if length < 126:
        header.append(length)
    elif length <= 0xFFFF:
        header.append(126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", length))
    sock.sendall(bytes(header) + payload)


class SurfaceHandler(BaseHTTPRequestHandler):
    server_version = "rs-surface/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)

    def send_json(self, obj: Any, status: int = 200) -> None:
        payload = json.dumps(obj, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(health_payload())
            return
        if self.path == "/status":
            self.send_json(status_payload())
            return
        if self.path == "/metrics":
            self.send_json(metrics_payload())
            return
        if self.path == "/primitives":
            self.send_json(primitive_payload())
            return
        if self.path == "/ws":
            self.handle_ws()
            return
        if self.path == "/credentials":
            try:
                from credential_provider import credential_status
            except ModuleNotFoundError:
                try:
                    from infra.credential_provider import credential_status
                except ModuleNotFoundError:
                    import sys

                    sys.path.insert(0, str(Path(__file__).resolve().parent))
                    from credential_provider import credential_status

            self.send_json(credential_status())
            return
        self.send_json({"error": "not-found"}, HTTPStatus.NOT_FOUND)

    def handle_ws(self) -> None:
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self.send_json({"error": "missing-websocket-key"}, HTTPStatus.BAD_REQUEST)
            return
        accept = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")
        self.send_response(HTTPStatus.SWITCHING_PROTOCOLS)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()

        sock = self.connection
        while True:
            try:
                data = read_ws_message(sock)
                request_id, codec, op, payload = parse_surface_frame(data)
                result = handle_surface_op(op, payload)
                write_ws_message(sock, build_surface_frame(request_id, op, result, codec=codec))
            except EOFError:
                return
            except Exception as exc:
                frame = build_surface_frame(0, OP_STATUS, {"error": str(exc)}, codec=CODEC_NONE)
                write_ws_message(sock, frame)
                return


def main() -> int:
    ensure_state()
    host = resolve_bind_host()
    port = int(os.environ.get("RS_SURFACE_PORT", str(PROFILE.get("api", {}).get("plain_health_port", 8080))))
    httpd = ThreadingHTTPServer((host, port), SurfaceHandler)
    print(f"rs-surface listening on {host}:{port} node={PROFILE['node_id']}", flush=True)
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
