#!/usr/bin/env python3
"""
Swarm Surface — OpenAPI compute substrate for the Tailscale mesh.
Zero-dependency: uses only Python stdlib (http.server, sqlite3, json).

Sync model:
- All nodes pull from peers they can reach (pull loop).
- All nodes push recent manifest entries to peers they can reach (push loop).
- JSON-L ingestion endpoint unifies Notion/Linear/ENE/RGFlow into ENE substrate.
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import URLError

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(os.environ.get("RESEARCH_STACK", "/home/allaun/Documents/Research Stack"))
ENE_DB = Path(os.environ.get("ENE_DB", str(PROJECT_ROOT / "data" / "substrate_index.db")))
LOCAL_PORT = int(os.environ.get("SWARM_PORT", "3001"))
SYNC_INTERVAL = int(os.environ.get("SWARM_SYNC_INTERVAL", "30"))
TOPO_INTERVAL = int(os.environ.get("SWARM_TOPO_INTERVAL", "60"))
PUSH_BATCH = int(os.environ.get("SWARM_PUSH_BATCH", "100"))
SRAM_SIZE = int(os.environ.get("SWARM_SRAM_SIZE", "1024"))

TAILSCALE_PEERS = [
    {"hostname": "qfox",              "ip": "100.105.111.120", "tags": []},
    {"hostname": "architect",         "ip": "100.127.111.7",   "tags": ["tag:family-server"]},
    {"hostname": "judge",             "ip": "100.111.192.47",  "tags": ["tag:work"]},
    {"hostname": "netcup-router",     "ip": "100.85.1.50",     "tags": []},
    {"hostname": "FoxTop",            "ip": "100.88.220.123",  "tags": ["tag:family-server"]},
    {"hostname": "ip-172-31-25-81",   "ip": "100.110.117.19",  "tags": []},
    {"hostname": "racknerd-510bd9c",  "ip": "100.103.54.58",   "tags": []},
]

# ---------------------------------------------------------------------------
# ENE Helpers
# ---------------------------------------------------------------------------

def _conn():
    ENE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ENE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS swarm_nodes (
            hostname TEXT PRIMARY KEY,
            tailscale_ip TEXT NOT NULL,
            role TEXT DEFAULT 'worker',
            status TEXT DEFAULT 'unknown',
            os TEXT,
            capabilities TEXT,
            latency_ms REAL,
            last_seen INTEGER,
            load REAL DEFAULT 0.0
        );
        CREATE TABLE IF NOT EXISTS swarm_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            t REAL NOT NULL,
            chain TEXT NOT NULL,
            height INTEGER NOT NULL,
            block_hash TEXT NOT NULL,
            address INTEGER NOT NULL,
            bucket INTEGER NOT NULL,
            genome TEXT NOT NULL,
            node TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_manifest_chain_height ON swarm_manifest(chain, height);
        CREATE INDEX IF NOT EXISTS idx_manifest_address ON swarm_manifest(address);
        CREATE TABLE IF NOT EXISTS swarm_work_queue (
            task_id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            chain TEXT NOT NULL,
            block_hash TEXT NOT NULL,
            payload TEXT NOT NULL,
            assigned_node TEXT,
            status TEXT DEFAULT 'pending',
            created_at INTEGER,
            started_at INTEGER,
            completed_at INTEGER,
            result TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_queue_status ON swarm_work_queue(status, task_type);
        CREATE TABLE IF NOT EXISTS swarm_sram (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT NOT NULL,
            t REAL NOT NULL,
            src TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_json TEXT NOT NULL,
            semantic_vector TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            ttl INTEGER NOT NULL
        );
    """)
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_manifest_unique ON swarm_manifest(chain, height)")
    except sqlite3.IntegrityError:
        conn.execute("DELETE FROM swarm_manifest WHERE id NOT IN (SELECT MIN(id) FROM swarm_manifest GROUP BY chain, height)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_manifest_unique ON swarm_manifest(chain, height)")
    conn.commit()
    conn.close()


