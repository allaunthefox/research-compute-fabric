#!/usr/bin/env python3
"""
Map System Equations to 4-Primitive Framework
==============================================
Review all system equations and map them to the 4 primitives:
- Field primitive (ρ(x⃗))
- Shear primitive (G = AᵀA)
- Packet primitive (Γᵢ)
- Spectral primitive (C = UΛUᵀ)
"""

import json
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

# 4-primitive framework
PRIMITIVES = {
    "field": {
        "equation": "ρ(x⃗)",
        "role": "tells you what exists (field / substrate / scalar manifold state)",
        "keywords": ["entropy", "density", "distribution", "manifold", "topology", "field", "state"]
    },
    "shear": {
        "equation": "G = AᵀA",
        "role": "tells you how it deforms (shear / metric deformation / lawful geometry)",
        "keywords": ["distance", "metric", "transform", "deformation", "shear", "geometry", "hyperbolic"]
    },
    "packet": {
        "equation": "Γᵢ",
        "role": "tells you what is emitted/witnessed (packet / executable typed glyph-witness / codec event)",
        "keywords": ["coding", "compression", "transform", "bwt", "ans", "packet", "codec", "optimization"]
    },
    "spectral": {
        "equation": "C = UΛUᵀ",
        "role": "tells you what basis survives (spectral / eigenbasis / pruning-correlation structure)",
        "keywords": ["complexity", "basis", "bottleneck", "decomposition", "spectral", "eigen", "dimension", "tradeoff"]
    }
}

