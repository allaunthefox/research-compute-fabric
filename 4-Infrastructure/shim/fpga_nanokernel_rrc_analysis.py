#!/usr/bin/env python3
"""Rainbow Raccoon Compiler analysis for FPGA/nanokernel/Verilator approach.

This script applies the Rainbow Raccoon manifold projection to the FPGA programming
approach components to identify optimization targets and map adjustments.
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
OUT = SHIM / "fpga_nanokernel_rrc_receipt.json"


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
    "FPGAHardwareLoader": {  # New shape for FPGA programming
        "semantic_entropy": 0.25,
        "geometric_mass": 0.45,
        "compression_pressure": 0.38,
        "topology_torsion": 0.28,
        "receipt_density": 0.85,
        "field_energy": 0.62,
        "hardware_affinity": 0.95,
        "proof_readiness": 0.35,
        "residual_risk": 0.42,
        "shape_closure": 0.78,
        "history_depth": 0.25,
        "negative_control_strength": 0.88,
        "projection_declared": 0.92,
        "decoder_declared": 0.88,
        "witness_declared": 0.82,
        "scale_band_declared": 0.71,
    },
    "NanokernelSurface": {  # New shape for nanokernel
        "semantic_entropy": 0.42,
        "geometric_mass": 0.35,
        "compression_pressure": 0.85,
        "topology_torsion": 0.38,
        "receipt_density": 0.72,
        "field_energy": 0.68,
        "hardware_affinity": 0.82,
        "proof_readiness": 0.48,
        "residual_risk": 0.35,
        "shape_closure": 0.85,
        "history_depth": 0.55,
        "negative_control_strength": 0.72,
        "projection_declared": 0.88,
        "decoder_declared": 0.65,
        "witness_declared": 0.78,
        "scale_band_declared": 0.58,
    },
    "VerilatorSimulation": {  # New shape for Verilator
        "semantic_entropy": 0.38,
        "geometric_mass": 0.52,
        "compression_pressure": 0.45,
        "topology_torsion": 0.32,
        "receipt_density": 0.68,
        "field_energy": 0.58,
        "hardware_affinity": 0.75,
        "proof_readiness": 0.52,
        "residual_risk": 0.28,
        "shape_closure": 0.82,
        "history_depth": 0.42,
        "negative_control_strength": 0.65,
        "projection_declared": 0.85,
        "decoder_declared": 0.72,
        "witness_declared": 0.80,
        "scale_band_declared": 0.65,
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
    "FPGAHardwareLoader": (
        "bitstream -> uart_protocol -> fpga_configuration; "
        "admit iff magic_header, length_checksum, footer_signature, and ack_sequence close"
    ),
    "NanokernelSurface": (
        "gcl_bytecode -> syscall_interface -> hardware_shim; "
        "admit iff memory_arena, swarm_coordination, lawful_loss_semantics, and triumvirate_clock close"
    ),
    "VerilatorSimulation": (
        "verilog -> cpp_model -> simulation_trace; "
        "admit iff timing_correctness, resource_constraints, testbench_coverage, and vcd_trace close"
    ),
    "HoldForUnlawfulOrUnderspecifiedShape": (
        "HOLD iff projection, decoder, witness, scale, or residual accounting is missing"
    ),
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


def build_fpga_objects() -> list[RRCObject]:
    """Build RRC objects for FPGA/nanokernel/Verilator components."""
    return [
        RRCObject(
            object_id="fpga_obj_verilog_design",
            label="Meta-Manifold Prover Verilog Design",
            kind="verilog_hardware",
            source_path="4-Infrastructure/hardware/metamanifold_prover_gowin.v",
            payload=text_payload("4-Infrastructure/hardware/metamanifold_prover_gowin.v"),
        ),
        RRCObject(
            object_id="fpga_obj_verilator_testbench",
            label="Verilator Testbench for Meta-Manifold Prover",
            kind="verilator_simulation",
            source_path="4-Infrastructure/hardware/tb_metamanifold_prover.cpp",
            payload=text_payload("4-Infrastructure/hardware/tb_metamanifold_prover.cpp"),
        ),
        RRCObject(
            object_id="fpga_obj_nanokernel_loader",
            label="Nanokernel UART FPGA Loader",
            kind="nanokernel_surface",
            source_path="4-Infrastructure/nano-kernel/fpga_uart_loader.gcl",
            payload=text_payload("4-Infrastructure/nano-kernel/fpga_uart_loader.gcl"),
        ),
        RRCObject(
            object_id="fpga_obj_simulation_results",
            label="Verilator Simulation Results",
            kind="simulation_receipt",
            source_path="6-Documentation/docs/verilator_simulation_results_2026-05-09.md",
            payload=text_payload("6-Documentation/docs/verilator_simulation_results_2026-05-09.md"),
        ),
        RRCObject(
            object_id="fpga_obj_approach_design",
            label="Nanokernel + Verilator FPGA Programming Approach",
            kind="architecture_design",
            source_path="6-Documentation/docs/nanokernel_verilator_fpga_approach_2026-05-09.md",
            payload=text_payload("6-Documentation/docs/nanokernel_verilator_fpga_approach_2026-05-09.md"),
        ),
    ]


def project_to_manifold(obj: RRCObject) -> dict[str, float]:
    """Project object onto 16-axis manifold."""
    text = obj.payload
    size = max(1, len(text.encode("utf-8")))
    unique_chars = len(set(text)) if text else 0
    entropy_proxy = clamp01(unique_chars / 96.0)
    json_like = 1.0 if text.lstrip().startswith(("{", "[")) else 0.0
    source_declared = 1.0 if obj.source_path else 0.0

    # FPGA-specific keywords
    fpga_terms = ["fpga", "verilog", "bitstream", "uart", "gowin", "tang", "hardware", "synthesis", "yosys"]
    nanokernel_terms = ["nanokernel", "gcl", "syscall", "memory_arena", "swarm", "triunvirate", "lawful_loss"]
    verilator_terms = ["verilator", "simulation", "testbench", "vcd", "trace", "cpp", "compile"]
    protocol_terms = ["uart", "protocol", "magic_header", "checksum", "ack", "footer", "bitstream"]
    verification_terms = ["test", "verify", "validate", "pass", "fail", "assertion", "coverage"]
    projection_terms = ["projection", "manifold", "coordinate", "shape", "design"]
    decoder_terms = ["decode", "decoder", "rehydration", "residual", "bytes", "protocol"]
    witness_terms = ["receipt", "witness", "hash", "sha256", "proof", "invariant"]
    scale_terms = ["scale", "lambda", "threshold", "tolerance", "budget", "bandwidth"]

    projection_declared = clamp01(max(source_declared, keyword_score(text, projection_terms)))
    decoder_declared = clamp01(keyword_score(text, decoder_terms))
    witness_declared = clamp01(keyword_score(text, witness_terms))
    scale_band_declared = clamp01(keyword_score(text, scale_terms))
    negative_control_strength = clamp01(keyword_score(text, ["negative", "control", "fail", "hold", "invalid"]))
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

    hardware_affinity = clamp01(keyword_score(text, fpga_terms + nanokernel_terms + verilator_terms))
    history_depth = clamp01(keyword_score(text, ["history", "recursive", "evolution", "curriculum", "nanokernel"]))

    return {
        "semantic_entropy": entropy_proxy,
        "geometric_mass": clamp01(keyword_score(text, ["geometry", "topology", "manifold", "fpga", "hardware"])),
        "compression_pressure": clamp01(keyword_score(text, ["compression", "codec", "bytes", "optimize", "reduce"])),
        "topology_torsion": clamp01(keyword_score(text, ["torsion", "contradiction", "nan0", "hold", "unlawful"])),
        "receipt_density": receipt_density,
        "field_energy": clamp01(keyword_score(text, ["field", "energy", "load", "gate", "equilibrium"])),
        "hardware_affinity": hardware_affinity,
        "proof_readiness": clamp01((witness_declared + keyword_score(text, ["lean", "theorem", "proof", "verify"])) / 2.0),
        "residual_risk": residual_risk,
        "shape_closure": shape_closure,
        "history_depth": history_depth,
        "negative_control_strength": negative_control_strength,
        "projection_declared": projection_declared,
        "decoder_declared": decoder_declared,
        "witness_declared": witness_declared,
        "scale_band_declared": scale_band_declared,
    }


def manifold_distance(a: dict[str, float], b: dict[str, float]) -> float:
    """Calculate Euclidean distance between manifold coordinates."""
    total = 0.0
    for axis in MANIFOLD_AXES:
        total += (a.get(axis, 0.0) - b.get(axis, 0.0)) ** 2
    return math.sqrt(total / len(MANIFOLD_AXES))


def nearest_lawful_shape(coords: dict[str, float], kind: str) -> dict[str, Any]:
    """Find nearest lawful shape prototype."""
    scored = [
        {
            "shape": shape,
            "distance": manifold_distance(coords, prototype),
            "raw_distance": manifold_distance(coords, prototype),
        }
        for shape, prototype in LAW_SHAPE_PROTOTYPES.items()
    ]
    scored.sort(key=lambda item: item["distance"])
    best = scored[0]
    return {
        "shape": best["shape"],
        "distance": round(best["distance"], 6),
        "declared_kind": kind,
        "alternates": scored[1:4],
    }


def type_witness(obj: RRCObject, coords: dict[str, float], shape: str, distance: float) -> dict[str, Any]:
    """Generate type witness for object."""
    required_axes = [
        "projection_declared",
        "witness_declared",
        "scale_band_declared",
    ]

    if shape == "FPGAHardwareLoader":
        required_axes.extend(["decoder_declared", "hardware_affinity"])
    if shape == "NanokernelSurface":
        required_axes.extend(["decoder_declared", "shape_closure", "hardware_affinity"])
    if shape == "VerilatorSimulation":
        required_axes.extend(["decoder_declared", "proof_readiness", "hardware_affinity"])

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
    """Compile object through RRC pipeline."""
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
        "schema": "rrc.fpga_object_receipt.v1",
        "object_id": obj.object_id,
        "shape": nearest["shape"],
        "status": witness["status"],
        "receipt_hash": sha256_text(stable_json(compiled)),
    }
    return compiled


def build_receipt() -> dict[str, Any]:
    """Build RRC receipt for FPGA/nanokernel approach."""
    objects = build_fpga_objects()
    compiled_objects = [compile_object(obj) for obj in objects]

    # Calculate map adjustments
    candidate_count = sum(1 for obj in compiled_objects if obj["type_witness"]["status"] == "CANDIDATE")
    hold_count = sum(1 for obj in compiled_objects if obj["type_witness"]["status"] == "HOLD")

    # Identify common missing axes
    all_missing = []
    for obj in compiled_objects:
        all_missing.extend(obj["type_witness"]["missing_or_weak_axes"])

    missing_frequency = {}
    for axis in all_missing:
        missing_frequency[axis] = missing_frequency.get(axis, 0) + 1

    # Generate map adjustment recommendations
    recommendations = []

    if missing_frequency.get("proof_readiness", 0) > 0:
        recommendations.append({
            "priority": "HIGH",
            "axis": "proof_readiness",
            "current_state": "Lean boundary: declared_not_proved",
            "adjustment": "Add Lean formal verification for Meta-Manifold Prover operations",
            "expected_improvement": "+0.15 proof_readiness score",
        })

    if missing_frequency.get("scale_band_declared", 0) > 0:
        recommendations.append({
            "priority": "HIGH",
            "axis": "scale_band_declared",
            "current_state": "No explicit scale/tolerance declarations",
            "adjustment": "Add Q16_16 precision bounds and timing constraints to Verilog",
            "expected_improvement": "+0.20 scale_band_declared score",
        })

    if missing_frequency.get("decoder_declared", 0) > 0:
        recommendations.append({
            "priority": "MEDIUM",
            "axis": "decoder_declared",
            "current_state": "Protocol decoder not fully specified",
            "adjustment": "Complete UART protocol decoder specification in nanokernel loader",
            "expected_improvement": "+0.15 decoder_declared score",
        })

    if missing_frequency.get("witness_declared", 0) > 0:
        recommendations.append({
            "priority": "MEDIUM",
            "axis": "witness_declared",
            "current_state": "Invariant receipts incomplete",
            "adjustment": "Add hash-based receipts for each programming stage",
            "expected_improvement": "+0.12 witness_declared score",
        })

    receipt: dict[str, Any] = {
        "schema": "fpga_nanokernel_rrc_analysis_v1",
        "claim_state": "integration_shim_not_formal_proof",
        "compiler_name": "Rainbow Raccoon Compiler",
        "compiler_abbrev": "RRC",
        "analysis_target": "FPGA/Nanokernel/Verilator Programming Approach",
        "primary_read": (
            "RRC analysis of FPGA programming approach identifies shape classifications "
            "and map adjustments for optimization. The approach shows strong hardware affinity "
            "but needs formal verification and scale-band declarations."
        ),
        "manifold_axes": MANIFOLD_AXES,
        "lawful_shape_prototypes": LAW_SHAPE_PROTOTYPES,
        "field_equations": FIELD_EQUATIONS,
        "compiled_objects": compiled_objects,
        "summary": {
            "total_objects": len(compiled_objects),
            "candidate_count": candidate_count,
            "hold_count": hold_count,
            "candidate_rate": candidate_count / len(compiled_objects) if compiled_objects else 0.0,
        },
        "map_adjustments": {
            "missing_axes_frequency": missing_frequency,
            "recommendations": recommendations,
            "priority_order": sorted(recommendations, key=lambda x: (
                0 if x["priority"] == "HIGH" else 1 if x["priority"] == "MEDIUM" else 2
            )),
        },
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "receipt": str(OUT.relative_to(REPO)),
                "receipt_hash": receipt["receipt_hash"],
                "compiled_object_count": len(receipt["compiled_objects"]),
                "candidate_count": receipt["summary"]["candidate_count"],
                "hold_count": receipt["summary"]["hold_count"],
                "candidate_rate": receipt["summary"]["candidate_rate"],
                "adjustment_count": len(receipt["map_adjustments"]["recommendations"]),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
