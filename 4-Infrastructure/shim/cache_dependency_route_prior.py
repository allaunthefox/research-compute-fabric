#!/usr/bin/env python3
"""Distill latency-vs-capacity cache use cases into route-evaluator guardrails.

The source article's useful extraction is dependency classification: identical
cache access code can be either a soft latency optimization or a load-bearing
capacity dependency. For the bounded route compiler, cache hits are never proof;
they are operational shortcuts that must be stress-tested against cold-cache
and hit-rate collapse scenarios.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "cache_dependency_route_prior_receipt.json"
CURRICULUM_OUT = SHIM / "cache_dependency_route_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"
SOURCE_URL = "https://read.thecoder.cafe/p/cache-use-cases"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


SOURCE_EVIDENCE = {
    "title": "Cache Use Cases Explained: Latency Cache vs. Capacity Cache",
    "author": "Teiva Harsanyi",
    "published_date": "2026-05-06",
    "source_url": SOURCE_URL,
    "observed_core_claims": [
        "latency_cache_reduces_average_response_time",
        "latency_cache_is_normally_soft_dependency",
        "capacity_cache_absorbs_load_backend_cannot_absorb_directly",
        "same_access_pattern_can_hide_dependency_change",
        "latency_cache_can_silently_become_capacity_cache_as_traffic_grows",
        "cold_cache_or_invalidation_can_create_miss_storm",
        "hit_rate_monitoring_load_testing_and_warming_manage_risk",
    ],
}


ROUTE_CACHE_TYPES = [
    {
        "id": "latency_route_cache",
        "definition": "memoizes route/evaluator results to reduce average evaluator latency",
        "dependency_class": "soft_if_backend_can_absorb_cold_cache_load",
        "local_examples": [
            "compression_ratio_vector_cache",
            "candidate_feature_cache",
            "tokenbook_preview_cache",
            "lower_bound_estimate_cache",
        ],
        "failure_behavior": "fall through to exact evaluator with slower runtime",
    },
    {
        "id": "capacity_route_cache",
        "definition": "absorbs route/evaluator demand that the backend cannot serve directly",
        "dependency_class": "hard_if_backend_cannot_absorb_cold_cache_load",
        "local_examples": [
            "large_slice_evaluator_result_cache",
            "expensive_decode_hash_receipt_cache",
            "route_population_archive_cache",
            "shared_tokenbook_materialization_cache",
        ],
        "failure_behavior": "miss storm can overwhelm evaluator or trigger unbounded fallback search",
    },
]


EQUATIONS = [
    {
        "id": "CACHE0_effective_backend_load",
        "equation": "backend_load = request_rate * (1 - cache_hit_rate)",
        "meaning": "Route evaluator pressure is governed by misses, not nominal request volume.",
    },
    {
        "id": "CACHE1_backend_headroom",
        "equation": "backend_headroom = backend_capacity - backend_load",
        "meaning": "A cache is still soft only while cold or degraded load leaves nonnegative backend headroom.",
    },
    {
        "id": "CACHE2_dependency_class",
        "equation": "dependency = latency if backend_capacity >= request_rate else capacity",
        "meaning": "If the backend cannot absorb full traffic without cache, the cache is load-bearing.",
    },
    {
        "id": "CACHE3_cold_start_stress",
        "equation": "cold_start_ok iff request_rate <= backend_capacity and warmup_time <= warmup_budget",
        "meaning": "Cache migration or invalidation must be tested as a first-class route failure mode.",
    },
    {
        "id": "CACHE4_route_proof_boundary",
        "equation": "promote(route) requires exact_decode_hash, not cache_hit",
        "meaning": "Cached receipts can speed evaluation, but cannot replace rehydration authority.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "cache_dependency_route_prior_v1",
        "generated_at": GENERATED_AT,
        "source_evidence": SOURCE_EVIDENCE,
        "primary_decision": {
            "name": "classify_route_caches_by_dependency_not_access_pattern",
            "statement": (
                "Treat route caches as latency or capacity dependencies based on "
                "whether the exact evaluator/backend can absorb cold-cache load. "
                "Do not infer dependency class from cache-first code shape."
            ),
        },
        "route_cache_types": ROUTE_CACHE_TYPES,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "route_cache_id",
            "cache_use_case_class",
            "cache_hit_rate",
            "cache_miss_rate",
            "backend_capacity_routes_per_sec",
            "estimated_request_rate",
            "backend_headroom",
            "cold_cache_stress_status",
            "warmup_receipt_id",
            "cache_dependency_status",
            "cache_invalidation_scope",
            "miss_storm_risk_class",
            "cached_receipt_hash",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "classify_route_cache_dependency",
            "measure_cache_hit_rate",
            "estimate_cold_cache_backend_load",
            "stress_without_route_cache",
            "warm_route_cache_before_cutover",
            "invalidate_cache_with_miss_storm_guard",
            "fall_through_to_exact_evaluator",
            "reject_cache_hit_as_proof",
        ],
        "lower_bound": [
            "cache_header_bytes",
            "warmup_receipt_floor",
            "invalidation_receipt_floor",
            "fallback_evaluator_capacity_floor",
            "exact_receipt_floor",
        ],
        "promotion_rule": [
            "cache_layer_only_memoizes_or_schedules_route_evaluation",
            "cache_dependency_class_is_explicit",
            "cold_cache_stress_either_passes_or_fails_closed",
            "capacity_cache_has_alerting_and_warmup_receipt",
            "cache_hit_never_replaces_decode_hash",
            "decoded_hash_matches_source",
            "measured_total_bytes_beat_incumbent_under_ratio_schema",
        ],
        "failure_rule": [
            "cache_hit_without_rehydration_hash -> invalid_receipt",
            "capacity_cache_labeled_as_latency_cache -> fail_closed",
            "cold_cache_miss_storm_exceeds_backend_capacity -> NaN0",
            "cache_warmup_overhead_exceeds_byte_gain -> prune",
            "cache_invalidation_without_scope_receipt -> fail_closed",
        ],
        "claim_boundary": (
            "This prior is an operational dependency model for route caches. It "
            "is not a compression result and does not promote cached outputs "
            "without exact decode/hash/byte-count receipts."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["route_cache_types"]:
        lines.append({"type": "route_cache_type", **item})
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
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
