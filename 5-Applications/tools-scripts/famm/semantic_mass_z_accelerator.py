#!/usr/bin/env python3
"""Semantic Mass Z-domain accelerator receipt.

Fits a simple autoregressive recurrence to a semantic mass stream and emits a
FAMM routing receipt. This is a lightweight measured shortcut: it turns
history into coefficients + state + residual seal.

The runner is intentionally small. It is not proof; it is a computational
routing witness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fit_ar(sequence: np.ndarray, order: int) -> tuple[np.ndarray, np.ndarray, float]:
    if order < 1:
        raise ValueError("order must be >= 1")
    if len(sequence) <= order + 1:
        raise ValueError("sequence too short for requested AR order")

    y = sequence[order:]
    X = np.column_stack([sequence[order - i - 1 : len(sequence) - i - 1] for i in range(order)])
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coeffs
    residual = y - pred
    rmse = float(np.sqrt(np.mean(residual**2)))
    return coeffs, residual, rmse


def route_from_poles(poles: np.ndarray, rmse: float, cfg: dict[str, Any]) -> dict[str, Any]:
    pole_abs = np.abs(poles)
    max_abs = float(np.max(pole_abs)) if len(pole_abs) else 0.0
    near_unit_tol = float(cfg.get("near_unit_tol", 0.05))
    stable_radius = float(cfg.get("stable_radius", 1.0))
    residual_max = float(cfg.get("residual_rmse_max", 0.1))

    if max_abs >= stable_radius:
        route = "closure_or_quarantine"
        reason = "pole outside admissible stable ROC"
    elif np.any(np.abs(pole_abs - 1.0) <= near_unit_tol):
        route = "long_memory_delta_mem"
        reason = "pole near unit circle indicates long semantic memory"
    elif rmse <= residual_max:
        route = "carry_recurrence_seal_residual"
        reason = "stable recurrence with bounded residual"
    else:
        route = "increase_order_or_seal_residual"
        reason = "stable but residual exceeds configured bound"

    return {
        "route": route,
        "reason": reason,
        "max_abs_pole": max_abs,
        "pole_abs": [float(x) for x in pole_abs.tolist()],
        "residual_rmse": rmse,
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    seq = np.array(config["semantic_mass_sequence"], dtype=float)
    order = int(config.get("ar_order", 4))
    coeffs, residual, rmse = fit_ar(seq, order)

    # AR recurrence: mu[k] = sum_i a_i mu[k-i]
    # Characteristic: lambda^p - a1 lambda^(p-1) - ... - ap = 0
    poly = np.concatenate([[1.0], -coeffs])
    poles = np.roots(poly)

    decision = route_from_poles(poles, rmse, config.get("route_thresholds", {}))

    receipt = {
        "receipt_type": "famm_semantic_mass_z_receipt",
        "schema_version": "0.1.0",
        "basis_layer": "MASS_Z_ACCEL",
        "ar_order": order,
        "sequence_len": int(len(seq)),
        "coefficients": [float(x) for x in coeffs.tolist()],
        "poles": [{"re": float(p.real), "im": float(p.imag), "abs": float(abs(p))} for p in poles],
        "residual": {
            "rmse": rmse,
            "samples_sha256": sha256_json([float(x) for x in residual.tolist()]),
            "max_abs": float(np.max(np.abs(residual))),
        },
        "route_decision": decision,
        "no_drift_boundary": (
            "This is a computational recurrence witness for Semantic Mass routing. "
            "It is not proof and does not replace exact receipts."
        ),
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = run(cfg)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Route: {receipt['route_decision']['route']} — {receipt['route_decision']['reason']}")
    print(f"Receipt SHA-256: {receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
