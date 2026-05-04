# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""
omni:// URI Resolver

Implements the omni:// scheme as defined in OMNI_URI_SCHEME.md.

Resolution rules (from spec §Step 3):
  port == 8447  → HTTP JSON
  port == 8446  → Omnitoken binary TCP
  default port  → 8446

Usage:
    from omni_resolver import omni_request

    result = omni_request("omni://localhost/attest/e3b0c442?source=claude")
    result = omni_request("omni://localhost:8447/metrics")
    result = omni_request("omni://localhost/health")
"""

import json
import os
import socket
import sqlite3
import struct
import time
import urllib.parse
import urllib.request
import urllib.error
import zlib
from typing import Any
import hashlib

from omnitoken_fragmentation import (
    MAX_FRAGMENT_COUNT,
    MAX_UNFRAGMENTED,
    TAG_CHUNK_HEX_FIELD,
    TAG_FRAGMENT_NAME,
    TAG_SEQ_FIELD,
    TAG_SHA256_FIELD,
    TAG_TOTAL_FIELD,
    chunk_size_for_tag_fragments,
)

# Hardcoded fallbacks — overridden by sub-register lookup at runtime
_DEFAULT_PORT_FALLBACK = 8446
_HTTP_PORT_FALLBACK = 8447
TIMEOUT = 2.0

# Sub-register keys for port bindings
_SUBREGISTER_TCP  = "subregister:port:warden:tcp"
_SUBREGISTER_HTTP = "subregister:port:warden:http"

# Prefix for any additional HTTP service port bindings
_SUBREGISTER_HTTP_PREFIX = "subregister:port:"
_SUBREGISTER_HTTP_SUFFIX = ":http"

# DB path — resolved relative to this file or via env override
_DB_PATH = os.environ.get(
    "SUBSTRATE_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate_index.db"),
)


def _lookup_port(sub_register_key: str, fallback: int) -> int:
    """
    Read a port value from the substrate sub-register.

    Queries packages WHERE sub_register_key=? and reads meta_capsule.port.
    Falls back to hardcoded default if DB is absent or entry is missing.
    """
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=1.0)
        row = conn.execute(
            "SELECT meta_capsule FROM packages WHERE sub_register_key=? LIMIT 1",
            (sub_register_key,),
        ).fetchone()
        conn.close()
        if row and row[0]:
            meta = json.loads(row[0])
            return int(meta["port"])
    except (sqlite3.Error, KeyError, TypeError, ValueError, OSError):
        pass
    return fallback


def _get_default_port() -> int:
    """TCP port from sub-register (subregister:port:warden:tcp)."""
    return _lookup_port(_SUBREGISTER_TCP, _DEFAULT_PORT_FALLBACK)


def _get_http_port() -> int:
    """HTTP port from sub-register (subregister:port:warden:http)."""
    return _lookup_port(_SUBREGISTER_HTTP, _HTTP_PORT_FALLBACK)


def _get_all_http_ports() -> set[int]:
    """Load all HTTP service ports from sub-register (any key ending in :http)."""
    ports = {_HTTP_PORT_FALLBACK}
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=1.0)
        rows = conn.execute(
            "SELECT meta_capsule FROM packages WHERE register_class='BOUND_PORT' AND sub_register_key LIKE ?",
            (f"{_SUBREGISTER_HTTP_PREFIX}%{_SUBREGISTER_HTTP_SUFFIX}",),
        ).fetchall()
        conn.close()
        for (mc,) in rows:
            if mc:
                meta = json.loads(mc)
                if "port" in meta:
                    ports.add(int(meta["port"]))
    except (sqlite3.Error, KeyError, TypeError, ValueError, OSError):
        pass
    return ports


def _lookup_host(pkg: str, fallback: str) -> str:
    """Read host from meta_capsule for a given package name."""
    try:
        conn = sqlite3.connect(_DB_PATH, timeout=1.0)
        row = conn.execute(
            "SELECT meta_capsule FROM packages WHERE pkg=? LIMIT 1",
            (pkg,),
        ).fetchone()
        conn.close()
        if row and row[0]:
            meta = json.loads(row[0])
            return meta.get("host", fallback)
    except (sqlite3.Error, KeyError, TypeError, ValueError, OSError):
        pass
    return fallback


def _get_warden_host() -> str:
    return _lookup_host("warden-port-http", "localhost")


def _get_builder_host() -> str:
    return _lookup_host("builder-port-http", "localhost")


def _get_racknerd_host() -> str:
    return _lookup_host("racknerd-warden-http", "127.0.0.1")


def _get_judge_host() -> str:
    return _lookup_host("judge-warden-http", "127.0.0.1")



# Cached at module load — call rebind_ports() to refresh after a DB change
DEFAULT_PORT: int      = _get_default_port()
HTTP_PORT: int         = _get_http_port()
HTTP_PORTS: set[int]   = _get_all_http_ports()
WARDEN_HOST: str       = _get_warden_host()
BUILDER_HOST: str      = _get_builder_host()
RACKNERD_HOST: str     = _get_racknerd_host()
JUDGE_HOST: str        = _get_judge_host()

# Logical hostname aliases → resolved hosts
_HOST_ALIASES: dict[str, str] = {
    "warden":       WARDEN_HOST,
    "architect":    WARDEN_HOST,
    "builder":      BUILDER_HOST,
    "racknerd":     RACKNERD_HOST,
    "racknerd-atl": RACKNERD_HOST,
    "judge":        JUDGE_HOST,
}


def rebind_ports() -> tuple[int, int]:
    """Re-read all ports from the sub-register and update module globals."""
    global DEFAULT_PORT, HTTP_PORT, HTTP_PORTS
    DEFAULT_PORT = _get_default_port()
    HTTP_PORT    = _get_http_port()
    HTTP_PORTS   = _get_all_http_ports()
    return DEFAULT_PORT, HTTP_PORT


# ── Omnitoken codec (inline, no import dependency) ───────────────────────────

def _otk_encode(name: str, value: float, tags: dict) -> bytes:
    packet = bytearray()
    packet.extend(b'\x00\x4F\x54\x4B')
    name_b = name.encode()
    packet.extend(len(name_b).to_bytes(2, 'big'))
    packet.extend(name_b)
    packet.extend(struct.pack('>d', value))
    packet.extend(int(time.time() * 1_000_000).to_bytes(8, 'big'))
    tags_b = json.dumps(tags, sort_keys=True).encode()
    packet.extend(len(tags_b).to_bytes(2, 'big'))
    packet.extend(tags_b)
    packet.extend((zlib.crc32(packet) & 0xFFFFFFFF).to_bytes(4, 'big'))
    return bytes(packet)


def _otk_decode(data: bytes) -> dict | None:
    if len(data) < 22:
        return None
    body, crc_bytes = data[:-4], data[-4:]
    if (zlib.crc32(body) & 0xFFFFFFFF) != int.from_bytes(crc_bytes, 'big'):
        return None
    if data[:4] != b'\x00\x4F\x54\x4B':
        return None
    off = 4
    nlen = int.from_bytes(data[off:off+2], 'big'); off += 2
    name = data[off:off+nlen].decode(); off += nlen
    value = struct.unpack('>d', data[off:off+8])[0]; off += 8
    off += 8  # skip timestamp
    tlen = int.from_bytes(data[off:off+2], 'big'); off += 2
    tags = json.loads(data[off:off+tlen].decode())
    return {"name": name, "value": value, "tags": tags}


# ── Transport ─────────────────────────────────────────────────────────────────

def _http_request(host: str, port: int, path: str,
                  params: dict | None = None,
                  body: dict | None = None) -> Any:
    """HTTP JSON transport."""
    query = ("?" + urllib.parse.urlencode(params)) if params else ""
    url = f"http://{host}:{port}{path}{query}"
    transport = _transport_for(host)
    headers = {
        "X-Omni-Transport": transport,
        "X-Omni-Token":     "OMNITOKEN/4",
    }
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        return json.loads(resp.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _tcp_request(host: str, port: int, name: str,
                 value: float, tags: dict) -> Any:
    """Omnitoken binary TCP transport (port 8446)."""
    packet = _otk_encode(name, value, tags)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((host, port))
        sock.sendall(packet)
        resp = sock.recv(4096)
        sock.close()
        return _otk_decode(resp)
    except (OSError, socket.timeout):
        return None


def _udp_request(host: str, port: int, name: str,
                 value: float, tags: dict) -> Any:
    """Omnitoken UDP transport — NAT-friendly, self-assembling."""
    packet = _otk_encode(name, value, tags)

    datagrams = [packet]
    if len(packet) > MAX_UNFRAGMENTED:
        chunk_size = chunk_size_for_tag_fragments(MAX_UNFRAGMENTED, base_tags={"op": tags.get("op", "QUERY")})
        chunks = [packet[index:index + chunk_size] for index in range(0, len(packet), chunk_size)]
        if len(chunks) > MAX_FRAGMENT_COUNT:
            raise ValueError(f"UDP payload requires {len(chunks)} fragments; max is {MAX_FRAGMENT_COUNT}")

        payload_sha256 = hashlib.sha256(packet).hexdigest()
        datagrams = []
        for index, chunk in enumerate(chunks):
            fragment_tags = {
                "op": tags.get("op", "QUERY"),
                TAG_SEQ_FIELD: str(index + 1),
                TAG_TOTAL_FIELD: str(len(chunks)),
                TAG_SHA256_FIELD: payload_sha256,
                TAG_CHUNK_HEX_FIELD: chunk.hex(),
            }
            datagrams.append(_otk_encode(TAG_FRAGMENT_NAME, 0.0, fragment_tags))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT)
        for datagram in datagrams:
            sock.sendto(datagram, (host, port))
        resp, _ = sock.recvfrom(4096)
        sock.close()
        return _otk_decode(resp)
    except (OSError, socket.timeout):
        return None


# ── URI parser ────────────────────────────────────────────────────────────────

_TAILSCALE_RANGE_START = (100 << 24) | (64 << 16)   # 100.64.0.0
_TAILSCALE_RANGE_END   = (100 << 24) | (128 << 16)  # 100.128.0.0  (/10 = 64 blocks of /16)


def _is_tailscale_ip(host: str) -> bool:
    """Return True if host is in the Tailscale address range 100.64.0.0/10."""
    try:
        parts = [int(p) for p in host.split(".")]
        if len(parts) != 4:
            return False
        ip_int = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
        return _TAILSCALE_RANGE_START <= ip_int < _TAILSCALE_RANGE_END
    except (ValueError, AttributeError):
        return False


def _transport_for(host: str) -> str:
    """Return the transport protocol name for a given resolved host."""
    if host == "localhost" or host == "127.0.0.1":
        return "OMNITOKEN"
    if _is_tailscale_ip(host):
        return "TAILSCALE"
    return "TCP"


def _parse(uri: str) -> tuple[str, int, str, dict]:
    """Return (host, port, path, params). Resolves logical hostname aliases."""
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "omni":
        raise ValueError(f"Not an omni:// URI: {uri!r}")
    host = parsed.hostname or "localhost"
    host = _HOST_ALIASES.get(host, host)
    port = parsed.port or DEFAULT_PORT
    path = parsed.path or "/"
    params = dict(urllib.parse.parse_qsl(parsed.query))
    return host, port, path, params


# ── Resource dispatch ─────────────────────────────────────────────────────────

_UDP_OFFSET = 1  # Warden UDP port = TCP port + 1

def _dispatch_tcp(host: str, port: int, path: str, params: dict) -> Any:
    """Map path + params to an Omnitoken operation. Tries UDP first, then TCP."""
    transport = _transport_for(host)
    udp_port = port + _UDP_OFFSET
    
    # Build tags with transport info
    def _mk_tags(op: str, extra: dict = None) -> dict:
        tags = {"op": op, "transport": transport}
        if extra:
            tags.update(extra)
        tags.update(params)
        return tags
    
    # Try UDP first (NAT-friendly, self-assembling)
    def _try_udp(name: str, value: float, tags: dict):
        result = _udp_request(host, udp_port, name, value, tags)
        if result is not None:
            result['_transport'] = 'UDP'
        return result
    
    # TCP fallback
    def _try_tcp(name: str, value: float, tags: dict):
        result = _tcp_request(host, port, name, value, tags)
        if result is not None:
            result['_transport'] = 'TCP'
        return result
    
    if path.startswith("/attest/"):
        sha256 = path[8:]
        tags = _mk_tags("ATTEST", {"sha256": sha256})
        return _try_udp(f"omni:attest:{sha256[:16]}", 1.0, tags) or _try_tcp(f"omni:attest:{sha256[:16]}", 1.0, tags)

    if path.startswith("/verify/"):
        sha256 = path[8:]
        tags = _mk_tags("VERIFY", {"sha256": sha256})
        return _try_udp(f"omni:verify:{sha256[:16]}", 1.0, tags) or _try_tcp(f"omni:verify:{sha256[:16]}", 1.0, tags)

    if path == "/metrics":
        tags = _mk_tags("QUERY")
        return _try_udp("omni:metrics", 0.0, tags) or _try_tcp("omni:metrics", 0.0, tags)

    if path.startswith("/dag/"):
        tick = path[5:]
        tags = _mk_tags("QUERY", {"tick": tick})
        return _try_udp(f"omni:dag:{tick}", float(tick or 0), tags) or _try_tcp(f"omni:dag:{tick}", float(tick or 0), tags)

    if path.startswith("/lut/"):
        protocol = path[5:]
        tags = _mk_tags("LUT", {"protocol": protocol})
        return _try_udp(f"omni:lut:{protocol}", 1.0, tags) or _try_tcp(f"omni:lut:{protocol}", 1.0, tags)

    if path == "/transport":
        mi = float(params.get("mi", "0"))
        size = int(params.get("size", "0"))
        tags = _mk_tags("TRANSPORT", {"mi": str(mi), "size": str(size)})
        return _try_udp("omni:transport", mi, tags) or _try_tcp("omni:transport", mi, tags)

    if path == "/health":
        tags = _mk_tags("QUERY")
        return _try_udp("omni:health", 1.0, tags) or _try_tcp("omni:health", 1.0, tags)

    # Fallback: generic operation
    tags = _mk_tags("QUERY", {"path": path})
    return _try_udp(f"omni:{path.strip('/')}", 1.0, tags) or _try_tcp(f"omni:{path.strip('/')}", 1.0, tags)


# ── Public API ────────────────────────────────────────────────────────────────

def omni_request(uri: str, body: dict | None = None) -> Any:
    """
    Resolve and execute an omni:// URI.

    Port determines transport:
      8447  → HTTP JSON  (GET or POST if body supplied)
      other → Omnitoken binary TCP

    Returns parsed response dict, or None on failure.
    """
    host, port, path, params = _parse(uri)

    if port in HTTP_PORTS:
        return _http_request(host, port, path, params or None, body)

    return _dispatch_tcp(host, port, path, params)


def omni_attest(sha256: str, metadata: dict | None = None,
                host: str = "localhost", port: int = DEFAULT_PORT) -> Any:
    """Convenience: attest a hash via omni://."""
    params = urllib.parse.urlencode(metadata or {})
    sep = "?" if params else ""
    return omni_request(f"omni://{host}:{port}/attest/{sha256}{sep}{params}")


def omni_verify(sha256: str, host: str = "localhost",
                port: int = DEFAULT_PORT) -> Any:
    """Convenience: verify an attestation via omni://."""
    return omni_request(f"omni://{host}:{port}/verify/{sha256}")


def omni_metrics(host: str = "localhost", port: int = HTTP_PORT) -> Any:
    """Convenience: fetch metrics via omni:// (defaults to HTTP port)."""
    return omni_request(f"omni://{host}:{port}/metrics")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: omni_resolver.py <omni://uri>")
        sys.exit(1)

    result = omni_request(sys.argv[1])
    print(json.dumps(result, indent=2) if result else "null")
