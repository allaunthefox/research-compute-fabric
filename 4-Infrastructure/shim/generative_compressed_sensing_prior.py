#!/usr/bin/env python3
"""Receipt for generative compressed sensing as a bounded route prior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "generative_compressed_sensing_prior_receipt.json"
CURRICULUM = SHIM / "generative_compressed_sensing_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "generative_compressed_sensing_prior_v1",
        "source_type": "user_supplied_consensus_bibliography",
        "primary_read": (
            "Generative compressed sensing extends sparse recovery by replacing "
            "or augmenting plain sparsity with a learned low-dimensional prior, "
            "but recovery guarantees depend on generator regularity, latent "
            "dimension, representation error, noise model, and optimization cost."
        ),
        "anchor_keys": [
            "Bora2017Compressed",
            "Huang2018A",
            "Hand2020Compressive",
            "Chen2023A",
            "Nguyen2021Provable",
            "Jalal2020Robust",
            "Asim2019Invertible",
            "Dhar2018Modeling",
            "Berk2022A",
            "Scarlett2022Theoretical",
            "Kamath2019Lower",
        ],
        "method_lanes": [
            {
                "lane": "gan_or_deep_generator_prior",
                "use": "restrict candidate signal to range of a generator",
                "risk": "representation error and dataset bias",
                "keys": ["Bora2017Compressed", "Shah2018Solving", "Hand2017Global"],
            },
            {
                "lane": "provable_convergence_and_sample_complexity",
                "use": "bound recovery under random/generative priors",
                "risk": "assumptions may not match real target distribution",
                "keys": ["Huang2018A", "Hand2020Compressive", "Chen2023A", "Scarlett2022Theoretical"],
            },
            {
                "lane": "robust_and_sparse_deviation_models",
                "use": "generator plus explicit sparse deviation or corruption lane",
                "risk": "deviation lane can become hidden payload if uncounted",
                "keys": ["Jalal2020Robust", "Dhar2018Modeling", "Cai2020Fast"],
            },
            {
                "lane": "langevin_bayesian_score_posterior",
                "use": "sample or score the posterior instead of deterministic projection",
                "risk": "sampling cost and uncertainty must be receipted",
                "keys": ["Nguyen2021Provable", "Meng2022Quantized", "Zhang2025Bayesian", "Bock2024Sparse"],
            },
            {
                "lane": "invertible_or_measurement_conditional_generators",
                "use": "reduce projection ambiguity and improve conditioning",
                "risk": "dependent noise and invertibility assumptions are domain-specific",
                "keys": ["Asim2019Invertible", "Whang2020Compressed", "Kim2020Compressed"],
            },
            {
                "lane": "physics_guided_or_model_based_deep_unrolling",
                "use": "blend physical forward model with learned reconstruction",
                "risk": "model mismatch can be mistaken for signal",
                "keys": ["Chen2023Deep", "Khobahi2020Model-Based", "Lazzaro2024Oracle-Net"],
            },
            {
                "lane": "application_specific_inverse_imaging",
                "use": "MRI, EIT, crack segmentation, pose, channel estimation, one-bit or quantized sensing",
                "risk": "application wins do not transfer without matching measurement operators",
                "keys": ["Jalal2021Robust", "Bohra2022Bayesian", "Hieu2023Reconstructing", "Balevi2020High"],
            },
        ],
        "route_state_additions": [
            "generator_prior_id",
            "generator_family_class",
            "latent_dimension",
            "latent_regularizer_id",
            "representation_error_bound",
            "dataset_bias_status",
            "measurement_operator_class",
            "noise_model_class",
            "posterior_sampling_status",
            "sparse_deviation_lane_id",
            "exact_residual_lane_id",
            "generator_witness_bytes",
            "byte_rehydration_hash",
        ],
        "equation_pipeline_mapping": {
            "equation_trace": "measurement y",
            "candidate_equation_family": "generator range G(z)",
            "symbolic_deviation": "sparse deviation lane",
            "notation_or_domain_bias": "dataset bias",
            "proof_or_unit_validator": "measurement consistency check",
            "held_out_equation_family": "generalization test",
        },
        "hutter_mapping": {
            "generator_prior": "route proposal or residual predictor only",
            "latent_code": "counted sidecar unless derived from decoder state",
            "sparse_deviation": "exact residual lane, not free correction",
            "reconstruction_loss": "diagnostic only",
            "promotion": "exact byte decode, hash, measured bytes, counted witnesses",
        },
        "failure_rules": [
            "generator prior used as hidden payload -> invalid receipt",
            "representation error not residualized -> not promoted",
            "dataset bias changes source bytes -> fail closed",
            "latent code larger than byte gain -> prune",
            "posterior uncertainty unreported -> diagnostic only",
            "application-specific operator assumed universal -> negative transfer hold",
        ],
        "bibtex_hygiene_notes": [
            "Quer2012Sensing,, contains a malformed BibTeX key with a double comma",
            "Some supplied entries have missing DOI or venue fields and should be verified before publication",
            "Keep this bundle as a research prior until individual sources are verified",
        ],
        "claim_boundary": (
            "Generative compressed sensing is a proposal and reconstruction prior "
            "for this stack. It cannot replace exact residual repair, proof checks, "
            "or Hutter byte receipts."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_generative_cs_lane",
            "input": "generative compressed-sensing paper or route",
            "target": "generator, convergence, robust deviation, posterior, invertible, physics-guided, or application lane",
        },
        {
            "task": "separate_latent_code_from_free_structure",
            "input": "generator-based compression proposal",
            "target": "count latent/witness bytes unless decoder derives them",
        },
        {
            "task": "require_exact_residual_for_hutter",
            "input": "lossy generator reconstruction",
            "target": "exact residual lane plus byte rehydration hash",
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
