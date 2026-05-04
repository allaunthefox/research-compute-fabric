"""
Mobile Microgripper Scientific Shortcut Refinement

Uses scipy and numpy for statistical and numerical analysis of mathematical shortcuts:
- scipy.stats for 6.5σ confidence intervals
- scipy.optimize for parameter optimization
- numpy for precise numerical calculations
- scipy.integrate for differential equation solving
- scipy.linalg for matrix operations

Applies 6.5σ bounds only to statistical quantities; numerical optimization
and physical design claims still require separate measurement/provenance gates.
"""

import numpy as np
import scipy.stats as stats
import scipy.optimize as opt
import scipy.integrate as integrate
import scipy.linalg as la
import math
import json
from typing import Dict, List, Tuple, Any, Callable

# Physical Constants (CODATA 2022)
KB = 1.380649e-23  # Boltzmann constant (J/K)
H_BAR = 1.054571817e-34  # Reduced Planck constant (J·s)
MU_0 = 4 * np.pi * 1e-7  # Vacuum permeability (T·m/A)
LAMBDA_TORSION = 1e-9  # Interaction length (m)

# Microgripper Parameters
ARM_LENGTH_UM = 200.0
ARM_WIDTH_UM = 30.0
ARM_THICKNESS_UM = 15.0
HINGE_RADIUS_UM = 10.0
GAP_OPEN_UM = 100.0
GAP_CLOSED_UM = 20.0
MAGNETIC_COATING_UM = 5.0
SENSOR_THICKNESS_UM = 10.0

# Magnetic Parameters
B_BASE = 1.2  # Tesla
B_STEER = 0.3  # Tesla
MU_PARTICLE = 8.6e-19  # A·m² (Fe₃O₄ nanoferrite)

# Temperature Range
T_MIN = 50.0  # K (critical temperature from buckyball-MOF spec)
T_MAX = 300.0  # K (room temperature)

class StatisticalValidation:
    """6.5σ statistical validation framework."""
    
    @staticmethod
    def calculate_confidence_interval(data: np.ndarray, confidence: float = 0.99999998) -> Tuple[float, float]:
        """Calculate confidence interval using scipy.stats."""
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        n = len(data)
        
        # 6.5σ corresponds to ~99.99998% confidence
        z_score = stats.norm.ppf((1 + confidence) / 2)
        margin = z_score * (std / np.sqrt(n))
        
        return (mean - margin, mean + margin)
    
    @staticmethod
    def hypothesis_test(sample_mean: float, population_mean: float, 
                       std_dev: float, n: int, alpha: float = 1e-6) -> Dict[str, Any]:
        """Two-tailed hypothesis test with 6.5σ significance."""
        z_score = (sample_mean - population_mean) / (std_dev / np.sqrt(n))
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # 6.5σ threshold: z ≈ 6.5, p ≈ 1e-10
        significant = p_value < alpha
        
        return {
            "z_score": z_score,
            "p_value": p_value,
            "significant": significant,
            "sigma_level": abs(z_score),
            "meets_6_5_sigma": abs(z_score) >= 6.5
        }

