#!/usr/bin/env python3
"""
Waveprobe Adapter for OTOM v4 Cotranslational Simulator

This adapter wraps the codon_peptide_rl_simulation_v4.py simulator
with a waveprobe-compatible interface for testing and validation.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Import the v4 simulator
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from codon_peptide_rl_simulation_v4 import run_v4


class WaveprobeV4Adapter:
    """Waveprobe adapter for OTOM v4 cotranslational simulator."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize waveprobe adapter with configuration."""
        self.config = config or {}
        self.probe_id = f"wave_{uuid.uuid4().hex[:12]}"
        self.timestamp = datetime.now().isoformat()
        
    def execute_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a waveprobe probe on the v4 simulator."""
        # Extract probe parameters
        use_bias = probe_config.get("use_bias", False)
        seed = probe_config.get("seed", 7)
        T = probe_config.get("T", 360)
        Lexp = probe_config.get("Lexp", 2)
        
        # Execute simulator
        history = run_v4(use_bias=use_bias, seed=seed, T=T, Lexp=Lexp)
        
        # Extract metrics
        metrics = self.extract_metrics(history, probe_config)
        
        # Validate convergence
        convergence_status = self.validate_convergence(metrics)
        
        # Build result
        result = {
            "probe_id": self.probe_id,
            "probe_config": probe_config,
            "execution_timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "convergence_status": convergence_status,
            "history": self._serialize_history(history)
        }
        
        return result
    
    def extract_metrics(self, history: Dict[str, Any], probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized metrics from simulator history."""
        metrics = {
            "final_phi": float(history["final_phi"]),
            "best_phi": float(history["best_phi"]),
            "final_codons": tuple(history["final_codons"]),
            "phi_convergence_rate": self._compute_convergence_rate(history["phi"]),
            "codon_convergence_stability": self._compute_codon_stability(history),
            "contact_formation_rate": self._compute_contact_rate(history),
            "pause_intensity_profile": self._compute_pause_profile(history),
            "trajectory_length": len(history["phi"]),
            "use_bias": probe_config.get("use_bias", False),
            "seed": probe_config.get("seed", 7),
            "T": probe_config.get("T", 360),
            "Lexp": probe_config.get("Lexp", 2)
        }
        return metrics
    
    def validate_convergence(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate convergence criteria."""
        convergence_status = {
            "phi_converged": metrics["phi_convergence_rate"] < 0.01,
            "codon_converged": metrics["codon_convergence_stability"] > 0.95,
            "contact_formation_stable": 0.1 < metrics["contact_formation_rate"] < 0.9,
            "overall_status": "converged" if (
                metrics["phi_convergence_rate"] < 0.01 and
                metrics["codon_convergence_stability"] > 0.95
            ) else "not_converged"
        }
        return convergence_status
    
    def serialize_results(self, result: Dict[str, Any]) -> str:
        """Serialize results in waveprobe-compatible JSON format."""
        serialized = json.dumps(result, indent=2, default=str)
        return serialized
    
    def store_to_topological(self, result: Dict[str, Any], storage_path: Optional[str] = None) -> str:
        """Store results in topological storage (placeholder for ENE integration)."""
        # Placeholder for ENE integration
        # In production, this would use ENE credential manager to store to Google Drive
        storage_path = storage_path or f"data/waveprobes/otom_v4/{self.probe_id}.json"
        
        # Create directory if needed
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize and save
        serialized = self.serialize_results(result)
        Path(storage_path).write_text(serialized)
        
        return storage_path
    
    def _compute_convergence_rate(self, phi_trajectory: List[float]) -> float:
        """Compute convergence rate from phi trajectory."""
        if len(phi_trajectory) < 10:
            return 1.0
        
        # Use last 10% of trajectory to compute convergence
        tail_size = max(10, len(phi_trajectory) // 10)
        tail = phi_trajectory[-tail_size:]
        
        # Compute standard deviation as convergence metric
        import numpy as np
        convergence_rate = float(np.std(tail) / (np.mean(np.abs(tail)) + 1e-10))
        return convergence_rate
    
    def _compute_codon_stability(self, history: Dict[str, Any]) -> float:
        """Compute codon choice stability."""
        if "visible" not in history:
            return 0.0
        
        # Check how often the visible prefix changes in the last 20% of simulation
        visible_history = history["visible"]
        if len(visible_history) < 5:
            return 0.0
        
        tail_size = max(5, len(visible_history) // 5)
        tail = visible_history[-tail_size:]
        
        # Count unique visible prefixes
        unique_prefixes = len(set(tail))
        stability = 1.0 - (unique_prefixes - 1) / len(tail)
        return max(0.0, min(1.0, stability))
    
    def _compute_contact_rate(self, history: Dict[str, Any]) -> float:
        """Compute average contact formation rate."""
        if "contact" not in history:
            return 0.0
        
        import numpy as np
        contact_trajectory = history["contact"]
        return float(np.mean(contact_trajectory))
    
    def _compute_pause_profile(self, history: Dict[str, Any]) -> Dict[str, float]:
        """Compute pause intensity profile statistics."""
        if "pause" not in history:
            return {"mean": 0.0, "std": 0.0, "max": 0.0}
        
        import numpy as np
        pause_trajectory = history["pause"]
        return {
            "mean": float(np.mean(pause_trajectory)),
            "std": float(np.std(pause_trajectory)),
            "max": float(np.max(pause_trajectory)),
            "min": float(np.min(pause_trajectory))
        }
    
    def _serialize_history(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize history for storage (convert numpy arrays to lists)."""
        serialized = {}
        for key, value in history.items():
            if hasattr(value, 'tolist'):
                serialized[key] = value.tolist()
            elif isinstance(value, dict):
                serialized[key] = {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in value.items()}
            else:
                serialized[key] = value
        return serialized


class WaveprobeProbeGenerator:
    """Generate waveprobe test probes for v4 simulator."""
    
    @staticmethod
    def generate_parameter_sweep_probes() -> List[Dict[str, Any]]:
        """Generate parameter sweep probes."""
        probes = []
        
        # Sweep use_bias
        for use_bias in [False, True]:
            probes.append({
                "probe_type": "parameter_sweep",
                "use_bias": use_bias,
                "seed": 7,
                "T": 360,
                "Lexp": 2,
                "description": f"Sweep use_bias={use_bias}"
            })
        
        # Sweep seed values
        for seed in [1, 7, 42, 100, 999]:
            probes.append({
                "probe_type": "parameter_sweep",
                "use_bias": False,
                "seed": seed,
                "T": 360,
                "Lexp": 2,
                "description": f"Sweep seed={seed}"
            })
        
        return probes
    
    @staticmethod
    def generate_multi_seed_convergence_probes(num_seeds: int = 10) -> List[Dict[str, Any]]:
        """Generate multi-seed convergence probes."""
        import numpy as np
        probes = []
        
        seeds = np.random.randint(1, 10000, size=num_seeds).tolist()
        
        for seed in seeds:
            probes.append({
                "probe_type": "multi_seed_convergence",
                "use_bias": False,
                "seed": int(seed),
                "T": 360,
                "Lexp": 2,
                "description": f"Convergence test seed={seed}"
            })
        
        return probes
    
    @staticmethod
    def generate_bias_ablation_comparison_probes() -> List[Dict[str, Any]]:
        """Generate bias ablation comparison probes."""
        probes = []
        
        for seed in [7, 42, 100]:
            for use_bias in [False, True]:
                probes.append({
                    "probe_type": "bias_ablation_comparison",
                    "use_bias": use_bias,
                    "seed": seed,
                    "T": 360,
                    "Lexp": 2,
                    "description": f"Bias ablation seed={seed} use_bias={use_bias}"
                })
        
        return probes
    
    @staticmethod
    def generate_convergence_stability_probes() -> List[Dict[str, Any]]:
        """Generate convergence stability probes."""
        probes = []
        
        for T in [180, 360, 720]:
            for Lexp in [1, 2, 3]:
                probes.append({
                    "probe_type": "convergence_stability",
                    "use_bias": False,
                    "seed": 7,
                    "T": T,
                    "Lexp": Lexp,
                    "description": f"Stability test T={T} Lexp={Lexp}"
                })
        
        return probes


def main():
    """Main entry point for testing the adapter."""
    print("=" * 70)
    print("Waveprobe V4 Adapter Test")
    print("=" * 70)
    
    # Initialize adapter
    adapter = WaveprobeV4Adapter()
    print(f"Adapter initialized: {adapter.probe_id}")
    
    # Test with a simple probe
    probe_config = {
        "probe_type": "test",
        "use_bias": False,
        "seed": 7,
        "T": 360,
        "Lexp": 2
    }
    
    print(f"\nExecuting probe: {probe_config}")
    result = adapter.execute_probe(probe_config)
    
    print(f"\nProbe execution completed")
    print(f"Final Phi: {result['metrics']['final_phi']:.6f}")
    print(f"Best Phi: {result['metrics']['best_phi']:.6f}")
    print(f"Final Codons: {result['metrics']['final_codons']}")
    print(f"Convergence Status: {result['convergence_status']['overall_status']}")
    
    # Store results
    storage_path = adapter.store_to_topological(result)
    print(f"\nResults stored to: {storage_path}")
    
    # Generate probe types
    print("\n" + "=" * 70)
    print("Probe Generation Test")
    print("=" * 70)
    
    generator = WaveprobeProbeGenerator()
    
    param_sweeps = generator.generate_parameter_sweep_probes()
    print(f"Parameter sweep probes: {len(param_sweeps)}")
    
    multi_seed = generator.generate_multi_seed_convergence_probes(num_seeds=5)
    print(f"Multi-seed probes: {len(multi_seed)}")
    
    bias_ablation = generator.generate_bias_ablation_comparison_probes()
    print(f"Bias ablation probes: {len(bias_ablation)}")
    
    stability = generator.generate_convergence_stability_probes()
    print(f"Stability probes: {len(stability)}")
    
    print("\n✅ Waveprobe adapter test completed successfully")


if __name__ == "__main__":
    main()
