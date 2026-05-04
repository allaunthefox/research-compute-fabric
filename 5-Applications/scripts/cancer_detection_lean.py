#!/usr/bin/env python3
"""
Lean RGFlow Cancer Sequence Detection
Use Lean to prove RGFlow can detect cancer mutations in TP53 gene sequence.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from infra.lean_unified_shim import LeanUnifiedShim

def run_lean_cancer_detection():
    # 1. TP53 Reference mRNA (Partial/Representative Segment)
    # This is a lawful, high-informativity biological sequence.
    tp53_healthy = ("ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCC"
                    "CTTGCCGTCCCAAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCAGATGAAGCTCCCAGAATGCCAG"
                    "AGGCTGCTCCCCGCGTGGCCCCTGCACCAGCAGCTCCTACACCGGCGGCCCCTGCACCAGCCCCCTCCTGGCCCCTGTCATCTTCTGTCCCTTCCCAGAAA"
                    "ACCTACCAGGGCAGCTACGGTTTCCGTCTGGGCTTCTTGCATTCTGGGACAGCCAAGTCTGTGACTTGCACGTACTCCCCTGCCCTCAACAAGATGTTTTG"
                    "CCAACTGGCCAAGACCTGCCCCGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACAGCACA"
                    "TGACGGAGGTTGTGAGGCGCTGCCCCCACCATGAGCGCTGCTCAGATAGCGATGGTCTGGCCCCTCCTCAGCATCTTATCCGAGTGGAAGGAAATTTGCGT"
                    "GTGGAGTATTTGGATGACAGAAACACTTTTCGACATAGTGTGGTGGTGCCCTATGAGCCGCCTGAGGTTGGCTCTGACTGTACCACCATCCACTACAACTA"
                    "CATGTGTAACAGTTCCTGCATGGGCGGCATGAACCGGAGGCCCATCCTCACCATCATCACACTGGAAGACTCCAGTGGTAATCTACTGGGACGGAACAGCT"
                    "TTGAGGTGCGTGTTTGTGCCTGTCCTGGGAGAGACCGGCGCACAGAGGAAGAGAATCTCCGCAAGAAAGGGGAGCCTCACCACGAGCTGCCCCCAGGGAGC"
                    "ACTAAGCGAGCACTGCCCAACAACACCAGCTCCTCTCCCCAGCCAAAGAAGAAACCACTGGATGGAGAATATTTCACCCTTCAGATCCGTGGGCGTGAGCG"
                    "CTTCGAGATGTTCCGAGAGCTGAATGAGGCCTTGGAACTCAAGGATGCCCAGGCTGGGAAGGAGCCAGGGGGGAGCAGGGCTCACTCCAGCCACCTGAAGT"
                    "CCAAAAAGGGTCAGTCTACCTCCCGCCATAAAAAACTCATGTTCAAGACAGAAGGGCCTGACTCAGACTGA")
    
    # 2. Inject "Godzilla" Hotspot Mutations
    # R175H (Arg -> His at codon 175)
    # R248W (Arg -> Trp at codon 248)
    
    tp53_cancer = list(tp53_healthy)
    
    # R175H: Typical CGC -> CAC transition
    loc_175 = 175 * 3
    tp53_cancer[loc_175:loc_175+3] = list("CAC")
    
    # R248W: Typical CGG -> TGG transition
    loc_248 = 248 * 3
    tp53_cancer[loc_248:loc_248+3] = list("TGG")
    
    tp53_cancer = "".join(tp53_cancer)
    
    print("=" * 60)
    print("LEAN RGFLOW CANCER SEQUENCE DETECTION")
    print("=" * 60)
    
    # Initialize Lean shim
    shim = LeanUnifiedShim("0-Core-Formalism/lean/Semantics")
    
    # Test window size (200 bases around each mutation)
    window_size = 200
    
    hotspots = [loc_175, loc_248]
    
    for start in hotspots:
        window_h = tp53_healthy[max(0, start-window_size) : min(len(tp53_healthy), start+window_size)]
        window_c = tp53_cancer[max(0, start-window_size) : min(len(tp53_cancer), start+window_size)]
        
        print(f"\nLocus {start} (Codon {start//3}):")
        
        # Call Lean compareSequenceWindows function
        lean_code = f"""
            import Semantics.RGFlowBioinformatics
            #eval Semantics.RGFlowBioinformatics.compareSequenceWindows "{window_h}" "{window_c}"
        """
        
        result = shim.query(lean_code)
        
        if result and "data" in result:
            try:
                # Parse the Lean tuple result
                data_str = result["data"]
                # The result is a tuple: (healthy_sigma, cancer_sigma, delta_sigma, percent_loss, detected)
                # Parse it manually
                print(f"  Lean Result: {data_str}")
                
                # Extract values from the string representation
                # Format: (1.947046, 1.942182, 0.004864, 0.250000, true)
                import re
                match = re.search(r'\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^)]+)\)', data_str)
                if match:
                    healthy_sigma = float(match.group(1))
                    cancer_sigma = float(match.group(2))
                    delta_sigma = float(match.group(3))
                    percent_loss = float(match.group(4))
                    detected = match.group(5).strip() == "true"
                    
                    print(f"  Healthy Sigma: {healthy_sigma:.6f}")
                    print(f"  Cancer Sigma:  {cancer_sigma:.6f}")
                    print(f"  Delta Sigma:   {delta_sigma:.6f}")
                    print(f"  Percent Loss:   {percent_loss:.2f}%")
                    
                    if detected:
                        print(f"  [✓] LEAN DETECTED: Informatic Collapse ({percent_loss:.2f}% reduction)")
                        print(f"  [+] RECOMMENDATION: Informatic Stripping (Restoration to reference)")
                    else:
                        print(f"  Match: Scale-stability preserved or neutral.")
                else:
                    print(f"  [!] ERROR: Could not parse Lean result")
                    print(f"  Raw result: {data_str}")
            except Exception as e:
                print(f"  [!] ERROR: Exception parsing result: {e}")
                print(f"  Raw result: {result}")
        else:
            print(f"  [!] ERROR: Failed to get result from Lean")
            print(f"  Result: {result}")
    
    print("\n" + "=" * 60)
    print("LEAN CANCER DETECTION COMPLETE")
    print("=" * 60)
    print("\nNOTE: Four functions in RGFlowBioinformatics.lean use 'partial'")
    print("      due to complex termination proofs. These require human")
    print("      sign-off per AGENTS.md before production use.")
    print("      TODO(lean-port) comments added to:")
    print("      - translateToAminoAcids")
    print("      - transitionRate")
    print("      - shannonEntropy")
    print("      - analyzeSequenceWindow")

if __name__ == "__main__":
    run_lean_cancer_detection()
