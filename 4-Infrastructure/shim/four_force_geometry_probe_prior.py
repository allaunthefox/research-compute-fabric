#!/usr/bin/env python3
"""Receipt for using the Merkle-tensegrity lattice as a four-force probe geometry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
SOURCE = SHIM / "merkle_tensegrity_load_equation_receipt.json"
OUT = SHIM / "four_force_geometry_probe_prior_receipt.json"
CURRICULUM = SHIM / "four_force_geometry_probe_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    receipt: dict[str, Any] = {
        "schema": "four_force_geometry_probe_prior_v1",
        "source_receipt": str(SOURCE.relative_to(REPO)),
        "source_receipt_hash": source["receipt_hash"],
        "source_merkle_root": source["merkle"]["root"],
        "primary_read": (
            "Use the braced Merkle-tensegrity cube as a probe geometry for force "
            "separation. Gravity is a direct external load. Electromagnetism governs "
            "material bonding, thermal response, sensing, and print actuation. Strong "
            "interaction appears only as a material binding baseline at this scale. Weak "
            "interaction appears as a radiation/transmutation boundary, not a printable "
            "load actuator."
        ),
        "four_force_mapping": {
            "gravity": {
                "active_in_harness": True,
                "equation_slot": "p_i^G = [0, 0, m_i g]",
                "geometry_role": "external body load and support reaction driver",
                "measurable_proxy": ["mass_per_node", "gravity", "support_reactions", "residual_norm_l2"],
                "print_control_status": "directly modeled as load",
            },
            "electromagnetic": {
                "active_in_harness": "implicit",
                "equation_slot": "K_material, thermal_window, bonding_energy, sensor_field",
                "geometry_role": "stiffness, adhesion, heat flow, actuator/sensor coupling",
                "measurable_proxy": ["material_batch", "temperature", "extrusion/flow", "conductivity", "sensor_digest"],
                "print_control_status": "dominant real-world print/material force but not yet solved in toy harness",
            },
            "strong": {
                "active_in_harness": False,
                "equation_slot": "E_binding_material_baseline",
                "geometry_role": "nuclear binding baseline behind material mass and atomic stability",
                "measurable_proxy": ["material isotope/specification only if relevant"],
                "print_control_status": "not a geometry control knob for ordinary 3D printing",
            },
            "weak": {
                "active_in_harness": False,
                "equation_slot": "R_decay_or_radiation_guard",
                "geometry_role": "radioactive decay/transmutation boundary condition",
                "measurable_proxy": ["radiation/isotope safety status only if relevant"],
                "print_control_status": "not a load actuator; safety guard only",
            },
        },
        "probe_state_16d": [
            "x",
            "y",
            "z",
            "mass_density",
            "gravity_load_z",
            "lateral_load_x",
            "lateral_load_y",
            "edge_force_density_q",
            "support_reaction",
            "print_density_rho",
            "em_stiffness_or_thermal_state",
            "material_binding_baseline",
            "radiation_decay_guard",
            "equilibrium_residual",
            "merkle_phase_commitment",
            "closure_margin",
        ],
        "probe_equations": {
            "force_sum": "p_i = p_i^G + p_i^EM + p_i^strong_baseline + p_i^weak_guard",
            "gravity_load": "p_i^G = [0, 0, m_i g]",
            "mechanical_closure": "sum_j q_ij(x_i - x_j) + p_i^G + r_i + p_i^EM ~= 0",
            "em_material_placeholder": "p_i^EM := thermal/material/sensor correction term pending calibration",
            "strong_baseline": "p_i^strong_baseline := 0 at macro geometry scale; enters material constants only",
            "weak_guard": "p_i^weak_guard := 0 unless radioactive/transmutation boundary is active",
            "closure_margin": "margin = epsilon_mech - ||R_mech||_2",
            "commitment": "M_root = MerkleRoot(H(node/edge/support/force records))",
        },
        "what_it_says_now": [
            "the current toy harness is mostly a gravity-plus-mechanics probe",
            "the bracing result shows geometry controls whether lateral disturbance can close",
            "EM must be the next real extension because printability is material/thermal/bonding dominated",
            "strong and weak should remain material/safety metadata unless the experiment involves nuclear/radiological regimes",
            "the 16D lift is useful as a typed probe-state vector, not as sixteen physical spatial dimensions",
        ],
        "next_probe_steps": [
            "add calibrated material stiffness and thermal expansion terms as the EM lane",
            "add material batch metadata for binding baseline rather than pretending to actuate strong force",
            "add radiation/isotope safety guard as a weak-force boundary if relevant",
            "compare residual and Merkle roots across gravity-only, gravity+EM, and failed unbraced geometries",
        ],
        "failure_rules": [
            "treating all four forces as equally active in a desktop 3D print -> overclaim",
            "using strong/weak forces as geometry knobs without nuclear/radiological model -> invalid",
            "calling Merkle commitment a force measurement -> invalid",
            "adding 16D axes without typed semantics -> bookkeeping noise",
            "EM material lane omitted in real print safety claim -> hold",
        ],
        "claim_boundary": (
            "This is a probe-state prior for separating force roles in a toy lattice. "
            "It is not a unified-field result, not a structural safety certificate, and "
            "not evidence that strong or weak interactions are controllable by this geometry."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_force_lane",
            "input": "gravity, electromagnetism, strong, or weak term in lattice probe",
            "target": "external load, material/thermal lane, binding baseline, or safety guard",
        },
        {
            "task": "build_16d_probe_state",
            "input": "node geometry, load, stress, material, residual, Merkle data",
            "target": "typed 16D probe vector with no untyped axes",
        },
        {
            "task": "reject_force_overclaim",
            "input": "claim that toy print lattice probes all four forces directly",
            "target": "gravity direct, EM next extension, strong/weak metadata or guard only",
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
        "source_receipt_hash": receipt["source_receipt_hash"],
        "probe_state_dimensions": len(receipt["probe_state_16d"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