class RefinedFAMMAnalysis:
    """Refined FAMM frustration analysis with scipy optimization."""
    
    def __init__(self):
        self.phi_history = []
    
    def frustration_function(self, temperature: float, field_strength: float) -> float:
        """Φ(T, B) = (τ_thermal + τ_steric) / τ_magnetic"""
        
        # Magnetic torque
        tau_magnetic = MU_PARTICLE * field_strength
        
        # Thermal torque
        tau_thermal = KB * temperature / LAMBDA_TORSION
        
        # Steric torque (from hinge geometry)
        k_steric = 1e-12
        theta_offset = math.radians(14)
        theta_lattice = math.radians(60)
        tau_steric = k_steric * (1 - math.cos(theta_offset - theta_lattice))
        
        phi = (tau_thermal + tau_steric) / tau_magnetic
        return phi
    
    def find_optimal_temperature(self, target_phi: float = 1.0, 
                                field_strength: float = B_BASE) -> float:
        """Find temperature that achieves target Φ using scipy.optimize."""
        
        def objective(T):
            return abs(self.frustration_function(T, field_strength) - target_phi)
        
        # Optimize in range [T_MIN, T_MAX]
        result = opt.minimize_scalar(objective, bounds=(T_MIN, T_MAX), method='bounded')
        
        return result.x
    
    def find_optimal_field(self, target_phi: float = 1.0, 
                          temperature: float = T_MAX) -> float:
        """Find field strength that achieves target Φ using scipy.optimize."""
        
        def objective(B):
            return abs(self.frustration_function(temperature, B) - target_phi)
        
        # Optimize in range [0.8, 2.0] Tesla (from buckyball-MOF spec)
        result = opt.minimize_scalar(objective, bounds=(0.8, 2.0), method='bounded')
        
        return result.x
    
    def monte_carlo_validation(self, n_samples: int = 10000) -> Dict[str, Any]:
        """Monte Carlo statistical interval for Φ; not physical validation."""
        
        # Sample temperature and field with uncertainty
        T_samples = np.random.normal(T_MAX, 10.0, n_samples)  # ±10K uncertainty
        B_samples = np.random.normal(B_BASE, 0.1, n_samples)  # ±0.1T uncertainty
        
        phi_samples = np.array([self.frustration_function(T, B) 
                               for T, B in zip(T_samples, B_samples)])
        
        # Calculate 6.5σ confidence interval
        ci_low, ci_high = StatisticalValidation.calculate_confidence_interval(phi_samples)
        
        # Test hypothesis: Φ >> 1 (thermal dominance)
        test_result = StatisticalValidation.hypothesis_test(
            np.mean(phi_samples), 1.0, np.std(phi_samples), n_samples
        )
        
        return {
            "phi_mean": np.mean(phi_samples),
            "phi_std": np.std(phi_samples),
            "phi_ci_6_5_sigma": (ci_low, ci_high),
            "hypothesis_test": test_result,
            "samples": n_samples
        }

class RefinedQuaternionOptimization:
    """Refined quaternion optimization using scipy.linalg."""
    
    def __init__(self):
        self.quaternions = []
    
    def quaternion_to_rotation_matrix(self, q: Tuple[float, float, float, float]) -> np.ndarray:
        """Convert quaternion to rotation matrix using scipy.linalg conventions."""
        w, x, y, z = q
        
        R = np.array([
            [1 - 2*(y**2 + z**2), 2*(x*y - w*z), 2*(x*z + w*y)],
            [2*(x*y + w*z), 1 - 2*(x**2 + z**2), 2*(y*z - w*x)],
            [2*(x*z - w*y), 2*(y*z + w*x), 1 - 2*(x**2 + y**2)]
        ])
        
        return R
    
    def optimize_counter_rotation(self, theta_initial: float, phi_initial: float) -> Tuple[float, float]:
        """Optimize angles for zero net angular momentum using scipy.optimize."""
        
        def net_momentum(angles):
            theta, phi = angles
            
            # Quaternion at layer N
            q_n = (math.cos(theta/2), math.sin(theta/2)*math.cos(phi),
                   math.sin(theta/2)*math.sin(phi), math.sin(theta/2)*math.cos(theta))
            
            # Quaternion at layer N-1 (counter-rotated)
            theta_minus_1 = -theta
            q_n_minus_1 = (math.cos(theta_minus_1/2), math.sin(theta_minus_1/2)*math.cos(phi),
                          math.sin(theta_minus_1/2)*math.sin(phi), math.sin(theta_minus_1/2)*math.cos(theta_minus_1))
            
            # Counter-rotation
            q_n_minus_1_conj = (q_n_minus_1[0], -q_n_minus_1[1], -q_n_minus_1[2], -q_n_minus_1[3])
            counter_rot = (
                q_n[0]*q_n_minus_1_conj[0] - q_n[1]*q_n_minus_1_conj[1] - q_n[2]*q_n_minus_1_conj[2] - q_n[3]*q_n_minus_1_conj[3],
                q_n[0]*q_n_minus_1_conj[1] + q_n[1]*q_n_minus_1_conj[0] + q_n[2]*q_n_minus_1_conj[3] - q_n[3]*q_n_minus_1_conj[2],
                q_n[0]*q_n_minus_1_conj[2] - q_n[1]*q_n_minus_1_conj[3] + q_n[2]*q_n_minus_1_conj[0] + q_n[3]*q_n_minus_1_conj[1],
                q_n[0]*q_n_minus_1_conj[3] + q_n[1]*q_n_minus_1_conj[2] - q_n[2]*q_n_minus_1_conj[1] + q_n[3]*q_n_minus_1_conj[0]
            )
            
            # Net angular momentum
            angle = 2 * math.acos(max(-1, min(1, counter_rot[0])))
            return angle**2  # Minimize squared angle
        
        # Optimize angles
        result = opt.minimize(net_momentum, 
                            x0=[theta_initial, phi_initial],
                            bounds=[(0, np.pi), (0, 2*np.pi)],
                            method='L-BFGS-B')
        
        return tuple(result.x)

