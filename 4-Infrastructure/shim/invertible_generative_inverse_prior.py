#!/usr/bin/env python3
"""Receipt for invertible/flow generative models as inverse-problem priors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "invertible_generative_inverse_prior_receipt.json"
CURRICULUM = SHIM / "invertible_generative_inverse_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "invertible_generative_inverse_prior_v1",
        "source_type": "user_supplied_invertible_generative_bibliography",
        "primary_read": (
            "Invertible networks, normalizing flows, and diffusion/score models "
            "can reduce representation error and expose uncertainty in inverse "
            "problems, but invertibility is not a free proof of correctness. "
            "Conditioning, exploding inverses, ill-posed reversible mappings, "
            "distribution shift, and exact residual obligations remain gates."
        ),
        "method_lanes": [
            {
                "lane": "invertible_generators_and_gan_inversion",
                "use": "map observations into latent states with reduced projection ambiguity",
                "risk": "latent inversion can still miss out-of-range content or inherit dataset bias",
                "keys": ["Asim2019Invertible", "Creswell2016Inverting", "Zhu2023In-Domain", "Li2025Patch"],
            },
            {
                "lane": "normalizing_flows",
                "use": "explicit likelihood and invertible density transform for inverse problems",
                "risk": "Jacobian cost, flow conditioning, and support mismatch",
                "keys": ["Durkan2019Neural", "Cai2023NF-ULA:", "Wang2024Normalizing", "Draxler2023Free-form"],
            },
            {
                "lane": "invertible_resnets_and_regularization_theory",
                "use": "regularized invertible architecture with provable properties",
                "risk": "exploding inverse or poorly conditioned inverse map",
                "keys": ["Arndt2023Invertible", "Arndt2024Invertible", "Behrmann2020Understanding"],
            },
            {
                "lane": "score_diffusion_and_manifold_constraints",
                "use": "solve inverse problems by conditioning generative diffusion or score models",
                "risk": "hard data consistency and manifold constraints must be explicit",
                "keys": ["Song2021Solving", "Song2023Solving", "Chung2022Improving", "Sfountouris2025Align"],
            },
            {
                "lane": "physics_guided_inverse_models",
                "use": "couple forward physics, flow constraints, or operator error models to learned priors",
                "risk": "physical model mismatch can become hidden correction",
                "keys": ["Jacobsen2023CoCoGen:", "Kang2025Flow-Rate-Constrained", "Toloubidokhti2022Interpretable", "Molnar2021Flow"],
            },
            {
                "lane": "compression_and_rescaling_flows",
                "use": "approximately invertible compression, rescaling, or low-resolution enhancement",
                "risk": "approximate invertibility is lossy unless residualized",
                "keys": ["Gao2024Approximately", "Helminger2020Lossy", "Windsheimer2023Multiscale", "Bao2026Enhancing"],
            },
            {
                "lane": "bayesian_uncertainty_and_distribution_shift",
                "use": "represent posterior uncertainty and distribution shift in inverse problems",
                "risk": "uncertainty estimate is diagnostic until tied to validation or exact residual",
                "keys": ["Oliviero-Durmus2025Generative", "Kim2025Towards", "Stevens2025Deep", "Levy2021Using"],
            },
        ],
        "route_state_additions": [
            "invertible_prior_id",
            "flow_family_class",
            "jacobian_cost_class",
            "inverse_condition_number_class",
            "exploding_inverse_guard",
            "support_mismatch_status",
            "distribution_shift_uncertainty",
            "hard_data_consistency_status",
            "physics_forward_model_id",
            "approx_invertibility_error_bound",
            "exact_residual_lane_id",
            "flow_witness_bytes",
            "byte_rehydration_hash",
        ],
        "equation_pipeline_mapping": {
            "invertible_map": "bidirectional equation chart between observation and latent parameter",
            "normalizing_flow": "density-aware chart over equation candidates",
            "jacobian": "local sensitivity / conditioning witness",
            "hard_data_consistency": "unit, numeric, proof, or byte validator",
            "distribution_shift": "domain mismatch between source equation family and target equation family",
            "support_mismatch": "candidate equation lies outside learned chart",
        },
        "hutter_mapping": {
            "invertible_prior": "route chart or reversible feature map only",
            "approximate_inverse_error": "must become exact residual",
            "latent_state": "counted witness unless decoder derives it",
            "flow_likelihood": "candidate score only",
            "promotion": "exact decode/hash/byte count remains authority",
        },
        "failure_rules": [
            "approximate invertibility treated as lossless -> invalid receipt",
            "exploding inverse guard missing -> fail closed",
            "support mismatch not detected -> diagnostic only",
            "flow likelihood treated as proof -> invalid",
            "physics-guided correction hides model error -> fail closed",
            "latent state or Jacobian witness exceeds byte gain -> prune",
        ],
        "bibtex_hygiene_notes": [
            "Supplied bibliography contains duplicate/empty entries such as 2020Invertible with missing author and DOI",
            "Several entries use future years or venue/DOI mismatches and need verification before publication",
            "Keep this as an internal prior until source metadata is independently verified",
        ],
        "claim_boundary": (
            "Invertible and flow-based generative models can provide better route "
            "charts and uncertainty surfaces, but they do not replace exact "
            "rehydration, proof validation, or counted compression receipts."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_invertible_inverse_lane",
            "input": "invertible/flow/diffusion inverse-problem method",
            "target": "invertible generator, flow, invertible ResNet, diffusion, physics-guided, compression-flow, or uncertainty lane",
        },
        {
            "task": "check_invertibility_claim",
            "input": "claimed reversible model",
            "target": "condition number, exploding inverse guard, support mismatch, and residual lane",
        },
        {
            "task": "separate_likelihood_from_proof",
            "input": "flow likelihood or posterior score",
            "target": "candidate score only until validator or exact byte receipt confirms",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps({
        "receipt": str(RECEIPT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "method_lane_count": len(receipt["method_lanes"]),
        "state_addition_count": len(receipt["route_state_additions"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
