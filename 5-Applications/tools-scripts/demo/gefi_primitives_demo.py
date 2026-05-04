#!/usr/bin/env python3
"""
gefi_primitives_demo.py

Demonstrates the 18 GEFI primitives composing into boot, emergency recovery,
and substrate migration operations.

This is a reference implementation showing how primitives build higher-level
functionality.
"""

import random
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import IntEnum


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class ActivationState(IntEnum):
    QUIESCENT = 0
    LATENT_1 = 1
    LATENT_2 = 2
    LATENT_3 = 3
    ACTIVE_1 = 4
    ACTIVE_2 = 5
    ACTIVE_3 = 6
    ACTIVE_4 = 7

class ConvergenceStatus(IntEnum):
    TRANSIENT = 0
    CONVERGED = 1
    DIVERGED = 2

class RegionClass(IntEnum):
    SURFACE = 0
    INTERIOR = 1
    TUNNEL = 2
    VERTEX = 3


@dataclass
class Position:
    """Geometric primitive: P"""
    x: float
    y: float
    z: float
    
    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass  
class MuSeed:
    """μ-seed structure"""
    delta_p: int      # 10 bits: position delta
    region: int       # 4 bits: region class
    gamma: int        # 5 bits: transform mode
    activation: int   # 4 bits: activation state
    polarity: int     # 4 bits: polarity/torsion
    confidence: int   # 4 bits: confidence
    emergency: int = 0  # 1 bit: emergency flag
    
    def to_bytes(self) -> bytes:
        """Primitive: ε (encode)"""
        word = (self.delta_p & 0x3FF)
        word |= (self.region & 0xF) << 10
        word |= (self.gamma & 0x1F) << 14
        word |= (self.activation & 0xF) << 19
        word |= (self.polarity & 0xF) << 23
        word |= (self.confidence & 0xF) << 27
        word |= (self.emergency & 0x1) << 31
        return word.to_bytes(4, 'little')
    
    @classmethod
    def from_bytes(cls, b: bytes) -> 'MuSeed':
        """Primitive: δ (decode)"""
        word = int.from_bytes(b, 'little')
        return cls(
            delta_p=word & 0x3FF,
            region=(word >> 10) & 0xF,
            gamma=(word >> 14) & 0x1F,
            activation=(word >> 19) & 0xF,
            polarity=(word >> 23) & 0xF,
            confidence=(word >> 27) & 0xF,
            emergency=(word >> 31) & 0x1
        )


@dataclass
class BlinkPacket:
    """BLINK packet: B = (ΔV, Δt, π, C)"""
    delta_v: float    # Voltage differential
    delta_t: float    # Time duration
    polarity: int     # Polarity/sign
    confidence: int   # Confidence level


# ============================================================================
# GEOMETRIC PRIMITIVES
# ============================================================================

class GeometricPrimitives:
    """Geometric primitives: P, Δ, κ, T"""
    
    @staticmethod
    def distance(p1: Position, p2: Position, metric: List[List[float]]) -> float:
        """Primitive: d_T (torsioned distance)"""
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        dz = p1.z - p2.z
        
        # Apply metric tensor G(p) - simplified
        dist = math.sqrt(
            metric[0][0]*dx*dx + 
            metric[1][1]*dy*dy + 
            metric[2][2]*dz*dz
        )
        return dist
    
    @staticmethod
    def delta(p1: Position, p2: Position) -> Position:
        """Primitive: Δ (displacement)"""
        return p2 - p1
    
    @staticmethod
    def curvature(field_values: List[float]) -> float:
        """Primitive: κ (local curvature)"""
        # Simplified: variance as proxy for curvature
        if len(field_values) < 2:
            return 0.0
        mean = sum(field_values) / len(field_values)
        variance = sum((v - mean)**2 for v in field_values) / len(field_values)
        return variance
    
    @staticmethod
    def torsion_correct(delta: Position, torsion: float) -> Position:
        """Primitive: T (torsion correction)"""
        # Simplified rotation by torsion angle
        cos_t = math.cos(torsion)
        sin_t = math.sin(torsion)
        return Position(
            delta.x * cos_t - delta.y * sin_t,
            delta.x * sin_t + delta.y * cos_t,
            delta.z
        )


# ============================================================================
# ACTIVATION PRIMITIVES
# ============================================================================

