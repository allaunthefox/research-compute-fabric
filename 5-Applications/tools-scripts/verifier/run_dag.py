#!/usr/bin/env python3
"""
run_dag.py — Merkle DAG provenance for verifier and audit runs.

Every run that uses RunDAG emits a JSON file describing its computation as a
directed acyclic graph of typed nodes:

    input    — a parameter or initial value, hashed by repr
    compute  — a deterministic function call on parent nodes, hashed by
               (function name, parent hashes, output summary)
    gate     — a verifier gate's result on parent compute outputs, hashed by
               (gate name, parent hashes, result)
    verdict  — terminal aggregation of all gates, hashed by gate results

Each node's hash includes its parents' hashes, so the DAG is a Merkle DAG: a
single byte changed anywhere upstream perturbs every downstream hash. This
gives the AVMR/metaprobe receipt principle a *structural* guarantee, not just
an asserted one.

Schema is intentionally simple JSON so the artifact is consumable by any tool
that reads JSON (and any graph viewer that accepts node/edge lists).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any


def _utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _sha256(s: str | bytes) -> str:
    if isinstance(s, str):
        s = s.encode("utf-8")
    return "sha256:" + hashlib.sha256(s).hexdigest()


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "sha256:MISSING"
    return _sha256(path.read_bytes())


def _stable_repr(value: Any) -> str:
    """Deterministic serialization for hashing.

    Falls back to repr() for objects json can't handle.
    """
    try:
        return json.dumps(value, sort_keys=True, default=repr)
    except (TypeError, ValueError):
        return repr(value)


class RunDAG:
    """Build up a Merkle DAG of a verifier or audit run as it executes."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, run_type: str, code_paths: list[Path] | None = None,
                 run_id: str | None = None):
        self.run_type = run_type
        self.run_id = run_id or f"{run_type}-{_utcnow()}-{uuid.uuid4().hex[:8]}"
        self.started_at = _utcnow()
        self.completed_at: str | None = None
        self.code_provenance = {
            str(p): _hash_file(p) for p in (code_paths or [])
        }
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    # ----- node primitives -----

    def _record_edges(self, node_id: str, parents: list[str]) -> None:
        for p in parents:
            if p not in self.nodes:
                raise KeyError(f"DAG edge {p} → {node_id}: parent not yet in DAG")
            self.edges.append({"from": p, "to": node_id})

    def add_input(self, node_id: str, value: Any) -> str:
        if node_id in self.nodes:
            raise KeyError(f"node already exists: {node_id}")
        value_repr = _stable_repr(value)
        h = _sha256(value_repr)
        self.nodes[node_id] = {
            "id": node_id, "type": "input",
            "value_repr": value_repr, "hash": h,
        }
        return h

    def add_compute(self, node_id: str, function: str, parents: list[str],
                    output_summary: dict) -> str:
        if node_id in self.nodes:
            raise KeyError(f"node already exists: {node_id}")
        parent_hashes = [self.nodes[p]["hash"] for p in parents]
        payload = _stable_repr({
            "function": function,
            "parent_hashes": parent_hashes,
            "output": output_summary,
        })
        h = _sha256(payload)
        self.nodes[node_id] = {
            "id": node_id, "type": "compute",
            "function": function, "parent_hashes": parent_hashes,
            "output_summary": output_summary, "hash": h,
        }
        self._record_edges(node_id, parents)
        return h

    def add_gate(self, node_id: str, function: str, parents: list[str],
                 result: dict) -> str:
        if node_id in self.nodes:
            raise KeyError(f"node already exists: {node_id}")
        parent_hashes = [self.nodes[p]["hash"] for p in parents]
        payload = _stable_repr({
            "function": function,
            "parent_hashes": parent_hashes,
            "result": result,
        })
        h = _sha256(payload)
        self.nodes[node_id] = {
            "id": node_id, "type": "gate",
            "function": function, "parent_hashes": parent_hashes,
            "result": result, "hash": h,
        }
        self._record_edges(node_id, parents)
        return h

    def add_verdict(self, node_id: str, gate_ids: list[str],
                    pass_predicate=lambda g: g["result"].get("passes", False)) -> str:
        if node_id in self.nodes:
            raise KeyError(f"node already exists: {node_id}")
        parent_hashes = [self.nodes[gid]["hash"] for gid in gate_ids]
        results = {gid: pass_predicate(self.nodes[gid]) for gid in gate_ids}
        # Hash MUST include parent hashes to preserve the Merkle property —
        # otherwise two runs with the same pass/fail pattern but different
        # underlying gate-metric values produce identical verdict hashes.
        payload = _stable_repr({
            "gate_ids": gate_ids,
            "parent_hashes": parent_hashes,
            "results": results,
        })
        h = _sha256(payload)
        self.nodes[node_id] = {
            "id": node_id, "type": "verdict",
            "gate_ids": gate_ids, "parent_hashes": parent_hashes,
            "results": results, "all_passed": all(results.values()),
            "hash": h,
        }
        self._record_edges(node_id, gate_ids)
        return h

    # ----- emit -----

    def merkle_root(self) -> str:
        verdict_nodes = [n for n in self.nodes.values() if n["type"] == "verdict"]
        if not verdict_nodes:
            # Aggregate hash over all leaf nodes if no explicit verdict
            leaf_hashes = sorted(n["hash"] for n in self.nodes.values())
            return _sha256(_stable_repr(leaf_hashes))
        # Single verdict: its hash IS the merkle root
        if len(verdict_nodes) == 1:
            return verdict_nodes[0]["hash"]
        # Multiple verdicts: hash of sorted verdict hashes
        return _sha256(_stable_repr(sorted(v["hash"] for v in verdict_nodes)))

    def emit(self, path: Path) -> Path:
        self.completed_at = _utcnow()
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "schema_version": self.SCHEMA_VERSION,
            "run_id": self.run_id,
            "run_type": self.run_type,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "code_provenance": self.code_provenance,
            "merkle_root": self.merkle_root(),
            "n_nodes": len(self.nodes),
            "n_edges": len(self.edges),
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
        }
        path.write_text(json.dumps(doc, indent=2, default=str))
        return path

    # ----- helpers -----

    def to_dot(self) -> str:
        """Emit Graphviz DOT for visual inspection."""
        lines = [f'digraph "{self.run_id}" {{', '  rankdir=LR;', '  node [shape=box];']
        type_color = {"input": "lightblue", "compute": "white",
                      "gate": "lightyellow", "verdict": "lightgreen"}
        for n in self.nodes.values():
            label = n["id"]
            if n["type"] == "gate":
                label += f"\\n{'PASS' if n['result'].get('passes') else 'FAIL'}"
                if "metric" in n["result"]:
                    label += f"\\nm={n['result']['metric']:.4g}"
            color = type_color.get(n["type"], "white")
            lines.append(f'  "{n["id"]}" [label="{label}", style=filled, fillcolor={color}];')
        for e in self.edges:
            lines.append(f'  "{e["from"]}" -> "{e["to"]}";')
        lines.append("}")
        return "\n".join(lines)
