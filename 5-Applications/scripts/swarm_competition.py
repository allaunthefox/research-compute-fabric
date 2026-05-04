#!/usr/bin/env python3
"""
swarm_competition.py — Swarm Competition System (SHIM)

# BOUNDARY: Python thin IO shim; logic in Semantics.SwarmCompetition
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
    print("SWARM COMPETITION SYSTEM (LEAN-BACKED)")
    print("=" * 70)
    
    try:
        result = shim.run_swarm_competition()
        
        print(f"\n🏆 Current Leader: {result['currentLeader'] if result['currentLeader'] else 'None'}")
        print(f"  Generation: {result['currentGeneration']}")
        
        print("\n" + "=" * 70)
        print("COMPETITION REVIEW COMPLETE (VERIFIED VIA LEAN)")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error calling Lean module: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
