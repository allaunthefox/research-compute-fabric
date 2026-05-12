#!/usr/bin/env python3
"""Curated MDPI density-marker miner.

This is a conservative metadata miner.  It records paper-level route candidates
and density markers, not article bodies.  Each candidate is treated as an RRC
prior until local replay/byte-law evidence exists.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "mdpi_density_markers"
JSONL = OUT_DIR / "mdpi_density_marker_candidates.jsonl"
CSV = OUT_DIR / "mdpi_density_marker_candidates.csv"
RECEIPT = OUT_DIR / "mdpi_density_marker_miner_receipt.json"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


CANDIDATES: list[dict[str, Any]] = [
    {
        "candidate_id": "MDPI.MILPE.EIGENVECTOR_PROJECTION.2026.0001",
        "title": "Multivariate Identification via Linear Projection of Eigenvectors",
        "journal": "Mathematics",
        "year": 2026,
        "url": "https://www.mdpi.com/2227-7390/14/5/897",
        "doi": "10.3390/math14050897",
        "density_markers": [
            "joint_input_output_solution_space",
            "cross_correlation_eigenvectors",
            "partial_eigenvector_replay",
            "low_rank_governing_equation_projection",
        ],
        "rrc_use": "LanguageSetMILPEProjection and density-marker eigenvector search",
        "claim_boundary": "algorithmic prior for projection/replay; not proof of language model correctness",
        "status": "CANDIDATE",
    },
    {
        "candidate_id": "MDPI.ENTROPY.EIGENVECTOR_LOCALIZATION.2019.0001",
        "title": "Information Entropy of Tight-Binding Random Networks with Losses and Gain",
        "journal": "Entropy",
        "year": 2019,
        "url": "https://www.mdpi.com/1099-4300/21/1/86",
        "doi": "10.3390/e21010086",
        "density_markers": [
            "eigenvector_information_entropy",
            "localized_extended_transition",
            "complex_spectrum_network_prior",
            "graph_adjacency_entropy_surface",
        ],
        "rrc_use": "score whether density-marker eigenvectors are localized, extended, or transition-like",
        "claim_boundary": "network spectral prior only until reproduced on local language/code graphs",
        "status": "HOLD",
    },
    {
        "candidate_id": "MDPI.ENTROPY.AUTOENCODER_INFORMATION_FLOW.2021.0001",
        "title": "Information Flows of Diverse Autoencoders",
        "journal": "Entropy",
        "year": 2021,
        "url": "https://www.mdpi.com/1099-4300/23/7/862",
        "doi": "10.3390/e23070862",
        "density_markers": [
            "information_plane_flow",
            "hidden_representation_compression_phase",
            "renyi_matrix_entropy",
            "sparsity_simplifying_phase",
        ],
        "rrc_use": "compare density-marker compression flow against hidden-representation simplification",
        "claim_boundary": "deep-learning diagnostic prior only; not a language compression result",
        "status": "HOLD",
    },
    {
        "candidate_id": "MDPI.SENSORS.GRAPH_LIGHT_FIELD_CODING.2022.0001",
        "title": "Novel Projection Schemes for Graph-Based Light Field Coding",
        "journal": "Sensors",
        "year": 2022,
        "url": "https://www.mdpi.com/1424-8220/22/13/4948",
        "doi": "10.3390/s22134948",
        "density_markers": [
            "graph_based_signal_redundancy",
            "irregular_shape_energy_compaction",
            "super_ray_projection",
            "graph_transform_coding",
        ],
        "rrc_use": "graph-transform analogy for irregular language/code density surfaces",
        "claim_boundary": "image/light-field coding prior only; needs local graph replay",
        "status": "HOLD",
    },
    {
        "candidate_id": "MDPI.ENTROPY.COMPLEX_NETWORK_ENTROPY_SURVEY.2020.0001",
        "title": "A Survey of Information Entropy Metrics for Complex Networks",
        "journal": "Entropy",
        "year": 2020,
        "url": "https://www.mdpi.com/1099-4300/22/12/1417",
        "doi": "10.3390/e22121417",
        "density_markers": [
            "graph_entropy_metric_catalog",
            "eigenvector_centrality_entropy",
            "topological_potential_entropy",
            "network_probability_distribution_choice",
        ],
        "rrc_use": "choose entropy measures for language-set density-marker graphs",
        "claim_boundary": "metric catalog prior; metric choice must be receipted per graph",
        "status": "CANDIDATE",
    },
    {
        "candidate_id": "MDPI.ALGORITHMS.MAXENT_GRAPH_SPECTRUM.2022.0001",
        "title": "Maximum Entropy Approach to Massive Graph Spectrum Learning with Applications",
        "journal": "Algorithms",
        "year": 2022,
        "url": "https://www.mdpi.com/1999-4893/15/6/209",
        "doi": "10.3390/a15060209",
        "density_markers": [
            "maximum_entropy_spectral_density",
            "graph_moment_information",
            "massive_graph_spectrum_approximation",
            "kernel_free_spectral_estimate",
        ],
        "rrc_use": "estimate spectrum of large language/code manifold graphs without full eigendecomposition",
        "claim_boundary": "spectral approximation prior; not accepted until compared with local exact small graphs",
        "status": "HOLD",
    },
    {
        "candidate_id": "MDPI.ENTROPY.NETWORK_CODING_THERMODYNAMICS.2019.0001",
        "title": "The Thermodynamics of Network Coding, and an Algorithmic Refinement of the Principle of Maximum Entropy",
        "journal": "Entropy",
        "year": 2019,
        "url": "https://www.mdpi.com/1099-4300/21/6/560",
        "doi": "10.3390/e21060560",
        "density_markers": [
            "algorithmic_probability_network_prior",
            "graph_entropy_distribution_dependence",
            "compressed_program_nonrandomness_witness",
            "maximum_entropy_refinement",
        ],
        "rrc_use": "separate apparent graph entropy from generator-law compressibility",
        "claim_boundary": "algorithmic-information prior; needs computable local compressor witness",
        "status": "CANDIDATE",
    },
    {
        "candidate_id": "MDPI.ENTROPY.MULTIDIMENSIONAL_NETWORK_DISTORTION.2021.0001",
        "title": "Algorithmic Information Distortions in Node-Aligned and Node-Unaligned Multidimensional Networks",
        "journal": "Entropy",
        "year": 2021,
        "url": "https://www.mdpi.com/1099-4300/23/7/835",
        "doi": "10.3390/e23070835",
        "density_markers": [
            "multidimensional_network_complexity",
            "lossless_compression_graph_distortion",
            "node_alignment_effect",
            "multilayer_network_information_content",
        ],
        "rrc_use": "warn when aligning language/code graph layers changes algorithmic information",
        "claim_boundary": "distortion prior; local alignment receipts required",
        "status": "HOLD",
    },
    {
        "candidate_id": "MDPI.ENTROPY.UNIQUE_INFORMATION.2014.0001",
        "title": "Quantifying Unique Information",
        "journal": "Entropy",
        "year": 2014,
        "url": "https://www.mdpi.com/70176",
        "doi": "10.3390/e16042161",
        "density_markers": [
            "shared_unique_synergistic_information",
            "partial_information_decomposition_prior",
            "marginal_invariance_property",
            "redundancy_synergy_split",
        ],
        "rrc_use": "separate shared density markers from language-specific unique markers",
        "claim_boundary": "information-decomposition prior; requires local variable definitions",
        "status": "CANDIDATE",
    },
    {
        "candidate_id": "MDPI.ENTROPY.TOPOLOGICAL_INFORMATION_DATA_ANALYSIS.2019.0001",
        "title": "Topological Information Data Analysis",
        "journal": "Entropy",
        "year": 2019,
        "url": "https://www.mdpi.com/1099-4300/21/9/869",
        "doi": "10.3390/e21090869",
        "density_markers": [
            "homological_information_functions",
            "mutual_information_decomposition_topology",
            "information_complex",
            "topological_data_analysis_entropy",
        ],
        "rrc_use": "topological lens for density-marker graph decompositions",
        "claim_boundary": "topological-information prior; needs local graph construction",
        "status": "HOLD",
    },
    {
        "candidate_id": "MDPI.ENTROPY.MULTIMODAL_INFORMATION_BOTTLENECK.2026.0001",
        "title": "A Unified Information Bottleneck Framework for Multimodal Biomedical Machine Learning",
        "journal": "Entropy",
        "year": 2026,
        "url": "https://www.mdpi.com/journal/entropy",
        "doi": "10.3390/e28040445",
        "density_markers": [
            "information_bottleneck_tradeoff",
            "modality_redundancy_synergy",
            "fusion_collapse_diagnostic",
            "transfer_entropy_sequence_prior",
        ],
        "rrc_use": "analogy for multi-language/code modality fusion and redundancy scoring",
        "claim_boundary": "journal listing/abstract prior; verify article page before promotion",
        "status": "HOLD",
    },
]


def packetize(candidate: dict[str, Any]) -> dict[str, Any]:
    packet = {
        "schema": "mdpi_density_marker_candidate_v1",
        "source_family": "MDPI",
        "rrc_shape_hint": "LanguageSetMILPEProjection",
        **candidate,
    }
    packet["packet_hash"] = sha256_text(stable_json(packet))
    return packet


def csv_escape(value: Any) -> str:
    text = str(value).replace('"', '""')
    return f'"{text}"'


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packets = [packetize(candidate) for candidate in CANDIDATES]
    JSONL.write_text("\n".join(stable_json(packet) for packet in packets) + "\n", encoding="utf-8")

    lines = ["candidate_id,title,journal,year,status,density_markers,rrc_use,url,doi,packet_hash"]
    for packet in packets:
        lines.append(
            ",".join(
                [
                    csv_escape(packet["candidate_id"]),
                    csv_escape(packet["title"]),
                    csv_escape(packet["journal"]),
                    csv_escape(packet["year"]),
                    csv_escape(packet["status"]),
                    csv_escape(";".join(packet["density_markers"])),
                    csv_escape(packet["rrc_use"]),
                    csv_escape(packet["url"]),
                    csv_escape(packet["doi"]),
                    csv_escape(packet["packet_hash"]),
                ]
            )
        )
    CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    status_counts: dict[str, int] = {}
    for packet in packets:
        status_counts[packet["status"]] = status_counts.get(packet["status"], 0) + 1
    receipt = {
        "schema": "mdpi_density_marker_miner_receipt_v1",
        "claim_boundary": "Metadata-only MDPI mining surface; candidates are priors until local replay, residual, and byte-law receipts exist.",
        "candidate_count": len(packets),
        "status_counts": status_counts,
        "jsonl": str(JSONL.relative_to(REPO)),
        "csv": str(CSV.relative_to(REPO)),
        "candidate_ids": [packet["candidate_id"] for packet in packets],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
