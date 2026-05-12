#!/usr/bin/env python3
"""Non-Euclidean geometry, compression, and semantic KV-store prior.

This records the user's pasted Consensus thread as a bounded route prior.  The
source says the three themes are mostly separate in current research, so the
local extraction is an integration rule rather than a claim that the literature
already proves a unified compressor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_RECEIPT = Path("4-Infrastructure/shim/non_euclidean_semantic_kv_prior_receipt.json")
DEFAULT_CURRICULUM = Path("4-Infrastructure/shim/non_euclidean_semantic_kv_prior_curriculum.jsonl")


CONSENSUS_SOURCE_SUMMARY = {
    "thread_title": "Non-Euclidean Geometry Compression Methods",
    "prompt": "non euclidian approaches to geometry, compression and semantic key stores",
    "mode": "Pro",
    "search_count": 4,
    "reported_query_counts": {
        "compression_methods_and_semantic_key_value_stores": 17_900_000,
        "geometric_methods_in_non_euclidean_spaces_and_manifold_based_geometry": 3_000_000,
        "non_euclidean_geometry_hyperbolic_spherical_metric_geometry": 865_100,
    },
    "consensus_meter_question": (
        "Does non-Euclidean geometry improve compression efficiency in semantic key-value stores?"
    ),
    "claim_boundary": (
        "The thread says current work touches non-Euclidean geometry, classic "
        "KV-store compression, and semantic KV-cache compression mostly in "
        "separate lines. This prior extracts integration constraints only."
    ),
}


PRIOR_FAMILIES = [
    {
        "id": "riemannian_manifold_distortion",
        "source_examples": [
            "A Riemannian geometric framework for manifold learning of non-Euclidean data",
            "Survey of geometric optimization from Euclidean space to Riemannian manifolds",
            "Manifold learning in metric spaces",
        ],
        "useful_shape": (
            "learn or compare data on curved spaces using coordinate-invariant "
            "distortion and near-isometry checks"
        ),
        "compressor_mapping": "semantic keys live on a curved route manifold instead of a flat vector table",
        "receipt_fields": [
            "manifold_family_id",
            "chart_id",
            "coordinate_invariant_distortion",
            "near_isometry_status",
        ],
        "failure_mode": "curved embedding clusters keys but does not preserve byte rehydration",
    },
    {
        "id": "cartan_hadamard_optimal_transport",
        "source_examples": [
            "Sliced-Wasserstein Distances and Flows on Cartan-Hadamard Manifolds",
            "Spherical and hyperbolic embeddings of data",
            "Computationally tractable Riemannian manifolds for graph embeddings",
        ],
        "useful_shape": (
            "use non-positive curvature, hyperbolic/SPD geometry, and sliced "
            "Wasserstein flows for distribution-aware key movement"
        ),
        "compressor_mapping": "route token/key populations by geodesic transport rather than flat nearest neighbor only",
        "receipt_fields": [
            "curvature_class",
            "transport_plan_id",
            "sliced_wasserstein_score",
            "geodesic_owner_id",
        ],
        "failure_mode": "transport score improves retrieval geometry while sidecar cost exceeds byte gain",
    },
    {
        "id": "classic_kv_store_byte_compression",
        "source_examples": [
            "Requirements and Trade-Offs of Compression Techniques in Key-Value Stores: A Survey",
            "ZipKV: In-Memory Key-Value Store with Built-In Data Compression",
            "KallaxDB: A Table-less Hash-based Key-Value Store on Storage Hardware with Built-in Transparent Compression",
            "TinyEnc: Enabling Compressed and Encrypted Big Data Stores With Rich Query Support",
        ],
        "useful_shape": (
            "classic KV stores tune Snappy/LZ4/Zstd/Zlib, compaction, block size, "
            "selective compression, and read/write amplification"
        ),
        "compressor_mapping": "backend key store must expose actual byte counts and throughput tradeoffs",
        "receipt_fields": [
            "kv_backend_id",
            "codec_id",
            "block_granularity_bytes",
            "read_amplification",
            "write_amplification",
            "compressed_store_bytes",
        ],
        "failure_mode": "semantic key route ignores store codec overhead or compaction cost",
    },
    {
        "id": "semantic_chunk_anchor_kv_cache",
        "source_examples": [
            "ChunkKV: Semantic-Preserving KV Cache Compression for Efficient Long-Context LLM Inference",
            "FINCH: Prompt-guided Key-Value Cache Compression for Large Language Models",
            "Autoencoding-Free Context Compression for LLMs via Contextual Semantic Anchors",
            "ClusterKV: Manipulating LLM KV Cache in Semantic Space for Recallable Compression",
            "SentenceKV: Efficient LLM Inference via Sentence-Level Semantic KV Caching",
        ],
        "useful_shape": (
            "preserve semantic chunks, anchor tokens, sentence units, or recallable "
            "clusters under strict KV-cache budgets"
        ),
        "compressor_mapping": "chunk/anchor selection proposes tokenbook and sidecar lanes",
        "receipt_fields": [
            "semantic_chunk_id",
            "anchor_token_map_hash",
            "cluster_id",
            "recallability_score",
            "chunk_residual_bytes",
        ],
        "failure_mode": "semantic anchor reconstructs meaning but not source bytes",
    },
    {
        "id": "head_layer_importance_kv_cache",
        "source_examples": [
            "Dynamic Memory Compression: Retrofitting LLMs for Accelerated Inference",
            "RazorAttention: Efficient KV Cache Compression Through Retrieval Heads",
            "CompressKV: Semantic Retrieval Heads Know What Tokens are Not Important Before Generation",
            "HeadKV: A Head-Level KV Cache Compression Method with Integrated Retrieval and Reasoning",
            "MiniCache: KV Cache Compression in Depth Dimension for Large Language Models",
            "A Simple and Effective L2 Norm-Based Strategy for KV Cache Compression",
        ],
        "useful_shape": (
            "heads, layers, norms, importance, and diversity can rank what KV state "
            "to keep, merge, or evict"
        ),
        "compressor_mapping": "attention-derived importance becomes a DD feature coordinate, not a proof",
        "receipt_fields": [
            "attention_head_id",
            "layer_id",
            "importance_score",
            "diversity_score",
            "eviction_policy_id",
            "kv_budget_bytes",
        ],
        "failure_mode": "head/layer pruning breaks exact decode or retrieval receipt",
    },
    {
        "id": "value_aware_low_rank_kv_cache",
        "source_examples": [
            "GEAR: An Efficient KV Cache Compression Recipe for Near-Lossless Generative Inference of LLM",
            "Value-Guided KV Compression for LLMs via Approximated CUR Decomposition",
            "Palu: KV-Cache Compression with Low-Rank Projection",
            "LoRC: Low-Rank Compression for LLMs KV Cache with a Progressive Compression Strategy",
            "SVDq: 1.25-bit and 410x Key Cache Compression for LLM Attention",
        ],
        "useful_shape": (
            "low-rank, sparse correction, quantization, CUR/SVD, and value-guided "
            "decomposition approximate attention outputs"
        ),
        "compressor_mapping": "low-rank KV is a predictor sketch that needs exact residual authority",
        "receipt_fields": [
            "decomposition_family_id",
            "rank_budget",
            "quantization_bits",
            "sparse_correction_bytes",
            "value_guidance_hash",
        ],
        "failure_mode": "near-lossless KV approximation is treated as byte-exact",
    },
    {
        "id": "geometry_inspired_but_unproven_unification",
        "source_examples": [
            "Position: Beyond Euclidean - Foundation Models Should Embrace Non-Euclidean Geometries",
            "Beyond Euclid: an illustrated guide to modern machine learning with geometric, topological, and algebraic structures",
            "State of the Art of Graph Visualization in non-Euclidean Spaces",
        ],
        "useful_shape": (
            "non-Euclidean geometry may improve representation and retrieval, but "
            "the cited thread does not establish a single unified KV compressor"
        ),
        "compressor_mapping": "require an explicit bridge receipt between curved geometry and byte-store behavior",
        "receipt_fields": [
            "bridge_claim_id",
            "geometry_to_kv_mapping_id",
            "byte_store_receipt_id",
            "semantic_cache_receipt_id",
            "unification_status",
        ],
        "failure_mode": "geometry metaphor is promoted without a byte-store and semantic-cache bridge",
    },
]


LOCAL_TREEFIDDY_STATUS = {
    "status": "found_in_current_checkout",
    "model_map_entry": "3-Mathematical-Models/MATH_MODEL_MAP.tsv:102",
    "documentation": "6-Documentation/docs/semantics/TREE_FIDDY.md",
    "local_role": (
        "TREE(3) / Kruskal-style tree-sequence bound used as a state-space "
        "pruning shortcut and bounded archive depth guard"
    ),
    "compression_claim_boundary": (
        "Tree Fiddy can bound TreeKV route depth, owner routing, and archive "
        "receipts. It is not a hidden payload channel and does not prove byte "
        "compression by itself."
    ),
}


PRIORITY_WATCH_ITEMS = [
    {
        "id": "tinyenc_compressed_encrypted_kv_store",
        "source_examples": [
            "TinyEnc: Enabling Compressed and Encrypted Big Data Stores With Rich Query Support",
            "Encrypted and Compressed Key-Value Store With Pattern-Analysis Security in Cloud Systems",
            "Optimal Compression for Encrypted Key-Value Store in Cloud Systems",
        ],
        "why_pay_attention": (
            "TinyEnc sits on the byte-store side of the bridge: compression, "
            "encryption, and rich query support must be paid for in one receipt."
        ),
        "compressor_mapping": (
            "encrypted KV packet -> compressed store packet + query-support "
            "index + leakage/pattern guard + exact byte rehydration receipt"
        ),
        "receipt_fields": [
            "encryption_envelope_id",
            "cipher_suite_id",
            "query_support_class",
            "query_index_bytes",
            "pattern_leakage_guard_id",
            "compressed_encrypted_bytes",
            "plaintext_rehydration_hash",
        ],
        "promotion_guard": (
            "promote only if encryption envelope, query index, and compression "
            "container overhead are counted and plaintext bytes rehydrate exactly"
        ),
        "failure_mode": "query/encryption metadata hides byte debt or weakens the claim boundary",
    },
    {
        "id": "treekv_treefiddy_modification",
        "source_examples": [
            "TreeKV: Smooth Key-Value Cache Compression with Tree Structures",
            "Tree Fiddy: TREE(3) Combinatorial State Space Shortcut",
            "BHOCS: Bounded Hierarchical Cryptographic Space",
        ],
        "why_pay_attention": (
            "TreeKV already gives a tree-structured KV-cache route. Local "
            "Tree Fiddy can modify it into a bounded route spine with explicit "
            "depth, embedding, owner, and leaf-residual receipts."
        ),
        "compressor_mapping": (
            "TreeKV node -> Tree Fiddy bounded route spine -> deterministic "
            "subtree owner -> smooth merge receipt -> exact residual leaves"
        ),
        "receipt_fields": [
            "treekv_node_id",
            "treefiddy_spine_id",
            "tree_label_budget_k",
            "tree_depth_budget",
            "homeomorphic_embedding_guard",
            "subtree_owner_hash",
            "smooth_merge_receipt_id",
            "leaf_residual_bytes",
        ],
        "promotion_guard": (
            "promote only if Tree Fiddy bounds depth/branching, TreeKV smooth "
            "merges preserve decode reachability, and residual leaves restore "
            "the exact bytes"
        ),
        "failure_mode": "tree merge changes decode reachability or opens recursive repair",
    },
]


INTEGRATION_RULES = {
    "three_surface_model": {
        "curved_key_surface": "non-Euclidean manifold stores similarity, hierarchy, and geodesic owner routing",
        "byte_store_surface": "KV backend stores bytes with codec, compaction, and throughput receipts",
        "semantic_cache_surface": "LLM KV/cache route stores semantic anchors, heads, ranks, and residuals",
    },
    "promotion_rule": (
        "promote iff curved geometry only routes or clusters keys, KV-store byte "
        "compression is measured, semantic KV approximations carry exact residual "
        "repair, decoded hash matches source, and total bytes beat incumbent"
    ),
    "failure_rule": (
        "non-Euclidean retrieval, semantic cache recall, or KV throughput improvement "
        "without byte-exact rehydration is diagnostic only"
    ),
    "tinyenc_watch_rule": (
        "TinyEnc-style compressed encryption is relevant when query support, "
        "encryption envelope, compressed bytes, and leakage guards are all "
        "counted in the same byte-store receipt"
    ),
    "treekv_treefiddy_rule": (
        "TreeKV may be modified to use Tree Fiddy as a bounded tree-spine and "
        "homeomorphic-embedding guard, but Tree Fiddy remains a pruning and "
        "receipt primitive, not compression evidence"
    ),
}


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "non_euclidean_semantic_kv_prior_v1",
        "generated_at": "2026-05-08T00:00:00+00:00",
        "source_summary": CONSENSUS_SOURCE_SUMMARY,
        "source_summary_hash": stable_hash(CONSENSUS_SOURCE_SUMMARY),
        "claim_boundary": (
            "This is an integration prior. It records source families for curved "
            "geometry, KV-store compression, and semantic KV-cache compression; "
            "local encode/decode/hash/byte-count receipts remain authoritative."
        ),
        "prior_families": PRIOR_FAMILIES,
        "priority_watch_items": PRIORITY_WATCH_ITEMS,
        "local_treefiddy_status": LOCAL_TREEFIDDY_STATUS,
        "integration_rules": INTEGRATION_RULES,
        "dd_state_extension": [
            "manifold_family_id",
            "chart_id",
            "curvature_class",
            "geodesic_owner_id",
            "kv_backend_id",
            "codec_id",
            "block_granularity_bytes",
            "semantic_chunk_id",
            "anchor_token_map_hash",
            "attention_head_id",
            "importance_score",
            "decomposition_family_id",
            "rank_budget",
            "sparse_correction_bytes",
            "geometry_to_kv_mapping_id",
            "byte_store_receipt_id",
            "semantic_cache_receipt_id",
            "encryption_envelope_id",
            "query_support_class",
            "pattern_leakage_guard_id",
            "treekv_node_id",
            "treefiddy_spine_id",
            "tree_label_budget_k",
            "tree_depth_budget",
            "homeomorphic_embedding_guard",
            "subtree_owner_hash",
            "smooth_merge_receipt_id",
            "leaf_residual_bytes",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "choose_curved_key_manifold",
            "assign_geodesic_owner",
            "measure_manifold_distortion",
            "choose_kv_backend_codec",
            "measure_kv_store_bytes",
            "emit_semantic_chunk_anchor",
            "rank_attention_heads",
            "apply_low_rank_kv_sketch",
            "emit_exact_kv_residual_lane",
            "bridge_geometry_to_byte_store",
            "charge_tinyenc_encryption_query_overhead",
            "open_treekv_treefiddy_spine",
            "bound_treefiddy_depth_and_embedding",
            "route_treefiddy_subtree_owner",
            "verify_treekv_smooth_merge_receipt",
            "emit_tree_leaf_exact_residuals",
            "verify_byte_rehydration_hash",
            "reject_geometry_only_kv_claim",
        ],
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = (
        "You are a non-Euclidean semantic KV route controller. Keep geometry, "
        "KV-store bytes, and semantic cache receipts separate until a bridge is verified."
    )
    records: list[dict[str, Any]] = []
    for family in receipt["prior_families"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "route_non_euclidean_semantic_kv_family",
                                "family_id": family["id"],
                                "useful_shape": family["useful_shape"],
                                "compressor_mapping": family["compressor_mapping"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "selected": True,
                                "receipt_fields": family["receipt_fields"],
                                "failure_mode": family["failure_mode"],
                                "claim_boundary": "integration-prior-only",
                                "promotion_authority": "local encode/decode/hash/byte-count receipt",
                            },
                            ensure_ascii=False,
                        ),
                    },
                ]
            }
        )
    for item in receipt["priority_watch_items"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "route_priority_watch_item",
                                "watch_item_id": item["id"],
                                "why_pay_attention": item["why_pay_attention"],
                                "compressor_mapping": item["compressor_mapping"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "selected": True,
                                "receipt_fields": item["receipt_fields"],
                                "promotion_guard": item["promotion_guard"],
                                "failure_mode": item["failure_mode"],
                                "promotion_authority": "local encode/decode/hash/byte-count receipt",
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
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    args = parser.parse_args()

    receipt = build_receipt()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
