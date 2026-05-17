#!/usr/bin/env python3
"""Transfold Hutter-style equations into a receipt-authoritative metastate.

This does not recompress data.  It translates the existing Hutter equation
surfaces into the stricter route/evaluator state required by the bounded exact
route compiler:

    proposal score -> candidate route coordinate -> exact receipt boundary

The useful move is to keep speculative equation fields as proposal features
while making exact decode/hash/byte accounting the only promotion authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "hutter_equation_metastate_transfold_receipt.json"
CURRICULUM_OUT = SHIM / "hutter_equation_metastate_transfold_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"
HUTTER_ENWIK9_TARGET_BYTES = 109_685_197

SOURCE_SURFACES = {
    "hutter_prize_equation_markdown": REPO
    / "6-Documentation"
    / "papers"
    / "OTOM"
    / "04_Hutter_Prize_Equation.md",
    "hutter_derivation_spec": REPO
    / "5-Applications"
    / "hutter_prize"
    / "DERIVATION_SPEC.md",
    "hutter_architecture": REPO
    / "5-Applications"
    / "hutter_prize"
    / "ARCHITECTURE.md",
    "hutter_static_target_omindirection_prior": REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Hutter Static Target Omindirection Prior.tid",
    "hutter_prize_compression_lean": REPO
    / "0-Core-Formalism"
    / "lean"
    / "Semantics"
    / "Semantics"
    / "HutterPrizeCompression.lean",
    "hutter_prize_flow_lean": REPO
    / "0-Core-Formalism"
    / "lean"
    / "Semantics"
    / "Semantics"
    / "HutterPrizeFlow.lean",
}

SOURCE_RECEIPTS = {
    "projectable_geometry_topology_model": SHIM
    / "projectable_geometry_topology_model_receipt.json",
    "dimensional_shell_dd_probe": SHIM / "dimensional_shell_dd_probe_receipt.json",
    "dd_target_implementation_reevaluation": SHIM
    / "dd_target_implementation_reevaluation_receipt.json",
    "compression_ratio_rederivation": SHIM
    / "compression_ratio_rederivation_receipt.json",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def file_record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": rel(path),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def receipt_hash(path: Path, data: dict[str, Any]) -> str:
    for key in (
        "receipt_hash",
        "stable_topology_model_hash_sha256",
        "stable_shell_dd_hash_sha256",
    ):
        value = data.get(key)
        if isinstance(value, str):
            return value
    return sha256_bytes(path.read_bytes())


def source_surface_records() -> dict[str, dict[str, Any]]:
    return {name: file_record(path) for name, path in SOURCE_SURFACES.items()}


def source_receipt_records(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "path": rel(SOURCE_RECEIPTS[name]),
            "schema": receipt.get("schema", "unknown"),
            "hash": receipt_hash(SOURCE_RECEIPTS[name], receipt),
        }
        for name, receipt in receipts.items()
    }


def current_best_metastate(topology: dict[str, Any], dd_target: dict[str, Any]) -> dict[str, Any]:
    selected = topology["best_approach"]["selected_route"]
    hard_target = dd_target.get("current_target", {}).get(
        "hard_target_bytes_enwik9", HUTTER_ENWIK9_TARGET_BYTES
    )
    projected = dd_target["current_best_implemented_route"].get(
        "projected_enwik9_total_bytes"
    )
    gap = None if projected is None else projected - hard_target
    return {
        "source_corpus_id": selected["slice"],
        "source_bytes": selected["source_bytes"],
        "candidate_chart": "xml_token_topology_witness_bz2",
        "transform_route": topology["best_approach"]["route"],
        "payload_bytes": selected["compressed_bytes"],
        "residual_bytes": 0,
        "witness_bytes": selected["topology_witness_bytes"],
        "decoder_delta_bytes": 0,
        "container_bytes": 0,
        "compressed_total_bytes": selected["modeled_total_bytes"],
        "baseline_bytes": selected["raw_baseline_bytes"],
        "margin_vs_baseline_bytes": selected["gain_vs_raw_after_topology_bytes"],
        "ratio_schema": "modeled_total_bytes / source_bytes; local slice diagnostic",
        "modeled_ratio": selected["modeled_ratio"],
        "hard_target_bytes_enwik9": hard_target,
        "projected_enwik9_total_bytes": projected,
        "projected_gap_to_hard_target_bytes": gap,
        "exact_decode_status": "inherited_from_existing_reversible_measurement_receipts",
        "source_hash_status": "not_embedded_in_topology_receipt",
        "decoded_hash_status": "not_embedded_in_topology_receipt",
        "promotion_status": (
            "current_small_slice_incumbent_only; not a Hutter Prize claim"
        ),
        "failure_code": None,
    }


def hutter_transfold_equations() -> dict[str, Any]:
    return {
        "source_equation_surface": (
            "C = proposal_score(comp, phys, geom, scaling) or "
            "phi_HP = field + compression_gain + decoder/resource penalties"
        ),
        "metastate_transfold": (
            "proposal_score -> candidate_route_coordinate -> "
            "bounded_exact_route_metastate -> promotion_receipt"
        ),
        "hutter_route_metastate": [
            "source_corpus_id",
            "source_bytes",
            "candidate_chart",
            "transform_route",
            "payload_bytes",
            "residual_bytes",
            "witness_bytes",
            "decoder_delta_bytes",
            "container_bytes",
            "runtime_budget",
            "compressed_total_bytes",
            "baseline_bytes",
            "hard_target_bytes",
            "ratio_schema",
            "exact_decode_status",
            "source_hash",
            "decoded_hash",
            "promotion_status",
            "failure_code",
        ],
        "counted_total": (
            "compressed_total_bytes = payload_bytes + residual_bytes + "
            "witness_bytes + decoder_delta_bytes + container_bytes"
        ),
        "lower_bound": (
            "LB_route = payload_floor + residual_floor + witness_floor + "
            "decoder_delta_floor + container_floor + evaluator_cost_floor"
        ),
        "prune_rule": "prune iff LB_route >= incumbent_bytes",
        "promotion_rule": (
            "promote iff decoded_hash == source_hash and compressed_total_bytes "
            "< incumbent_bytes and ratio_schema is explicit and all witness, "
            "residual, decoder, and container bytes are counted"
        ),
        "hard_target_rule": (
            "Hutter-hard promotion additionally requires the total contest artifact "
            "for enwik9 to beat 109685197 bytes under the applicable prize rules"
        ),
    }


def bridge_lanes() -> list[dict[str, Any]]:
    return [
        {
            "lane": "symbolic_score_to_route_feature",
            "input": "C_comp, C_phys, C_geom, S, G, F, rho",
            "metastate_role": "proposal coordinate / search prior",
            "promotion_authority": "none",
        },
        {
            "lane": "flow_penalty_to_lower_bound",
            "input": "decoder penalty, resource penalty, tau, sigma, q",
            "metastate_role": "lower-bound and prune pressure",
            "promotion_authority": "none unless counted in bytes/runtime receipt",
        },
        {
            "lane": "trinary_vm_to_decoder_boundary",
            "input": "declared rules, subregister trace, deterministic program",
            "metastate_role": "portable reconstruction contract",
            "promotion_authority": "exact replay only after source hash matches",
        },
        {
            "lane": "topology_witness_to_counted_metadata",
            "input": "Menger/Torus/Braid/NaN0 16-byte witness",
            "metastate_role": "bounded control-plane witness",
            "promotion_authority": "only if route margin survives witness bytes",
        },
        {
            "lane": "residual_to_byte_authority",
            "input": "sidecar, repair lane, exact rehydration",
            "metastate_role": "restore all bytes removed by proposal charts",
            "promotion_authority": "decoded_hash == source_hash",
        },
    ]


def implications(best: dict[str, Any]) -> list[dict[str, Any]]:
    margin = int(best["margin_vs_baseline_bytes"])
    return [
        {
            "id": "winning_equation_demotion",
            "implication": (
                "The weighted Hutter score is useful as a route-search coordinate, "
                "not as a byte claim."
            ),
        },
        {
            "id": "metastate_authority",
            "implication": (
                "The metastate's invariant root is exact reconstruction under "
                "counted compressed_total_bytes."
            ),
        },
        {
            "id": "current_margin_constraint",
            "implication": (
                f"The current small-slice route has {margin} bytes of margin after "
                "the 16-byte topology witness; additional overlays must earn their "
                "own payload savings before promotion."
            ),
        },
        {
            "id": "hutter_gap",
            "implication": (
                "The current projected enwik9 size remains diagnostic only and is "
                "far above the hard target; the next useful work is payload-saving "
                "transforms, not more unpriced metadata."
            ),
        },
    ]


def research_tasks() -> list[dict[str, str]]:
    return [
        {
            "id": "embed_hash_authority",
            "task": "carry source_hash and decoded_hash through every local Hutter route receipt",
        },
        {
            "id": "route_matrix_wrapper",
            "task": "evaluate candidate charts with payload/residual/witness/decoder/container byte columns",
        },
        {
            "id": "demote_unpriced_scores",
            "task": "treat physics/geometric/topology scores as priors until exact route bytes exist",
        },
        {
            "id": "payload_transform_trials",
            "task": "test corpus-resolution, fascicle, tokenbook, and residualized normalization routes",
        },
        {
            "id": "lean_alignment",
            "task": "align Lean Hutter score modules with the metastate distinction between proposal score and promotion receipt",
        },
    ]


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for lane in receipt["bridge_lanes"]:
        lines.append({"type": "bridge_lane", **lane})
    for item in receipt["metastate_implications"]:
        lines.append({"type": "implication", **item})
    for item in receipt["research_tasks"]:
        lines.append({"type": "research_task", **item})
    return lines


def build_receipt() -> dict[str, Any]:
    receipts = {name: load_json(path) for name, path in SOURCE_RECEIPTS.items()}
    best = current_best_metastate(
        receipts["projectable_geometry_topology_model"],
        receipts["dd_target_implementation_reevaluation"],
    )
    receipt: dict[str, Any] = {
        "schema": "hutter_equation_metastate_transfold_v1",
        "generated_at": GENERATED_AT,
        "runner": rel(Path(__file__)),
        "source_surfaces": source_surface_records(),
        "source_receipts": source_receipt_records(receipts),
        "transfold_definition": (
            "Transfold the Hutter equation surface from symbolic compression score "
            "into a bounded exact route metastate whose invariant root is exact "
            "decode plus counted byte total."
        ),
        "hutter_transfold_equations": hutter_transfold_equations(),
        "bridge_lanes": bridge_lanes(),
        "current_best_metastate": best,
        "metastate_implications": implications(best),
        "research_tasks": research_tasks(),
        "claim_boundary": (
            "This is a Hutter-equation transfold and receipt-indexing artifact. "
            "It does not recompress data, improve byte counts, prove optimality, "
            "or make a Hutter Prize submission. Promotion still requires exact "
            "encode/decode/hash verification and measured total bytes with every "
            "witness, residual, decoder, and container cost counted."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_bytes(stable_json(preimage).encode("utf-8"))
    return receipt


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = curriculum_lines(receipt)
    CURRICULUM_OUT.write_text(
        "".join(json.dumps(line, sort_keys=True) + "\n" for line in lines),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "receipt": rel(OUT),
                "curriculum": rel(CURRICULUM_OUT),
                "receipt_hash": receipt["receipt_hash"],
                "bridge_lane_count": len(receipt["bridge_lanes"]),
                "research_task_count": len(receipt["research_tasks"]),
                "current_route": receipt["current_best_metastate"]["transform_route"],
                "current_total_bytes": receipt["current_best_metastate"][
                    "compressed_total_bytes"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
