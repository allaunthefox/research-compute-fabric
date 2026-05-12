#!/usr/bin/env python3
"""
Hypercube → Hyper-Rhomboid Composition: Stack Mapping
======================================================
Maps the hypercube/rhomboid calculus concept onto Research Stack primitives.
Key insight: shearing orthogonal tensor axes into a parallelotope is the
mathematical dual of PIST n-dimensional encoding, topological state transitions,
and Observer-Admissible Cavity manifestation.
"""

import json, time
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

HYPER_RHOMBOID = {
    "id": "hypercube-rhomboid-composition",
    "source": "User conceptual synthesis — hypercube matrix calculus → hyper-rhomboid",
    "title": "Hypercube → Hyper-Rhomboid Composition: Sheared Tensor Manifolds as Compression Geometry",
    "date": "2026-05-07",

    "core_claim": (
        "A hypercube of matrix calculus (n-D tensor of partial derivatives) assumes "
        "orthogonal axes — all variables independent. Composing hypercubes into a "
        "hyper-rhomboid (parallelotope) applies geometric shear: axes lean into each "
        "other, modeling entangled dimensions. This is the geometric engine behind "
        "topological compression, manifold mapping, and information-theoretic gravity."
    ),

    "geometric_primitives": {
        "hypercube": {
            "definition": "n-dimensional tensor grid with orthogonal (90°) axes",
            "mathematical_form": "T_{i,j,k,l} ∈ ℝ^{d₁×d₂×d₃×d₄}",
            "assumption": "All variables statistically independent (Cartesian)",
            "problem": "Empty geometric space between correlated variables — inefficient packing"
        },
        "hyper_rhomboid": {
            "definition": "Sheared parallelotope — axes at non-orthogonal angles",
            "mathematical_form": "S = A·T where A is a shear matrix (non-orthogonal basis)",
            "property": "Axes lean into correlated dimensions; volume preserved under shear",
            "gain": "Dense packing, entanglement modeling, manifold approximation"
        },
        "shear_matrix": {
            "definition": "Linear transform collapsing 90° angles to acute/oblique",
            "form": "A_{ij} = δ_{ij} + α_{ij} where α encodes correlation strength",
            "determinant": "det(A) = 1 (volume-preserving shear)"
        }
    },

    "stack_mappings": {
        "pist_nd_encoding": {
            "analogue": "PIST n-dimensional Cartesian → Bundle → Radial encoding",
            "mechanism": "Cartesian encode = orthogonal hypercube; Bundle encode = sheared rhomboid with fiber dimensions; Radial encode = fully collapsed angular coordinates",
            "file": "3-Mathematical-Models/pist_biological_polymorphic_shifter_v3_complete.py",
            "functions": ["pist_nd_cartesian_encode", "pist_nd_bundle_encode", "pist_nd_radial_encode"]
        },
        "topological_state_machine": {
            "analogue": "State transition = shear operation on state hypercube",
            "mechanism": "Each transition applies a shear matrix A_t to the state tensor S_t → S_{t+1} = A_t·S_t. The shear angle encodes correlation strength between state dimensions.",
            "file": "5-Applications/scripts/topological_state_machine.py"
        },
        "ndimensional_gene_hypothesis": {
            "analogue": "Gene expression = projection of sheared n-D rhomboid onto 3D observer frame",
            "mechanism": "The gene is an n-D rhomboid (entangled dimensions). The 3D molecular structure is a projection shadow. Epigenetic marks are shear-angle adjustments.",
            "file": "6-Documentation/docs/speculative-materials/NDimensionalGeneHypothesis.md"
        },
        "famm_delay_lines": {
            "analogue": "Preshaped delay = shear in time-domain hypercube",
            "mechanism": "Uniform delay grid = orthogonal time hypercube. Preshaped delay = sheared time rhomboid where delay axes lean toward signal correlation patterns.",
            "file": "4-Infrastructure/hardware/famm_verilator_bench.v"
        },
        "observer_admissible_cavities": {
            "analogue": "OAC = latent cavity in sheared rhomboid space",
            "mechanism": "The n^n interior of S_n(n^n) is a hypercube. Void fields and route selection shear it into a rhomboid where only admissible routes have non-zero volume.",
            "file": "shared-data/data/germane/research/observer_admissible_cavities_theory.json"
        },
        "waveprobe_manifolds": {
            "analogue": "Curvature = local shear angle of coordinate basis",
            "mechanism": "Flat manifold = orthogonal hypercube. Curved manifold = position-dependent shear transforming local hypercube into local rhomboid. Ricci curvature = trace of shear gradient.",
            "file": "5-Applications/scripts/hdmi_computational_shell.py"
        }
    },

    "compression_interpretation": {
        "topological_compression": (
            "Orthogonal hypercube has empty space between correlated axes. "
            "Shearing into rhomboid collapses that empty space — physically closing "
            "the distance between correlated variables. This is geometric compression: "
            "same information in less volume."
        ),
        "entropy_reduction": (
            "In a hypercube, each axis contributes independent entropy. "
            "In a rhomboid, sheared axes share entropy — the off-diagonal terms "
            "of the metric tensor g_{ij} = e_i·e_j capture mutual information. "
            "Compression ratio ≈ det(g)^{-1/2}."
        ),
        "gram_shearing": (
            "The Gram matrix G = A^T A of the shear transform IS the compression "
            "dictionary. Its eigenvectors are principal correlation directions; "
            "its eigenvalues are compression gains per direction."
        )
    },

    "information_gravity": {
        "analogy": (
            "Flat orthogonal grid = empty spacetime. "
            "Sheared rhomboid grid = spacetime with mass. "
            "The shear angle at each point encodes local information density. "
            "Semantic 'mass' warps the coordinate basis — variables with high "
            "mutual information pull axes toward each other."
        ),
        "metric_tensor": "g_{μν} = δ_{μν} + κ·I_{μν} where I_{μν} is mutual information between dimensions μ,ν and κ is the gravitational coupling",
        "geodesics": "Information flow follows geodesics of the sheared metric — shortest path through entangled variable space"
    },

    "keeper_phrases": [
        "A hypercube assumes independence; a hyper-rhomboid models entanglement.",
        "Shearing a tensor is the geometric dual of discovering correlation.",
        "The Gram matrix of the shear is the compression dictionary.",
        "Information has mass — it warps the coordinate basis it lives in.",
        "Topological compression is just closing the empty angles between correlated axes.",
        "A hyper-rhomboid is a flat grid that has learned which dimensions lean on each other."
    ],

    "metadata": {
        "ingested_at": time.time(),
        "tags": [
            "hypercube", "hyper-rhomboid", "parallelotope", "tensor-calculus",
            "geometric-shear", "topological-compression", "information-gravity",
            "manifold-learning", "gram-matrix", "entanglement-geometry"
        ]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)

    out_path = germane_dir / "hypercube_rhomboid_composition.json"
    with open(out_path, 'w') as f:
        json.dump(HYPER_RHOMBOID, f, indent=2)

    print(f"✓ Ingested: {out_path}")

    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)

    index.append({
        "id": HYPER_RHOMBOID["id"],
        "title": HYPER_RHOMBOID["title"],
        "date": HYPER_RHOMBOID["date"],
        "source": HYPER_RHOMBOID["source"],
        "ingested_at": HYPER_RHOMBOID["metadata"]["ingested_at"],
        "tags": HYPER_RHOMBOID["metadata"]["tags"],
    })

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"✓ Index: {len(index)} entries")

    print(f"\nStack mappings:")
    for name, mapping in HYPER_RHOMBOID["stack_mappings"].items():
        print(f"  ↔ {name}: {mapping['analogue'][:80]}...")

    print(f"\nKeeper phrases:")
    for p in HYPER_RHOMBOID["keeper_phrases"]:
        print(f"  → {p}")


if __name__ == "__main__":
    ingest()
