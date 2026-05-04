# PBACS: Policy-Based Adaptive Constraint System
## Canonical Signal Transport Architecture (NOT Compression)

**Version**: 2026-04-16  
**Status**: Specification Complete, Implementation In Progress  
**Core Reframe**: This is NOT compression. This is deterministic signal transport + constraint-based reconstruction.

---

## The Canonical 5-Layer Stack

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: RECONSTRUCTION  [BracketedDIAT]                   │
│  Constraint-preserving interval arithmetic                  │
│  ├─ Gap conservation: g_l + g_u = u - l                   │
│  ├─ Conservative operations: min/max bounds                │
│  └─ Truth-preserving: value always ∈ [l, u]               │
├─────────────────────────────────────────────────────────────┤
│  LAYER 4: VALIDATION  [PBACS Core / CMYK-SLUQ]              │
│  Adaptive stress routing with policy-based state machine    │
│  ├─ K (Black/00): Fast path → no extra checks             │
│  ├─ C (Cyan/01): Monitor → widen observation window       │
│  ├─ M (Magenta/10): Verify → secondary attestation        │
│  └─ Y (Yellow/11): Prune/Reset → swap shadow table        │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: CORRECTION  [Void Mask LUT]                       │
│  Blue-noise structured thresholding replaces arithmetic       │
│  ├─ LUT_void: 8Kbit pre-baked blue noise mask             │
│  ├─ θ_t = LUT[(Φ_t >> n) ⊕ MSB_flip]                      │
│  └─ Popcount validation: AND(LUT, deviation)              │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: SCHEDULING  [φ-Traversal Engine]                  │
│  Deterministic coprime traversal (no PRNG)                  │
│  ├─ Φ_{t+1} = Φ_t + 106070 (mod 2^32)                     │
│  ├─ 91-step full coverage (13 × 7 coprime)                │
│  └─ MSB mirror: quadrant fold on bit flip                   │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: TRANSPORT  [1-Bit Noise-Shaped Encoder]         │
│  Structure-preserving encoding over time                    │
│  ├─ b_t = 1[v_t + e_{t-1} > θ_t]                          │
│  ├─ e_t = v_t + e_{t-1} - b_t  (error never discarded)    │
│  └─ Information in: time + structure + constraints          │
└─────────────────────────────────────────────────────────────┘
```

---

## PBACS Core Equations

### The Unified State Vector

$$
\boxed{
X_t = (\Phi_t, e_t, a_t, s_t, b_t, \mathcal{B}_t)
}
$$

Where:
- $\Phi_t$: φ-accumulator (scheduling state)
- $e_t$: Error accumulator (transport state)  
- $a_t$: SLUQ stress accumulator (validation state)
- $s_t$: CMYK policy state (2-bit routing)
- $b_t$: 1-bit output symbol
- $\mathcal{B}_t$: BracketedDIAT constraint structure

### The 8-Step Canonical Update

$$
\begin{align}
\text{Step 1: } & \Phi_{t+1} = \Phi_t + \Delta_\phi \pmod{2^{32}} \\
\text{Step 2: } & \theta_t = \text{LUT}_{\text{void}}\big[(\Phi_t \gg n) \oplus \text{MSB}_{\text{flip}}\big] \\
\text{Step 3: } & b_t = \mathbb{1}[v_t + e_{t-1} > \theta_t] \\
\text{Step 4: } & e_t = v_t + e_{t-1} - b_t \\
\text{Step 5: } & \text{stress}_t = \alpha|e_t| + \beta|\hat{\mu}_t - \mu^*_t| + \gamma \cdot \text{popcount}(\text{LUT}_{\text{void}}[i] \land \text{deviation}) \\
\text{Step 6: } & a_{t+1} = a_t - (a_t \gg 6) + \text{stress}_t \\
\text{Step 7: } & s_t = a_t \gg 14 \in \{00, 01, 10, 11\} \\
\text{Step 8: } & \mathcal{B}_{t+1} = \text{BracketOp}(\mathcal{B}_t, b_t, \pi(s_t))
\end{align}
$$

---

## Layer Specifications

### Layer 1: TRANSPORT — 1-Bit Noise-Shaped Encoder

**Purpose**: Move signal through time with minimal precision

**Core Equation**:
$$
\boxed{
b_t = \begin{cases} 1 & \text{if } v_t + e_{t-1} > \theta_t \\ 0 & \text{otherwise} \end{cases}, \quad e_t = v_t + e_{t-1} - b_t
}
$$

**Key Properties**:
- Error **never discarded** — feeds forward
- Precision → moved into **time domain**
- Single comparator, one register

**Hardware Cost**: 1 LUT (comparator) + 16 FF (error reg)

---

### Layer 2: SCHEDULING — φ-Traversal Engine

**Purpose**: Deterministic uniform coverage without PRNG

**Core Equation**:
$$
\boxed{
\Phi_{t+1} = \Phi_t + \lfloor \phi \cdot 2^{16} \rfloor \pmod{2^{32}} = \Phi_t + 106070 \pmod{4294967296}
}
$$

**Coverage Guarantee**:
$$
\text{Period} = \frac{13 \times 7}{\gcd(13,7)} = 91 \text{ steps (full traversal)}
$$

**Key Properties**:
- Most irrational step (φ) = lowest discrepancy
- No multiplication at runtime (iterative add)
- Coprime ensures no harmonic aliasing

**Hardware Cost**: 32 FF + adder

---

### Layer 3: CORRECTION — Void Mask LUT

**Purpose**: Structured thresholding replaces arithmetic transforms

**Core Equation**:
$$
\boxed{
\theta_t = \text{LUT}_{\text{void}}\big[(\Phi_t \gg n) \oplus \underbrace{(\text{MSB}(\Phi_t) \neq \text{MSB}(\Phi_{t-1}))}_{\text{mirror fold}}\big]
}
$$

**Attestation Validation**:
$$
\text{attest}_t = \text{popcount}(\text{LUT}_{\text{void}}[i_t] \land \text{Deviation}_{\text{seg}})
$$

**Key Properties**:
- Blue noise mask baked at synthesis
- Self-attesting via JTAG readback
- F2b immunity by construction (not calibration)

**Hardware Cost**: 8Kbit LUTRAM

---

### Layer 4: VALIDATION — PBACS / CMYK-SLUQ

**Purpose**: Adaptive routing based on stream stability

**Stress Accumulator**:
$$
\boxed{
\text{stress}_t = \alpha|e_t| + \beta|\hat{\mu}_t - \mu^*_t| + \gamma \cdot \text{attest}_t
}
$$

**SLUQ Update**:
$$
\boxed{
a_{t+1} = a_t - (a_t \gg 6) + \text{stress}_t
}
$$

**Policy State Decode**:
$$
\boxed{
s_t = a_t \gg 14 \mapsto \begin{cases} 00 & \rightarrow \text{K (Fast)} \\ 01 & \rightarrow \text{C (Monitor)} \\ 10 & \rightarrow \text{M (Verify)} \\ 11 & \rightarrow \text{Y (Prune)} \end{cases}
}
$$

**Policy Actions**:

| State | Binary | Stress Range | Action | Effort |
|-------|--------|--------------|--------|--------|
| **K** | 00 | [0, 16384) | Fast path, no extra checks | Low |
| **C** | 01 | [16384, 32768) | Widen observation window | Medium |
| **M** | 10 | [32768, 49152) | Secondary attestation check | High |
| **Y** | 11 | [49152, 65536) | Prune branch, swap shadow table | Terminal |

**Hardware Cost**: 16 FF (accumulator) + 2 LUT (decode)

---

### Layer 5: RECONSTRUCTION — BracketedDIAT

**Purpose**: Constraint-preserving interval arithmetic

**Structure**:
$$
\boxed{
\mathcal{B} = \langle l, u, v, g_l, g_u, s, p, d \rangle
}
$$

**Invariant**:
$$
\boxed{
g_l + g_u = u - l \quad \text{(Gap Conservation Law)}
}
$$

**Conservative Multiplication**:
$$
\boxed{
\mathcal{B}_1 \otimes \mathcal{B}_2 = \langle \min(v_i v_j), \max(v_i v_j), v_1 v_2, s_{\max} \rangle
}
$$

**Policy-Driven Update**:
$$
\mathcal{B}_{t+1} = \begin{cases}
\text{bracketAdd}(\mathcal{B}_t, b_t) & s_t = K \\
\text{bracketWiden}(\mathcal{B}_t) & s_t = C \\
\text{bracketVerify}(\mathcal{B}_t, \text{attest}_t) & s_t = M \\
\text{bracketReset}() & s_t = Y
\end{cases}
$$

**Hardware Cost**: 6 × 16 FF (Fix16 fields) + comparison logic

---

## The "Not Compression" Manifesto

| Traditional Compression | PBACS Canonical Signal Transport |
|-------------------------|----------------------------------|
| Minimize entropy | **Preserve structure under quantization** |
| Store fewer bits | **Represent value as trajectory** |
| Information in bits | **Information in time + structure + constraints** |
| Perfect reconstruction | **Constraint-based recovery** |
| Global optimization | **Local constraint satisfaction** |
| Floating-point elegance | **Add/shift/LUT/compare only** |

---

## Implementation Status

| Component | Spec | Lean | Verilog | Testbench |
|-----------|------|------|---------|-----------|
| 1-bit encoder | ✅ | ❌ | ❌ | ❌ |
| φ-accumulator | ✅ | ❌ | ❌ | ❌ |
| Void mask LUT | ✅ | ❌ | ❌ | ❌ |
| CMYK-SLUQ | ✅ | ❌ | ❌ | ❌ |
| BracketedDIAT | ✅ | ✅ | ❌ | ⚠️ |
| LocalDerivative | ✅ | ✅ | ❌ | ⚠️ |
| **Full 8-step loop** | ✅ | ❌ | ❌ | ❌ |

**Critical Path**: Void mask generator → 1-bit encoder Verilog → SLUQ→Bracket wiring

---

## Single-Sentence Definition

> **PBACS** is a Policy-Based Adaptive Constraint System that uses deterministic φ-traversal, blue-noise LUT thresholding, and 2-bit stress routing to transport signals through 1-bit time-domain encoding while preserving truth via bracketed interval constraints.

---

## Resource Budget (Lattice iCE40 HX8K)

| Layer | LUTs | FFs | BRAM | Notes |
|-------|------|-----|------|-------|
| Transport | 1 | 16 | 0 | 1-bit encoder |
| Scheduling | 2 | 32 | 0 | φ-accumulator |
| Correction | 4 | 0 | 8K | Void mask LUT |
| Validation | 2 | 16 | 0 | SLUQ + CMYK decode |
| Reconstruction | 10 | 96 | 0 | BracketedDIAT |
| **TOTAL** | **~200** | **~160** | **8K** | **Zero DSP blocks** |

---

## Canonical Test Suite

### Test 1: Stability Loop
```
Input: constant v_t
Verify: |e_t| < ε, s_t ∈ {K, C}
```

### Test 2: Stress Response
```
Input: threshold distortion
Verify: M triggers, recovery completes, no runaway
```

### Test 3: Gap Conservation
```
Input: bracket operations sequence
Verify: ∀t: g_l(t) + g_u(t) = u(t) - l(t)
```

### Test 4: Adversarial Resilience
```
Input: corrupted LUT region
Verify: Y triggers early, system self-prunes
```

---

**Document ID**: PBACS_CANONICAL_ARCHITECTURE  
**Cross-ref**: LUT_AS_DSP_EQUATION.md, FPGA_WARDEN_NODE_SPEC.md, ADAPTIVE_1BIT_CMYK_MERGED.md, BracketedCalculus.lean