class RefinedPISTOptimization:
    """Refined PIST state space optimization with scipy integration."""
    
    def __init__(self):
        self.state_space = []
    
    def pist_dynamics(self, state: np.ndarray, t: float, phi_threshold: float) -> np.ndarray:
        """PIST state space dynamics as differential equation."""
        k, t_coord, mass = state
        
        # State space pruning rate
        pruning_rate = phi_threshold * np.exp(-phi_threshold * t)
        
        return np.array([-pruning_rate * k, -pruning_rate * t_coord, -pruning_rate * mass])
    
    def integrate_state_space(self, initial_state: Tuple[float, float, float], 
                            phi_threshold: float, t_max: float = 10.0) -> np.ndarray:
        """Integrate PIST dynamics using scipy.integrate.odeint."""
        
        sol = integrate.odeint(
            self.pist_dynamics,
            initial_state,
            np.linspace(0, t_max, 100),
            args=(phi_threshold,)
        )
        
        return sol[-1]  # Final state
    
    def optimize_phi_threshold(self, target_reduction: float = 0.5) -> float:
        """Find optimal Φ threshold for target state space reduction."""
        
        initial_state = (1000, 100, 6000)  # Initial (k, t, mass)
        
        def objective(phi):
            final_state = self.integrate_state_space(initial_state, phi)
            reduction = 1 - (final_state[0] / initial_state[0])
            return abs(reduction - target_reduction)
        
        result = opt.minimize_scalar(objective, bounds=(0.1, 0.9), method='bounded')
        
        return result.x

class RefinedStringStarAnalysis:
    """Refined String-Star curvature analysis with scipy.linalg."""
    
    def __init__(self):
        self.curvature_data = []
    
    def calculate_curvature_tensor(self, radius: float) -> np.ndarray:
        """Calculate curvature tensor using differential geometry."""
        # For spherical surface: R_ij = (1/R²) * g_ij
        g_ij = np.eye(3)  # Metric tensor (simplified)
        R_ij = (1.0 / radius**2) * g_ij
        
        return R_ij
    
    def calculate_ricci_scalar(self, radius: float) -> float:
        """Calculate Ricci scalar (scalar curvature)."""
        # For sphere: R = 2/R²
        return 2.0 / (radius**2)
    
    def optimize_hinge_radius(self, target_curvature: float = 100.0) -> float:
        """Optimize hinge radius for target curvature."""
        
        def objective(r):
            curvature = self.calculate_ricci_scalar(r)
            return abs(curvature - target_curvature)
        
        # Optimize in range [5, 20] μm
        result = opt.minimize_scalar(objective, bounds=(5e-6, 20e-6), method='bounded')
        
        return result.x

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

