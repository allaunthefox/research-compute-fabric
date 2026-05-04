#!/usr/bin/env python3
"""
swarm_topology_integration.py — Swarm-Topology Integration (SHIM)

# BOUNDARY: Python thin IO shim; logic in Semantics.SwarmTopology
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
    print("SWARM-TOPOLOGY INTEGRATION (LEAN-BACKED)")
    print("=" * 70)
    
    try:
        result = shim.run_swarm_topology_analysis()
        
        print("\n📊 Topology Analysis Summary:")
        print(f"  Overall Score: {result['topologyOptimizationScore']/65536:.3f}")
        print(f"  Consensus: {result['consensus']/65536*100:.1f}%")
        
        print("\n💡 Recommendations:")
        for r in result['recommendations']:
            print(f"  • {r}")
            
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE (VERIFIED VIA LEAN)")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error calling Lean module: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
