# Chromatic Braid Field (CBF) Hardware Specification

**Version:** 1.0-CBF  
**Status:** Design phase — FPGA Warden Node rewrite  
**Date:** 2026-04-17

---

## 1. Overview

The Chromatic Braid Field (CBF) core unifies:
- DIAT local tuple encoding
- Corrected AMMR vector accumulation
- Bracket-based admissibility calculus
- AVMR hierarchical strand aggregation
- CMYK channel decomposition

**Formal identity:**
```
CBF = DIAT ∘ AMMR ∘ Bracket ∘ AVMR ∘ CMYK ∘ Rope/MIMO
```

---

## 2. Processing Pipeline

```
Input bytes / local samples
    ↓
[Segmenter / Leaf Builder]
    ↓
build DIATLeaf(a, b, ab, a-b, residue, slot, parity, jitter)
    ↓
[DIAT Lift]
    ↓
Φ(DIATLeaf) → PhaseVec(x, y)
    ↓
[φ-Accumulator + Prime Counter + Void Mask LUT]
    ↓
deterministic address / resonance basis
proximity / modulation contribution
carrier-local weighting
    ↓
[AMMR Vector Accumulator]
    ↓
Σ PhaseVec over active leaves / modes / strands
    ↓
[Bracket Step]
    ↓
κ = ||z_φ||
φ = atan2(z_y, z_x)
lower / upper / gap
admissible?
    ↓
[CMYK Colorizer]
    ↓
C = coherence
M = modulation
Y = yield
K = constraint
    ↓
[Braid Cross / AVMR Merge]
    ↓
merge phaseAcc linearly
merge metadata
recompute bracket
recompute color
    ↓
[Colored Rope Binder]
    ↓
bundle all strands for this cycle
    ↓
[Carrier Encoder / MIMO Projection]
    ↓
audio projection
video projection
caption projection
timing projection
    ↓
[Processor / Channel / Detangler]
    ↓
recover strands for next cycle
```

---

## 3. Core Principles

### 3.1 Linear Accumulation Discipline

All strand and carrier composition occurs by **linear accumulation in vector space**. Only after accumulation is complete does the core perform:
1. Single nonlinear projection to derive magnitude and phase
2. Bracket-shell construction
3. Chromatic channel assignment

**Result:** Nonlinear work moved out of the inner loop; associativity, commutativity, and parallel recombination preserved.

### 3.2 Q16.16 Fixed-Point Arithmetic

All arithmetic uses Q16.16 fixed-point:
- `κ` approximation: octagonal norm
- `atan2`: quadrant-aware polynomial approximation
- Zero-vector handling: `ϕ = 0` when `(x, y) = (0, 0)`

---

## 4. Module Specifications

### 4.1 DIAT Leaf Builder

**Input:** Raw bytes / samples  
**Output:** `DIATLeaf` structure

| Field | Type | Description |
|-------|------|-------------|
| `a` | Q16.16 | Primary value |
| `b` | Q16.16 | Secondary value |
| `ab` | Q16.16 | Product a·b |
| `diff` | Q16.16 | Difference a-b |
| `residue` | Q16.16 | Local residue |
| `slot` | UInt32 | Timing slot |
| `parity` | Bool | Strand parity |
| `jitterTolerance` | Q16.16 | Jitter bound |

**Lift function:**
```
Φ(DIATLeaf) → PhaseVec:
    x = a - b
    y = ab + residue
```

### 4.2 AMMR Vector Accumulator

**Input:** `PhaseVec` contributions  
**Output:** Accumulated `PhaseVec`

```
z_φ = Σ Φᵢ
```

**Properties:**
- Associative
- Commutative
- Parallelizable
- No nonlinear operations in-loop

### 4.3 Bracket Step

**Input:** Accumulated `PhaseVec`  
**Output:** `BraidBracket`

