#!/usr/bin/env python3
"""Compile the fractal-Go-on-T16 idea into the existing PIST bundle prior.

The tiddler already selected ``pist_nd_bundle`` over Go tiles as the native
topology witness primitive.  This receipt keeps that decision: fractal Go is
useful as a rule-language prior, but the serializable route primitive remains
a sparse PIST bundle packet with exact residual repair.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Decision Diagram Compression Tuning Prior.tid"
)
OUT = SHIM / "fractal_go_t16_pist_bridge_receipt.json"
CURRICULUM_OUT = SHIM / "fractal_go_t16_pist_bridge_curriculum.jsonl"
ARCHIVE = Path("/home/allaun/Documents/ingest/ChatGPT-Batch-2026-05-08.zip")
REFINEMENT_MEMBER = "ChatGPT-16D_Torus_with_Go_Tiles.json"
GENERATED_SECTION = "!! Fractal Go T16 PIST Bridge"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def tiddler_source_surface() -> str:
    """Read the source tiddler without this generated bridge section."""
    text = TIDDLER.read_text(encoding="utf-8")
    kept: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.strip() == GENERATED_SECTION:
            skipping = True
            continue
        if skipping and line.startswith("!! "):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def source_evidence() -> dict[str, Any]:
    text = tiddler_source_surface()
    markers = [
        "16D torus should use nD PIST rather than Go tiles",
        "pist_nd_bundle",
        "Do not simulate a full 16D torus board",
        "Store sparse active PIST bundle packets",
        "T16 = (S1)^16",
        "Percolating the 16D Hypercube",
    ]
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for marker in markers:
            if marker in line:
                hits.append({"line": lineno, "marker": marker, "text": line.strip()})
    return {
        "source_tiddler": rel(TIDDLER),
        "source_sha256": sha256_bytes(text.encode("utf-8")),
        "generated_section_excluded": GENERATED_SECTION,
        "markers": markers,
        "hits": hits,
    }


def archive_evidence() -> dict[str, Any]:
    archive_bytes = ARCHIVE.read_bytes()
    with zipfile.ZipFile(ARCHIVE) as zf:
        names = zf.namelist()
        raw = zf.read(REFINEMENT_MEMBER)
    chat = json.loads(raw.decode("utf-8"))
    body = "\n\n".join(str(message.get("content", "")) for message in chat.get("messages", []))
    markers = [
        "16D torus",
        "fractal Go",
        "goxel",
        "liberties",
        "capture",
        "ko",
        "territory",
        "AMMR",
        "O-AMMR",
        "G16 = (T16, Sigma, N, F, R, Pi)",
        "|Omega| = b^(m^16)",
        "Do not simulate the full torus",
    ]
    marker_hits = [marker for marker in markers if marker.lower() in body.lower()]
    return {
        "archive_path": str(ARCHIVE),
        "archive_sha256": sha256_bytes(archive_bytes),
        "member_count": len(names),
        "member_names": names,
        "refinement_member": REFINEMENT_MEMBER,
        "refinement_sha256": sha256_bytes(raw),
        "title": chat.get("title"),
        "timestamp": chat.get("timestamp"),
        "url": chat.get("url"),
        "message_count": len(chat.get("messages", [])),
        "marker_hits": marker_hits,
        "extracted_model": {
            "compact_space": "T16 = (S1)^16",
            "rule_language": "fractal_go_goxel_automaton",
            "native_packet": "sparse_pist_bundle_packet",
            "explosion_guard": "materialize active goxel packets only",
            "claim_boundary": "proposal/pruning prior until exact residual decode/hash/byte count closes",
        },
    }


SELF_FOLDED_CANDIDATES = [
    {
        "id": "sixteen_orthoplex",
        "role": "axis_pinched_basis",
        "useful_as": "sharp sparse axis carrier / signed basis proposal",
        "not_useful_as": "full route payload or proof of byte compression",
        "verdict": "proposal_feature",
    },
    {
        "id": "barnes_wall_lambda_16",
        "role": "dense_owner_lattice",
        "useful_as": "future deterministic owner quantizer or packing diagnostic in 16D",
        "not_useful_as": "serializable lattice payload without measured overhead",
        "verdict": "diagnostic_until_receipted",
    },
    {
        "id": "calabi_yau_8_complex",
        "role": "continuous_topological_fold_metaphor",
        "useful_as": "language for compactification / cycle bookkeeping",
        "not_useful_as": "finite compression primitive in this stack",
        "verdict": "background_only",
    },
    {
        "id": "sixteen_cube",
        "role": "active_frontier_reference",
        "useful_as": "65536-state activation/card prior and hypercube reachability check",
        "not_useful_as": "full materialized 16D board",
        "verdict": "frontier_model_only",
    },
]

GO_TO_PIST_COMPILATION = [
    {
        "go_term": "placement",
        "compiled_role": "open_sparse_bundle_packet",
        "receipt_field": "active_bundle_id",
    },
    {
        "go_term": "liberties",
        "compiled_role": "admissible_continuation_count",
        "receipt_field": "liberty_count",
    },
    {
        "go_term": "capture",
        "compiled_role": "residual_or_void_collapse",
        "receipt_field": "capture_receipt_id",
    },
    {
        "go_term": "territory",
        "compiled_role": "deterministic_owner_region",
        "receipt_field": "owner_route_id",
    },
    {
        "go_term": "ko",
        "compiled_role": "no_repeat_invalid_trace",
        "receipt_field": "ko_trace_hash",
    },
    {
        "go_term": "fractal_scale",
        "compiled_role": "pist_shell_base_and_offset",
        "receipt_field": "shell_k_offset_t",
    },
]

EQUATIONS = [
    {
        "id": "FG0_torus_phase_space",
        "equation": "T16 = (S1)^16; theta_i == theta_i + 2*pi",
        "meaning": "Use compact cyclic phase space so boundary failure becomes recurrence or capture, not infinity.",
    },
    {
        "id": "FG1_tile_state",
        "equation": "sigma_i = (occupancy, chi, kappa, rho, lambda_mode, epsilon_budget, q, scale)",
        "meaning": "Treat a Go tile as a bounded diagnostic state packet, not as payload.",
    },
    {
        "id": "FG2_sparse_automaton",
        "equation": "G16 = (T16, Sigma, N, F, R, Pi)",
        "meaning": "Fractal Go is a compact recursive admissibility automaton over toroidal phase space.",
    },
    {
        "id": "FG3_liberties",
        "equation": "L(G_i) = {n in N(i) | A(n) == admissible}",
        "meaning": "Liberties measure admissible continuation rather than board-game freedom.",
    },
    {
        "id": "FG4_capture",
        "equation": "|L(G_i)| == 0 -> residual_lane or void_receipt or archive_packet or shadow_projection",
        "meaning": "Capture is topological cleanup: collapse unstable state into a bounded receipt path.",
    },
    {
        "id": "FG5_multiscale_update",
        "equation": "sigma_i^k(t+1) = F(N_i^k, P_down(sigma^(k+1)), P_up(sigma^(k-1)), Phi)",
        "meaning": "Fine tiles supply detail; coarse tiles enforce law; projections must be receipted.",
    },
    {
        "id": "FG6_state_explosion_guard",
        "equation": "|Omega| = b^(m^16); materialize(active_packets) only",
        "meaning": "Never store or search the full 16D board.",
    },
    {
        "id": "FG7_pist_compilation",
        "equation": "GoTile_i^k -> PistBundlePacket(shell_k, offset_t, fiber_vector_hash, phase, residual_budget, receipt_hash)",
        "meaning": "The native implementation target is sparse PIST bundle packets.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "fractal_go_t16_pist_bridge_v1",
        "generated_at": GENERATED_AT,
        "archive_evidence": archive_evidence(),
        "source_evidence": source_evidence(),
        "primary_decision": {
            "name": "compile_fractal_go_to_sparse_pist_bundle",
            "statement": (
                "Use fractal Go as a rule-language prior for liberties, capture, "
                "territory, ko, and multiscale admissibility; keep PIST bundle "
                "packets as the serializable route primitive."
            ),
            "native_primitive": "pist_nd_bundle",
            "rejected_native_primitive": "full_fractal_go_t16_board",
        },
        "self_folded_shape_verdicts": SELF_FOLDED_CANDIDATES,
        "go_to_pist_compilation": GO_TO_PIST_COMPILATION,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "t16_phase_key",
            "goxel_packet_id",
            "tile_occupancy_class",
            "chirality_class",
            "curvature_class",
            "density_mass_class",
            "spectral_mode_class",
            "liberty_count",
            "capture_receipt_id",
            "ko_trace_hash",
            "fractal_scale_k",
            "pist_shell_k",
            "pist_offset_t",
            "fiber_vector_hash",
            "owner_route_id",
            "residual_lane_id",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "open_sparse_goxel_packet",
            "compute_toroidal_neighbor_liberties",
            "capture_zero_liberty_region",
            "route_territory_to_owner",
            "reject_ko_trace_repeat",
            "project_fractal_scale_to_pist_bundle",
            "emit_exact_residual_lane",
            "close_with_rehydration_hash",
        ],
        "promotion_rule": [
            "fractal_go_layer_only_proposes_or_prunes_routes",
            "full_t16_board_is_never_materialized",
            "zero_liberty_capture_emits_bounded_receipt",
            "ko_trace_hash_prevents_recursive_invalid_loops",
            "pist_bundle_packet_fits_witness_budget",
            "exact_residual_lane_restores_source_bytes",
            "decoded_hash_matches_source",
            "measured_total_bytes_beats_incumbent",
        ],
        "failure_rule": [
            "full_board_materialization -> NaN0",
            "capture_without_residual_or_void_receipt -> fail_closed",
            "ko_repeat_without_trace_hash -> NaN0",
            "continuous_shape_claim_without_finite_packet -> diagnostic_only",
            "witness_bytes_exceed_remaining_margin -> prune",
        ],
        "claim_boundary": (
            "This receipt compiles a conceptual fractal-Go/T16 state machine into "
            "the existing sparse PIST bundle discipline. It is not a compression "
            "result and does not promote a route without exact decode/hash/byte "
            "measurement."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_bytes(stable_json(preimage).encode("utf-8"))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["self_folded_shape_verdicts"]:
        lines.append({"type": "shape_verdict", **item})
    for item in receipt["go_to_pist_compilation"]:
        lines.append({"type": "compilation_rule", **item})
    for item in receipt["equations"]:
        lines.append({"type": "equation", **item})
    return lines


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = curriculum_lines(receipt)
    CURRICULUM_OUT.write_text(
        "".join(json.dumps(line, sort_keys=True) + "\n" for line in lines),
        encoding="utf-8",
    )
    print(json.dumps({
        "receipt": rel(OUT),
        "curriculum": rel(CURRICULUM_OUT),
        "receipt_hash": receipt["receipt_hash"],
        "curriculum_records": len(lines),
        "decision": receipt["primary_decision"]["name"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
