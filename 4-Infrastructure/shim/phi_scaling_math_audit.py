#!/usr/bin/env python3
"""Numerical audit for the Φ-scaling transfold equations."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def stable_hash(payload: dict[str, Any]) -> str:
    stable = {k: v for k, v in payload.items() if k != "receipt_hash"}
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    lambda_phi = phi**2
    fractal_dimension = math.log(2.0) / math.log(phi)
    k_b_ev_per_k = 8.617333262e-5

    temperatures = {
        "room_298K": 298.0,
        "ltee_310K": 310.0,
    }
    barriers_ev = [0.05, 0.1, 0.5, 1.0, 10.0]
    boltzmann = {}
    for label, temp in temperatures.items():
        kT = k_b_ev_per_k * temp
        boltzmann[label] = {
            "kT_eV": kT,
            "suppression_by_barrier_eV": {
                str(barrier): math.exp(-barrier / kT) for barrier in barriers_ev
            },
        }

    receipt: dict[str, Any] = {
        "runner": "phi_scaling_math_audit.py",
        "constants": {
            "phi": phi,
            "lambda_phi_phi_squared": lambda_phi,
            "fractal_dimension_log2_over_logphi": fractal_dimension,
            "phi_to_fractal_dimension": phi**fractal_dimension,
            "phi_squared_to_fractal_dimension": lambda_phi**fractal_dimension,
            "phi_to_6": phi**6,
            "thirty_phi_to_6": 30.0 * phi**6,
        },
        "boltzmann_gate_audit": boltzmann,
        "corrections": [
            "Phi^1.44 is approximately 2 when Phi means the golden ratio.",
            "(Phi^2)^1.44 is approximately 4 when Phi^2 is the hierarchy scale factor.",
            "The previous approximate 3.5 constant mixed notation and is not retained.",
            "Raw exp(-E_bind/kT) with chemical-scale binding energies suppresses too strongly for direct phenotype amplitude.",
            "Use exp(-gamma * DeltaE_eff/kT) as a route barrier or prune gate.",
            "Drake-rule mutation scaling should preserve inverse genome-size direction for per-site mutation rates.",
            "500 generations is near 30 * phi^6 but is not derived as a Nyquist rate.",
        ],
        "claim_boundary": (
            "This is a numerical audit of local equations. It does not validate "
            "the biological, physical, compression, or FPGA claims."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)

    out = Path(__file__).with_name("phi_scaling_math_audit_receipt.json")
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt["constants"], indent=2, sort_keys=True))
    print(f"receipt: {out}")
    print(f"receipt_hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
