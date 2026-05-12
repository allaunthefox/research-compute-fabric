#!/usr/bin/env python3
"""Receipt-backed map of domains suited for refined shadow-layer encoding.

Shadow encoding applies when a visible low-dimensional object is best treated
as a projection of a richer typed state. The visible layer can be compact, but
only if the hidden state, adapter, residual, closure policy, and algebraic
accumulator path are receipted.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "shadow_layer_opportunities"
MAP = OUT_DIR / "shadow_layer_opportunity_map.json"
RECEIPT = OUT_DIR / "shadow_layer_opportunity_map_receipt.json"
SUMMARY = OUT_DIR / "shadow_layer_opportunity_map.md"

SOURCE_REFS = [
    REPO / "4-Infrastructure" / "shim" / "mmff_rigid_body_geometry_probe.py",
    REPO / "shared-data" / "data" / "mmff_rigid_body_geometry" / "mmff_rigid_body_geometry_receipt.json",
    REPO / "6-Documentation" / "docs" / "specs" / "FORWARD_FOUNDATION_EQUATION_COMPILER.md",
    REPO / "6-Documentation" / "docs" / "specs" / "GCCL_ENCODING_CONTRACT.md",
    REPO / "6-Documentation" / "docs" / "specs" / "GENSIS_COMPILER_SPEC.md",
    REPO / "6-Documentation" / "docs" / "specs" / "PROJECTABLE_GEOMETRY_COMPRESSOR_SPEC.md",
    REPO / "6-Documentation" / "articles" / "meme-math-that-pays-rent" / "article.md",
    REPO / "0-Core-Formalism" / "otom" / "tools" / "lean" / "Semantics" / "Semantics" / "LochMonsterFilter.lean",
    REPO / "shared-data" / "data" / "bibliographic_event_horizon" / "bibliographic_event_horizon_receipt.json",
    REPO / "shared-data" / "data" / "asymptotic_closure_horizon" / "asymptotic_closure_horizon_receipt.json",
]

EXTERNAL_CITATIONS = [
    {
        "id": "immaterialscience_bibliographic_event_horizon",
        "title": "The Bibliographic Event Horizon: A Study on the Gravitational Pull of [1]",
        "url": "https://www.immaterialscience.org/2026/citations",
        "role": "bibliographic_shadow_prompt",
        "status": "satirical_source_used_as_real_diagnostic_prompt",
    },
    {
        "id": "reddit_bibliographic_event_horizon_discussion",
        "title": "Reddit discussion wrapper for bibliographic event horizon prompt",
        "url": "https://www.reddit.com/r/ImmaterialScience/comments/1t7plf9/the_bibliographic_event_horizon_a_study_on_the/",
        "role": "discussion_pointer",
        "status": "metadata_only",
    },
    {
        "id": "charmm_mmff_docs",
        "title": "CHARMM MMFF documentation",
        "url": "https://www.charmm-gui.org/charmmdoc/mmff.html",
        "role": "molecular_shadow_reference",
        "status": "external_reference",
    },
    {
        "id": "openbabel_mmff94_docs",
        "title": "Open Babel MMFF94 force field documentation",
        "url": "https://openbabel.org/docs/Forcefields/mmff94.html",
        "role": "molecular_shadow_reference",
        "status": "external_reference",
    },
    {
        "id": "rdkit_mmff_implementation_paper",
        "title": "MMFF implementation validation reference in RDKit ecosystem",
        "url": "https://link.springer.com/article/10.1186/s13321-014-0037-3",
        "role": "implementation_reference",
        "status": "external_reference",
    },
    {
        "id": "user_supplied_asymptote_meme",
        "title": "Asymptote meme source prompt",
        "role": "asymptotic_shadow_prompt",
        "status": "user_supplied_image_prompt",
    },
]

TREE_FIDDY_CAGE_BOUNDARY_BYTES = 350


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


def shadow_route(
    *,
    rank: int,
    route_id: str,
    domain: str,
    visible_shadow: str,
    hidden_state: str,
    chain: list[str],
    residual_handles: list[str],
    reusable_kernels: list[str],
    fixture_targets: list[str],
    hold_surfaces: list[str],
    next_probe: str,
    estimated_yield: str,
    decision: str = "SHADOW_ROUTE_READY",
    archive_mode: str = "TREE_FIDDY_CANDIDATE",
) -> dict[str, Any]:
    item = {
        "rank": rank,
        "route_id": route_id,
        "domain": domain,
        "visible_shadow": visible_shadow,
        "hidden_state": hidden_state,
        "refined_shadow_chain": chain,
        "accumulator": {
            "kind": "O-AMMR",
            "meaning": "ordered algebraic Merkle mountain range over typed projection nodes",
            "plain_merkle_role": "content hash field only; not the whole trust object",
        },
        "representative_carrier": {
            "shape": "16D signed envelope -> 12D source/residual plane -> 4D primitive keel -> genus-3 residual boat -> 0D closure",
            "closure_budget_twelfths": {
                "visible_4d": 4,
                "shadow_3d": 3,
                "closure_0d": 1,
                "lawbound": 4,
                "unresolved": 0,
                "total": 12,
            },
            "residual_handles": residual_handles,
        },
        "tree_fiddy_guard": {
            "cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "archive_mode": archive_mode,
            "archive_rule": "if committed_or_shielded then Q_active(i)=0",
            "promotion_rule": "archive route only when control+receipt+residual budget is bounded by cage boundary",
            "failure_lane": "HOLD_ACTIVE_SHADOW_ROUTE",
        },
        "reusable_kernels": reusable_kernels,
        "fixture_targets": fixture_targets,
        "hold_surfaces": hold_surfaces,
        "next_probe": next_probe,
        "estimated_yield": estimated_yield,
        "decision": decision,
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def build_map() -> dict[str, Any]:
    default_chain = [
        "L16_signed_envelope",
        "L12_source_residual_plane",
        "L4_primitive_keel",
        "Rg3_residual_boat",
        "L3_or_L2_visible_shadow",
        "L0_closure",
        "O_AMMR_root",
    ]
    default_handles = ["packet_local", "shear_torsion", "spectral_field"]
    routes = [
        shadow_route(
            rank=1,
            route_id="molecular_mmff_rigid_bodies",
            domain="molecular mechanics and MMFF-style geometry",
            visible_shadow="3D atom coordinates and local fragment poses",
            hidden_state="typed chemistry body state: atom identity, topology, aromaticity, charge, force-field slots, residual strain",
            chain=[
                "L16_body_state",
                "L12_chemistry_residual_plane",
                "L8_mmff_adapter_state",
                "L4_geometry_primitive",
                "Rg3_strain_residual_boat",
                "L3_coordinate_shadow",
                "L0_replay_closure",
                "O_AMMR_root",
            ],
            residual_handles=["coordinate_packet", "torsion_shear", "forcefield_spectral_slot"],
            reusable_kernels=["RIGID_BODY_POSE", "HINGED_RIGID_BODY", "TORSION_OPCODE", "MN_BOND_DEVIATION"],
            fixture_targets=["ring templates", "rotor groups", "rigid triads", "fragment pose replay"],
            hold_surfaces=["atom typing", "aromaticity", "parameter tables", "charges", "nonbonded interactions", "energy minimization"],
            next_probe="mmff_rigid_body_geometry_probe.py",
            estimated_yield="very_high",
        ),
        shadow_route(
            rank=2,
            route_id="protein_secondary_structure",
            domain="protein geometry and folding surfaces",
            visible_shadow="backbone coordinates, alpha helices, beta sheets, contact maps",
            hidden_state="sequence, residue chemistry, torsion state, hydrogen-bond graph, solvent/exposure lanes",
            chain=default_chain,
            residual_handles=default_handles,
            reusable_kernels=["RIGID_BODY_POSE", "HINGED_CHAIN", "CONTACT_MAP_SHADOW", "TORSION_OPCODE"],
            fixture_targets=["ideal helix template", "beta-strand template", "Ramachandran torsion bins", "contact-map replay"],
            hold_surfaces=["force field validity", "solvent model", "folding dynamics", "experimental structure uncertainty"],
            next_probe="protein_shadow_geometry_probe.py",
            estimated_yield="high",
        ),
        shadow_route(
            rank=3,
            route_id="crystal_lattice_basis",
            domain="crystallography and solid-state structures",
            visible_shadow="unit-cell coordinates and lattice basis",
            hidden_state="space group, motif, Wyckoff positions, occupancy, defects, temperature factors",
            chain=[
                "L16_material_state",
                "L12_symmetry_residual_plane",
                "L8_symmetry_adapter",
                "L4_lattice_primitive",
                "Rg3_defect_residual_boat",
                "L3_unit_cell_shadow",
                "L0_orbit_closure",
                "O_AMMR_root",
            ],
            residual_handles=["motif_packet", "symmetry_shear", "defect_spectral_field"],
            reusable_kernels=["LATTICE_BASIS", "SYMMETRY_ORBIT", "MOTIF_REPLAY", "DEFECT_RESIDUAL"],
            fixture_targets=["NaCl cell", "graphite/diamond motif", "space-group orbit expansion", "defect residual lane"],
            hold_surfaces=["disorder", "partial occupancy", "thermal ellipsoids", "DFT/experimental provenance"],
            next_probe="crystal_lattice_shadow_probe.py",
            estimated_yield="very_high",
        ),
        shadow_route(
            rank=4,
            route_id="cad_mechanical_assemblies",
            domain="CAD and mechanical assemblies",
            visible_shadow="3D part mesh, pose graph, constraints",
            hidden_state="parametric sketch, joints, tolerances, material, manufacturing operations, load paths",
            chain=[
                "L16_design_intent",
                "L12_feature_residual_plane",
                "L8_feature_adapter",
                "L4_joint_primitive",
                "Rg3_tolerance_residual_boat",
                "L3_mesh_shadow",
                "L0_assembly_closure",
                "O_AMMR_root",
            ],
            residual_handles=["feature_packet", "joint_shear_torsion", "loadpath_spectral_field"],
            reusable_kernels=["RIGID_BODY_POSE", "JOINT_CONSTRAINT", "SYMMETRY_REPEAT", "MESH_RESIDUAL"],
            fixture_targets=["bolted plate", "hinge assembly", "patterned holes", "extrude/revolve replay"],
            hold_surfaces=["FEA validity", "manufacturing tolerance", "contact/friction", "load certification"],
            next_probe="cad_assembly_shadow_probe.py",
            estimated_yield="high",
        ),
        shadow_route(
            rank=5,
            route_id="seismic_interior_witness",
            domain="geophysics and inaccessible interiors",
            visible_shadow="boundary wave arrivals, travel-time residuals, mode signatures",
            hidden_state="opaque interior material state, phase regions, anisotropy, temperature/pressure lanes",
            chain=[
                "L16_interior_state",
                "L12_wave_residual_plane",
                "L8_wave_adapter",
                "L4_boundary_witness",
                "Rg3_tomography_residual_boat",
                "L1_time_series_shadow",
                "L0_witness_closure",
                "O_AMMR_root",
            ],
            residual_handles=["arrival_packet", "anisotropy_shear", "attenuation_spectral_field"],
            reusable_kernels=["BOUNDARY_WITNESS", "MN_IMPEDANCE_CONTRAST", "RESIDUAL_TOMOGRAPHY", "UNDERVERSE_LANE"],
            fixture_targets=["two-layer travel-time fixture", "S-wave missing lane", "impedance reflection", "tomography residual"],
            hold_surfaces=["unique interior decode", "material phase overclaim", "measurement noise", "model nonuniqueness"],
            next_probe="seismic_shadow_witness_probe.py",
            estimated_yield="medium_high",
        ),
        shadow_route(
            rank=6,
            route_id="medical_imaging_anatomy",
            domain="medical imaging geometry",
            visible_shadow="2D/3D scan slices, segmentation masks, landmark coordinates",
            hidden_state="anatomy state, tissue class, acquisition protocol, orientation, uncertainty, diagnosis boundary",
            chain=default_chain,
            residual_handles=default_handles,
            reusable_kernels=["SLICE_STACK", "SEGMENTATION_MASK", "RIGID_REGISTRATION", "RESIDUAL_UNCERTAINTY"],
            fixture_targets=["phantom object slices", "rigid registration", "mask run-length replay", "landmark pose replay"],
            hold_surfaces=["diagnosis", "clinical validity", "scanner artifacts", "privacy/provenance"],
            next_probe="medical_image_shadow_probe.py",
            estimated_yield="medium_high",
            decision="SHADOW_ROUTE_HOLD_FIRST",
            archive_mode="TREE_FIDDY_BLOCKED_CLINICAL_HOLD",
        ),
        shadow_route(
            rank=7,
            route_id="language_parse_semantics",
            domain="language syntax and semantic compression",
            visible_shadow="token stream, parse tree, formatted text",
            hidden_state="syntax, entity graph, discourse state, source provenance, ambiguity lanes",
            chain=[
                "L16_discourse_state",
                "L12_text_residual_plane",
                "L8_semantic_adapter",
                "L4_parse_primitive",
                "Rg3_ambiguity_residual_boat",
                "L1_token_shadow",
                "L0_byte_replay_closure",
                "O_AMMR_root",
            ],
            residual_handles=["token_packet", "syntax_shear", "semantic_spectral_field"],
            reusable_kernels=["GRAMMAR_TEMPLATE", "ENTITY_REFERENCE", "MORPHOLOGY_OPCODE", "RESIDUAL_TEXT"],
            fixture_targets=["inflection tables", "template-heavy wiki text", "citation template parse", "entity-link replay"],
            hold_surfaces=["meaning equivalence", "translation claims", "ambiguous grammar", "human intent"],
            next_probe="language_shadow_parse_probe.py",
            estimated_yield="high",
        ),
        shadow_route(
            rank=8,
            route_id="bibliographic_event_horizon",
            domain="bibliography and citation-provenance graphs",
            visible_shadow="citation number, bibliography entry, theorem/source label",
            hidden_state="source graph, dependency graph, claim fanout, quote coverage, receipt thrust, residual obligations",
            chain=[
                "L16_source_ecology",
                "L12_claim_dependency_residual_plane",
                "L8_bibliography_adapter",
                "L4_citation_gravity_primitive",
                "Rg3_obligation_residual_boat",
                "L1_reference_label_shadow",
                "L0_forward_receipt_closure",
                "O_AMMR_root",
            ],
            residual_handles=["quote_packet", "dependency_shear", "claim_spectral_field"],
            reusable_kernels=["CITATION_GRAVITY", "FORWARD_RECEIPT_THRUST", "DEPENDENCY_O_AMMR", "HOLD_LABEL_AUTHORITY"],
            fixture_targets=["over-cited root label", "forward-receipted source", "small source-hash note"],
            hold_surfaces=["citation label as proof", "prestige authority", "unquoted dependency", "unclosed theorem chain"],
            next_probe="bibliographic_event_horizon_probe.py",
            estimated_yield="high",
        ),
        shadow_route(
            rank=9,
            route_id="asymptotic_closure_horizon",
            domain="limit arguments, near-proofs, near-compression, and near-authority routes",
            visible_shadow="approach curve, limit statement, near-zero delta, near-complete proof label",
            hidden_state="finite gate state: replay, residual, receipt, byte law, and closure witness",
            chain=[
                "L16_limit_claim_state",
                "L12_finite_gate_residual_plane",
                "L8_limit_adapter",
                "L4_approach_primitive",
                "Rg3_missing_witness_residual_boat",
                "L1_asymptote_shadow",
                "L0_finite_intersection_closure",
                "O_AMMR_root",
            ],
            residual_handles=["approach_packet", "gate_shear", "missing_witness_spectral_field"],
            reusable_kernels=["FINITE_INTERSECTION_GATE", "ASYMPTOTIC_HOLD", "TREE_FIDDY_ARCHIVE_DIAGNOSTIC"],
            fixture_targets=["citation gravity near-authority", "global-delta near-zero compression", "finite coordinate replay", "proof label dependency chain"],
            hold_surfaces=["limit language as proof", "approaches-zero as byte law", "eventual closure without witness", "infinite citation chain"],
            next_probe="asymptotic_closure_horizon_probe.py",
            estimated_yield="high",
        ),
        shadow_route(
            rank=10,
            route_id="proof_equation_derivations",
            domain="proof objects and equation derivation chains",
            visible_shadow="rendered theorem/equation statement",
            hidden_state="foundation kernel, dependencies, transform rules, residual obligations, closure gates",
            chain=[
                "L16_foundation_state",
                "L12_dependency_residual_plane",
                "L8_dependency_adapter",
                "L4_transform_primitive",
                "Rg3_obligation_residual_boat",
                "L2_statement_shadow",
                "L0_closure_witness",
                "O_AMMR_root",
            ],
            residual_handles=["equation_packet", "dependency_shear", "proof_spectral_field"],
            reusable_kernels=["FORWARD_DERIVATION", "DEPENDENCY_MERKLE", "CLOSURE_WITNESS", "HOLD_RESIDUAL"],
            fixture_targets=["foundation equation atom", "dependency hash replay", "PASS-ADD-PAUSE-SUBTRACT event chain"],
            hold_surfaces=["human theorem label", "citation trust", "unclosed residual", "semantic overclaim"],
            next_probe="proof_shadow_derivation_probe.py",
            estimated_yield="high",
        ),
        shadow_route(
            rank=11,
            route_id="pde_field_snapshots",
            domain="PDE fields and simulation state",
            visible_shadow="mesh/grid samples and time slices",
            hidden_state="governing equation, boundary conditions, units, solver, mesh, timestep, residual norm",
            chain=default_chain,
            residual_handles=default_handles,
            reusable_kernels=["BOUNDARY_CONDITION", "STENCIL_OPCODE", "MODE_BASIS", "RESIDUAL_NORM"],
            fixture_targets=["heat equation stencil", "wave mode packet", "boundary-condition replay", "coarse-grid residual"],
            hold_surfaces=["solver correctness", "stability", "physical validity", "mesh convergence"],
            next_probe="pde_field_shadow_probe.py",
            estimated_yield="medium",
        ),
        shadow_route(
            rank=12,
            route_id="genomic_chromatin_projection",
            domain="genomics and chromatin/projection surfaces",
            visible_shadow="sequence string, contact map, 3D chromatin trace",
            hidden_state="regulatory state, epigenetic marks, cell type, assay protocol, uncertainty, causal boundary",
            chain=default_chain,
            residual_handles=default_handles,
            reusable_kernels=["SEQUENCE_TEMPLATE", "CONTACT_MAP_SHADOW", "MARK_RUN", "ASSAY_RESIDUAL"],
            fixture_targets=["repeat sequence run", "motif replay", "contact-map block", "mark interval encoding"],
            hold_surfaces=["causality", "cell-state generalization", "batch effects", "clinical/biological overclaim"],
            next_probe="genomic_shadow_projection_probe.py",
            estimated_yield="medium",
            decision="SHADOW_ROUTE_HOLD_FIRST",
            archive_mode="TREE_FIDDY_BLOCKED_CAUSAL_HOLD",
        ),
    ]
    return {
        "schema": "shadow_layer_opportunity_map_v1",
        "citations": {
            "local_source_refs": [rel(path) for path in SOURCE_REFS],
            "external_citations": EXTERNAL_CITATIONS,
        },
        "canonical_statement": (
            "Shadow layers are useful where the visible object is a cheap projection "
            "of a richer typed state. The low-dimensional shadow may be encoded, but "
            "the hidden state, adapter, residual, closure policy, and O-AMMR route "
            "must be receipted. Plain Merkle hashes are only content commitments."
        ),
        "selection_rule": (
            "Promote replayable shadows first. Keep semantics, physical validity, diagnosis, "
            "causality, and theorem trust in HOLD until local closure receipts exist."
        ),
        "refinement_rule": {
            "avoid": "pure Merkle tree as trust object",
            "use": "O-AMMR plus typed representative carrier",
            "carrier_law": "source_12D = lift(project(source_12D)) + residual_12D",
            "residual_law": "packet_local + shear_torsion + spectral_field = residual_12D",
            "promotion_requires": [
                "axis counts match",
                "three residual handles close",
                "unresolved shell mass is zero",
                "visible shadow replays exactly",
                "source and receipt hashes are present",
            ],
        },
        "tree_fiddy_rule": {
            "meaning": "bounded archive and safety cage for shadow routes",
            "cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "active_pull_rule": "Q_active(i)=0 if i is committed or shielded",
            "assignment": "BHOCS/archive commit routes are Tree Fiddy owned; live recurrence remains outside the cage",
            "shadow_use": (
                "A shadow route may be archived only after replay, residual, and receipt "
                "costs fit within the cage. Otherwise it stays HOLD_ACTIVE_SHADOW_ROUTE."
            ),
        },
        "claim_boundary": (
            "Planning receipt only. This map ranks likely shadow-layer encoding surfaces; "
            "it does not assert compression gains, physical truth, clinical validity, or proof validity."
        ),
        "routes": routes,
        "route_count": len(routes),
        "status_counts": {
            status: sum(1 for item in routes if item["decision"] == status)
            for status in sorted({item["decision"] for item in routes})
        },
    }


def build_receipt(route_map: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "shadow_layer_opportunity_map_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "map": rel(MAP),
        "map_hash": hash_obj(route_map),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "external_citations": route_map["citations"]["external_citations"],
        "route_count": route_map["route_count"],
        "status_counts": route_map["status_counts"],
        "decision": "ADMIT_SHADOW_ROUTE_MAP_HOLD_FIRST",
        "claim_boundary": route_map["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(route_map: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Shadow Layer Opportunity Map",
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
        "## Refinement Rule",
        "",
        f"- Avoid: `{route_map['refinement_rule']['avoid']}`",
        f"- Use: `{route_map['refinement_rule']['use']}`",
        f"- Carrier law: `{route_map['refinement_rule']['carrier_law']}`",
        f"- Residual law: `{route_map['refinement_rule']['residual_law']}`",
        "",
        "## Tree Fiddy Guard",
        "",
        f"- Cage boundary bytes: `{route_map['tree_fiddy_rule']['cage_boundary_bytes']}`",
        f"- Active pull rule: `{route_map['tree_fiddy_rule']['active_pull_rule']}`",
        f"- Assignment: {route_map['tree_fiddy_rule']['assignment']}",
        f"- Shadow use: {route_map['tree_fiddy_rule']['shadow_use']}",
        "",
        "## Ranked Routes",
        "",
        "| Rank | Route | Domain | Visible shadow | Yield | Decision | Next probe |",
        "|---:|---|---|---|---|---|---|",
    ]
    for item in route_map["routes"]:
        lines.append(
            f"| {item['rank']} | `{item['route_id']}` | {item['domain']} | "
            f"{item['visible_shadow']} | {item['estimated_yield']} | `{item['decision']}` | `{item['next_probe']}` |"
        )
    lines.extend(["", "## Rule", "", route_map["selection_rule"]])
    lines.extend(["", "## Citations", ""])
    lines.append("Local source refs:")
    for source in receipt["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    lines.append("")
    lines.append("External/source prompts:")
    for citation in route_map["citations"]["external_citations"]:
        target = citation.get("url") or citation["status"]
        lines.append(f"- `{citation['id']}`: {citation['title']} ({target}); role: `{citation['role']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    route_map = build_map()
    receipt = build_receipt(route_map)
    MAP.write_text(json.dumps(route_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(route_map, receipt)
    print(
        json.dumps(
            {
                "map": rel(MAP),
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
