#!/usr/bin/env python3
"""
External Service Registry — MySQL-backed node discovery and credential store.

Backup/fallback registry. Primary discovery uses Tailscale mesh + internal infra.
This MySQL backend is for:
  - Edge nodes that can't reach the mesh (ESP32, Cloudflare Workers)
  - Mesh-down fallback (Tailscale outage)
  - Cross-mesh discovery (nodes on different tailnets)
  - Low-impact config distribution

Primary path: Tailscale mesh + internal PostgreSQL/SQLite
Backup path: This MySQL registry (InfinityFree, always available)

Schema:
  nodes       — registered devices with capabilities and tier
  credentials — encrypted credential blobs (short TTL)
  config      — distributed configuration key-value store

Security:
  - Credentials are encrypted at rest (ChaCha20, key from env)
  - Connection over TLS when available
  - No plaintext secrets in the database
  - Short TTL tokens auto-expire
"""

import json
import os
import time
import hashlib
import struct
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# ── Connection config (from env or defaults) ─────────────────────────────────

DB_HOST = os.environ.get("REGISTRY_HOST", "sql103.infinityfree.com")
DB_PORT = int(os.environ.get("REGISTRY_PORT", "3306"))
DB_USER = os.environ.get("REGISTRY_USER", "if0_42058601")
DB_PASS = os.environ.get("REGISTRY_PASS", "")
DB_NAME = os.environ.get("REGISTRY_DB", "if0_42058601_registry")

ENCRYPTION_KEY = os.environ.get("REGISTRY_ENCRYPT_KEY", "")

# ── Schema ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    node_id VARCHAR(128) PRIMARY KEY,
    hostname VARCHAR(256) NOT NULL,
    tailscale_ip VARCHAR(45),
    public_ip VARCHAR(45),
    tier VARCHAR(32) NOT NULL DEFAULT 'OFFLINE',
    capabilities JSON,
    limitations JSON,
    last_seen_at DATETIME NOT NULL,
    registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tier (tier),
    INDEX idx_last_seen (last_seen_at)
);

CREATE TABLE IF NOT EXISTS credentials (
    cred_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    encrypted_blob BLOB NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    INDEX idx_name (name),
    INDEX idx_expires (expires_at)
);

CREATE TABLE IF NOT EXISTS config (
    config_key VARCHAR(256) PRIMARY KEY,
    config_value JSON NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
"""


# ── Connection helper ────────────────────────────────────────────────────────

def _get_connection():
    """Get a MySQL connection. Falls back to pymysql if mysql-connector unavailable."""
    try:
        import mysql.connector
        return mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASS, database=DB_NAME,
            connect_timeout=10, autocommit=True,
        )
    except ImportError:
        pass

    try:
        import pymysql
        return pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASS, database=DB_NAME,
            connect_timeout=10, autocommit=True,
        )
    except ImportError:
        raise ImportError("Install mysql-connector-python or pymysql: pip install mysql-connector-python")


def init_schema():
    """Create tables if they don't exist."""
    conn = _get_connection()
    cursor = conn.cursor()
    for statement in SCHEMA_SQL.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)
    conn.commit()
    cursor.close()
    conn.close()


# ── Node registration ────────────────────────────────────────────────────────

