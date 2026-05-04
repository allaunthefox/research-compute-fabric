#!/usr/bin/env python3
"""ENE fractal fold codec.

This module gives ENE one canonical substrate for:

- fractal encoding: recursive self-similar nodes with O(log n) path traversal;
- manifold folding: Gray-code folded addresses that preserve near neighbors;
- damage prevention: parent/child hash consistency checks;
- endless growth: no fixed maximum tree size, only local storage limits.

It is a compact Python carrier for the ENE schema. It is not a compression
oracle; it is a lawful addressing and verification layer that other codecs can
use before or after Delta GCL, MS3C, or wiki/package binding.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import sqlite3
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


VERSION = "ene_fractal_fold_v1"
SOURCE_TYPE = "json_catalog"
GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def gray_code(index: int) -> int:
    """Fold a linear index into a Gray-code neighborhood address."""
    return index ^ (index >> 1)


def inverse_gray_code(code: int) -> int:
    value = code
    while code > 0:
        code >>= 1
        value ^= code
    return value


def golden_spiral_point(address: int, level: int = 0) -> dict[str, float]:
    """Project a folded address into a deterministic golden-spiral chart."""
    radius = math.sqrt(address + 1.0)
    theta = (address + 1.0) * GOLDEN_ANGLE
    shell = float(level + 1)
    return {
        "x": round(radius * math.cos(theta), 9),
        "y": round(radius * math.sin(theta), 9),
        "r": round(radius, 9),
        "theta": round(theta % (2.0 * math.pi), 9),
        "shell": shell,
    }


def manifold_distance(a: dict[str, float], b: dict[str, float]) -> float:
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    ds = a["shell"] - b["shell"]
    return math.sqrt(dx * dx + dy * dy + ds * ds)


def tree_depth(leaves: int, branching_factor: int) -> int:
    if leaves <= 1:
        return 0
    return math.ceil(math.log(leaves, branching_factor))


@dataclass(frozen=True)
class FractalNode:
    node_hash: str
    kind: str
    level: int
    ordinal: int
    fold_address: int
    start_leaf: int
    end_leaf: int
    size_bytes: int
    children: list[str]
    payload_b64: str | None = None


@dataclass(frozen=True)
class FractalManifest:
    root_hash: str
    name: str
    byte_len: int
    leaves_count: int
    depth: int
    chunk_size: int
    branching_factor: int
    created_at: str
    receipt: str


def make_leaf(chunk: bytes, ordinal: int) -> FractalNode:
    payload_hash = sha256_bytes(chunk)
    body = {
        "v": VERSION,
        "kind": "leaf",
        "level": 0,
        "ordinal": ordinal,
        "fold_address": gray_code(ordinal),
        "size_bytes": len(chunk),
        "payload_hash": payload_hash,
    }
    return FractalNode(
        node_hash=sha256_text(canonical_json(body)),
        kind="leaf",
        level=0,
        ordinal=ordinal,
        fold_address=gray_code(ordinal),
        start_leaf=ordinal,
        end_leaf=ordinal,
        size_bytes=len(chunk),
        children=[],
        payload_b64=base64.b64encode(chunk).decode("ascii"),
    )


def make_parent(children: list[FractalNode], level: int, ordinal: int) -> FractalNode:
    body = {
        "v": VERSION,
        "kind": "parent",
        "level": level,
        "ordinal": ordinal,
        "fold_address": gray_code(ordinal),
        "start_leaf": children[0].start_leaf,
        "end_leaf": children[-1].end_leaf,
        "size_bytes": sum(child.size_bytes for child in children),
        "children": [child.node_hash for child in children],
    }
    return FractalNode(
        node_hash=sha256_text(canonical_json(body)),
        kind="parent",
        level=level,
        ordinal=ordinal,
        fold_address=gray_code(ordinal),
        start_leaf=children[0].start_leaf,
        end_leaf=children[-1].end_leaf,
        size_bytes=sum(child.size_bytes for child in children),
        children=[child.node_hash for child in children],
    )


def encode_fractal_chunks(chunks: list[bytes], name: str, chunk_size: int, branching_factor: int = 4) -> tuple[FractalManifest, list[FractalNode]]:
    if branching_factor < 2:
        raise ValueError("branching_factor must be at least 2")
    chunks = chunks or [b""]
    all_nodes: list[FractalNode] = [make_leaf(chunk, idx) for idx, chunk in enumerate(chunks)]
    current = all_nodes[:]
    level = 1
    while len(current) > 1:
        parents: list[FractalNode] = []
        for idx in range(0, len(current), branching_factor):
            parent = make_parent(current[idx : idx + branching_factor], level, len(parents))
            parents.append(parent)
        all_nodes.extend(parents)
        current = parents
        level += 1

    root = current[0]
    created_at = iso_utc()
    receipt_body = {
        "v": VERSION,
        "name": name,
        "root_hash": root.node_hash,
        "byte_len": sum(len(chunk) for chunk in chunks),
        "leaves_count": len(chunks),
        "depth": level - 1,
        "chunk_size": chunk_size,
        "branching_factor": branching_factor,
        "created_at": created_at,
    }
    receipt = sha256_text(canonical_json(receipt_body))
    manifest = FractalManifest(
        root_hash=root.node_hash,
        name=name,
        byte_len=sum(len(chunk) for chunk in chunks),
        leaves_count=len(chunks),
        depth=level - 1,
        chunk_size=chunk_size,
        branching_factor=branching_factor,
        created_at=created_at,
        receipt=receipt,
    )
    return manifest, all_nodes


def encode_fractal(data: bytes, name: str, chunk_size: int = 4096, branching_factor: int = 4) -> tuple[FractalManifest, list[FractalNode]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)] or [b""]
    return encode_fractal_chunks(chunks, name, chunk_size, branching_factor)


def parse_graphml_concepts(graphml: bytes) -> tuple[list[dict[str, Any]], list[bytes]]:
    """Convert GraphML nodes/edges into ENE concept records.

    Each graph node becomes one fractal leaf so concept retrieval maps directly
    to the O(log n) navigation path.
    """
    root = ET.fromstring(graphml)
    ns = {"g": "http://graphml.graphdrawing.org/xmlns"}
    key_names = {
        key.attrib.get("id", ""): key.attrib.get("attr.name", key.attrib.get("id", ""))
        for key in root.findall("g:key", ns)
    }
    nodes: dict[str, dict[str, Any]] = {}
    adjacency: dict[str, list[str]] = {}
    for node in root.findall(".//g:node", ns):
        node_id = node.attrib["id"]
        data = {}
        for item in node.findall("g:data", ns):
            data[key_names.get(item.attrib.get("key", ""), item.attrib.get("key", ""))] = item.text or ""
        nodes[node_id] = {
            "graph_node_id": node_id,
            "name": data.get("name", node_id),
            "family": data.get("family", ""),
            "domain": data.get("domain", ""),
        }
        adjacency[node_id] = []
    for edge in root.findall(".//g:edge", ns):
        source = edge.attrib.get("source")
        target = edge.attrib.get("target")
        if source in adjacency and target:
            adjacency[source].append(target)

    records = []
    for idx, node_id in enumerate(sorted(nodes)):
        record = {
            "kind": "graphml_concept",
            "leaf_index": idx,
            "fold_address": gray_code(idx),
            "golden_spiral": golden_spiral_point(gray_code(idx), 0),
            **nodes[node_id],
            "neighbors": sorted(adjacency.get(node_id, [])),
        }
        records.append(record)
    chunks = [canonical_json(record).encode("utf-8") for record in records]
    return records, chunks


def node_record(node: FractalNode) -> dict[str, Any]:
    return asdict(node)


def archive_record(manifest: FractalManifest) -> dict[str, Any]:
    raw_content = {
        "kind": "ene_fractal_fold_manifest",
        "version": VERSION,
        "manifest": asdict(manifest),
        "properties": {
            "fractal_encoding": "self_similar_recursive_tree",
            "traversal": "O(log_B(n)) by root-to-leaf proof path",
            "entity_retrieval": "O(log_B(n)) via manifold_distance_pruning",
            "manifold_folding": "gray_code_folded_leaf_addresses",
            "navigation": "golden_spiral_address_chart",
            "damage_prevention": "fractal_hash_parent_child_consistency",
            "endless": "unbounded_recursion_subject_to_storage_policy",
        },
    }
    content_hash = sha256_text(canonical_json(raw_content))
    return {
        "archive_id": f"json_catalog_ene_fractal_{manifest.root_hash[:16]}",
        "source_type": SOURCE_TYPE,
        "source_file": f"ene-fractal://{manifest.root_hash}",
        "raw_content": raw_content,
        "extracted_text": f"{manifest.name} {manifest.root_hash} fractal fold manifold compression",
        "extracted_at": manifest.created_at,
        "content_hash": content_hash,
        "extraction_version": VERSION,
    }


def jsonl_event(record: dict[str, Any], manifest: FractalManifest) -> dict[str, Any]:
    pkg = f"ene/fractal/{manifest.root_hash[:16]}"
    event = {
        "src": "ene",
        "op": "upsert",
        "data": {
            "pkg": pkg,
            "version": VERSION,
            "tier": "RESEARCH",
            "domain": "topology",
            "archetype": "fractal_fold",
            "description": "ENE fractal fold manifest",
        "tags": ["ene", "fractal", "fold", "manifold", "compression"],
            "source": "ene_fractal_fold",
            "sha256": record["content_hash"],
        },
        "bind": {
            "lawful": True,
            "class": "geometric_bind",
            "invariant": "parent_child_hash_consistency",
        },
        "provenance": {
            "archive_id": record["archive_id"],
            "attestation_hash": f"sha256:{manifest.receipt}",
            "node": "ene-fractal-fold",
        },
    }
    event["id"] = f"ene:{sha256_text(canonical_json(event))[:32]}"
    return event


class ENEFractalFold:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS ene_fractal_manifolds (
                    root_hash TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    byte_len INTEGER NOT NULL,
                    leaves_count INTEGER NOT NULL,
                    depth INTEGER NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    branching_factor INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    receipt TEXT NOT NULL,
                    archive_record TEXT NOT NULL,
                    jsonl_event TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ene_fractal_nodes (
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
                );

                CREATE INDEX IF NOT EXISTS idx_ene_fractal_leaf
                ON ene_fractal_nodes(root_hash, level, ordinal);

                CREATE TABLE IF NOT EXISTS ene_fractal_graph_entities (
                    root_hash TEXT NOT NULL,
                    graph_node_id TEXT NOT NULL,
                    leaf_index INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    family TEXT,
                    domain TEXT,
                    neighbors TEXT NOT NULL,
                    PRIMARY KEY (root_hash, graph_node_id)
                );

                CREATE INDEX IF NOT EXISTS idx_ene_fractal_graph_name
                ON ene_fractal_graph_entities(root_hash, name);
                """
            )

    def _store(self, manifest: FractalManifest, nodes: list[FractalNode]) -> tuple[dict[str, Any], dict[str, Any]]:
        record = archive_record(manifest)
        event = jsonl_event(record, manifest)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ene_fractal_manifolds
                (root_hash, name, byte_len, leaves_count, depth, chunk_size, branching_factor,
                 created_at, receipt, archive_record, jsonl_event)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.root_hash,
                    manifest.name,
                    manifest.byte_len,
                    manifest.leaves_count,
                    manifest.depth,
                    manifest.chunk_size,
                    manifest.branching_factor,
                    manifest.created_at,
                    manifest.receipt,
                    canonical_json(record),
                    canonical_json(event),
                ),
            )
            conn.execute("DELETE FROM ene_fractal_nodes WHERE root_hash = ?", (manifest.root_hash,))
            conn.executemany(
                """
                INSERT INTO ene_fractal_nodes
                (root_hash, node_hash, kind, level, ordinal, fold_address, start_leaf,
                 end_leaf, size_bytes, children, payload_b64)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        manifest.root_hash,
                        node.node_hash,
                        node.kind,
                        node.level,
                        node.ordinal,
                        node.fold_address,
                        node.start_leaf,
                        node.end_leaf,
                        node.size_bytes,
                        canonical_json(node.children),
                        node.payload_b64,
                    )
                    for node in nodes
                ],
            )
        return record, event

    def put(self, data: bytes, name: str = "unnamed", chunk_size: int = 4096, branching_factor: int = 4) -> dict[str, Any]:
        manifest, nodes = encode_fractal(data, name, chunk_size, branching_factor)
        record, event = self._store(manifest, nodes)
        return {
            "ok": True,
            "op": "fractal_put",
            "manifest": asdict(manifest),
            "archive_record": record,
            "jsonl_event": event,
        }

    def put_graphml(self, graphml: bytes, name: str = "graphml", branching_factor: int = 4) -> dict[str, Any]:
        records, chunks = parse_graphml_concepts(graphml)
        max_chunk = max((len(chunk) for chunk in chunks), default=0)
        manifest, nodes = encode_fractal_chunks(chunks, name, max_chunk, branching_factor)
        record, event = self._store(manifest, nodes)
        with self._connect() as conn:
            conn.execute("DELETE FROM ene_fractal_graph_entities WHERE root_hash = ?", (manifest.root_hash,))
            conn.executemany(
                """
                INSERT INTO ene_fractal_graph_entities
                (root_hash, graph_node_id, leaf_index, name, family, domain, neighbors)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        manifest.root_hash,
                        concept["graph_node_id"],
                        concept["leaf_index"],
                        concept["name"],
                        concept["family"],
                        concept["domain"],
                        canonical_json(concept["neighbors"]),
                    )
                    for concept in records
                ],
            )
        return {
            "ok": True,
            "op": "fractal_graphml_put",
            "manifest": asdict(manifest),
            "graphml": {"concepts": len(records), "concept_leaf_mode": True},
            "archive_record": record,
            "jsonl_event": event,
        }

    def manifest(self, root_hash: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM ene_fractal_manifolds WHERE root_hash = ?",
                (root_hash,),
            ).fetchone()
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
            "created_at": row["created_at"],
            "receipt": row["receipt"],
            "archive_record": json.loads(row["archive_record"]),
            "jsonl_event": json.loads(row["jsonl_event"]),
        }

    def _node(self, conn: sqlite3.Connection, root_hash: str, node_hash: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM ene_fractal_nodes WHERE root_hash = ? AND node_hash = ?",
            (root_hash, node_hash),
        ).fetchone()
        if row is None:
            raise KeyError(f"missing fractal node {node_hash}")
        return row

    def proof(self, root_hash: str, leaf_index: int) -> dict[str, Any]:
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        if leaf_index < 0 or leaf_index >= meta["leaves_count"]:
            raise IndexError("leaf_index outside manifold")

        with self._connect() as conn:
            frontier = root_hash
            path = []
            target_point = golden_spiral_point(gray_code(leaf_index), 0)
            while True:
                row = self._node(conn, root_hash, frontier)
                children = json.loads(row["children"])
                node_point = golden_spiral_point(row["fold_address"], row["level"])
                path.append(
                    {key: row[key] for key in row.keys() if key != "payload_b64"}
                    | {
                        "children": children,
                        "golden_spiral": node_point,
                        "distance_to_target": round(manifold_distance(node_point, target_point), 9),
                    }
                )
                if row["kind"] == "leaf":
                    payload = base64.b64decode(row["payload_b64"] or "")
                    break
                next_hash = None
                pruned = []
                for child_hash in children:
                    child = self._node(conn, root_hash, child_hash)
                    child_point = golden_spiral_point(child["fold_address"], child["level"])
                    pruned.append(
                        {
                            "node_hash": child_hash,
                            "covers_target": child["start_leaf"] <= leaf_index <= child["end_leaf"],
                            "distance": round(manifold_distance(child_point, target_point), 9),
                        }
                    )
                    if child["start_leaf"] <= leaf_index <= child["end_leaf"]:
                        next_hash = child_hash
                path[-1]["manifold_distance_pruning"] = sorted(pruned, key=lambda item: item["distance"])
                if next_hash is None:
                    raise ValueError("corrupt tree: no child covers requested leaf")
                frontier = next_hash

        path_valid = self._verify_path_rows(path, payload)
        return {
            "ok": True,
            "op": "fractal_proof",
            "root_hash": root_hash,
            "leaf_index": leaf_index,
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
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ene_fractal_nodes WHERE root_hash = ?",
                (root_hash,),
            ).fetchall()
            by_hash = {row["node_hash"]: row for row in rows}
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
                    child_nodes.append(
                        FractalNode(
                            node_hash=child["node_hash"],
                            kind=child["kind"],
                            level=child["level"],
                            ordinal=child["ordinal"],
                            fold_address=child["fold_address"],
                            start_leaf=child["start_leaf"],
                            end_leaf=child["end_leaf"],
                            size_bytes=child["size_bytes"],
                            children=json.loads(child["children"]),
                            payload_b64=child["payload_b64"],
                        )
                    )
                if len(child_nodes) == len(children):
                    expected = make_parent(child_nodes, row["level"], row["ordinal"]).node_hash
                    if expected != row["node_hash"]:
                        errors.append({"node": row["node_hash"], "error": "parent_hash_mismatch", "expected": expected})

        return {
            "ok": not errors,
            "op": "fractal_verify",
            "root_hash": root_hash,
            "checked_nodes": len(rows),
            "errors": errors,
            "damage_detected": bool(errors),
        }

    def neighbors(self, root_hash: str, leaf_index: int) -> dict[str, Any]:
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        candidates = sorted(set(idx for idx in (leaf_index - 1, leaf_index, leaf_index + 1) if 0 <= idx < meta["leaves_count"]))
        return {
            "ok": True,
            "op": "fractal_neighbors",
            "root_hash": root_hash,
            "leaf_index": leaf_index,
            "fold_address": gray_code(leaf_index),
            "neighbors": [
                {
                    "leaf_index": idx,
                    "fold_address": gray_code(idx),
                    "golden_spiral": golden_spiral_point(gray_code(idx), 0),
                    "fold_distance": bin(gray_code(idx) ^ gray_code(leaf_index)).count("1"),
                }
                for idx in candidates
            ],
        }

    def graph_entity(self, root_hash: str, graph_node_id: str = "", name: str = "") -> dict[str, Any]:
        with self._connect() as conn:
            if graph_node_id:
                row = conn.execute(
                    "SELECT * FROM ene_fractal_graph_entities WHERE root_hash = ? AND graph_node_id = ?",
                    (root_hash, graph_node_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM ene_fractal_graph_entities WHERE root_hash = ? AND lower(name) = lower(?)",
                    (root_hash, name),
                ).fetchone()
        if row is None:
            return {"ok": False, "op": "fractal_graph_entity", "error": "graph entity not found"}
        proof = self.navigate(root_hash, row["leaf_index"])
        return {
            "ok": True,
            "op": "fractal_graph_entity",
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
        with self._connect() as conn:
            rows = [
                conn.execute(
                    "SELECT * FROM ene_fractal_graph_entities WHERE root_hash = ? AND graph_node_id = ?",
                    (root_hash, neighbor_id),
                ).fetchone()
                for neighbor_id in neighbor_ids
            ]
        return {
            "ok": True,
            "op": "fractal_graph_neighbors",
            "root_hash": root_hash,
            "graph_node_id": graph_node_id,
            "neighbors": [
                {
                    "graph_node_id": row["graph_node_id"],
                    "leaf_index": row["leaf_index"],
                    "name": row["name"],
                    "family": row["family"],
                    "domain": row["domain"],
                    "fold_address": gray_code(row["leaf_index"]),
                    "golden_spiral": golden_spiral_point(gray_code(row["leaf_index"]), 0),
                }
                for row in rows
                if row is not None
            ],
        }

    def navigate(self, root_hash: str, leaf_index: int) -> dict[str, Any]:
        """Retrieve an entity path by fixed-factor manifold-distance pruning."""
        meta = self.manifest(root_hash)
        if meta is None:
            raise KeyError(f"unknown root {root_hash}")
        if leaf_index < 0 or leaf_index >= meta["leaves_count"]:
            raise IndexError("leaf_index outside manifold")

        target_point = golden_spiral_point(gray_code(leaf_index), 0)
        with self._connect() as conn:
            frontier = root_hash
            path = []
            while True:
                row = self._node(conn, root_hash, frontier)
                children = json.loads(row["children"])
                path.append(
                    {
                        "node_hash": row["node_hash"],
                        "kind": row["kind"],
                        "level": row["level"],
                        "ordinal": row["ordinal"],
                        "start_leaf": row["start_leaf"],
                        "end_leaf": row["end_leaf"],
                        "fold_address": row["fold_address"],
                        "children": children,
                        "golden_spiral": golden_spiral_point(row["fold_address"], row["level"]),
                    }
                )
                if row["kind"] == "leaf":
                    payload = base64.b64decode(row["payload_b64"] or "")
                    break

                ranked = []
                for child_hash in children:
                    child = self._node(conn, root_hash, child_hash)
                    point = golden_spiral_point(child["fold_address"], child["level"])
                    ranked.append(
                        {
                            "node_hash": child_hash,
                            "distance": manifold_distance(point, target_point),
                            "covers_target": child["start_leaf"] <= leaf_index <= child["end_leaf"],
                        }
                    )
                ranked.sort(key=lambda item: (not item["covers_target"], item["distance"]))
                path[-1]["pruned_candidates"] = [
                    {
                        "node_hash": item["node_hash"],
                        "distance": round(item["distance"], 9),
                        "covers_target": item["covers_target"],
                    }
                    for item in ranked
                ]
                frontier = ranked[0]["node_hash"]

        return {
            "ok": True,
            "op": "fractal_navigate",
            "root_hash": root_hash,
            "leaf_index": leaf_index,
            "target": {
                "fold_address": gray_code(leaf_index),
                "golden_spiral": target_point,
            },
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
    parser = argparse.ArgumentParser(description="ENE fractal fold codec")
    parser.add_argument("--db", default="data/ene-fractal-fold.db")
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

    layer = ENEFractalFold(args.db)
    if args.op in {"put", "encode"}:
        data = args.file.read() if args.file else args.text.encode("utf-8")
        result = layer.put(data, args.name, args.chunk_size, args.branching_factor)
    elif args.op in {"put_graphml", "graphml"}:
        data = args.file.read() if args.file else args.text.encode("utf-8")
        result = layer.put_graphml(data, args.name, args.branching_factor)
    elif args.op in {"graph_entity", "concept", "graph_neighbors"}:
        result = layer.handle_request(
            {
                "op": args.op,
                "root_hash": args.root_hash,
                "leaf_index": args.leaf_index,
                "graph_node_id": args.graph_node_id or "",
                "name": args.name,
            }
        )
    else:
        result = layer.handle_request(
            {"op": args.op, "root_hash": args.root_hash, "leaf_index": args.leaf_index}
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
