#!/usr/bin/env python3
"""
Ingest: Observer-Admissible Cavities & Radius-Ratio Compression Theory
Maps the ChatGPT conversation into Research Stack database with
cross-references to existing modules.
"""

import json, time
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

OAC_THEORY = {
    "id": "observer-admissible-cavities-theory",
    "source": "ChatGPT conversation — radius-ratio → Pidgen-hole → S3C/Spherion → OAC",
    "title": "Observer-Admissible Cavities: Latent Shaped Holes as Compression Primitives",
    "date": "2026-05-07",
    "summary": "Observer-Admissible Cavities (OACs) are latent shaped holes whose combinatorial interiors remain compressed until a lawful observer touches them. Admissible touches manifest routes; inadmissible touches manifest void scars. OACs create temporary exploration spaces that do not pollute the substrate address space — only receipts, accepted routes, and residuals commit.",
    
    "key_concepts": {
        "radius_ratio_rule": {
            "definition": "Cation/anion radius ratio predicts admissible coordination geometry (CN3=0.155, CN4=0.225, CN6=0.414, CN8=0.732)",
            "compression_analogue": "Local scale ratio → admissible motif class → decode rule + residual",
            "sources": ["LibreTexts 9.1", "Wikipedia cation-anion radius ratio", "MIT 12.108 lec4"]
        },
        "pidgen_hole_theory": {
            "definition": "Objects fall into typed admissible holes; compression stores hole_id + residual. A hole is compressive when L(hole) + L(residual) < L(raw).",
            "upgrade": "Radius-ratio gives holes typed geometry (not just buckets). S3C gives shell coordinates. Spherion gives surface shaping."
        },
        "s3c_shell_coordinates": {
            "definition": "n = k² + a, with mirror complement b⁰, next-shell tension b⁺, mass = a×b⁰, mirror_delta = a-b⁰",
            "compression_role": "Converts raw values into structured shell cavities with throat/boundary/asymmetry classification",
            "existing_module": "4-Infrastructure/shim/SPEC_SHEET_REFERENCE.md, S3C geometry docs"
        },
        "spherion_shaping": {
            "definition": "Resonant spherical surfaces with pyramid protrusions (positive) and voids (negative). High-Q = narrow confident prediction; low-Q = broad noisy prediction.",
            "compression_role": "Pyramid height = amplitude, base width = duration, slope = transition, asymmetry = skew, apex = precision. Negative pyramids = expected-but-missing features (void carrier).",
            "existing_module": "topology-resonance hierarchy doc, pyramid-spherion gear review"
        },
        "sn_nn": {
            "definition": "S_n(n^n): shaped shell with symbolic n^n combinatorial interior. Interior is latent — not materialized. Only selected route + residual paid.",
            "recursive_form": "S_n((S_{n-1})^n): recursive shell grammar — nth shell contains n choices of previous shell state",
            "compression_role": "Explosive interior bound behind compact shell descriptor"
        },
        "observer_admissible_cavity": {
            "definition": "OAC = (S_n, A_O, T, V, R, ε): latent cavity that only manifests under lawful observer touch",
            "touch_operator": "touch(O, OAC_i, q) → (S_i, r_i, ε_i, ρ_i) if admissible, (V_i, scar_i, ρ_i) otherwise",
            "address_space_rule": "OAC ⊄ A_substrate; only receipt, accepted route, and residual may commit",
            "temporary_exploration": "OACs create observer-scoped scratch manifolds that evaporate after gate decision — no substrate pollution"
        }
    },
    
    "compression_pipeline": [
        "raw bytes/tokens/graph nodes",
        "map to integer or local state n",
        "S3C split: k, a, b⁰, b⁺",
        "classify throat/boundary/asymmetry",
        "map to spherion mode σ",
        "add pyramid/void shaping h",
        "emit S_n codon",
        "emit residual",
        "entropy-code streams separately"
    ],
    
    "output_streams": [
        "shell indices k",
        "offsets a",
        "throat/mass classes",
        "shape modes",
        "void/protrusion masks",
        "residual bytes"
    ],
    
    "admissibility_gate": {
        "accept": "L(S_n) + L(route) + L(ε) < L(x)",
        "reject": "void scar + FAMM memory + down-ranked prior",
        "existing_module": "MS3C GCL admissibility wrapper, FAMM failure-memory compression"
    },
    
    "keeper_phrases": [
        "A compressive hole is a lawful cavity whose residual is cheaper than the thing it absorbs.",
        "S3C gives the pigeon a lawful shell; Spherion shaping gives the hole teeth, voids, and resonance.",
        "S_n(n^n) is a Matryoshka shell: externally small, internally combinatorial, decoded only along lawful routed paths.",
        "Do not store the n^n interior. Store the shaped shell, the void field, the selected route, and the residual.",
        "The holes are lazy. They do not exist as expanded objects; they exist as lawful cavities with manifestation rules.",
        "Observer-Admissible Cavities create temporary exploration manifolds whose interiors do not occupy substrate address space.",
        "OACs let the system think in holes without storing every hole it thinks through."
    ],
    
    "cross_references": {
        "existing_modules": {
            "pist_biological_polymorphic_shifter_v3_complete.py": "PIST nD bundle encode/decode — direct S3C shell mapping target",
            "topological_state_machine.py": "State transitions → touch operations on OACs",
            "hdmi_computational_shell.py": "Shell computation surface → OAC manifestation target",
            "FixedPoint.lean": "Q16.16 arithmetic for mass/mirror_delta/throat classification",
            "NDimensionalGeneHypothesis.md": "Gene as n-D information structure → OAC as gene-analogue cavity",
            "famm_verilator_bench.v": "FAMM preshaped delays → OAC route latency model",
            "prover_orchestration_layer.py": "L0-L3 pipeline → OAC touch/gate/commit pipeline"
        },
        "new_primitives_needed": [
            "OAC.lean — Lean 4 formalization of Observer-Admissible Cavities",
            "s3c_shell_codec.py — S3C shell coordinate encoder/decoder",
            "spherion_shape_quantizer.py — Pyramid/void field classifier",
            "oac_touch_gate.py — Touch operator with GCL admissibility check"
        ]
    },
    
    "metadata": {
        "ingested_at": time.time(),
        "tags": [
            "observer-admissible-cavities", "radius-ratio", "coordination-geometry",
            "pidgen-hole-theory", "s3c-shells", "spherion-shaping",
            "compression-theory", "lazy-manifestation", "substrate-separation",
            "temporary-exploration", "admissibility-gate", "void-carrier"
        ]
    }
}


