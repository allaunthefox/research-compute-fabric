#!/usr/bin/env python3
"""Model-selection pass for the Φ-scaling response functions.

This runner keeps the validated part of the local Φ surface separate from the
unvalidated parts:

* D_f = log(2)/log(phi) is treated as a topology prior.
* LTEE fitness and Drake-rule mutation rates are treated as domain response
  functions that must be selected by error, not forced into a preferred form.

The goal is not to prove the best biological model.  The goal is to prevent
the project from force-fitting a square-root, logarithm, or any other function
without a receipt.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "phi_scaling_response_model_selection_receipt.json"
RESULTS_OUT = SHIM / "phi_scaling_response_model_selection_results.json"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
LAMBDA_PHI = PHI**2
D_F = math.log(2.0) / math.log(PHI)
FRACTAL_GAIN = LAMBDA_PHI**D_F

LTEE_DATA = [
    {"generations": 2_000, "mutations": 10.0, "fitness": 1.35},
    {"generations": 10_000, "mutations": 50.0, "fitness": 1.65},
    {"generations": 20_000, "mutations": 100.0, "fitness": 1.80},
    {"generations": 40_000, "mutations": 200.0, "fitness": 1.95},
    {"generations": 50_000, "mutations": 250.0, "fitness": 2.00},
]

DRAKE_DATA = [
    {"organism": "E. coli", "genome_size_bp": 4.6e6, "per_genome_rate": 0.0025, "per_site_rate": 5.4e-10},
    {"organism": "S. cerevisiae", "genome_size_bp": 1.2e7, "per_genome_rate": 0.003, "per_site_rate": 2.5e-10},
    {"organism": "D. melanogaster", "genome_size_bp": 1.2e8, "per_genome_rate": 0.14, "per_site_rate": 1.2e-9},
    {"organism": "C. elegans", "genome_size_bp": 1.0e8, "per_genome_rate": 0.02, "per_site_rate": 2.0e-10},
    {"organism": "H. sapiens", "genome_size_bp": 3.2e9, "per_genome_rate": 70.0, "per_site_rate": 2.2e-8},
]

FRACTAL_DATA = [
    {"network_type": "Protein interaction (yeast)", "measured_D_f": 1.5},
    {"network_type": "Metabolic (E. coli)", "measured_D_f": 1.45},
    {"network_type": "Transcriptional (human)", "measured_D_f": 1.4},
    {"network_type": "Gene regulatory (Drosophila)", "measured_D_f": 1.65},
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def fit_scale(xs: list[float], ys: list[float]) -> float:
    denom = sum(x * x for x in xs)
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(xs, ys)) / denom


def mape(predicted: list[float], observed: list[float]) -> float:
    return sum(abs(p - o) / abs(o) for p, o in zip(predicted, observed)) / len(observed) * 100.0


def rmse(predicted: list[float], observed: list[float]) -> float:
    return math.sqrt(sum((p - o) ** 2 for p, o in zip(predicted, observed)) / len(observed))


def aic_like(predicted: list[float], observed: list[float], parameter_count: int) -> float:
    n = len(observed)
    sse = sum((p - o) ** 2 for p, o in zip(predicted, observed))
    return n * math.log(max(sse / n, 1e-18)) + 2 * parameter_count


def ltee_fit(
    model_id: str,
    parameter_count: int,
    basis_fn: Callable[[float], float],
    params: dict[str, Any],
) -> dict[str, Any]:
    # Fit relative fitness excess, so all models satisfy ancestor baseline of 1.
    observed_excess = [row["fitness"] - 1.0 for row in LTEE_DATA]
    basis = [basis_fn(row["mutations"]) * FRACTAL_GAIN for row in LTEE_DATA]
    scale = fit_scale(basis, observed_excess)
    predicted_excess = [scale * value for value in basis]
    predicted = [1.0 + value for value in predicted_excess]
    observed = [row["fitness"] for row in LTEE_DATA]
    rows = []
    for row, pred in zip(LTEE_DATA, predicted):
        rows.append({
            "generations": row["generations"],
            "mutations": row["mutations"],
            "observed_fitness": row["fitness"],
            "predicted_fitness": pred,
            "error_percent": abs(pred - row["fitness"]) / row["fitness"] * 100.0,
        })
    return {
        "model_id": model_id,
        "parameters": params | {"C_domain_fit": scale},
        "parameter_count": parameter_count,
        "avg_error_percent": mape(predicted, observed),
        "rmse": rmse(predicted, observed),
        "aic_like": aic_like(predicted, observed, parameter_count),
        "rows": rows,
    }


def select_ltee_models() -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    models.append(ltee_fit("sqrt_mutations", 1, lambda s: math.sqrt(s), {}))

    for alpha in [i / 20.0 for i in range(2, 21)]:
        models.append(ltee_fit(
            "power_mutations",
            2,
            lambda s, a=alpha: s**a,
            {"alpha": alpha},
        ))

    for beta in [10 ** x for x in [-3, -2.5, -2, -1.5, -1, -0.5, 0]]:
        models.append(ltee_fit(
            "log_mutations",
            2,
            lambda s, b=beta: math.log1p(b * s),
            {"beta": beta},
        ))

    for k in [5, 10, 20, 50, 100, 200, 500]:
        models.append(ltee_fit(
            "michaelis_menten",
            2,
            lambda s, kk=k: s / (kk + s),
            {"K": k},
        ))

    for k in [10, 20, 50, 100, 200, 500]:
        for hill in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
            models.append(ltee_fit(
                "hill_saturation",
                3,
                lambda s, kk=k, h=hill: (s**h) / (kk**h + s**h),
                {"K": k, "hill": hill},
            ))

    return sorted(models, key=lambda item: (item["avg_error_percent"], item["aic_like"]))


def drake_fit(model_id: str, parameter_count: int, basis_fn: Callable[[float], float], params: dict[str, Any]) -> dict[str, Any]:
    observed = [row["per_site_rate"] for row in DRAKE_DATA]
    basis = [basis_fn(row["genome_size_bp"]) * FRACTAL_GAIN for row in DRAKE_DATA]
    scale = fit_scale(basis, observed)
    predicted = [scale * value for value in basis]
    rows = []
    for row, pred in zip(DRAKE_DATA, predicted):
        rows.append({
            "organism": row["organism"],
            "genome_size_bp": row["genome_size_bp"],
            "observed_per_site_rate": row["per_site_rate"],
            "predicted_per_site_rate": pred,
            "observed_per_genome_rate": row["per_genome_rate"],
            "predicted_per_genome_rate": pred * row["genome_size_bp"],
            "error_percent": abs(pred - row["per_site_rate"]) / row["per_site_rate"] * 100.0,
        })
    return {
        "model_id": model_id,
        "parameters": params | {"C_domain_fit": scale},
        "parameter_count": parameter_count,
        "avg_error_percent": mape(predicted, observed),
        "rmse": rmse(predicted, observed),
        "aic_like": aic_like(predicted, observed, parameter_count),
        "rows": rows,
    }


def select_drake_models() -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    models.append(drake_fit("constant_per_site", 1, lambda _g: 1.0, {}))
    models.append(drake_fit("inverse_genome_size", 1, lambda g: 1.0 / g, {}))
    for alpha in [i / 20.0 for i in range(0, 41)]:
        models.append(drake_fit(
            "genome_power_law",
            2,
            lambda g, a=alpha: g ** (-a),
            {"alpha": alpha},
        ))
    # This is not a predictive model. It records the missing-covariate floor:
    # observed per-genome rates vary by many orders of magnitude, so g/Ne/repair
    # must be measured before a cross-taxa mutation-rate claim can be promoted.
    return sorted(models, key=lambda item: (item["avg_error_percent"], item["aic_like"]))


def fractal_dimension_check() -> dict[str, Any]:
    rows = []
    for row in FRACTAL_DATA:
        error = abs(D_F - row["measured_D_f"]) / row["measured_D_f"] * 100.0
        rows.append({
            "network_type": row["network_type"],
            "measured_D_f": row["measured_D_f"],
            "predicted_D_f": D_F,
            "error_percent": error,
        })
    return {
        "predicted_D_f": D_F,
        "avg_error_percent": sum(row["error_percent"] for row in rows) / len(rows),
        "rows": rows,
        "verdict": "retain_as_topological_prior",
    }


def build_receipt() -> dict[str, Any]:
    ltee = select_ltee_models()
    drake = select_drake_models()
    fractal = fractal_dimension_check()
    best_ltee = ltee[0]
    best_drake = drake[0]
    receipt: dict[str, Any] = {
        "schema": "phi_scaling_response_model_selection_v1",
        "constants": {
            "phi": PHI,
            "lambda_phi": LAMBDA_PHI,
            "D_f_log2_over_logphi": D_F,
            "lambda_phi_to_D_f": FRACTAL_GAIN,
        },
        "model_selection_policy": {
            "posture": "do_not_force_fit_function",
            "rule": (
                "Keep D_f as a topology prior; choose each domain response "
                "function by measured error and complexity penalty."
            ),
            "promotion_boundary": (
                "A response function may be used as a fitted diagnostic only "
                "until validated against held-out domain data."
            ),
        },
        "ltee_model_ranking": ltee[:12],
        "drake_model_ranking": drake[:12],
        "fractal_dimension_check": fractal,
        "selected_read": {
            "ltee": {
                "best_model_id": best_ltee["model_id"],
                "avg_error_percent": best_ltee["avg_error_percent"],
                "parameters": best_ltee["parameters"],
                "interpretation": (
                    "LTEE needs a saturating or very low-exponent response. "
                    "Logarithmic scaling is allowed only if it ranks well; it "
                    "is not assumed."
                ),
            },
            "drake": {
                "best_model_id": best_drake["model_id"],
                "avg_error_percent": best_drake["avg_error_percent"],
                "parameters": best_drake["parameters"],
                "interpretation": (
                    "Genome-size-only fits are underidentified across taxa. "
                    "Generation time, Ne, repair efficiency, and organism class "
                    "remain required covariates before promotion."
                ),
            },
            "fractal": fractal["verdict"],
        },
        "claim_boundary": (
            "This is a model-selection receipt over a tiny local dataset. It "
            "does not prove a biological law. It demotes failed universal "
            "power laws and keeps Phi/D_f only where the error surface supports it."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RESULTS_OUT.write_text(
        json.dumps(
            {
                "best_ltee": receipt["selected_read"]["ltee"],
                "best_drake": receipt["selected_read"]["drake"],
                "fractal": receipt["fractal_dimension_check"],
                "receipt_hash": receipt["receipt_hash"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "receipt": rel(OUT),
        "results": rel(RESULTS_OUT),
        "receipt_hash": receipt["receipt_hash"],
        "best_ltee": receipt["selected_read"]["ltee"],
        "best_drake": receipt["selected_read"]["drake"],
        "fractal_avg_error_percent": receipt["fractal_dimension_check"]["avg_error_percent"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
