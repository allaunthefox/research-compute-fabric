#!/usr/bin/env python3
"""Merkle-attested tensegrity load-equation generator for a synthetic print lattice.

This is a mechanical/attestation test harness, not a slicer and not a safety
certifier.  The key separation is:

* mechanics: solve an equilibrium residual over geometry, loads, edge force
  densities, and support reactions;
* print command: map force magnitudes into bounded density commands with a
  sigmoid;
* attestation: commit the records into a Merkle root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "4-Infrastructure" / "shim" / "merkle_tensegrity_load_equation_receipt.json"
CURRICULUM = REPO / "4-Infrastructure" / "shim" / "merkle_tensegrity_load_equation_curriculum.jsonl"


@dataclass(frozen=True)
class Lattice:
    nodes: np.ndarray
    edges: list[tuple[int, int]]
    supports: list[int]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cube_lattice(*, include_face_diagonals: bool) -> Lattice:
    nodes = np.array([[x, y, z] for x in [0.0, 1.0] for y in [0.0, 1.0] for z in [0.0, 1.0]], dtype=float)
    edges: list[tuple[int, int]] = []
    for i, xi in enumerate(nodes):
        for j, xj in enumerate(nodes):
            if j <= i:
                continue
            length = np.linalg.norm(xi - xj)
            if np.isclose(length, 1.0) or (include_face_diagonals and np.isclose(length, 2 ** 0.5)):
                edges.append((i, j))
    supports = [i for i, node in enumerate(nodes) if np.isclose(node[2], 0.0)]
    return Lattice(nodes=nodes, edges=edges, supports=supports)


def generate_load_profile(
    num_nodes: int,
    *,
    rng: np.random.Generator,
    gravity: float = -9.81,
    mass_per_node: float = 0.1,
    lateral_noise_sigma: float = 0.05,
) -> np.ndarray:
    loads = np.zeros((num_nodes, 3), dtype=float)
    loads[:, 0] = rng.normal(0.0, lateral_noise_sigma, size=num_nodes)
    loads[:, 1] = rng.normal(0.0, lateral_noise_sigma, size=num_nodes)
    loads[:, 2] = mass_per_node * gravity
    return loads


def equilibrium_matrix(nodes: np.ndarray, edges: list[tuple[int, int]]) -> np.ndarray:
    """Return B where B @ q gives nodal force from signed edge force densities."""
    n = len(nodes)
    b = np.zeros((3 * n, len(edges)), dtype=float)
    for col, (i, j) in enumerate(edges):
        direction_i = nodes[i] - nodes[j]
        direction_j = nodes[j] - nodes[i]
        b[3 * i : 3 * i + 3, col] = direction_i
        b[3 * j : 3 * j + 3, col] = direction_j
    return b


def support_reaction_matrix(num_nodes: int, supports: list[int]) -> np.ndarray:
    """Three reaction components per support node."""
    r = np.zeros((3 * num_nodes, 3 * len(supports)), dtype=float)
    for support_index, node_index in enumerate(supports):
        for axis in range(3):
            r[3 * node_index + axis, 3 * support_index + axis] = 1.0
    return r


def solve_equilibrium(lattice: Lattice, loads: np.ndarray) -> dict[str, Any]:
    b_edge = equilibrium_matrix(lattice.nodes, lattice.edges)
    b_support = support_reaction_matrix(len(lattice.nodes), lattice.supports)
    a_aug = np.concatenate([b_edge, b_support], axis=1)
    rhs = -loads.reshape(-1)
    solution, *_ = np.linalg.lstsq(a_aug, rhs, rcond=None)
    q_signed = solution[: len(lattice.edges)]
    support_reactions = solution[len(lattice.edges) :]
    residual = a_aug @ solution + loads.reshape(-1)
    return {
        "equilibrium_matrix": b_edge,
        "support_matrix": b_support,
        "augmented_matrix": a_aug,
        "q_signed": q_signed,
        "support_reactions": support_reactions.reshape((len(lattice.supports), 3)),
        "residual": residual.reshape(loads.shape),
    }


def shielded_density(q_signed: np.ndarray, *, duality_coefficient: float, density_midpoint: float) -> np.ndarray:
    """Map signed force density magnitude to a bounded [0,1] print-density command."""
    q_abs = np.abs(q_signed)
    x = duality_coefficient * (q_abs - density_midpoint)
    return 1.0 / (1.0 + np.exp(-x))


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return sha256_text("")
    level = leaves[:]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            sha256_text(level[i] + level[i + 1])
            for i in range(0, len(level), 2)
        ]
    return level[0]


def rounded_list(array: np.ndarray, decimals: int = 8) -> Any:
    return np.round(array.astype(float), decimals).tolist()


def build_leaf_records(
    lattice: Lattice,
    loads: np.ndarray,
    q_signed: np.ndarray,
    density: np.ndarray,
    support_reactions: np.ndarray,
    residual: np.ndarray,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for i, node in enumerate(lattice.nodes):
        records.append({
            "record_type": "node_load",
            "node_id": i,
            "position": rounded_list(node),
            "external_load": rounded_list(loads[i]),
            "equilibrium_residual": rounded_list(residual[i]),
        })
    for edge_id, (i, j) in enumerate(lattice.edges):
        records.append({
            "record_type": "edge_force_density",
            "edge_id": edge_id,
            "nodes": [i, j],
            "vector_i_minus_j": rounded_list(lattice.nodes[i] - lattice.nodes[j]),
            "q_signed": round(float(q_signed[edge_id]), 10),
            "print_density_0_1": round(float(density[edge_id]), 10),
        })
    for support_row, node_id in enumerate(lattice.supports):
        records.append({
            "record_type": "support_reaction",
            "node_id": node_id,
            "reaction": rounded_list(support_reactions[support_row]),
        })
    return records


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    lattice = cube_lattice(include_face_diagonals=args.include_face_diagonals)
    rng = np.random.default_rng(args.seed)
    loads = generate_load_profile(
        len(lattice.nodes),
        rng=rng,
        gravity=args.gravity,
        mass_per_node=args.mass_per_node,
        lateral_noise_sigma=args.lateral_noise_sigma,
    )
    solved = solve_equilibrium(lattice, loads)
    q_signed = solved["q_signed"]
    density = shielded_density(
        q_signed,
        duality_coefficient=args.duality_coefficient,
        density_midpoint=args.density_midpoint,
    )
    residual = solved["residual"]
    residual_norm = float(np.linalg.norm(residual))
    acceptable = residual_norm <= args.epsilon_mech
    leaf_records = build_leaf_records(
        lattice,
        loads,
        q_signed,
        density,
        solved["support_reactions"],
        residual,
    )
    leaf_hashes = [sha256_text(stable_json(record)) for record in leaf_records]
    receipt: dict[str, Any] = {
        "schema": "merkle_tensegrity_load_equation_receipt_v1",
        "claim_boundary": (
            "This harness tests equilibrium residuals and Merkle commitments for a "
            "synthetic cube lattice. It is not a structural safety certificate, "
            "not a slicer, and not proof that sigmoid density commands are printable "
            "or mechanically sufficient."
        ),
        "source_priors": {
            "merkle_attested_3d_printing_note": "docs/merkle_tree_3d_printing_zcash_load_distribution.md",
            "invariant_dual_mechanics": {
                "title": "Invariant dual mechanics of tensegrity and origami",
                "doi": "10.1073/pnas.2519138123",
                "local_supporting_materials": "Invariant Dual Mechanics Supporting Materials",
            },
        },
        "parameters": {
            "seed": args.seed,
            "gravity": args.gravity,
            "mass_per_node": args.mass_per_node,
            "lateral_noise_sigma": args.lateral_noise_sigma,
            "duality_coefficient": args.duality_coefficient,
            "density_midpoint": args.density_midpoint,
            "epsilon_mech": args.epsilon_mech,
            "include_face_diagonals": args.include_face_diagonals,
        },
        "equations": {
            "node_equilibrium": "sum_{j in adj(i)} q_ij * (x_i - x_j) + p_i + r_i = 0",
            "matrix_equilibrium": "[B_edges B_support] * [q r]^T = -p",
            "least_squares_solution": "argmin_{q,r} ||[B_edges B_support][q r]^T + p||_2",
            "shielded_density": "rho_e = 1 / (1 + exp(-alpha * (abs(q_e) - q_mid)))",
            "mechanical_acceptance": "||R_mech||_2 <= epsilon_mech",
            "leaf_commitment": "leaf_i = H(stable_json(record_i))",
            "merkle_root": "MerkleRoot(leaf_1, ..., leaf_N)",
        },
        "lattice": {
            "node_count": len(lattice.nodes),
            "edge_count": len(lattice.edges),
            "support_count": len(lattice.supports),
            "nodes": rounded_list(lattice.nodes),
            "edges": lattice.edges,
            "supports": lattice.supports,
        },
        "results": {
            "load_vectors": rounded_list(loads),
            "q_signed": rounded_list(q_signed),
            "print_density_0_1": rounded_list(density),
            "support_reactions": rounded_list(solved["support_reactions"]),
            "residual_vectors": rounded_list(residual),
            "residual_norm_l2": residual_norm,
            "mechanically_acceptable": acceptable,
            "total_abs_edge_force_density": float(np.sum(np.abs(q_signed))),
            "density_min": float(np.min(density)),
            "density_max": float(np.max(density)),
        },
        "merkle": {
            "leaf_count": len(leaf_records),
            "leaf_hashes": leaf_hashes,
            "root": merkle_root(leaf_hashes),
        },
        "failure_rules": [
            "Merkle root treated as mechanical proof -> invalid",
            "sigmoid density treated as solved equilibrium -> invalid",
            "unbraced lattice cannot carry lateral loads -> invalid residual or add diagonals",
            "unsupported free-body gravity case without support reactions -> invalid residual",
            "residual_norm_l2 > epsilon_mech -> replan or repair",
            "density command used on real printer without slicer/material calibration -> unsafe",
        ],
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum() -> None:
    rows = [
        {
            "task": "separate_mechanics_from_attestation",
            "input": "load vectors, force densities, density commands, Merkle root",
            "target": "mechanical residual first; Merkle commits to records only",
        },
        {
            "task": "solve_supported_lattice_equilibrium",
            "input": "nodes, edges, support nodes, external loads",
            "target": "signed edge force densities, support reactions, residual norm",
        },
        {
            "task": "reject_hidden_print_risk",
            "input": "bounded sigmoid density command",
            "target": "heuristic print-density command requiring slicer/material calibration",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2519138123)
    parser.add_argument("--gravity", type=float, default=-9.81)
    parser.add_argument("--mass-per-node", type=float, default=0.1)
    parser.add_argument("--lateral-noise-sigma", type=float, default=0.05)
    parser.add_argument("--duality-coefficient", type=float, default=2 ** 0.5)
    parser.add_argument("--density-midpoint", type=float, default=0.25)
    parser.add_argument("--epsilon-mech", type=float, default=1e-8)
    parser.add_argument("--no-face-diagonals", action="store_false", dest="include_face_diagonals")
    parser.set_defaults(include_face_diagonals=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    receipt = build_receipt(args)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum()
    print(json.dumps({
        "receipt": str(OUT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "merkle_root": receipt["merkle"]["root"],
        "node_count": receipt["lattice"]["node_count"],
        "edge_count": receipt["lattice"]["edge_count"],
        "residual_norm_l2": receipt["results"]["residual_norm_l2"],
        "mechanically_acceptable": receipt["results"]["mechanically_acceptable"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
