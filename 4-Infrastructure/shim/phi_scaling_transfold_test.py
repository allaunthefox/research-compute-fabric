#!/usr/bin/env python3
"""
Φ-Scaling Transfold Equation Tests

Tests the corrected Φ-scaling equations against known outcomes:
1. LTEE fitness trajectory
2. Drake's rule (mutation rate vs genome size)
3. Fractal dimension of genetic networks

Corrected equation:
P ∝ S^{1/2} · lambda_phi^{1.44042} · exp(-gamma · DeltaE_eff/kT)

where:
- phi = (1 + sqrt(5)) / 2 ≈ 1.618
- lambda_phi = phi^2 ≈ 2.618
- D_f = log(2) / log(phi) ≈ 1.44042
"""

import math
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Constants
PHI = (1 + math.sqrt(5)) / 2
LAMBDA_PHI = PHI ** 2
D_F = math.log(2) / math.log(PHI)
K_BOLTZMANN = 8.617e-5  # eV/K
TEMP_C = 37  # physiological temperature in Celsius
TEMP_K = TEMP_C + 273.15
K_T = K_BOLTZMANN * TEMP_K

print(f"Φ = {PHI:.6f}")
print(f"λ_Φ = {LAMBDA_PHI:.6f}")
print(f"D_f = {D_F:.6f}")
print(f"kT at {TEMP_C}°C = {K_T:.6f} eV")
print(f"λ_Φ^D_f = {LAMBDA_PHI ** D_F:.6f}")
print(f"Φ^D_f = {PHI ** D_F:.6f}")
print()

@dataclass
class LTETest:
    """LTEE fitness trajectory test"""
    generations: int
    mutations: int
    observed_fitness: float
    predicted_fitness: float
    error: float
    gamma: float
    delta_E_eff: float

@dataclass
class DrakeRuleTest:
    """Drake's rule test (mutation rate vs genome size)"""
    organism: str
    genome_size_bp: float
    per_genome_rate: float
    per_site_rate: float
    predicted_per_site: float
    error: float

@dataclass
class FractalDimTest:
    """Fractal dimension test for genetic networks"""
    network_type: str
    measured_D_f: float
    predicted_D_f: float
    error: float

def phi_scaling_transform(
    S: float,
    gamma: float = 1.0,
    delta_E_eff: float = 0.0,
    lambda_phi: float = LAMBDA_PHI,
    C_domain: float = 1.0
) -> float:
    """
    Corrected Φ-scaling transform:
    P = C_domain · S^{1/2} · lambda_phi^{D_f} · exp(-gamma · DeltaE_eff/kT)
    """
    amplitude_term = S ** 0.5
    fractal_term = lambda_phi ** D_F
    binding_gate = math.exp(-gamma * delta_E_eff / K_T)

    return C_domain * amplitude_term * fractal_term * binding_gate

def test_ltee_fitness():
    """Test LTEE fitness trajectory predictions"""
    print("=" * 60)
    print("TEST 1: LTEE Fitness Trajectory")
    print("=" * 60)

    # LTEE data from Wiser et al. 2013, Lenski et al.
    # Fitness relative to ancestor (W/W0)
    ltee_data = [
        (2000, 10, 1.35),   # 2000 generations, ~10 mutations, fitness 1.35
        (10000, 50, 1.65),  # 10000 generations, ~50 mutations, fitness 1.65
        (20000, 100, 1.80), # 20000 generations, ~100 mutations, fitness 1.80
        (40000, 200, 1.95), # 40000 generations, ~200 mutations, fitness 1.95
        (50000, 250, 2.00), # 50000 generations, ~250 mutations, fitness 2.00
    ]

    # Fit C_domain and gamma using early data point
    # Using (2000, 10, 1.35) as reference
    ref_S = 10
    ref_P = 1.35
    ref_delta_E = 0.01  # eV (small incremental barrier)

    # Solve for C_domain assuming gamma=1
    ref_amplitude = ref_S ** 0.5
    ref_fractal = LAMBDA_PHI ** D_F
    ref_binding = math.exp(-1.0 * ref_delta_E / K_T)
    C_domain = ref_P / (ref_amplitude * ref_fractal * ref_binding)

    print(f"Fitted C_domain = {C_domain:.6f}")
    print(f"Using gamma = 1.0, DeltaE_eff = 0.01 eV")
    print()

    results = []
    for gens, mutations, observed in ltee_data:
        predicted = phi_scaling_transform(mutations, gamma=1.0, delta_E_eff=0.01, C_domain=C_domain)
        error = abs(predicted - observed) / observed * 100

        test = LTETest(
            generations=gens,
            mutations=mutations,
            observed_fitness=observed,
            predicted_fitness=predicted,
            error=error,
            gamma=1.0,
            delta_E_eff=0.01
        )
        results.append(test)

        print(f"Generation {gens:6d}: Mut={mutations:4d}, Obs={observed:.3f}, Pred={predicted:.3f}, Err={error:.2f}%")

    avg_error = sum(t.error for t in results) / len(results)
    print(f"\nAverage error: {avg_error:.2f}%")
    print()

    return results

