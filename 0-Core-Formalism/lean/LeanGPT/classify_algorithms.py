#!/usr/bin/env python3
"""
Improved algorithm classification system
Examines unclassified algorithms and assigns them to appropriate OTOM domains
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Enhanced domain classification rules
DOMAIN_RULES = {
    "core": {
        "file_patterns": ["Bind", "Canon", "Metatype", "Transition", "Protocol", "Orchestrate", "Tape", "Pbacs"],
        "name_patterns": ["computeConfidence", "computeAngularMomentum", "computeFlowLine", "computeBetti", "computeScore", "computeInvariants", "computeSpeedup"],
        "namespace_patterns": ["Semantics.Bind", "Semantics.Canon", "Semantics.Metatype", "Semantics.Tape", "Semantics.Pbacs"]
    },
    "compression": {
        "file_patterns": ["Compression", "Genomic", "Landauer"],
        "name_patterns": ["compress", "encode", "decode", "chromatin", "conserved"],
        "namespace_patterns": ["Semantics.Compression", "Semantics.Genomic"]
    },
    "spatialVLSI": {
        "file_patterns": ["AVMR", "FlagSort", "ThermodynamicSort", "VLsI", "Spatial", "NGemetry"],
        "name_patterns": ["computeCamera", "computeDepth", "computeOrdering", "computeObjectDistance", "spatial", "euclideanDistance", "manhattanDistance"],
        "namespace_patterns": ["Semantics.Spatial", "Semantics.AVMR", "Semantics.NGemetry"]
    },
    "diffusionFlow": {
        "file_patterns": ["Diffusion", "Entropy", "Hybrid", "Surface"],
        "name_patterns": ["diffusion", "entropy", "hybrid", "surface"],
        "namespace_patterns": ["Semantics.Diffusion", "Semantics.Entropy"]
    },
    "memoryState": {
        "file_patterns": ["SSMS", "Memory", "Fuzzy"],
        "name_patterns": ["memory", "state", "fuzzy"],
        "namespace_patterns": ["Semantics.Memory", "Semantics.SSMS"]
    },
    "pistShell": {
        "file_patterns": ["PIST", "Pist", "Bracket", "Shell"],
        "name_patterns": ["bracket", "shell", "pist"],
        "namespace_patterns": ["Semantics.PIST", "Semantics.Bracket"]
    },
    "fieldPhysics": {
        "file_patterns": ["Field", "Rotation", "Triangle", "Waveprobe", "Curvature", "NBody", "Physics"],
        "name_patterns": ["field", "rotation", "triangle", "waveprobe", "curvature", "laplacian", "gravitational", "hamiltonian", "kinetic", "potential", "energy"],
        "namespace_patterns": ["Semantics.Field", "Semantics.Rotation", "Semantics.Triangle", "ExtensionScaffold/Physics"]
    },
    "evolutionSearch": {
        "file_patterns": ["Search", "Find", "Prime", "Lut"],
        "name_patterns": ["search", "find", "prime", "optimize", "solve", "update", "iterate"],
        "namespace_patterns": ["Semantics.Search", "Semantics.Prime"]
    },
    "braidAlgebra": {
        "file_patterns": ["Braid", "Strand", "Cross"],
        "name_patterns": ["braid", "strand", "cross"],
        "namespace_patterns": ["Semantics.Braid"]
    },
    "kernelDomain": {
        "file_patterns": ["Kernel", "Domain"],
        "name_patterns": ["kernel", "domain"],
        "namespace_patterns": ["Semantics.Kernel", "Semantics.Domain"]
    },
    "cognitiveControl": {
        "file_patterns": ["Agent", "Orchestration", "Control"],
        "name_patterns": ["agent", "orchestration", "control", "task"],
        "namespace_patterns": ["Semantics.Agent", "Semantics.Orchestration"]
    },
    "geometry": {
        "file_patterns": ["Geometry", "Manifold", "Topology", "BumpFunction"],
        "name_patterns": ["geometry", "manifold", "topology", "curvature", "bump", "fiber"],
        "namespace_patterns": ["Semantics.Geometry", "Semantics.Manifold", "Mathlib/Geometry"]
    },
    "thermodynamic": {
        "file_patterns": ["Thermodynamic", "Sort", "Energy"],
        "name_patterns": ["thermodynamic", "sort", "energy"],
        "namespace_patterns": ["Semantics.Thermodynamic"]
    },
    "diagnostic": {
        "file_patterns": ["Test", "Diagnostic", "Server", "Linter"],
        "name_patterns": ["test", "diagnostic", "server", "linter"],
        "namespace_patterns": ["Semantics.Test", "Semantics.Diagnostic", "ExtensionScaffold/ENE"]
    },
    "extensionScaffold": {
        "file_patterns": ["ExtensionScaffold"],
        "name_patterns": [],
        "namespace_patterns": ["ExtensionScaffold"]
    }
}

def classify_algorithm(algorithm: dict) -> str:
    """Classify a single algorithm into a domain"""
    file_path = algorithm['file']
    name = algorithm['name']
    
    # Check each domain's rules
    for domain, rules in DOMAIN_RULES.items():
        score = 0
        
        # Check file patterns
        for pattern in rules['file_patterns']:
            if pattern in file_path:
                score += 3
        
        # Check name patterns
        for pattern in rules['name_patterns']:
            if pattern.lower() in name.lower():
                score += 2
        
        # Check namespace patterns (from file path)
        for pattern in rules['namespace_patterns']:
            if pattern.replace("Semantics.", "").lower() in file_path.lower():
                score += 1
        
        if score > 0:
            return domain
    
    return "unclassified"

def classify_unclassified(results_file: str):
    """Classify unclassified algorithms using enhanced rules"""
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    algorithms = results['algorithms']
    
    # Classify all algorithms
    domain_groups = defaultdict(list)
    
    for algo in algorithms:
        domain = classify_algorithm(algo)
        domain_groups[domain].append(algo)
    
    # Print summary
    print("=" * 60)
    print("IMPROVED ALGORITHM CLASSIFICATION")
    print("=" * 60)
    
    total_algorithms = len(algorithms)
    
    for domain in sorted(domain_groups.keys()):
        count = len(domain_groups[domain])
        percentage = (count / total_algorithms) * 100
        print(f"\n{domain.upper():20} | {count:4} algorithms | {percentage:5.1f}%")
        
        # Show top 5 algorithms in this domain
        print("-" * 60)
        for algo in sorted(domain_groups[domain], key=lambda x: x['name'])[:5]:
            print(f"  - {algo['name']:30} | {algo['file']}")
        
        if len(domain_groups[domain]) > 5:
            print(f"  ... and {len(domain_groups[domain]) - 5} more")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {total_algorithms} algorithms across {len(domain_groups)} domains")
    
    # Calculate improvement
    unclassified_count = len(domain_groups.get("unclassified", []))
    unclassified_pct = (unclassified_count / total_algorithms) * 100
    print(f"UNCLASSIFIED: {unclassified_count} algorithms ({unclassified_pct:.1f}%)")
    print("=" * 60)
    
    # Save improved classification
    improved_results = {
        "domain_summary": {
            domain: {
                "count": len(algos),
                "percentage": (len(algos) / total_algorithms) * 100,
                "algorithms": [algo['name'] for algo in algos]
            }
            for domain, algos in domain_groups.items()
        },
        "total_algorithms": total_algorithms,
        "total_domains": len(domain_groups),
        "unclassified_percentage": unclassified_pct,
        "timestamp": results['timestamp']
    }
    
    output_file = Path(results_file).parent / "algorithms_classified.json"
    with open(output_file, 'w') as f:
        json.dump(improved_results, f, indent=2)
    
    print(f"\nImproved classification saved to {output_file}")

if __name__ == "__main__":
    results_file = "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT/bootstrap_results.json"
    classify_unclassified(results_file)
