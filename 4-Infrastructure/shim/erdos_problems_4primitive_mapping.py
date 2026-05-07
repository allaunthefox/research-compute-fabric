#!/usr/bin/env python3
"""
Erdős Problems → 4-Primitive Framework Mapping
==============================================
Identify which Erdős problems could be approached using the
4-primitive framework (field, shear, packet, spectral).
"""

import json
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")

# 4-primitive framework
PRIMITIVES = {
    "field": {
        "equation": "ρ(x⃗)",
        "role": "tells you what exists (field / substrate / scalar manifold state)",
        "erdos_applications": [
            "Density of primes and prime gaps",
            "Arithmetic progressions in dense sets (Szemerédi)",
            "Distribution of integers in additive sets",
            "Density in combinatorial structures",
            "Erdős–Turán theorem on additive bases"
        ]
    },
    "shear": {
        "equation": "G = AᵀA",
        "role": "tells you how it deforms (shear / metric deformation / lawful geometry)",
        "erdos_applications": [
            "Graph distances and metric embeddings",
            "Extremal graph theory (max/min edges)",
            "Graph isoperimetry and expansion",
            "Erdős–Stone theorem (extremal function)",
            "Graph minor theory and treewidth"
        ]
    },
    "packet": {
        "equation": "Γᵢ",
        "role": "tells you what is emitted/witnessed (packet / executable typed glyph-witness / codec event)",
        "erdos_applications": [
            "Ramsey numbers and witness structures",
            "Extremal set systems (covering/packing)",
            "Erdős–Ko–Rado theorem",
            "Erdős–Szekeres theorem (monotone subsequences)",
            "Erdős–Ginzburg–Ziv theorem (zero-sum subsets)"
        ]
    },
    "spectral": {
        "equation": "C = UΛUᵀ",
        "role": "tells you what basis survives (spectral / eigenbasis / pruning-correlation structure)",
        "erdos_applications": [
            "Graph spectra and eigenvalue bounds",
            "Graph partitioning and clustering",
            "Random graph eigenvalue distributions",
            "Erdős–Rényi model properties",
            "Expander graphs and spectral gap"
        ]
    }
}

