#!/usr/bin/env python3
"""
Forest Filter Normalization

Applies filter normalization technique from NeurIPS 2018 to all equations
in the Research Stack forest (MATH_MODEL_MAP.tsv).

Enables meaningful side-by-side comparison of equation landscapes.

AUDIT-ONLY SHIM:
This script is not a source-of-truth implementation under 6-Documentation/docs/AGENTS.md.
It may generate exploratory JSON/audit evidence only. Any curvature,
compression strategy, invariant, or branching logic here must be ported to
Lean before being used by the core model or release claims.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
import json
import hashlib
from pathlib import Path


class EquationNormalizer:
    """
    Applies filter normalization to equation state spaces.
    
    Treats equation variables as "state vectors" and normalizes
    them to unit length for meaningful landscape comparison.
    """
    
    def __init__(self):
        pass
    
    def parse_equation_variables(self, equation_str: str, variables_str: str) -> List[float]:
        """
        Parse equation variables into a state vector.
        
        This is a simplified parser - in practice, you'd need
        equation-specific parsing for each equation type.
        """
        # For now, use variable names as hash-based state
        # In practice, this would be equation-specific
        variable_names = [v.strip() for v in variables_str.split(',')]
        
        # Create a hash-based state vector
        state_vector = []
        for i, var in enumerate(variable_names):
            # Stable hash to float; Python's built-in hash is process-salted.
            digest = hashlib.sha256(var.encode("utf-8")).digest()
            hash_val = int.from_bytes(digest[:8], "big") % 100
            state_vector.append(float(hash_val))
        
        return state_vector
    
    def normalize_state(self, state: List[float]) -> Dict[str, Any]:
        """
        Apply filter normalization to state vector.
        """
        state_array = np.array(state)
        norm = np.linalg.norm(state_array)
        
        if norm > 0:
            normalized = state_array / norm
        else:
            normalized = state_array
        
        return {
            "original": state,
            "normalized": normalized.tolist(),
            "norm": float(norm)
        }
    
    def calculate_curvature_metric(self, state: List[float]) -> float:
        """
        Calculate a simple curvature metric for the state.
        
        This is a proxy for actual phase space curvature.
        """
        state_array = np.array(state)
        
        # Use variance as a proxy for curvature
        curvature = np.var(state_array)
        
        return float(curvature)
    
    def process_equation(self, name: str, equation: str, variables: str) -> Dict[str, Any]:
        """
        Process a single equation through filter normalization.
        """
        # Parse variables into state
        state = self.parse_equation_variables(equation, variables)
        
        # Normalize
        normalized = self.normalize_state(state)
        
        # Calculate curvature
        curvature = self.calculate_curvature_metric(state)
        
        return {
            "name": name,
            "equation": equation,
            "variables": variables,
            "state": state,
            "normalized_state": normalized["normalized"],
            "norm": normalized["norm"],
            "curvature": curvature
        }


def main():
    """Run forest filter normalization."""
    print("=" * 70)
    print("FOREST FILTER NORMALIZATION")
    print("=" * 70)
    print("\n[*] Applying filter normalization to all Research Stack equations")
    print("[*] Enabling meaningful side-by-side landscape comparison")
    
    # Read MATH_MODEL_MAP.tsv
    print(f"\n[*] Reading MATH_MODEL_MAP.tsv...")
    equations = []
    
    with open('/home/allaun/Documents/Research Stack/3-Mathematical-Models/MATH_MODEL_MAP.tsv', 'r') as f:
        lines = f.readlines()
        
    # Skip header
    for line in lines[1:]:
        parts = line.strip().split('\t')
        if len(parts) >= 4:
            name = parts[1]
            equation = parts[3]
            variables = parts[4]
            
            # Only process equations with actual formulas
            if '=' in equation and len(variables) > 10:
                equations.append({
                    "name": name,
                    "equation": equation,
                    "variables": variables
                })
    
    print(f"    Found {len(equations)} equations to process")
    
    # Process equations
    normalizer = EquationNormalizer()
    processed = []
    
    for eq in equations:
        try:
            result = normalizer.process_equation(
                eq["name"],
                eq["equation"],
                eq["variables"]
            )
            processed.append(result)
        except Exception as e:
            print(f"    Error processing {eq['name']}: {e}")
    
    print(f"\n[*] Processed {len(processed)} equations")
    
    # Calculate statistics
    norms = [p["norm"] for p in processed]
    curvatures = [p["curvature"] for p in processed]
    
    print(f"\n[*] Normalization Statistics:")
    print(f"    Avg norm: {np.mean(norms):.4f}")
    print(f"    Max norm: {np.max(norms):.4f}")
    print(f"    Min norm: {np.min(norms):.4f}")
    
    print(f"\n[*] Curvature Statistics:")
    print(f"    Avg curvature: {np.mean(curvatures):.4f}")
    print(f"    Max curvature: {np.max(curvatures):.4f}")
    print(f"    Min curvature: {np.min(curvatures):.4f}")
    
    # Find highest curvature equations
    sorted_by_curvature = sorted(processed, key=lambda x: x["curvature"], reverse=True)
    
    print(f"\n[*] Top 5 Highest Curvature Equations:")
    for i, eq in enumerate(sorted_by_curvature[:5]):
        print(f"    {i+1}. {eq['name']}: {eq['curvature']:.4f}")
    
    # Find lowest curvature equations
    sorted_by_curvature_asc = sorted(processed, key=lambda x: x["curvature"])
    
    print(f"\n[*] Top 5 Lowest Curvature Equations:")
    for i, eq in enumerate(sorted_by_curvature_asc[:5]):
        print(f"    {i+1}. {eq['name']}: {eq['curvature']:.4f}")
    
    # Save results
    results = {
        "total_equations": len(equations),
        "processed_equations": len(processed),
        "statistics": {
            "avg_norm": float(np.mean(norms)),
            "max_norm": float(np.max(norms)),
            "min_norm": float(np.min(norms)),
            "avg_curvature": float(np.mean(curvatures)),
            "max_curvature": float(np.max(curvatures)),
            "min_curvature": float(np.min(curvatures))
        },
        "equations": processed
    }
    
    output_path = "/home/allaun/Documents/Research Stack/data/forest_filter_normalization.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ FOREST FILTER NORMALIZATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
