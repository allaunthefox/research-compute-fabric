#!/usr/bin/env python3
"""
Group algorithms by OTOM domain from bootstrap results
"""

import json
from pathlib import Path
from collections import defaultdict

# OTOM domain mapping based on file paths
DOMAIN_MAPPING = {
    "core": [
        "Bind.lean", "Metatype.lean", "Transition.lean", "Protocol.lean",
        "Canon.lean", "Orchestrate.lean", "Hutter.lean", "MasterEquation.lean"
    ],
    "compression": [
        "GenomicCompression.lean", "CrossModalCompression.lean", "CompressionLossComparison.lean",
        "CompressionMechanics.lean", "CompressionMechanicsBridge.lean", "CompressionControl.lean",
        "CompressionEvidence.lean", "LandauerCompression.lean"
    ],
    "spatialVLSI": [
        "AVMR.lean", "FlagSort.lean", "ThermodynamicSort.lean", "VLsIPartition.lean",
        "SpatialEvo.lean", "OrderedFieldTokens.lean"
    ],
    "diffusionFlow": [
        "DiffusionSNRBias.lean", "HybridConvergence.lean", "SurfaceCore.lean",
        "EntropyMeasures.lean", "ExperienceCompression.lean"
    ],
    "memoryState": [
        "SSMS.lean", "SSMS_nD.lean", "DomainKernel.lean", "FuzzyAssociation.lean"
    ],
    "pistShell": [
        "PIST.lean", "PistSimulation.lean", "PistBridge.lean", "BracketShellCount.lean",
        "BraidBracket.lean", "BraidStrand.lean", "BraidCross.lean"
    ],
    "fieldPhysics": [
        "FieldSolver.lean", "RotationQUBO.lean", "TriangleManifold.lean",
        "Waveprobe.lean", "Curvature.lean", "CalibratedKernel.lean"
    ],
    "evolutionSearch": [
        "Metatype.lean", "PrimeLut.lean", "SpatialEvo.lean", "Search.lean"
    ],
    "braidAlgebra": [
        "BraidBracket.lean", "BraidStrand.lean", "BraidCross.lean"
    ],
    "kernelDomain": [
        "DomainKernel.lean", "PistBridge.lean", "PistSimulation.lean"
    ],
    "cognitiveControl": [
        "ResearchAgent.lean", "AgenticOrchestration.lean", "Orchestrate.lean"
    ],
    "geometry": [
        "Curvature.lean", "TriangleManifold.lean", "SpatialEvo.lean"
    ],
    "thermodynamic": [
        "ThermodynamicSort.lean", "EntropyMeasures.lean"
    ],
    "diagnostic": [
        "Tests.lean", "SearchServer.lean"
    ]
}

def map_file_to_domain(file_path: str) -> str:
    """Map a file path to its OTOM domain"""
    file_name = file_path.split("/")[-1]
    file_lower = file_path.lower()
    
    for domain, files in DOMAIN_MAPPING.items():
        if file_name in files:
            return domain
    
    # Enhanced default mapping based on directory structure and file patterns
    if "braid" in file_lower:
        return "braidAlgebra"
    elif "compression" in file_lower or "genomic" in file_lower:
        return "compression"
    elif "field" in file_lower or "rotation" in file_lower or "triangle" in file_lower:
        return "fieldPhysics"
    elif "pist" in file_lower or "pist" in file_name:
        return "pistShell"
    elif "spatial" in file_lower or "vlsi" in file_lower or "ordering" in file_lower:
        return "spatialVLSI"
    elif "memory" in file_lower or "ssms" in file_lower:
        return "memoryState"
    elif "diffusion" in file_lower or "entropy" in file_lower or "hybrid" in file_lower:
        return "diffusionFlow"
    elif "search" in file_lower or "find" in file_lower or "prime" in file_lower:
        return "evolutionSearch"
    elif "geometry" in file_lower or "curvature" in file_lower:
        return "geometry"
    elif "thermodynamic" in file_lower or "sort" in file_lower:
        return "thermodynamic"
    elif "kernel" in file_lower:
        return "kernelDomain"
    elif "agent" in file_lower or "orchestration" in file_lower:
        return "cognitiveControl"
    elif "bind" in file_lower or "canon" in file_lower or "metatype" in file_lower:
        return "core"
    elif "extension" in file_lower:
        # Map extension scaffold files to their parent domains
        if "physics" in file_lower:
            return "fieldPhysics"
        elif "compression" in file_lower:
            return "compression"
        else:
            return "core"
    else:
        return "unclassified"

def group_algorithms_by_domain(results_file: str):
    """Group algorithms from bootstrap results by domain"""
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    algorithms = results['algorithms']
    
    # Group by domain
    domain_groups = defaultdict(list)
    
    for algo in algorithms:
        domain = map_file_to_domain(algo['file'])
        domain_groups[domain].append(algo)
    
    # Print summary
    print("=" * 60)
    print("ALGORITHMS GROUPED BY OTOM DOMAIN")
    print("=" * 60)
    
    total_algorithms = len(algorithms)
    
    for domain in sorted(domain_groups.keys()):
        count = len(domain_groups[domain])
        percentage = (count / total_algorithms) * 100
        print(f"\n{domain.upper():20} | {count:4} algorithms | {percentage:5.1f}%")
        
        # Show top 5 algorithms in this domain
        print("-" * 60)
        for algo in sorted(domain_groups[domain], key=lambda x: x['name'])[:5]:
            print(f"  - {algo['name']:30} | {algo['complexity']:6} | {algo['type']:10}")
        
        if len(domain_groups[domain]) > 5:
            print(f"  ... and {len(domain_groups[domain]) - 5} more")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {total_algorithms} algorithms across {len(domain_groups)} domains")
    print("=" * 60)
    
    # Save grouped results
    grouped_results = {
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
        "timestamp": results['timestamp']
    }
    
    output_file = Path(results_file).parent / "algorithms_by_domain.json"
    with open(output_file, 'w') as f:
        json.dump(grouped_results, f, indent=2)
    
    print(f"\nGrouped results saved to {output_file}")

if __name__ == "__main__":
    results_file = "/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT/bootstrap_results.json"
    group_algorithms_by_domain(results_file)
