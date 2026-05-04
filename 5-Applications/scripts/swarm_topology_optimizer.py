#!/usr/bin/env python3
"""
swarm_topology_optimizer.py — Swarm Topology Optimizer (SHIM)

# BOUNDARY: Python thin IO shim; logic in Semantics.TopologyOptimization
"""

import sys
from pathlib import Path

# Add infra to path
sys.path.append(str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))
from lean_unified_shim import LeanUnifiedShim


def main():
    """Main function calling Lean via unified shim."""
    shim = LeanUnifiedShim()
    print("=" * 70)
    print("SWARM TOPOLOGY OPTIMIZER (LEAN-BACKED)")
    print("=" * 70)
    
    try:
        result = shim.run_topology_optimization()
        
        print("\n📊 Topology Optimization State:")
        print(f"  Nodes: {len(result['nodes'])}")
        print(f"  Tasks: {len(result['tasks'])}")
        
        print("\n" + "=" * 70)
        print("OPTIMIZATION COMPLETE (VERIFIED VIA LEAN)")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error calling Lean module: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
