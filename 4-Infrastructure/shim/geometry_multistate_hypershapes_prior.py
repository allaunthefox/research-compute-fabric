#!/usr/bin/env python3
"""Geometry / multi-state hypershapes literature prior.

This consumes a local Consensus CSV export and distills it into a bounded
route-control prior for the projectable-geometry compressor.  The CSV is
evidence of a source bundle and search vocabulary; it is not compression
evidence.  Promotion still belongs to local encode/decode/hash receipts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path(
    "/home/allaun/Documents/ingest/geomtry and multi state hypershapes - May 07, 2026.csv"
)
DEFAULT_RECEIPT = Path(
    "4-Infrastructure/shim/geometry_multistate_hypershapes_prior_receipt.json"
)
DEFAULT_CURRICULUM = Path(
    "4-Infrastructure/shim/geometry_multistate_hypershapes_prior_curriculum.jsonl"
)


CLUSTERS = [
    {
        "id": "multistable_origami_metasurfaces",
        "keywords": [
            "origami",
            "fold",
            "bistable",
            "multistable",
            "metasurface",
            "tensegrity",
            "mechanism",
        ],
        "compressor_use": "fold-state gates for reversible route transitions and shell closure stress tests",
        "dd_state_fields": [
            "fold_state_id",
            "mechanism_class",
            "stability_class",
            "closure_receipt_id",
        ],
        "failure_mode": "fold changes byte reachability or opens recursive repair",
    },
    {
        "id": "manifold_geometric_deep_learning",
        "keywords": [
            "geometric deep learning",
            "manifold",
            "latent",
            "representation",
            "neural",
            "flow field",
            "gauge",
        ],
        "compressor_use": "proposal features for route clustering, latent route axes, and duplicate-island detection",
        "dd_state_fields": [
            "manifold_chart_id",
            "latent_route_axis_id",
            "local_flow_field_id",
            "feature_receipt_id",
        ],
        "failure_mode": "latent similarity promoted without byte-exact decode",
    },
    {
        "id": "tensor_network_entanglement_geometry",
        "keywords": [
            "tensor",
            "matrix product",
            "projected entangled",
            "entanglement",
            "many-body",
            "tensor network",
        ],
        "compressor_use": "bounded carrier topology for shared tokenbooks, local tensors, and sidecar factorization",
        "dd_state_fields": [
            "tensor_carrier_id",
            "bond_dimension_class",
            "local_factor_id",
            "residual_lane_id",
        ],
        "failure_mode": "factorization hides payload or increases sidecar beyond gain",
    },
    {
        "id": "quantum_phase_geometry",
        "keywords": [
            "quantum geometry",
            "berry",
            "quantum metric",
            "phase",
            "topological",
            "correlation",
            "bell",
        ],
        "compressor_use": "phase/metric witness for route holonomy, orbit changes, and nonclassical correlation diagnostics",
        "dd_state_fields": [
            "phase_metric_class",
            "holonomy_receipt_id",
            "orbit_change_id",
            "correlation_witness_id",
        ],
        "failure_mode": "phase witness treated as decoded payload instead of bounded receipt",
    },
    {
        "id": "molecular_shape_hyperstable_design",
        "keywords": [
            "molecular",
            "protein",
            "peptide",
            "drug",
            "shape",
            "electrostatic",
            "constrained",
        ],
        "compressor_use": "shape/electrostatic analogy for compact partial-feature bundles with exact residual lanes",
        "dd_state_fields": [
            "shape_signature_id",
            "electrostatic_feature_id",
            "compact_feature_bundle_id",
            "exact_residual_lane_id",
        ],
        "failure_mode": "shape match loses byte-level attributes",
    },
    {
        "id": "parallel_coordinate_hypershape_visualization",
        "keywords": [
            "parallel coordinates",
            "multi-dimensional",
            "hypershape",
            "visualizing",
            "high-dimensional",
        ],
        "compressor_use": "dashboard and feature-vector surface for inspecting high-dimensional route populations",
        "dd_state_fields": [
            "route_feature_vector_id",
            "axis_projection_id",
            "dashboard_card_id",
            "incumbent_receipt_id",
        ],
        "failure_mode": "visual separation mistaken for measured compression gain",
    },
]


PRACTICAL_LIMIT_PRIORS = [
    {
        "id": "state_explosion_and_spurious_minima",
        "source_prompt": "What are the practical limits of programmable multi-stability using geometric design?",
        "observed_limit": (
            "stable-state count may grow quickly with cell count, but unwanted minima "
            "and route ambiguity make specific target states hard to address"
        ),
        "compressor_mapping": "route family explosion and duplicate/spurious transform minima",
        "dd_guard": "require deterministic state selection, lower-bound pruning, and fail-closed tie receipts",
        "receipt_fields": [
            "stable_state_count_estimate",
            "spurious_state_count",
            "state_selection_policy_id",
            "tie_break_receipt_id",
        ],
        "failure_mode": "many possible states but no bounded path to the intended decoded byte stream",
    },
    {
        "id": "energy_barrier_and_transition_path",
        "source_prompt": "What are the practical limits of programmable multi-stability using geometric design?",
        "observed_limit": (
            "multi-compatible trusses and highly multistable structures need energy "
            "barriers and transition paths that remain controllable"
        ),
        "compressor_mapping": "transform transitions must have bounded repair cost and no recursive rollback",
        "dd_guard": "record transition energy/barrier class and reject unbounded repair paths",
        "receipt_fields": [
            "transition_path_id",
            "barrier_class",
            "rollback_window_bytes",
            "repair_path_depth",
        ],
        "failure_mode": "route transition exists in principle but requires unbounded search to repair",
    },
    {
        "id": "geometry_parameter_sensitivity",
        "source_prompt": "What are the practical limits of programmable multi-stability using geometric design?",
        "observed_limit": (
            "crease geometry, layer count, panel ratios, conical degree, graded height, "
            "and symmetry breaking strongly affect whether multistability survives"
        ),
        "compressor_mapping": "route parameters need tolerance bands before promotion",
        "dd_guard": "stress each promoted route under one-parameter perturbations and record N-1 failure packets",
        "receipt_fields": [
            "parameter_band_id",
            "n_minus_1_perturbation_count",
            "stability_margin_class",
            "failure_packet_id",
        ],
        "failure_mode": "byte win disappears under small admissible route-parameter perturbation",
    },
    {
        "id": "actuation_and_addressability",
        "source_prompt": "What are the practical limits of programmable multi-stability using geometric design?",
        "observed_limit": (
            "reachable stable states may require multi-DOF actuation, thermal windows, "
            "pneumatic control, or path-specific switching"
        ),
        "compressor_mapping": "candidate states must be addressable by a finite decoder/control packet",
        "dd_guard": "promote only if owner routing plus control witness selects the state without broadcast search",
        "receipt_fields": [
            "addressability_class",
            "control_packet_bytes",
            "owner_route_id",
            "broadcast_search_required",
        ],
        "failure_mode": "route is compact only if the decoder probes many candidate states",
    },
    {
        "id": "material_fatigue_and_tolerance",
        "source_prompt": "What are the practical limits of programmable multi-stability using geometric design?",
        "observed_limit": (
            "fatigue, hinge localization, allowable strain, local peak forces, and "
            "manufacturing tolerances limit repeated reliable switching"
        ),
        "compressor_mapping": "route should track repair churn, tolerance drift, and sidecar wear",
        "dd_guard": "reject aggressive routes whose repeated rehydration produces unstable repair churn",
        "receipt_fields": [
            "repair_churn_count",
            "tolerance_drift_class",
            "local_peak_sidecar_bytes",
            "repeat_decode_count",
        ],
        "failure_mode": "route passes once but is not stable under repeated decode/evaluate cycles",
    },
    {
        "id": "scalability_and_manufacturability",
        "source_prompt": "What are the practical limits of programmable multi-stability using geometric design?",
        "observed_limit": (
            "microscale and lattice designs scale, but fabrication and characterization "
            "constraints bound usable complexity"
        ),
        "compressor_mapping": "route witnesses must fit carrier capacity and remain inspectable",
        "dd_guard": "require witness budget, carrier capacity, and receipt readability before evaluation promotion",
        "receipt_fields": [
            "carrier_capacity_bytes",
            "witness_budget_bytes",
            "inspectability_status",
            "characterization_receipt_id",
        ],
        "failure_mode": "route metadata grows faster than measured byte savings",
    },
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_text(row: dict[str, str]) -> str:
    fields = [
        row.get("Title", ""),
        row.get("Takeaway", ""),
        row.get("Abstract", ""),
        row.get("Journal", ""),
    ]
    return " ".join(fields).lower()


def classify_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for cluster in CLUSTERS:
        matches: list[dict[str, Any]] = []
        keywords = [keyword.lower() for keyword in cluster["keywords"]]
        for row in rows:
            text = row_text(row)
            hit_count = sum(1 for keyword in keywords if keyword in text)
            if hit_count:
                matches.append(
                    {
                        "title": row.get("Title", ""),
                        "year": row.get("Year", ""),
                        "citations": int(row.get("Citations") or 0),
                        "doi": row.get("DOI", ""),
                        "consensus_link": row.get("Consensus Link", ""),
                        "matched_keyword_count": hit_count,
                    }
                )
        matches.sort(key=lambda item: (item["matched_keyword_count"], item["citations"]), reverse=True)
        item = dict(cluster)
        item["match_count"] = len(matches)
        item["top_matches"] = matches[:8]
        classified.append(item)
    return classified


def top_cited(rows: list[dict[str, str]], limit: int = 15) -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda row: int(row.get("Citations") or 0), reverse=True)
    return [
        {
            "title": row.get("Title", ""),
            "year": row.get("Year", ""),
            "citations": int(row.get("Citations") or 0),
            "doi": row.get("DOI", ""),
            "journal": row.get("Journal", ""),
            "consensus_link": row.get("Consensus Link", ""),
        }
        for row in ranked[:limit]
    ]


def build_receipt(source: Path) -> dict[str, Any]:
    rows = read_rows(source)
    source_mtime = datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat()
    fieldnames = list(rows[0].keys()) if rows else []
    years = Counter(row.get("Year", "") for row in rows if row.get("Year"))
    journals = Counter((row.get("Journal", "") or "<blank>").strip() or "<blank>" for row in rows)
    nonempty = {
        field: sum(1 for row in rows if (row.get(field, "") or "").strip())
        for field in fieldnames
    }
    clusters = classify_rows(rows)
    summary = {
        "row_count": len(rows),
        "fieldnames": fieldnames,
        "nonempty_fields": nonempty,
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "year_counts": dict(sorted(years.items())),
        "top_journals": [
            {"journal": journal, "count": count}
            for journal, count in journals.most_common(12)
        ],
        "top_cited": top_cited(rows),
    }
    receipt: dict[str, Any] = {
        "schema": "geometry_multistate_hypershapes_prior_v1",
        "generated_at": source_mtime,
        "source_csv": str(source),
        "source_sha256": sha256_path(source),
        "claim_boundary": (
            "Consensus CSV rows provide a geometry/multistate source bundle and "
            "route-control vocabulary only; local encode/decode/hash/byte-count "
            "receipts remain the compression authority."
        ),
        "summary": summary,
        "clusters": clusters,
        "practical_limit_priors": PRACTICAL_LIMIT_PRIORS,
        "route_extraction": {
            "base_object": "multi-state hypershape route family",
            "control_shape": [
                "finite state shell",
                "manifold chart",
                "tensor/fiber carrier",
                "phase/holonomy witness",
                "exact residual lane",
            ],
            "candidate_dd_edges": [
                "open_multistate_shape_shell",
                "choose_manifold_chart",
                "emit_tensor_or_fiber_carrier",
                "record_phase_holonomy_witness",
                "fold_state_if_reachability_preserved",
                "emit_exact_residual_lane",
                "close_with_rehydration_hash",
                "reject_unbounded_hypershape_expansion",
            ],
            "promotion_rule": (
                "promote iff the hypershape layer only proposes/constrains routes, "
                "all chart/fold/tensor/phase witnesses are bounded, exact residual "
                "lanes restore source bytes, decoded hash matches, and measured "
                "total bytes beat the incumbent under one explicit ratio_schema"
            ),
            "failure_rule": (
                "latent geometry, visual separation, quantum phase, or tensor "
                "factorization without byte-exact residual repair is diagnostic only"
            ),
            "practical_limit_rule": (
                "multistability is useful only when states are addressable, stable "
                "under bounded perturbation, cheap to switch, and small enough to "
                "receipt without losing the measured byte gain"
            ),
        },
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = (
        "You are a projectable-geometry compression route controller. "
        "Use literature clusters as bounded proposal priors only."
    )
    records: list[dict[str, Any]] = []
    for cluster in receipt["clusters"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "route_geometry_hypershape_cluster",
                                "cluster_id": cluster["id"],
                                "match_count": cluster["match_count"],
                                "compressor_use": cluster["compressor_use"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "selected": cluster["match_count"] > 0,
                                "dd_state_fields": cluster["dd_state_fields"],
                                "failure_mode": cluster["failure_mode"],
                                "claim_boundary": "source-bundle-prior-only",
                                "promotion_authority": "local encode/decode/hash/byte-count receipt",
                            },
                            ensure_ascii=False,
                        ),
                    },
                ]
            }
        )
    for prior in receipt["practical_limit_priors"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "route_practical_multistability_limit",
                                "limit_id": prior["id"],
                                "observed_limit": prior["observed_limit"],
                                "compressor_mapping": prior["compressor_mapping"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "selected": True,
                                "dd_guard": prior["dd_guard"],
                                "receipt_fields": prior["receipt_fields"],
                                "failure_mode": prior["failure_mode"],
                                "claim_boundary": "practical-limit-prior-only",
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
