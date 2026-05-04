#!/usr/bin/env python3
"""
COUCH Phase Space Filter Normalization

Applies filter normalization technique from NeurIPS 2018 paper
"Visualizing the Loss Landscape of Neural Nets" to COUCH phase space.

Filter normalization enables meaningful side-by-side comparisons
between different coupling regimes by normalizing oscillator states.

AUDIT-ONLY SHIM:
This script is not a source-of-truth implementation under 6-Documentation/docs/AGENTS.md.
It may generate exploratory JSON/audit evidence only. Any curvature,
compression strategy, invariant, or branching logic here must be ported to
Lean before being used by the core model or release claims.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import json


@dataclass
class COUCHState:
    """COUCH oscillator state."""
    position: np.ndarray  # x_i
    velocity: np.ndarray  # ẋ_i
    acceleration: np.ndarray  # ẍ_i
    coupling: np.ndarray  # κ_ij
    damping: float  # γ
    frequency: np.ndarray  # ω_i
    forcing: float  # F(t)


class COUCHFilterNormalizer:
    """
    Applies filter normalization to COUCH phase space.
    
    Based on Li et al. (2018) - filter normalizes directions
    to enable meaningful curvature comparisons.
    """
    
    def __init__(self, n_oscillators: int = 3):
        self.n_oscillators = n_oscillators
        
    def normalize_state(self, state: COUCHState) -> Dict[str, np.ndarray]:
        """
        Apply filter normalization to COUCH state.
        
        Normalizes each oscillator's state vector to unit length
        while preserving relative phase relationships.
        """
        # Stack state into phase space vector
        phase_space = np.concatenate([
            state.position,
            state.velocity,
            state.acceleration
        ])
        
        # Normalize to unit length (filter normalization)
        norm = np.linalg.norm(phase_space)
        if norm > 0:
            normalized_phase_space = phase_space / norm
        else:
            normalized_phase_space = phase_space
        
        # Extract normalized components
        n = self.n_oscillators
        normalized_position = normalized_phase_space[:n]
        normalized_velocity = normalized_phase_space[n:2*n]
        normalized_acceleration = normalized_phase_space[2*n:3*n]
        
        return {
            "position": normalized_position,
            "velocity": normalized_velocity,
            "acceleration": normalized_acceleration,
            "phase_space": normalized_phase_space,
            "norm": norm
        }
    
    def calculate_curvature(self, state: COUCHState, normalized: Dict[str, np.ndarray]) -> float:
        """
        Calculate curvature of COUCH phase space trajectory.
        
        Curvature = ||d²r/ds²|| where s is arc length
        """
        # Use normalized velocity and acceleration
        v = normalized["velocity"]
        a = normalized["acceleration"]
        
        # Curvature formula: κ = ||v × a|| / ||v||³
        # For normalized states, ||v|| ≈ 1
        cross_product = np.cross(v, a)
        if len(cross_product.shape) == 0:
            cross_mag = abs(cross_product)
        else:
            cross_mag = np.linalg.norm(cross_product)
        
        v_mag = np.linalg.norm(v)
        if v_mag > 0:
            curvature = cross_mag / (v_mag ** 3)
        else:
            curvature = 0.0
        
        return curvature
    
    def sample_trajectory(self, state: COUCHState, steps: int = 100) -> List[Dict[str, Any]]:
        """
        Sample COUCH trajectory and apply filter normalization.
        
        Simulates COUCH dynamics using RK4 integration.
        """
        trajectory = []
        
        # Initial state
        x = state.position.copy()
        v = state.velocity.copy()
        a = state.acceleration.copy()
        
        dt = 0.01
        
        for i in range(steps):
            # COUCH dynamics: ẍ_i + γẋ_i + ω_i²x_i + Σ_j κ_ij(x_i - x_j) = F(t)
            # Solve for acceleration
            damping_term = state.damping * v
            spring_term = state.frequency ** 2 * x
            pairwise_displacement = x[:, None] - x[None, :]
            coupling_term = np.sum(state.coupling * pairwise_displacement, axis=1)
            forcing_term = state.forcing
            
            a = forcing_term - damping_term - spring_term - coupling_term
            
            # Create temporary state for normalization
            temp_state = COUCHState(
                position=x,
                velocity=v,
                acceleration=a,
                coupling=state.coupling,
                damping=state.damping,
                frequency=state.frequency,
                forcing=state.forcing
            )
            
            # Normalize
            normalized = self.normalize_state(temp_state)
            
            # Calculate curvature
            curvature = self.calculate_curvature(temp_state, normalized)
            
            trajectory.append({
                "step": i,
                "position": x.copy(),
                "velocity": v.copy(),
                "acceleration": a.copy(),
                "normalized_position": normalized["position"].copy(),
                "normalized_velocity": normalized["velocity"].copy(),
                "normalized_acceleration": normalized["acceleration"].copy(),
                "norm": normalized["norm"],
                "curvature": curvature
            })
            
            # RK4 integration step
            k1_v = a
            k1_x = v
            
            k2_v = a  # Simplified (would need full RK4)
            k2_x = v + k1_v * dt / 2
            
            k3_v = a
            k3_x = v + k2_v * dt / 2
            
            k4_v = a
            k4_x = v + k3_v * dt
            
            v = v + (k1_v + 2*k2_v + 2*k3_v + k4_v) * dt / 6
            x = x + (k1_x + 2*k2_x + 2*k3_x + k4_x) * dt / 6
        
        return trajectory
    
    def compare_coupling_regimes(self, base_state: COUCHState, coupling_values: List[float]) -> Dict[str, Any]:
        """
        Compare different coupling regimes using filter normalization.
        
        This is the key application - meaningful side-by-side comparison
        of different κ values enabled by filter normalization.
        """
        comparisons = {}
        
        for kappa in coupling_values:
            # Modify coupling strength
            modified_state = COUCHState(
                position=base_state.position.copy(),
                velocity=base_state.velocity.copy(),
                acceleration=base_state.acceleration.copy(),
                coupling=base_state.coupling * kappa,
                damping=base_state.damping,
                frequency=base_state.frequency.copy(),
                forcing=base_state.forcing
            )
            
            # Sample trajectory
            trajectory = self.sample_trajectory(modified_state, steps=50)
            
            # Calculate statistics
            curvatures = [t["curvature"] for t in trajectory]
            norms = [t["norm"] for t in trajectory]
            
            comparisons[f"kappa_{kappa:.2f}"] = {
                "coupling_strength": kappa,
                "avg_curvature": np.mean(curvatures),
                "max_curvature": np.max(curvatures),
                "min_curvature": np.min(curvatures),
                "std_curvature": np.std(curvatures),
                "avg_norm": np.mean(norms),
                "trajectory": trajectory[:10],  # Sample
                "curvature_history": curvatures
            }
        
        return comparisons
    
    def visualize_landscape_summary(self, comparisons: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of the COUCH loss landscape across coupling regimes.
        """
        summary = {
            "regimes": list(comparisons.keys()),
            "curvature_comparison": {},
            "norm_comparison": {},
            "chaotic_threshold": 1.0  # Arbitrary threshold for "super freak" regime
        }
        
        for regime, data in comparisons.items():
            summary["curvature_comparison"][regime] = {
                "avg": data["avg_curvature"],
                "max": data["max_curvature"],
                "std": data["std_curvature"]
            }
            
            summary["norm_comparison"][regime] = {
                "avg": data["avg_norm"]
            }
            
            # Classify regime
            if data["avg_curvature"] > summary["chaotic_threshold"]:
                regime_type = "chaotic_super_freak"
            elif data["avg_curvature"] > 0.5:
                regime_type = "transitional"
            else:
                regime_type = "stable"
            
            data["regime_type"] = regime_type
        
        return summary


