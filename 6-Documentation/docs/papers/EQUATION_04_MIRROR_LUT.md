# Paper Stub: The Mirror LUT — Cross-Domain Unification

**Equation ID:** MIRROR-LUT-004  
**Status:** Theoretical framework (3 domains unified)  
**Lineage:** Abstraction layer above LUT-DSP-003  
**Date:** 2026-04-19  
**Ancestry:** Discovers isomorphism between hardware, software, and simulation domains

---

## The Equation

```
𝒰(q, s, t) = ℋ(ℱ(q) ⊕ 𝒯(t)) mod 2^n

where:
  q = Query (position/address/state)
  s = State (entropy/accumulator)
  t = Time (counter/step)
  ℋ = Hash function (deterministic mixing)
  ℱ = Fold operation (mirror/quadrant)
  𝒯 = Transform (phase shift)
```

## Domain Instantiations

| Domain | Query | State | Time | Hash | Fold | Transform |
|--------|-------|-------|------|------|------|-----------|
| **Hardware** | Φ_acc ≫ 16 | Φ_acc mod 2^32 | c_mod7 ∈ {0..6} | LUT_void | MSB_flip | φ·t mod 2^16 |
| **Software** | basin(x) ∈ {0..8} | entropy(x) ∈ [0,8] | spectral_density(x) | φ^pow | frac part | log₂(t+1) |
| **Simulation** | position ∈ ℤ³ | engram_key ∈ 2^32 | simulation tick | SHA256 | XOR coords | linear stride |

## Mutation: The Universal Form

```
𝒰*(q, s, t) = ⌊φ^(α·ℋ(q,s) + β·𝒯(t)) · 2^n⌋ ⊕ ℱ(q) mod 2^n

Optimal parameters:
  α = 0.7 (hybrid weight)
  β = 0.15 (temporal weight)
  n = 16 (hardware-native)
```

## Half-Thought: The Hybrid Hash

> "ℋ*(q,s) = fold_64(SHA256(s ‖ q) ⊕ LUT_φ[q mod 8192])"

This "hybrid hash" concept is documented but never implemented:
- Combines cryptographic collision resistance with φ-uniformity
- Requires 8K-entry LUT_φ (precomputed, but content undefined)
- The fold_64 operation is described but no specification given

**The gap:** The universal form depends on LUT_φ, but the generation of this table is unspecified. It's the software analog of the void mask hardware secret.

## Ancestral Tree

```
LUT-DSP-003 (hardware-specific)
    ↓ abstraction
MIRROR-LUT-004 (cross-domain)
    ├─→ Hardware (MSB flip, 91-step)
    ├─→ Software (φ^entropy, input-dependent)
    └─→ Simulation (SHA256, 2^256 period)
    ↓ universal synthesis
UNIVERSAL-003c (hybrid parameters)
    ↓ DNA encoding bridge
QUATERNION-SLUG-005 (ternary via quaternion)
```

## The Period Convergence Problem

Each domain has different natural period:

| Domain | Period | Source |
|--------|--------|--------|
| Hardware | 91 = 13×7 | Coprime traversal |
| Software | Input-dependent | Deterministic per input |
| Simulation | 2^256 | Cryptographic |
| **Universal** | **65521 (prime)** | Proposed compromise |

The universal form suggests period 65521 (a Mersenne-like prime), but there's no derivation for why this specific number.

## Unfinished: Cross-Domain Verification

Can a computation verified in one domain be trusted in another?

- Hardware → Software: Timing attacks on φ-accumulator
- Software → Simulation: Floating-point vs fixed-point divergence
- Simulation → Hardware: Cryptographic security vs physical probing

The isomorphism is structural, not operational.

---

*Part of the Equation Ancestry Project*
