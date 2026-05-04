# Paper Stub: LUT-as-DSP Hardware Collapse

**Equation ID:** LUT-DSP-003  
**Status:** Hardware specification (Verilog + Lean formalization)  
**Lineage:** Hardware extraction from ENE cost functions  
**Date:** 2026-04-19  
**Ancestry:** FPGA Warden Node — the first equation designed for silicon

---

## The Equation

```
φ_corr = LUT_void[(Φ_acc ≫ n) ⊕ MSB_flip]

where:
  Φ_acc^(t+1) = (Φ_acc^(t) + ⌊φ · 2^16⌋) mod 2^32
  
  c_mod7^(t+1) = { 0            if c_mod7^(t) = 6
                 { c_mod7^(t) + 1 otherwise
  
  idx_mirror = (Φ_acc ≫ n) ⊕ (MSB(Φ_acc^(t)) ≠ MSB(Φ_acc^(t-1)))
```

## Mutation History

| Variant | Domain | Key Difference |
|---------|--------|----------------|
| LUT-DSP-003 | Hardware | φ-accumulator + mod-7 counter |
| LUT-SW-003a | Software | φ^entropy · 2^64 polynomial seed |
| LUT-SIM-003b | Simulation | SHA256(engram_key ‖ position) ≫ 4 |
| UNIVERSAL-003c | Cross-domain | Hybrid hash + XOR fold (see MIRROR_LUT_EQUATIONS.md) |

## Half-Thought: The Void Mask

> "LUT_void[i] = void-and-cluster(i) ∈ {0,1}^2^13"

The void mask is described as "baked at synthesis time — no runtime PRNG, no seed, no non-determinism." But the generation algorithm (`void-and-cluster`) is never specified in the codebase. This is intentional opacity:

- The mask generation is a **manufacturing secret**
- Different Warden nodes may have different void masks
- The security property relies on mask diversity, not mask algorithm

## Hardware-to-Lean Correspondence

| Hardware | Lean Formalization | File |
|----------|-------------------|------|
| φ-accumulator | `DynamicCanal.phiAccumulator` | `DynamicCanal.lean` |
| mod-7 counter | `BraidBracket.mod7Counter` | `BraidBracket.lean` |
| Void mask LUT | `SLUG3.landauerCostBits` (placeholder) | `SLUG3.lean` |
| XOR fold | `UnitQuaternion.conjugate` (partial) | `QuaternionGenomic.lean` |

## The Resource Collapse

The equation achieves **zero DSP blocks** by replacing all arithmetic with LUT lookups:

| Operation | Traditional | LUT-as-DSP |
|-----------|-------------|------------|
| φ^(i mod 7) | `pow(PHI, i % 7)` floating-point | `phi_acc + 106070` |
| Multiplication | `*` operator | LUT lookup |
| Entropy | `os.urandom()` / PRNG | Void mask (baked) |

## Ancestral Connection

```
ENE-BIND-001 (cost: UInt32 Q16.16)
    ↓ hardware extraction
LUT-DSP-003 (cost: LUT lookup cycles)
    ↓ cross-domain unification
UNIVERSAL-003c (hybrid hash function)
    ↓ DNA encoding
QUATERNION-SLUG-005 (ternary gate)
```

The LUT-DSP-003 equation is the **hardware anchor** — it proves the cost function can be evaluated without floating-point, making all upstream equations hardware-extractable.

## Open Hardware Questions

1. What is the actual void-and-cluster algorithm? (Trade secret vs. open specification)
2. Can the 91-step period (13×7) be extended for higher security?
3. Dual-port A/B swap: race-free by construction, but what about power-glide attacks?

---

*Part of the Equation Ancestry Project*
