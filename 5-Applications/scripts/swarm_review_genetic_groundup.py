#!/usr/bin/env python3
"""
swarm_review_genetic_groundup.py — Formal Triumvirate Code Review System (SHIM)

# BOUNDARY: Python thin IO shim; logic in Semantics.SwarmCodeReview
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
    print("SWARM CODE REVIEW: GENETIC GROUNDUP (LEAN-BACKED)")
    print("=" * 70)
    
    try:
        result = shim.run_swarm_code_review()
        
        print(f"\n📑 Review ID: {result['reviewId']}")
        print(f"⚖️  Verdict: {result['verdict'].upper()}")
        print(f"📊 Quality Score: {result['qualityScore']/65536*100:.1f}%")
        
        print("\n🔍 Findings:")
        if not result['findings']:
            print("  ✅ No critical findings remaining.")
        else:
            for f in result['findings']:
                print(f"  • [{f['severity'].upper()}] {f['category']}: {f['issue']}")
                print(f"    State: {f['state']}")
                print(f"    Evidence: {f['evidence']}")
            
        print("\n" + "=" * 70)
        print("REVIEW COMPLETE (VERIFIED VIA LEAN)")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error calling Lean module: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
