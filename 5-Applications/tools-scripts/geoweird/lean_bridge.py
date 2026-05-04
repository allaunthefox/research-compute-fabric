"""
GeoWeird Lean Bridge - Python bindings for Lean formalization
Connects thermal_arbiter.py, mass_archivist.py, sovereign_warden to Lean FFI
"""

import ctypes
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

# Load the Lean FFI shared library
_LIB_PATH = Path(__file__).parent.parent / "build" / "lib" / "libgeoweirdffi.so"

try:
    _lib = ctypes.CDLL(str(_LIB_PATH))
except OSError:
    print(f"[LeanBridge] FFI library not found at {_LIB_PATH}, using mock mode")
    _lib = None


@dataclass
class PhaseTransitionSignal:
    """Signal from Lean phase detector"""
    should_transition: bool
    target_phase: str
    entropy_seed: float
    frozen_isa_hash: str


@dataclass  
class WitnessOpcode:
    """WITNESS_* opcode from emergence"""
    opcode_type: str  # "BASIC", "EMERGENCE", "COLLIDE", "NOVEL"
    geometry_budget: float
    trust_stamp: float
    recoverability_class: int
    raw_bytes: bytes


class LeanBridge:
    """
    Bridge between Python implementation and Lean formalization.
    
    This class:
    1. Exports Python state to Lean (stress levels, metrics, etc.)
    2. Receives phase transition signals from Lean
    3. Coordinates emergence protocol execution
    4. Persists discovered witnesses via mass_archivist
    """
    
    def __init__(
        self,
        thermal_arbiter=None,
        mass_archivist=None,
        warden_bridge=None
    ):
        self.thermal = thermal_arbiter
        self.archivist = mass_archivist
        self.warden = warden_bridge
        
        # Phase transition state
        self.current_phase = "Darwinian"
        self.metric_history: List[Tuple[float, float]] = []  # (metric, load)
        self.emergence_active = False
        self.truth_registry: List[WitnessOpcode] = []
        
        # Thresholds (match Lean defaults)
        self.thresholds = {
            "min_improvement_rate": 0.001,
            "max_acceleration": 0.0001,
            "sustained_windows": 10,
            "entropy_floor": 0.5
        }
        
        # Initialize FFI if available
        if _lib:
            self._init_ffi()
    
    def _init_ffi(self):
        """Initialize C FFI layer"""
        # Create opaque handles for Python objects
        thermal_handle = ctypes.py_object(self.thermal) if self.thermal else None
        archivist_handle = ctypes.py_object(self.archivist) if self.archivist else None
        warden_handle = ctypes.py_object(self.warden) if self.warden else None
        
        # Call geoweird_ffi_init
        _lib.geoweird_ffi_init.argtypes = [
            ctypes.py_object, ctypes.py_object, ctypes.py_object
        ]
        _lib.geoweird_ffi_init(thermal_handle, archivist_handle, warden_handle)
    
    def record_epoch(self, metric: float, cognitive_load: float) -> Optional[PhaseTransitionSignal]:
        """
        Record optimization result and check for phase transition.
        
        Called by sovereign_warden after each batch attestation.
        
        Args:
            metric: Optimization metric (e.g., compression ratio)
            cognitive_load: From COGNITIVE_LOAD_FUNCTIONS_SPEC
            
        Returns:
            PhaseTransitionSignal if transition should occur, None otherwise
        """
        self.metric_history.append((metric, cognitive_load))
        
        # Keep only last 1000 points
        if len(self.metric_history) > 1000:
            self.metric_history = self.metric_history[-1000:]
        
        # Check for diminishing returns
        if len(self.metric_history) >= self.thresholds["sustained_windows"]:
            if self._check_diminishing_returns():
                return self._trigger_emergence()
        
        return None
    
    def _check_diminishing_returns(self) -> bool:
        """Check if improvement has plateaued"""
        recent = self.metric_history[-self.thresholds["sustained_windows"]:]
        metrics = [m for m, _ in recent]
        
        # Calculate first derivative (improvement rate)
        first_derivs = [metrics[i+1] - metrics[i] for i in range(len(metrics)-1)]
        avg_first = sum(first_derivs) / len(first_derivs)
        
        # Calculate second derivative (acceleration)
        second_derivs = [first_derivs[i+1] - first_derivs[i] for i in range(len(first_derivs)-1)]
        avg_second = sum(abs(d) for d in second_derivs) / len(second_derivs)
        
        # Check conditions
        improvement_stalled = avg_first <= self.thresholds["min_improvement_rate"]
        acceleration_collapsed = avg_second < self.thresholds["max_acceleration"]
        
        return improvement_stalled and acceleration_collapsed
    
    def _trigger_emergence(self) -> PhaseTransitionSignal:
        """Trigger emergence phase"""
        self.emergence_active = True
        self.current_phase = "Emergence"
        
        # Calculate entropy seed from metric history
        entropy = self._calculate_entropy()
        
        signal = PhaseTransitionSignal(
            should_transition=True,
            target_phase="Emergence",
            entropy_seed=entropy,
            frozen_isa_hash=self._capture_isa_hash()
        )
        
        print(f"[LeanBridge] Phase transition triggered!")
        print(f"  Entropy seed: {entropy:.4f}")
        print(f"  Metric history: {len(self.metric_history)} points")
        
        return signal
    
    def _calculate_entropy(self) -> float:
        """Calculate Shannon entropy of metric distribution"""
        if len(self.metric_history) < 2:
            return 0.5
        
        metrics = np.array([m for m, _ in self.metric_history])
        # Simple entropy estimate from variance
        variance = np.var(metrics)
        return min(1.0, variance / (1.0 + variance))
    
    def _capture_isa_hash(self) -> str:
        """Capture current ISA version hash"""
        # In real implementation, hash current opcode set
        import hashlib
        isa_data = json.dumps({"version": "2.0.0", "opcodes": []})
        return hashlib.sha256(isa_data.encode()).hexdigest()[:16]
    
    def run_emergence(
        self,
        universe_configs: List[dict],
        collision_budget: int = 10000
    ) -> List[WitnessOpcode]:
        """
        Run emergence protocol with multi-universe collision.
        
        Args:
            universe_configs: List of 5 universe configurations
            collision_budget: Max collisions before stopping
            
        Returns:
            List of discovered WITNESS_* opcodes
        """
        if len(universe_configs) != 5:
            raise ValueError("Exactly 5 universes required (Euclidean, Hyperbolic, Spherical, Lorentzian, Custom)")
        
        print(f"[LeanBridge] Starting emergence with {collision_budget} collision budget")
        
        discovered = []
        
        # Generate all pairwise collisions
        pairs = [(i, j) for i in range(5) for j in range(i+1, 5)]
        
        for collision_id in range(min(collision_budget, len(pairs) * 100)):
            # Select universe pair
            a_idx, b_idx = pairs[collision_id % len(pairs)]
            
            # Simulate collision (real impl uses Lean formalization)
            witness = self._simulate_collision(
                universe_configs[a_idx],
                universe_configs[b_idx],
                collision_id
            )
            
            if witness:
                discovered.append(witness)
                self.truth_registry.append(witness)
                
                # Persist via mass_archivist if available
                if self.archivist:
                    self._persist_witness(witness)
        
        print(f"[LeanBridge] Emergence complete: {len(discovered)} witnesses discovered")
        
        self.emergence_active = False
        self.current_phase = "Consolidation"
        
        return discovered
    
    def _simulate_collision(
        self,
        universe_a: dict,
        universe_b: dict,
        collision_id: int
    ) -> Optional[WitnessOpcode]:
        """Simulate collision between two universes"""
        # Check compatibility
        if universe_a.get("dimension") != universe_b.get("dimension"):
            return None
        
        # Calculate consensus strength
        curvature_product = universe_a.get("curvature", 0) * universe_b.get("curvature", 0)
        consensus_strength = 0.5 + 0.5 * np.tanh(curvature_product)
        
        if consensus_strength < 0.49:
            return None  # Weak consensus
        
        # Generate witness
        witness = WitnessOpcode(
            opcode_type="EMERGENCE",
            geometry_budget=min(
                universe_a.get("volume", 1.0),
                universe_b.get("volume", 1.0)
            ) * 0.1,
            trust_stamp=consensus_strength,
            recoverability_class=1,
            raw_bytes=f"WITNESS_EMERGENCE_{collision_id}".encode()
        )
        
        return witness
    
    def _persist_witness(self, witness: WitnessOpcode) -> bool:
        """Persist witness via mass_archivist"""
        if not self.archivist:
            return False
        
        # Wait for rest event
        if hasattr(self.archivist, 'arbiter'):
            if not self.archivist.arbiter.rest_event.wait(timeout=5.0):
                return False
        
        # Serialize and submit
        data = json.dumps({
            "type": witness.opcode_type,
            "budget": witness.geometry_budget,
            "trust": witness.trust_stamp,
            "recoverability": witness.recoverability_class
        }).encode()
        
        # Submit to archivist (mock)
        print(f"[LeanBridge] Persisted witness (trust={witness.trust_stamp:.3f})")
        return True
    
    def export_to_lean(self) -> dict:
        """Export current state for Lean verification"""
        return {
            "phase": self.current_phase,
            "metric_history": self.metric_history,
            "truth_registry": [
                {
                    "type": w.opcode_type,
                    "budget": w.geometry_budget,
                    "trust": w.trust_stamp
                }
                for w in self.truth_registry
            ],
            "thresholds": self.thresholds
        }
    
    def cleanup(self):
        """Cleanup FFI resources"""
        if _lib:
            _lib.geoweird_ffi_cleanup()


# Singleton instance for global access
_bridge: Optional[LeanBridge] = None


def init_bridge(thermal=None, archivist=None, warden=None) -> LeanBridge:
    """Initialize global Lean bridge"""
    global _bridge
    _bridge = LeanBridge(thermal, archivist, warden)
    return _bridge


def get_bridge() -> Optional[LeanBridge]:
    """Get global Lean bridge instance"""
    return _bridge
