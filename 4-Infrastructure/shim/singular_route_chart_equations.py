#!/usr/bin/env python3
"""Singular Route Chart equation group.

This crystallizes the scattered singularity logic in the Decision Diagram
Compression Tuning Prior into a named equation group.  It is a fail-closed
route-control surface: singular regions may choose finite charts and exact
residual repair, but they cannot promote without decode/hash/byte-count
verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path(
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Decision Diagram Compression Tuning Prior.tid"
)
DEFAULT_RECEIPT = Path("4-Infrastructure/shim/singular_route_chart_equations_receipt.json")
DEFAULT_CURRICULUM = Path("4-Infrastructure/shim/singular_route_chart_equations_curriculum.jsonl")


SINGULAR_MARKERS = (
    "singular",
    "singularity",
    "NaN0",
    "FiniteBundleChart",
    "canonical blow-up",
    "blow-up ranking",
    "unresolved_metadata_hold",
    "fail closed",
)


SINGULAR_ROUTE_CHART = {
    "name": "SingularRouteChart",
    "purpose": (
        "Turn singular, non-transverse, unbounded, ambiguous, or metadata-held "
        "route regions into finite chart attempts with ranked failure and exact "
        "residual repair."
    ),
    "primary_function": "detect -> chart -> rank -> bound -> repair -> verify_or_NaN0",
    "claim_boundary": (
        "A singular chart is a route-control and fail-closed device. It is not "
        "compression evidence unless decoded bytes hash to the source and total "
        "measured bytes beat the incumbent."
    ),
}


EQUATIONS = [
    {
        "id": "SRC0_detect_singularity",
        "equation": "sigma(r) = class(route_region_r)",
        "meaning": (
            "Classify the route region as regular, singular, non_transverse, "
            "non_locally_trivial, unbounded, ambiguous, or metadata_hold."
        ),
        "inputs": ["route_region_r", "receipt_class", "claim_boundary_status"],
        "outputs": ["singularity_class", "singularity_status"],
        "fail_closed_when": "class is unbounded or metadata is unverified",
    },
    {
        "id": "SRC1_choose_finite_chart",
        "equation": "C_s = framework(sigma(r), failure_mode_r)",
        "meaning": (
            "Select the smallest finite chart family for the singular region: "
            "derived_stack, diffeological_pseudobundle, banach_hilbert_bundle, "
            "principal_infinity_bundle, noncommutative_bundle, or fredholm_bundle."
        ),
        "inputs": ["singularity_class", "failure_mode_r"],
        "outputs": ["framework_family_id", "bundle_chart_id", "finite_rank_proxy_id"],
        "fail_closed_when": "no finite chart can be explicit",
    },
    {
        "id": "SRC2_project_to_finite_proxy",
        "equation": (
            "RouteChart_c = P_finite(Section_c, framework_family_id, "
            "norm_bound_id, gauge_coherence_receipt) + exact_residual_lane_c"
        ),
        "meaning": (
            "Never serialize the infinite or singular object. Project it into a "
            "finite proxy and attach an exact residual lane."
        ),
        "inputs": [
            "local_section_id",
            "framework_family_id",
            "norm_bound_id",
            "gauge_coherence_receipt",
            "source_hash",
        ],
        "outputs": ["finite_rank_proxy_id", "exact_residual_lane_id"],
        "fail_closed_when": "finite proxy lacks exact residual repair",
    },
    {
        "id": "SRC3_rank_blowup_failure",
        "equation": "rho_{t+1} < rho_t for every repair step",
        "meaning": (
            "Use a well-founded blow-up rank so singular repair cannot become "
            "recursive search."
        ),
        "inputs": ["blowup_rank_t", "repair_step_t"],
        "outputs": ["blowup_rank_next", "repair_path_depth"],
        "fail_closed_when": "rank does not decrease or repair depth exceeds budget",
    },
    {
        "id": "SRC4_bound_singular_cost",
        "equation": (
            "LB_s = chart_header + singularity_receipt + rank_receipt + "
            "norm_bound_receipt + exact_residual_floor"
        ),
        "meaning": (
            "Charge singularity handling before expensive evaluation. Prune if "
            "the lower bound cannot beat the incumbent."
        ),
        "inputs": [
            "chart_header_bytes",
            "singularity_receipt_bytes",
            "rank_receipt_bytes",
            "norm_bound_receipt_bytes",
            "exact_residual_floor",
        ],
        "outputs": ["singular_lower_bound_bytes"],
        "fail_closed_when": "lower bound exceeds incumbent",
    },
    {
        "id": "SRC5_verify_or_nan0",
        "equation": (
            "close_s iff hash(decode(RouteChart_c)) == source_hash and "
            "nan0_flag == 0"
        ),
        "meaning": "The singular chart closes only through byte-exact decode and NaN0 false.",
        "inputs": ["RouteChart_c", "source_hash", "nan0_flag"],
        "outputs": ["byte_rehydration_hash", "closure_status"],
        "fail_closed_when": "decode hash mismatches or nan0_flag is true",
    },
    {
        "id": "SRC6_promote_singular_route",
        "equation": (
            "promote_s iff close_s and total_bytes_s < incumbent_bytes and "
            "ratio_schema is explicit"
        ),
        "meaning": (
            "Promotion authority remains measured bytes and exact hash; singular "
            "math only controls safe charting and pruning."
        ),
        "inputs": ["closure_status", "total_bytes_s", "incumbent_bytes", "ratio_schema"],
        "outputs": ["promotion_status"],
        "fail_closed_when": "any receipt, byte count, or ratio schema is missing",
    },
]


DD_STATE_EXTENSION = [
    "singular_route_chart_id",
    "singularity_class",
    "singularity_status",
    "framework_family_id",
    "bundle_chart_id",
    "finite_rank_proxy_id",
    "norm_bound_id",
    "gauge_coherence_receipt_id",
    "index_witness_id",
    "blowup_rank",
    "repair_path_depth",
    "singular_lower_bound_bytes",
    "exact_residual_lane_id",
    "nan0_flag",
    "byte_rehydration_hash",
]


CANDIDATE_EDGES = [
    "detect_singular_route_region",
    "choose_singular_finite_chart",
    "project_singular_to_finite_proxy",
    "rank_blowup_failure",
    "bound_singular_route_cost",
    "emit_singular_exact_residual",
    "verify_singular_decode_hash",
    "promote_singular_route_or_nan0",
]


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_surface(text: str) -> str:
    marker = "\n!! Citation Math Function Distillation\n"
    if marker not in text:
        return text
    before, after = text.split(marker, 1)
    next_marker = "\n!! Where To Tune Next\n"
    if next_marker in after:
        _, tail = after.split(next_marker, 1)
        return before + next_marker + tail
    return before


def extract_singular_evidence(source_text: str) -> dict[str, Any]:
    lines = source_surface(source_text).splitlines()
    hits: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        folded = line.lower()
        if any(marker.lower() in folded for marker in SINGULAR_MARKERS):
            hits.append({"line": idx, "text": line.strip()})
    return {
        "matched_line_count": len(hits),
        "markers": list(SINGULAR_MARKERS),
        "sample_hits": hits[:40],
        "source_surface_sha256": hashlib.sha256(source_surface(source_text).encode("utf-8")).hexdigest(),
    }


def build_receipt(source: Path) -> dict[str, Any]:
    source_text = source.read_text(encoding="utf-8")
    evidence = extract_singular_evidence(source_text)
    receipt: dict[str, Any] = {
        "schema": "singular_route_chart_equations_v1",
        "generated_at": "2026-05-08T00:00:00+00:00",
        "source_tiddler": str(source),
        "source_surface_scope": (
            "tiddler excluding generated Citation Math Function Distillation and "
            "Singular Route Chart Equation Group sections"
        ),
        "singular_evidence": evidence,
        "singular_route_chart": SINGULAR_ROUTE_CHART,
        "equations": EQUATIONS,
        "dd_state_extension": DD_STATE_EXTENSION,
        "candidate_edges": CANDIDATE_EDGES,
        "promotion_rule": (
            "promote singular route iff finite chart is explicit, blow-up rank "
            "decreases, lower bound beats incumbent, exact residual repairs bytes, "
            "decoded hash matches, nan0_flag is false, and measured bytes beat "
            "the incumbent under an explicit ratio_schema"
        ),
        "failure_rule": (
            "unbounded section, non-decreasing repair rank, missing singularity "
            "receipt, hidden payload in chart, metadata hold, hash mismatch, or "
            "NaN0 all fail closed"
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = (
        "You are a SingularRouteChart controller. Convert singular route "
        "regions into finite, receipted, byte-exact chart attempts or fail closed."
    )
    records: list[dict[str, Any]] = []
    for equation in receipt["equations"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "apply_singular_route_chart_equation",
                                "equation_id": equation["id"],
                                "equation": equation["equation"],
                                "inputs": equation["inputs"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "outputs": equation["outputs"],
                                "meaning": equation["meaning"],
                                "fail_closed_when": equation["fail_closed_when"],
                                "promotion_authority": "decode/hash/byte-count receipt",
                            },
                            ensure_ascii=False,
                        ),
                    },
                ]
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    args = parser.parse_args()

    receipt = build_receipt(args.source)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
