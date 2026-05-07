#!/usr/bin/env python3
"""
Refined Investigation of Erdős–Mollin–Walsh Conjecture with DAG + FAMM
======================================================================
Investigate Erdős–Mollin–Walsh Conjecture with DAG + FAMM components.
Conjecture: There are no consecutive triples of powerful numbers.

Previous test found consecutive triples (conjecture holds: False).
This investigation uses DAG + FAMM for powerful number sequence analysis.
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")


def is_powerful(n):
    """Check if n is a powerful number (all prime factors have exponent >= 2)."""
    if n < 1:
        return False
    
    for p in range(2, int(np.sqrt(n)) + 1):
        if n % p == 0:
            count = 0
            while n % p == 0:
                n //= p
                count += 1
            if count == 1:
                return False
    
    return n == 1 or n > 1


def generate_powerful_numbers(max_n):
    """Generate all powerful numbers up to max_n."""
    powerful = []
    for n in range(1, max_n + 1):
        if is_powerful(n):
            powerful.append(n)
    return powerful


def find_consecutive_triples(powerful_numbers):
    """Find consecutive triples of powerful numbers."""
    triples = []
    for i in range(len(powerful_numbers) - 2):
        if powerful_numbers[i + 1] == powerful_numbers[i] + 1 and powerful_numbers[i + 2] == powerful_numbers[i] + 2:
            triples.append((powerful_numbers[i], powerful_numbers[i + 1], powerful_numbers[i + 2]))
    return triples


def dag_powerful_sequence(powerful_numbers):
    """Build DAG structure for powerful number sequence."""
    n = len(powerful_numbers)
    
    # Assign layers based on prime factor complexity
    layers = []
    for num in powerful_numbers:
        # Layer based on number of distinct prime factors
        temp = num
        distinct_primes = 0
        for p in range(2, int(np.sqrt(temp)) + 1):
            if temp % p == 0:
                distinct_primes += 1
                while temp % p == 0:
                    temp //= p
        if temp > 1:
            distinct_primes += 1
        layers.append(distinct_primes % 4)
    
    # Build DAG with edges based on divisibility
    A = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            # Edge if j is a multiple of i (divisibility relation)
            if powerful_numbers[j] % powerful_numbers[i] == 0:
                if layers[j] >= layers[i]:  # Forward in complexity
                    A[i, j] = 1
    
    return A, layers


def famm_powerful_sequence(A, layers, delay_steps=3):
    """Apply FAMM delay lines for powerful number temporal sequencing."""
    n = A.shape[0]
    
    # Create delay line matrices for each delay step
    delay_matrices = []
    
    for delay in range(1, delay_steps + 1):
        # Delay matrix: information flows with delay
        D = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if A[i, j] == 1:
                    # Check if j is exactly 'delay' complexity layers ahead of i
                    if layers[j] - layers[i] == delay:
                        D[i, j] = 1
        delay_matrices.append(D)
    
    # Engram consolidation: weighted sum of delay lines
    engram_matrix = np.zeros((n, n))
    for i, D in enumerate(delay_matrices):
        weight = 1.0 / (i + 1)  # Decreasing weight for longer delays
        engram_matrix += weight * D
    
    return {
        "delay_matrices": [D.tolist() for D in delay_matrices],
        "engram_matrix": engram_matrix.tolist(),
        "delay_steps": delay_steps
    }


def field_analysis_powerful(powerful_numbers, max_n):
    """Compute field primitive metrics for powerful numbers."""
    if not powerful_numbers:
        return {
            "density": 0.0,
            "asymptotic_density": 0.0,
            "gap_distribution": []
        }
    
    density = len(powerful_numbers) / max_n
    asymptotic_density = density
    gaps = [powerful_numbers[i + 1] - powerful_numbers[i] for i in range(len(powerful_numbers) - 1)]
    
    return {
        "density": float(density),
        "asymptotic_density": float(asymptotic_density),
        "avg_gap": float(np.mean(gaps)) if gaps else 0.0,
        "max_gap": float(np.max(gaps)) if gaps else 0.0,
        "gap_distribution": gaps[:10]
    }


def spectral_analysis_powerful(A):
    """Compute spectral decomposition of powerful number DAG."""
    eigenvalues, _ = np.linalg.eigh(A)
    eigenvalues = np.sort(eigenvalues)[::-1]
    
    return {
        "eigenvalues": eigenvalues.tolist(),
        "spectral_radius": float(np.max(np.abs(eigenvalues))),
        "structure_rank": int(np.linalg.matrix_rank(A))
    }


def shear_analysis_powerful(powerful_numbers):
    """Compute shear primitive metrics for powerful number deformation."""
    if not powerful_numbers:
        return {
            "powerful_rigidity": 0.0,
            "gap_variance": 0.0,
            "clustering_score": 0.0
        }
    
    gaps = [powerful_numbers[i + 1] - powerful_numbers[i] for i in range(len(powerful_numbers) - 1)]
    gap_variance = np.var(gaps)
    powerful_rigidity = 1.0 / (gap_variance + 1e-10)
    small_gaps = sum(1 for g in gaps if g <= 2)
    clustering_score = small_gaps / len(gaps) if gaps else 0.0
    
    return {
        "powerful_rigidity": float(powerful_rigidity),
        "gap_variance": float(gap_variance),
        "clustering_score": float(clustering_score)
    }


def packet_analysis_powerful(powerful_numbers, triples):
    """Compute packet primitive metrics for powerful number encoding."""
    if not powerful_numbers:
        return {
            "packet_size": 0,
            "triple_count": 0,
            "encoding_efficiency": 0.0
        }
    
    packet_size = len(powerful_numbers)
    triple_count = len(triples)
    max_n = powerful_numbers[-1] if powerful_numbers else 1
    encoding_efficiency = packet_size / max_n if max_n > 0 else 0.0
    
    return {
        "packet_size": packet_size,
        "triple_count": triple_count,
        "encoding_efficiency": float(encoding_efficiency)
    }


def dag_analysis_powerful(A, layers):
    """Compute DAG-specific metrics for powerful numbers."""
    n = A.shape[0]
    topological_depth = len(set(layers))
    
    has_directed_cycle = False
    for i in range(n):
        for j in range(n):
            if A[i, j] == 1 and A[j, i] == 1:
                has_directed_cycle = True
                break
        if has_directed_cycle:
            break
    
    cross_layer_edges = 0
    total_edges = 0
    for i in range(n):
        for j in range(n):
            if A[i, j] == 1:
                total_edges += 1
                if layers[i] != layers[j]:
                    cross_layer_edges += 1
    
    temporal_density = cross_layer_edges / total_edges if total_edges > 0 else 0.0
    
    return {
        "topological_depth": topological_depth,
        "has_directed_cycle": has_directed_cycle,
        "temporal_density": float(temporal_density),
        "is_acyclic": not has_directed_cycle
    }


def famm_analysis_powerful(famm_result):
    """Compute FAMM-specific metrics for powerful numbers."""
    delay_matrices = famm_result["delay_matrices"]
    engram_matrix = np.array(famm_result["engram_matrix"])
    
    engram_strength = np.sum(engram_matrix)
    delay_diversity = sum(1 for D in delay_matrices if np.sum(D) > 0)
    temporal_integration = np.trace(engram_matrix) / engram_strength if engram_strength > 0 else 0.0
    
    return {
        "engram_strength": float(engram_strength),
        "delay_diversity": delay_diversity,
        "temporal_integration": float(temporal_integration),
        "delay_steps": famm_result["delay_steps"]
    }


def investigate_erdos_mollin_walsh_refined(max_n_values):
    """Investigate Erdős–Mollin–Walsh Conjecture with DAG + FAMM."""
    results = []
    
    for max_n in max_n_values:
        # Generate powerful numbers
        powerful_numbers = generate_powerful_numbers(max_n)
        
        # Find consecutive triples
        triples = find_consecutive_triples(powerful_numbers)
        
        # Build DAG structure
        A, layers = dag_powerful_sequence(powerful_numbers)
        
        # Apply FAMM delay lines
        famm_result = famm_powerful_sequence(A, layers, delay_steps=3)
        
        # 4-primitive analysis
        field = field_analysis_powerful(powerful_numbers, max_n)
        spectral = spectral_analysis_powerful(A)
        shear = shear_analysis_powerful(powerful_numbers)
        packet = packet_analysis_powerful(powerful_numbers, triples)
        
        # DAG + FAMM analysis
        dag = dag_analysis_powerful(A, layers)
        famm = famm_analysis_powerful(famm_result)
        
        results.append({
            "max_n": max_n,
            "num_powerful": len(powerful_numbers),
            "consecutive_triples": triples,
            "triple_count": len(triples),
            "conjecture_holds": len(triples) == 0,
            "field": field,
            "spectral": spectral,
            "shear": shear,
            "packet": packet,
            "dag": dag,
            "famm": famm
        })
    
    return results


def analyze_investigation(results):
    """Analyze investigation results with DAG + FAMM."""
    total = len(results)
    holds_count = sum(1 for r in results if r["conjecture_holds"])
    
    # DAG metrics
    avg_acyclic = np.mean([1 if r["dag"]["is_acyclic"] else 0 for r in results]) if results else 0.0
    avg_temporal_density = np.mean([r["dag"]["temporal_density"] for r in results]) if results else 0.0
    
    # FAMM metrics
    avg_engram_strength = np.mean([r["famm"]["engram_strength"] for r in results]) if results else 0.0
    avg_delay_diversity = np.mean([r["famm"]["delay_diversity"] for r in results]) if results else 0.0
    
    return {
        "total_tests": total,
        "conjecture_holds_count": holds_count,
        "conjecture_holds": holds_count == total if total > 0 else True,
        "dag_metrics": {
            "avg_acyclic_rate": float(avg_acyclic),
            "avg_temporal_density": float(avg_temporal_density)
        },
        "famm_metrics": {
            "avg_engram_strength": float(avg_engram_strength),
            "avg_delay_diversity": float(avg_delay_diversity)
        },
        "note": "Refined investigation using DAG structure + FAMM delay lines for powerful number sequence analysis"
    }


def main():
    print("=" * 70)
    print("  REFINED INVESTIGATION OF ERDŐS–MOLLIN–WALSH WITH DAG + FAMM")
    print("=" * 70)
    
    # Test parameters
    max_n_values = [100, 1000, 10000]
    
    print(f"\nTest parameters:")
    print(f"  max_n values: {max_n_values}")
    print(f"  Total tests: {len(max_n_values)}")
    print(f"  Graph construction: DAG (divisibility-based)")
    print(f"  Temporal sequencing: FAMM delay lines")
    print(f"  Layer assignment: Prime factor complexity")
    
    print("\n" + "=" * 70)
    print("  GENERATING POWERFUL NUMBER DAG + FAMM")
    print("=" * 70)
    
    results = investigate_erdos_mollin_walsh_refined(max_n_values)
    
    print(f"\nGenerated {len(results)} powerful number DAG + FAMM analyses")
    
    print("\n" + "=" * 70)
    print("  ANALYZING INVESTIGATION RESULTS")
    print("=" * 70)
    
    analysis = analyze_investigation(results)
    
    print(f"\nInvestigation analysis:")
    print(f"  Total tests: {analysis['total_tests']}")
    print(f"  Conjecture holds: {analysis['conjecture_holds_count']}/{analysis['total_tests']}")
    print(f"  Conjecture holds: {analysis['conjecture_holds']}")
    print(f"\n  DAG metrics:")
    print(f"    Avg acyclic rate: {analysis['dag_metrics']['avg_acyclic_rate']:.2%}")
    print(f"    Avg temporal density: {analysis['dag_metrics']['avg_temporal_density']:.2%}")
    print(f"\n  FAMM metrics:")
    print(f"    Avg engram strength: {analysis['famm_metrics']['avg_engram_strength']:.4f}")
    print(f"    Avg delay diversity: {analysis['famm_metrics']['avg_delay_diversity']:.2f}")
    print(f"  Note: {analysis['note']}")
    
    print("\n" + "=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)
    
    print("\n1. DAG structure based on divisibility:")
    print("   - Layers encode prime factor complexity")
    print("   - Edges represent divisibility relations")
    print("   - Temporal density measures cross-complexity connectivity")
    
    print("\n2. FAMM delay lines capture temporal dynamics:")
    print("   - Delay matrices capture complexity-level flow")
    print("   - Engram consolidation integrates weighted delays")
    print("   - Temporal integration measures cross-complexity coherence")
    
    print("\n3. 4-primitive framework provides structural insight:")
    print("   - Field: density and gap distribution")
    print("   - Spectral: divisibility structure")
    print("   - Shear: gap variance and clustering")
    print("   - Packet: triple encoding")
    
    # Save results
    output_data = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "max_n_values": max_n_values,
            "total_tests": len(max_n_values),
            "graph_construction": "DAG (divisibility-based)",
            "temporal_sequencing": "FAMM delay lines",
            "layer_assignment": "Prime factor complexity"
        },
        "results": results,
        "investigation_analysis": analysis,
        "primitive_insights": {
            "field": "Density and gap distribution",
            "spectral": "Divisibility structure",
            "shear": "Gap variance and clustering",
            "packet": "Triple encoding"
        },
        "dag_insights": {
            "divisibility_structure": "Edges represent divisibility relations",
            "complexity_layers": "Prime factor complexity encoding",
            "temporal_density": "Cross-complexity connectivity"
        },
        "famm_insights": {
            "complexity_flow": "Delay matrices capture complexity-level flow",
            "engram_consolidation": "Weighted delay integration",
            "temporal_integration": "Cross-complexity coherence"
        },
        "validation": {
            "status": "INVESTIGATION_COMPLETE",
            "insight": "Refined investigation using DAG structure (divisibility-based) + FAMM delay lines for powerful number sequence analysis. DAG provides divisibility structure. FAMM captures complexity-level temporal dynamics. Investigating whether consecutive triples exist in powerful number sequence with temporal structure."
        }
    }
    
    output_file = RESEARCH_STACK / "4-Infrastructure/shim/investigate_erdos_mollin_walsh_refined_results.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