# System equations from grand unified theory
SYSTEM_EQUATIONS = {
    "grand_unified_theory": {
        "source": "grand_unified_theory_20260504_163327.json",
        "axioms": {
            "axiom_1_shannon_entropy": {
                "formula": "H(X) = -sum_{i} p(x_i) log_2 p(x_i) ≈ 0.6-1.3 bits/character",
                "primitive": "field",
                "mapping": "Shannon entropy = field state (probability distribution over symbols)"
            },
            "axiom_2_kolmogorov_complexity": {
                "formula": "K(x) = min_{p: U(p)=x} |p|",
                "primitive": "spectral",
                "mapping": "Kolmogorov complexity = spectral basis (shortest program = optimal basis)"
            },
            "axiom_3_zipf_law": {
                "formula": "f(r) = C * r^(-α), where α ≈ 1.0-1.2 for English",
                "primitive": "field",
                "mapping": "Zipf law = field distribution (power-law distribution over symbols)"
            },
            "axiom_4_grammar_as_manifold": {
                "formula": "dim(M_grammar) << dim(Σ*)",
                "primitive": "field",
                "mapping": "Grammar as manifold = field topology (low-dimensional embedding)"
            },
            "axiom_5_hyperbolic_hierarchy": {
                "formula": "d(u,v) = arccosh(1 + 2||u-v||^2/((1-||u||^2)(1-||v||^2)))",
                "primitive": "shear",
                "mapping": "Hyperbolic hierarchy = geometric deformation (distance metric in curved space)"
            },
            "axiom_6_information_bottleneck": {
                "formula": "min I(X;Z) - β*I(Z;Y)",
                "primitive": "spectral",
                "mapping": "Information bottleneck = spectral decomposition (compress irrelevant, preserve relevant)"
            },
            "axiom_7_ans_optimality": {
                "formula": "L_ANS <= H(X) + ε, where ε ≈ 0.001 bits/symbol",
                "primitive": "packet",
                "mapping": "ANS optimality = packet coding (near-optimal entropy coding)"
            },
            "axiom_8_bwt_repetitiveness": {
                "formula": "|RLBWT(w)| = O(r), where r = number of runs in BWT output",
                "primitive": "packet",
                "mapping": "BWT repetitiveness = packet transform (permuted sort clusters contexts)"
            },
            "axiom_9_mdl_principle": {
                "formula": "L(D,M) = L(M) + L(D|M)",
                "primitive": "spectral",
                "mapping": "MDL principle = spectral tradeoff (model size + data description)"
            },
            "axiom_10_topological_invariants": {
                "formula": "H_k(X_ε) for ε in [0, ∞), tracking birth/death of k-dimensional holes",
                "primitive": "field",
                "mapping": "Topological invariants = field topology (persistent homology)"
            }
        },
        "unified_equations": {
            "grand_compression_equation": {
                "formula": "C* = argmin_C [ H(X|C) + λ|C| + μ*K(C) + ν*dim(M_C) ]",
                "primitive": "packet",
                "mapping": "Grand compression equation = packet optimization (balance entropy, model size, complexity, dimensionality)"
            },
            "language_as_manifold": {
                "formula": "L = { w ∈ Σ* | G(w) = 1 } ≈ M ⊂ R^d",
                "primitive": "shear",
                "mapping": "Language as manifold = shear transform (grammar → manifold embedding)"
            },
            "hyperbolic_semantic_distance": {
                "formula": "d_P(u,v) = arccosh(1 + 2*||u-v||^2/((1-||u||^2)(1-||v||^2)))",
                "primitive": "spectral",
                "mapping": "Hyperbolic semantic distance = spectral metric (distance in hyperbolic space)"
            },
            "information_bottleneck_language": {
                "formula": "min_{p(z|x)} I(X;Z) - β*I(Z;Y) + γ*R(Z)",
                "primitive": "spectral",
                "mapping": "Information bottleneck for language = spectral regularization (compression + prediction + geometry)"
            }
        }
    },
    "compactified_core_equations": {
        "source": "compactified_core_equations_v1.json",
        "primitives": {
            "field_primitive": {
                "equation": "ρ(x⃗)",
                "derives": ["morse_smale", "radius_ratio", "residual_ratio", "s3c_shell"],
                "role": "field state / substrate / scalar manifold state"
            },
            "shear_primitive": {
                "equation": "G = AᵀA",
                "derives": ["shear_matrix", "famm_delay", "eigen_decomposition"],
                "role": "shear / metric deformation / lawful geometry"
            },
            "packet_primitive": {
                "equation": "Γᵢ = γᵢ ⊗ χᵢ ⊗ κᵢ ⊗ τᵢ ⊗ UᵢΛᵢaᵢ ⊗ θᵢ ⊗ εᵢ",
                "derives": ["gccl_packet", "gain_test"],
                "role": "packet / executable typed glyph-witness / codec event"
            },
            "spectral_primitive": {
                "equation": "C = UΛUᵀ",
                "derives": ["residual_correlation", "eigen_decomposition", "famm_spectral"],
                "role": "spectral / eigenbasis / pruning-correlation structure"
            }
        }
    }
}