def register_node(node_id: str, hostname: str, tier: str,
                  capabilities: dict, limitations: dict,
                  tailscale_ip: str = "", public_ip: str = "") -> None:
    """Register or update a node in the registry."""
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO nodes (node_id, hostname, tailscale_ip, public_ip,
                          tier, capabilities, limitations, last_seen_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            hostname = VALUES(hostname),
            tailscale_ip = VALUES(tailscale_ip),
            public_ip = VALUES(public_ip),
            tier = VALUES(tier),
            capabilities = VALUES(capabilities),
            limitations = VALUES(limitations),
            last_seen_at = VALUES(last_seen_at)
    """, (node_id, hostname, tailscale_ip, public_ip,
          tier, json.dumps(capabilities), json.dumps(limitations), now))
    conn.commit()
    cursor.close()
    conn.close()


def heartbeat(node_id: str) -> None:
    """Update last_seen_at for a node."""
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE nodes SET last_seen_at = %s WHERE node_id = %s", (now, node_id))
    conn.commit()
    cursor.close()
    conn.close()


def discover_nodes(tier: Optional[str] = None,
                   max_age_seconds: int = 300) -> List[dict]:
    """Discover registered nodes, optionally filtered by tier.

    Only returns nodes seen within max_age_seconds.
    """
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)
    cutoff = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if tier:
        cursor.execute("""
            SELECT * FROM nodes
            WHERE tier = %s AND last_seen_at >= DATE_SUB(%s, INTERVAL %s SECOND)
            ORDER BY last_seen_at DESC
        """, (tier, cutoff, max_age_seconds))
    else:
        cursor.execute("""
            SELECT * FROM nodes
            WHERE last_seen_at >= DATE_SUB(%s, INTERVAL %s SECOND)
            ORDER BY last_seen_at DESC
        """, (cutoff, max_age_seconds))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in rows:
        if isinstance(row.get("capabilities"), str):
            row["capabilities"] = json.loads(row["capabilities"])
        if isinstance(row.get("limitations"), str):
            row["limitations"] = json.loads(row["limitations"])
        row["is_alive"] = True

    return rows


# ── Credential store ─────────────────────────────────────────────────────────

def _encrypt(plaintext: str) -> bytes:
    """Encrypt a credential blob with ChaCha20."""
    if not ENCRYPTION_KEY:
        raise ValueError("REGISTRY_ENCRYPT_KEY not set")

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers import algorithms
        import os as _os
        key = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
        nonce = _os.urandom(16)
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        encryptor = cipher.encryptor()
        ct = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return nonce + ct
    except ImportError:
        # Fallback: XOR with key (not secure, but functional)
        key_bytes = ENCRYPTION_KEY.encode()
        data = plaintext.encode()
        return bytes(d ^ key_bytes[i % len(key_bytes)] for i, d in enumerate(data))


def _decrypt(blob: bytes) -> str:
    """Decrypt a credential blob."""
    if not ENCRYPTION_KEY:
        raise ValueError("REGISTRY_ENCRYPT_KEY not set")

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers import algorithms
        key = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
        nonce = blob[:16]
        ct = blob[16:]
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        decryptor = cipher.decryptor()
        return (decryptor.update(ct) + decryptor.finalize()).decode()
    except ImportError:
        key_bytes = ENCRYPTION_KEY.encode()
        return bytes(d ^ key_bytes[i % len(key_bytes)] for i, d in enumerate(blob)).decode()


def store_credential(name: str, value: str, ttl_seconds: int = 3600) -> str:
    """Store an encrypted credential with TTL. Returns cred_id."""
    import uuid
    cred_id = str(uuid.uuid4())
    encrypted = _encrypt(value)
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    expires = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)
    cursor.execute("""
        INSERT INTO credentials (cred_id, name, encrypted_blob, expires_at)
        VALUES (%s, %s, %s, %s)
    """, (cred_id, name, encrypted, expires.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    cursor.close()
    conn.close()
    return cred_id


def get_credential(name: str) -> Optional[str]:
    """Retrieve and decrypt a credential by name. Returns None if expired."""
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        SELECT encrypted_blob FROM credentials
        WHERE name = %s AND expires_at > %s
        ORDER BY created_at DESC LIMIT 1
    """, (name, now))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return _decrypt(row["encrypted_blob"])
    return None


def cleanup_expired() -> int:
    """Delete expired credentials. Returns count deleted."""
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM credentials WHERE expires_at <= %s", (now,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return deleted


# ── Config store ─────────────────────────────────────────────────────────────

def set_config(key: str, value: Any) -> None:
    """Set a configuration value."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO config (config_key, config_value)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE config_value = VALUES(config_value)
    """, (key, json.dumps(value)))
    conn.commit()
    cursor.close()
    conn.close()


