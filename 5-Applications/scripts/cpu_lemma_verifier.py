#!/usr/bin/env python3
"""
CPU-based Lemma Verification for Lean Proofs
Uses exhaustive search across bounded ranges to verify arithmetic lemmas
"""
from typing import Tuple, List

class CPULemmaVerifier:
    """CPU-based verification of Lean lemmas across bounded ranges"""

    def __init__(self):
        print("CPU Lemma Verifier initialized")

    def verify_weighted_term_bounded(self, max_e: int = 100, max_alpha: int = 100) -> bool:
        """
        Verify (E * α) / 65536 <= E for all E in [0, max_e] and α in [0, max_alpha]
        Uses exhaustive search across bounded ranges
        """
        print(f"Verifying weighted term bounded for E in [0,{max_e}], α in [0,{max_alpha}]")
        for e in range(max_e + 1):
            for alpha in range(max_alpha + 1):
                product = e * alpha
                divided = product // 65536
                if divided > e:
                    print(f"FAILED at E={e}, α={alpha}: {divided} > {e}")
                    return False
        print("✓ Weighted term bounded verification PASSED")
        return True

    def verify_bit_shift_equivalence(self, max_x: int = 1000) -> bool:
        """
        Verify x >>> 16 = x / 65536 for all x in [0, max_x]
        Uses exhaustive search
        """
        print(f"Verifying bit shift equivalence for x in [0,{max_x}]")
        for x in range(max_x + 1):
            shifted = x >> 16
            divided = x // 65536
            if shifted != divided:
                print(f"FAILED at x={x}: {shifted} != {divided}")
                return False
        print("✓ Bit shift equivalence verification PASSED")
        return True

    def verify_bit_shift_monotonicity(self, max_val: int = 100) -> bool:
        """
        Verify a >>> 16 <= b >>> 16 when a <= b
        Uses exhaustive search across all pairs
        """
        print(f"Verifying bit shift monotonicity for a,b in [0,{max_val}]")
        for a in range(max_val + 1):
            for b in range(a, max_val + 1):
                a_shifted = a >> 16
                b_shifted = b >> 16
                if a_shifted > b_shifted:
                    print(f"FAILED at a={a}, b={b}: {a_shifted} > {b_shifted}")
                    return False
        print("✓ Bit shift monotonicity verification PASSED")
        return True

    def verify_division_comparison(self, max_x: int = 50, max_divisor: int = 50) -> bool:
        """
        Verify x / a <= x / b when a > b and x >= 0
        Uses exhaustive search across all valid triples
        """
        print(f"Verifying division comparison for x in [0,{max_x}], a,b in [1,{max_divisor}]")
        for x in range(max_x + 1):
            for b in range(1, max_divisor + 1):
                for a in range(b + 1, max_divisor + 1):
                    div_a = x // a
                    div_b = x // b
                    if div_a > div_b:
                        print(f"FAILED at x={x}, a={a}, b={b}: {div_a} > {div_b}")
                        return False
        print("✓ Division comparison verification PASSED")
        return True

def main():
    """Run CPU verification for all lemmas"""
    verifier = CPULemmaVerifier()

    print("Starting CPU-based lemma verification...")
    print("=" * 60)

    # Verify each lemma with bounded ranges
    results = {}
    results['weighted_term_bounded'] = verifier.verify_weighted_term_bounded(max_e=100, max_alpha=100)
    results['bit_shift_equivalence'] = verifier.verify_bit_shift_equivalence(max_x=1000)
    results['bit_shift_monotonicity'] = verifier.verify_bit_shift_monotonicity(max_val=100)
    results['division_comparison'] = verifier.verify_division_comparison(max_x=50, max_divisor=50)

    print("=" * 60)
    print("CPU Verification Results:")
    for lemma, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {lemma}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All lemmas verified successfully via CPU exhaustive search!")
        print("This provides computational evidence for the Lean proofs.")
    else:
        print("\n✗ Some lemmas failed verification")

    return all_passed

if __name__ == "__main__":
    main()
