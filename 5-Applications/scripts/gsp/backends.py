from abc import ABC, abstractmethod
import numpy as np
import hashlib
import json

# Phase 3 — Define VirtualSubstrateBackend

class VirtualSubstrateBackend(ABC):
    """
    VirtualSubstrateBackend:
      encode(a) -> θ
      program(θ) -> substrate_state
      sample(substrate_state, N, seed) -> histogram
      witness(histogram) -> Ω
      digest(a, θ, histogram, Ω, ν_eff) -> hash
    """
    
    @abstractmethod
    def encode(self, a: tuple[int, int, int]) -> dict:
        pass
        
    @abstractmethod
    def program(self, theta: dict) -> dict:
        pass
        
    @abstractmethod
    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        pass
        
    @abstractmethod
    def witness(self, histogram: dict) -> int:
        """Returns Q16.16 Ω"""
        pass
        
    def digest(self, a: tuple[int, int, int], theta: dict, histogram: dict, omega: int, nu_eff: int) -> str:
        payload = {
            "a": a,
            "theta": theta,
            "histogram": histogram,
            "omega": omega,
            "nu_eff": nu_eff
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

# Phase 4 — Build classical witness baseline

class ClassicalHeuristicBackend(VirtualSubstrateBackend):
    def __init__(self, c1=0.1, c2=0.1, c3=0.0):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.last_energy = 0
        
    def encode(self, a: tuple[int, int, int]) -> dict:
        # Converts Q16.16 to floats for classical calculation
        Q16_ONE = 1 << 16
        return {
            "a1": a[0] / Q16_ONE,
            "a2": a[1] / Q16_ONE,
            "a3": a[2] / Q16_ONE
        }

    def program(self, theta: dict) -> dict:
        return theta

    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        # Classical doesn't sample, just passes state
        return substrate_state

    def witness(self, histogram: dict) -> int:
        """
        Ω_classical = c₁ |a₁a₃| + c₂ |a₂a₃| + c₃ max(0, energy_growth)
        """
        a1 = histogram["a1"]
        a2 = histogram["a2"]
        a3 = histogram["a3"]
        
        current_energy = 0.5 * (a1**2 + a2**2 + a3**2)
        energy_growth = max(0.0, current_energy - self.last_energy)
        self.last_energy = current_energy
        
        omega_float = self.c1 * abs(a1 * a3) + self.c2 * abs(a2 * a3) + self.c3 * energy_growth
        
        # Convert to Q16.16
        Q16_ONE = 1 << 16
        omega_q16 = int(omega_float * Q16_ONE)
        return omega_q16

class EddyViscosityROMBackend(VirtualSubstrateBackend):
    def __init__(self, c_smag=0.1):
        self.c_smag = c_smag
        
    def encode(self, a: tuple[int, int, int]) -> dict:
        Q16_ONE = 1 << 16
        return {
            "a3": a[2] / Q16_ONE
        }

    def program(self, theta: dict) -> dict:
        return theta

    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        return substrate_state

    def witness(self, histogram: dict) -> int:
        """
        Smagorinsky-style eddy viscosity: scales with highest resolved mode.
        Ω_eddy = c_smag * |a3|
        """
        omega_float = self.c_smag * abs(histogram["a3"])
        Q16_ONE = 1 << 16
        return int(omega_float * Q16_ONE)


class LearnedClosureBaselineBackend(VirtualSubstrateBackend):
    def __init__(self):
        self.history = []
        
    def encode(self, a: tuple[int, int, int]) -> dict:
        Q16_ONE = 1 << 16
        return {
            "a": [x / Q16_ONE for x in a]
        }

    def program(self, theta: dict) -> dict:
        return theta

    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        return substrate_state

    def witness(self, histogram: dict) -> int:
        """
        Mock LSTM/NODE: nonlinear combination of recent history.
        Using a fixed random projection to simulate a latent-space closure.
        """
        a_current = histogram["a"]
        self.history.append(a_current)
        if len(self.history) > 3:
            self.history.pop(0)
            
        # Mock latent space extraction
        flat_hist = np.array(self.history).flatten()
        # Deterministic pseudo-random weights
        np.random.seed(42)
        weights = np.random.randn(len(flat_hist))
        
        omega_float = float(abs(np.tanh(np.dot(weights, flat_hist)) * 0.1))
        
        Q16_ONE = 1 << 16
        return int(omega_float * Q16_ONE)


class SoftwareTriangleBackend(VirtualSubstrateBackend):
    """Null backend that just returns 0 (No closure baseline)"""
    def encode(self, a: tuple[int, int, int]) -> dict:
        return {}
    def program(self, theta: dict) -> dict:
        return {}
    def sample(self, substrate_state: dict, N: int, seed: int) -> dict:
        return {}
    def witness(self, histogram: dict) -> int:
        return 0
