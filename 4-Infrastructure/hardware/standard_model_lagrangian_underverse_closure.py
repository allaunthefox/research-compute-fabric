#!/usr/bin/env python3
"""Exact underverse closure checks for the Standard Model term graph.

Two closures are tested:

1. Complement closure:
   G_visible + G_under_complement - G_total = 0

2. Annihilation closure:
   G_visible + G_under_mirror = 0

The arithmetic is exact rational / Q(phi), matching the exact-average probe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from standard_model_lagrangian_eigen_probe import NODES, OBSERVATIONS
from standard_model_lagrangian_exact_average import QPhi, exact_rational_average, fraction_str, phi_targeted_average


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_underverse_closure_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def edge_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def rational_edges() -> dict[tuple[str, str], Fraction]:
    edges: dict[tuple[str, str], Fraction] = {}
    for left, right, weight, _note in OBSERVATIONS:
        key = edge_key(left, right)
        edges[key] = edges.get(key, Fraction(0)) + Fraction(int(weight))
    return edges


def complete_edges(capacity: Fraction) -> dict[tuple[str, str], Fraction]:
    edges: dict[tuple[str, str], Fraction] = {}
    for i, left in enumerate(NODES):
        for right in NODES[i + 1 :]:
            edges[edge_key(left, right)] = capacity
    return edges


def add_edges(*graphs: dict[tuple[str, str], Fraction]) -> dict[tuple[str, str], Fraction]:
    result: dict[tuple[str, str], Fraction] = {}
    keys = set().union(*(graph.keys() for graph in graphs))
    for key in keys:
        result[key] = sum((graph.get(key, Fraction(0)) for graph in graphs), Fraction(0))
    return result


def negate_edges(graph: dict[tuple[str, str], Fraction]) -> dict[tuple[str, str], Fraction]:
    return {key: -value for key, value in graph.items()}


def edge_closure_report(graph: dict[tuple[str, str], Fraction]) -> dict[str, Any]:
    nonzero = {f"{left}::{right}": value for (left, right), value in graph.items() if value != 0}
    l1 = sum((abs(value) for value in graph.values()), Fraction(0))
    return {
        "closed_exactly": l1 == 0,
        "nonzero_count": len(nonzero),
        "l1_error": fraction_str(l1),
        "nonzero_edges": {key: fraction_str(value) for key, value in sorted(nonzero.items())},
    }


def centroid_from_edges(edges: dict[tuple[str, str], Fraction]) -> dict[str, Fraction]:
    strengths = {node: Fraction(0) for node in NODES}
    for (left, right), weight in edges.items():
        strengths[left] += weight
        strengths[right] += weight
    total = sum(strengths.values(), Fraction(0))
    if total == 0:
        return strengths
    return {node: value / total for node, value in strengths.items()}


def signed_centroid_from_edges(edges: dict[tuple[str, str], Fraction]) -> dict[str, Fraction]:
    strengths = {node: Fraction(0) for node in NODES}
    for (left, right), weight in edges.items():
        strengths[left] += weight
        strengths[right] += weight
    total_abs = sum((abs(value) for value in strengths.values()), Fraction(0))
    if total_abs == 0:
        return strengths
    return {node: value / total_abs for node, value in strengths.items()}


def centroid_closure_report(left: dict[str, Fraction], right: dict[str, Fraction]) -> dict[str, Any]:
    sums = {node: left.get(node, Fraction(0)) + right.get(node, Fraction(0)) for node in NODES}
    l1 = sum((abs(value) for value in sums.values()), Fraction(0))
    return {
        "closed_exactly": l1 == 0,
        "l1_error": fraction_str(l1),
        "nonzero_components": {
            node: fraction_str(value)
            for node, value in sums.items()
            if value != 0
        },
    }


def qphi_closure_report() -> dict[str, Any]:
    visible = phi_targeted_average()["centroid_components_qphi"]
    visible_by_node = {
        item["node"]: QPhi(Fraction(item["centroid_component_qphi"]["a"]), Fraction(item["centroid_component_qphi"]["b"]))
        for item in visible
    }
    mirror = {node: QPhi(-value.a, -value.b) for node, value in visible_by_node.items()}
    sums = {node: visible_by_node[node] + mirror[node] for node in NODES}
    closed = all(value.a == 0 and value.b == 0 for value in sums.values())
    return {
        "closed_exactly": closed,
        "nonzero_components": {
            node: value.as_json()
            for node, value in sums.items()
            if value.a != 0 or value.b != 0
        },
        "visible_top_component": visible[0],
        "claim_boundary": "Q(phi) closure is exact for the targeted phi centroid and its signed mirror only.",
    }


def build_receipt() -> dict[str, Any]:
    visible = rational_edges()
    capacity = max(visible.values())
    total = complete_edges(capacity)
    complement = add_edges(total, negate_edges(visible))
    complement_closure = add_edges(visible, complement, negate_edges(total))
    mirror = negate_edges(visible)
    annihilation_closure = add_edges(visible, mirror)

    visible_centroid = centroid_from_edges(visible)
    mirror_centroid = signed_centroid_from_edges(mirror)
    rational_average = exact_rational_average()
    receipt = {
        "schema": "standard_model_lagrangian_underverse_closure_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_lagrangian_underverse_closure",
        "source": {
            "node_count": len(NODES),
            "visible_observation_count": len(OBSERVATIONS),
            "visible_edge_count": len(visible),
            "complete_edge_count": len(total),
            "complete_graph_capacity": fraction_str(capacity),
            "visible_average_hash_source": "4-Infrastructure/hardware/standard_model_lagrangian_exact_average_receipt.json",
        },
        "complement_closure": {
            "definition": "G_under_complement = G_total - G_visible",
            "expected_identity": "G_visible + G_under_complement - G_total = 0",
            "edge_closure": edge_closure_report(complement_closure),
        },
        "annihilation_closure": {
            "definition": "G_under_mirror = -G_visible",
            "expected_identity": "G_visible + G_under_mirror = 0",
            "edge_closure": edge_closure_report(annihilation_closure),
            "centroid_closure": centroid_closure_report(visible_centroid, mirror_centroid),
        },
        "qphi_annihilation_closure": qphi_closure_report(),
        "visible_rational_average_summary": {
            "average_edge_weight": rational_average["average_edge_weight"],
            "top_component": rational_average["centroid_components"][0],
            "top_group": next(iter(rational_average["group_centroid"].items())),
        },
        "lawful": True,
        "claim_boundary": (
            "Closure is exact for the extracted symbolic graph and its constructed "
            "underverse complement/mirror. It is not a physics claim about missing "
            "Standard Model terms or hidden sectors."
        ),
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "complement_closure": receipt["complement_closure"],
        "annihilation_closure": receipt["annihilation_closure"],
        "qphi_annihilation_closure": receipt["qphi_annihilation_closure"],
        "visible_rational_average_summary": receipt["visible_rational_average_summary"],
        "lawful": receipt["lawful"],
        "claim_boundary": receipt["claim_boundary"],
    }).encode("utf-8")
    receipt["stable_closure_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "complement_edge_closed": receipt["complement_closure"]["edge_closure"]["closed_exactly"],
        "annihilation_edge_closed": receipt["annihilation_closure"]["edge_closure"]["closed_exactly"],
        "annihilation_centroid_closed": receipt["annihilation_closure"]["centroid_closure"]["closed_exactly"],
        "qphi_annihilation_closed": receipt["qphi_annihilation_closure"]["closed_exactly"],
        "stable_closure_hash_sha256": receipt["stable_closure_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "out": str(args.out.relative_to(REPO)) if args.out.is_relative_to(REPO) else str(args.out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
