#!/usr/bin/env python3
"""Build receipted density-marker priors from user-supplied Kaggle notebook excerpts.

These packets intentionally preserve design patterns, not leaderboard claims:
chunked dtype reduction, columnar Parquet access, binary travel-map routing,
autoencoder/decomposition feature compression, and AIMO3 inference-appliance
guardrails. All packets remain HOLD until a local dataset, implementation, and
replay/benchmark receipt close.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "kaggle_density_priors"
PACKETS = OUT_DIR / "kaggle_density_marker_prior_packets.jsonl"
RECEIPT = OUT_DIR / "kaggle_density_marker_prior_receipt.json"
SOURCES_CFF = OUT_DIR / "kaggle_density_marker_prior_sources.cff"

KAGGLE_LICENSE_NOTICE = {
    "platform": "Kaggle",
    "platform_terms_url": "https://www.kaggle.com/terms",
    "license_status": "source_notebook_license_not_verified_from_pasted_excerpt",
    "use_policy": (
        "This registry records design-principle summaries and density markers only. "
        "It does not vendor, redistribute, or relicense Kaggle notebook code. "
        "Before copying or adapting notebook code, inspect the Kaggle page metadata "
        "and honor the author's license, Kaggle terms, and any competition or dataset terms."
    ),
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def packet(
    packet_id: str,
    name: str,
    source_surface: str,
    source_urls: list[str],
    source_authors: list[str],
    route: str,
    density_markers: list[str],
    compression_relevance: str,
    claim_boundary: str,
) -> dict[str, Any]:
    obj = {
        "schema": "kaggle_density_marker_prior_packet_v1",
        "packet_id": packet_id,
        "name": name,
        "source_surface": source_surface,
        "source_urls": source_urls,
        "source_authors": source_authors,
        "license_provenance": KAGGLE_LICENSE_NOTICE,
        "rrc_shape_hint": "KaggleCompetitionAlgorithmPrior",
        "route": route,
        "density_markers": density_markers,
        "compression_relevance": compression_relevance,
        "claim_boundary": claim_boundary,
        "decision": "HOLD",
    }
    obj["packet_hash"] = sha256_text(stable_json(obj))
    return obj


def source_reference(packet_obj: dict[str, Any]) -> dict[str, Any]:
    authors = packet_obj["source_authors"] or ["Unknown Kaggle author"]
    first_url = packet_obj["source_urls"][0] if packet_obj["source_urls"] else "https://www.kaggle.com/"
    return {
        "type": "software",
        "title": packet_obj["name"],
        "authors": [{"name": author} for author in authors],
        "url": first_url,
        "notes": (
            "Kaggle source cited as an external design-prior surface only. "
            "Notebook code is not vendored in this repository; license must be "
            "verified on Kaggle before copying, adapting, or redistributing code."
        ),
    }


def write_sources_cff(packets: list[dict[str, Any]]) -> None:
    cff = {
        "cff-version": "1.2.0",
        "message": (
            "If you use these Kaggle-derived density-prior notes, cite the original "
            "Kaggle sources and verify each source license before copying code."
        ),
        "type": "dataset",
        "title": "Kaggle Algorithm Density Marker Prior Sources",
        "authors": [{"name": "Research Stack Contributors"}],
        "date-released": "2026-05-08",
        "url": "https://github.com/allaunthefox/Research-Stack",
        "repository-code": "https://github.com/allaunthefox/Research-Stack",
        "license": "Apache-2.0",
        "references": [
            *[source_reference(packet_obj) for packet_obj in packets],
            {
                "type": "webpage",
                "title": "Kaggle Terms of Use",
                "authors": [{"name": "Kaggle"}],
                "url": "https://www.kaggle.com/terms",
                "notes": "Platform terms; individual notebooks/datasets may carry additional metadata and licenses.",
            },
        ],
    }

    def render_scalar(value: Any) -> str:
        text = str(value).replace('"', '\\"')
        return f'"{text}"'

    lines = [
        "cff-version: 1.2.0",
        f"message: {render_scalar(cff['message'])}",
        "type: dataset",
        f"title: {render_scalar(cff['title'])}",
        "authors:",
    ]
    for author in cff["authors"]:
        lines.append(f"  - name: {render_scalar(author['name'])}")
    lines.extend(
        [
            f"date-released: {cff['date-released']}",
            f"url: {render_scalar(cff['url'])}",
            f"repository-code: {render_scalar(cff['repository-code'])}",
            f"license: {cff['license']}",
            "references:",
        ]
    )
    for ref in cff["references"]:
        lines.append(f"  - type: {ref['type']}")
        lines.append(f"    title: {render_scalar(ref['title'])}")
        lines.append("    authors:")
        for author in ref["authors"]:
            lines.append(f"      - name: {render_scalar(author['name'])}")
        lines.append(f"    url: {render_scalar(ref['url'])}")
        lines.append(f"    notes: {render_scalar(ref['notes'])}")
    SOURCES_CFF.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    packets = [
        packet(
            packet_id="KAGGLE.UBIQUANT.CHUNKED_DTYPE_REDUCTION.0001",
            name="Ubiquant chunked dtype reduction",
            source_surface="user-pasted Ubiquant Market Prediction tutorial excerpt",
            source_urls=[
                "https://www.kaggle.com/competitions/ubiquant-market-prediction",
            ],
            source_authors=["Unknown Kaggle notebook author"],
            route=(
                "large_csv -> chunked pandas read -> dtype min/max downcast -> pickle chunks "
                "-> concatenated low-memory frame"
            ),
            density_markers=[
                "chunked_stream_ingest",
                "dtype_range_downcast",
                "float16_feature_surface",
                "pickle_chunk_materialization",
                "weak_linear_correlation_signal",
                "generator_batch_surface",
            ],
            compression_relevance=(
                "Shows a practical memory-shrink route: 18GB-class tabular CSV can be moved "
                "into smaller typed carriers before model or RRC feature extraction."
            ),
            claim_boundary=(
                "Notebook excerpt only; dtype reduction may change numeric precision and must be "
                "validated against target replay before promotion."
            ),
        ),
        packet(
            packet_id="KAGGLE.UBIQUANT.PARQUET_COLUMNAR_IO.0001",
            name="Ubiquant Parquet columnar loading",
            source_surface="user-pasted Ubiquant Parquet loading excerpt",
            source_urls=[
                "https://www.kaggle.com/robikscube/ubiquant-parquet",
                "https://www.kaggle.com/competitions/ubiquant-market-prediction",
            ],
            source_authors=["Rob Mulla", "Unknown Kaggle notebook author"],
            route=(
                "csv table -> Parquet columnar table -> low-memory typed Parquet -> column subset "
                "or investment_id shard"
            ),
            density_markers=[
                "columnar_storage_surface",
                "record_shredding_assembly",
                "low_memory_float32_uint16_schema",
                "column_subset_projection",
                "investment_id_partition_shard",
                "io_minimization_gate",
            ],
            compression_relevance=(
                "Useful as a database-store prior: select only the columns or ID shard required "
                "by the RRC route instead of loading the full feature manifold."
            ),
            claim_boundary=(
                "External dataset/layout prior only; exact load times and sizes require local "
                "dataset receipts."
            ),
        ),
        packet(
            packet_id="KAGGLE.SANTA.PIXEL_TRAVEL_MAP.0001",
            name="Santa 2022 pixel travel map",
            source_surface="user-pasted Santa 2022 pixel travel map excerpt",
            source_urls=[
                "https://www.kaggle.com/code/oxzplvifi/pixel-travel-map",
                "https://www.kaggle.com/code/crodoc/82409-improved-baseline-santa-2022",
                "https://www.kaggle.com/code/ryanholbrook/getting-started-with-santa-2022",
            ],
            source_authors=["oxzplvifi", "crodoc", "Ryan Holbrook"],
            route=(
                "image pixels -> binary unvisited map -> down-first local motion -> least-cost "
                "single/double-link move -> nearest-unvisited recovery -> return-to-origin path"
            ),
            density_markers=[
                "binary_visit_bitmap",
                "down_first_hole_avoidance",
                "single_link_motion_enum",
                "double_link_motion_enum",
                "nearest_unvisited_recovery",
                "return_to_origin_constraint",
            ],
            compression_relevance=(
                "A direct topology-routing prior: a binary coverage map plus local move rules can "
                "encode traversal policy and residual recovery without storing the full route naively."
            ),
            claim_boundary=(
                "Algorithm sketch only; route cost, validity, and image traversal coverage require "
                "local replay with the Santa arm helpers."
            ),
        ),
        packet(
            packet_id="KAGGLE.MERCEDES.AUTOENCODER_FEATURE_COMPRESSION.0001",
            name="Mercedes autoencoder feature compression",
            source_surface="user-pasted Mercedes-Benz Greener Manufacturing notebook excerpt",
            source_urls=[
                "https://www.kaggle.com/code/remidi/neural-compression-auto-encoder-lb-0-55",
                "https://www.kaggle.com/competitions/mercedes-benz-greener-manufacturing",
            ],
            source_authors=["remidi"],
            route=(
                "categorical/numeric table -> one-hot + target means -> 12D autoencoder bottleneck "
                "+ PCA/ICA/SVD/random projections/NMF -> XGBoost + stacked ensemble"
            ),
            density_markers=[
                "autoencoder_bottleneck_12d",
                "denoised_reconstruction_surface",
                "target_mean_category_encoding",
                "multi_projection_feature_family",
                "stacking_prediction_as_feature",
                "weighted_ensemble_output",
            ],
            compression_relevance=(
                "Gives a compact-feature atlas prior: many heterogeneous projections can be treated "
                "as candidate manifold coordinates, with the autoencoder bottleneck as a lossy route."
            ),
            claim_boundary=(
                "Predictive feature-engineering prior only; neural bottleneck is lossy unless an "
                "explicit residual/reconstruction receipt is added."
            ),
        ),
        packet(
            packet_id="KAGGLE.AIMO3.SPECDEC_CONTEXT_APPLIANCE.0001",
            name="AIMO3 speculative decoding and context-compression appliance",
            source_surface=(
                "user-pasted Kaggle AIMO3 Eagle3/speculative decoding notebook excerpt "
                "https://www.kaggle.com/code/khoinguyennguyen/eagle3-specdecoding-optional-context-compression"
            ),
            source_urls=[
                "https://www.kaggle.com/code/khoinguyennguyen/eagle3-specdecoding-optional-context-compression",
                "https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3",
            ],
            source_authors=["khoinguyennguyen"],
            route=(
                "offline wheelhouse -> vLLM OpenAI server -> GPT-OSS model with Eagle3/ngram/draft "
                "speculative decoding -> persistent Jupyter tool sandboxes -> multi-attempt answer "
                "voting -> optional STATE_SUMMARY context reset"
            ),
            density_markers=[
                "offline_wheelhouse_environment",
                "speculative_decoding_eagle3",
                "fp8_kv_cache_surface",
                "persistent_jupyter_tool_pool",
                "multi_attempt_consensus_vote",
                "boxed_answer_range_gate",
                "context_handoff_summary",
                "gpu_memory_reclaim_guard",
            ],
            compression_relevance=(
                "This is an inference-control compression prior: reduce wall-clock and context waste "
                "by caching weights, drafting tokens, keeping tool kernels warm, and checkpointing "
                "long reasoning into a bounded handoff report."
            ),
            claim_boundary=(
                "Notebook excerpt only. Leaderboard score, speedup, correctness, and safety require "
                "local AIMO3 replay receipts. Context compression is disabled in the pasted CFG and "
                "must not be treated as validated."
            ),
        ),
    ]

    PACKETS.write_text("\n".join(stable_json(p) for p in packets) + "\n", encoding="utf-8")
    write_sources_cff(packets)
    receipt = {
        "schema": "kaggle_density_marker_prior_receipt_v1",
        "packet_count": len(packets),
        "packets": str(PACKETS.relative_to(REPO)),
        "sources_cff": str(SOURCES_CFF.relative_to(REPO)),
        "density_marker_total": sum(len(p["density_markers"]) for p in packets),
        "source_basis": "user-pasted Kaggle notebook excerpts in Codex session",
        "source_surfaces": [p["source_surface"] for p in packets],
        "license_provenance": KAGGLE_LICENSE_NOTICE,
        "route_families": [
            "tabular_dtype_memory_compression",
            "columnar_parquet_database_store",
            "topological_travel_map_path_planning",
            "neural_bottleneck_feature_compression",
            "aimo3_speculative_inference_appliance",
        ],
        "claim_boundary": (
            "These packets record algorithm-density markers only. No Kaggle dataset was downloaded "
            "or benchmark reproduced by this registry. All packets remain HOLD until local replay, "
            "byte law, residual, and receipt checks close."
        ),
        "decision": "HOLD",
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
