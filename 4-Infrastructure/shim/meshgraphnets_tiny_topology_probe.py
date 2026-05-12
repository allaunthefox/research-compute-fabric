#!/usr/bin/env python3
"""Tiny MeshGraphNets-style topology probe.

This is a metadata/replay fixture for irregular mesh route surfaces. It does
not download, vendor, or score MeshGraphNets data. It checks whether a mesh
packet preserves canonical edges, faces, boundary nodes, degree sequence, and a
tiny deterministic message-passing replay before any real mesh slice is
admitted.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "meshgraphnets_tiny_probe"
RECEIPT = OUT_DIR / "meshgraphnets_tiny_topology_probe_receipt.json"
TABLE = OUT_DIR / "meshgraphnets_tiny_topology_probe_table.jsonl"


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    route_surface: str
    actual_mesh: dict[str, Any]
    candidate_mesh: dict[str, Any]
    negative_control: bool


BASE_MESH = {
    "mesh_family": "meshgraphnets_style_micro_fixture",
    "nodes": [
        {"id": 0, "xy": [0, 0], "kind": "boundary"},
        {"id": 1, "xy": [1, 0], "kind": "boundary"},
        {"id": 2, "xy": [1, 1], "kind": "boundary"},
        {"id": 3, "xy": [0, 1], "kind": "boundary"},
        {"id": 4, "xy": [1, 2], "kind": "boundary"},
        {"id": 5, "xy": [0, 2], "kind": "boundary"},
        {"id": 6, "xy": [0, 0], "kind": "anchor"},
    ],
    "edges": [
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
        [2, 4],
        [4, 5],
        [5, 3],
        [0, 2],
        [3, 4],
        [0, 6],
    ],
    "faces": [
        [0, 1, 2],
        [0, 2, 3],
        [3, 2, 4],
        [3, 4, 5],
    ],
    "node_feature": [1, 2, 3, 4, 5, 6, 7],
    "split": "tiny_local_probe",
    "source_bytes_vendored": 0,
}


def without_edge(mesh: dict[str, Any], edge: list[int]) -> dict[str, Any]:
    clone = json.loads(json.dumps(mesh))
    target = sorted(edge)
    clone["edges"] = [item for item in clone["edges"] if sorted(item) != target]
    return clone


def without_boundary_kind(mesh: dict[str, Any], node_id: int) -> dict[str, Any]:
    clone = json.loads(json.dumps(mesh))
    for node in clone["nodes"]:
        if node["id"] == node_id:
            node["kind"] = "unknown"
    return clone


FIXTURES = [
    Fixture(
        fixture_id="mesh_topology_canonical_admit",
        route_surface="MeshGraphNets",
        actual_mesh=BASE_MESH,
        candidate_mesh=BASE_MESH,
        negative_control=False,
    ),
    Fixture(
        fixture_id="mesh_missing_diagonal_negative",
        route_surface="MeshGraphNets",
        actual_mesh=BASE_MESH,
        candidate_mesh=without_edge(BASE_MESH, [0, 2]),
        negative_control=True,
    ),
    Fixture(
        fixture_id="mesh_boundary_kind_hold",
        route_surface="MeshGraphNets",
        actual_mesh=BASE_MESH,
        candidate_mesh=without_boundary_kind(BASE_MESH, 4),
        negative_control=False,
    ),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def canonical_edges(mesh: dict[str, Any]) -> list[list[int]]:
    return sorted([sorted([int(a), int(b)]) for a, b in mesh["edges"]])


def canonical_faces(mesh: dict[str, Any]) -> list[list[int]]:
    return sorted([sorted([int(value) for value in face]) for face in mesh["faces"]])


def boundary_nodes(mesh: dict[str, Any]) -> list[int]:
    return sorted(int(node["id"]) for node in mesh["nodes"] if node.get("kind") == "boundary")


def degree_sequence(mesh: dict[str, Any]) -> list[int]:
    node_ids = sorted(int(node["id"]) for node in mesh["nodes"])
    degree = {node_id: 0 for node_id in node_ids}
    for a, b in canonical_edges(mesh):
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    return [degree[node_id] for node_id in node_ids]


def message_pass(mesh: dict[str, Any]) -> list[int]:
    features = {int(index): int(value) for index, value in enumerate(mesh["node_feature"])}
    output = {int(node["id"]): features[int(node["id"])] for node in mesh["nodes"]}
    for a, b in canonical_edges(mesh):
        output[a] += features[b]
        output[b] += features[a]
    return [output[node_id] for node_id in sorted(output)]


def topology_errors(actual: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("node_count", len(actual["nodes"]), len(candidate["nodes"])),
        ("edge_set", canonical_edges(actual), canonical_edges(candidate)),
        ("face_set", canonical_faces(actual), canonical_faces(candidate)),
        ("boundary_nodes", boundary_nodes(actual), boundary_nodes(candidate)),
        ("degree_sequence", degree_sequence(actual), degree_sequence(candidate)),
        ("message_pass", message_pass(actual), message_pass(candidate)),
    ]
    errors: list[dict[str, Any]] = []
    for path, actual_value, candidate_value in checks:
        if actual_value != candidate_value:
            errors.append(
                {
                    "path": path,
                    "error": "value_mismatch",
                    "actual": actual_value,
                    "candidate": candidate_value,
                }
            )
    return errors


def generator_packet(fixture: Fixture) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "generator": "two_cell_strip_plus_anchor",
        "route_surface": fixture.route_surface,
        "node_count": len(fixture.candidate_mesh["nodes"]),
        "face_count": len(fixture.candidate_mesh["faces"]),
    }
    if fixture.fixture_id == "mesh_missing_diagonal_negative":
        packet["mutation"] = {"remove_edge": [0, 2]}
    elif fixture.fixture_id == "mesh_boundary_kind_hold":
        packet["mutation"] = {"node_kind": {"id": 4, "kind": "unknown"}}
    else:
        packet["mutation"] = "none"
    return packet


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    errors = topology_errors(fixture.actual_mesh, fixture.candidate_mesh)
    replay_valid = not errors
    residual_declared = True

    encoded_payload = {
        "packet": generator_packet(fixture),
        "topology_hashes": {
            "edge_set": sha256_text(stable_json(canonical_edges(fixture.candidate_mesh))),
            "face_set": sha256_text(stable_json(canonical_faces(fixture.candidate_mesh))),
        },
    }
    explicit_payload = {
        "nodes": fixture.actual_mesh["nodes"],
        "edges": fixture.actual_mesh["edges"],
        "faces": fixture.actual_mesh["faces"],
        "message_pass": message_pass(fixture.actual_mesh),
    }
    residual_payload = {"topology_errors": errors}

    encoded_bytes = len(stable_json(encoded_payload).encode("utf-8"))
    explicit_bytes = len(stable_json(explicit_payload).encode("utf-8"))
    residual_bytes = 0 if replay_valid else len(stable_json(residual_payload).encode("utf-8"))
    total_candidate_bytes = encoded_bytes + residual_bytes
    byte_gain = explicit_bytes - total_candidate_bytes

    if fixture.negative_control and replay_valid:
        status = "FAIL_NEGATIVE_CONTROL"
    elif replay_valid and residual_declared and byte_gain > 0 and not fixture.negative_control:
        status = "ADMIT_FIXTURE"
    else:
        status = "HOLD_DIAGNOSTIC"

    result = {
        "fixture_id": fixture.fixture_id,
        "route_surface": fixture.route_surface,
        "negative_control": fixture.negative_control,
        "actual_mesh_hash": sha256_text(stable_json(fixture.actual_mesh)),
        "candidate_mesh_hash": sha256_text(stable_json(fixture.candidate_mesh)),
        "edge_set_hash": sha256_text(stable_json(canonical_edges(fixture.actual_mesh))),
        "face_set_hash": sha256_text(stable_json(canonical_faces(fixture.actual_mesh))),
        "degree_sequence": degree_sequence(fixture.actual_mesh),
        "message_pass_hash": sha256_text(stable_json(message_pass(fixture.actual_mesh))),
        "topology_error_count": len(errors),
        "topology_errors": errors,
        "replay_valid": replay_valid,
        "residual_declared": residual_declared,
        "encoded_bytes": encoded_bytes,
        "explicit_bytes": explicit_bytes,
        "residual_bytes": residual_bytes,
        "byte_gain": byte_gain,
        "status": status,
    }
    result["result_hash"] = sha256_text(stable_json({k: v for k, v in result.items() if k != "result_hash"}))
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_fixture(fixture) for fixture in FIXTURES]
    with TABLE.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, sort_keys=True) + "\n")

    status_values = sorted({result["status"] for result in results})
    receipt = {
        "schema": "meshgraphnets_tiny_topology_probe_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_count": len(results),
        "table": rel(TABLE),
        "status_counts": {
            status: sum(1 for result in results if result["status"] == status)
            for status in status_values
        },
        "results": results,
        "decision": "HOLD",
        "claim_boundary": (
            "Tiny MeshGraphNets-style topology probe only. It tests canonical "
            "edge, face, boundary, degree-sequence, message-pass, residual, and "
            "byte-law accounting; it does not download MeshGraphNets data, does "
            "not vendor mesh trajectories, and does not claim benchmark results."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "table": rel(TABLE),
                "receipt_hash": receipt["receipt_hash"],
                "status_counts": receipt["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
