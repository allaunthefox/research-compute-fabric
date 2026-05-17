#!/usr/bin/env python3
"""Plasma Chiral Drag Witness Gate.

Computes a residual receipt for Alfvén-wave image rotation in rotating plasma.
Uses DeltaTheta_pred ≈ L * Omega / (2 * v_A).
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run(config: dict[str, Any]) -> dict[str, Any]:
    L = float(config["path_length_m"])
    v_A = float(config["alfven_speed_m_s"])
    tol = float(config.get("tolerance_rad", 0.05))

    if "omega_rad_s" in config:
        omega = float(config["omega_rad_s"])
        omega_source = "direct"
    else:
        r = float(config["radius_m"])
        B0 = float(config["magnetic_field_t"])
        dphi_dr = float(config["d_potential_dr_v_m"])
        omega = dphi_dr / (r * B0)
        omega_source = "E_cross_B_from_radial_potential"

    observed = float(config.get("observed_rotation_rad", 0.0))
    phi_per_m = 0.5 * omega / v_A
    predicted = L * phi_per_m
    residual = abs(observed - predicted)

    sign_match = True
    if observed != 0.0 and predicted != 0.0:
        sign_match = math.copysign(1.0, observed) == math.copysign(1.0, predicted)

    receipt = {
        "receipt_type": "famm_plasma_chiral_drag_witness_receipt",
        "schema_version": "0.1.0",
        "source_model": "Image rotation in plasmas, arXiv:2505.18062",
        "inputs": config,
        "derived": {
            "omega_rad_s": omega,
            "omega_source": omega_source,
            "phi_per_meter_rad_m": phi_per_m,
            "predicted_rotation_rad": predicted,
            "predicted_rotation_deg": predicted * 180.0 / math.pi,
            "observed_rotation_rad": observed,
            "observed_rotation_deg": observed * 180.0 / math.pi,
            "residual_rad": residual,
            "sign_match": sign_match,
        },
        "famm": {
            "scar_class": "PASS_CHIRAL_DRAG" if residual <= tol and sign_match else "CHIRAL_DRAG_SCAR",
            "residual": residual,
            "tolerance_rad": tol,
            "coarsening_agent": None if residual <= tol and sign_match else {
                "type": "plasma_chiral_drag_mismatch",
                "action": "scar_or_downweight_this_wave_medium_model",
                "reason": "observed image rotation does not match predicted signed torsion witness within tolerance"
            }
        },
        "packet": {
            "name": "Gamma_plasma_drag",
            "projection": "plasma_state_to_wave_image_rotation_witness",
            "invariant": "signed angular/torsion/chirality witness",
            "guard": "rotating magnetized plasma with Alfven-wave transverse image structure",
        },
        "no_drift_boundary": "This gate models Alfvén-wave image rotation in rotating magnetized plasma. It is not a universal wave-twist law or a vacuum-light claim."
    }
    receipt["receipt_hash"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = run(config)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Predicted rotation deg: {receipt['derived']['predicted_rotation_deg']}")
    print(f"Residual rad: {receipt['derived']['residual_rad']}")
    print(f"Scar class: {receipt['famm']['scar_class']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")

if __name__ == "__main__":
    main()