```
κ = ||z_φ||          (octagonal approximation)
ϕ = atan2(z_y, z_x)  (safe, total function)

lower = -κ
upper = κ
gap = upper - lower
admissible = gap ≤ threshold
```

### 4.4 CMYK Colorizer

**Input:** `BraidBracket` + `AVMRMeta`  
**Output:** `CMYKWeights`

| Channel | Mapping | Semantics |
|---------|---------|-----------|
| C | `bracket.kappa` | Coherence |
| M | `meta.totalInteraction` | Modulation |
| Y | `half if admissible else quarter` | Yield |
| K | `quarter if admissible else one` | Constraint |

### 4.5 Braid Cross / AVMR Merge

**Input:** Two `BraidStrand` objects  
**Output:** Merged `BraidStrand`

**Merge rules:**
```
phaseAcc = l.phaseAcc + r.phaseAcc      (linear)
meta = metaMerge(l.meta, r.meta)         (hierarchical)
bracket = bracketStep(phaseAcc)       (recomputed)
color = colorize(bracket, meta)         (recomputed)
```

**Crossing residual:**
```
Rᵢⱼ = Bᵢⱼ - (Bᵢ + Bⱼ)
```

### 4.6 Colored Rope Binder

**Input:** Array of `BraidStrand`  
**Output:** `ColoredRope`

Bundles all strands for the current cycle into a multiplexed rope object.

### 4.7 MIMO Carrier Encoder

**Input:** `ColoredRope`  
**Output:** Carrier projections

| Carrier | Projection | Channel |
|---------|------------|---------|
| Audio | `rope.audio()` | Φ⁽ᵃ⁾ |
| Video | `rope.video()` | Φ⁽ᵛ⁾ |
| Caption | `rope.caption()` | Φ⁽ᶜ⁾ |
| Timing | `rope.timing()` | Φ⁽ᵗ⁾ |

---

## 5. Target Hardware

### 5.1 Primary Target: Lattice iCE40 HX8K

| Resource | Required | Budget | Utilisation |
|----------|----------|--------|-------------|
| LUT cells (logic) | ~300 | 7,680 | 3.9% |
| LUTRAM (void mask) | 512 bits | 8KB | 6.3% |
| Flip-flops | ~150 | 7,680 | 2.0% |
| Block RAM | 0 | 128KB | 0% |
| DSP slices | 0 | 8 | 0% |

### 5.2 Performance

- **Clock:** 50 MHz (20ns/cycle)
- **Accumulation latency:** N_MODES × 1 cycle
- **Final projection:** 4 cycles (pipelined)
- **Total per attestation:** ~20 cycles = **400ns**
- **Throughput:** **2.5M attestations/second**

---

## 6. Files

| File | Role |
|------|------|
| `Semantics/CBFCore.lean` | Formal core (DIAT, AMMR, Bracket, AVMR, CMYK) |
| `hardware/cbf_warden.v` | Verilog: CBF Warden implementation |
| `hardware/diat_builder.v` | DIAT leaf construction |
| `hardware/ammr_accum.v` | PhaseVec accumulator |
| `hardware/bracket_step.v` | Bracket calculus unit |
| `hardware/cmyk_colorizer.v` | CMYK channel assignment |
| `hardware/braid_cross.v` | Strand merge / crossing |
| `hardware/rope_binder.v` | Colored rope assembly |
| `hardware/mimo_encoder.v` | Carrier projection |
| `hardware/q16_norm.v` | Octagonal norm approximation |
| `hardware/q16_atan2.v` | Safe atan2 implementation |

---

## 7. One-Line Summary

> CBF reduces processing by moving nonlinear work out of the inner loop, preserving associativity through linear AMMR accumulation, and applying bracket calculus only after complete strand state is known.

---

**Attestation Hash:** SHA256(CBF ∘ AMMR ∘ Bracket ∘ CMYK)  
**Registry Entry:** `pkg/cbf-hardware/v1.0`  
**Tier:** CRYSTALLINE