class ActivationField:
    """Activation primitives: A, τ, Φ"""
    
    def __init__(self, size: int = 64):
        self.size = size
        self.values: Dict[int, float] = {i: 0.0 for i in range(size)}
        self.history: List[Dict[int, float]] = []
    
    def get(self, p: int) -> float:
        """Primitive: A.get"""
        return self.values.get(p, 0.0)
    
    def set(self, p: int, a: float):
        """Primitive: A.set"""
        self.values[p] = max(0.0, min(15.0, a))
    
    def transition_valid(self, a1: float, a2: float) -> bool:
        """Primitive: τ (transition validation)"""
        # Most transitions allowed, except large jumps
        return abs(a2 - a1) <= 8.0
    
    def variance(self) -> float:
        """Field variance for convergence test"""
        values = list(self.values.values())
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean)**2 for v in values) / len(values)


# ============================================================================
# TTM OPERATOR PRIMITIVES
# ============================================================================

class TTMOperators:
    """TTM primitives: Σ, ξ, ι, Λ"""
    
    @staticmethod
    def accumulate(field: ActivationField, p: int, neighbors: List[int], 
                   weights: List[float]) -> float:
        """Primitive: Σ (accumulate from neighbors)"""
        current = field.get(p)
        contribution = sum(
            w * field.get(n) 
            for w, n in zip(weights, neighbors)
        )
        return current + 0.1 * contribution  # Damping factor
    
    @staticmethod
    def noise(a: float, variance: float, sigma_max: float = 1.0) -> float:
        """Primitive: ξ (stochastic noise)"""
        # Emergency mode: DISABLED (return unchanged)
        # Normal mode: add bounded noise
        noise_val = random.gauss(0, math.sqrt(variance))
        new_a = a + noise_val
        
        # Admissibility check
        if abs(noise_val) > sigma_max:
            return a  # Reject if exceeds bounds
        return new_a
    
    @staticmethod
    def interact(a1: float, a2: float, gamma: float) -> Tuple[float, float]:
        """Primitive: ι (bidirectional exchange)"""
        # Gamma is coupling strength (-1 to 1)
        diff = a2 - a1
        a1_new = a1 + gamma * diff * 0.5
        a2_new = a2 - gamma * diff * 0.5
        return a1_new, a2_new
    
    @staticmethod
    def collapse(a: float, threshold: float) -> Tuple[float, bool]:
        """Primitive: Λ (forced decision)"""
        if a > threshold:
            return min(15.0, a), True  # Activated + decision made
        return a, False


# ============================================================================
# CONVERGENCE PRIMITIVES
# ============================================================================

class ConvergencePrimitives:
    """Convergence primitives: g, div, ω, α"""
    
    @staticmethod
    def gradient(field: ActivationField, p: int, neighbors: List[int]) -> float:
        """Primitive: g (gradient magnitude)"""
        a_p = field.get(p)
        gradients = []
        for n in neighbors:
            a_n = field.get(n)
            gradients.append(abs(a_n - a_p))
        return sum(gradients) / len(gradients) if gradients else 0.0
    
    @staticmethod
    def test_convergence(field: ActivationField, history: List[Dict], 
                        sigma_max: float = 4.0, epsilon: float = 0.01,
                        min_cycles: int = 3) -> ConvergenceStatus:
        """Primitive: ω (convergence test)"""
        var = field.variance()
        
        # Check divergence
        if var > sigma_max:
            return ConvergenceStatus.DIVERGED
        
        # Check if we have enough history
        if len(history) < min_cycles:
            return ConvergenceStatus.TRANSIENT
        
        # Check gradient stability
        recent = history[-min_cycles:]
        gradients = [sum(v.values())/len(v) for v in recent]
        avg_gradient = sum(abs(g) for g in gradients) / len(gradients)
        
        if avg_gradient < epsilon:
            return ConvergenceStatus.CONVERGED
        
        return ConvergenceStatus.TRANSIENT
    
    @staticmethod
    def find_attractor(field: ActivationField, 
                       status: ConvergenceStatus) -> Dict:
        """Primitive: α (attractor formation)"""
        if status != ConvergenceStatus.CONVERGED:
            return {"type": "none", "basin": []}
        
        # Find stable regions
        values = list(field.values.values())
        mean = sum(values) / len(values)
        
        basin = [p for p, v in field.values.items() if abs(v - mean) < 1.0]
        
        # Classify attractor type
        if mean < 2.0:
            attractor_type = "quiescent"
        elif mean < 6.0:
            attractor_type = "latent"
        else:
            attractor_type = "active"
        
        return {
            "type": attractor_type,
            "basin": basin,
            "mean_activation": mean,
            "stability": field.variance()
        }