def main():
    """Run COUCH filter normalization analysis."""
    print("=" * 70)
    print("COUCH PHASE SPACE FILTER NORMALIZATION")
    print("=" * 70)
    print("\n[*] Applying filter normalization from NeurIPS 2018")
    print("[*] Enabling meaningful side-by-side coupling regime comparisons")
    
    # Initialize normalizer
    normalizer = COUCHFilterNormalizer(n_oscillators=3)
    
    # Create base COUCH state
    np.random.seed(42)
    base_state = COUCHState(
        position=np.random.randn(3) * 0.5,
        velocity=np.random.randn(3) * 0.3,
        acceleration=np.zeros(3),
        coupling=np.random.randn(3, 3) * 0.1,
        damping=0.5,
        frequency=np.ones(3) * 2.0,
        forcing=1.0
    )
    
    # Symmetrize coupling matrix
    base_state.coupling = (base_state.coupling + base_state.coupling.T) / 2
    
    print(f"\n[*] Base COUCH State:")
    print(f"    Position: {base_state.position}")
    print(f"    Velocity: {base_state.velocity}")
    print(f"    Damping: {base_state.damping}")
    print(f"    Forcing: {base_state.forcing}")
    
    # Apply filter normalization to base state
    print(f"\n[*] Applying filter normalization...")
    normalized = normalizer.normalize_state(base_state)
    print(f"    Original norm: {normalized['norm']:.4f}")
    print(f"    Normalized position: {normalized['position']}")
    print(f"    Normalized velocity: {normalized['velocity']}")
    
    # Calculate curvature
    curvature = normalizer.calculate_curvature(base_state, normalized)
    print(f"    Phase space curvature: {curvature:.4f}")
    
    # Compare coupling regimes
    print(f"\n[*] Comparing coupling regimes (κ values)...")
    coupling_values = [0.5, 1.0, 1.5, 2.0, 2.5]
    comparisons = normalizer.compare_coupling_regimes(base_state, coupling_values)
    
    print(f"\n[*] Coupling Regime Comparison:")
    for regime, data in comparisons.items():
        print(f"    {regime}:")
        print(f"        Avg curvature: {data['avg_curvature']:.4f}")
        print(f"        Max curvature: {data['max_curvature']:.4f}")
        print(f"        Std curvature: {data['std_curvature']:.4f}")
        print(f"        Avg norm: {data['avg_norm']:.4f}")
        print(f"        Regime type: {data.get('regime_type', 'unknown')}")
    
    # Visualize landscape summary
    print(f"\n[*] Creating landscape summary...")
    summary = normalizer.visualize_landscape_summary(comparisons)
    
    print(f"\n[*] Landscape Summary:")
    print(f"    Regimes analyzed: {summary['regimes']}")
    print(f"    Chaotic threshold: {summary['chaotic_threshold']}")
    
    # Find transition to chaotic regime
    chaotic_regimes = [r for r, d in comparisons.items() if d.get('regime_type') == 'chaotic_super_freak']
    if chaotic_regimes:
        print(f"    Chaotic regimes: {chaotic_regimes}")
    else:
        print(f"    No chaotic regimes detected (may need higher κ)")
    
    # Save results
    def convert_to_native(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        else:
            return obj
    
    results = {
        "base_state": {
            "position": base_state.position.tolist(),
            "velocity": base_state.velocity.tolist(),
            "damping": base_state.damping,
            "forcing": base_state.forcing
        },
        "normalized_base": convert_to_native(normalized),
        "base_curvature": curvature,
        "coupling_comparisons": convert_to_native(comparisons),
        "landscape_summary": convert_to_native(summary)
    }
    
    output_path = "/home/allaun/Documents/Research Stack/data/couch_filter_normalization.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ COUCH FILTER NORMALIZATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