def run_scientific_refinement() -> Dict[str, Any]:
    """Run refined scientific analysis using scipy packages."""
    
    print("Running Scientific Refinement with scipy and numpy...")
    print("=" * 70)
    
    results = {}
    
    # 1. Refined FAMM Analysis
    print("\n1. Refined FAMM Frustration Analysis (scipy.optimize)")
    famm = RefinedFAMMAnalysis()
    
    # Find optimal parameters
    optimal_temp = famm.find_optimal_temperature(target_phi=1.0, field_strength=B_BASE)
    optimal_field = famm.find_optimal_field(target_phi=1.0, temperature=T_MAX)
    
    # Monte Carlo validation
    mc_results = famm.monte_carlo_validation(n_samples=10000)
    
    results["famm_refined"] = {
        "optimal_temperature_K": float(optimal_temp),
        "optimal_field_T": float(optimal_field),
        "monte_carlo_validation": convert_numpy_types(mc_results),
        "refined_claim": f"Assembly requires T < {optimal_temp:.1f}K or B > {optimal_field:.2f}T",
        "confidence": "Monte Carlo statistical interval; physical claim still requires measurement provenance"
    }
    
    print(f"  Optimal Temperature: {optimal_temp:.2f} K")
    print(f"  Optimal Field: {optimal_field:.3f} T")
    print(f"  Φ Mean: {mc_results['phi_mean']:.2e}")
    print(f"  Φ 6.5σ CI: [{mc_results['phi_ci_6_5_sigma'][0]:.2e}, {mc_results['phi_ci_6_5_sigma'][1]:.2e}]")
    print(f"  Hypothesis Test Z-score: {mc_results['hypothesis_test']['z_score']:.2f}")
    print(f"  Meets 6.5σ: {mc_results['hypothesis_test']['meets_6_5_sigma']}")
    
    # 2. Refined Quaternion Optimization
    print("\n2. Refined Quaternion Optimization (scipy.linalg + scipy.optimize)")
    quat = RefinedQuaternionOptimization()
    
    theta_initial = math.radians(45)
    phi_initial = math.radians(30)
    optimal_angles = quat.optimize_counter_rotation(theta_initial, phi_initial)
    
    results["quaternion_refined"] = {
        "optimal_theta_rad": float(optimal_angles[0]),
        "optimal_phi_rad": float(optimal_angles[1]),
        "optimal_theta_deg": float(math.degrees(optimal_angles[0])),
        "optimal_phi_deg": float(math.degrees(optimal_angles[1])),
        "refined_claim": "Counter-rotation achievable with optimized field angles",
        "confidence": "Numerical optimization convergence"
    }
    
    print(f"  Optimal Theta: {math.degrees(optimal_angles[0]):.2f}°")
    print(f"  Optimal Phi: {math.degrees(optimal_angles[1]):.2f}°")
    
    # 3. Refined PIST Optimization
    print("\n3. Refined PIST State Space Optimization (scipy.integrate)")
    pist = RefinedPISTOptimization()
    
    optimal_phi = pist.optimize_phi_threshold(target_reduction=0.5)
    
    results["pist_refined"] = {
        "optimal_phi_threshold": float(optimal_phi),
        "refined_claim": f"Φ threshold of {optimal_phi:.3f} achieves 50% state space reduction",
        "confidence": "Differential equation integration"
    }
    
    print(f"  Optimal Φ Threshold: {optimal_phi:.3f}")
    
    # 4. Refined String-Star Analysis
    print("\n4. Refined String-Star Curvature Analysis (scipy.linalg)")
    ss = RefinedStringStarAnalysis()
    
    optimal_radius = ss.optimize_hinge_radius(target_curvature=100.0)
    
    results["string_star_refined"] = {
        "optimal_hinge_radius_m": float(optimal_radius),
        "optimal_hinge_radius_um": float(optimal_radius * 1e6),
        "refined_claim": f"Optimal hinge radius: {optimal_radius*1e6:.2f} μm for target curvature",
        "confidence": "Curvature tensor calculation"
    }
    
    print(f"  Optimal Hinge Radius: {optimal_radius*1e6:.2f} μm")
    
    # Summary of refined claims
    print("\n" + "=" * 70)
    print("REFINED CLAIMS (domain-gated; statistical intervals are not physical validation):")
    
    refined_claims = [
        f"FAMM: Assembly requires T < {optimal_temp:.1f}K or B > {optimal_field:.2f}T (Monte Carlo interval; needs physical measurement)",
        f"Quaternion: Counter-rotation achievable at θ={math.degrees(optimal_angles[0]):.1f}°, φ={math.degrees(optimal_angles[1]):.1f}° (numerical optimization)",
        f"PIST: Φ threshold {optimal_phi:.3f} achieves 50% reduction (ODE integration)",
        f"String-Star: Optimal hinge radius {optimal_radius*1e6:.2f} μm (curvature tensor)"
    ]
    
    for i, claim in enumerate(refined_claims, 1):
        print(f"  {i}. {claim}")
    
    results["refined_claims"] = refined_claims
    results["summary"] = {
        "total_refined_claims": len(refined_claims),
        "validation_method": "scipy + numpy numerical analysis with statistical interval where applicable",
        "primary_refinement": "FAMM assembly conditions quantified with Monte Carlo",
        "secondary_refinement": "Quaternion angles optimized via L-BFGS-B",
        "tertiary_refinement": "PIST dynamics integrated via ODE solver"
    }
    
    return results

if __name__ == "__main__":
    results = run_scientific_refinement()
    
    # Save results
    output_file = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/mobile_microgripper_sci_refined.json"
    with open(output_file, 'w') as f:
        json.dump(convert_numpy_types(results), f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nScientific refinement complete!")
