#!/usr/bin/env python3
"""Receipt for connectome manipulation and self-updating model priors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "connectome_manipulation_self_update_prior_receipt.json"
CURRICULUM = SHIM / "connectome_manipulation_self_update_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "connectome_manipulation_self_update_prior_v1",
        "source_type": "user_supplied_connectome_and_self_updating_bibliography",
        "primary_read": (
            "Connectome work provides a disciplined graph perturbation loop: "
            "structural graph, simulated dynamics, function readout, reproducible "
            "manipulation, prediction, and error remediation. For this stack it "
            "is a virtual-connectome control prior, not evidence of autonomous "
            "self-rewrite."
        ),
        "method_lanes": [
            {
                "lane": "connectome_manipulation_framework",
                "use": "systematically perturb graph structure and measure simulated function",
                "risk": "simulation result depends on model assumptions and perturbation scope",
                "keys": ["Pokorny2024A"],
            },
            {
                "lane": "generative_connectome_models",
                "use": "generate plausible network structure from wiring and topology rules",
                "risk": "generated graph plausibility is not functional validation",
                "keys": ["Betzel2015Generative"],
            },
            {
                "lane": "structural_to_functional_dynamics",
                "use": "simulate functional connectivity evolving over structural connectome",
                "risk": "static structure can support multiple dynamic regimes",
                "keys": ["Cabral2017Functional", "Arbabyazd2021Virtual"],
            },
            {
                "lane": "connectome_predictive_modeling",
                "use": "predict behavior or phenotype from connectivity features",
                "risk": "prediction does not explain mechanism without perturbation tests",
                "keys": ["Shen2017Using", "Ali2022A"],
            },
            {
                "lane": "connectome_tooling_and_reproducibility",
                "use": "query, manipulate, and audit network datasets",
                "risk": "tool query result is not a model claim by itself",
                "keys": ["Clements2020neuPrint:"],
            },
            {
                "lane": "self_updating_and_nonstationary_models",
                "use": "periodically update, self-train, or remediate model errors under drift",
                "risk": "self-update can amplify errors unless gated by validation",
                "keys": ["Li2024Online", "Duarte2024Generating", "Doak2020Self-Updating", "Kim2020Domain"],
            },
            {
                "lane": "model_connectomes_for_language_models",
                "use": "treat model internals as structured graph lineage for data-efficient training",
                "risk": "model-connectome analogy requires direct measurement of model graph/function",
                "keys": ["Kotar2025Model"],
            },
        ],
        "virtual_connectome_state": [
            "node_set_id",
            "edge_set_id",
            "edge_weight_schema",
            "structural_connectome_hash",
            "functional_state_vector",
            "perturbation_operator_id",
            "simulation_dynamics_id",
            "prediction_head_id",
            "error_remediation_policy_id",
            "drift_detector_id",
            "update_epoch",
            "validation_receipt_id",
            "rollback_state_hash",
        ],
        "equation_pipeline_mapping": {
            "structural_connectome": "equation dependency graph",
            "functional_connectivity": "observed equation behavior under validators",
            "connectome_manipulation": "controlled rewrite or perturbation of equation graph",
            "simulation": "numeric, symbolic, unit, or byte-route evaluation",
            "self_update": "bounded model/equation index update after validation",
            "error_remediation": "rollback or patch when validation fails",
        },
        "hutter_mapping": {
            "connectome_graph": "route dependency graph",
            "functional_readout": "compressed bytes, decode hash, runtime, witness cost",
            "perturbation": "route transform change",
            "self_update": "route scheduler update only after receipt",
            "rollback": "restore previous incumbent and dependency graph",
        },
        "promotion_rule": [
            "graph state is versioned and hashed",
            "perturbation operator is explicit and bounded",
            "functional readout is measured locally",
            "self-update has validation and rollback receipts",
            "Hutter route updates preserve exact decode/hash authority",
        ],
        "failure_rules": [
            "graph analogy without measured function -> diagnostic only",
            "self-update without validation receipt -> fail closed",
            "model drift detector missing -> hold",
            "rollback state missing -> invalid update",
            "prediction score replaces mechanism or byte receipt -> invalid",
        ],
        "bibliography_keys": [
            "Pokorny2024A",
            "Betzel2015Generative",
            "Arbabyazd2021Virtual",
            "Cabral2017Functional",
            "Clements2020neuPrint:",
            "Li2024Online",
            "Ali2022A",
            "Kotar2025Model",
            "Shen2017Using",
            "Duarte2024Generating",
            "Hammer2004Recursive",
            "Kim2020Domain",
            "Borst2023Connecting",
            "Doak2020Self-Updating",
        ],
        "bibtex_hygiene_notes": [
            "Clements2020neuPrint: contains punctuation in the BibTeX key",
            "Doak2020Self-Updating contains punctuation in the BibTeX key",
            "Consensus-style DOI metadata should be verified before publication",
        ],
        "claim_boundary": (
            "This prior supports reproducible graph manipulation and bounded "
            "self-update discipline. It does not prove autonomous metatyping, "
            "biological equivalence, or compression improvement."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_connectome_update_lane",
            "input": "graph manipulation or self-updating model method",
            "target": "connectome manipulation, generative graph, dynamics, prediction, tooling, self-update, or model-connectome lane",
        },
        {
            "task": "require_validation_and_rollback",
            "input": "self-updating equation or route graph",
            "target": "validation receipt plus rollback state hash",
        },
        {
            "task": "separate_graph_analogy_from_function",
            "input": "connectome-inspired route or equation graph",
            "target": "measured functional readout before promotion",
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
        "state_field_count": len(receipt["virtual_connectome_state"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
