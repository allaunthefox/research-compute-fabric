#!/usr/bin/env python3
"""Receipt a scholar-style deep dive on abstraction-layer shape matches.

The search target is the local abstraction:

    each stage is parallel domains of the data type being processed

The useful source matches are not compression claims. They are operator
families that resemble the local machine: synchronization schemas, reduced
product abstract domains, staged computation, multi-view fusion, provenance
semirings, lenses, and type/data-oriented parallel systems.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "scholar_abstraction_layer_shape_deep_dive_receipt.json"
CURRICULUM_OUT = SHIM / "scholar_abstraction_layer_shape_deep_dive_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


SOURCE_BUNDLE = [
    {
        "id": "synchronization_schemas",
        "title": "Synchronization Schemas",
        "authors": "Rajeev Alur et al.",
        "venue": "PODS 2021",
        "url": "https://research.google/pubs/synchronization-schemas/",
        "shape": "type-theoretic synchronization over series-parallel streams",
        "local_mapping": "cross-domain barrier and typed stage stream object",
        "strength": "primary_match",
    },
    {
        "id": "reduced_product_abstract_transformers",
        "title": "Synthesizing Abstract Transformers for Reduced-Product Domains",
        "authors": "Pankaj Kumar Kalita, Thomas Reps, Subhajit Roy",
        "venue": "arXiv 2024",
        "doi": "10.48550/arXiv.2408.04040",
        "url": "https://arxiv.org/abs/2408.04040",
        "shape": "component transformers over product domains must cooperate",
        "local_mapping": "parallel stage domains with cross-domain contracts",
        "strength": "primary_match",
    },
    {
        "id": "product_operators_abstract_interpretation",
        "title": "A Survey on Product Operators in Abstract Interpretation",
        "authors": "Agostino Cortesi, Giulia Costantini, Pietro Ferrara",
        "venue": "EPTCS 129, 2013",
        "doi": "10.4204/EPTCS.129.19",
        "url": "https://arxiv.org/abs/1309.5146",
        "shape": "Cartesian products, reduced products, and cardinal powers combine domains",
        "local_mapping": "domain vector algebra for byte/token/structure/residual/witness views",
        "strength": "primary_match",
    },
    {
        "id": "multidirectional_synchronization",
        "title": "Controllable and decomposable multidirectional synchronizations",
        "authors": "Hermann et al.",
        "venue": "Software and Systems Modeling, 2021",
        "doi": "10.1007/s10270-021-00879-w",
        "url": "https://link.springer.com/article/10.1007/s10270-021-00879-w",
        "shape": "wide span of lenses synchronizes multiple views through a central model",
        "local_mapping": "central byte authority with token/structure/witness/domain views",
        "strength": "primary_match",
    },
    {
        "id": "staged_computation",
        "title": "Staged computation",
        "authors": "James R. Larus and Michael Parkes",
        "venue": "USENIX 2002",
        "url": "https://www.usenix.org/publications/library/proceedings/usenix02/full_papers/larus/larus_html/index.html",
        "shape": "stage as asynchronous operation group with private data and scheduling autonomy",
        "local_mapping": "stage control plane, but local model adds typed parallel domains",
        "strength": "strong_analogy",
    },
    {
        "id": "staged_classes",
        "title": "Multi-stage Programming in the Large with Staged Classes",
        "authors": "Lionel Parreaux, Amir Shaikhha",
        "venue": "GPCE 2020",
        "url": "https://cse.hkust.edu.hk/~parreaux/publication/gpce20/",
        "shape": "zero-cost staged abstractions for modular programs and data structures",
        "local_mapping": "compile route-stage abstractions away from payload; keep receipts only",
        "strength": "strong_analogy",
    },
    {
        "id": "multi_view_gnn_taxonomy",
        "title": "Graph neural networks for multi-view learning: a taxonomic review",
        "authors": "Shunxin Xiao et al.",
        "venue": "Artificial Intelligence Review, 2024",
        "doi": "10.1007/s10462-024-10990-1",
        "url": "https://link.springer.com/article/10.1007/s10462-024-10990-1",
        "shape": "multiple graph/relation/attribute views are fused or aligned",
        "local_mapping": "parallel route views propose and align but cannot override byte hash",
        "strength": "strong_analogy",
    },
    {
        "id": "semiring_provenance",
        "title": "PROX: Approximated Summarization of Data Provenance",
        "authors": "Deutch, Gilad, Moskovitch et al.",
        "venue": "VLDB / PMC version",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5001561/",
        "shape": "provenance annotations summarize how outputs depend on input domains",
        "local_mapping": "witness/provenance domain with bounded summaries and exact byte authority",
        "strength": "strong_analogy",
    },
    {
        "id": "hawkeye_datatype_semantics",
        "title": "HAWKEYE: Effective Discovery of Dataflow Impediments to Parallelization",
        "authors": "Omer Tripp, Greta Yorsh, John Field, Mooly Sagiv",
        "venue": "OOPSLA 2011",
        "url": "https://research.google/pubs/hawkeye-effective-discovery-of-dataflow-impediments-to-parallelization/",
        "shape": "parallelization dependencies tracked at abstract data-type semantics",
        "local_mapping": "domain contracts should track semantic dependencies, not raw field noise",
        "strength": "strong_analogy",
    },
    {
        "id": "yedalog",
        "title": "Yedalog: Exploring Knowledge at Scale",
        "authors": "Brian Chin et al.",
        "venue": "SNAPL 2015",
        "url": "https://research.google/pubs/yedalog-exploring-knowledge-at-scale/",
        "shape": "mix data-parallel pipelines and computation in one declarative language over nested records",
        "local_mapping": "route compiler DSL can mix domain-parallel transforms with structured corpus records",
        "strength": "supporting_match",
    },
    {
        "id": "dynamically_managed_data_cpu_gpu",
        "title": "Dynamically Managed Data for CPU-GPU Architectures",
        "authors": "Thomas B. Jablin et al.",
        "venue": "CGO 2012",
        "url": "https://research.google/pubs/dynamically-managed-data-for-cpu-gpu-architectures/",
        "shape": "automatic consistency management for CPU/GPU views of complex data",
        "local_mapping": "owner/budget/closure domains must keep heterogeneous route views consistent",
        "strength": "supporting_match",
    },
    {
        "id": "scalable_data_abstractions",
        "title": "Scalable data abstractions for distributed parallel computations",
        "authors": "James Hanlon, Simon J. Hollis, David May",
        "venue": "arXiv 2012",
        "doi": "10.48550/arXiv.1210.1157",
        "url": "https://arxiv.org/abs/1210.1157",
        "shape": "separate data representation from computation and allow distributed representations",
        "local_mapping": "active data type has distributed domain views; byte view remains authority",
        "strength": "supporting_match",
    },
]


CLUSTERS = [
    {
        "id": "typed_synchronization_streams",
        "members": ["synchronization_schemas", "yedalog"],
        "local_operator": "type each route stage as a series-parallel stream of domains",
    },
    {
        "id": "reduced_product_domain_algebra",
        "members": ["reduced_product_abstract_transformers", "product_operators_abstract_interpretation"],
        "local_operator": "combine byte/token/structure/residual/witness domains as a reduced product with cross-domain reductions",
    },
    {
        "id": "multi_view_consistency",
        "members": ["multidirectional_synchronization", "multi_view_gnn_taxonomy"],
        "local_operator": "let views align and synchronize, while central byte authority resolves promotion",
    },
    {
        "id": "stage_runtime_boundary",
        "members": ["staged_computation", "staged_classes", "dynamically_managed_data_cpu_gpu"],
        "local_operator": "stage abstractions manage computation and consistency but must not become payload",
    },
    {
        "id": "provenance_dependency_witness",
        "members": ["semiring_provenance", "hawkeye_datatype_semantics", "scalable_data_abstractions"],
        "local_operator": "track provenance and data-type dependencies as bounded witness domains",
    },
]


EQUATIONS = [
    {
        "id": "SAD0_reduced_product_stage",
        "equation": "Stage_t = D_byte x_R D_token x_R D_structure x_R D_residual x_R D_witness x_R D_owner x_R D_budget x_R D_closure",
        "meaning": "The stage is a reduced product of mutually constraining domains, not a flat tuple.",
    },
    {
        "id": "SAD1_domain_transformer_vector",
        "equation": "F_t^# = <f_byte^#, f_token^#, ..., f_closure^#>",
        "meaning": "Each stage edge is a vector of component transformers.",
    },
    {
        "id": "SAD2_synchronization_schema",
        "equation": "sync_schema(Stage_t) = ordering + key_partition + barrier_contract",
        "meaning": "A typed schema controls which domains are ordered, keyed, parallel, or barriered.",
    },
    {
        "id": "SAD3_lens_center",
        "equation": "central_model = exact_byte_span + exact_residuals",
        "meaning": "Token, structure, and witness views synchronize through the byte/residual center.",
    },
    {
        "id": "SAD4_provenance_witness",
        "equation": "W = provenance_semiring(route_edges, source_spans, residual_obligations)",
        "meaning": "Witness domains record how a route result depends on inputs and repairs.",
    },
    {
        "id": "SAD5_promotion_barrier",
        "equation": "promote iff all reductions close and hash(decode(center)) == source_hash",
        "meaning": "No view alignment or abstract-domain precision replaces byte rehydration.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "scholar_abstraction_layer_shape_deep_dive_v1",
        "generated_at": GENERATED_AT,
        "search_note": (
            "Direct automated Google Scholar access is unreliable, so this scan used "
            "Google-Scholar-linked research pages plus primary publisher, arXiv, "
            "Springer, USENIX, and Google Research pages."
        ),
        "source_bundle": SOURCE_BUNDLE,
        "clusters": CLUSTERS,
        "equations": EQUATIONS,
        "primary_decision": {
            "name": "treat_parallel_stage_domains_as_reduced_product_with_sync_schema",
            "statement": (
                "The closest literature shape is a reduced-product domain vector "
                "controlled by synchronization schemas and lens-like consistency. "
                "For the compressor, each stage should expose typed component "
                "transformers, cross-domain reduction/barrier rules, bounded "
                "provenance witnesses, and one exact byte/residual center."
            ),
        },
        "candidate_dd_state_extension": [
            "reduced_product_stage_id",
            "sync_schema_id",
            "domain_transformer_vector_id",
            "domain_reduction_operator_id",
            "view_lens_center_id",
            "provenance_semiring_id",
            "data_type_dependency_witness_id",
            "stage_parallelism_class",
            "domain_consistency_status",
            "domain_reduction_fixpoint_status",
            "byte_residual_center_hash",
        ],
        "candidate_dd_edges": [
            "choose_sync_schema",
            "open_reduced_product_stage",
            "synthesize_domain_transformer_vector",
            "apply_cross_domain_reduction",
            "synchronize_views_through_byte_center",
            "emit_provenance_semiring_witness",
            "track_data_type_dependency",
            "reject_view_consistency_without_byte_hash",
            "close_reduced_product_stage",
        ],
        "promotion_rule": [
            "stage_domains_are_a_reduced_product_not_unrelated_sidecars",
            "sync_schema_declares_ordering_keying_and_barriers",
            "component_transformers_are_typed_and_receipted",
            "cross_domain_reductions_reach_fixpoint_or_fail_closed",
            "views_synchronize_through_exact_byte_residual_center",
            "provenance_witness_is_bounded",
            "decoded_hash_matches_source",
            "measured_total_bytes_beat_incumbent_under_ratio_schema",
        ],
        "failure_rule": [
            "view_fusion_without_byte_center -> diagnostic_only",
            "reduced_product_search_space_explodes -> prune_or_split_stage",
            "sync_schema_missing_barrier -> invalid_receipt",
            "provenance_polynomial_unbounded -> summarize_or_prune",
            "stage_abstraction_serialized_as_payload -> invalid_receipt",
            "data_type_dependency_ignored -> unsafe_parallelization",
        ],
        "claim_boundary": (
            "These papers provide similar abstraction-layer shapes. None are "
            "evidence of compression improvement until local encode/decode/hash/"
            "byte-count receipts close under one ratio schema."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["source_bundle"]:
        lines.append({"type": "source_shape", **item})
    for item in receipt["clusters"]:
        lines.append({"type": "cluster", **item})
    for item in receipt["equations"]:
        lines.append({"type": "equation", **item})
    for rule in receipt["promotion_rule"]:
        lines.append({"type": "promotion_rule", "rule": rule})
    for rule in receipt["failure_rule"]:
        lines.append({"type": "failure_rule", "rule": rule})
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
        "source_count": len(receipt["source_bundle"]),
        "cluster_count": len(receipt["clusters"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
