#!/usr/bin/env python3
"""Build DD experiment-card receipts from the pulled AlphaEvolve gallery.

This runner does not execute AlphaEvolve programs and does not import their
mathematical claims into the compressor.  It turns the pulled public examples
into local decision-diagram task cards:

* route-search objective text
* incumbent score fields
* generated/analysed counters where the pull exposes them
* applicability class for the projectable-geometry compressor
* strict promotion/failure gates that keep byte-exact rehydration authoritative
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PULL = REPO / "4-Infrastructure" / "shim" / "alphaevolve_example_gallery_pull.json"
OUT = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "alphaevolve_dd_experiment_card_receipt.json"
)


DIRECT_USE = {
    "11b5bd33_f8f1_4f90_81b0_6eb607d1c2dc": {
        "compression_role": "active_frontier_activation",
        "extraction": (
            "Activate reachable transform states without materializing the full "
            "16D torus or hypercube surface."
        ),
    },
    "963c9114_4a7d_4870_b015_865c8e7235e7": {
        "compression_role": "rehydration_from_local_witnesses",
        "extraction": (
            "Reconstruct the global byte object from local witnesses, with the "
            "rehydration hash as authority."
        ),
    },
    "58693cb6_5bce_4219_bb14_a064a87e3117": {
        "compression_role": "failure_ranking",
        "extraction": (
            "Assign route failures a well-founded decreasing rank so repair "
            "does not become recursive search."
        ),
    },
    "98c69bce_fe46_4008_a78c_30e16b51ab8e": {
        "compression_role": "sequence_transform_stress",
        "extraction": (
            "Stress transform sequences by worst monotone sidecar and residual "
            "growth."
        ),
    },
    "6d1433b9_a0b7_45b3_9cc7_bf7fdb4ddd53": {
        "compression_role": "tokenbook_tradeoff",
        "extraction": (
            "Score tokenbook additions against residual differences; dictionary "
            "expressiveness is not enough without receipt gain."
        ),
    },
    "71958997_88f3_4055_8284_bec06b6e7fc1": {
        "compression_role": "carrier_capacity",
        "extraction": (
            "Use bounded packing pressure to test whether sidecars, witnesses, "
            "and repair packets fit in the carrier budget."
        ),
    },
    "2e9c383f_d87f_4c27_ad2c_4c0960c5e04e": {
        "compression_role": "carrier_capacity",
        "extraction": (
            "Use bounded packing pressure to test tight carrier capacity before "
            "route promotion."
        ),
    },
}

DIVERSITY_GEOMETRY_PRESSURE = {
    "f5ff0dbd_0bb3_4c6b_9bf7_6a98363b935e": "route_diversity_pressure",
    "2fdd52c5_1bfb_4f3e_90b4_e9e40ce956e5": "pairwise_route_interference",
    "8177393c_d974_4ea4_a94a_0a86760e72e7": "overlapping_sidecar_coverage",
    "d1c84781_a661_49e0_9086_9f69967ef89f": "basis_exchange_pressure",
    "bdda954a_99b4_4137_a469_6adb535d63d5": "orientation_invariant_route_test",
    "aa66c428_98bb_4fa1_8da0_b7ef686ee54a": "invariant_class_route_test",
}

BACKGROUND_ONLY = {
    "52293977_6793_49d7_b09e_41b2324f6c9f": "functional_quotient_background",
    "e6797d2f_e480_4e18_bff9_f708c00cfb59": "norm_inequality_background",
    "413b3ea9_5aee_43a6_8147_e514d7dd9682": "norm_quotient_background",
    "9a90ae12_ea5d_4783_bcc4_72e0d18f55aa": "fourier_norm_background",
    "f507d54b_bba8_427f_8b39_7f06c9aaae1f": "olympiad_problem_background",
}

PROMOTION_GATE = (
    "local_evaluator_is_reproducible",
    "best_score_has_receipt",
    "route_candidate_code_is_archived",
    "rehydration_hash_matches",
    "byte_count_beats_incumbent",
    "witness_and_sidecar_budget_is_bounded",
    "nan0_status_is_false",
)

FAILURE_GATE = (
    "score_without_decode_hash_is_not_promoted",
    "gallery_score_is_not_transferable_compression_evidence",
    "unbounded_artifact_side_channel_is_pruned",
    "recursive_repair_search_becomes_nan0",
)

CLAIM_BOUNDARY = (
    "AlphaEvolve examples are imported only as evaluator/card/search-shape "
    "priors. Compression promotion still requires local encode/decode/hash/"
    "byte-count receipts."
)


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def intish(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def derive_program_count(summary: dict[str, Any], experiment: dict[str, Any]) -> int:
    stats = experiment.get("stats") or {}
    keys = (
        "programs_generated",
        "programs_analysed",
        "best_program_count",
    )
    stat_keys = (
        "database/num_programs_seen_map_elites",
        "database/num_programs_registered_map_elites",
        "database/num_programs_seen_islands",
        "database/num_programs_registered_islands",
        "database/programs_map_elites",
    )
    values = [intish(summary.get(key)) for key in keys]
    values.extend(intish(stats.get(key)) for key in stat_keys)
    numeric = [value for value in values if value is not None]
    return max(numeric) if numeric else 0


def analysed_count(summary: dict[str, Any], experiment: dict[str, Any]) -> int:
    stats = experiment.get("stats") or {}
    candidates = (
        intish(summary.get("programs_analysed")),
        intish(stats.get("analyser/programs_analysed")),
    )
    numeric = [value for value in candidates if value is not None]
    return max(numeric) if numeric else 0


def classify(experiment_id: str) -> tuple[str, str, str]:
    if experiment_id in DIRECT_USE:
        item = DIRECT_USE[experiment_id]
        return "direct", item["compression_role"], item["extraction"]
    if experiment_id in DIVERSITY_GEOMETRY_PRESSURE:
        role = DIVERSITY_GEOMETRY_PRESSURE[experiment_id]
        return (
            "diversity_geometry_pressure",
            role,
            "Use as route-diversity or geometry pressure, not as proof.",
        )
    if experiment_id in BACKGROUND_ONLY:
        role = BACKGROUND_ONLY[experiment_id]
        return (
            "background_only",
            role,
            "Keep as background search intuition only.",
        )
    return (
        "unclassified",
        "none",
        "No local compression extraction has been assigned.",
    )


def normalize_best_scores(best_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for score in best_scores:
        normalized.append({
            "gid": score.get("gid"),
            "name": score.get("name"),
            "score": score.get("score"),
        })
    return normalized


def build_card(page: dict[str, Any]) -> dict[str, Any]:
    summary = page["summary"]
    experiment = page.get("experiment") or {}
    experiment_id = summary["id"]
    applicability, role, extraction = classify(experiment_id)
    best_scores = normalize_best_scores(summary.get("best_scores") or [])
    return {
        "experiment_id": experiment_id,
        "title": summary.get("title"),
        "url": summary.get("url"),
        "description": summary.get("description"),
        "created_time": summary.get("created_time"),
        "status": summary.get("status"),
        "applicability_class": applicability,
        "compression_role": role,
        "compression_extraction": extraction,
        "route_search_mapping": {
            "experiment_card": "route_search_task_card",
            "problem_statement": "transform_family_objective",
            "best_score": "incumbent_compressed_byte_receipt",
            "program_count": "route_candidate_count",
            "analysed_count": "evaluated_route_count",
            "score_names": "pareto_or_diagnostic_receipt_fields",
        },
        "score_names": summary.get("score_names") or [],
        "best_scores": best_scores,
        "program_count": derive_program_count(summary, experiment),
        "analysed_count": analysed_count(summary, experiment),
        "best_program_count": intish(summary.get("best_program_count")) or 0,
        "evaluator_count": intish(summary.get("evaluator_count")) or 0,
        "prompt_count": intish(summary.get("prompt_count")) or 0,
        "evaluator_doc_pulled": bool(page.get("evaluators")),
        "prompt_doc_pulled": bool(page.get("prompts")),
        "best_program_docs_pulled": len(page.get("best_programs") or []),
        "archive_policy": {
            "best_programs": "referenced_best_program_documents_pulled",
            "full_program_collection": "omitted",
            "candidate_code_required_for_promotion": True,
        },
        "promotion_gate": list(PROMOTION_GATE),
        "failure_gate": list(FAILURE_GATE),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def validate(cards: list[dict[str, Any]], source_page_count: int) -> list[str]:
    errors: list[str] = []
    ids = [card["experiment_id"] for card in cards]
    if len(cards) != source_page_count:
        errors.append(f"card count {len(cards)} != source page count {source_page_count}")
    if len(set(ids)) != len(ids):
        errors.append("duplicate experiment ids in cards")
    expected = set(DIRECT_USE) | set(DIVERSITY_GEOMETRY_PRESSURE) | set(BACKGROUND_ONLY)
    actual = set(ids)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"expected experiment ids missing from pull: {missing}")
    if extra:
        errors.append(f"unclassified experiment ids in pull: {extra}")
    for card in cards:
        if not card["best_scores"]:
            errors.append(f"{card['experiment_id']} has no best scores")
        if card["analysed_count"] <= 0:
            errors.append(f"{card['experiment_id']} has no analysed count")
        if card["evaluator_count"] <= 0 or not card["evaluator_doc_pulled"]:
            errors.append(f"{card['experiment_id']} has no pulled evaluator document")
        if card["prompt_count"] <= 0 or not card["prompt_doc_pulled"]:
            errors.append(f"{card['experiment_id']} has no pulled prompt document")
    return errors


def build_receipt(input_path: Path) -> dict[str, Any]:
    pull = load_json(input_path)
    cards = [build_card(page) for page in pull.get("pages", [])]
    errors = validate(cards, int(pull.get("page_count", len(cards))))
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    class_counts: dict[str, int] = {}
    for card in cards:
        key = card["applicability_class"]
        class_counts[key] = class_counts.get(key, 0) + 1

    direct_use_cards = [
        {
            "experiment_id": card["experiment_id"],
            "title": card["title"],
            "compression_role": card["compression_role"],
            "compression_extraction": card["compression_extraction"],
        }
        for card in cards
        if card["applicability_class"] == "direct"
    ]

    receipt_without_hash = {
        "generated_at_utc": pull.get("pulled_at_utc"),
        "source_pull_path": str(input_path.relative_to(REPO)),
        "source_pull_hash": sha256_bytes(input_path.read_bytes()),
        "source": pull.get("source"),
        "root_firestore_collection": pull.get("root_firestore_collection"),
        "strategy": pull.get("strategy"),
        "card_count": len(cards),
        "class_counts": class_counts,
        "validation": {
            "all_pages_accounted": True,
            "no_duplicate_experiment_ids": True,
            "all_cards_have_best_scores": True,
            "all_cards_have_evaluator_docs": True,
            "full_generated_program_collections_pulled": False,
        },
        "runner_policy": {
            "does_not_execute_gallery_programs": True,
            "does_not_import_gallery_scores_as_compression_evidence": True,
            "keeps_decode_hash_authoritative": True,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        "compression_runner_shape": {
            "candidate_generator": "route_generator",
            "task_local_evaluator": "encode_decode_hash_byte_count",
            "best_so_far_score": "incumbent_byte_count",
            "analysed_count": "evaluated_route_count",
            "failure_packet": "nan0_or_prune_receipt",
            "archived_program_candidate": "archived_transform_recipe",
        },
        "promotion_gate": list(PROMOTION_GATE),
        "failure_gate": list(FAILURE_GATE),
        "direct_use_cards": direct_use_cards,
        "cards": cards,
    }
    receipt = dict(receipt_without_hash)
    receipt["receipt_hash"] = sha256_bytes(stable_json(receipt_without_hash).encode("utf-8"))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=PULL)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    receipt = build_receipt(args.input)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output.relative_to(REPO)}")
    print(f"receipt_hash {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