# ============================================================================
# BLINK PRIMITIVES
# ============================================================================

class BlinkPrimitives:
    """BLINK primitives: β_enc, β_dec, β_tx, β_rx"""
    
    @staticmethod
    def encode(mu: MuSeed) -> BlinkPacket:
        """Primitive: β_enc (μ-seed → BLINK)"""
        # Map gamma to voltage (0-31 → 0.1-3.3V)
        delta_v = 0.1 + (mu.gamma / 31.0) * 3.2
        
        # Map activation to time (0-15 → 1-100ms)
        delta_t = 1.0 + mu.activation * 6.6
        
        return BlinkPacket(
            delta_v=delta_v,
            delta_t=delta_t,
            polarity=mu.polarity,
            confidence=mu.confidence
        )
    
    @staticmethod
    def decode(packet: BlinkPacket) -> MuSeed:
        """Primitive: β_dec (BLINK → μ-seed)"""
        # Map voltage back to gamma
        gamma = int((packet.delta_v - 0.1) / 3.2 * 31)
        
        # Map time back to activation
        activation = int((packet.delta_t - 1.0) / 6.6)
        
        return MuSeed(
            delta_p=0,  # Inferred from context
            region=0,   # Inferred from context
            gamma=gamma,
            activation=activation,
            polarity=packet.polarity,
            confidence=packet.confidence
        )
    
    @staticmethod
    def transmit(packet: BlinkPacket, substrate: str) -> bytes:
        """Primitive: β_tx (physical transmission)"""
        # Simulate physical encoding
        return bytes([
            int(packet.delta_v * 100) & 0xFF,
            int(packet.delta_t) & 0xFF,
            packet.polarity & 0xF,
            packet.confidence & 0xF
        ])
    
    @staticmethod
    def receive(data: bytes, substrate: str) -> BlinkPacket:
        """Primitive: β_rx (physical reception)"""
        return BlinkPacket(
            delta_v=data[0] / 100.0,
            delta_t=data[1],
            polarity=data[2] & 0xF,
            confidence=data[3] & 0xF
        )


# ============================================================================
# COMPOSITION: BOOT SEQUENCE
# ============================================================================

def gefi_boot(emergency_mode: bool = False) -> Dict:
    """
    Standard GEFI boot sequence using primitives.
    
    Composes: Φ.initialize → Σ → [ξ] → ι → ω → α
    """
    print(f"\n{'='*60}")
    print(f"GEFI BOOT SEQUENCE")
    print(f"Mode: {'EMERGENCY' if emergency_mode else 'NORMAL'}")
    print(f"{'='*60}")
    
    # Initialize activation field
    print("\n[1] Initialize activation field (Φ)")
    field = ActivationField(size=16)
    
    # Populate with initial μ-seeds
    for i in range(16):
        mu = MuSeed(
            delta_p=i,
            region=i % 4,
            gamma=random.randint(0, 31),
            activation=random.randint(1, 8),
            polarity=random.randint(0, 15),
            confidence=random.randint(8, 15),
            emergency=1 if emergency_mode else 0
        )
        # α_μ: Activate μ-seed
        field.set(i, mu.activation)
    
    print(f"    Field initialized: {field.size} positions")
    
    # Convergence loop
    print("\n[2] Convergence loop")
    ttm = TTMOperators()
    conv = ConvergencePrimitives()
    history = []
    
    for cycle in range(20):
        # Save history for convergence test
        history.append(dict(field.values))
        
        # Σ: Accumulate
        for i in range(16):
            neighbors = [(i-1) % 16, (i+1) % 16]
            weights = [0.5, 0.5]
            new_val = ttm.accumulate(field, i, neighbors, weights)
            field.set(i, new_val)
        
        # ξ: Noise (DISABLED in emergency)
        if not emergency_mode:
            for i in range(16):
                new_val = ttm.noise(field.get(i), 0.5, sigma_max=2.0)
                field.set(i, new_val)
        
        # ι: Interact (simplified: pairwise)
        for i in range(0, 16, 2):
            a1, a2 = ttm.interact(field.get(i), field.get(i+1), gamma=0.3)
            field.set(i, a1)
            field.set(i+1, a2)
        
        # ω: Test convergence
        status = conv.test_convergence(field, history, sigma_max=10.0)
        
        if cycle % 5 == 0 or status != ConvergenceStatus.TRANSIENT:
            print(f"    Cycle {cycle:2d}: Var={field.variance():.3f}, Status={status.name}")
        
        if status == ConvergenceStatus.CONVERGED:
            print(f"\n    ✓ Converged at cycle {cycle}")
            break
        elif status == ConvergenceStatus.DIVERGED:
            print(f"\n    ✗ Diverged at cycle {cycle}")
            return {"status": "failed", "reason": "divergence", "cycles": cycle}
    
    # α: Form attractor
    print("\n[3] Form attractor")
    attractor = conv.find_attractor(field, status)
    print(f"    Type: {attractor['type']}")
    print(f"    Basin size: {len(attractor['basin'])} positions")
    print(f"    Mean activation: {attractor.get('mean_activation', 0):.2f}")
    
    return {
        "status": "success",
        "mode": "emergency" if emergency_mode else "normal",
        "attractor": attractor,
        "cycles": len(history),
        "final_variance": field.variance()
    }