def ingest():
    germane_dir = RESEARCH_STACK / "shared-data/data/germane/research"
    germane_dir.mkdir(parents=True, exist_ok=True)
    
    out_path = germane_dir / "observer_admissible_cavities_theory.json"
    with open(out_path, 'w') as f:
        json.dump(OAC_THEORY, f, indent=2)
    
    print(f"✓ Ingested: {out_path}")
    
    # Update index
    index_path = germane_dir / "research_ingestion_index.json"
    index = []
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    
    index.append({
        "id": OAC_THEORY["id"],
        "title": OAC_THEORY["title"],
        "date": OAC_THEORY["date"],
        "source": OAC_THEORY["source"],
        "ingested_at": OAC_THEORY["metadata"]["ingested_at"],
        "tags": OAC_THEORY["metadata"]["tags"],
    })
    
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"✓ Index: {len(index)} entries")
    
    print(f"\nKey concepts ingested:")
    for name, concept in OAC_THEORY["key_concepts"].items():
        print(f"  • {name}: {concept['definition'][:80]}...")
    
    print(f"\nCross-references to existing modules:")
    for module, role in OAC_THEORY["cross_references"]["existing_modules"].items():
        print(f"  ↔ {module}: {role[:70]}...")
    
    print(f"\nNew primitives needed:")
    for p in OAC_THEORY["cross_references"]["new_primitives_needed"]:
        print(f"  + {p}")
    
    print(f"\nKeeper phrases ({len(OAC_THEORY['keeper_phrases'])}):")
    for phrase in OAC_THEORY["keeper_phrases"]:
        print(f"  → {phrase}")


if __name__ == "__main__":
    ingest()