def test_drake_rule():
    """Test Drake's rule predictions"""
    print("=" * 60)
    print("TEST 2: Drake's Rule (Mutation Rate vs Genome Size)")
    print("=" * 60)

    # Drake's rule data from Drake et al. 1998, Lynch et al.
    drake_data = [
        ("E. coli", 4.6e6, 0.0025, 5.4e-10),
        ("S. cerevisiae", 1.2e7, 0.003, 2.5e-10),
        ("D. melanogaster", 1.2e8, 0.14, 1.2e-9),
        ("C. elegans", 1.0e8, 0.02, 2.0e-10),
        ("H. sapiens", 3.2e9, 70, 2.2e-8),
    ]

    # Corrected model: per-genome rate bounded, per-site rate ∝ 1/G
    # U_genome ≈ C_domain · lambda_phi^D_f · B_gate
    # μ_site ≈ U_genome / G

    # Fit C_domain using E. coli as reference
    ref_organism = drake_data[0]
    ref_G = ref_organism[1]
    ref_U = ref_organism[2]
    ref_delta_E = 0.005  # eV (DNA replication barrier)

    ref_fractal = LAMBDA_PHI ** D_F
    ref_binding = math.exp(-1.0 * ref_delta_E / K_T)
    C_domain = ref_U / (ref_fractal * ref_binding)

    print(f"Fitted C_domain = {C_domain:.6f}")
    print(f"Using gamma = 1.0, DeltaE_eff = 0.005 eV")
    print()

    results = []
    for organism, G, U_observed, mu_observed in drake_data:
        # Predict per-genome rate
        U_predicted = C_domain * ref_fractal * ref_binding

        # Predict per-site rate
        mu_predicted = U_predicted / G

        error = abs(mu_predicted - mu_observed) / mu_observed * 100

        test = DrakeRuleTest(
            organism=organism,
            genome_size_bp=G,
            per_genome_rate=U_observed,
            per_site_rate=mu_observed,
            predicted_per_site=mu_predicted,
            error=error
        )
        results.append(test)

        print(f"{organism:15s}: G={G:.2e}, U_obs={U_observed:.4f}, μ_obs={mu_observed:.2e}, μ_pred={mu_predicted:.2e}, Err={error:.2f}%")

    avg_error = sum(t.error for t in results) / len(results)
    print(f"\nAverage error: {avg_error:.2f}%")
    print()

    return results

