#!/usr/bin/env python3
"""Signed positive/negative axis graph for the equation manifold chart."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from standard_model_lagrangian_eigen_probe import NODES


REPO = Path(__file__).resolve().parents[2]
SHAPE = REPO / "4-Infrastructure" / "hardware" / "standard_model_underverse_manifold_shape_receipt.json"
AVERAGE = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_exact_average_receipt.json"
OUT_JSON = REPO / "4-Infrastructure" / "hardware" / "standard_model_signed_axis_graph_receipt.json"
OUT_GRAPHML = REPO / "4-Infrastructure" / "hardware" / "standard_model_signed_axis_graph.graphml"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def frac_from_json(obj: dict[str, Any]) -> Fraction:
    return Fraction(int(obj["numerator"]), int(obj["denominator"]))


def fraction_str(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def fraction_json(value: Fraction) -> dict[str, Any]:
    return {
        "fraction": fraction_str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(SHAPE.read_text(encoding="utf-8")),
        json.loads(AVERAGE.read_text(encoding="utf-8")),
    )


def visible_centroid(avg: dict[str, Any]) -> dict[str, Fraction]:
    return {
        item["node"]: frac_from_json(item["centroid_component"])
        for item in avg["rational_average"]["centroid_components"]
    }


def build_axis_records(shape: dict[str, Any], avg: dict[str, Any]) -> list[dict[str, Any]]:
    centroid = visible_centroid(avg)
    axes: list[dict[str, Any]] = []
    for node in NODES:
        positive = centroid[node]
        negative = -positive
        axes.append({
            "axis_id": f"centroid::{node}",
            "kind": "exact_centroid_mirror",
            "positive_node": f"+{node}",
            "negative_node": f"-{node}",
            "center_node": "origin::exact_closure",
            "positive_value": fraction_json(positive),
            "negative_value": fraction_json(negative),
            "closure_sum": fraction_json(positive + negative),
            "closed_exactly": positive + negative == 0,
            "classification": "annihilating_axis",
        })

    coords = shape["shape"]["coordinates"]
    axes.extend([
        {
            "axis_id": "phi_delta::higgs_goldstone_scalar",
            "kind": "targeted_phi_displacement",
            "positive_node": "+higgs_goldstone_phi_displacement",
            "negative_node": "-higgs_goldstone_phi_displacement",
            "center_node": "origin::qphi_mirror",
            "positive_value": shape["shape"]["dominant_axes"][2]["value_qphi"],
            "negative_value": {
                "form": "mirror of qphi_delta",
                "approx": -shape["shape"]["dominant_axes"][2]["value_qphi"]["approx"],
            },
            "magnitude_l2": coords["qphi_delta_norm_l2"],
            "closed_exactly": True,
            "classification": "qphi_signed_displacement_axis",
        },
        {
            "axis_id": "residual::top6_mass",
            "kind": "residual_mass_axis",
            "positive_node": "+top6_explicit_core",
            "negative_node": "-residual_sidecar",
            "center_node": "origin::rehydration_balance",
            "positive_value": {
                "fraction": "103/146",
                "decimal": 103 / 146,
                "note": "top six retained centroid mass",
            },
            "negative_value": coords["top6_residual_mass"],
            "closed_exactly": True,
            "classification": "core_residual_balance_axis",
        },
        {
            "axis_id": "antihydrogen::gravity_residual",
            "kind": "experimental_residual_axis",
            "positive_node": "+ordinary_gravity_reference",
            "negative_node": "-antihydrogen_central_residual",
            "center_node": "origin::uncertainty_envelope",
            "positive_value": {"g_reference": 1.0},
            "negative_value": {
                "residual_g": coords["antihydrogen_gravity_residual_g"],
                "sigma_g": coords["antihydrogen_gravity_sigma_g"],
                "z_score": coords["antihydrogen_gravity_z_score"],
            },
            "closed_exactly": False,
            "classification": "uncertainty_envelope_axis",
        },
        {
            "axis_id": "eigen_gap::phi_lift",
            "kind": "spectral_gap_lift_axis",
            "positive_node": "+phi_gap_lift",
            "negative_node": "-no_phi_gap_reference",
            "center_node": "origin::eigen_gap_reference",
            "positive_value": {
                "sector_phi_gap_lift": coords["sector_phi_gap_lift"],
                "omni_phi_gap_lift": coords["omni_phi_gap_lift"],
            },
            "negative_value": {"no_phi_gap": coords["eigen_gap_no_phi"]},
            "closed_exactly": False,
            "classification": "measured_feature_axis",
        },
    ])
    return axes


def graph_nodes_edges(axis_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {
        "origin::exact_closure": {"id": "origin::exact_closure", "label": "exact closure origin", "kind": "origin"},
        "origin::qphi_mirror": {"id": "origin::qphi_mirror", "label": "Q(phi) mirror origin", "kind": "origin"},
        "origin::rehydration_balance": {"id": "origin::rehydration_balance", "label": "rehydration balance origin", "kind": "origin"},
        "origin::uncertainty_envelope": {"id": "origin::uncertainty_envelope", "label": "uncertainty envelope origin", "kind": "origin"},
        "origin::eigen_gap_reference": {"id": "origin::eigen_gap_reference", "label": "eigen gap reference origin", "kind": "origin"},
    }
    edges = []
    for axis in axis_records:
        for sign_key, sign in (("positive_node", "+"), ("negative_node", "-")):
            node_id = axis[sign_key]
            nodes[node_id] = {
                "id": node_id,
                "label": node_id,
                "kind": axis["kind"],
                "sign": sign,
                "axis_id": axis["axis_id"],
            }
            edges.append({
                "id": f"{axis['axis_id']}::{sign}",
                "source": axis["center_node"],
                "target": node_id,
                "axis_id": axis["axis_id"],
                "sign": sign,
                "classification": axis["classification"],
                "closed_exactly": axis["closed_exactly"],
            })
    return list(nodes.values()), edges


def graphml(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="label" for="all" attr.name="label" attr.type="string"/>',
        '  <key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '  <key id="sign" for="all" attr.name="sign" attr.type="string"/>',
        '  <key id="axis_id" for="all" attr.name="axis_id" attr.type="string"/>',
        '  <key id="classification" for="edge" attr.name="classification" attr.type="string"/>',
        '  <key id="closed_exactly" for="edge" attr.name="closed_exactly" attr.type="boolean"/>',
        '  <graph id="standard_model_signed_axis_graph" edgedefault="directed">',
    ]
    for node in nodes:
        lines.append(f'    <node id="{escape(node["id"])}">')
        for key in ("label", "kind", "sign", "axis_id"):
            if key in node:
                lines.append(f'      <data key="{key}">{escape(str(node[key]))}</data>')
        lines.append("    </node>")
    for edge in edges:
        lines.append(f'    <edge id="{escape(edge["id"])}" source="{escape(edge["source"])}" target="{escape(edge["target"])}">')
        for key in ("axis_id", "sign", "classification", "closed_exactly"):
            lines.append(f'      <data key="{key}">{escape(str(edge[key]).lower() if isinstance(edge[key], bool) else str(edge[key]))}</data>')
        lines.append("    </edge>")
    lines.extend(["  </graph>", "</graphml>"])
    return "\n".join(lines) + "\n"


def build_receipt() -> dict[str, Any]:
    shape, avg = load_inputs()
    axes = build_axis_records(shape, avg)
    nodes, edges = graph_nodes_edges(axes)
    graphml_text = graphml(nodes, edges)
    OUT_GRAPHML.write_text(graphml_text, encoding="utf-8")
    receipt = {
        "schema": "standard_model_signed_axis_graph_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_signed_axis_graph",
        "source": {
            "shape_receipt": str(SHAPE.relative_to(REPO)),
            "shape_hash": file_hash(SHAPE),
            "average_receipt": str(AVERAGE.relative_to(REPO)),
            "average_hash": file_hash(AVERAGE),
        },
        "axis_count": len(axes),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "axes": axes,
        "graph": {
            "graphml": str(OUT_GRAPHML.relative_to(REPO)),
            "graphml_hash_sha256": sha256_bytes(graphml_text.encode("utf-8")),
        },
        "lawful": True,
        "claim_boundary": (
            "Signed-axis graph is a symbolic/compression graph. Positive and negative "
            "endpoints are coordinate directions, not physical charges or hidden sectors."
        ),
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "axis_count": receipt["axis_count"],
        "node_count": receipt["node_count"],
        "edge_count": receipt["edge_count"],
        "axes": receipt["axes"],
        "graph": receipt["graph"],
        "lawful": receipt["lawful"],
        "claim_boundary": receipt["claim_boundary"],
    }).encode("utf-8")
    receipt["stable_axis_graph_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_JSON)
    args = parser.parse_args()
    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "axis_count": receipt["axis_count"],
        "node_count": receipt["node_count"],
        "edge_count": receipt["edge_count"],
        "graphml": receipt["graph"],
        "stable_axis_graph_hash_sha256": receipt["stable_axis_graph_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "out": str(args.out.relative_to(REPO)) if args.out.is_relative_to(REPO) else str(args.out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
