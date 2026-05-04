#!/usr/bin/env python3
"""
Equation Forest to Genome18 Encoder

Maps the 12-kernel equation forest to 6x3-bit Genome18 bins for FPGA LUT addressing.

Mapping:
- F01-F03 (entropy/compression) → mBin, neBin, sigmaBin
- F04-F07 (thermodynamic limits) → cost/failure mask (derived)
- F08-F10 (geometry/geodesics) → cBin (connectance)
- F11-F12 (load/routing) → muBin (mutation/drift), rhoBin (verification pressure)
- DIAT/AVMR/S3C/PIST bridge → encoded transition surface

Stack:
raw equation
→ F01-F12 kernel signature
→ street / bridge assignment
→ six 3-bit Genome18 bins
→ 18-bit ISA/LUT address
→ FPGA route expansion
→ PIST/witness audit
→ Lean/proof/executable check
"""

import json
import numpy as np
from typing import Dict, List, Tuple

class Genome18Encoder:
    """Encodes equation forest signatures into Genome18 addresses."""
    
    def __init__(self):
        self.bin_ranges = {
            "muBin": (0, 7),
            "rhoBin": (0, 7),
            "cBin": (0, 7),
            "mBin": (0, 7),
            "neBin": (0, 7),
            "sigmaBin": (0, 7)
        }
    
    def kernel_to_bins(self, foundation_vector: List[float]) -> Dict[str, int]:
        """
        Map 12-dimensional kernel vector to 6 bins (3 bits each).
        
        Mapping:
        - muBin: F11 (aggregate load) + F12 (routing ratio) → mutation/drift
        - rhoBin: F11 (aggregate load) - F12 (routing ratio) → verification pressure
        - cBin: F08 (metric) + F09 (connection) + F10 (geodesic) → connectance
        - mBin: F01 (local entropy) + F02 (global entropy) → compression residue
        - neBin: F03 (hierarchical entropy) → effective sample
        - sigmaBin: F01 (local entropy) - F02 (global entropy) → fitness proxy
        """
        # Extract kernel values
        f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12 = foundation_vector
        
        # Compute bin values (scaled to 0-7 range)
        muBin = self._scale_to_3bit(f11 + f12)  # routing load
        rhoBin = self._scale_to_3bit(abs(f11 - f12))  # verification pressure
        cBin = self._scale_to_3bit(f08 + f09 + f10)  # connectance
        mBin = self._scale_to_3bit(f01 + f02)  # compression residue
        neBin = self._scale_to_3bit(f03)  # effective sample
        sigmaBin = self._scale_to_3bit(abs(f01 - f02))  # fitness proxy
        
        return {
            "muBin": int(muBin),
            "rhoBin": int(rhoBin),
            "cBin": int(cBin),
            "mBin": int(mBin),
            "neBin": int(neBin),
            "sigmaBin": int(sigmaBin)
        }
    
    def _scale_to_3bit(self, value: float) -> int:
        """Scale a float value to 0-7 range (3 bits)."""
        # Clamp to 0-2 range first (typical for kernel values)
        clamped = max(0.0, min(2.0, value))
        # Scale to 0-7
        scaled = int(clamped * 3.5)
        return min(7, max(0, scaled))
    
    def bins_to_address(self, bins: Dict[str, int]) -> int:
        """
        Compute 18-bit address from 6 bins.
        
        Address calculation:
        addr = muBin * 32768 + rhoBin * 4096 + cBin * 512 + mBin * 64 + neBin * 8 + sigmaBin
        """
        addr = (
            bins["muBin"] * 32768 +
            bins["rhoBin"] * 4096 +
            bins["cBin"] * 512 +
            bins["mBin"] * 64 +
            bins["neBin"] * 8 +
            bins["sigmaBin"]
        )
        return addr
    
    def encode_equation(self, equation: Dict) -> Dict:
        """Encode a single equation into Genome18 bins and address."""
        foundation_vector = equation.get("foundation_vector", [0.0] * 12)
        
        # Map to bins
        bins = self.kernel_to_bins(foundation_vector)
        
        # Compute address
        address = self.bins_to_address(bins)
        
        return {
            "uuid": equation.get("uuid"),
            "model_name": equation.get("model_name"),
            "genome18_bins": bins,
            "genome18_address": address
        }
    
    def encode_forest(self, equations: List[Dict]) -> List[Dict]:
        """Encode all equations in the forest."""
        encoded = []
        for eq in equations:
            if eq.get("namespace") == "equation":
                encoded.append(self.encode_equation(eq))
        return encoded

def main():
    """Main entry point."""
    equations_file = "/home/allaun/Documents/Research Stack/data/equations_forest.jsonl"
    output_file = "/home/allaun/Documents/Research Stack/data/equations_forest_genome18.jsonl"
    
    # Load equations
    equations = []
    with open(equations_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    equations.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Skipping malformed line: {e}")
                    continue
    
    # Encode
    encoder = Genome18Encoder()
    encoded = encoder.encode_forest(equations)
    
    # Save
    with open(output_file, 'w') as f:
        for enc in encoded:
            f.write(json.dumps(enc) + '\n')
    
    print(f"Encoded {len(encoded)} equations to Genome18 addresses")
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    main()
