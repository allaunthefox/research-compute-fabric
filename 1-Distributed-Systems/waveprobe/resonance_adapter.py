#!/usr/bin/env python3
"""
Waveprobe Adapter for Resonance Analysis

This adapter extracts signal metrics from resonance patterns in the topology
and provides waveprobe-compatible interfaces for testing and validation.
"""

import json
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class ResonanceAnalysisAdapter:
    """Waveprobe adapter for resonance analysis."""
    
    def __init__(self):
        """Initialize adapter."""
        self.probe_id = f"wave_{uuid.uuid4().hex[:12]}"
        self.timestamp = datetime.now().isoformat()
        
        # Resonance types
        self.resonance_types = ["spherion", "pyramid", "waveform", "topology"]
        
    def execute_probe(self, probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a waveprobe probe on resonance patterns."""
        # Extract probe parameters
        time_steps = probe_config.get("time_steps", 1000)
        dt = probe_config.get("dt", 0.01)
        frequency_range = probe_config.get("frequency_range", (0.1, 1000.0))
        resonance_type = probe_config.get("resonance_type", "spherion")
        coupling_strength = probe_config.get("coupling_strength", 1.0)
        quality_factor = probe_config.get("quality_factor", 10.0)
        
        # Simulate resonance dynamics
        history = self._simulate_resonance_dynamics(
            time_steps, dt, frequency_range, resonance_type, coupling_strength, quality_factor
        )
        
        # Extract metrics
        metrics = self._extract_metrics(history, probe_config)
        
        # Validate resonance quality
        resonance_status = self._validate_resonance(metrics)
        
        # Build result
        result = {
            "probe_id": self.probe_id,
            "probe_config": probe_config,
            "execution_timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "resonance_status": resonance_status,
            "history": history
        }
        
        return result
    
    def _simulate_resonance_dynamics(
        self, 
        time_steps: int, 
        dt: float, 
        frequency_range: Tuple[float, float],
        resonance_type: str,
        coupling_strength: float,
        quality_factor: float
    ) -> Dict[str, Any]:
        """Simulate resonance dynamics."""
        
        # Initialize resonance parameters
        f_min, f_max = frequency_range
        t = 0.0
        omega_res = 2 * np.pi * np.sqrt(coupling_strength / 1.0)  # Resonant frequency
        delta_omega = omega_res / quality_factor  # Linewidth
        
        # Trajectory storage
        time_trajectory = []
        amplitude_trajectory = []
        phase_trajectory = []
        frequency_trajectory = []
        quality_trajectory = []
        energy_trajectory = []
        standing_wave_nodes = []
        
        for step in range(time_steps):
            # Simulate resonance amplitude
            amplitude = self._compute_resonance_amplitude(t, omega_res, delta_omega, resonance_type)
            
            # Simulate phase evolution
            phase = omega_res * t + np.random.normal(0, 0.1)
            
            # Simulate frequency modulation
            frequency = omega_res / (2 * np.pi) + 0.1 * np.sin(2 * np.pi * 0.1 * t)
            
            # Simulate quality factor evolution
            q_factor = quality_factor * (1 + 0.05 * np.sin(2 * np.pi * 0.05 * t))
            
            # Compute resonance energy
            energy = amplitude ** 2 * q_factor
            
            # Identify standing wave nodes
            nodes = self._identify_standing_wave_nodes(t, omega_res, resonance_type)
            
            # Store trajectory
            time_trajectory.append(t)
            amplitude_trajectory.append(amplitude)
            phase_trajectory.append(phase)
            frequency_trajectory.append(frequency)
            quality_trajectory.append(q_factor)
            energy_trajectory.append(energy)
            standing_wave_nodes.append(nodes)
            
            t += dt
        
        return {
            "time": time_trajectory,
            "amplitude": amplitude_trajectory,
            "phase": phase_trajectory,
            "frequency": frequency_trajectory,
            "quality_factor": quality_trajectory,
            "energy": energy_trajectory,
            "standing_wave_nodes": standing_wave_nodes,
            "resonance_type": resonance_type
        }
    
    def _compute_resonance_amplitude(self, t: float, omega_res: float, delta_omega: float, resonance_type: str) -> float:
        """Compute resonance amplitude at time t."""
        # Lorentzian resonance profile
        omega = omega_res  # At resonance
        amplitude = 1.0 / np.sqrt((omega - omega_res)**2 + (delta_omega / 2)**2)
        
        # Modulate by resonance type
        if resonance_type == "spherion":
            amplitude *= 1.5  # Spherions have higher resonance
        elif resonance_type == "pyramid":
            amplitude *= 1.0
        elif resonance_type == "waveform":
            amplitude *= 0.8
        elif resonance_type == "topology":
            amplitude *= 1.2
        
        # Add temporal modulation
        amplitude *= (1 + 0.1 * np.sin(2 * np.pi * 0.1 * t))
        
        return amplitude
    
    def _identify_standing_wave_nodes(self, t: float, omega_res: float, resonance_type: str) -> List[float]:
        """Identify standing wave node positions."""
        # Simplified standing wave node identification
        if resonance_type == "spherion":
            # Spherical harmonics nodes
            nodes = [np.pi * n / 2 for n in range(4)]
        else:
            # 1D standing wave nodes
            wavelength = 2 * np.pi / omega_res
            nodes = [n * wavelength / 2 for n in range(4)]
        
        return nodes
    
    def _extract_metrics(self, history: Dict[str, Any], probe_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized metrics from resonance analysis."""
        amplitude_trajectory = history["amplitude"]
        frequency_trajectory = history["frequency"]
        quality_trajectory = history["quality_factor"]
        energy_trajectory = history["energy"]
        
        metrics = {
            "peak_amplitude": float(max(amplitude_trajectory)),
            "mean_amplitude": float(np.mean(amplitude_trajectory)),
            "amplitude_stability": self._compute_stability(amplitude_trajectory),
            "resonant_frequency": float(np.mean(frequency_trajectory)),
            "frequency_drift": float(np.std(frequency_trajectory)),
            "mean_quality_factor": float(np.mean(quality_trajectory)),
            "peak_energy": float(max(energy_trajectory)),
            "mean_energy": float(np.mean(energy_trajectory)),
            "energy_convergence": self._compute_convergence_rate(energy_trajectory),
            "standing_wave_node_count": int(len(history["standing_wave_nodes"][0])),
            "resonance_type": history["resonance_type"],
            "coupling_strength": probe_config.get("coupling_strength", 1.0),
            "total_time_steps": len(amplitude_trajectory)
        }
        return metrics
    
    def _validate_resonance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate resonance quality."""
        resonance_status = {
            "high_q_resonance": metrics["mean_quality_factor"] > 10.0,
            "stable_amplitude": metrics["amplitude_stability"] > 0.9,
            "narrow_bandwidth": metrics["frequency_drift"] < 0.1,
            "energy_converged": metrics["energy_convergence"] < 0.01,
            "standing_waves_present": metrics["standing_wave_node_count"] >= 2,
            "overall_status": "resonant" if (
                metrics["mean_quality_factor"] > 10.0 and
                metrics["amplitude_stability"] > 0.9
            ) else "non_resonant"
        }
        return resonance_status
    
    def _compute_stability(self, trajectory: List[float]) -> float:
        """Compute stability metric."""
        if len(trajectory) < 10:
            return 0.0
        
        tail_size = max(10, len(trajectory) // 10)
        tail = trajectory[-tail_size:]
        stability = 1.0 - float(np.std(tail) / (np.mean(np.abs(tail)) + 1e-10))
        return max(0.0, min(1.0, stability))
    
    def _compute_convergence_rate(self, trajectory: List[float]) -> float:
        """Compute convergence rate from trajectory."""
        if len(trajectory) < 10:
            return 1.0
        
        tail_size = max(10, len(trajectory) // 10)
        tail = trajectory[-tail_size:]
        convergence_rate = float(np.std(tail) / (np.mean(np.abs(tail)) + 1e-10))
        return convergence_rate
    
    def serialize_results(self, result: Dict[str, Any]) -> str:
        """Serialize results in waveprobe-compatible JSON format."""
        serialized = json.dumps(result, indent=2, default=str)
        return serialized
    
    def store_to_topological(self, result: Dict[str, Any], storage_path: Optional[str] = None) -> str:
        """Store results in topological storage (placeholder for ENE integration)."""
        storage_path = storage_path or f"data/waveprobes/resonance_analysis/{self.probe_id}.json"
        
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        serialized = self.serialize_results(result)
        Path(storage_path).write_text(serialized)
        
        return storage_path


class ResonanceProbeGenerator:
    """Generate waveprobe test probes for resonance analysis."""
    
    @staticmethod
    def generate_frequency_sweep_probes() -> List[Dict[str, Any]]:
        """Generate frequency sweep probes."""
        probes = []
        
        # Sweep frequency range
        for f_range in [(0.1, 10.0), (1.0, 100.0), (10.0, 1000.0)]:
            probes.append({
                "probe_type": "frequency_sweep",
                "frequency_range": f_range,
                "time_steps": 1000,
                "dt": 0.01,
                "resonance_type": "spherion",
                "coupling_strength": 1.0,
                "quality_factor": 10.0,
                "description": f"Sweep frequency_range={f_range}"
            })
        
        return probes
    
    @staticmethod
    def generate_coupling_sweep_probes() -> List[Dict[str, Any]]:
        """Generate coupling strength sweep probes."""
        probes = []
        
        # Sweep coupling strength
        for coupling in [0.5, 1.0, 2.0]:
            probes.append({
                "probe_type": "coupling_sweep",
                "frequency_range": (0.1, 100.0),
                "time_steps": 1000,
                "dt": 0.01,
                "resonance_type": "spherion",
                "coupling_strength": coupling,
                "quality_factor": 10.0,
                "description": f"Sweep coupling_strength={coupling}"
            })
        
        return probes
    
    @staticmethod
    def generate_quality_factor_probes() -> List[Dict[str, Any]]:
        """Generate quality factor sweep probes."""
        probes = []
        
        # Sweep quality factor
        for q_factor in [5.0, 10.0, 20.0]:
            probes.append({
                "probe_type": "quality_factor_sweep",
                "frequency_range": (0.1, 100.0),
                "time_steps": 1000,
                "dt": 0.01,
                "resonance_type": "spherion",
                "coupling_strength": 1.0,
                "quality_factor": q_factor,
                "description": f"Sweep quality_factor={q_factor}"
            })
        
        return probes
    
    @staticmethod
    def generate_resonance_type_probes() -> List[Dict[str, Any]]:
        """Generate resonance type comparison probes."""
        probes = []
        
        # Compare resonance types
        for res_type in ["spherion", "pyramid", "waveform", "topology"]:
            probes.append({
                "probe_type": "resonance_type_comparison",
                "frequency_range": (0.1, 100.0),
                "time_steps": 1000,
                "dt": 0.01,
                "resonance_type": res_type,
                "coupling_strength": 1.0,
                "quality_factor": 10.0,
                "description": f"Resonance type: {res_type}"
            })
        
        return probes


def main():
    """Main entry point for testing the adapter."""
    print("=" * 70)
    print("Waveprobe Adapter for Resonance Analysis")
    print("=" * 70)
    
    # Initialize adapter
    adapter = ResonanceAnalysisAdapter()
    print(f"Adapter initialized: {adapter.probe_id}")
    
    # Test with a simple probe
    probe_config = {
        "probe_type": "test",
        "frequency_range": (0.1, 100.0),
        "time_steps": 1000,
        "dt": 0.01,
        "resonance_type": "spherion",
        "coupling_strength": 1.0,
        "quality_factor": 10.0
    }
    
    print(f"\nExecuting probe: {probe_config}")
    result = adapter.execute_probe(probe_config)
    
    print(f"\nProbe execution completed")
    print(f"Peak Amplitude: {result['metrics']['peak_amplitude']:.6f}")
    print(f"Resonant Frequency: {result['metrics']['resonant_frequency']:.6f} Hz")
    print(f"Mean Quality Factor: {result['metrics']['mean_quality_factor']:.6f}")
    print(f"Peak Energy: {result['metrics']['peak_energy']:.6f}")
    print(f"Standing Wave Nodes: {result['metrics']['standing_wave_node_count']}")
    print(f"Resonance Status: {result['resonance_status']['overall_status']}")
    
    # Store results
    storage_path = adapter.store_to_topological(result)
    print(f"\nResults stored to: {storage_path}")
    
    # Generate probe types
    print("\n" + "=" * 70)
    print("Probe Generation Test")
    print("=" * 70)
    
    generator = ResonanceProbeGenerator()
    
    frequency_sweeps = generator.generate_frequency_sweep_probes()
    print(f"Frequency sweep probes: {len(frequency_sweeps)}")
    
    coupling_sweeps = generator.generate_coupling_sweep_probes()
    print(f"Coupling sweep probes: {len(coupling_sweeps)}")
    
    quality_factor_probes = generator.generate_quality_factor_probes()
    print(f"Quality factor probes: {len(quality_factor_probes)}")
    
    resonance_type_probes = generator.generate_resonance_type_probes()
    print(f"Resonance type probes: {len(resonance_type_probes)}")
    
    print("\n✅ Resonance analysis waveprobe adapter test completed successfully")


if __name__ == "__main__":
    main()
