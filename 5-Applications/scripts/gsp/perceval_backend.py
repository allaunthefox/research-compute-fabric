import numpy as np
import perceval as pcvl
from .backends import VirtualSubstrateBackend

# Phase 5 — Build GeometryShaverPercevalBackend
# Implemented using the genuine Quandela Perceval SDK

class PercevalGeometryShaverBackend(VirtualSubstrateBackend):
    def __init__(self, M=6, exhaust_modes=(3, 4, 5)):
        self.M = M
        self.exhaust_modes = exhaust_modes
        
    def encode(self, a: tuple[int, int, int]) -> dict:
        Q16_ONE = 1 << 16
        a_f = [x / Q16_ONE for x in a]
        
        # Normalize and map to phase angles to encode signed modal amplitudes
        norm = np.linalg.norm(a_f)
        if norm < 1e-9:
            return {"theta": [0.0, 0.0, 0.0], "norm": 0.0}
            
        # Map amplitude to phase angle (e.g., theta = pi * (a / norm))
        theta = [float(np.pi * (x / norm)) for x in a_f]
        return {"theta": theta, "norm": float(norm)}

    def program(self, theta: dict) -> dict:
        # Return serialized parameters for AVMR digest
        return {
            "theta": theta["theta"],
            "norm": theta["norm"],
            "M": self.M
        }

    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        M = substrate_state["M"]
        theta = substrate_state["theta"]
        norm = substrate_state["norm"]
        
        if norm < 1e-9:
            return {str(i): 0.0 for i in range(M)}
            
        # Build the U_shear circuit
        circuit = pcvl.Circuit(M)
        # Phase encoding for modes 1-3
        for i in range(3):
            circuit.add(i, pcvl.PS(theta[i]))
            
        # Fixed exhaust structure: mix adjacent modes to shear
        for i in range(M - 1):
            circuit.add((i, i+1), pcvl.BS())
            
        # Input state: 1 photon in each of the first 3 modes (representing the triad)
        input_state = pcvl.BasicState([1, 1, 1] + [0] * (M - 3))
        
        # Processor
        processor = pcvl.Processor("SLOS", circuit)
        processor.with_input(input_state)
        
        # Sample
        sampler = pcvl.algorithm.Sampler(processor)
        res = sampler.sample_count(N)
        
        # Build histogram of photon detection in each mode
        hist = {str(i): 0.0 for i in range(M)}
        for state, count in res["results"].items():
            prob = count / N
            for mode, photons in enumerate(state):
                hist[str(mode)] += photons * prob
                
        # Scale back by total energy (norm^2) to make Omega proportional to physical scale
        for k in hist:
            hist[k] *= (norm**2)
            
        return hist

    def witness(self, histogram: dict) -> int:
        """
        Ω_Q = Σ_{y∈Exhaust} P̂_U(y)
        """
        omega_float = 0.0
        for m in self.exhaust_modes:
            omega_float += histogram.get(str(m), 0.0)
            
        # Convert to Q16.16
        Q16_ONE = 1 << 16
        return int(omega_float * Q16_ONE)