# Erdős problems mapped to 4 primitives
ERDOS_PROBLEMS = {
    "high_priority": {
        "erdos_turan_conjecture": {
            "name": "Erdős–Turán Conjecture on Additive Bases",
            "statement": "If A is an additive basis of order 2 for the natural numbers, then the sum of reciprocals diverges: Σ_{a∈A} 1/a = ∞",
            "primitive": "field",
            "mapping": "Additive basis density = field distribution. Conjecture about density of basis elements.",
            "approach": "Treat A as density field ρ(n). Analyze spectral decomposition of additive structure. Use field primitive to model basis density and shear primitive to analyze additive deformation.",
            "feasibility": "HIGH - Directly about density/distribution, maps cleanly to field primitive"
        },
        "erdos_straus_conjecture": {
            "name": "Erdős–Straus Conjecture",
            "statement": "For every integer n ≥ 2, the equation 4/n = 1/x + 1/y + 1/z has a solution in positive integers x, y, z",
            "primitive": "packet",
            "mapping": "Egyptian fraction decomposition = packet encoding. Each solution is a packet (x,y,z) encoding 4/n.",
            "approach": "Treat solutions as packets. Use packet primitive to search for encoding space. Spectral analysis of solution space structure.",
            "feasibility": "HIGH - Problem about finding encodings/packets, natural fit for packet primitive"
        },
        "erdos_conjecture_arithmetic_progressions": {
            "name": "Erdős Conjecture on Arithmetic Progressions",
            "statement": "If Σ_{a∈A} 1/a diverges, then A contains arbitrarily long arithmetic progressions",
            "primitive": "field",
            "mapping": "Divergent reciprocal sum = high density field. High density implies rich structure (APs).",
            "approach": "Use field primitive to model density ρ(A). Apply shear primitive to analyze how density deforms under translation (arithmetic progression structure). Spectral decomposition to detect periodic structure.",
            "feasibility": "HIGH - Directly about density implying structure, field primitive natural fit"
        },
        "erdos_renyi_random_graph": {
            "name": "Erdős–Rényi Random Graph Model",
            "statement": "Study properties of G(n,p) random graphs. Threshold phenomena for connectivity, giant component, Hamiltonicity",
            "primitive": "spectral",
            "mapping": "Random graph eigenvalue distribution = spectral basis. Phase transitions = spectral pruning.",
            "approach": "Use spectral primitive to analyze eigenvalue distribution of G(n,p). Detect phase transitions via spectral gap. Field primitive for density of edges.",
            "feasibility": "VERY HIGH - Well-studied, spectral methods standard, direct mapping"
        }
    },
    "medium_priority": {
        "erdos_ko_rado": {
            "name": "Erdős–Ko–Rado Theorem (extensions)",
            "statement": "Maximum size of intersecting families of k-subsets of {1,...,n}",
            "primitive": "packet",
            "mapping": "Intersecting family = packet collection with witness property (intersection).",
            "approach": "Treat each family as packet set. Use packet primitive to analyze encoding constraints. Spectral analysis of intersection graph.",
            "feasibility": "MEDIUM - Solved for large n, but extensions open. Packet primitive useful for generalizations"
        },
        "erdos_szekeres": {
            "name": "Erdős–Szekeres Theorem (generalizations)",
            "statement": "Any sequence of n²+1 distinct real numbers contains a monotone subsequence of length n+1",
            "primitive": "packet",
            "mapping": "Monotone subsequence = packet witness. Ramsey-type problem about finding structure.",
            "approach": "Use packet primitive to model subsequences as witnesses. Shear primitive for ordering deformation. Spectral analysis of permutation patterns.",
            "feasibility": "MEDIUM - Solved, but generalizations and extensions open"
        },
        "erdos_ginzburg_ziv": {
            "name": "Erdős–Ginzburg–Ziv Theorem (extensions)",
            "statement": "Any 2n-1 integers contain n whose sum is divisible by n",
            "primitive": "packet",
            "mapping": "Zero-sum subset = packet with witness property (sum = 0 mod n).",
            "approach": "Treat subsets as packets. Use packet primitive to search for zero-sum encoding. Spectral analysis of additive structure modulo n.",
            "feasibility": "MEDIUM - Solved, but extensions to other groups and structures open"
        },
        "erdos_stone": {
            "name": "Erdős–Stone Theorem (extremal function)",
            "statement": "For any graph H, ex(n,H) = (1 - 1/χ(H)-1 + o(1))n²/2 where χ(H) is chromatic number",
            "primitive": "shear",
            "mapping": "Extremal function = shear metric. Maximum edges without H = deformation constraint.",
            "approach": "Use shear primitive to analyze edge density under forbidden subgraph constraint. Spectral analysis of extremal graphs. Field primitive for density.",
            "feasibility": "MEDIUM - Solved, but generalizations to hypergraphs open"
        }
    },
    "exploratory": {
        "erdos_faber_lovasz": {
            "name": "Erdős–Faber–Lovász Conjecture",
            "statement": "If each edge of a complete graph on n vertices is colored with one of n colors, then there exists a set of n edges with no two sharing a vertex or having the same color",
            "primitive": "packet",
            "mapping": "Edge coloring = packet encoding. Matching = packet set with witness properties.",
            "approach": "Use packet primitive to model edge colorings as encodings. Spectral analysis of intersection graph. Shear for matching constraints.",
            "feasibility": "EXPLORATORY - Recently solved (2021), but method could generalize"
        },
        "erdos_distinct_distances": {
            "name": "Erdős Distinct Distances Problem",
            "statement": "Any set of n points in the plane determines at least n/√log n distinct distances",
            "primitive": "shear",
            "mapping": "Distance set = shear metric. Point configuration = field manifold.",
            "approach": "Use field primitive for point configuration. Shear primitive for distance metric. Spectral analysis of distance distribution.",
            "feasibility": "EXPLORATORY - Solved (Guth-Katz), but 4-primitive approach could provide new perspective"
        },
        "erdos_moser_problem": {
            "name": "Erdős–Moser Problem",
            "statement": "Find all solutions to 1/a + 1/b + 1/c + 1/d + 1/e = 1 in distinct positive integers",
            "primitive": "packet",
            "mapping": "Egyptian fraction decomposition = packet encoding. Each solution is a 5-tuple packet.",
            "approach": "Use packet primitive to search for encoding space. Spectral analysis of solution structure. Field for density of solutions.",
            "feasibility": "EXPLORATORY - Solved (only known solution), but method could generalize to other Diophantine equations"
        },
        "erdos_hadamard": {
            "name": "Erdős Hadamard Conjecture",
            "statement": "There exist Hadamard matrices of order 4k for all k",
            "primitive": "spectral",
            "mapping": "Hadamard matrix = spectral basis (orthogonal rows/columns). Eigenvalues = ±√n.",
            "approach": "Use spectral primitive to analyze matrix structure. Field for existence density. Packet for construction methods.",
            "feasibility": "EXPLORATORY - Open problem, spectral methods standard in Hadamard matrix theory"
        }
    }
}


