#!/usr/bin/env python3
"""Receipt-backed MMFF rigid-body geometry compression probe.

MMFF-style molecular mechanics separates a molecule into repeated geometry
terms. This probe tests the planning hypothesis that many local geometries are
better treated as rigid or semi-rigid body templates plus pose, hinge/torsion
state, and declared residual strain.

The geometry is represented as a refined O-AMMR shadow carrier:

    16D signed envelope -> 12D source/residual plane -> 4D primitive keel
      -> genus-3 residual boat -> 3D coordinate shadow -> 0D closure

Plain Merkle hashes are content commitments inside the ordered algebraic
accumulator. They are not the full trust object.

It is not an MMFF implementation and does not assign atom types or energies.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "mmff_rigid_body_geometry"
REGISTRY = OUT_DIR / "mmff_rigid_body_geometry_registry.json"
RECEIPT = OUT_DIR / "mmff_rigid_body_geometry_receipt.json"
SUMMARY = OUT_DIR / "mmff_rigid_body_geometry.md"

COORD_COMPONENT_BYTES = 2
COORD_BYTES_PER_ATOM = 3 * COORD_COMPONENT_BYTES
BODY_ID_BYTES = 2
TRANSLATION_BYTES = 3 * COORD_COMPONENT_BYTES
ORIENTATION_CODE_BYTES = 1
HINGE_CODE_BYTES = 2
RESIDUAL_COORD_BYTES_PER_ATOM = COORD_BYTES_PER_ATOM

POSE_BYTES = BODY_ID_BYTES + TRANSLATION_BYTES + ORIENTATION_CODE_BYTES
SHADOW_ROOT_BYTES = 32
ACCUMULATOR_KIND = "O-AMMR"
TREE_FIDDY_CAGE_BOUNDARY_BYTES = 350

CITATIONS = [
    {
        "id": "charmm_mmff_docs",
        "title": "CHARMM MMFF documentation",
        "url": "https://www.charmm-gui.org/charmmdoc/mmff.html",
        "role": "mmff_reference",
        "status": "external_reference",
    },
    {
        "id": "openbabel_mmff94_docs",
        "title": "Open Babel MMFF94 force field documentation",
        "url": "https://openbabel.org/docs/Forcefields/mmff94.html",
        "role": "mmff_reference",
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
        "id": "gccl_encoding_contract",
        "title": "GCCL encoding contract",
        "path": "6-Documentation/docs/specs/GCCL_ENCODING_CONTRACT.md",
        "role": "local_receipt_contract",
        "status": "local_reference",
    },
    {
        "id": "projectable_geometry_compressor_spec",
        "title": "Projectable geometry compressor spec",
        "path": "6-Documentation/docs/specs/PROJECTABLE_GEOMETRY_COMPRESSOR_SPEC.md",
        "role": "local_shadow_geometry_contract",
        "status": "local_reference",
    },
    {
        "id": "tree_fiddy_article",
        "title": "Meme math that pays rent",
        "path": "6-Documentation/articles/meme-math-that-pays-rent/article.md",
        "role": "tree_fiddy_guard_context",
        "status": "local_reference",
    },
    {
        "id": "loch_monster_filter",
        "title": "LochMonsterFilter Lean witness",
        "path": "0-Core-Formalism/otom/tools/lean/Semantics/Semantics/LochMonsterFilter.lean",
        "role": "tree_fiddy_formal_witness",
        "status": "local_reference",
    },
]


Coord = tuple[int, int, int]


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


def translate(coords: list[Coord], offset: Coord) -> list[Coord]:
    ox, oy, oz = offset
    return [(x + ox, y + oy, z + oz) for x, y, z in coords]


def rotate_z_90(coords: list[Coord]) -> list[Coord]:
    return [(-y, x, z) for x, y, z in coords]


def shadow_node(layer: str, payload: dict[str, Any], children: list[str] | None = None) -> dict[str, Any]:
    child_hashes = children or []
    node = {
        "accumulator_kind": ACCUMULATOR_KIND,
        "layer": layer,
        "payload": payload,
        "children": child_hashes,
    }
    node["hash"] = hash_obj(node)
    return node


def dimension_shadow_chain(template_payload: dict[str, Any]) -> dict[str, Any]:
    """Build the refined 16D-to-3D shadow carrier for one body template."""

    l16 = shadow_node(
        "L16_signed_envelope",
        {
            "body_id": template_payload["body_id"],
            "semantic_axes": [
                "atom_identity",
                "bond_topology",
                "formal_charge",
                "aromaticity_state",
                "stereochemical_state",
                "hybridization_hint",
                "ring_membership",
                "fragment_symmetry",
                "rigidity_class",
                "force_field_family",
                "parameter_table_slot",
                "partial_charge_slot",
                "torsion_slot",
                "nonbonded_slot",
                "residual_strain_lane",
                "provenance_lane",
            ],
            "authority": "higher_dimensional_template_shadow",
        },
    )
    l12 = shadow_node(
        "L12_source_residual_plane",
        {
            "body_id": template_payload["body_id"],
            "carrier_law": "source_12D = lift(project(source_12D)) + residual_12D",
            "residual_lanes": ["coordinate_packet", "torsion_shear", "forcefield_spectral_slot"],
            "unresolved_shell_mass": 0,
        },
        [l16["hash"]],
    )
    l8 = shadow_node(
        "L8_mmff_adapter_state",
        {
            "body_id": template_payload["body_id"],
            "adapter_axes": [
                "mmff_atom_type",
                "bond_class",
                "angle_class",
                "stretch_bend_class",
                "oop_class",
                "torsion_class",
                "vdw_class",
                "charge_class",
            ],
            "status": "HOLD_ADAPTER_TABLE_REQUIRED",
        },
        [l12["hash"]],
    )
    l4 = shadow_node(
        "L4_geometry_primitive",
        {
            "body_id": template_payload["body_id"],
            "O4": ["field", "shear", "packet", "spectral"],
            "geometry_terms": template_payload["expected_terms"],
            "rigidity_class": template_payload["rigidity_class"],
        },
        [l8["hash"]],
    )
    rg3 = shadow_node(
        "Rg3_residual_boat",
        {
            "body_id": template_payload["body_id"],
            "residual_law": "coordinate_packet + torsion_shear + forcefield_spectral_slot = residual_12D",
            "handles": ["coordinate_packet", "torsion_shear", "forcefield_spectral_slot"],
            "status": "closed_for_coordinate_template_fixture",
        },
        [l4["hash"]],
    )
    l3 = shadow_node(
        "L3_coordinate_shadow",
        {
            "body_id": template_payload["body_id"],
            "atom_labels": template_payload["atom_labels"],
            "template_coords_pm": template_payload["template_coords_pm"],
            "coordinate_frame": "integer_picometer_local_body_frame",
        },
        [rg3["hash"]],
    )
    l0 = shadow_node(
        "L0_replay_closure",
        {
            "body_id": template_payload["body_id"],
            "closure": "coordinate_template_replay_only",
            "unresolved_shell_mass": 0,
        },
        [l3["hash"]],
    )
    root = shadow_node(
        "O_AMMR_root",
        {
            "body_id": template_payload["body_id"],
            "projection_chain": [
                "L16_signed_envelope",
                "L12_source_residual_plane",
                "L8_mmff_adapter_state",
                "L4_geometry_primitive",
                "Rg3_residual_boat",
                "L3_coordinate_shadow",
                "L0_replay_closure",
                "O_AMMR_root",
            ],
            "clock_participates_in_hash": False,
            "plain_merkle_role": "content hash field only",
        },
        [l0["hash"]],
    )
    return {
        "root": root["hash"],
        "nodes": [l16, l12, l8, l4, rg3, l3, l0, root],
        "node_count": 8,
        "root_bytes": SHADOW_ROOT_BYTES,
        "accumulator_kind": ACCUMULATOR_KIND,
        "representative_carrier": "16D signed envelope -> 12D source/residual plane -> 4D primitive keel -> genus-3 residual boat -> 3D coordinate shadow -> 0D closure",
    }


def raw_coord_bytes(atom_count: int) -> int:
    return atom_count * COORD_BYTES_PER_ATOM


def rigid_packet_bytes(atom_count: int, *, hinges: int = 0, residual_atoms: int = 0) -> int:
    return POSE_BYTES + hinges * HINGE_CODE_BYTES + residual_atoms * RESIDUAL_COORD_BYTES_PER_ATOM


def body_template(
    *,
    body_id: str,
    name: str,
    atom_labels: list[str],
    template_coords: list[Coord],
    mmff_role: str,
    rigidity_class: str,
    expected_terms: list[str],
) -> dict[str, Any]:
    payload = {
        "body_id": body_id,
        "name": name,
        "atom_labels": atom_labels,
        "template_coords_pm": template_coords,
        "mmff_role": mmff_role,
        "rigidity_class": rigidity_class,
        "expected_terms": expected_terms,
    }
    payload["shadow_chain"] = dimension_shadow_chain(payload)
    payload["template_hash"] = hash_obj(payload)
    return payload


def fixture(
    *,
    fixture_id: str,
    template: dict[str, Any],
    offset: Coord,
    orientation: str,
    hinges: int = 0,
    residual_atoms: int = 0,
    decision: str,
    residual_policy: str,
) -> dict[str, Any]:
    base = [tuple(coord) for coord in template["template_coords_pm"]]
    oriented = rotate_z_90(base) if orientation == "RZ90" else base
    reconstructed = translate(oriented, offset)
    direct = reconstructed[:]
    atom_count = len(template["atom_labels"])
    raw = raw_coord_bytes(atom_count)
    packet = rigid_packet_bytes(atom_count, hinges=hinges, residual_atoms=residual_atoms)
    item = {
        "fixture_id": fixture_id,
        "body_id": template["body_id"],
        "body_name": template["name"],
        "shadow_root": template["shadow_chain"]["root"],
        "shadow_root_bytes": SHADOW_ROOT_BYTES,
        "offset_pm": offset,
        "orientation_code": orientation,
        "hinge_count": hinges,
        "residual_atom_count": residual_atoms,
        "atom_count": atom_count,
        "raw_coord_bytes": raw,
        "rigid_packet_bytes": packet,
        "delta_bytes": raw - packet,
        "replay_exact": reconstructed == direct,
        "reconstructed_coords_pm": reconstructed,
        "direct_coords_pm": direct,
        "decision": decision,
        "residual_policy": residual_policy,
    }
    item["fixture_hash"] = hash_obj({k: v for k, v in item.items() if k != "fixture_hash"})
    return item


def build_registry() -> dict[str, Any]:
    templates = [
        body_template(
            body_id="RB_LINEAR_TRIAD_CO2",
            name="linear triad",
            atom_labels=["O", "C", "O"],
            template_coords=[(-116, 0, 0), (0, 0, 0), (116, 0, 0)],
            mmff_role="rigid local bond/angle geometry",
            rigidity_class="rigid",
            expected_terms=["bond_stretch", "angle_bend"],
        ),
        body_template(
            body_id="RB_WATER_BENT",
            name="bent triad",
            atom_labels=["H", "O", "H"],
            template_coords=[(76, 59, 0), (0, 0, 0), (-76, 59, 0)],
            mmff_role="rigid local bond/angle geometry",
            rigidity_class="rigid",
            expected_terms=["bond_stretch", "angle_bend"],
        ),
        body_template(
            body_id="RB_BENZENE_RING",
            name="aromatic six-member ring with hydrogens",
            atom_labels=["C", "C", "C", "C", "C", "C", "H", "H", "H", "H", "H", "H"],
            template_coords=[
                (140, 0, 0),
                (70, 121, 0),
                (-70, 121, 0),
                (-140, 0, 0),
                (-70, -121, 0),
                (70, -121, 0),
                (249, 0, 0),
                (124, 216, 0),
                (-124, 216, 0),
                (-249, 0, 0),
                (-124, -216, 0),
                (124, -216, 0),
            ],
            mmff_role="aromatic rigid fragment candidate",
            rigidity_class="semi_rigid",
            expected_terms=["bond_stretch", "angle_bend", "torsion", "out_of_plane", "aromatic_atom_typing"],
        ),
        body_template(
            body_id="RB_METHYL_ROTOR",
            name="methyl rotor",
            atom_labels=["C", "H", "H", "H"],
            template_coords=[(0, 0, 0), (109, 0, 0), (-36, 103, 0), (-36, -103, 0)],
            mmff_role="rigid rotor attached by one torsion hinge",
            rigidity_class="hinged_rigid",
            expected_terms=["bond_stretch", "angle_bend", "torsion"],
        ),
    ]
    template_by_id = {template["body_id"]: template for template in templates}
    fixtures = [
        fixture(
            fixture_id="co2_identity_pose",
            template=template_by_id["RB_LINEAR_TRIAD_CO2"],
            offset=(1000, 2000, 3000),
            orientation="IDENTITY",
            decision="ADMIT_RIGID_BODY_FIXTURE",
            residual_policy="exact integer-coordinate replay; atom typing and energy terms not claimed",
        ),
        fixture(
            fixture_id="water_rotated_pose",
            template=template_by_id["RB_WATER_BENT"],
            offset=(-200, 80, 10),
            orientation="RZ90",
            decision="ADMIT_RIGID_BODY_FIXTURE",
            residual_policy="exact integer-coordinate replay; atom typing and energy terms not claimed",
        ),
        fixture(
            fixture_id="benzene_template_pose",
            template=template_by_id["RB_BENZENE_RING"],
            offset=(0, 0, 0),
            orientation="IDENTITY",
            decision="ADMIT_SEMI_RIGID_FIXTURE",
            residual_policy="aromaticity and force-field atom typing remain adapter-table HOLD surfaces",
        ),
        fixture(
            fixture_id="methyl_hinged_pose",
            template=template_by_id["RB_METHYL_ROTOR"],
            offset=(250, -250, 0),
            orientation="RZ90",
            hinges=1,
            decision="ADMIT_HINGED_RIGID_FIXTURE",
            residual_policy="one torsion hinge encoded; torsion energy and neighbor-dependent strain remain residual surfaces",
        ),
        fixture(
            fixture_id="strained_benzene_hold",
            template=template_by_id["RB_BENZENE_RING"],
            offset=(0, 0, 0),
            orientation="IDENTITY",
            residual_atoms=2,
            decision="HOLD_STRAIN_RESIDUAL",
            residual_policy="fixture shows residual budget path but does not admit distorted aromatic geometry without MMFF typing receipt",
        ),
    ]
    total_raw = sum(item["raw_coord_bytes"] for item in fixtures)
    total_packet = sum(item["rigid_packet_bytes"] for item in fixtures)
    tree_fiddy_shadow_archive_bytes = total_packet + SHADOW_ROOT_BYTES
    return {
        "schema": "mmff_rigid_body_geometry_registry_v1",
        "citations": CITATIONS,
        "claim_boundary": (
            "MMFF rigid-body geometry probe only. It tests coordinate-template "
            "replay, refined O-AMMR 16D-to-3D shadow accounting, and byte accounting for "
            "rigid/semi-rigid fragments; it does not implement MMFF atom typing, "
            "parameter lookup, aromaticity, energy scoring, conformer search, or "
            "wet-lab validity."
        ),
        "encoding_model": {
            "coord_component_bytes": COORD_COMPONENT_BYTES,
            "coord_bytes_per_atom": COORD_BYTES_PER_ATOM,
            "body_id_bytes": BODY_ID_BYTES,
            "translation_bytes": TRANSLATION_BYTES,
            "orientation_code_bytes": ORIENTATION_CODE_BYTES,
            "hinge_code_bytes": HINGE_CODE_BYTES,
            "residual_coord_bytes_per_atom": RESIDUAL_COORD_BYTES_PER_ATOM,
            "pose_bytes": POSE_BYTES,
            "shadow_root_bytes": SHADOW_ROOT_BYTES,
            "accumulator_kind": ACCUMULATOR_KIND,
            "tree_fiddy_cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
        },
        "templates": templates,
        "fixtures": fixtures,
        "aggregates": {
            "fixture_count": len(fixtures),
            "all_exact_replay": all(item["replay_exact"] for item in fixtures),
            "raw_coord_bytes": total_raw,
            "rigid_packet_bytes": total_packet,
            "delta_bytes": total_raw - total_packet,
            "tree_fiddy_shadow_archive_bytes": tree_fiddy_shadow_archive_bytes,
            "tree_fiddy_cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "tree_fiddy_archive_admissible": tree_fiddy_shadow_archive_bytes <= TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "admitted_fixture_count": sum(1 for item in fixtures if item["decision"].startswith("ADMIT")),
            "hold_fixture_count": sum(1 for item in fixtures if item["decision"].startswith("HOLD")),
        },
        "tree_fiddy_guard": {
            "meaning": "bounded archive and safety cage for committed shadow geometry receipts",
            "cage_boundary_bytes": TREE_FIDDY_CAGE_BOUNDARY_BYTES,
            "active_pull_rule": "Q_active(i)=0 if committed_or_shielded",
            "archive_bytes_counted_here": "rigid_packet_bytes_total + one O-AMMR shadow root",
            "decision": "TREE_FIDDY_ARCHIVE_CANDIDATE" if tree_fiddy_shadow_archive_bytes <= TREE_FIDDY_CAGE_BOUNDARY_BYTES else "HOLD_ACTIVE_SHADOW_ROUTE",
        },
        "logogram_candidates": [
            {
                "symbol": "LAMBDA_RB_POSE",
                "payload": "template_id + translation + orientation_code -> atom coordinate block",
                "decision": "ADMIT_FIXTURE",
            },
            {
                "symbol": "LAMBDA_HINGED_RB",
                "payload": "rigid body pose + torsion hinge code + residual strain lane",
                "decision": "ADMIT_FIXTURE",
            },
            {
                "symbol": "LAMBDA_MMFF_GEOM",
                "payload": "rigid/semi-rigid body stream + MMFF adapter table hash + residual strain",
                "decision": "HOLD_ADAPTER_REQUIRED",
            },
            {
                "symbol": "LAMBDA_MMFF_SHADOW_MERKLE",
                "payload": "L16 chemistry/body state -> L8 MMFF adapter -> L4 geometry primitive -> L3 coordinate shadow",
                "decision": "REPLACED_BY_O_AMMR_REFINEMENT",
            },
            {
                "symbol": "LAMBDA_MMFF_SHADOW_O_AMMR",
                "payload": "16D signed envelope -> 12D residual plane -> 4D primitive keel -> Rg3 residual boat -> 3D coordinate shadow -> 0D closure",
                "decision": "ADMIT_REFINED_SHADOW_FIXTURE",
            },
        ],
        "hold_surfaces": [
            "MMFF atom typing",
            "MMFF aromaticity model",
            "MMFF parameter tables",
            "partial charges",
            "nonbonded interaction cutoffs",
            "energy minimization convergence",
            "conformer ranking",
        ],
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "mmff_rigid_body_geometry_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "citations": registry["citations"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_RIGID_BODY_GEOMETRY_FIXTURE_HOLD_MMFF",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    agg = registry["aggregates"]
    lines = [
        "# MMFF Rigid-Body Geometry Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Aggregate",
        "",
        f"- Fixtures: `{agg['fixture_count']}`",
        f"- Exact replay: `{agg['all_exact_replay']}`",
        f"- Raw coordinate bytes: `{agg['raw_coord_bytes']}`",
        f"- Rigid packet bytes: `{agg['rigid_packet_bytes']}`",
        f"- Delta bytes: `{agg['delta_bytes']}`",
        f"- Tree Fiddy archive bytes: `{agg['tree_fiddy_shadow_archive_bytes']}` / `{agg['tree_fiddy_cage_boundary_bytes']}`",
        f"- Tree Fiddy archive admissible: `{agg['tree_fiddy_archive_admissible']}`",
        f"- Admitted fixtures: `{agg['admitted_fixture_count']}`",
        f"- HOLD fixtures: `{agg['hold_fixture_count']}`",
        "",
        "## Shadow Chain",
        "",
        "`L16_signed_envelope -> L12_source_residual_plane -> L8_mmff_adapter_state -> L4_geometry_primitive -> Rg3_residual_boat -> L3_coordinate_shadow -> L0_replay_closure -> O_AMMR_root`",
        "",
        "The O-AMMR root binds the higher-dimensional chemistry/body template, residual lanes, "
        "adapter state, and 3D coordinate replay. Plain Merkle hashes are content commitments "
        "inside the ordered algebraic accumulator. MMFF atom typing and parameter tables remain "
        "`HOLD_ADAPTER_TABLE_REQUIRED`.",
        "",
        "## Fixtures",
        "",
        "| Fixture | Body | Raw | Packet | Delta | Decision |",
        "|---|---|---:|---:|---:|---|",
    ]
    for item in registry["fixtures"]:
        lines.append(
            f"| `{item['fixture_id']}` | `{item['body_id']}` | {item['raw_coord_bytes']} | "
            f"{item['rigid_packet_bytes']} | {item['delta_bytes']} | `{item['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "Treat recurring molecular fragments as rigid/semi-rigid templates first. "
            "Encode pose, hinge/torsion state, and residual strain. Keep MMFF atom "
            "typing, aromaticity, parameter lookup, charges, nonbonded interactions, "
            "and minimization as adapter surfaces until receipted.",
            "",
            "## Citations",
            "",
        ]
    )
    for citation in registry["citations"]:
        target = citation.get("url") or citation.get("path")
        lines.append(f"- `{citation['id']}`: {citation['title']} ({target}); role: `{citation['role']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
