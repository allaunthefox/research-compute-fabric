#!/usr/bin/env python3
"""Receipt for holographic, fractional, and recursive connectome priors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "holographic_fractional_recursive_connectome_prior_receipt.json"
CURRICULUM = SHIM / "holographic_fractional_recursive_connectome_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "holographic_fractional_recursive_connectome_prior_v1",
        "source_type": "user_supplied_consensus_connectome_holography_fractional_recursion_bundle",
        "primary_read": (
            "Holographic, fractional, and recursive connectome mechanisms each "
            "provide a plausible reconfiguration primitive: boundary/bulk coding, "
            "memory kernels, and iterative self-organization. The integrated "
            "all-three biological-connectome claim remains weak and should be "
            "treated as an open research program, not an established fact."
        ),
        "reported_search_shapes": {
            "latex_version": {
                "identified_papers": 271065,
                "screened_papers": 239,
                "eligible_papers": 198,
                "included_papers": 50,
            },
            "ama_numeric_version": {
                "retrieved": "83.4M",
                "eligible": 2099,
                "included": 50,
                "note": "The supplied versions disagree on retrieval counts; preserve both as unverified Consensus metadata.",
            },
        },
        "evidence_claims": [
            {
                "claim": "connectomes can dynamically reconfigure structure/function with new data",
                "strength": "strong_9_10",
                "risk": "empirical reconfiguration does not identify a reusable compiler mechanism by itself",
                "keys": ["Seguin2023Brain", "Bennett2018Rewiring", "Park2021An"],
            },
            {
                "claim": "holographic/tensor models can support adaptable encoding and decoding",
                "strength": "strong_8_10",
                "risk": "holographic representation is not automatically byte-exact or biologically instantiated",
                "keys": ["Hu2019Machine", "Pastawski2015Holographic", "Melnikov2023Connectomes"],
            },
            {
                "claim": "fractional-order models can add memory effects and long-range dependence",
                "strength": "moderate_7_10",
                "risk": "fractional order must be fitted, bounded, and paid as model complexity",
                "keys": ["Joshi2023A", "Ionescu2017The", "Zhou2020Clarify"],
            },
            {
                "claim": "recursive/self-organizing architectures support continual structured updates",
                "strength": "moderate_7_10",
                "risk": "recursive update can drift unless validation and rollback are explicit",
                "keys": ["Hammer2004Recursive", "Doncevic2022A"],
            },
            {
                "claim": "all three mechanisms are empirically validated together in biological connectomes",
                "strength": "weak_2_10",
                "risk": "no direct integrated validation in supplied evidence",
                "keys": [],
            },
            {
                "claim": "fractal geometry provides useful markers for structural/functional dynamics",
                "strength": "moderate_6_10",
                "risk": "marker quality does not imply causal mechanism or compression gain",
                "keys": ["Radulescu2025Fractal"],
            },
        ],
        "method_lanes": [
            {
                "lane": "connectome_harmonic_and_manifold_reconfiguration",
                "use": "represent dynamics as modes over a structural graph or manifold",
                "keys": ["Atasoy2017Connectome-harmonic", "Park2021An", "Preti2017The"],
                "stack_mapping": "equation or route graph Laplacian eigenmodes",
            },
            {
                "lane": "holographic_boundary_bulk_encoding",
                "use": "separate compact boundary representation from richer interior state",
                "keys": ["Pastawski2015Holographic", "Melnikov2023Connectomes", "Hu2019Machine"],
                "stack_mapping": "boundary receipt/index plus exact interior residual rehydration",
            },
            {
                "lane": "deep_holographic_reconstruction",
                "use": "learn inverse reconstruction from sparse or phase-like observations",
                "keys": ["Rivenson2017Phase", "Situ2022Deep", "Huang2024Quantitative", "Wang2019Y-Net:"],
                "stack_mapping": "candidate inverse map, never final byte authority",
            },
            {
                "lane": "fractional_memory_dynamics",
                "use": "model long-memory state updates with non-integer order dynamics",
                "keys": ["Ionescu2017The", "Joshi2023A", "Zhou2020Clarify"],
                "stack_mapping": "bounded history kernel for route/equation state",
            },
            {
                "lane": "recursive_self_organizing_update",
                "use": "process sequential or structured inputs through repeated internal updates",
                "keys": ["Hammer2004Recursive", "Doncevic2022A", "Lynn2022Heavy-tailed"],
                "stack_mapping": "recursive graph updater with drift, validation, and rollback gates",
            },
            {
                "lane": "atlas_remapping_and_domain_adaptation",
                "use": "move connectome representations between atlas/schema domains",
                "keys": ["Dadashkarimi2023Cross", "Ganin2015Domain-Adversarial", "Zoph2017Learning"],
                "stack_mapping": "optimal-transport or adversarial remap between equation dialects",
            },
            {
                "lane": "fractal_and_heavy_tail_network_markers",
                "use": "measure multiscale structure and heavy-tailed connectivity",
                "keys": ["Radulescu2025Fractal", "Lynn2022Heavy-tailed"],
                "stack_mapping": "fractal dimension and tail diagnostics as priors, not receipts",
            },
            {
                "lane": "dynamic_network_reconfiguration",
                "use": "borrow reconfiguration discipline from network science and power networks",
                "keys": ["Behbahani2024Comprehensive", "Bennett2018Rewiring", "Seguin2023Brain"],
                "stack_mapping": "bounded topology rewrite with cost and stability constraints",
            },
        ],
        "integrated_state": [
            "graph_state_hash",
            "harmonic_basis_id",
            "boundary_code_id",
            "bulk_state_commitment",
            "fractional_order_alpha",
            "memory_kernel_id",
            "recursive_update_operator_id",
            "atlas_mapping_id",
            "domain_adaptation_guard_id",
            "fractal_marker_vector",
            "holographic_reconstruction_error_bound",
            "history_window_cost",
            "validation_receipt_id",
            "rollback_state_hash",
        ],
        "equation_pipeline_mapping": {
            "holographic_boundary": "compact equation/route index or receipt boundary",
            "holographic_bulk": "full latent/interior state requiring exact residual closure",
            "fractional_memory": "history-sensitive update kernel for nonstationary routes",
            "recursive_update": "iterative equation graph rewriter under validation",
            "connectome_harmonic": "graph Laplacian eigenbasis for route/equation modes",
            "atlas_remapping": "schema or dialect transfer between incompatible equation maps",
            "fractal_marker": "multiscale topology diagnostic for candidate segmentation",
        },
        "hutter_mapping": {
            "boundary_code": "short route descriptor or index",
            "bulk_state": "hidden state that must be rehydrated or paid as residual",
            "fractional_kernel": "history model whose parameters and window bytes count",
            "recursive_update": "route proposal update, not byte authority",
            "harmonic_basis": "candidate transform basis over route graph",
            "fractal_marker": "route-pruning feature only",
        },
        "promotion_rule": [
            "each lane declares whether it is representation, memory, update, remap, or diagnostic",
            "fractional order and memory kernel cost are bounded",
            "boundary/bulk split has exact residual closure",
            "recursive update has validation and rollback receipts",
            "atlas/domain remap has an admissibility witness",
            "Hutter use preserves exact decode/hash/measured-byte authority",
        ],
        "failure_rules": [
            "integrated all-three claim treated as established -> overclaim",
            "holographic boundary hides payload bytes -> invalid receipt",
            "fractional memory kernel unbounded -> NaN0",
            "recursive update without rollback -> fail closed",
            "atlas remap without admissibility witness -> hold",
            "fractal marker replaces validation -> diagnostic only",
            "reconstruction confidence replaces exact decode/hash -> invalid",
        ],
        "research_gap_matrix": {
            "encoding_decoding_adaptation": {
                "holographic_models": 4,
                "fractional_models": "GAP",
                "recursive_models": "GAP",
                "empirical_connectome_data": "GAP",
            },
            "memory_effects": {
                "holographic_models": "GAP",
                "fractional_models": 4,
                "recursive_models": "GAP",
                "empirical_connectome_data": "GAP",
            },
            "sequential_data_integration": {
                "holographic_models": "GAP",
                "fractional_models": "GAP",
                "recursive_models": 3,
                "empirical_connectome_data": "GAP",
            },
            "biological_validation": {
                "holographic_models": 1,
                "fractional_models": 2,
                "recursive_models": 1,
                "empirical_connectome_data": 8,
            },
        },
        "bibliography_keys": [
            "Atasoy2017Connectome-harmonic",
            "Bazinet2023Towards",
            "Behbahani2024Comprehensive",
            "Bennett2018Rewiring",
            "Dadashkarimi2023Cross",
            "Doncevic2022A",
            "Fatemiabhari2024From",
            "Ganin2015Domain-Adversarial",
            "Hammer2004Recursive",
            "Hu2019Machine",
            "Huang2024Quantitative",
            "Ionescu2017The",
            "Joshi2023A",
            "Liu20234K-DMDNet:",
            "Lynn2022Heavy-tailed",
            "Melnikov2023Connectomes",
            "Noecker2023Stereo-EEG-guided",
            "Park2021An",
            "Pastawski2015Holographic",
            "Petersen2019Holographic",
            "Preti2017The",
            "Radulescu2025Fractal",
            "Rivenson2017Phase",
            "Seguin2023Brain",
            "Situ2022Deep",
            "Vasa2022Null",
            "Wang2019Y-Net:",
            "Wang2024Reconfigurable",
            "Zhou2020Clarify",
            "Zoph2017Learning",
        ],
        "bibtex_hygiene_notes": [
            "Several supplied keys contain punctuation or accents; normalize before publication",
            "The supplied Consensus search-shape counts disagree between LaTeX and AMA versions",
            "Consensus-generated DOI and citation metadata should be verified before final citation use",
        ],
        "claim_boundary": (
            "This prior supports a research program for combining holographic "
            "boundary/bulk coding, fractional memory, and recursive graph update. "
            "It does not establish an empirically validated unified biological "
            "connectome mechanism, autonomous self-reconfiguration, or compression gain."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_reconfiguration_lane",
            "input": "holographic, fractional, recursive, harmonic, atlas, or fractal method",
            "target": "representation, memory, update, remap, or diagnostic lane",
        },
        {
            "task": "protect_integrated_claim_boundary",
            "input": "claim that holography, fractionality, and recursion are jointly validated",
            "target": "weak/open frontier unless direct integrated evidence is present",
        },
        {
            "task": "charge_memory_and_boundary_costs",
            "input": "fractional memory kernel or holographic boundary/bulk split",
            "target": "bounded kernel cost and exact residual closure",
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
        "state_field_count": len(receipt["integrated_state"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
