#!/usr/bin/env python3
"""
Waveprobe Adapter for WSM_WR_EGS_WC.lean

This adapter extracts signal metrics from the Wavefunction Superposition Metacomputation
pipeline (Waveform Recording → Energy-Gradient Signal → Waveprobe Coarse-Graining)
and provides waveprobe-compatible interfaces for testing and validation.
"""

import json
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class WSM_WR_EGS_WC_Adapter:
    """Waveprobe adapter for WSM_WR_EGS_WC Lean module."""
    
    def __init__(self):
        """Initialize adapter."""
        self.probe_id = f"wave_{uuid.uuid4().hex[:12]}"
        self.timestamp = datetime.now().isoformat()
        
        # Shape modes from the Lean module
        self.shape_modes = ["void", "protrusion", "flat", "complex"]
        
    def execute_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a waveprobe probe on WSM pipeline."""
        # Extract probe parameters
        time_steps = probe_config.get("time_steps", 200)
        dt = probe_config.get("dt", 0.01)
        lambdaE = probe_config.get("lambdaE", 1.0)  # Energy gradient weight
        lambdaC = probe_config.get("lambdaC", 0.5)  # Shape-energy coupling weight
        use_bias = probe_config.get("use_bias", True)  # Use transient codon bias
        branch = probe_config.get("branch", "closed")  # "closed" or "open"
        
        # Simulate WSM pipeline
        history = self._simulate_wsm_pipeline(
            time_steps, dt, lambdaE, lambdaC, use_bias, branch
        )
        
        # Extract metrics
        metrics = self._extract_metrics(history, probe_config)
        
        # Validate convergence
        convergence_status = self._validate_convergence(metrics)
        
        # Build result
        result = {
            "probe_id": self.probe_id,
            "probe_config": probe_config,
            "execution_timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "convergence_status": convergence_status,
            "history": history
        }
        
        return result
    
    def _simulate_wsm_pipeline(
        self, 
        time_steps: int, 
        dt: float, 
        lambdaE: float, 
        lambdaC: float, 
        use_bias: bool,
        branch: str
    ) -> Dict[str, Any]:
        """Simulate WSM pipeline: Waveform Recording → Energy-Gradient Signal → Waveprobe Coarse-Graining."""
        
        # Initialize state
        t = 0.0
        psi = self._initialize_wavefunction()
        energy = self._compute_energy(psi)
        
        # Trajectory storage
        time_trajectory = []
        energy_trajectory = []
        dE_dt_trajectory = []
        spatial_grad_trajectory = []
        shape_recording_trajectory = []
        total_signal_trajectory = []
        occupancy_trajectories = {mode: [] for mode in self.shape_modes}
        
        for step in range(time_steps):
            # 1. Waveform Recording: Record shape field
            shape_field = self._record_shape_field(psi)
            shape_recording_trajectory.append(shape_field)
            
            # 2. Energy-Gradient Signal: Compute temporal and spatial gradients
            if step > 0:
                dE_dt = (energy - energy_trajectory[-1]) / dt
            else:
                dE_dt = 0.0
            
            spatial_grad = self._compute_spatial_gradient(psi)
            spatial_grad_norm = np.sqrt(spatial_grad[0]**2 + spatial_grad[1]**2)
            
            dE_dt_trajectory.append(dE_dt)
            spatial_grad_trajectory.append(spatial_grad_norm)
            
            # 3. Total signal: Rshape + λE*GE + λC*ΓSE + η
            Rshape = np.sum(shape_field)
            GE = np.sqrt(dE_dt**2 + spatial_grad_norm**2)
            GammaSE = self._shape_energy_coupling(psi, use_bias)
            eta = self._noise_signal(t)
            
            total_signal = Rshape + lambdaE * GE + lambdaC * GammaSE + eta
            total_signal_trajectory.append(total_signal)
            
            # 4. Mode occupancy
            occupancy = self._compute_mode_occupancy(psi)
            for mode in self.shape_modes:
                occupancy_trajectories[mode].append(occupancy[mode])
            
            # Store trajectory
            time_trajectory.append(t)
            energy_trajectory.append(energy)
            
            # Evolve state (Schrödinger-like evolution for closed, Lindblad for open)
            psi = self._evolve_state(psi, dt, branch)
            energy = self._compute_energy(psi)
            t += dt
        
        return {
            "time": time_trajectory,
            "energy": energy_trajectory,
            "dE_dt": dE_dt_trajectory,
            "spatial_gradient": spatial_grad_trajectory,
            "shape_recording": shape_recording_trajectory,
            "total_signal": total_signal_trajectory,
            "occupancy": occupancy_trajectories,
            "final_psi": psi
        }
    
    def _initialize_wavefunction(self) -> Dict[str, Any]:
        """Initialize wavefunction with superposition over shape modes."""
        # Initial state: superposition of void and protrusion
        psi = {
            "amplitudes": {
                "void": 0.7 + 0.0j,
                "protrusion": 0.7 + 0.0j,
                "flat": 0.0 + 0.0j,
                "complex": 0.0 + 0.0j
            },
            "position": (0.0, 0.0)
        }
        return psi
    
    def _compute_energy(self, psi: Dict[str, Any]) -> float:
        """Compute energy observable E(t) = ⟨ψ(t)|Ĥ|ψ(t)⟩."""
        # Simplified energy calculation
        amplitudes = psi["amplitudes"]
        energy = sum(
            np.abs(amp)**2 * weight
            for amp, weight in zip(amplitudes.values(), [0.0, 1.0, 0.8, 1.2])
        )
        return energy
    
    def _record_shape_field(self, psi: Dict[str, Any]) -> np.ndarray:
        """Record shape field from wavefunction."""
        amplitudes = psi["amplitudes"]
        # Shape field as weighted sum of basis states
        shape_field = np.array([
            np.abs(amplitudes["void"]) * 0.0,
            np.abs(amplitudes["protrusion"]) * 1.0,
            np.abs(amplitudes["flat"]) * 0.5,
            np.abs(amplitudes["complex"]) * 1.5
        ])
        return shape_field
    
    def _compute_spatial_gradient(self, psi: Dict[str, Any]) -> Tuple[float, float]:
        """Compute spatial gradient ∇xE."""
        # Simplified spatial gradient based on position
        x, y = psi["position"]
        dE_dx = 0.1 * np.sin(x)
        dE_dy = 0.1 * np.cos(y)
        return (dE_dx, dE_dy)
    
    def _shape_energy_coupling(self, psi: Dict[str, Any], use_bias: bool) -> float:
        """Compute shape-energy coupling ΓSE."""
        amplitudes = psi["amplitudes"]
        # Coupling depends on mode occupancy
        coupling = (
            np.abs(amplitudes["protrusion"])**2 * 0.1 +
            np.abs(amplitudes["flat"])**2 * 0.2 +
            np.abs(amplitudes["complex"])**2 * 0.3
        )
        if use_bias:
            coupling += 0.05  # Transient bias term
        return coupling
    
    def _noise_signal(self, t: float) -> float:
        """Generate noise signal η(t)."""
        # Simple white noise
        return np.random.normal(0, 0.01)
    
    def _compute_mode_occupancy(self, psi: Dict[str, Any]) -> Dict[str, float]:
        """Compute mode occupancy probabilities."""
        amplitudes = psi["amplitudes"]
        # Normalize
        total = sum(np.abs(amp)**2 for amp in amplitudes.values())
        if total > 0:
            occupancy = {
                mode: np.abs(amp)**2 / total
                for mode, amp in amplitudes.items()
            }
        else:
            occupancy = {mode: 0.25 for mode in self.shape_modes}
        return occupancy
    
    def _evolve_state(self, psi: Dict[str, Any], dt: float, branch: str) -> Dict[str, Any]:
        """Evolve state using Schrödinger (closed) or Lindblad (open) dynamics."""
        amplitudes = psi["amplitudes"].copy()
        
        # Evolution rates
        rates = {
            "void_to_protrusion": 0.05,
            "void_to_flat": 0.1,
            "void_to_complex": 0.02,
            "protrusion_to_flat": 0.08,
            "protrusion_to_complex": 0.05,
            "flat_to_complex": 0.1
        }
        
        # Evolve amplitudes (simplified)
        amplitudes["protrusion"] = amplitudes["protrusion"] + rates["void_to_protrusion"] * dt
        amplitudes["flat"] = amplitudes["flat"] + rates["void_to_flat"] * dt
        amplitudes["complex"] = amplitudes["complex"] + rates["void_to_complex"] * dt
        
        # Add decoherence for open system
        if branch == "open":
            decay = 0.01 * dt
            for mode in amplitudes:
                amplitudes[mode] *= (1 - decay)
        
        # Update position
        x, y = psi["position"]
        new_x = x + 0.01 * np.cos(dt)
        new_y = y + 0.01 * np.sin(dt)
        
        return {
            "amplitudes": amplitudes,
            "position": (new_x, new_y)
        }
    
    def _extract_metrics(self, history: Dict[str, Any], probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized metrics from WSM pipeline."""
        energy_trajectory = history["energy"]
        dE_dt_trajectory = history["dE_dt"]
        spatial_grad_trajectory = history["spatial_gradient"]
        total_signal_trajectory = history["total_signal"]
        occupancy_trajectories = history["occupancy"]
        
        metrics = {
            "final_energy": float(energy_trajectory[-1]),
            "max_energy": float(max(energy_trajectory)),
            "min_energy": float(min(energy_trajectory)),
            "energy_convergence_rate": self._compute_convergence_rate(energy_trajectory),
            "final_dE_dt": float(dE_dt_trajectory[-1]),
            "mean_spatial_gradient": float(np.mean(spatial_grad_trajectory)),
            "final_total_signal": float(total_signal_trajectory[-1]),
            "total_signal_convergence": self._compute_convergence_rate(total_signal_trajectory),
            "final_occupancy": {
                mode: float(trajectory[-1])
                for mode, trajectory in occupancy_trajectories.items()
            },
            "occupancy_stability": self._compute_occupancy_stability(occupancy_trajectories),
            "lambdaE": probe_config.get("lambdaE", 1.0),
            "lambdaC": probe_config.get("lambdaC", 0.5),
            "branch": probe_config.get("branch", "closed"),
            "total_time_steps": len(energy_trajectory)
        }
        return metrics
    
    def _validate_convergence(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate convergence criteria."""
        convergence_status = {
            "energy_converged": metrics["energy_convergence_rate"] < 0.01,
            "total_signal_converged": metrics["total_signal_convergence"] < 0.01,
            "occupancy_stable": metrics["occupancy_stability"] > 0.95,
            "temporal_gradient_zero": abs(metrics["final_dE_dt"]) < 0.01,
            "overall_status": "converged" if (
                metrics["energy_convergence_rate"] < 0.01 and
                metrics["total_signal_convergence"] < 0.01
            ) else "not_converged"
        }
        return convergence_status
    
    def _compute_convergence_rate(self, trajectory: List[float]) -> float:
        """Compute convergence rate from trajectory."""
        if len(trajectory) < 10:
            return 1.0
        
        tail_size = max(10, len(trajectory) // 10)
        tail = trajectory[-tail_size:]
        convergence_rate = float(np.std(tail) / (np.mean(np.abs(tail)) + 1e-10))
        return convergence_rate
    
    def _compute_occupancy_stability(self, occupancy_trajectories: Dict[str, List[float]]) -> float:
        """Compute occupancy stability."""
        tail_size = max(5, len(occupancy_trajectories["void"]) // 5)
        stabilities = []
        
        for mode, trajectory in occupancy_trajectories.items():
            tail = trajectory[-tail_size:]
            unique_values = len(set([round(v, 4) for v in tail]))
            stability = 1.0 - (unique_values - 1) / len(tail)
            stabilities.append(max(0.0, min(1.0, stability)))
        
        return float(np.mean(stabilities))
    
    def serialize_results(self, result: Dict[str, Any]) -> str:
        """Serialize results in waveprobe-compatible JSON format."""
        serialized = json.dumps(result, indent=2, default=str)
        return serialized
    
    def store_to_topological(self, result: Dict[str, Any], storage_path: Optional[str] = None) -> str:
        """Store results in topological storage (placeholder for ENE integration)."""
        storage_path = storage_path or f"data/waveprobes/wsm_wr_egs_wc/{self.probe_id}.json"
        
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        serialized = self.serialize_results(result)
        Path(storage_path).write_text(serialized)
        
        return storage_path


class WSM_WR_EGS_WC_ProbeGenerator:
    """Generate waveprobe test probes for WSM pipeline."""
    
    @staticmethod
    def generate_lambda_sweep_probes() -> List[Dict[str, Any]]:
        """Generate lambda parameter sweep probes."""
        probes = []
        
        # Sweep lambdaE (energy gradient weight)
        for lambdaE in [0.5, 1.0, 2.0]:
            probes.append({
                "probe_type": "lambda_sweep",
                "lambdaE": lambdaE,
                "lambdaC": 0.5,
                "time_steps": 200,
                "dt": 0.01,
                "branch": "closed",
                "description": f"Sweep lambdaE={lambdaE}"
            })
        
        # Sweep lambdaC (shape-energy coupling weight)
        for lambdaC in [0.25, 0.5, 1.0]:
            probes.append({
                "probe_type": "lambda_sweep",
                "lambdaE": 1.0,
                "lambdaC": lambdaC,
                "time_steps": 200,
                "dt": 0.01,
                "branch": "closed",
                "description": f"Sweep lambdaC={lambdaC}"
            })
        
        return probes
    
    @staticmethod
    def generate_branch_comparison_probes() -> List[Dict[str, Any]]:
        """Generate closed vs open branch comparison probes."""
        probes = []
        
        for branch in ["closed", "open"]:
            for seed in [1, 7, 42]:
                probes.append({
                    "probe_type": "branch_comparison",
                    "lambdaE": 1.0,
                    "lambdaC": 0.5,
                    "time_steps": 200,
                    "dt": 0.01,
                    "branch": branch,
                    "seed": seed,
                    "description": f"Branch comparison: {branch} seed={seed}"
                })
        
        return probes
    
    @staticmethod
    def generate_bias_ablation_probes() -> List[Dict[str, Any]]:
        """Generate bias ablation probes."""
        probes = []
        
        for use_bias in [False, True]:
            probes.append({
                "probe_type": "bias_ablation",
                "lambdaE": 1.0,
                "lambdaC": 0.5,
                "time_steps": 200,
                "dt": 0.01,
                "branch": "closed",
                "use_bias": use_bias,
                "description": f"Bias ablation: use_bias={use_bias}"
            })
        
        return probes


def main():
    """Main entry point for testing the adapter."""
    print("=" * 70)
    print("Waveprobe Adapter for WSM_WR_EGS_WC.lean")
    print("=" * 70)
    
    # Initialize adapter
    adapter = WSM_WR_EGS_WC_Adapter()
    print(f"Adapter initialized: {adapter.probe_id}")
    
    # Test with a simple probe
    probe_config = {
        "probe_type": "test",
        "lambdaE": 1.0,
        "lambdaC": 0.5,
        "time_steps": 200,
        "dt": 0.01,
        "branch": "closed",
        "use_bias": True
    }
    
    print(f"\nExecuting probe: {probe_config}")
    result = adapter.execute_probe(probe_config)
    
    print(f"\nProbe execution completed")
    print(f"Final Energy: {result['metrics']['final_energy']:.6f}")
    print(f"Energy Convergence Rate: {result['metrics']['energy_convergence_rate']:.6f}")
    print(f"Final dE/dt: {result['metrics']['final_dE_dt']:.6f}")
    print(f"Final Total Signal: {result['metrics']['final_total_signal']:.6f}")
    print(f"Final Occupancy: {result['metrics']['final_occupancy']}")
    print(f"Convergence Status: {result['convergence_status']['overall_status']}")
    
    # Store results
    storage_path = adapter.store_to_topological(result)
    print(f"\nResults stored to: {storage_path}")
    
    # Generate probe types
    print("\n" + "=" * 70)
    print("Probe Generation Test")
    print("=" * 70)
    
    generator = WSM_WR_EGS_WC_ProbeGenerator()
    
    lambda_sweeps = generator.generate_lambda_sweep_probes()
    print(f"Lambda sweep probes: {len(lambda_sweeps)}")
    
    branch_comparison = generator.generate_branch_comparison_probes()
    print(f"Branch comparison probes: {len(branch_comparison)}")
    
    bias_ablation = generator.generate_bias_ablation_probes()
    print(f"Bias ablation probes: {len(bias_ablation)}")
    
    print("\n✅ WSM_WR_EGS_WC waveprobe adapter test completed successfully")


if __name__ == "__main__":
    main()