def _http_probe(ip: str, port: int = LOCAL_PORT) -> Optional[float]:
    t0 = time.time()
    try:
        with urlopen(f"http://{ip}:{port}/health", timeout=3) as resp:
            if resp.status == 200:
                return (time.time() - t0) * 1000.0
    except Exception:
        pass
    return None


def _probe_node(hostname: str, ip: str) -> Dict[str, Any]:
    latency = _http_probe(ip)
    return {
        "hostname": hostname,
        "tailscale_ip": ip,
        "latency_ms": latency,
        "status": "active" if latency is not None else "offline",
    }


def _refresh_topology():
    conn = _conn()
    for peer in TAILSCALE_PEERS:
        info = _probe_node(peer["hostname"], peer["ip"])
        conn.execute(
            """INSERT INTO swarm_nodes (hostname, tailscale_ip, status, last_seen, latency_ms)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(hostname) DO UPDATE SET
                   status=excluded.status,
                   last_seen=excluded.last_seen,
                   latency_ms=excluded.latency_ms""",
            (info["hostname"], info["tailscale_ip"], info["status"],
             int(time.time()), info["latency_ms"])
        )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# JSON-L Ingestion
# ---------------------------------------------------------------------------

def _genome_to_address(genome: Dict[str, int]) -> int:
    return ((genome.get("mu", 0) & 0x7) << 15) | \
           ((genome.get("rho", 0) & 0x7) << 12) | \
           ((genome.get("c", 0) & 0x7) << 9) | \
           ((genome.get("m", 0) & 0x7) << 6) | \
           ((genome.get("ne", 0) & 0x7) << 3) | \
           (genome.get("sig", 0) & 0x7)


