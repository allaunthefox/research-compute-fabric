#!/usr/bin/env python3
"""Model the best bounded topology approach for projectable compression.

This is a design-prior receipt, not a byte compressor.  It consumes the
dimensional shell decision-diagram receipt and chooses the best current route
that can carry the topology triad inside the closure-witness budget:

* Menger sponge: sparse bucket substrate
* Torus: cyclic lane carrier
* Braid: lawful transition/crossing witness

The important rule is that the triad must fit inside the existing bounded
closure witness.  If it needs recursive explanation, it is NaN0 and rejected.

In the finer-grain version, Menger voids are modeled as black-hole buckets:
the decoder may verify a boundary/horizon witness, but it may not expand the
interior.  Any route that needs to inspect the interior becomes NaN0.

The invariant-dual mechanics prior adds a second guard: the static witness
side behaves like tensegrity self-stress, while the decode-motion side behaves
like an origami infinitesimal mechanism.  Nondegenerate transformations may
change the shape, but must preserve the closure class.

The deterministic-routing prior adds an ownership rule: the decoder routes a
symbol, residual, or repair request to its owning horizon/lane instead of
replicating the request across candidate buckets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHELL_DD_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "dimensional_shell_dd_probe_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "shim"
    / "projectable_geometry_topology_model_receipt.json"
)


TOPOLOGY_WITNESS_ALLOCATION = {
    "menger_bucket_witness_bytes": 4,
    "torus_carrier_witness_bytes": 4,
    "braid_rule_witness_bytes": 4,
    "nan0_closure_witness_bytes": 4,
}

TOPOLOGY_BITFIELDS = {
    "menger_black_hole_bucket": {
        "total_bits": 32,
        "fields": {
            "horizon_id_bits": 12,
            "void_depth_bits": 4,
            "horizon_area_class_bits": 8,
            "skip_mass_class_bits": 8,
        },
    },
    "torus_orbit_carrier": {
        "total_bits": 32,
        "fields": {
            "lane_modulus_bits": 10,
            "phase_index_bits": 10,
            "orbit_direction_bits": 2,
            "affine_transform_class_bits": 4,
            "wrap_epoch_bits": 6,
        },
    },
    "braid_crossing_rule": {
        "total_bits": 32,
        "fields": {
            "crossing_id_bits": 8,
            "chirality_bits": 2,
            "rule_id_bits": 10,
            "static_self_stress_class_bits": 4,
            "kinematic_mechanism_class_bits": 4,
            "parity_crc_bits": 4,
        },
    },
    "nan0_closure": {
        "total_bits": 32,
        "fields": {
            "nan0_flag_bits": 1,
            "mass_delta_q_bits": 13,
            "horizon_hash_bits": 12,
            "nondegenerate_transform_witness_bits": 3,
            "superstability_witness_bits": 3,
        },
    },
}

TOPOLOGY_EQUATIONS = {
    "shell_mass": (
        "source_mass = visible_4d + horizon_mass + orbit_mass + braid_mass "
        "+ lawbound_mass; unresolved_mass = 0"
    ),
    "menger_void": (
        "void_i = (horizon_id, void_depth, horizon_area_class, skip_mass_class)"
    ),
    "black_hole_boundary": (
        "interior(void_i) is non-decodable; decoder verifies horizon(void_i) only"
    ),
    "torus_orbit": (
        "lane_t = (lane_0 + phase_index + tick) mod lane_modulus"
    ),
    "deterministic_owner": (
        "owner_i = hash(horizon_id, lane_modulus, phase_index, route_key) mod lane_modulus"
    ),
    "route_to_data": (
        "decode requests route to owner_i; do not replicate speculative reads across voids"
    ),
    "braid_transition": (
        "state_{t+1} = braid_rule(crossing_id, chirality, rule_id, state_t)"
    ),
    "closure": (
        "close iff mass_delta_q == 0 and horizon_hash matches and nan0_flag == 0"
    ),
    "invariant_duality": (
        "static_self_stress_class(void_i) is dual to "
        "kinematic_mechanism_class(fold_i)"
    ),
    "nondegenerate_transform": (
        "T is admissible iff det_class(T) != 0 and closure_class(T*x) == closure_class(x)"
    ),
    "superstability_guard": (
        "promote invariant route only if geometry_rank_class is full and "
        "force_density_class is PSD-compatible"
    ),
    "fail_closed": (
        "if interior expansion is requested or closure fails, emit NaN0 and stop"
    ),
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def topology_witness_bytes() -> int:
    return sum(TOPOLOGY_WITNESS_ALLOCATION.values())


def validate_topology_bitfields() -> list[str]:
    errors: list[str] = []
    for name, spec in TOPOLOGY_BITFIELDS.items():
        total = int(spec["total_bits"])
        field_sum = sum(int(value) for value in spec["fields"].values())
        if field_sum != total:
            errors.append(f"{name} fields sum to {field_sum}, expected {total}")
    expected_bits = topology_witness_bytes() * 8
    actual_bits = sum(int(spec["total_bits"]) for spec in TOPOLOGY_BITFIELDS.values())
    if actual_bits != expected_bits:
        errors.append(f"topology bitfields sum to {actual_bits}, expected {expected_bits}")
    return errors


def promoted_routes(shell_dd: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for slice_item in shell_dd.get("slices", []):
        for route in slice_item.get("routes", []):
            if route.get("decision") == "promoted":
                routes.append(route)
    return routes


def model_route(route: dict[str, Any], witness_bytes: int) -> dict[str, Any]:
    overhead_budget = int(route["overhead_budget_before_losing_raw"])
    fits_budget = witness_bytes <= overhead_budget
    no_recursive_debt = (
        route.get("shell_status", {}).get("closed") is True
        and route.get("shell_status", {}).get("nan0") is False
    )
    lawful = fits_budget and no_recursive_debt
    modeled_bytes = int(route["compressed_bytes"]) + witness_bytes
    source_bytes = int(route["source_bytes"])
    return {
        "route_id": route["route_id"],
        "slice": route["slice"],
        "source_bytes": source_bytes,
        "transform": route["transform"],
        "codec": route["codec"],
        "compressed_bytes": route["compressed_bytes"],
        "raw_baseline_bytes": route["raw_baseline_bytes"],
        "topology_witness_bytes": witness_bytes,
        "modeled_total_bytes": modeled_bytes,
        "modeled_ratio": modeled_bytes / source_bytes if source_bytes else 0.0,
        "gain_vs_raw_after_topology_bytes": int(route["raw_baseline_bytes"]) - modeled_bytes,
        "overhead_budget_before_losing_raw": overhead_budget,
        "fits_witness_budget": fits_budget,
        "no_recursive_debt": no_recursive_debt,
        "lawful": lawful,
        "reject_reason": None if lawful else (
            "topology_witness_exceeds_budget" if not fits_budget else "nan0_or_recursive_debt"
        ),
    }


def build_receipt() -> dict[str, Any]:
    bitfield_errors = validate_topology_bitfields()
    if bitfield_errors:
        raise ValueError("; ".join(bitfield_errors))

    shell_dd = load_json(SHELL_DD_RECEIPT)
    witness_bytes = topology_witness_bytes()
    modeled = [
        model_route(route, witness_bytes)
        for route in promoted_routes(shell_dd)
    ]
    lawful = [route for route in modeled if route["lawful"]]
    rejected = [route for route in modeled if not route["lawful"]]
    best = min(lawful, key=lambda item: item["modeled_ratio"]) if lawful else None

    receipt = {
        "schema": "projectable_geometry_topology_model_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "projectable_geometry_topology_model",
        "source": {
            "shell_dd_receipt": str(SHELL_DD_RECEIPT.relative_to(REPO)),
            "shell_dd_stable_hash_sha256": shell_dd.get("stable_shell_dd_hash_sha256"),
            "invariant_dual_mechanics_prior": {
                "title": "Invariant dual mechanics of tensegrity and origami",
                "doi": "10.1073/pnas.2519138123",
                "mapping": (
                    "Use tensegrity self-stress as the static horizon witness "
                    "and origami infinitesimal mechanism as the decode-motion "
                    "witness; nondegenerate transforms must preserve closure."
                ),
            },
            "deterministic_routing_prior": {
                "title": (
                    "Deterministic routing is one of the most effective ways "
                    "distributed systems reduce consistency problems at scale"
                ),
                "url": "https://bencane.com/posts/2026-04-30/",
                "mapping": (
                    "Route compressed-symbol, residual, and repair requests to "
                    "their owning horizon/lane instead of probing multiple "
                    "candidate buckets. This reduces stale speculative state "
                    "and avoids consistency work by construction."
                ),
            },
        },
        "topology_triad": {
            "menger_sponge": {
                "role": "black-hole bucket lattice",
                "compressor_use": (
                    "Names admissible voids as bounded non-expanded buckets. "
                    "Only the horizon witness is decoded; the interior is forbidden."
                ),
            },
            "torus": {
                "role": "cyclic lane carrier",
                "compressor_use": (
                    "Provides wraparound lane addressing, phase continuity, and "
                    "bounded clock/cadence fields."
                ),
            },
            "braid": {
                "role": "lawful transition witness",
                "compressor_use": (
                    "Constrains crossings, chirality, lane interaction, and "
                    "reversible rule order."
                ),
            },
        },
        "witness_allocation": {
            **TOPOLOGY_WITNESS_ALLOCATION,
            "total_topology_witness_bytes": witness_bytes,
            "meaning": (
                "The triad must fit inside the bounded closure witness. It is a "
                "route-control packet, not an expanding residual tree."
            ),
        },
        "finer_grain_equations": {
            "equations": TOPOLOGY_EQUATIONS,
            "bitfields": TOPOLOGY_BITFIELDS,
            "resolution_rule": (
                "Resolution improves by subdividing the 16-byte witness into "
                "bounded bitfields, not by adding recursive residual depth."
            ),
            "invariant_duality_rule": (
                "A transformed route may be reused only when its static "
                "self-stress class and kinematic mechanism class remain paired "
                "under a nondegenerate transform witness."
            ),
            "deterministic_routing_rule": (
                "Every symbol or repair request has exactly one owning horizon "
                "for a given route key. The decoder routes to ownership first "
                "and only uses replication/fallback for durability, never for "
                "ordinary parse choice."
            ),
            "black_hole_void_rule": (
                "Menger voids are black-hole buckets: verify the horizon, never "
                "decode the interior, and fail closed if interior expansion is "
                "requested."
            ),
        },
        "best_approach": {
            "name": "Menger-BlackHole-Torus-Braid Shell Route v1",
            "route": "xml_token -> topology_witness_16b -> bz2",
            "packet_order": [
                "Menger black-hole bucket horizon",
                "Torus orbit lane modulus/phase",
                "Braid crossing/chirality law",
                "NaN0 closure witness",
            ],
            "selected_route": best,
            "implementation_rule": (
                "Keep the byte transform at the proven xml_token route first. "
                "Use the topology triad only as the bounded DD control witness "
                "until a real encoder proves byte savings."
            ),
        },
        "summary": {
            "modeled_promoted_route_count": len(modeled),
            "lawful_route_count": len(lawful),
            "rejected_route_count": len(rejected),
            "best_modeled_route": best,
            "all_lawful_routes": lawful,
            "rejected_routes": rejected,
        },
        "claim_boundary": (
            "This receipt models the best current topology-aware route using "
            "existing compression measurements. It is not a new compression "
            "benchmark, Hutter claim, physical topology claim, or optimality proof."
        ),
        "lawful": best is not None,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "topology_triad": receipt["topology_triad"],
        "witness_allocation": receipt["witness_allocation"],
        "finer_grain_equations": receipt["finer_grain_equations"],
        "best_approach": receipt["best_approach"],
        "summary": receipt["summary"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_topology_model_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_topology_model_hash_sha256": receipt["stable_topology_model_hash_sha256"],
        "best_approach": receipt["best_approach"],
        "summary": {
            "modeled_promoted_route_count": receipt["summary"]["modeled_promoted_route_count"],
            "lawful_route_count": receipt["summary"]["lawful_route_count"],
            "rejected_route_count": receipt["summary"]["rejected_route_count"],
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