def test_fractal_dimension():
    """Test fractal dimension predictions for genetic networks"""
    print("=" * 60)
    print("TEST 3: Fractal Dimension of Genetic Networks")
    print("=" * 60)

    # Measured fractal dimensions from biological networks
    fractal_data = [
        ("Protein interaction (yeast)", 1.2, 1.8),
        ("Metabolic (E. coli)", 1.3, 1.6),
        ("Transcriptional (human)", 1.1, 1.7),
        ("Gene regulatory (Drosophila)", 1.4, 1.9),
    ]

    print(f"Predicted D_f = {D_F:.6f}")
    print()

    results = []
    for network_type, D_min, D_max in fractal_data:
        D_measured = (D_min + D_max) / 2
        error = abs(D_F - D_measured) / D_measured * 100

        test = FractalDimTest(
            network_type=network_type,
            measured_D_f=D_measured,
            predicted_D_f=D_F,
            error=error
        )
        results.append(test)

        print(f"{network_type:30s}: D_meas={D_measured:.3f}, D_pred={D_F:.3f}, Err={error:.2f}%")

    avg_error = sum(t.error for t in results) / len(results)
    print(f"\nAverage error: {avg_error:.2f}%")
    print()

    return results

def test_phi_scaling_coincidence():
    """Test the 500-generation ≈ 30·Φ^6 coincidence"""
    print("=" * 60)
    print("TEST 4: 500-Generation Sampling Coincidence")
    print("=" * 60)

    phi_6 = PHI ** 6
    thirty_phi_6 = 30 * phi_6

    print(f"Φ^6 = {phi_6:.6f}")
    print(f"30·Φ^6 = {thirty_phi_6:.6f}")
    print(f"LTEE sampling interval = 500 generations")
    print(f"Difference = {abs(thirty_phi_6 - 500):.2f} generations")
    print(f"Relative error = {abs(thirty_phi_6 - 500) / 500 * 100:.2f}%")
    print()

    if abs(thirty_phi_6 - 500) / 500 < 0.1:
        print("Conclusion: Close coincidence (within 10%), but not exact")
    else:
        print("Conclusion: Not a strong coincidence")
    print()

def main():
    """Run all tests"""
    print("Φ-SCALING TRANSFOLD EQUATION TESTS")
    print("=" * 60)
    print()

    # Test 1: LTEE fitness
    ltee_results = test_ltee_fitness()

    # Test 2: Drake's rule
    drake_results = test_drake_rule()

    # Test 3: Fractal dimension
    fractal_results = test_fractal_dimension()

    # Test 4: Sampling coincidence
    test_phi_scaling_coincidence()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    ltee_avg_error = sum(t.error for t in ltee_results) / len(ltee_results)
    drake_avg_error = sum(t.error for t in drake_results) / len(drake_results)
    fractal_avg_error = sum(t.error for t in fractal_results) / len(fractal_results)

    print(f"LTEE fitness average error: {ltee_avg_error:.2f}%")
    print(f"Drake's rule average error: {drake_avg_error:.2f}%")
    print(f"Fractal dimension average error: {fractal_avg_error:.2f}%")
    print()

    # Save results to JSON
    output = {
        "phi": PHI,
        "lambda_phi": LAMBDA_PHI,
        "D_f": D_F,
        "kT_eV": K_T,
        "ltee_results": [
            {
                "generations": t.generations,
                "mutations": t.mutations,
                "observed_fitness": t.observed_fitness,
                "predicted_fitness": t.predicted_fitness,
                "error_percent": t.error
            }
            for t in ltee_results
        ],
        "drake_results": [
            {
                "organism": t.organism,
                "genome_size_bp": t.genome_size_bp,
                "per_genome_rate": t.per_genome_rate,
                "per_site_rate": t.per_site_rate,
                "predicted_per_site": t.predicted_per_site,
                "error_percent": t.error
            }
            for t in drake_results
        ],
        "fractal_results": [
            {
                "network_type": t.network_type,
                "measured_D_f": t.measured_D_f,
                "predicted_D_f": t.predicted_D_f,
                "error_percent": t.error
            }
            for t in fractal_results
        ],
        "summary": {
            "ltee_avg_error": ltee_avg_error,
            "drake_avg_error": drake_avg_error,
            "fractal_avg_error": fractal_avg_error
        }
    }

    output_file = "/home/allaun/Documents/Research Stack/4-Infrastructure/shim/phi_scaling_transfold_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
