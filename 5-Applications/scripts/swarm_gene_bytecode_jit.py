#!/usr/bin/env python3
"""
swarm_gene_bytecode_jit.py — Swarm-Designed Gene Bytecode JIT Compiler (SHIM)

# BOUNDARY: Python thin IO shim; logic in Semantics.GeneBytecodeJIT
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
    print("SWARM GENE BYTECODE JIT COMPILER (LEAN-BACKED)")
    print("=" * 70)
    
    try:
        result = shim.run_gene_bytecode_jit()
        
        print(f"\n📑 Program ID: {result['programId']}")
        print(f"⚙️  Optimization Level: {result['optimizationLevel']}")
        print(f"⏱️  Execution Time: {result['executionTimeMs']/65536:.4f} ms")
        print(f"💾 Memory Footprint: {result['memoryFootprintKb']} KB")
        
        print("\n🛡️  Triumvirate Validation:")
        print(f"  • Builder Verified: {'✅' if result['builderVerified'] else '❌'}")
        print(f"  • Warden Validated: {'✅' if result['wardenValidated'] else '❌'}")
        print(f"  • Judge Approved: {'✅' if result['judgeApproved'] else '❌'}")
            
        print("\n" + "=" * 70)
        print("COMPILATION COMPLETE (VERIFIED VIA LEAN)")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error calling Lean module: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