def analyze_mapping():
    print("=" * 70)
    print("  SYSTEM EQUATIONS → 4-PRIMITIVE FRAMEWORK MAPPING")
    print("=" * 70)

    print("\n4-PRIMITIVE FRAMEWORK:")
    for prim, data in PRIMITIVES.items():
        print(f"\n{prim.upper()}: {data['equation']}")
        print(f"  Role: {data['role']}")
        print(f"  Keywords: {', '.join(data['keywords'])}")

    print("\n" + "=" * 70)
    print("  GRAND UNIFIED THEORY EQUATIONS")
    print("=" * 70)

    gut = SYSTEM_EQUATIONS["grand_unified_theory"]
    print(f"\nSource: {gut['source']}")
    print(f"10 axioms, 4 unified equations")

    print("\nAXIOMS:")
    for ax_name, ax_data in gut["axioms"].items():
        prim = ax_data["primitive"].upper()
        print(f"\n{ax_name}:")
        print(f"  Formula: {ax_data['formula']}")
        print(f"  Primitive: {prim}")
        print(f"  Mapping: {ax_data['mapping']}")

    print("\nUNIFIED EQUATIONS:")
    for eq_name, eq_data in gut["unified_equations"].items():
        prim = eq_data["primitive"].upper()
        print(f"\n{eq_name}:")
        print(f"  Formula: {eq_data['formula']}")
        print(f"  Primitive: {prim}")
        print(f"  Mapping: {eq_data['mapping']}")

    print("\n" + "=" * 70)
    print("  PRIMITIVE DISTRIBUTION")
    print("=" * 70)

    primitive_counts = {"field": 0, "shear": 0, "packet": 0, "spectral": 0}

    for ax_data in gut["axioms"].values():
        primitive_counts[ax_data["primitive"]] += 1

    for eq_data in gut["unified_equations"].values():
        primitive_counts[eq_data["primitive"]] += 1

    print(f"\nField primitive (ρ(x⃗)): {primitive_counts['field']} equations")
    print(f"Shear primitive (G = AᵀA): {primitive_counts['shear']} equations")
    print(f"Packet primitive (Γᵢ): {primitive_counts['packet']} equations")
    print(f"Spectral primitive (C = UΛUᵀ): {primitive_counts['spectral']} equations")

    print("\n" + "=" * 70)
    print("  COMPACTIFIED CORE EQUATIONS")
    print("=" * 70)

    cce = SYSTEM_EQUATIONS["compactified_core_equations"]
    print(f"\nSource: {cce['source']}")

    for prim, data in cce["primitives"].items():
        print(f"\n{prim}:")
        print(f"  Equation: {data['equation']}")
        print(f"  Derives: {', '.join(data['derives'])}")
        print(f"  Role: {data['role']}")

    print("\n" + "=" * 70)
    print("  INTEGRATION ANALYSIS")
    print("=" * 70)

    print("\nGrand unified theory equations map to:")
    print(f"  - Field primitive: {primitive_counts['field']} equations (Shannon entropy, Zipf law, grammar manifold, topological invariants)")
    print(f"  - Shear primitive: {primitive_counts['shear']} equations (hyperbolic hierarchy, language as manifold)")
    print(f"  - Packet primitive: {primitive_counts['packet']} equations (ANS optimality, BWT, grand compression)")
    print(f"  - Spectral primitive: {primitive_counts['spectral']} equations (Kolmogorov complexity, information bottleneck, MDL, hyperbolic distance)")

    print("\nCompactified core equations:")
    print("  - Field primitive: derives Morse-Smale, radius_ratio, residual_ratio, S3C shells")
    print("  - Shear primitive: derives shear_matrix, FAMM delays, eigen_decomposition")
    print("  - Packet primitive: derives GCCL packet, gain test")
    print("  - Spectral primitive: derives residual correlation, eigen_decomposition, FAMM spectral")

    print("\n" + "=" * 70)
    print("  KEY INSIGHTS")
    print("=" * 70)

    print("\n1. Consistency: Grand unified theory axioms map cleanly to 4 primitives")
    print("2. Redundancy: Some equations span multiple primitives (e.g., grand compression = packet + spectral)")
    print("3. Completeness: Each primitive has representative equations from multiple sources")
    print("4. Integration: Compactified core equations subsume grand unified theory equations")
    print("5. Canonical mapping:")
    print("   - Field: entropy, density, topology, manifold structure")
    print("   - Shear: distance, metric, deformation, geometric transform")
    print("   - Packet: coding, compression, transform, optimization")
    print("   - Spectral: complexity, basis, bottleneck, decomposition, tradeoff")

    # Save mapping
    output_file = RESEARCH_STACK / "4-Infrastructure/shim/system_equations_4primitive_mapping.json"
    with open(output_file, 'w') as f:
        json.dump({
            "primitives": PRIMITIVES,
            "system_equations": SYSTEM_EQUATIONS,
            "primitive_counts": primitive_counts,
            "insights": {
                "consistency": "Grand unified theory axioms map cleanly to 4 primitives",
                "redundancy": "Some equations span multiple primitives",
                "completeness": "Each primitive has representative equations from multiple sources",
                "integration": "Compactified core equations subsume grand unified theory equations"
            }
        }, f, indent=2)

    print(f"\n✓ Mapping saved to: {output_file}")


if __name__ == "__main__":
    analyze_mapping()
