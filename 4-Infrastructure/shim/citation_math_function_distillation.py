#!/usr/bin/env python3
"""Distill cited priors into math/function groups.

This runner treats the Decision Diagram Compression Tuning Prior tiddler as the
source surface. It extracts the local citation footprint, then records a
bounded synthesis: what mathematical role each citation family contributes and
what primary compressor function it should serve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path(
    "6-Documentation/tiddlywiki-local/wiki/tiddlers/Decision Diagram Compression Tuning Prior.tid"
)
DEFAULT_RECEIPT = Path("4-Infrastructure/shim/citation_math_function_distillation_receipt.json")
DEFAULT_CURRICULUM = Path(
    "4-Infrastructure/shim/citation_math_function_distillation_curriculum.jsonl"
)


PRIMARY_FUNCTION = {
    "name": "bounded_exact_route_compiler",
    "statement": (
        "Use citations as route priors that propose, bound, transport, fold, "
        "allocate, repair, or verify transform routes; promote only after local "
        "encode/decode/hash/byte-count receipt beats the incumbent."
    ),
    "function_chain": [
        "observe_corpus_structure",
        "propose_route_family",
        "bound_witness_sidecar_and_compute_cost",
        "route_to_deterministic_owner",
        "fold_or_factor_only_when_reachability_is_preserved",
        "emit_exact_residual_repair",
        "verify_rehydration_hash",
        "measure_total_bytes_under_one_ratio_schema",
        "promote_or_fail_closed",
    ],
}


FUNCTION_GROUPS = [
    {
        "id": "exact_outer_inner_route_search",
        "source_examples": [
            "An Exact Framework for Solving the Space-Time Dependent TSP",
            "decision diagram / branch-and-bound route planning",
        ],
        "math_shape": "outer discrete route search + expensive inner evaluator + bounds",
        "primary_function": "turn transform tuning into a prunable decision diagram",
        "dd_role": "search_and_bound",
    },
    {
        "id": "bounded_topology_closure",
        "source_examples": [
            "Invariant dual mechanics of tensegrity and origami",
            "deterministic routing",
            "Menger-Torus-Braid Shell Route v0",
            "T16 nD Bundle PIST Shell Machine",
        ],
        "math_shape": "finite witness fields + closure classes + deterministic owners",
        "primary_function": "prevent topology metaphors from becoming recursive sidecars",
        "dd_role": "closure_guard",
    },
    {
        "id": "finite_group_fiber_invariant_recursion",
        "source_examples": [
            "Cayley fibergraph visualization",
            "Q8 quaternion product fibers",
            "stator-indexed contraction",
            "braided fiber connector",
            "axial core",
        ],
        "math_shape": "finite group action + product fiber + bounded substitution + invariant axis",
        "primary_function": "generate structured route families while keeping recursion finite and receipted",
        "dd_role": "invariant_route_generator",
    },
    {
        "id": "bundle_transport_framework_selection",
        "source_examples": [
            "fibered n-spaces",
            "Parseval frames for vector bundles",
            "quaternionic slice regular functions",
            "infinite-dimensional differential geometry",
            "diffeological pseudobundles",
            "Fredholm bundles",
        ],
        "math_shape": "base space + fiber + section + frame + transport + finite chart",
        "primary_function": "choose the smallest bounded chart that can carry exact residual repair",
        "dd_role": "framework_switchboard",
    },
    {
        "id": "state_machine_folding_reachability",
        "source_examples": [
            "Recursive State Machine Guided Graph Folding for CFL Reachability",
            "TF-Label topological-folding reachability",
            "origami and kirigami folding complexity",
        ],
        "math_shape": "quotient graph / folded state machine preserving reachability",
        "primary_function": "collapse equivalent DD states only when exact decode reachability is unchanged",
        "dd_role": "frontier_reducer",
    },
    {
        "id": "consensus_repair_and_topology_robustness",
        "source_examples": [
            "DeepConsensus",
            "CANOS N-1 topology robust solver",
            "gap-aware alignment",
        ],
        "math_shape": "multiple weak observations + perturbation + exact validator",
        "primary_function": "repair route observations and stress promoted routes without relaxing exactness",
        "dd_role": "repair_and_stress_test",
    },
    {
        "id": "evolutionary_route_population",
        "source_examples": [
            "OpenEvolve",
            "AlphaEvolve example gallery",
            "MAP-Elites / islands / evaluator score",
        ],
        "math_shape": "quality-diversity population + evaluator + archive",
        "primary_function": "expand the candidate frontier while keeping evaluator receipts authoritative",
        "dd_role": "proposal_engine",
    },
    {
        "id": "ratio_quality_and_measurement_schema",
        "source_examples": [
            "Syllabic compression effective compression ratios",
            "Definition of Compression Ratio: JPEG2000 library differences",
            "compression quality coupling",
        ],
        "math_shape": "nominal setting != achieved ratio; parameters couple to quality and overhead",
        "primary_function": "force actual byte measurement under one explicit ratio schema",
        "dd_role": "measurement_normalizer",
    },
    {
        "id": "semantic_information_limits_and_allocation",
        "source_examples": [
            "Semantic Rate-Distortion Theory",
            "information bottleneck",
            "semantic arithmetic coding",
            "probabilistic semantic communication with RSMA",
            "prompt compression rate-distortion",
        ],
        "math_shape": "semantic entropy/rate-distortion/bottleneck + side information and resource budgets",
        "primary_function": "turn semantic theory into budget coordinates, not byte-loss permission",
        "dd_role": "semantic_budget_model",
    },
    {
        "id": "adaptive_predictor_with_exact_residual",
        "source_examples": [
            "SZ-style error-controlled scientific compression",
            "Lorenzo / regression predictors",
            "block-local predictor selection",
        ],
        "math_shape": "local predictor family + diagnostic error bound + exact residual repair",
        "primary_function": "use lossy predictors as sketches only when residual lanes restore bytes",
        "dd_role": "sketch_then_repair",
    },
    {
        "id": "semantic_corpus_resolution",
        "source_examples": [
            "fascicles",
            "ItCompress",
            "SPARTAN",
            "DeepSqueeze",
            "semantic trajectories",
            "embedding wavelet subbands",
        ],
        "math_shape": "record/attribute lanes + compact bundles + model predictions + residual lanes",
        "primary_function": "raise corpus resolution so proposals are local, reversible, and byte-authorized",
        "dd_role": "corpus_observation_stack",
    },
    {
        "id": "syntax_semantic_feature_witnesses",
        "source_examples": [
            "dependency-based text compression",
            "DeepSIC",
            "compression-ratio vector representation",
        ],
        "math_shape": "skeleton/head/feature projection + diagnostic witness + residualized deletion",
        "primary_function": "share semantic or syntactic features with the route while paying witness bytes",
        "dd_role": "feature_witness_surface",
    },
    {
        "id": "non_euclidean_semantic_kv_tree_store",
        "source_examples": [
            "Riemannian manifold learning",
            "Cartan-Hadamard sliced-Wasserstein flows",
            "TinyEnc",
            "TreeKV",
            "Tree Fiddy",
            "GEAR / low-rank KV cache compression",
        ],
        "math_shape": "curved key manifold + compressed/encrypted byte store + tree-bounded cache route",
        "primary_function": "separate key geometry, store bytes, cache approximation, and exact residual authority",
        "dd_role": "semantic_kv_bridge",
    },
    {
        "id": "multistate_geometry_addressability",
        "source_examples": [
            "multistable origami metasurfaces",
            "manifold geometric deep learning",
            "tensor network geometry",
            "quantum phase geometry",
            "programmable multistability limits",
        ],
        "math_shape": "many stable states + controllability/addressability/energy/tolerance gates",
        "primary_function": "prune route states that are stable-looking but not addressable, bounded, or exact",
        "dd_role": "state_addressability_gate",
    },
    {
        "id": "epigenetic_phase_control",
        "source_examples": [
            "epigenetic control of satellite cells",
            "activation/proliferation/commitment/differentiation/fusion phases",
        ],
        "math_shape": "same substrate + phase-specific gates + bounded transition receipts",
        "primary_function": "schedule route opening, suppression, specialization, repair, and fusion",
        "dd_role": "route_scheduler",
    },
    {
        "id": "unresolved_metadata_hold",
        "source_examples": [
            "unresolved IEEE Xplore metadata note",
            "HTTP 418 / unable to load page / unverified title or DOI",
        ],
        "math_shape": "unknown citation -> no extracted prior",
        "primary_function": "hold unverified sources outside the route prior until metadata is reliable",
        "dd_role": "claim_boundary_hold",
    },
]


DD_FUNCTION_ALGEBRA = [
    {
        "symbol": "B(route)",
        "name": "bound",
        "definition": "lower-bound payload + sidecar + witness + compute/container costs before evaluation",
    },
    {
        "symbol": "R(key)",
        "name": "route",
        "definition": "deterministically assign route/key/repair requests to an owner or chart",
    },
    {
        "symbol": "F(states)",
        "name": "fold",
        "definition": "merge states only when decode reachability and receipt class are preserved",
    },
    {
        "symbol": "T(section)",
        "name": "transport",
        "definition": "move local route sections across bundle/fiber/base regions with bounded holonomy",
    },
    {
        "symbol": "A(budget)",
        "name": "allocate",
        "definition": "split byte/runtime/witness budgets across shared, private, and repair lanes",
    },
    {
        "symbol": "E(residual)",
        "name": "exact_repair",
        "definition": "emit residual lanes that restore the exact source bytes after any sketch/proposal",
    },
    {
        "symbol": "V(output)",
        "name": "verify",
        "definition": "decode, hash, count bytes, and compare against incumbent under one ratio schema",
    },
]


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def citation_source_surface(source_text: str) -> str:
    """Return the tiddler region that contains input citations.

    The generated distillation section contains its own receipt hash. Excluding
    it keeps the receipt stable across reruns after the wiki is updated.
    """
    marker = "\n!! Citation Math Function Distillation\n"
    if marker not in source_text:
        return source_text
    before, after = source_text.split(marker, 1)
    next_marker = "\n!! Where To Tune Next\n"
    if next_marker in after:
        _, tail = after.split(next_marker, 1)
        return before + next_marker + tail
    return before


def extract_citation_surface(source_text: str) -> dict[str, Any]:
    dois = sorted(set(re.findall(r"10\.\d{4,9}/[A-Za-z0-9._;()/:+-]+", source_text)))
    urls = sorted(set(re.findall(r"https?://[^\s`]+", source_text)))
    titles = sorted(
        set(
            match.strip()
            for match in re.findall(r'"([^"\n]{12,180})"', source_text)
            if not match.startswith("http")
        )
    )
    consensus_threads = sorted(
        set(re.findall(r"Consensus thread:\n\n```\n([^`]+?)\n```", source_text, flags=re.MULTILINE))
    )
    unresolved_ieee = [url for url in urls if "ieeexplore.ieee.org/abstract/document/" in url]
    return {
        "source_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "doi_count": len(dois),
        "url_count": len(urls),
        "quoted_title_count": len(titles),
        "consensus_thread_count": len(consensus_threads),
        "unresolved_ieee_url_count": len(unresolved_ieee),
        "dois": dois,
        "urls": urls,
        "consensus_threads": consensus_threads,
        "sample_quoted_titles": titles[:25],
    }


def build_receipt(source: Path) -> dict[str, Any]:
    source_text = source.read_text(encoding="utf-8")
    source_surface = citation_source_surface(source_text)
    citation_surface = extract_citation_surface(source_surface)
    receipt: dict[str, Any] = {
        "schema": "citation_math_function_distillation_v1",
        "generated_at": "2026-05-08T00:00:00+00:00",
        "source_tiddler": str(source),
        "source_surface_scope": (
            "tiddler excluding generated Citation Math Function Distillation section"
        ),
        "citation_surface": citation_surface,
        "claim_boundary": (
            "This distills cited papers into math/function roles. It does not "
            "verify every paper externally and does not promote any compression "
            "claim without local byte receipts."
        ),
        "primary_function": PRIMARY_FUNCTION,
        "dd_function_algebra": DD_FUNCTION_ALGEBRA,
        "function_groups": FUNCTION_GROUPS,
        "distilled_core": (
            "All citation families collapse to one operational compressor: a "
            "bounded exact route compiler whose only promotion authority is "
            "local rehydration hash plus measured compressed_total_bytes."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = (
        "You are a citation math distiller for the projectable-geometry "
        "compressor. Group citations by mathematical function and preserve the "
        "byte-exact claim boundary."
    )
    records: list[dict[str, Any]] = []
    for group in receipt["function_groups"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "distill_citation_group",
                                "group_id": group["id"],
                                "source_examples": group["source_examples"],
                                "math_shape": group["math_shape"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "primary_function": group["primary_function"],
                                "dd_role": group["dd_role"],
                                "promotion_authority": "local encode/decode/hash/byte-count receipt",
                                "claim_boundary": "citation_function_prior_only",
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
