"""RDS-backed ENEFractalFold — drop-in replacement for SQLite ENEFractalFold.

API-compatible with ene_fractal_fold.ENEFractalFold: same dataclasses, same
handle_request() protocol, but backed by PostgreSQL via psycopg2.

Constructor:
  ENERDSFractalFold(dsn="postgresql://user:pass@host:5432/dbname")

The DSN defaults to the RDS_HOST / RDS_PORT / RDS_USER / RDS_PASSWORD / RDS_DB
environment variables.
"""

from __future__ import annotations

import base64
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

from infra.ene_fractal_fold import (
    FractalNode,
    FractalManifest,
    VERSION,
    GOLDEN_ANGLE,
    canonical_json,
    sha256_text,
    sha256_bytes,
    gray_code,
    inverse_gray_code,
    golden_spiral_point,
    manifold_distance,
    tree_depth,
    make_leaf,
    make_parent,
    encode_fractal,
    encode_fractal_chunks,
    parse_graphml_concepts,
    node_record,
    archive_record,
    jsonl_event,
)


import os


def _default_dsn() -> str:
    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = os.environ.get("RDS_PORT", "5432")
    user = os.environ.get("RDS_USER", "postgres")
    password = os.environ.get("RDS_PASSWORD") or os.environ.get("RDS_IAM_TOKEN", "")
    dbname = os.environ.get("RDS_DB", "postgres")
    return f"host={host} port={port} dbname={dbname} user={user} password={password} sslmode=require"