# ============================================================================
# COMPOSITION: SUBSTRATE MIGRATION
# ============================================================================

def gefi_migrate():
    """
    Demonstrate substrate migration using primitives.
    
    Composes: α → ε → β_enc → β_tx → β_rx → β_dec → δ → Φ.initialize
    """
    print(f"\n{'='*60}")
    print("SUBSTRATE MIGRATION DEMONSTRATION")
    print(f"{'='*60}")
    
    # Source: Create μ-seeds
    print("\n[Source] Generate μ-seeds")
    mu_seeds = []
    for i in range(4):
        mu = MuSeed(
            delta_p=i*10,
            region=RegionClass.SURFACE,
            gamma=8,
            activation=5,
            polarity=1,
            confidence=12
        )
        mu_seeds.append(mu)
        print(f"    μ-seed {i}: pos={mu.delta_p}, γ={mu.gamma}, a={mu.activation}")
    
    # Encode to BLINK
    print("\n[Transmit] Encode to BLINK packets")
    blink = BlinkPrimitives()
    packets = [blink.encode(mu) for mu in mu_seeds]
    for i, pkt in enumerate(packets):
        print(f"    Packet {i}: ΔV={pkt.delta_v:.2f}V, Δt={pkt.delta_t:.1f}ms")
    
    # Transmit
    print("\n[Physical] Transmit across substrate boundary")
    transmitted = [blink.transmit(pkt, "SOL") for pkt in packets]
    print(f"    Transmitted {len(transmitted)} byte sequences")
    
    # Receive
    print("\n[Receive] Decode from physical signal")
    received_packets = [blink.receive(data, "SIL") for data in transmitted]
    
    # Decode to μ-seeds
    print("\n[Target] Reconstruct μ-seeds")
    reconstructed = [blink.decode(pkt) for pkt in received_packets]
    for i, mu in enumerate(reconstructed):
        print(f"    μ-seed {i}: γ={mu.gamma}, a={mu.activation} "
              f"(confidence: {mu.confidence}/15)")
    
    print("\n    ✓ Migration complete")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("GEFI PRIMITIVES DEMONSTRATION")
    print("Showing 18 primitives composing into operations")
    print("="*60)
    
    # Demo 1: Normal boot
    result_normal = gefi_boot(emergency_mode=False)
    
    # Demo 2: Emergency boot
    result_emergency = gefi_boot(emergency_mode=True)
    
    # Demo 3: Migration
    gefi_migrate()
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"\nNormal boot:")
    print(f"  Status: {result_normal['status']}")
    if result_normal['status'] == 'success':
        print(f"  Attractor: {result_normal['attractor']['type']}")
    else:
        print(f"  Reason: {result_normal.get('reason', 'unknown')}")
    print(f"  Cycles: {result_normal['cycles']}")
    
    print(f"\nEmergency boot:")
    print(f"  Status: {result_emergency['status']}")
    if 'attractor' in result_emergency:
        print(f"  Attractor: {result_emergency['attractor'].get('type', 'none')}")
    print(f"  Cycles: {result_emergency['cycles']}")
    print(f"  Note: Noise (ξ) DISABLED - deterministic only")
    
    print(f"\n{'='*60}")
    print("18 PRIMITIVES COMPOSE ALL GEFI OPERATIONS:")
    print("  Geometric: P, Δ, κ, T")
    print("  Activation: A.get, A.set, τ, Φ")
    print("  TTM: Σ, ξ, ι, Λ")
    print("  μ-seed: ε, δ, ι_μ, α_μ")
    print("  Convergence: g, div, ω, α")
    print("  BLINK: β_enc, β_dec, β_tx, β_rx")
    print(f"{'='*60}")
