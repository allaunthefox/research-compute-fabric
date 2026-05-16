#!/usr/bin/env python3
"""FAMM empirical Hessian receipt runner.

This is a delivery shim around `hessian-eigenthings`; it does not implement
Lanczos/Hutch++/SLQ itself. It turns a matrix-free curvature operator into a
receipt JSON that FAMM can use for route decisions.

Supported operator sources:
  - kind="diagonal": JSON list of diagonal entries.
  - kind="dense_npy": path to a .npy dense symmetric matrix.
  - kind="torch_plugin": dotted factory path returning a CurvatureOperator.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

try:
    from hessian_eigenthings import LambdaOperator, lanczos, trace, spectral_density
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency `hessian-eigenthings`. Install with:\n"
        "  pip install hessian-eigenthings\n"
        f"Original import error: {exc}"
    )


@dataclass(frozen=True)
class RouteThresholds:
    lambda_max: float = 10.0
    negative_eigenvalue_tol: float = -1.0e-6
    flat_abs_tol: float = 1.0e-5
    flat_ratio_min: float = 0.35
    trace_max: float | None = None


def _sha256_jsonable(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _tensor_to_list(x: torch.Tensor) -> list[float]:
    return [float(v) for v in x.detach().cpu().reshape(-1).tolist()]


def load_operator(config: dict[str, Any]):
    op_cfg = config["operator"]
    kind = op_cfg["kind"]
    dtype = getattr(torch, op_cfg.get("dtype", "float64"))
    device = torch.device(op_cfg.get("device", "cpu"))

    if kind == "diagonal":
        diag = torch.tensor(op_cfg["diagonal"], dtype=dtype, device=device)

        def matvec(v: torch.Tensor) -> torch.Tensor:
            return diag * v

        return LambdaOperator(matvec, size=diag.numel(), device=device, dtype=dtype)

    if kind == "dense_npy":
        import numpy as np

        matrix = torch.tensor(np.load(op_cfg["path"]), dtype=dtype, device=device)
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("dense_npy operator must be a square matrix")

        def matvec(v: torch.Tensor) -> torch.Tensor:
            return matrix @ v

        return LambdaOperator(matvec, size=matrix.shape[0], device=device, dtype=dtype)

    if kind == "torch_plugin":
        dotted = op_cfg["factory"]
        mod_name, func_name = dotted.rsplit(".", 1)
        factory = getattr(importlib.import_module(mod_name), func_name)
        return factory(op_cfg)

    raise ValueError(f"Unknown operator kind: {kind!r}")


def decide_route(
    eigenvalues: list[float],
    trace_estimate: float | None,
    thresholds: RouteThresholds,
) -> dict[str, Any]:
    if not eigenvalues:
        return {"route": "manual_review", "reason": "no eigenvalues returned"}

    lam_max = max(eigenvalues)
    lam_abs_max = max(abs(v) for v in eigenvalues)
    negative_count = sum(1 for v in eigenvalues if v < thresholds.negative_eigenvalue_tol)
    flat_count = sum(1 for v in eigenvalues if abs(v) <= thresholds.flat_abs_tol)
    flat_ratio = flat_count / max(1, len(eigenvalues))

    if negative_count:
        route = "probe_saddle_scar"
        reason = "negative curvature detected"
    elif lam_abs_max >= thresholds.lambda_max:
        route = "protect_or_seal_stiff_invariant"
        reason = "dominant curvature exceeds lambda_max"
    elif flat_ratio >= thresholds.flat_ratio_min:
        route = "press_flat_gauge"
        reason = "near-zero eigenvalue mass suggests flat/gauge direction"
    elif thresholds.trace_max is not None and trace_estimate is not None and trace_estimate >= thresholds.trace_max:
        route = "seal_high_total_curvature"
        reason = "trace exceeds trace_max"
    else:
        route = "continue_measured_probe"
        reason = "curvature is within configured pressure bounds"

    return {
        "route": route,
        "reason": reason,
        "lambda_max_observed": lam_max,
        "lambda_abs_max_observed": lam_abs_max,
        "negative_count": negative_count,
        "flat_count": flat_count,
        "flat_ratio": flat_ratio,
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    operator = load_operator(config)
    seed = int(config.get("seed", 0))

    lanczos_cfg = config.get("lanczos", {})
    trace_cfg = config.get("trace", {})
    density_cfg = config.get("spectral_density", {})

    eig = lanczos(
        operator,
        k=int(lanczos_cfg.get("k", 8)),
        max_iter=lanczos_cfg.get("max_iter"),
        tol=float(lanczos_cfg.get("tol", 1.0e-4)),
        which=lanczos_cfg.get("which", "LM"),
        seed=seed,
    )

    tr = None
    if trace_cfg.get("enabled", True):
        tr = trace(
            operator,
            num_matvecs=int(trace_cfg.get("num_matvecs", 99)),
            method=trace_cfg.get("method", "hutch++"),
            seed=seed,
        )

    rho = None
    if density_cfg.get("enabled", True):
        rho = spectral_density(
            operator,
            num_runs=int(density_cfg.get("num_runs", 4)),
            lanczos_steps=int(density_cfg.get("lanczos_steps", 32)),
            num_grid_points=int(density_cfg.get("num_grid_points", 512)),
            seed=seed,
        )

    eigenvalues = _tensor_to_list(eig.eigenvalues)
    residuals = _tensor_to_list(eig.residuals)
    converged = [bool(v) for v in eig.converged.detach().cpu().reshape(-1).tolist()]

    trace_payload = None
    if tr is not None:
        trace_payload = {
            "estimate": float(tr.estimate),
            "stderr": None if tr.stderr != tr.stderr else float(tr.stderr),
            "samples_sha256": _sha256_jsonable(_tensor_to_list(tr.samples)),
        }

    density_payload = None
    if rho is not None:
        density_payload = {
            "sigma": float(rho.sigma),
            "grid_sha256": _sha256_jsonable(_tensor_to_list(rho.grid)),
            "density_sha256": _sha256_jsonable(_tensor_to_list(rho.density)),
            "raw_eigenvalues_sha256": _sha256_jsonable(_tensor_to_list(rho.raw_eigenvalues)),
            "raw_weights_sha256": _sha256_jsonable(_tensor_to_list(rho.raw_weights)),
        }

    thresholds = RouteThresholds(**config.get("route_thresholds", {}))
    decision = decide_route(
        eigenvalues=eigenvalues,
        trace_estimate=None if trace_payload is None else trace_payload["estimate"],
        thresholds=thresholds,
    )

    receipt = {
        "receipt_type": "famm_hessian_curvature_receipt",
        "schema_version": "0.1.0",
        "basis_layer": "HESSIAN_EIGEN",
        "seed": seed,
        "operator": {
            "kind": config["operator"]["kind"],
            "size": int(operator.size),
            "dtype": str(operator.dtype).replace("torch.", ""),
            "device": str(operator.device),
        },
        "lanczos": {
            "k": int(lanczos_cfg.get("k", 8)),
            "iterations": int(eig.iterations),
            "eigenvalues": eigenvalues,
            "ritz_residuals": residuals,
            "converged": converged,
        },
        "trace": trace_payload,
        "spectral_density": density_payload,
        "route_decision": decision,
        "no_drift_boundary": (
            "This is a computational curvature witness. It routes proof/compression/scar work; "
            "it is not theorem proof."
        ),
    }
    receipt["receipt_sha256"] = _sha256_jsonable(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to FAMM Hessian receipt config JSON.")
    parser.add_argument("--out", required=True, help="Output receipt JSON path.")
    args = parser.parse_args()

    config_path = Path(args.config)
    out_path = Path(args.out)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    receipt = run(config)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Route: {receipt['route_decision']['route']} — {receipt['route_decision']['reason']}")
    print(f"Receipt SHA-256: {receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
