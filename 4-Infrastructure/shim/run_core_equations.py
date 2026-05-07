#!/usr/bin/env python3
"""
Run 12 Core Equations Against 12 Ingested Theories
==================================================
Extract 12 core equations from master synthesis and check their presence
across the 12 ingested compression theories.
"""

import json
from pathlib import Path

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")
GERMANE_DIR = RESEARCH_STACK / "shared-data/data/germane/research"

# 12 core equations from the compression architecture
CORE_EQUATIONS = {
    "density_field": {
        "equation": "ρ(x⃗)",
        "description": "Semantic density field representing text as n-D manifold",
        "latex": "\\rho(\\vec{x})",
        "theories_expected": ["density_field_encoding_theory", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "morse_smale": {
        "equation": "Critical points + separatrices",
        "description": "Morse-Smale complex: topological skeleton of meaning",
        "latex": "\\text{Morse-Smale} = \\{p, r, s, v, \\text{sep}\\}",
        "theories_expected": ["density_field_encoding_theory", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "shear_matrix": {
        "equation": "A_{ij} = δ_{ij} + α_{ij}",
        "description": "Shear matrix transforming orthogonal hypercube to correlated rhomboid",
        "latex": "A_{ij} = \\delta_{ij} + \\alpha_{ij}",
        "theories_expected": ["hypercube_rhomboid_composition", "hypercube_rhomboid_hutter_prize", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "gram_matrix": {
        "equation": "G = A^T A",
        "description": "Gram matrix = compression dictionary (eigenvectors = principal directions)",
        "latex": "G = A^T A",
        "theories_expected": ["hypercube_rhomboid_composition", "hypercube_rhomboid_hutter_prize", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "gccl_packet": {
        "equation": "Γᵢ = γᵢ ⊗ χᵢ ⊗ κᵢ ⊗ τᵢ ⊗ UᵢΛᵢaᵢ ⊗ θᵢ ⊗ εᵢ",
        "description": "GCCL glyph packet with chirality, type, eigen descriptor, residual",
        "latex": "\\Gamma_i = \\gamma_i \\otimes \\chi_i \\otimes \\kappa_i \\otimes \\tau_i \\otimes U_i\\Lambda_i a_i \\otimes \\theta_i \\otimes \\varepsilon_i",
        "theories_expected": ["gccl_gec_spec_v1", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "gain_test": {
        "equation": "ΔGCL > 0",
        "description": "GCCL gain test: only compressive motifs kept",
        "latex": "\\Delta GCL > 0",
        "theories_expected": ["gccl_gec_spec_v1", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "s3c_shell": {
        "equation": "n = k² + a",
        "description": "S3C shell coordinate encoding",
        "latex": "n = k^2 + a",
        "theories_expected": ["observer_admissible_cavities_theory", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "radius_ratio": {
        "equation": "ρᵢ = s_center(i) / median(s(N(i)))",
        "description": "Radius-ratio local scale ratio → admissible motif class",
        "latex": "\\rho_i = s_{\\text{center}}(i) / \\text{median}(s(N(i)))",
        "theories_expected": ["observer_admissible_cavities_theory", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "residual_ratio": {
        "equation": "ρ = |ε| / |raw_span|",
        "description": "Residual ratio: the only number that matters",
        "latex": "\\rho = |\\varepsilon| / |\\text{raw_span}|",
        "theories_expected": ["gccl_gec_spec_v1", "unified_compression_architecture_synthesis_v1", "master_synthesis_complete_v1"]
    },
    "famm_delay": {
        "equation": "Delay = path integral through field gradient",
        "description": "FAMM delay profile = path integral through density field gradient",
        "latex": "\\text{Delay} = \\int_{\\gamma} \\nabla \\rho \\cdot d\\vec{l}",
        "theories_expected": ["unified_compression_architecture_synthesis_v1", "hippocampus_tabula_plena_combined_v1", "master_synthesis_complete_v1"]
    },
    "residual_correlation": {
        "equation": "C_{ij} = ⟨ε_i ε_j⟩",
        "description": "Residual correlation matrix for spectral decomposition",
        "latex": "C_{ij} = \\langle \\varepsilon_i \\varepsilon_j \\rangle",
        "theories_expected": ["erans_field_effect_spectrum_v1", "master_synthesis_complete_v1"]
    },
    "eigen_decomposition": {
        "equation": "C = UΛU^T",
        "description": "Eigen decomposition of residual correlation matrix",
        "latex": "C = U\\Lambda U^T",
        "theories_expected": ["hypercube_rhomboid_composition", "erans_field_effect_spectrum_v1", "master_synthesis_complete_v1"]
    }
}

# 12 compression theories (excluding non-compression entries)
THEORIES = [
    "observer_admissible_cavities_theory",
    "hypercube_rhomboid_composition",
    "hypercube_rhomboid_hutter_prize",
    "erans_enumerative_rans_reference",
    "density_field_encoding_theory",
    "gccl_gec_spec_v1",
    "unified_compression_architecture_synthesis_v1",
    "hippocampus_tabula_plena_combined_v1",
    "erans_field_effect_spectrum_v1",
    "master_synthesis_complete_v1"
]

def load_theory(theory_id):
    """Load a theory JSON file."""
    theory_file = GERMANE_DIR / f"{theory_id}.json"
    if theory_file.exists():
        with open(theory_file) as f:
            return json.load(f)
    return None

def check_equation_in_theory(equation_key, theory_data):
    """Check if an equation is present in a theory."""
    theory_str = json.dumps(theory_data, indent=2).lower()
    
    # Check for equation-specific patterns
    equation_patterns = {
        "density_field": ["rho", "density field", "semantic manifold"],
        "morse_smale": ["morse", "smale", "topological", "skeleton", "critical point"],
        "shear_matrix": ["shear", "matrix", "a_{ij}", "alpha", "delta"],
        "gram_matrix": ["gram", "g = a^t a", "eigenvector", "principal"],
        "gccl_packet": ["gamma", "chirality", "eigen", "residual", "glyph"],
        "gain_test": ["delta", "gcl", "gain", "> 0"],
        "s3c_shell": ["s3c", "shell", "k²", "k^2", "a", "mirror"],
        "radius_ratio": ["radius", "ratio", "coordination", "cn3", "cn4", "cn6"],
        "residual_ratio": ["residual", "ratio", "raw_span"],
        "famm_delay": ["famm", "delay", "gradient", "path integral"],
        "residual_correlation": ["correlation", "c_{ij}", "residual field"],
        "eigen_decomposition": ["eigen", "decompose", "u", "lambda", "c = u"]
    }
    
    patterns = equation_patterns.get(equation_key, [])
    for pattern in patterns:
        if pattern in theory_str:
            return True
    return False

def main():
    print("=" * 70)
    print("  RUNNING 12 CORE EQUATIONS AGAINST 12 COMPRESSION THEORIES")
    print("=" * 70)
    
    results = {}
    
    # Load all theories
    theory_data = {}
    for theory_id in THEORIES:
        data = load_theory(theory_id)
        if data:
            theory_data[theory_id] = data
            print(f"\n✓ Loaded: {theory_id}")
        else:
            print(f"\n✗ Missing: {theory_id}")
    
    # Check each equation against each theory
    print("\n" + "=" * 70)
    print("  EQUATION × THEORY MATRIX")
    print("=" * 70)
    
    for eq_key, eq_info in CORE_EQUATIONS.items():
        print(f"\n{eq_key}: {eq_info['equation']}")
        print(f"  {eq_info['description']}")
        print(f"  Expected in: {', '.join(eq_info['theories_expected'])}")
        print(f"  Found in:")
        
        found_in = []
        for theory_id, data in theory_data.items():
            if check_equation_in_theory(eq_key, data):
                found_in.append(theory_id)
                print(f"    ✓ {theory_id}")
            else:
                print(f"    ✗ {theory_id}")
        
        results[eq_key] = {
            "equation": eq_info["equation"],
            "description": eq_info["description"],
            "expected": eq_info["theories_expected"],
            "found": found_in,
            "coverage": len(found_in) / len(theory_data) if theory_data else 0
        }
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("  SUMMARY STATISTICS")
    print("=" * 70)
    
    total_checks = len(CORE_EQUATIONS) * len(theory_data)
    total_found = sum(len(r["found"]) for r in results.values())
    
    print(f"\nTotal equation-theory checks: {total_checks}")
    print(f"Total matches found: {total_found}")
    print(f"Coverage: {total_found}/{total_checks} = {total_found/total_checks*100:.1f}%")
    
    # Equations with full coverage
    print("\nEquations with full coverage (found in all theories):")
    for eq_key, result in results.items():
        if result["coverage"] == 1.0:
            print(f"  ✓ {eq_key}: {result['equation']}")
    
    # Equations with partial coverage
    print("\nEquations with partial coverage:")
    for eq_key, result in results.items():
        if 0 < result["coverage"] < 1.0:
            print(f"  ○ {eq_key}: {result['equation']} ({result['coverage']*100:.1f}%)")
    
    # Equations with no coverage
    print("\nEquations with no coverage:")
    for eq_key, result in results.items():
        if result["coverage"] == 0:
            print(f"  ✗ {eq_key}: {result['equation']}")
    
    # Save results
    output_file = RESEARCH_STACK / "4-Infrastructure/shim/core_equations_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    # Expected vs actual comparison
    print("\n" + "=" * 70)
    print("  EXPECTED VS ACTUAL")
    print("=" * 70)
    
    for eq_key, result in results.items():
        expected_set = set(result["expected"])
        found_set = set(result["found"])
        missing = expected_set - found_set
        unexpected = found_set - expected_set
        
        if missing or unexpected:
            print(f"\n{eq_key}:")
            if missing:
                print(f"  Missing (expected but not found): {', '.join(missing)}")
            if unexpected:
                print(f"  Unexpected (found but not expected): {', '.join(unexpected)}")
        else:
            print(f"\n{eq_key}: ✓ All expected theories found")

if __name__ == "__main__":
    main()