class ENERDSFractalFold:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or _default_dsn()
        self._init_db()

    def _get_conn(self):
        return psycopg2.connect(self.dsn)

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS ene")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.fractal_manifolds (
                        root_hash TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        byte_len INTEGER NOT NULL,
                        leaves_count INTEGER NOT NULL,
                        depth INTEGER NOT NULL,
                        chunk_size INTEGER NOT NULL,
                        branching_factor INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        receipt TEXT NOT NULL,
                        archive_record JSONB NOT NULL DEFAULT '{}',
                        jsonl_event JSONB NOT NULL DEFAULT '{}'
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.fractal_nodes (
                        root_hash TEXT NOT NULL,
                        node_hash TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        level INTEGER NOT NULL,
                        ordinal INTEGER NOT NULL,
                        fold_address INTEGER NOT NULL,
                        start_leaf INTEGER NOT NULL,
                        end_leaf INTEGER NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        children TEXT NOT NULL,
                        payload_b64 TEXT,
                        PRIMARY KEY (root_hash, node_hash)
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_rds_fractal_leaf
                    ON ene.fractal_nodes (root_hash, level, ordinal)
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.fractal_graph_entities (
                        root_hash TEXT NOT NULL,
                        graph_node_id TEXT NOT NULL,
                        leaf_index INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        family TEXT,
                        domain TEXT,
                        neighbors TEXT NOT NULL,
                        PRIMARY KEY (root_hash, graph_node_id)
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_rds_fractal_graph_name
                    ON ene.fractal_graph_entities (root_hash, name)
                """)
            conn.commit()

    def _store(self, manifest: FractalManifest, nodes: list[FractalNode]) -> tuple[dict[str, Any], dict[str, Any]]:
        record = archive_record(manifest)
        event = jsonl_event(record, manifest)
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ene.fractal_manifolds
                    (root_hash, name, byte_len, leaves_count, depth, chunk_size, branching_factor,
                     created_at, receipt, archive_record, jsonl_event)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (root_hash) DO UPDATE SET
                        name = EXCLUDED.name,
                        byte_len = EXCLUDED.byte_len,
                        leaves_count = EXCLUDED.leaves_count,
                        depth = EXCLUDED.depth,
                        chunk_size = EXCLUDED.chunk_size,
                        branching_factor = EXCLUDED.branching_factor,
                        receipt = EXCLUDED.receipt,
                        archive_record = EXCLUDED.archive_record,
                        jsonl_event = EXCLUDED.jsonl_event
                """, (
                    manifest.root_hash, manifest.name, manifest.byte_len,
                    manifest.leaves_count, manifest.depth, manifest.chunk_size,
                    manifest.branching_factor, manifest.created_at, manifest.receipt,
                    json.dumps(record, sort_keys=True), json.dumps(event, sort_keys=True),
                ))

                cur.execute("DELETE FROM ene.fractal_nodes WHERE root_hash = %s", (manifest.root_hash,))
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO ene.fractal_nodes
                    (root_hash, node_hash, kind, level, ordinal, fold_address, start_leaf,
                     end_leaf, size_bytes, children, payload_b64)
                    VALUES %s
                    """,
                    [
                        (
                            manifest.root_hash, node.node_hash, node.kind, node.level,
                            node.ordinal, node.fold_address, node.start_leaf, node.end_leaf,
                            node.size_bytes, canonical_json(node.children), node.payload_b64,
                        )
                        for node in nodes
                    ],
                )
            conn.commit()
        return record, event

    def put(self, data: bytes, name: str = "unnamed", chunk_size: int = 4096, branching_factor: int = 4) -> dict[str, Any]:
        manifest, nodes = encode_fractal(data, name, chunk_size, branching_factor)
        record, event = self._store(manifest, nodes)
        return {
            "ok": True, "op": "fractal_put",
            "manifest": asdict(manifest),
            "archive_record": record,
            "jsonl_event": event,
        }

    def put_graphml(self, graphml: bytes, name: str = "graphml", branching_factor: int = 4) -> dict[str, Any]:
        records, chunks = parse_graphml_concepts(graphml)
        max_chunk = max((len(chunk) for chunk in chunks), default=0)
        manifest, nodes = encode_fractal_chunks(chunks, name, max_chunk, branching_factor)
        record, event = self._store(manifest, nodes)
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ene.fractal_graph_entities WHERE root_hash = %s", (manifest.root_hash,))
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO ene.fractal_graph_entities
                    (root_hash, graph_node_id, leaf_index, name, family, domain, neighbors)
                    VALUES %s
                    """,
                    [
                        (
                            manifest.root_hash, concept["graph_node_id"],
                            concept["leaf_index"], concept["name"],
                            concept["family"], concept["domain"],
                            canonical_json(concept["neighbors"]),
                        )
                        for concept in records
                    ],
                )
            conn.commit()
        return {
            "ok": True, "op": "fractal_graphml_put",
            "manifest": asdict(manifest),
            "graphml": {"concepts": len(records), "concept_leaf_mode": True},
            "archive_record": record,
            "jsonl_event": event,
        }

    def manifest(self, root_hash: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM ene.fractal_manifolds WHERE root_hash = %s", (root_hash,))
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "root_hash": row["root_hash"],
            "name": row["name"],
            "byte_len": row["byte_len"],
            "leaves_count": row["leaves_count"],
            "depth": row["depth"],
            "chunk_size": row["chunk_size"],
            "branching_factor": row["branching_factor"],
            "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
            "receipt": row["receipt"],
            "archive_record": row["archive_record"] if isinstance(row["archive_record"], dict) else json.loads(row["archive_record"] or "{}"),
            "jsonl_event": row["jsonl_event"] if isinstance(row["jsonl_event"], dict) else json.loads(row["jsonl_event"] or "{}"),
        }

    def _node(self, cur, root_hash: str, node_hash: str) -> dict[str, Any]:
        cur.execute(
            "SELECT * FROM ene.fractal_nodes WHERE root_hash = %s AND node_hash = %s",
            (root_hash, node_hash),
        )
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"missing fractal node {node_hash}")
        return dict(row)

    def proof(self, root_hash: str, leaf_index: int) -> dict[str, Any]:
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        if leaf_index < 0 or leaf_index >= meta["leaves_count"]:
            raise IndexError("leaf_index outside manifold")

        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                frontier = root_hash
                path = []
                target_point = golden_spiral_point(gray_code(leaf_index), 0)
                while True:
                    row = self._node(cur, root_hash, frontier)
                    children = json.loads(row["children"])
                    node_point = golden_spiral_point(row["fold_address"], row["level"])
                    entry = {k: v for k, v in dict(row).items() if k != "payload_b64"}
                    entry["children"] = children
                    entry["golden_spiral"] = node_point
                    entry["distance_to_target"] = round(manifold_distance(node_point, target_point), 9)
                    path.append(entry)

                    if row["kind"] == "leaf":
                        payload = base64.b64decode(row["payload_b64"] or "")
                        break

                    next_hash = None
                    pruned = []
                    for child_hash in children:
                        child = self._node(cur, root_hash, child_hash)
                        child_point = golden_spiral_point(child["fold_address"], child["level"])
                        pruned.append({
                            "node_hash": child_hash,
                            "covers_target": child["start_leaf"] <= leaf_index <= child["end_leaf"],
                            "distance": round(manifold_distance(child_point, target_point), 9),
                        })
                        if child["start_leaf"] <= leaf_index <= child["end_leaf"]:
                            next_hash = child_hash
                    path[-1]["manifold_distance_pruning"] = sorted(pruned, key=lambda item: item["distance"])
                    if next_hash is None:
                        raise ValueError("corrupt tree: no child covers requested leaf")
                    frontier = next_hash

        path_valid = self._verify_path_rows(path, payload)
        return {
            "ok": True, "op": "fractal_proof",
            "root_hash": root_hash, "leaf_index": leaf_index,
            "fold_address": gray_code(leaf_index),
            "inverse_fold_address": inverse_gray_code(gray_code(leaf_index)),
            "golden_spiral": golden_spiral_point(gray_code(leaf_index), 0),
            "traversal_cost": len(path),
            "expected_complexity": f"O(log_{meta['branching_factor']}(n))",
            "path_hash_verified": path_valid,
            "path": path,
            "payload_b64": base64.b64encode(payload).decode("ascii"),
        }

    def _verify_path_rows(self, path: list[dict[str, Any]], payload: bytes) -> bool:
        if not path:
            return False
        leaf = path[-1]
        if leaf["kind"] != "leaf":
            return False
        expected_leaf = make_leaf(payload, leaf["ordinal"]).node_hash
        if expected_leaf != leaf["node_hash"]:
            return False
        child_hash = expected_leaf
        for row in reversed(path[:-1]):
            if child_hash not in row["children"]:
                return False
            child_hash = row["node_hash"]
        return child_hash == path[0]["node_hash"]

    def verify(self, root_hash: str) -> dict[str, Any]:
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        errors = []
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM ene.fractal_nodes WHERE root_hash = %s", (root_hash,))
                rows = cur.fetchall()
                by_hash = {r["node_hash"]: r for r in rows}
                for row in rows:
                    children = json.loads(row["children"])
                    if row["kind"] == "leaf":
                        payload = base64.b64decode(row["payload_b64"] or "")
                        expected = make_leaf(payload, row["ordinal"]).node_hash
                        if expected != row["node_hash"]:
                            errors.append({"node": row["node_hash"], "error": "leaf_hash_mismatch", "expected": expected})
                        continue
                    child_nodes = []
                    for child_hash in children:
                        child = by_hash.get(child_hash)
                        if child is None:
                            errors.append({"node": row["node_hash"], "error": "missing_child", "child": child_hash})
                            continue
                        child_nodes.append(FractalNode(
                            node_hash=child["node_hash"], kind=child["kind"],
                            level=child["level"], ordinal=child["ordinal"],
                            fold_address=child["fold_address"],
                            start_leaf=child["start_leaf"], end_leaf=child["end_leaf"],
                            size_bytes=child["size_bytes"],
                            children=json.loads(child["children"]),
                            payload_b64=child["payload_b64"],
                        ))
                    if len(child_nodes) == len(children):
                        expected = make_parent(child_nodes, row["level"], row["ordinal"]).node_hash
                        if expected != row["node_hash"]:
                            errors.append({"node": row["node_hash"], "error": "parent_hash_mismatch", "expected": expected})
        return {
            "ok": not errors, "op": "fractal_verify",
            "root_hash": root_hash, "checked_nodes": len(rows),
            "errors": errors, "damage_detected": bool(errors),
        }

    def neighbors(self, root_hash: str, leaf_index: int) -> dict[str, Any]:
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        candidates = sorted(set(idx for idx in (leaf_index - 1, leaf_index, leaf_index + 1) if 0 <= idx < meta["leaves_count"]))
        return {
            "ok": True, "op": "fractal_neighbors",
            "root_hash": root_hash, "leaf_index": leaf_index,
            "fold_address": gray_code(leaf_index),
            "neighbors": [
                {
                    "leaf_index": idx, "fold_address": gray_code(idx),
                    "golden_spiral": golden_spiral_point(gray_code(idx), 0),
                    "fold_distance": bin(gray_code(idx) ^ gray_code(leaf_index)).count("1"),
                }
                for idx in candidates
            ],
        }

    def graph_entity(self, root_hash: str, graph_node_id: str = "", name: str = "") -> dict[str, Any]:
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if graph_node_id:
                    cur.execute(
                        "SELECT * FROM ene.fractal_graph_entities WHERE root_hash = %s AND graph_node_id = %s",
                        (root_hash, graph_node_id),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM ene.fractal_graph_entities WHERE root_hash = %s AND lower(name) = lower(%s)",
                        (root_hash, name),
                    )
                row = cur.fetchone()
        if row is None:
            return {"ok": False, "op": "fractal_graph_entity", "error": "graph entity not found"}
        proof = self.navigate(root_hash, row["leaf_index"])
        return {
            "ok": True, "op": "fractal_graph_entity",
            "root_hash": root_hash,
            "entity": {
                "graph_node_id": row["graph_node_id"],
                "leaf_index": row["leaf_index"],
                "name": row["name"],
                "family": row["family"],
                "domain": row["domain"],
                "neighbors": json.loads(row["neighbors"]),
            },
            "retrieval": proof,
        }

    def graph_neighbors(self, root_hash: str, graph_node_id: str) -> dict[str, Any]:
        entity = self.graph_entity(root_hash, graph_node_id=graph_node_id)
        if not entity.get("ok"):
            return entity
        neighbor_ids = entity["entity"]["neighbors"]
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                rows = []
                for nid in neighbor_ids:
                    cur.execute(
                        "SELECT * FROM ene.fractal_graph_entities WHERE root_hash = %s AND graph_node_id = %s",
                        (root_hash, nid),
                    )
                    row = cur.fetchone()
                    if row is not None:
                        rows.append(row)
        return {
            "ok": True, "op": "fractal_graph_neighbors",
            "root_hash": root_hash, "graph_node_id": graph_node_id,
            "neighbors": [
                {
                    "graph_node_id": r["graph_node_id"],
                    "leaf_index": r["leaf_index"],
                    "name": r["name"],
                    "family": r["family"],
                    "domain": r["domain"],
                    "fold_address": gray_code(r["leaf_index"]),
                    "golden_spiral": golden_spiral_point(gray_code(r["leaf_index"]), 0),
                }
                for r in rows
            ],
        }

    def navigate(self, root_hash: str, leaf_index: int) -> dict[str, Any]:
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        if leaf_index < 0 or leaf_index >= meta["leaves_count"]:
            raise IndexError("leaf_index outside manifold")

        target_point = golden_spiral_point(gray_code(leaf_index), 0)
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                frontier = root_hash
                path = []
                while True:
                    row = self._node(cur, root_hash, frontier)
                    children = json.loads(row["children"])
                    entry = {
                        "node_hash": row["node_hash"], "kind": row["kind"],
                        "level": row["level"], "ordinal": row["ordinal"],
                        "start_leaf": row["start_leaf"], "end_leaf": row["end_leaf"],
                        "fold_address": row["fold_address"],
                        "children": children,
                        "golden_spiral": golden_spiral_point(row["fold_address"], row["level"]),
                    }
                    path.append(entry)

                    if row["kind"] == "leaf":
                        payload = base64.b64decode(row["payload_b64"] or "")
                        break

                    ranked = []
                    for child_hash in children:
                        child = self._node(cur, root_hash, child_hash)
                        point = golden_spiral_point(child["fold_address"], child["level"])
                        ranked.append({
                            "node_hash": child_hash,
                            "distance": manifold_distance(point, target_point),
                            "covers_target": child["start_leaf"] <= leaf_index <= child["end_leaf"],
                        })
                    ranked.sort(key=lambda item: (not item["covers_target"], item["distance"]))
                    path[-1]["pruned_candidates"] = [
                        {"node_hash": item["node_hash"], "distance": round(item["distance"], 9), "covers_target": item["covers_target"]}
                        for item in ranked
                    ]
                    frontier = ranked[0]["node_hash"]

        return {
            "ok": True, "op": "fractal_navigate",
            "root_hash": root_hash, "leaf_index": leaf_index,
            "target": {"fold_address": gray_code(leaf_index), "golden_spiral": target_point},
            "retrieval_complexity": f"O(log_{meta['branching_factor']}(n))",
            "navigation": "golden_spiral_manifold_distance_pruning",
            "path_hash_verified": self._verify_path_rows(path, payload),
            "path": path,
            "payload_b64": base64.b64encode(payload).decode("ascii"),
        }

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        op = str(request.get("op", "manifest"))
        if op in {"put", "encode"}:
            if "data_b64" in request:
                data = base64.b64decode(str(request["data_b64"]))
            else:
                data = str(request.get("text", "")).encode("utf-8")
            return self.put(
                data=data,
                name=str(request.get("name", "unnamed")),
                chunk_size=int(request.get("chunk_size", 4096)),
                branching_factor=int(request.get("branching_factor", 4)),
            )
        if op in {"put_graphml", "graphml"}:
            if "data_b64" in request:
                data = base64.b64decode(str(request["data_b64"]))
            else:
                data = str(request.get("text", "")).encode("utf-8")
            return self.put_graphml(
                graphml=data,
                name=str(request.get("name", "graphml")),
                branching_factor=int(request.get("branching_factor", 4)),
            )
        root_hash = str(request.get("root_hash", ""))
        if not root_hash:
            raise ValueError("root_hash is required for this operation")
        if op == "manifest":
            meta = self.manifest(root_hash)
            return {"ok": meta is not None, "op": "fractal_manifest", "manifest": meta}
        if op == "proof":
            return self.proof(root_hash, int(request.get("leaf_index", 0)))
        if op in {"navigate", "get"}:
            return self.navigate(root_hash, int(request.get("leaf_index", 0)))
        if op == "verify":
            return self.verify(root_hash)
        if op == "neighbors":
            return self.neighbors(root_hash, int(request.get("leaf_index", 0)))
        if op in {"graph_entity", "concept"}:
            return self.graph_entity(
                root_hash,
                graph_node_id=str(request.get("graph_node_id", "")),
                name=str(request.get("name", "")),
            )
        if op in {"graph_neighbors", "concept_neighbors"}:
            return self.graph_neighbors(root_hash, str(request.get("graph_node_id", "")))
        raise ValueError(f"unsupported fractal op {op!r}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="ENE RDS fractal fold codec")
    parser.add_argument("--dsn", help="PostgreSQL DSN")
    parser.add_argument("--op", default="put")
    parser.add_argument("--name", default="cli")
    parser.add_argument("--text", default="")
    parser.add_argument("--file", type=argparse.FileType("rb"))
    parser.add_argument("--graph-node-id")
    parser.add_argument("--root-hash")
    parser.add_argument("--leaf-index", type=int, default=0)
    parser.add_argument("--chunk-size", type=int, default=4096)
    parser.add_argument("--branching-factor", type=int, default=4)
    args = parser.parse_args()

    layer = ENERDSFractalFold(args.dsn)
    if args.op in {"put", "encode"}:
        data = args.file.read() if args.file else args.text.encode("utf-8")
        result = layer.put(data, args.name, args.chunk_size, args.branching_factor)
    elif args.op in {"put_graphml", "graphml"}:
        data = args.file.read() if args.file else args.text.encode("utf-8")
        result = layer.put_graphml(data, args.name, args.branching_factor)
    elif args.op in {"graph_entity", "concept", "graph_neighbors"}:
        result = layer.handle_request({
            "op": args.op, "root_hash": args.root_hash,
            "leaf_index": args.leaf_index,
            "graph_node_id": args.graph_node_id or "",
            "name": args.name,
        })
    else:
        result = layer.handle_request({
            "op": args.op, "root_hash": args.root_hash,
            "leaf_index": args.leaf_index,
        })
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