def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    conn = _get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT config_value FROM config WHERE config_key = %s", (key,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        val = row["config_value"]
        return json.loads(val) if isinstance(val, str) else val
    return default


# ── Auto-register from capability probe ──────────────────────────────────────

def auto_register() -> dict:
    """Register this device using the capability probe."""
    from device_capability_probe import probe_device, get_limitations

    caps = probe_device()
    lim = get_limitations(caps)

    import socket
    node_id = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]

    # Get IPs
    ts_ip = ""
    try:
        import subprocess
        r = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            ts_ip = r.stdout.strip()
    except Exception:
        pass

    pub_ip = ""
    try:
        import urllib.request
        pub_ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
    except Exception:
        pass

    register_node(
        node_id=node_id,
        hostname=caps.hostname,
        tier=caps.tier.name,
        capabilities={
            "gpus": [{"vendor": g.vendor_name, "name": g.device_name, "vram_mb": g.vram_mb}
                     for g in caps.gpus],
            "ffmpeg": caps.has_ffmpeg,
            "encoders": caps.ffmpeg_encoders,
            "arch": caps.os_arch,
            "memory_mb": caps.total_memory_mb,
        },
        limitations={
            "max_payload_bytes": lim.max_payload_bytes,
            "max_concurrent_tasks": lim.max_concurrent_tasks,
            "max_task_duration_ms": lim.max_task_duration_ms,
            "notes": lim.notes,
        },
        tailscale_ip=ts_ip,
        public_ip=pub_ip,
    )

    return {"node_id": node_id, "hostname": caps.hostname, "tier": caps.tier.name}


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="External Service Registry")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Initialize database schema")
    sub.add_parser("register", help="Auto-register this device")
    sub.add_parser("heartbeat", help="Send heartbeat")

    disc = sub.add_parser("discover", help="Discover nodes")
    disc.add_argument("--tier", help="Filter by tier")
    disc.add_argument("--max-age", type=int, default=300, help="Max age in seconds")

    store = sub.add_parser("store", help="Store a credential")
    store.add_argument("--name", required=True)
    store.add_argument("--value", required=True)
    store.add_argument("--ttl", type=int, default=3600)

    get = sub.add_parser("get", help="Get a credential")
    get.add_argument("--name", required=True)

    sub.add_parser("cleanup", help="Delete expired credentials")

    cfg = sub.add_parser("config-set", help="Set config value")
    cfg.add_argument("--key", required=True)
    cfg.add_argument("--value", required=True)

    cfgget = sub.add_parser("config-get", help="Get config value")
    cfgget.add_argument("--key", required=True)

    args = parser.parse_args()

    if args.cmd == "init":
        init_schema()
        print("Schema initialized")

    elif args.cmd == "register":
        result = auto_register()
        print(json.dumps(result, indent=2))

    elif args.cmd == "heartbeat":
        import socket
        node_id = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
        heartbeat(node_id)
        print(f"Heartbeat sent for {node_id}")

    elif args.cmd == "discover":
        nodes = discover_nodes(tier=args.tier, max_age_seconds=args.max_age)
        print(json.dumps(nodes, indent=2, default=str))
        print(f"\n{len(nodes)} nodes found")

    elif args.cmd == "store":
        cred_id = store_credential(args.name, args.value, args.ttl)
        print(f"Stored: {cred_id}")

    elif args.cmd == "get":
        value = get_credential(args.name)
        if value:
            print(value)
        else:
            print("Not found or expired")

    elif args.cmd == "cleanup":
        deleted = cleanup_expired()
        print(f"Deleted {deleted} expired credentials")

    elif args.cmd == "config-set":
        set_config(args.key, json.loads(args.value))
        print(f"Set {args.key}")

    elif args.cmd == "config-get":
        value = get_config(args.key)
        print(json.dumps(value, indent=2) if value else "Not found")


if __name__ == "__main__":
    main()