def analyze_erdos_mapping():
    print("=" * 70)
    print("  ERDŐS PROBLEMS → 4-PRIMITIVE FRAMEWORK MAPPING")
    print("=" * 70)

    print("\n4-PRIMITIVE FRAMEWORK:")
    for prim, data in PRIMITIVES.items():
        print(f"\n{prim.upper()}: {data['equation']}")
        print(f"  Role: {data['role']}")
        print(f"  Erdős applications:")
        for app in data['erdos_applications']:
            print(f"    • {app}")

    print("\n" + "=" * 70)
    print("  ERDŐS PROBLEMS BY PRIORITY")
    print("=" * 70)

    for priority, problems in ERDOS_PROBLEMS.items():
        print(f"\n{priority.upper().replace('_', ' ')} ({len(problems)} problems):")
        for prob_id, prob in problems.items():
            prim = prob["primitive"].upper()
            print(f"\n  • {prob['name']}")
            print(f"    Primitive: {prim}")
            print(f"    Statement: {prob['statement'][:100]}...")
            print(f"    Mapping: {prob['mapping']}")
            print(f"    Feasibility: {prob['feasibility']}")

    print("\n" + "=" * 70)
    print("  PRIMITIVE DISTRIBUTION")
    print("=" * 70)

    primitive_counts = {"field": 0, "shear": 0, "packet": 0, "spectral": 0}
    for priority, problems in ERDOS_PROBLEMS.items():
        for prob in problems.values():
            primitive_counts[prob["primitive"]] += 1

    total = sum(primitive_counts.values())
    for prim, count in primitive_counts.items():
        percent = count / total * 100 if total > 0 else 0
        print(f"\n{prim.upper()} ({count} problems, {percent:.1f}%):")
        problems_list = []
        for priority, problems in ERDOS_PROBLEMS.items():
            for prob_id, prob in problems.items():
                if prob["primitive"] == prim:
                    problems_list.append(f"{prob['name']} ({priority})")
        for p in problems_list:
            print(f"  • {p}")

    print("\n" + "=" * 70)
    print("  RECOMMENDED APPROACH ORDER")
    print("=" * 70)

    print("\n1. Erdős–Rényi Random Graph Model (SPECTRAL)")
    print("   - Why: Well-studied, spectral methods standard, direct mapping")
    print("   - Approach: Analyze eigenvalue distribution of G(n,p), detect phase transitions via spectral gap")
    print("   - Expected outcome: New insights into random graph phase transitions")

    print("\n2. Erdős–Turán Conjecture (FIELD)")
    print("   - Why: Directly about density/distribution, maps cleanly to field primitive")
    print("   - Approach: Treat additive basis as density field, analyze spectral decomposition of additive structure")
    print("   - Expected outcome: New perspective on basis density and additive structure")

    print("\n3. Erdős–Straus Conjecture (PACKET)")
    print("   - Why: Problem about finding encodings/packets, natural fit for packet primitive")
    print("   - Approach: Treat solutions as packets, search encoding space, spectral analysis of solution structure")
    print("   - Expected outcome: Potential progress on long-standing Diophantine problem")

    print("\n4. Erdős Conjecture on Arithmetic Progressions (FIELD)")
    print("   - Why: Directly about density implying structure, field primitive natural fit")
    print("   - Approach: Model density ρ(A), apply shear to analyze density deformation under translation")
    print("   - Expected outcome: New approach to Szemerédi-type theorems")

    print("\n" + "=" * 70)
    print("  KEY INSIGHTS")
    print("=" * 70)

    print("\n1. Field primitive (2 problems):")
    print("   - Erdős–Turán Conjecture: additive basis density")
    print("   - Erdős Conjecture on APs: density implies structure")
    print("   - Core: density problems, distribution analysis, additive structure")

    print("\n2. Shear primitive (2 problems):")
    print("   - Erdős–Stone Theorem: extremal function")
    print("   - Erdős Distinct Distances: distance metric")
    print("   - Core: extremal problems, metric geometry, graph deformation")

    print("\n3. Packet primitive (5 problems):")
    print("   - Erdős–Straus Conjecture: Egyptian fraction encoding")
    print("   - Erdős–Ko–Rado: intersecting families")
    print("   - Erdős–Szekeres: monotone subsequences")
    print("   - Erdős–Ginzburg–Ziv: zero-sum subsets")
    print("   - Erdős–Faber–Lovász: edge colorings")
    print("   - Core: encoding problems, witness structures, Ramsey-type problems")

    print("\n4. Spectral primitive (2 problems):")
    print("   - Erdős–Rényi Random Graph: eigenvalue distribution")
    print("   - Erdős Hadamard Conjecture: orthogonal matrices")
    print("   - Core: eigenvalue problems, spectral methods, random matrix theory")

    print("\n5. Cross-domain patterns:")
    print("   - Packet primitive dominates (5 problems) - many Erdős problems are about encodings/witnesses")
    print("   - Field and spectral each have 2 problems - density and eigenvalue problems are common")
    print("   - Shear has 2 problems - extremal and metric geometry problems")
    print("   - All primitives represented - 4-primitive framework covers diverse Erdős problem types")

    print("\n6. Recommended starting point:")
    print("   - Erdős–Rényi Random Graph Model: spectral methods standard, high feasibility")
    print("   - This provides a validation of the 4-primitive framework on well-understood problem")
    print("   - Success here would validate approach for harder problems (Erdős–Turán, Erdős–Straus)")

    # Save mapping
    output_file = RESEARCH_STACK / "4-Infrastructure/shim/erdos_problems_4primitive_mapping.json"
    with open(output_file, 'w') as f:
        json.dump({
            "primitives": PRIMITIVES,
            "erdos_problems": ERDOS_PROBLEMS,
            "primitive_distribution": primitive_counts,
            "recommended_order": [
                "erdos_renyi_random_graph",
                "erdos_turan_conjecture",
                "erdos_straus_conjecture",
                "erdos_conjecture_arithmetic_progressions"
            ],
            "insights": {
                "packet_dominance": "Packet primitive dominates (5 problems) - many Erdős problems are about encodings/witnesses",
                "spectral_validation": "Erdős–Rényi provides validation point - spectral methods standard",
                "field_additive": "Field primitive for additive problems - density and structure",
                "shear_extremal": "Shear primitive for extremal problems - metric and deformation",
                "cross_domain": "All primitives represented - framework covers diverse Erdős problem types"
            }
        }, f, indent=2)

    print(f"\n✓ Mapping saved to: {output_file}")


if __name__ == "__main__":
    analyze_erdos_mapping()
