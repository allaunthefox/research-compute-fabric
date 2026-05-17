#!/usr/bin/env python3
"""Experiment matrix for turning the Merkle-tensegrity CAD prior into measurements.

The point of this layer is deliberately modest: make the lattice testable by
pinning every claim to a simulated scenario, a bench measurement field, or a
hold condition.  The Merkle root is a receipt for the experiment record, not a
force sensor and not a structural safety certificate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
SOURCE_RECEIPT = SHIM / "four_force_geometry_probe_prior_receipt.json"
LOAD_HARNESS = SHIM / "merkle_tensegrity_load_equation_generator.py"
OUT = SHIM / "cad_force_probe_experiment_matrix_receipt.json"
CURRICULUM = SHIM / "cad_force_probe_experiment_matrix_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_harness_module() -> Any:
    spec = importlib.util.spec_from_file_location("merkle_tensegrity_load_equation_generator", LOAD_HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import load harness from {LOAD_HARNESS}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def scenario_args(**overrides: Any) -> argparse.Namespace:
    defaults = {
        "seed": 2519138123,
        "gravity": -9.81,
        "mass_per_node": 0.1,
        "lateral_noise_sigma": 0.05,
        "duality_coefficient": 2 ** 0.5,
        "density_midpoint": 0.25,
        "epsilon_mech": 1e-8,
        "include_face_diagonals": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def summarize_simulation(name: str, description: str, args: argparse.Namespace, harness: Any) -> dict[str, Any]:
    receipt = harness.build_receipt(args)
    return {
        "name": name,
        "description": description,
        "parameters": receipt["parameters"],
        "result": {
            "edge_count": receipt["lattice"]["edge_count"],
            "support_count": receipt["lattice"]["support_count"],
            "residual_norm_l2": receipt["results"]["residual_norm_l2"],
            "mechanically_acceptable": receipt["results"]["mechanically_acceptable"],
            "density_min": receipt["results"]["density_min"],
            "density_max": receipt["results"]["density_max"],
            "total_abs_edge_force_density": receipt["results"]["total_abs_edge_force_density"],
            "merkle_root": receipt["merkle"]["root"],
            "receipt_hash": receipt["receipt_hash"],
        },
    }


def build_simulated_scenarios(harness: Any) -> list[dict[str, Any]]:
    scenarios = [
        summarize_simulation(
            "G0_braced_static_gravity",
            "Default braced cube under gravity and small lateral disturbance.",
            scenario_args(include_face_diagonals=True, lateral_noise_sigma=0.05, mass_per_node=0.1),
            harness,
        ),
        summarize_simulation(
            "G1_gravity_only_braced",
            "Braced cube with lateral disturbance removed; isolates gravity/support closure.",
            scenario_args(include_face_diagonals=True, lateral_noise_sigma=0.0, mass_per_node=0.1),
            harness,
        ),
        summarize_simulation(
            "G2_lateral_sweep_braced_0p20",
            "Braced cube under amplified lateral disturbance; checks whether bracing still closes.",
            scenario_args(include_face_diagonals=True, lateral_noise_sigma=0.2, mass_per_node=0.1),
            harness,
        ),
        summarize_simulation(
            "G3_mass_sweep_braced_0p20kg",
            "Braced cube with doubled nodal mass; checks force-density and density-command response.",
            scenario_args(include_face_diagonals=True, lateral_noise_sigma=0.05, mass_per_node=0.2),
            harness,
        ),
        summarize_simulation(
            "NC1_unbraced_lateral_negative_control",
            "Axis-only cube under the same lateral disturbance; expected to fail residual closure.",
            scenario_args(include_face_diagonals=False, lateral_noise_sigma=0.05, mass_per_node=0.1),
            harness,
        ),
    ]
    return scenarios


def build_receipt() -> dict[str, Any]:
    source = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    harness = load_harness_module()
    simulated_scenarios = build_simulated_scenarios(harness)

    receipt: dict[str, Any] = {
        "schema": "cad_force_probe_experiment_matrix_v1",
        "source_prior": str(SOURCE_RECEIPT.relative_to(REPO)),
        "source_prior_hash": source["receipt_hash"],
        "source_merkle_root": source["source_merkle_root"],
        "primary_read": (
            "This is the most directly testable frame in the current theory stack "
            "besides biological DNA work: the object can be modeled as CAD, printed, "
            "loaded with known forces, measured with fixtures/sensors, and committed "
            "as a Merkle-verifiable experiment record."
        ),
        "why_more_testable_than_dna": {
            "cad_lattice": [
                "geometry is controlled directly",
                "loads can be set by fixture, mass, or actuator",
                "displacement and failure can be measured immediately",
                "negative controls can be printed with known bad bracing",
                "Merkle receipts can commit each geometry/load/material trace",
            ],
            "dna_frame": [
                "biological state is harder to control directly",
                "measurement loops are slower and more confounded",
                "ethical and safety constraints are far tighter",
                "latent variables dominate unless the assay is very narrow",
            ],
        },
        "simulated_scenarios": simulated_scenarios,
        "bench_experiment_matrix": [
            {
                "experiment_id": "BENCH_G0",
                "force_lane": "gravity",
                "printed_geometry": "braced cube lattice",
                "set_force": "known mass plus Earth gravity",
                "direct_measurements": ["mass_measurement", "support_reaction_if_available", "vertical_displacement_trace"],
                "expected_signal": "small closure residual and monotone displacement with added mass",
                "hold_condition": "crack, delamination, fixture slip, or displacement beyond calibrated limit",
            },
            {
                "experiment_id": "BENCH_G1",
                "force_lane": "gravity + lateral mechanical disturbance",
                "printed_geometry": "braced cube lattice",
                "set_force": "known lateral load from pulley, spring scale, or actuator",
                "direct_measurements": ["load_cell_trace", "lateral_displacement_trace", "video_marker_trace"],
                "expected_signal": "braced lattice carries lateral load with bounded displacement",
                "hold_condition": "observed lateral response diverges from calibrated model beyond epsilon_u",
            },
            {
                "experiment_id": "BENCH_NC1",
                "force_lane": "negative control",
                "printed_geometry": "axis-only unbraced cube",
                "set_force": "same lateral load as BENCH_G1",
                "direct_measurements": ["load_cell_trace", "lateral_displacement_trace", "failure_mode"],
                "expected_signal": "higher residual proxy, higher displacement, or failure relative to braced cube",
                "hold_condition": "negative control performs indistinguishably from braced design; model needs revision",
            },
            {
                "experiment_id": "BENCH_EM1",
                "force_lane": "electromagnetic material lane",
                "printed_geometry": "same braced cube across materials or print profiles",
                "set_force": "same gravity/lateral load with material, temperature, or infill varied",
                "direct_measurements": ["material_batch", "printer_profile", "temperature_trace", "stiffness_proxy"],
                "expected_signal": "material/thermal lane changes stiffness and deformation more than Merkle state alone",
                "hold_condition": "material profile omitted from any mechanical claim",
            },
            {
                "experiment_id": "BENCH_COMMIT1",
                "force_lane": "attestation",
                "printed_geometry": "same geometry record with one load or density field changed",
                "set_force": "none; data integrity perturbation",
                "direct_measurements": ["leaf_hashes", "merkle_root_before", "merkle_root_after"],
                "expected_signal": "Merkle root changes under record mutation",
                "hold_condition": "hash unchanged after semantically relevant record mutation",
            },
        ],
        "measurement_record_schema": {
            "geometry": ["cad_model_hash", "stl_hash", "node_edge_schema_hash", "support_fixture_id"],
            "print": ["printer_id", "slicer_profile_hash", "material_batch", "infill_profile", "nozzle_temperature_trace"],
            "force": ["load_fixture_id", "mass_measurement", "load_cell_trace_hash", "actuator_profile_hash"],
            "observation": [
                "dial_indicator_trace_hash",
                "camera_marker_trace_hash",
                "strain_marker_trace_hash",
                "temperature_trace_hash",
                "failure_mode",
            ],
            "model_compare": [
                "predicted_residual_norm_l2",
                "observed_displacement",
                "displacement_error",
                "stiffness_proxy",
                "calibration_gain",
                "safety_hold",
            ],
            "attestation": ["leaf_hashes", "merkle_root", "receipt_hash", "operator_signature_optional"],
        },
        "measurement_equations": {
            "force_closure_error": "e_F = ||B q + R + p||_2",
            "displacement_error": "e_u = ||u_observed - u_predicted||_2",
            "stiffness_proxy": "K_proxy = F_applied / max(delta_observed, epsilon_delta)",
            "calibration_gain": "k* = argmin_k ||u_observed - k u_predicted||_2",
            "bracing_gain": "G_brace = K_proxy(braced) / K_proxy(unbraced)",
            "attested_leaf": "leaf_i = H(stable_json(geometry, print, force, observation, model_compare))",
            "safety_hold": "hold iff e_F > epsilon_F or e_u > epsilon_u or crack/failure/fixture_slip is observed",
        },
        "claim_tests": [
            {
                "claim": "bracing matters under lateral disturbance",
                "test": "compare BENCH_G1 against BENCH_NC1",
                "pass_signal": "braced lattice has lower displacement or higher stiffness proxy than unbraced negative control",
            },
            {
                "claim": "gravity lane is directly measurable",
                "test": "mass sweep in BENCH_G0",
                "pass_signal": "observed displacement or support reaction increases monotonically with applied mass",
            },
            {
                "claim": "EM lane dominates material printability",
                "test": "material or thermal sweep in BENCH_EM1",
                "pass_signal": "same geometry/load produces materially different stiffness proxy across profiles",
            },
            {
                "claim": "Merkle commits the experiment, but does not certify mechanics",
                "test": "BENCH_COMMIT1 plus NC1",
                "pass_signal": "root changes under record mutation; failed geometry can still have a valid failure receipt",
            },
        ],
        "failure_rules": [
            "bench measurement omitted -> theory claim remains speculative",
            "negative control omitted -> bracing claim is weak",
            "Merkle root treated as load-cell evidence -> invalid",
            "EM/material metadata omitted from printability claim -> hold",
            "strong or weak interaction treated as directly actuated by desktop CAD load test -> overclaim",
            "fixture slip, print delamination, or sensor saturation ignored -> invalid measurement",
            "safety_hold true but result reported as pass -> invalid receipt",
        ],
        "claim_boundary": (
            "This receipt defines an experiment matrix and simulated priors for a CAD-load "
            "probe. It does not certify a printed object, prove a unified force theory, or "
            "replace finite-element analysis, slicer calibration, or physical safety testing."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "choose_direct_measurement",
            "input": "gravity, lateral, EM/material, or attestation lane",
            "target": "mass/load-cell/displacement/material-trace/Merkle-root measurement",
        },
        {
            "task": "reject_untestable_force_claim",
            "input": "claim about four forces from desktop CAD print",
            "target": "gravity direct, EM material lane, strong/weak guard or baseline only",
        },
        {
            "task": "apply_negative_control",
            "input": "braced cube result without unbraced comparison",
            "target": "run or cite unbraced lateral negative control",
        },
        {
            "task": "build_bench_receipt",
            "input": "geometry, print, force, observation, model compare",
            "target": "stable JSON leaf records plus Merkle root and hold flags",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps({
        "receipt": str(OUT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "scenario_count": len(receipt["simulated_scenarios"]),
        "bench_experiment_count": len(receipt["bench_experiment_matrix"]),
        "source_prior_hash": receipt["source_prior_hash"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