def _ingest_jsonl(event: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest a canonical JSON-L event into ENE. Returns summary."""
    src = event.get("src", "unknown")
    op = event.get("op", "upsert")
    data = event.get("data", {})
    genome = event.get("genome")
    provenance = event.get("provenance", {})
    t = event.get("t", time.time())
    event_id = event.get("id", f"unknown:{t}")

    # Write to SRAM scaffolding buffer
    sem_vec = genome if genome else data.get("concept_vector", [0.0] * 14)
    sem_vec_str = json.dumps(sem_vec)
    query_hash = hashlib.sha256(f"{event_id}:{t}".encode()).hexdigest()[:32]

    conn = _conn()
    conn.execute(
        """INSERT INTO swarm_sram (query_hash, t, src, event_id, event_json, semantic_vector, created_at, ttl)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (query_hash, t, src, event_id, json.dumps(event), sem_vec_str, int(time.time()), 86400)
    )
    # Trim SRAM to circular buffer size
    conn.execute(
        "DELETE FROM swarm_sram WHERE seq <= (SELECT MAX(seq) FROM swarm_sram) - ?",
        (SRAM_SIZE,)
    )

    result = {"src": src, "id": event_id, "inserted": False, "table": None}

    if src == "rgflow":
        chain = data.get("chain", "?")
        height = data.get("height", 0)
        block_hash = data.get("block_hash", "?")
        addr = data.get("address", _genome_to_address(genome) if genome else 0)
        bucket = data.get("bucket", addr >> 15)
        node = provenance.get("node", "unknown")
        try:
            conn.execute(
                """INSERT OR IGNORE INTO swarm_manifest (t, chain, height, block_hash, address, bucket, genome, node)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (t, chain, height, block_hash, addr, bucket, json.dumps(genome) if genome else "{}", node)
            )
            result["inserted"] = True
            result["table"] = "swarm_manifest"
        except sqlite3.IntegrityError:
            pass

    elif src in ("notion", "linear", "ene"):
        # Map to packages table
        if src == "notion":
            pkg = f"notion/{data.get('page_id', event_id)}"
            archetype = "document"
            tier = "RESEARCH"
            concept_anchor = json.dumps({"domain": "knowledge", "concept": data.get("title", "")[:50], "resolution": data.get("property_changes", {}).get("Status", {}).get("new", "SEED")})
        elif src == "linear":
            pkg = f"linear/{data.get('issue_id', event_id)}"
            archetype = "issue"
            tier = "RESEARCH"
            resolution_map = {"Todo": "SEED", "In Progress": "FORMING", "Done": "STABLE", "Canceled": "RECOVERED"}
            state_new = data.get("state", {}).get("new", "")
            concept_anchor = json.dumps({"domain": "planning", "concept": data.get("title", "")[:50], "resolution": resolution_map.get(state_new, "SEED")})
        else:  # ene
            pkg = data.get("pkg", event_id)
            archetype = data.get("archetype", "unknown")
            tier = data.get("tier", "RESEARCH")
            concept_anchor = json.dumps(data.get("concept_anchor", {}))

        version = data.get("version", "0.0.0")
        domain = data.get("domain", "general")
        description = data.get("title", data.get("description", ""))[:200]
        tags = json.dumps(data.get("tags", []))
        files = json.dumps(data.get("files", []))
        depends = json.dumps(data.get("depends", []))
        concept_vector = json.dumps(data.get("concept_vector", []))
        idea_weights = json.dumps(data.get("idea_weights", {}))
        analog_map = json.dumps(data.get("analog_map", {}))
        sha256_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        try:
            conn.execute(
                """INSERT INTO packages (pkg, version, tier, domain, archetype, description, tags, source, sha256, indexed_utc, concept_anchor, concept_vector, idea_weights, analog_map)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(pkg, version) DO UPDATE SET
                       description=excluded.description,
                       tags=excluded.tags,
                       sha256=excluded.sha256,
                       indexed_utc=excluded.indexed_utc,
                       concept_anchor=excluded.concept_anchor,
                       concept_vector=excluded.concept_vector,
                       idea_weights=excluded.idea_weights,
                       analog_map=excluded.analog_map""",
                (pkg, version, tier, domain, archetype, description, tags, src, sha256_hash,
                 time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), concept_anchor, concept_vector, idea_weights, analog_map)
            )
            result["inserted"] = True
            result["table"] = "packages"
        except Exception as e:
            result["error"] = str(e)

    elif src == "swarm":
        event_type = data.get("event_type", "unknown")
        if event_type == "topology_change":
            hostname = data.get("hostname", "unknown")
            tailscale_ip = data.get("tailscale_ip", "")
            status = data.get("status", "unknown")
            latency_ms = data.get("latency_ms")
            load = data.get("load", 0.0)
            conn.execute(
                """INSERT INTO swarm_nodes (hostname, tailscale_ip, status, last_seen, latency_ms, load)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(hostname) DO UPDATE SET
                       status=excluded.status,
                       last_seen=excluded.last_seen,
                       latency_ms=excluded.latency_ms,
                       load=excluded.load""",
                (hostname, tailscale_ip, status, int(time.time()), latency_ms, load)
            )
            result["inserted"] = True
            result["table"] = "swarm_nodes"

    conn.commit()
    conn.close()
    return result


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def _sync_from_peer(ip: str, port: int = LOCAL_PORT) -> Dict[str, Any]:
    results = {"manifest_inserted": 0, "topology_updated": 0}
    try:
        with urlopen(f"http://{ip}:{port}/manifest?limit=1000", timeout=5) as resp:
            entries = json.loads(resp.read().decode())
            if entries:
                conn = _conn()
                inserted = 0
                for e in entries:
                    try:
                        conn.execute(
                            """INSERT OR IGNORE INTO swarm_manifest (t, chain, height, block_hash, address, bucket, genome, node)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (e.get("t"), e.get("chain"), e.get("height"), e.get("block_hash"),
                             e.get("address"), e.get("bucket"), json.dumps(e.get("genome")), e.get("node"))
                        )
                        inserted += 1
                    except sqlite3.IntegrityError:
                        pass
                conn.commit()
                conn.close()
                results["manifest_inserted"] = inserted
    except Exception:
        pass

    try:
        with urlopen(f"http://{ip}:{port}/topology", timeout=5) as resp:
            peers = json.loads(resp.read().decode())
            conn = _conn()
            for p in peers:
                conn.execute(
                    """INSERT INTO swarm_nodes (hostname, tailscale_ip, status, last_seen, latency_ms)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(hostname) DO UPDATE SET
                           status=excluded.status,
                           last_seen=excluded.last_seen,
                           latency_ms=excluded.latency_ms""",
                    (p["hostname"], p["tailscale_ip"], p.get("status", "unknown"),
                     int(time.time()), p.get("latency_ms"))
                )
            conn.commit()
            conn.close()
            results["topology_updated"] = len(peers)
    except Exception:
        pass

    return results


