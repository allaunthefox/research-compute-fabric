#!/usr/bin/env python3
"""
MathGPT Gatekeeper — Prevents Bad Math from Entering System

REQUIREMENT: ALL equations must pass this gatekeeper before:
- Being added to math_entities.db
- Being committed to git  
- Being added to MATH_MODEL_MAP
- Being implemented in Lean
- Being published in papers

This script MUST be run before accepting ANY equation.
"""

import sys
sys.path.insert(0, '/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/LeanGPT')

from mathematical_law_conviction import MathematicalLawConviction


def main():
    print("="*70)
    print("MATHGPT GATEKEEPER — Mathematical Rigor Enforcement")
    print("="*70)
    print()
    print("This tool validates equations against physical laws BEFORE acceptance.")
    print("Any equation that violates Landauer or other laws is REJECTED.")
    print()
    
    # Examples of what should be REJECTED
    bad_examples = [
        "Φ = Σ w/lnN + Σ v/lnN",           # Old wrong formulation
        "Φ = Σ wᵢ/lnNᵢ - Σ vⱼ/lnNⱼ",      # Unicode variant
        "E = kT/lnN",                      # Inverse Landauer
    ]
    
    # Examples of what should be ACCEPTED
    good_examples = [
        "Φ = Σ w·lnN - Σ v·lnN",           # Correct cost form
        "Φ = Σ w·h/lnN - Σ v·p/lnN",      # Efficiency form (inverse ok here)
    ]
    
    math_gpt = MathematicalLawConviction()
    
    print("TESTING: Bad equations (should be REJECTED)")
    print("-"*70)
    for eq in bad_examples:
        result = math_gpt.validate_equation_rigorously(eq, "TestBuilder")
        print(f"Result: {'❌ CORRECTLY REJECTED' if not result['valid'] else '⚠️  WRONGLY ACCEPTED'}")
        print()
    
    print("TESTING: Good equations (should be ACCEPTED)")
    print("-"*70)
    for eq in good_examples:
        result = math_gpt.validate_equation_rigorously(eq, "TestBuilder")
        print(f"Result: {'✅ CORRECTLY ACCEPTED' if result['valid'] else '❌ WRONGLY REJECTED'}")
        print()
    
    # Interactive mode
    print("="*70)
    print("INTERACTIVE MODE")
    print("="*70)
    print("Enter equation to validate (or 'quit' to exit):")
    
    while True:
        print()
        equation = input("> ")
        if equation.lower() in ['quit', 'exit', 'q']:
            break
        
        result = math_gpt.validate_equation_rigorously(equation, "User")
        
        if result['valid']:
            print("\n✅ EQUATION APPROVED — Can be committed")
        else:
            print("\n❌ EQUATION REJECTED — Fix before committing")
    
    print()
    print("="*70)
    print("MathGPT Gatekeeper exiting.")
    print("Remember: Always run this before accepting equations!")
    print("="*70)


if __name__ == '__main__':
    main()
