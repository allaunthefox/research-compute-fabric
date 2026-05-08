#!/usr/bin/env python3
"""Rainbow Raccoon Compiler integration shim.

RRC is modeled here as a manifold-indexed type-checker surface.  This is not a
Lean proof generator yet.  It is the receipt-bearing Python boundary that turns
raw objects into:

1. a deterministic manifold projection,
2. a nearest lawful-shape classification,
3. an explicit type-witness status,
4. a field-equation profile,
5. an invariant receipt.

The important rule is conservative synthesis: missing proof evidence becomes a
HOLD witness, never a promoted proof.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "rainbow_raccoon_compiler_receipt.json"
CURRICULUM = SHIM / "rainbow_raccoon_compiler_curriculum.jsonl"


SOURCE_ARTIFACTS = [
    "docs/compression_signal_shaping_synthesis.md",
    "4-Infrastructure/shim/compression_signal_shaping_synthesis_receipt.json",
    "4-Infrastructure/shim/projectable_geometry_topology_model_receipt.json",
    "4-Infrastructure/shim/holographic_fractional_recursive_equation_fold_receipt.json",
    "4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json",
    "4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json",
    "docs/research/GCCL_THEORY_INTRO.md",
    "0-Core-Formalism/lean/Semantics/Semantics/GeometricCompressionWorkspace.lean",
]


MANIFOLD_AXES = [
    "semantic_entropy",
    "geometric_mass",
    "compression_pressure",
    "topology_torsion",
    "receipt_density",
    "field_energy",
    "hardware_affinity",
    "proof_readiness",
    "residual_risk",
    "shape_closure",
    "history_depth",
    "negative_control_strength",
    "projection_declared",
    "decoder_declared",
    "witness_declared",
    "scale_band_declared",
]


LAW_SHAPE_PROTOTYPES: dict[str, dict[str, float]] = {
    "SignalShapedRouteCompiler": {
        "semantic_entropy": 0.58,
        "geometric_mass": 0.28,
        "compression_pressure": 0.92,
        "topology_torsion": 0.34,
        "receipt_density": 0.78,
        "field_energy": 0.52,
        "hardware_affinity": 0.61,
        "proof_readiness": 0.42,
        "residual_risk": 0.31,
        "shape_closure": 0.76,
        "history_depth": 0.46,
        "negative_control_strength": 0.83,
        "projection_declared": 0.91,
        "decoder_declared": 0.88,
        "witness_declared": 0.79,
        "scale_band_declared": 0.64,
    },
    "ProjectableGeometryTopology": {
        "semantic_entropy": 0.34,
        "geometric_mass": 0.94,
        "compression_pressure": 0.56,
        "topology_torsion": 0.72,
        "receipt_density": 0.81,
        "field_energy": 0.76,
        "hardware_affinity": 0.68,
        "proof_readiness": 0.49,
        "residual_risk": 0.37,
        "shape_closure": 0.90,
        "history_depth": 0.38,
        "negative_control_strength": 0.61,
        "projection_declared": 0.95,
        "decoder_declared": 0.70,
        "witness_declared": 0.84,
        "scale_band_declared": 0.73,
    },
    "CognitiveLoadField": {
        "semantic_entropy": 0.86,
        "geometric_mass": 0.42,
        "compression_pressure": 0.63,
        "topology_torsion": 0.66,
        "receipt_density": 0.55,
        "field_energy": 0.88,
        "hardware_affinity": 0.37,
        "proof_readiness": 0.28,
        "residual_risk": 0.71,
        "shape_closure": 0.52,
        "history_depth": 0.91,
        "negative_control_strength": 0.42,
        "projection_declared": 0.76,
        "decoder_declared": 0.38,
        "witness_declared": 0.53,
        "scale_band_declared": 0.68,
    },
    "CadForceProbeReceipt": {
        "semantic_entropy": 0.25,
        "geometric_mass": 0.91,
        "compression_pressure": 0.30,
        "topology_torsion": 0.64,
        "receipt_density": 0.87,
        "field_energy": 0.81,
        "hardware_affinity": 0.73,
        "proof_readiness": 0.45,
        "residual_risk": 0.43,
        "shape_closure": 0.86,
        "history_depth": 0.31,
        "negative_control_strength": 0.88,
        "projection_declared": 0.92,
        "decoder_declared": 0.46,
        "witness_declared": 0.89,
        "scale_band_declared": 0.79,
    },
    "LogogramProjection": {
        "semantic_entropy": 0.62,
        "geometric_mass": 0.49,
        "compression_pressure": 0.86,
        "topology_torsion": 0.48,
        "receipt_density": 0.72,
        "field_energy": 0.43,
        "hardware_affinity": 0.58,
        "proof_readiness": 0.36,
        "residual_risk": 0.34,
        "shape_closure": 0.78,
        "history_depth": 0.34,
        "negative_control_strength": 0.55,
        "projection_declared": 0.93,
        "decoder_declared": 0.84,
        "witness_declared": 0.82,
        "scale_band_declared": 0.58,
    },
    "HoldForUnlawfulOrUnderspecifiedShape": {
        "semantic_entropy": 0.76,
        "geometric_mass": 0.40,
        "compression_pressure": 0.50,
        "topology_torsion": 0.83,
        "receipt_density": 0.24,
        "field_energy": 0.70,
        "hardware_affinity": 0.25,
        "proof_readiness": 0.10,
        "residual_risk": 0.91,
        "shape_closure": 0.19,
        "history_depth": 0.74,
        "negative_control_strength": 0.12,
        "projection_declared": 0.18,
        "decoder_declared": 0.15,
        "witness_declared": 0.10,
        "scale_band_declared": 0.22,
    },
}


FIELD_EQUATIONS = {
    "SignalShapedRouteCompiler": (
        "r* = argmin_r LB(r | phi_signal(c), semantic_regime(c), history_state); "
        "promote iff exact decode hash closes and total bytes beat incumbent"
    ),
    "ProjectableGeometryTopology": (
        "close iff mass_delta_q == 0 and horizon_hash matches and nan0_flag == 0"
    ),
    "CognitiveLoadField": (
        "L_total = C_domain * response_family(S; theta) * phi_gain * B_gate * overflow_gate"
    ),
    "CadForceProbeReceipt": (
        "sum_j q_ij * (x_i - x_j) + p_i = 0; residual must stay under declared tolerance"
    ),
    "LogogramProjection": (
        "logogram_cell -> canonical_hash -> glyph_payload -> projection_lane; "
        "admit iff cell hash, payload bound, substitution receipt, and regime guard close"
    ),
    "HoldForUnlawfulOrUnderspecifiedShape": (
        "HOLD iff projection, decoder, witness, scale, or residual accounting is missing"
    ),
}

KIND_SHAPE_PRIORS = {
    "compression_route_prior": "SignalShapedRouteCompiler",
    "geometry_topology_receipt": "ProjectableGeometryTopology",
    "cognitive_field_receipt": "CognitiveLoadField",
    "cad_force_receipt": "CadForceProbeReceipt",
    "logogram_projection": "LogogramProjection",
    "negative_control": "HoldForUnlawfulOrUnderspecifiedShape",
}


@dataclass(frozen=True)
class RRCObject:
    object_id: str
    label: str
    kind: str
    payload: str
    source_path: str | None = None


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(REPO)),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def keyword_score(text: str, keywords: list[str]) -> float:
    lowered = text.lower()
    if not keywords:
        return 0.0
    hits = sum(1 for word in keywords if word.lower() in lowered)
    return hits / len(keywords)


def text_payload(path: str) -> str:
    p = REPO / path
    if not p.exists():
        return ""
    data = p.read_text(encoding="utf-8", errors="replace")
    return data[:12000]


def build_objects() -> list[RRCObject]:
    return [
        RRCObject(
            object_id="rrc_obj_signal_route_compiler",
            label="Compression Signal Shaping Synthesis",
            kind="compression_route_prior",
            source_path="docs/compression_signal_shaping_synthesis.md",
            payload=text_payload("docs/compression_signal_shaping_synthesis.md"),
        ),
        RRCObject(
            object_id="rrc_obj_projectable_geometry",
            label="Projectable Geometry Topology Receipt",
            kind="geometry_topology_receipt",
            source_path="4-Infrastructure/shim/projectable_geometry_topology_model_receipt.json",
            payload=text_payload("4-Infrastructure/shim/projectable_geometry_topology_model_receipt.json"),
        ),
        RRCObject(
            object_id="rrc_obj_cognitive_load",
            label="Connectome Protective Cognitive Load Receipt",
            kind="cognitive_field_receipt",
            source_path="4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json",
            payload=text_payload("4-Infrastructure/shim/connectome_protective_cognitive_load_reweighting_receipt.json"),
        ),
        RRCObject(
            object_id="rrc_obj_cad_force_probe",
            label="CAD Force Probe Experiment Matrix Receipt",
            kind="cad_force_receipt",
            source_path="4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json",
            payload=text_payload("4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json"),
        ),
        RRCObject(
            object_id="rrc_obj_underspecified",
            label="Underspecified raw object negative control",
            kind="negative_control",
            payload="raw object with no declared projection, witness, decoder, residual, or scale band",
        ),
    ]


def project_to_manifold(obj: RRCObject) -> dict[str, float]:
    text = obj.payload
    size = max(1, len(text.encode("utf-8")))
    unique_chars = len(set(text)) if text else 0
    entropy_proxy = clamp01(unique_chars / 96.0)
    json_like = 1.0 if text.lstrip().startswith(("{", "[")) else 0.0
    source_declared = 1.0 if obj.source_path else 0.0

    projection_terms = ["projection", "manifold", "phi_signal", "coordinate", "shape"]
    decoder_terms = ["decode", "decoder", "rehydration", "residual", "bytes"]
    witness_terms = ["receipt", "witness", "hash", "sha256", "proof"]
    scale_terms = ["scale", "lambda", "threshold", "tolerance", "budget"]
    geometry_terms = ["geometry", "topology", "cad", "force", "load", "manifold", "horizon"]
    compression_terms = ["compression", "codec", "bytes", "route", "hutter", "wiki8"]
    field_terms = ["field", "energy", "load", "gate", "overflow", "force", "equilibrium"]
    control_terms = ["negative control", "baseline", "fail", "hold", "invalid"]

    projection_declared = clamp01(max(source_declared, keyword_score(text, projection_terms)))
    decoder_declared = clamp01(keyword_score(text, decoder_terms))
    witness_declared = clamp01(keyword_score(text, witness_terms))
    scale_band_declared = clamp01(keyword_score(text, scale_terms))
    if obj.kind == "logogram_projection" and (
        "surface_payload_len" in text
        and "bounded_glyph_payload_16_bytes" in text
        and "scale_band_declared" in text
    ):
        scale_band_declared = max(scale_band_declared, 0.80)
    negative_control_strength = clamp01(keyword_score(text, control_terms))
    receipt_density = clamp01((text.lower().count("receipt") + text.lower().count("hash")) / 18.0)

    residual_risk = clamp01(
        1.0
        - (
            0.20 * projection_declared
            + 0.20 * decoder_declared
            + 0.25 * witness_declared
            + 0.15 * scale_band_declared
            + 0.20 * negative_control_strength
        )
    )
    shape_closure = clamp01(
        0.30 * projection_declared
        + 0.25 * decoder_declared
        + 0.25 * witness_declared
        + 0.20 * scale_band_declared
    )

    hardware_affinity = clamp01(keyword_score(text, ["fpga", "hardware", "cad", "slicer", "uart", "lean"]))
    history_depth = clamp01(keyword_score(text, ["history", "recursive", "fractional", "memory", "curriculum"]))

    return {
        "semantic_entropy": entropy_proxy,
        "geometric_mass": clamp01(keyword_score(text, geometry_terms) + (0.20 if obj.kind.startswith("geometry") else 0.0)),
        "compression_pressure": clamp01(keyword_score(text, compression_terms) + (0.20 if "compression" in obj.kind else 0.0)),
        "topology_torsion": clamp01(keyword_score(text, ["torsion", "contradiction", "nan0", "hold", "unlawful"])),
        "receipt_density": receipt_density,
        "field_energy": clamp01(keyword_score(text, field_terms)),
        "hardware_affinity": hardware_affinity,
        "proof_readiness": clamp01((witness_declared + keyword_score(text, ["lean", "theorem", "native_decide", "proof"])) / 2.0),
        "residual_risk": residual_risk,
        "shape_closure": shape_closure,
        "history_depth": history_depth,
        "negative_control_strength": negative_control_strength,
        "projection_declared": projection_declared,
        "decoder_declared": decoder_declared,
        "witness_declared": witness_declared,
        "scale_band_declared": scale_band_declared,
    } | ({"_payload_bytes": float(size), "_json_like": json_like})


def manifold_distance(a: dict[str, float], b: dict[str, float]) -> float:
    total = 0.0
    for axis in MANIFOLD_AXES:
        total += (a.get(axis, 0.0) - b.get(axis, 0.0)) ** 2
    return math.sqrt(total / len(MANIFOLD_AXES))


def nearest_lawful_shape(coords: dict[str, float], kind: str) -> dict[str, Any]:
    kind_prior = KIND_SHAPE_PRIORS.get(kind)
    scored = [
        {
            "shape": shape,
            "distance": max(
                0.0,
                manifold_distance(coords, prototype)
                - (0.18 if shape == kind_prior else 0.0),
            ),
            "raw_distance": manifold_distance(coords, prototype),
            "kind_prior_bonus": 0.18 if shape == kind_prior else 0.0,
        }
        for shape, prototype in LAW_SHAPE_PROTOTYPES.items()
    ]
    scored.sort(key=lambda item: item["distance"])
    best = scored[0]
    return {
        "shape": best["shape"],
        "distance": round(best["distance"], 6),
        "declared_kind": kind,
        "kind_prior_shape": kind_prior,
        "alternates": scored[1:4],
    }


def type_witness(obj: RRCObject, coords: dict[str, float], shape: str, distance: float) -> dict[str, Any]:
    required_axes = [
        "projection_declared",
        "witness_declared",
        "scale_band_declared",
    ]
    if shape == "SignalShapedRouteCompiler":
        required_axes.append("decoder_declared")
    if shape in {"ProjectableGeometryTopology", "CadForceProbeReceipt"}:
        required_axes.extend(["shape_closure", "negative_control_strength"])

    missing = [axis for axis in required_axes if coords.get(axis, 0.0) < 0.35]
    status = "HOLD" if missing or shape == "HoldForUnlawfulOrUnderspecifiedShape" else "CANDIDATE"
    if distance > 0.55:
        status = "HOLD"
        if "nearest_shape_distance" not in missing:
            missing.append("nearest_shape_distance")

    witness_payload = {
        "object_id": obj.object_id,
        "shape": shape,
        "status": status,
        "required_axes": required_axes,
        "missing_or_weak_axes": missing,
        "lean_boundary": "declared_not_proved",
        "conservative_synthesis": status != "CANDIDATE",
    }
    return witness_payload | {"witness_hash": sha256_text(stable_json(witness_payload))}


def compile_object(obj: RRCObject) -> dict[str, Any]:
    coords = project_to_manifold(obj)
    nearest = nearest_lawful_shape(coords, obj.kind)
    witness = type_witness(obj, coords, nearest["shape"], float(nearest["distance"]))
    field_equation = FIELD_EQUATIONS[nearest["shape"]]
    compiled = {
        "object": {
            "object_id": obj.object_id,
            "label": obj.label,
            "kind": obj.kind,
            "source_path": obj.source_path,
            "payload_sha256": sha256_text(obj.payload),
            "payload_bytes_sampled": len(obj.payload.encode("utf-8")),
        },
        "pipeline": [
            "object",
            "manifold_projection",
            "nearest_lawful_shape",
            "type_witness",
            "field_equation",
            "invariant_receipt",
        ],
        "manifold_projection": {
            "axes": MANIFOLD_AXES,
            "coordinates": {axis: round(coords[axis], 6) for axis in MANIFOLD_AXES},
        },
        "nearest_lawful_shape": nearest,
        "type_witness": witness,
        "field_equation": field_equation,
    }
    compiled["invariant_receipt"] = {
        "schema": "rrc.object_receipt.v1",
        "object_id": obj.object_id,
        "shape": nearest["shape"],
        "status": witness["status"],
        "receipt_hash": sha256_text(stable_json(compiled)),
    }
    return compiled


def build_receipt() -> dict[str, Any]:
    sources = [file_digest(REPO / rel) for rel in SOURCE_ARTIFACTS if (REPO / rel).exists()]
    objects = build_objects()
    compiled_objects = [compile_object(obj) for obj in objects]
    receipt: dict[str, Any] = {
        "schema": "rainbow_raccoon_compiler_integration_v1",
        "claim_state": "integration_shim_not_formal_proof",
        "source_artifacts": sources,
        "compiler_name": "Rainbow Raccoon Compiler",
        "compiler_abbrev": "RRC",
        "primary_read": (
            "RRC becomes the type-checking layer for the signal-shaped route compiler: "
            "objects are projected into a named manifold vector, matched to lawful "
            "shape prototypes, assigned conservative type witnesses, and emitted as "
            "hash-stable invariant receipts."
        ),
        "pipeline": [
            {
                "step": "object",
                "meaning": "raw object, receipt, source file, model state, or probe record",
            },
            {
                "step": "manifold_projection",
                "meaning": "map object into a 16-axis semantic/geometric/compression phase vector",
            },
            {
                "step": "nearest_lawful_shape",
                "meaning": "choose closest declared type-shape prototype under normalized distance",
            },
            {
                "step": "type_witness",
                "meaning": "emit CANDIDATE or HOLD witness; Lean status is explicit",
            },
            {
                "step": "field_equation",
                "meaning": "attach behavior equation for the selected shape",
            },
            {
                "step": "invariant_receipt",
                "meaning": "hash-stable receipt for replay and audit",
            },
        ],
        "manifold_axes": MANIFOLD_AXES,
        "lawful_shape_prototypes": LAW_SHAPE_PROTOTYPES,
        "field_equations": FIELD_EQUATIONS,
        "compiled_objects": compiled_objects,
        "promotion_rules": [
            "CANDIDATE is not a Lean proof; it is only admissible for next-stage proving.",
            "HOLD is emitted when projection, witness, decoder, residual, or scale is weak.",
            "No object may be promoted as lawful without a replayable invariant receipt.",
            "Compression gain must still count residual, witness, decoder, sidecar, and container bytes.",
            "Geometry or force claims require calibrated physical measurement receipts.",
        ],
        "next_integration_steps": [
            "Add a Lean RRCShape enum and witness-gate theorem surface.",
            "Wire RRC classifications into the compression route classifier from E1/E2.",
            "Use RRC HOLD status as a fail-closed gate for semantic tokenbook merges.",
            "Map CAD force-probe receipts through RRC before four-force geometry claims.",
        ],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = []
    for compiled in receipt["compiled_objects"]:
        rows.append(
            {
                "prompt": (
                    "Classify this object with the Rainbow Raccoon Compiler pipeline: "
                    f"{compiled['object']['label']}"
                ),
                "completion": {
                    "shape": compiled["nearest_lawful_shape"]["shape"],
                    "status": compiled["type_witness"]["status"],
                    "field_equation": compiled["field_equation"],
                    "receipt_hash": compiled["invariant_receipt"]["receipt_hash"],
                },
            }
        )
    CURRICULUM.write_text(
        "\n".join(stable_json(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_curriculum(receipt)
    print(
        json.dumps(
            {
                "receipt": str(OUT.relative_to(REPO)),
                "curriculum": str(CURRICULUM.relative_to(REPO)),
                "receipt_hash": receipt["receipt_hash"],
                "compiled_object_count": len(receipt["compiled_objects"]),
                "candidate_count": sum(
                    1
                    for obj in receipt["compiled_objects"]
                    if obj["type_witness"]["status"] == "CANDIDATE"
                ),
                "hold_count": sum(
                    1
                    for obj in receipt["compiled_objects"]
                    if obj["type_witness"]["status"] == "HOLD"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
