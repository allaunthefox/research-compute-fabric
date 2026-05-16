#!/usr/bin/env python3
"""FAMM Semantic Mass Route Plow.

This runner welds Semantic Mass Numbers directly into FAMM routing.

It accepts:
  - typed semantic-mass lane samples,
  - route candidates with distance/scar/invariant/cost features,
  - optional CFD residual lanes,
  - optional external Hessian and Z-domain receipts,

and emits:
  - a semantic mass stream,
  - Z-domain recurrence/pole diagnosis,
  - route rankings,
  - residual seal recommendation,
  - closure recommendation,
  - a receipt hash.

Boundary:
  This is a computational routing witness. It is not proof and does not replace
  exact Lean/Fraction/OISC receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def weighted_mass(sample: dict[str, Any], weights: dict[str, float]) -> float:
    lanes = sample.get("lanes", {})
    return float(sum(float(weights.get(k, 0.0)) * float(v) for k, v in lanes.items()))


def build_mass_stream(config: dict[str, Any]) -> list[float]:
    weights = config["lane_weights"]
    return [weighted_mass(sample, weights) for sample in config["semantic_mass_samples"]]


def fit_ar(sequence: np.ndarray, order: int) -> tuple[np.ndarray, np.ndarray, float]:
    if order < 1:
        raise ValueError("ar_order must be >= 1")
    if len(sequence) <= order + 1:
        raise ValueError("semantic_mass_sequence too short for requested ar_order")

    y = sequence[order:]
    x_cols = [
        sequence[order - i - 1 : len(sequence) - i - 1]
        for i in range(order)
    ]
    X = np.column_stack(x_cols)
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coeffs
    residual = y - pred
    rmse = float(np.sqrt(np.mean(residual**2)))
    return coeffs, residual, rmse


def ar_poles(coeffs: np.ndarray) -> np.ndarray:
    # mu[k] = a1 mu[k-1] + ... + ap mu[k-p]
    # lambda^p - a1 lambda^(p-1) - ... - ap = 0
    return np.roots(np.concatenate([[1.0], -coeffs]))


def z_diagnosis(poles: np.ndarray, residual_rmse: float, cfg: dict[str, Any]) -> dict[str, Any]:
    pole_abs = np.abs(poles)
    max_abs = float(np.max(pole_abs)) if len(pole_abs) else 0.0
    stable_radius = float(cfg.get("stable_radius", 1.0))
    near_unit_tol = float(cfg.get("near_unit_tol", 0.05))
    residual_rmse_max = float(cfg.get("residual_rmse_max", 0.10))

    if max_abs >= stable_radius:
        route = "closure_or_quarantine"
        reason = "pole outside admissible stable ROC"
    elif np.any(np.abs(pole_abs - 1.0) <= near_unit_tol):
        route = "long_memory_delta_mem"
        reason = "pole near unit circle indicates long-memory semantic mass"
    elif residual_rmse <= residual_rmse_max:
        route = "carry_recurrence_seal_residual"
        reason = "stable recurrence with bounded residual"
    else:
        route = "increase_order_or_seal_residual"
        reason = "stable but recurrence residual exceeds bound"

    return {
        "route": route,
        "reason": reason,
        "max_abs_pole": max_abs,
        "pole_abs": [float(x) for x in pole_abs.tolist()],
        "residual_rmse": residual_rmse,
    }


def load_optional_json(path_or_obj: Any) -> dict[str, Any] | None:
    if path_or_obj is None:
        return None
    if isinstance(path_or_obj, dict):
        return path_or_obj
    p = Path(path_or_obj)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def hessian_modifier(candidate: dict[str, Any], hessian_receipt: dict[str, Any] | None) -> float:
    if not hessian_receipt:
        return 0.0

    decision = hessian_receipt.get("route_decision", {})
    route = decision.get("route", "")
    scar = float(candidate.get("scar", 0.0))
    cost = float(candidate.get("cost", 0.0))
    invariant = float(candidate.get("invariant_overlap", 0.0))

    if route == "probe_saddle_scar":
        return 0.35 * scar
    if route == "protect_or_seal_stiff_invariant":
        return 0.35 * invariant - 0.25 * cost
    if route == "press_flat_gauge":
        return 0.35 * (1.0 - cost)
    if route == "seal_high_total_curvature":
        return -0.50 * cost
    return 0.0


def z_modifier(z_diag: dict[str, Any], candidate: dict[str, Any]) -> float:
    route = z_diag.get("route", "")
    scar = float(candidate.get("scar", 0.0))
    invariant = float(candidate.get("invariant_overlap", 0.0))
    cost = float(candidate.get("cost", 0.0))

    if route == "carry_recurrence_seal_residual":
        return 0.25 * invariant - 0.10 * cost
    if route == "long_memory_delta_mem":
        return 0.20 * invariant - 0.05 * scar
    if route == "closure_or_quarantine":
        return -0.35 * cost - 0.25 * scar
    if route == "increase_order_or_seal_residual":
        return -0.15 * cost
    return 0.0


def rank_routes(
    candidates: list[dict[str, Any]],
    z_diag: dict[str, Any],
    hessian_receipt: dict[str, Any] | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    alpha = float(cfg.get("alpha_distance", 1.0))
    beta = float(cfg.get("beta_scar", 1.0))
    gamma = float(cfg.get("gamma_invariant", 1.0))
    eta = float(cfg.get("eta_cost", 1.0))
    mass_gain = float(cfg.get("mass_gain", 0.5))

    scored = []
    for c in candidates:
        distance = float(c.get("distance", 0.0))
        scar = float(c.get("scar", 0.0))
        invariant = float(c.get("invariant_overlap", 0.0))
        cost = float(c.get("cost", 0.0))
        prior = float(c.get("prior", 0.0))
        mass = float(c.get("semantic_mass", 0.0))

        logit = (
            prior
            + mass_gain * mass
            - alpha * distance
            - beta * scar
            + gamma * invariant
            - eta * cost
            + z_modifier(z_diag, c)
            + hessian_modifier(c, hessian_receipt)
        )
        scored.append({**c, "route_logit": logit})

    max_logit = max((r["route_logit"] for r in scored), default=0.0)
    denom = sum(math.exp(r["route_logit"] - max_logit) for r in scored) or 1.0
    for r in scored:
        r["route_probability"] = math.exp(r["route_logit"] - max_logit) / denom

    return sorted(scored, key=lambda r: r["route_probability"], reverse=True)


def closure_recommendation(z_diag: dict[str, Any], ranked: list[dict[str, Any]]) -> dict[str, Any]:
    if z_diag["route"] == "closure_or_quarantine":
        return {
            "needed": True,
            "reason": "unstable Z-domain pole suggests missing boundary, bad CFL-like setting, or invalid route",
        }
    if ranked and ranked[0].get("scar", 0.0) >= 0.75:
        return {
            "needed": True,
            "reason": "top route is scar-heavy; test whether residual is a boundary-closure artifact",
        }
    return {"needed": False, "reason": "no immediate closure trigger"}


def run(config: dict[str, Any]) -> dict[str, Any]:
    mass_stream = np.array(build_mass_stream(config), dtype=float)
    ar_order = int(config.get("z_domain", {}).get("ar_order", 3))
    coeffs, residual, rmse = fit_ar(mass_stream, ar_order)
    poles = ar_poles(coeffs)
    z_diag = z_diagnosis(poles, rmse, config.get("z_domain", {}).get("thresholds", {}))

    hessian_receipt = load_optional_json(config.get("hessian_receipt"))

    candidates = config.get("route_candidates", [])
    final_mass = float(mass_stream[-1])
    candidates = [
        {**c, "semantic_mass": float(c.get("semantic_mass", final_mass))}
        for c in candidates
    ]
    ranked = rank_routes(
        candidates,
        z_diag=z_diag,
        hessian_receipt=hessian_receipt,
        cfg=config.get("ranking", {}),
    )

    closure = closure_recommendation(z_diag, ranked)
    residual_max = float(config.get("z_domain", {}).get("thresholds", {}).get("residual_rmse_max", 0.10))
    residual_seal = {
        "seal": bool(rmse <= residual_max),
        "reason": (
            "bounded recurrence residual; seal instead of rescan"
            if rmse <= residual_max
            else "residual above bound; increase order, test closure, or store explicit residual"
        ),
        "rmse": rmse,
    }

    receipt = {
        "receipt_type": "famm_semantic_mass_route_plow_receipt",
        "schema_version": "0.1.0",
        "basis_layers": [
            "SEMANTIC_MASS",
            "Z_DOMAIN_GATE",
            "DELTA_MEM",
            "HESSIAN_EIGEN",
            "E_TAIL_BOUND",
            "SYSTEM_CLOSURE",
        ],
        "mass_stream": {
            "length": int(len(mass_stream)),
            "sha256": sha256_json([float(x) for x in mass_stream.tolist()]),
            "last": float(mass_stream[-1]),
            "mean": float(np.mean(mass_stream)),
        },
        "z_domain": {
            "ar_order": ar_order,
            "coefficients": [float(x) for x in coeffs.tolist()],
            "poles": [
                {"re": float(p.real), "im": float(p.imag), "abs": float(abs(p))}
                for p in poles
            ],
            "residual_sha256": sha256_json([float(x) for x in residual.tolist()]),
            "diagnosis": z_diag,
        },
        "ranked_routes": ranked,
        "closure_recommendation": closure,
        "residual_seal": residual_seal,
        "no_drift_boundary": (
            "This receipt ranks routes and accelerates search. It is not theorem proof "
            "and does not replace exact receipts."
        ),
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = run(config)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    top = receipt["ranked_routes"][0] if receipt["ranked_routes"] else None
    print(f"Wrote {out_path}")
    print(f"Z route: {receipt['z_domain']['diagnosis']['route']} — {receipt['z_domain']['diagnosis']['reason']}")
    if top:
        print(f"Top route: {top.get('route_id')} p={top['route_probability']:.4f}")
    print(f"Closure: {receipt['closure_recommendation']['needed']} — {receipt['closure_recommendation']['reason']}")
    print(f"Residual seal: {receipt['residual_seal']['seal']} — {receipt['residual_seal']['reason']}")
    print(f"Receipt SHA-256: {receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