def _push_to_peer(ip: str, port: int = LOCAL_PORT) -> int:
    try:
        conn = _conn()
        rows = conn.execute(
            "SELECT * FROM swarm_manifest ORDER BY t DESC LIMIT ?",
            (PUSH_BATCH,)
        ).fetchall()
        conn.close()
        if not rows:
            return 0
        entries = [
            {
                "t": r["t"], "chain": r["chain"], "height": r["height"],
                "block_hash": r["block_hash"], "address": r["address"],
                "bucket": r["bucket"], "genome": json.loads(r["genome"]),
                "node": r["node"],
            }
            for r in rows
        ]
        data = json.dumps(entries).encode()
        req = Request(f"http://{ip}:{port}/sync/manifest", data=data,
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("inserted", 0)
    except Exception:
        return 0


def _pull_loop():
    while True:
        time.sleep(SYNC_INTERVAL)
        try:
            conn = _conn()
            peers = conn.execute("SELECT tailscale_ip FROM swarm_nodes WHERE status='active'").fetchall()
            conn.close()
            for row in peers:
                _sync_from_peer(row["tailscale_ip"])
        except Exception:
            pass


def _push_loop():
    while True:
        time.sleep(SYNC_INTERVAL)
        try:
            conn = _conn()
            peers = conn.execute("SELECT tailscale_ip FROM swarm_nodes WHERE status='active'").fetchall()
            conn.close()
            for row in peers:
                _push_to_peer(row["tailscale_ip"])
        except Exception:
            pass


def _topo_loop():
    time.sleep(5)
    while True:
        try:
            _refresh_topology()
        except Exception:
            pass
        time.sleep(TOPO_INTERVAL)


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class SurfaceHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json_response(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        return json.loads(body) if body else {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            conn = _conn()
            active = conn.execute("SELECT COUNT(*) FROM swarm_nodes WHERE status='active'").fetchone()[0]
            manifest = conn.execute("SELECT COUNT(*) FROM swarm_manifest").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM swarm_work_queue WHERE status='pending'").fetchone()[0]
            sram = conn.execute("SELECT COUNT(*) FROM swarm_sram").fetchone()[0]
            conn.close()
            self._json_response({
                "status": "ok", "surface": "swarm",
                "active_nodes": active, "manifest_entries": manifest,
                "pending_tasks": pending, "sram_events": sram,
                "time": time.time(),
            })

        elif path == "/topology":
            conn = _conn()
            rows = conn.execute("SELECT * FROM swarm_nodes ORDER BY latency_ms ASC").fetchall()
            conn.close()
            self._json_response([
                {
                    "hostname": r["hostname"], "tailscale_ip": r["tailscale_ip"],
                    "role": r["role"], "status": r["status"],
                    "latency_ms": r["latency_ms"], "load": r["load"],
                    "capabilities": json.loads(r["capabilities"]) if r["capabilities"] else None,
                }
                for r in rows
            ])

        elif path == "/manifest":
            chain = qs.get("chain", [None])[0]
            limit = int(qs.get("limit", ["1000"])[0])
            conn = _conn()
            if chain:
                rows = conn.execute(
                    "SELECT * FROM swarm_manifest WHERE chain=? ORDER BY t DESC LIMIT ?",
                    (chain, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM swarm_manifest ORDER BY t DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            conn.close()
            self._json_response([
                {
                    "t": r["t"], "chain": r["chain"], "height": r["height"],
                    "block_hash": r["block_hash"], "address": r["address"],
                    "bucket": r["bucket"], "genome": json.loads(r["genome"]),
                    "node": r["node"],
                }
                for r in rows
            ])

        elif path == "/sram":
            limit = int(qs.get("limit", ["100"])[0])
            conn = _conn()
            rows = conn.execute(
                "SELECT t, src, event_id, semantic_vector FROM swarm_sram ORDER BY seq DESC LIMIT ?",
                (limit,)
            ).fetchall()
            conn.close()
            self._json_response([
                {"t": r["t"], "src": r["src"], "id": r["event_id"], "semantic_vector": json.loads(r["semantic_vector"])}
                for r in rows
            ])

        else:
            self._json_response({"detail": "Not Found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/compute/rgflow":
            req = self._read_json()
            task_id = f"rgflow-{req.get('chain','?')}-{req.get('height',0)}-{int(time.time()*1000)}"
            conn = _conn()
            conn.execute(
                """INSERT INTO swarm_work_queue
                   (task_id, task_type, chain, block_hash, payload, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (task_id, "rgflow_compress", req.get("chain"), req.get("block_hash"),
                 json.dumps(req), "pending", int(time.time()))
            )
            row = conn.execute(
                "SELECT hostname FROM swarm_nodes WHERE status='active' ORDER BY latency_ms ASC LIMIT 1"
            ).fetchone()
            assigned = row["hostname"] if row else None
            if assigned:
                conn.execute(
                    "UPDATE swarm_work_queue SET assigned_node=?, status='running', started_at=? WHERE task_id=?",
                    (assigned, int(time.time()), task_id)
                )
            conn.commit()
            conn.close()
            self._json_response({
                "task_id": task_id, "status": "running" if assigned else "pending",
                "assigned_node": assigned,
            })

        elif path == "/sync/manifest":
            entries = self._read_json()
            conn = _conn()
            inserted = 0
            for e in entries:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO swarm_manifest (t, chain, height, block_hash, address, bucket, genome, node)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (e.get("t"), e.get("chain"), e.get("height"), e.get("block_hash"),
                         e.get("address"), e.get("bucket"), json.dumps(e.get("genome")), e.get("node"))
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
            conn.close()
            self._json_response({"inserted": inserted})

        elif path == "/ingest/jsonl":
            events = self._read_json()
            if not isinstance(events, list):
                events = [events]
            results = []
            for event in events:
                try:
                    results.append(_ingest_jsonl(event))
                except Exception as e:
                    results.append({"error": str(e), "event_id": event.get("id", "unknown")})
            self._json_response({"ingested": len(results), "results": results})

        else:
            self._json_response({"detail": "Not Found"}, 404)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_server(host: str = "0.0.0.0", port: int = LOCAL_PORT):
    _ensure_tables()
    threading.Thread(target=_topo_loop, daemon=True).start()
    threading.Thread(target=_pull_loop, daemon=True).start()
    threading.Thread(target=_push_loop, daemon=True).start()
    server = ThreadingHTTPServer((host, port), SurfaceHandler)
    server.socket.settimeout(5)
    print(f"[SWARM-SURFACE] Listening on {host}:{port}")
    print(f"[SWARM-SURFACE] ENE_DB={ENE_DB}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SWARM-SURFACE] Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    run_server()
