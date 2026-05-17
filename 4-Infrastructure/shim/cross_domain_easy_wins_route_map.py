#!/usr/bin/env python3
"""Build a receipt-backed route map of easy cross-domain kernel wins.

The map ranks domains where local algebraic/logogram fixtures are likely to be
cheap to encode and easy to verify. It is a planning receipt, not a benchmark or
domain-proof result.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "cross_domain_easy_wins"
ROUTE_MAP = OUT_DIR / "cross_domain_easy_wins_route_map.json"
RECEIPT = OUT_DIR / "cross_domain_easy_wins_route_map_receipt.json"
SUMMARY = OUT_DIR / "cross_domain_easy_wins_route_map.md"

SOURCE_REFS = [
    REPO / "shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
    REPO / "shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry_receipt.json",
    REPO / "shared-data/data/magnetic_derivative_kernels/magnetic_derivative_kernel_receipt.json",
    REPO / "shared-data/data/solids_physics_kernels/solids_physics_kernel_receipt.json",
    REPO / "shared-data/data/mmff_rigid_body_geometry/mmff_rigid_body_geometry_receipt.json",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def route(
    *,
    rank: int,
    route_id: str,
    domain: str,
    easy_kernels: list[str],
    fixture_targets: list[str],
    hold_hazards: list[str],
    next_probe: str,
    estimated_candidate_yield: str,
    decision: str = "ROUTE_READY",
) -> dict[str, Any]:
    item = {
        "rank": rank,
        "route_id": route_id,
        "domain": domain,
        "easy_kernels": easy_kernels,
        "fixture_targets": fixture_targets,
        "hold_hazards": hold_hazards,
        "next_probe": next_probe,
        "estimated_candidate_yield": estimated_candidate_yield,
        "decision": decision,
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def build_route_map() -> dict[str, Any]:
    routes = [
        route(
            rank=1,
            route_id="circuits_impedance",
            domain="electrical circuits and transmission lines",
            easy_kernels=["MN_REFLECT", "MN_TRANSMIT_POWER", "MN_PAIR_PRODUCT", "MN_REDUCED"],
            fixture_targets=[
                "voltage divider",
                "Thevenin/Norton pair reduction",
                "series/parallel resistor identities",
                "transmission-line reflection coefficient",
            ],
            hold_hazards=["frequency-dependent parasitics", "nonlinear devices", "layout/skin-effect models"],
            next_probe="electrical_circuit_kernel_probe.py",
            estimated_candidate_yield="high",
        ),
        route(
            rank=2,
            route_id="thermal_diffusion",
            domain="thermal conduction and diffusion",
            easy_kernels=["MN_REFLECT", "MN_REDUCED", "MN_BLEND", "DERIV_LINEAR"],
            fixture_targets=[
                "thermal resistance series/parallel",
                "effusivity boundary contrast",
                "two-material steady flux",
                "lumped RC thermal time constant",
            ],
            hold_hazards=["transient PDE solves", "phase change", "temperature-dependent material laws"],
            next_probe="thermal_diffusion_kernel_probe.py",
            estimated_candidate_yield="high",
        ),
        route(
            rank=3,
            route_id="acoustics_waves",
            domain="acoustics and scalar waves",
            easy_kernels=["MN_REFLECT", "MN_TRANSMIT_POWER", "ANALYTIC_SQRT_RATIO"],
            fixture_targets=[
                "normal-incidence impedance reflection",
                "power transmission from reflection coefficient",
                "string/wave speed scalar route",
            ],
            hold_hazards=["oblique incidence", "loss/attenuation", "mode conversion", "boundary geometry"],
            next_probe="acoustic_wave_kernel_probe.py",
            estimated_candidate_yield="high",
        ),
        route(
            rank=4,
            route_id="probability_routing",
            domain="probability, routing, and expert selection",
            easy_kernels=["MN_BINARY_P", "MN_BLEND", "MN_BINARY_ENTROPY"],
            fixture_targets=[
                "two-route normalized probability",
                "confidence-weighted blend",
                "binary odds recovery",
                "entropy route with declared numeric policy",
            ],
            hold_hazards=["uncalibrated priors", "correlated experts", "floating-point entropy policy"],
            next_probe="probability_routing_kernel_probe.py",
            estimated_candidate_yield="very_high",
        ),
        route(
            rank=5,
            route_id="orbital_two_body",
            domain="two-body mechanics and orbital reductions",
            easy_kernels=["MN_SPLIT", "MN_REDUCED", "MN_ELASTIC_1D"],
            fixture_targets=[
                "mass split from total and MN",
                "reduced mass",
                "center-of-mass blend",
                "1D elastic collision",
            ],
            hold_hazards=["N-body dynamics", "relativistic corrections", "numerical integration"],
            next_probe="two_body_mechanics_kernel_probe.py",
            estimated_candidate_yield="high",
        ),
        route(
            rank=6,
            route_id="mmff_rigid_body_geometry",
            domain="MMFF-style molecular geometry as rigid/semi-rigid bodies",
            easy_kernels=["RIGID_BODY_POSE", "HINGED_RIGID_BODY", "MN_BOND_DEVIATION", "TORSION_OPCODE"],
            fixture_targets=[
                "linear triad coordinate replay",
                "bent triad coordinate replay",
                "aromatic ring template pose",
                "methyl rotor hinge state",
            ],
            hold_hazards=[
                "MMFF atom typing",
                "aromaticity perception",
                "parameter lookup tables",
                "partial charges and nonbonded cutoffs",
                "energy minimization and conformer ranking",
            ],
            next_probe="mmff_rigid_body_geometry_probe.py",
            estimated_candidate_yield="high",
        ),
        route(
            rank=7,
            route_id="chemistry_equilibrium",
            domain="chemistry equilibrium and reaction routing",
            easy_kernels=["MN_RATIO_INV", "MN_BINARY_P", "MN_BLEND"],
            fixture_targets=[
                "two-species normalized fraction",
                "odds/ratio recovery",
                "mixture weighted property",
                "two-lane equilibrium contrast fixture",
            ],
            hold_hazards=["activity coefficients", "temperature dependence", "kinetics and catalysis"],
            next_probe="chemistry_equilibrium_kernel_probe.py",
            estimated_candidate_yield="medium_high",
        ),
        route(
            rank=8,
            route_id="optics_fresnel",
            domain="optics at normal incidence",
            easy_kernels=["MN_REFLECT", "MN_TRANSMIT_POWER"],
            fixture_targets=[
                "normal-incidence amplitude reflection",
                "power transmission from contrast",
                "index/impedance contrast",
            ],
            hold_hazards=["polarization", "oblique incidence", "complex refractive index", "thin-film interference"],
            next_probe="optics_fresnel_kernel_probe.py",
            estimated_candidate_yield="medium_high",
        ),
        route(
            rank=9,
            route_id="statistics_effect_size",
            domain="statistics and signal scoring",
            easy_kernels=["MN", "MN_BLEND", "MN_BINARY_ENTROPY"],
            fixture_targets=[
                "two-bin contrast",
                "normalized difference score",
                "weighted mean update",
                "binary uncertainty score",
            ],
            hold_hazards=["sampling assumptions", "p-value misuse", "distributional claims"],
            next_probe="statistics_signal_kernel_probe.py",
            estimated_candidate_yield="medium",
        ),
        route(
            rank=10,
            route_id="bio_expression_contrast",
            domain="biology expression/accessibility contrast",
            easy_kernels=["MN", "MN_BINARY_P", "MN_BLEND"],
            fixture_targets=[
                "two-condition expression contrast",
                "accessibility contrast",
                "two-source regulatory blend",
            ],
            hold_hazards=["biological causality", "batch effects", "measurement normalization", "thermodynamic overclaim"],
            next_probe="bio_expression_contrast_kernel_probe.py",
            estimated_candidate_yield="medium",
        ),
        route(
            rank=11,
            route_id="geometry_contact",
            domain="contact geometry and motion planning",
            easy_kernels=["MN", "MN_BLEND"],
            fixture_targets=[
                "two-clearance contact contrast",
                "signed-distance transition fixture",
                "contact-regime switch scoring",
            ],
            hold_hazards=["continuous collision proof", "area optimality", "path completeness"],
            next_probe="contact_geometry_kernel_probe.py",
            estimated_candidate_yield="medium",
            decision="ROUTE_HOLD_FIRST",
        ),
    ]
    return {
        "schema": "cross_domain_easy_wins_route_map_v1",
        "claim_boundary": (
            "Planning receipt only. It ranks likely low-cost cross-domain kernel "
            "probes; it does not assert compression gain, domain truth, or benchmark "
            "performance. Each route still requires its own fixture receipt."
        ),
        "canonical_statement": (
            "Easy wins are domains where exact local algebra kernels can be checked "
            "before domain-specific PDEs, material laws, geometry, or measurement "
            "claims are touched."
        ),
        "selection_rule": "prefer exact local algebra first; HOLD nonlinear, field, geometry, and measurement claims",
        "routes": routes,
        "route_count": len(routes),
        "status_counts": {
            status: sum(1 for item in routes if item["decision"] == status)
            for status in sorted({item["decision"] for item in routes})
        },
    }


def build_receipt(route_map: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "cross_domain_easy_wins_route_map_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "route_map_path": rel(ROUTE_MAP),
        "route_map_hash": hash_obj(route_map),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "route_count": route_map["route_count"],
        "status_counts": route_map["status_counts"],
        "decision": "ADMIT_ROUTE_MAP_HOLD_FIRST",
        "claim_boundary": route_map["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(route_map: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Cross-Domain Easy Wins Route Map",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        route_map["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        route_map["canonical_statement"],
        "",
        "## Ranked Routes",
        "",
        "| Rank | Route | Domain | Yield | Decision | Next probe |",
        "|---:|---|---|---|---|---|",
    ]
    for item in route_map["routes"]:
        lines.append(
            f"| {item['rank']} | `{item['route_id']}` | {item['domain']} | "
            f"{item['estimated_candidate_yield']} | `{item['decision']}` | `{item['next_probe']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            route_map["selection_rule"],
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    route_map = build_route_map()
    receipt = build_receipt(route_map)
    ROUTE_MAP.write_text(json.dumps(route_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(route_map, receipt)
    print(
        json.dumps(
            {
                "route_map": rel(ROUTE_MAP),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "status_counts": route_map["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
