#!/usr/bin/env python3
"""
Swarm Query: GPU and Component Optimization to 80% Load

Ask the swarm to figure out how to safely maximize the entire interface
of the GPU and all other components connected together up to 80% of
total possible load.
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from infra.enhanced_integrated_swarm import EnhancedIntegratedSwarm

def main():
    print("=" * 70)
    print("SWARM QUERY: GPU and Component Optimization to 80% Load")
    print("=" * 70)
    
    swarm = EnhancedIntegratedSwarm()
    
    # Query the swarm about GPU optimization
    print("\n[1] Querying swarm about GPU knowledge...")
    gpu_knowledge = swarm.shim.swarm_gpu_knowledge()
    
    if "error" in gpu_knowledge:
        print(f"ERROR: {gpu_knowledge['error']}")
        return
    
    print("\n[2] GPU Knowledge from Swarm:")
    print(json.dumps(gpu_knowledge, indent=2))
    
    # Query about interface adoption
    print("\n[3] Querying swarm about interface adoption...")
    interface_adoption = swarm.shim.swarm_adopt_interface()
    
    if "error" in interface_adoption:
        print(f"ERROR: {interface_adoption['error']}")
        return
    
    print("\n[4] Interface Adoption from Swarm:")
    print(json.dumps(interface_adoption, indent=2))
    
    # Query about topology documentation
    print("\n[5] Querying swarm about topology documentation...")
    topology_doc = swarm.shim.swarm_document_topology()
    
    if "error" in topology_doc:
        print(f"ERROR: {topology_doc['error']}")
        return
    
    print("\n[6] Topology Documentation from Swarm:")
    print(json.dumps(topology_doc, indent=2))
    
    # Save results
    result = {
        "query": "GPU and component optimization to 80% load",
        "gpu_knowledge": gpu_knowledge,
        "interface_adoption": interface_adoption,
        "topology_documentation": topology_doc
    }
    
    output_path = Path(__file__).parent.parent.parent / "data" / "swarm_gpu_optimization_80_percent.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n[7] Results saved to: {output_path}")
    print("\n" + "=" * 70)
    print("SWARM QUERY COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
