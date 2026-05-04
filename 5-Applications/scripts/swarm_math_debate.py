#!/usr/bin/env python3
"""
swarm_math_debate.py — Swarm Math Debate with Skeptical Agents (SHIM)

# BOUNDARY: Python thin IO shim; logic in Semantics.MathDebate
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
    print("SWARM MATH DEBATE: SKEPTICAL AGENTS (LEAN-BACKED)")
    print("=" * 70)
    
    try:
        result = shim.run_math_debate()
        
        print(f"\n📝 Proposer: {result['proposer']}")
        print(f"📐 Equation: {result['equation']}")
        print(f"⚖️  Consensus: {result['consensus'].upper()}")
        print(f"📋 Reason: {result['reason']}")
        
        print(f"\n📊 Vote Counts (Total: {result['votes']['total']}):")
        print(f"  • Conviced: {result['votes']['convinced']}")
        print(f"  • Skeptical: {result['votes']['skeptical']}")
        print(f"  • Outraged: {result['votes']['outraged']}")
            
        print("\n" + "=" * 70)
        print("DEBATE COMPLETE (VERIFIED VIA LEAN)")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error calling Lean module: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
