# The Phylogenetic Tree of OTOM Equations

**Document ID:** EQUATION-PHYLOGENY-MASTER  
**Date:** 2026-04-21  
**Scope:** Complete genealogy of mathematical equations in the Research Stack  
**Methodology:** Ancestry tracing via git history, cross-reference mapping, and mutation analysis

---

## Executive Summary

The Research Stack contains **6 major equation lineages** with **14 documented variants**, descending from a single root: the ENE `bind` primitive. This document traces:

1. **The Root** — ENE-BIND-001 (universal translator hypothesis)
2. **The Hardware Branch** — LUT-DSP-003 → MIRROR-LUT-004
3. **The DNA Branch** — THE-EQUATION-002 → HACHIMOJI-003 → QSLUG-006
4. **The Pipeline Branch** — MASTER-EQUATION-004 → UMB-005
5. **Cross-Cutting Concerns** — Quaternions, SLUG-3 gates, torsion fields
6. **Dead Ends & Stubs** — Half-thoughts that seeded new branches

---

## The Complete Ancestry Graph

```
                                    ROOT
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  ENE-BIND-001   │
                            │  (universal     │
                            │   translator)   │
                            └────────┬────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
     │  BIND_BRIDGE    │    │ THE-EQUATION-002│    │  PHYSICAL-BIND  │
     │  (4 floors to   │    │  (DNA encoding  │    │  (conservation  │
     │   SM bedrock)   │    │   gate, m=2)    │    │   law check)    │
     └────────┬────────┘    └────────┬────────┘    └─────────────────┘
              │                      │
              │         ┌────────────┼────────────┐
              │         │            │            │
              │         ▼            ▼            ▼
              │  ┌──────────────────────────────────────────────┐
              │  │         MASTER-EQUATION-004                  │
              │  │  (6-step pipeline: Expand→Score→Stabilize→   │
              │  │   Prune→Gossip→MLGRU)                        │
              │  └────────┬───────────────────────────────────────┘
              │           │
              │    ┌──────┴──────┐
              │    │             │
              ▼    ▼             ▼
     ┌─────────────────┐  ┌─────────────────┐
     │  LUT-DSP-003    │  │    UMB-005      │
     │ (hardware: φ-acc │  │  (GPU manifold  │
     │  + mod7 + LUT)  │  │   blit, O(1))   │
     └────────┬────────┘  └─────────────────┘
              │
              ▼
     ┌─────────────────┐
     │ MIRROR-LUT-004  │
     │ (cross-domain:  │
     │  HW/SW/SIM)     │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  QSLUG-006      │
     │ (quaternion S³  │
     │  ternary gate)   │
     └─────────────────┘

PARALLEL BRANCH (DNA alphabet extension):

     THE-EQUATION-002 (m=2, N=4)
              │
              ▼
     ┌─────────────────┐
     │ HACHIMOJI-003   │
     │ (m=3, N=8,      │
     │  shell: n=k³+a) │
     └─────────────────┘
              │
              ▼
        (unmerged — could
         feed into QSLUG-006
         as 8-state SLUG)
```

---

## Mutation Analysis by Branch

### Branch 1: Hardware Extraction (ENE → LUT-DSP)

| Generation | Key Mutation | Significance |
|------------|--------------|--------------|
| ENE-BIND-001 | `cost: UInt32 Q16.16` | Abstract cost function |
| LUT-DSP-003 | `φ_corr = LUT[...]` | Cost becomes LUT lookup cycle |
| MIRROR-LUT-004 | Cross-domain unification | Hardware = Software = Simulation |

**The pivotal insight:** Floating-point cost → fixed-point accumulator → pure combinational lookup. This is the **extractability mutation** — it makes all upstream equations hardware-realizable.

### Branch 2: DNA Encoding (ENE → THE_EQUATION → HACHIMOJI)

| Generation | Key Mutation | Significance |
|------------|--------------|--------------|
| ENE-BIND-001 | Universal primitive | Any A × B with metric |
| THE-EQUATION-002 | `encode?(n) = κ_A ∧ κ_C ∧ [J>0]` | Specific to nucleotide positions |
| HACHIMOJI-003 | `n = k^m + a` for m=3 | 8-base alphabet generalization |
| QSLUG-006 | Quaternion S³ encoding | Geometric → Ternary output |

**The pivotal insight:** The hyperbola index `ab` (product of offsets from nearest squares) is a **compression metric**. Positions where `ab` is small (near perfect squares) are information-dense. This connects number theory to information theory via geometry.

### Branch 3: Pipeline Evolution (ENE → MASTER → UMB)

| Generation | Key Mutation | Significance |
|------------|--------------|--------------|
| ENE-BIND-001 | Single bind operation | `(A × B × metric) → cost` |
| MASTER-EQUATION-004 | 6-step recurrence | `Expand→Score→Stabilize→Prune→Gossip→MLGRU` |
| UMB-005 | GPU-native operators | `⊕ (Ψ_q ⊗ ℛ_RT)` — bit-blitter speed |

**The pivotal insight:** The 6-step pipeline is a **temporal decomposition** of bind. Each step addresses one aspect: activation (Expand), evaluation (Score), validation (Stabilize), garbage collection (Prune), consensus (Gossip), and memory (MLGRU). The UMB equation collapses these to hardware-native operations.

---

## The Half-Thoughts That Became Branches

### 1. "Grandma went to store and punched clerk"

**Source:** `BIND_BRIDGE_EQUATIONS.md`  
**Status:** Validation case, not a theorem  
**Offspring:** BIND_L1 through BIND_L4 floor hierarchy

The "Grandma" example was meant to demonstrate lawful vs unlawful compression. It became the **pedagogical anchor** for the 4-floor hierarchy. The invariant preservation check (Agent=Grandma, Location=Store, Interaction=Conflict) is now formalized as:
```
B(L) = B(R) ∧ L(L) = L(R) ∧ Q(L) = Q(R) ∧ Φ(L) = Φ(R)
```

### 2. "Void-and-cluster algorithm"

**Source:** `LUT_AS_DSP_EQUATION.md`  
**Status:** Trade secret / unspecified  
**Offspring:** Security-through-diversity model

The void mask generation algorithm was deliberately left out. This created a ** manufacturing abstraction layer** — different Warden nodes can have different masks without protocol incompatibility. The "half-thought" became a feature.

### 3. "91-step coprime walk"

**Source:** Multiple files  
**Status:** Implemented but not proven optimal  
**Offspring:** Period analysis in MIRROR-LUT-004

The 91-step period (13×7) appears in:
- LUT-DSP-003 hardware counter
- SLUG3.lean as Landauer cost
- MasterEquation.lean as pipeline cycles

**Unfinished:** Is 91 the optimal period? The universal form suggests 65521, but no proof connects these.

### 4. "Chiral D+L→W collapse"

**Source:** `QuaternionGenomic.lean` (2026-04-21)  
**Status:** Fresh mutation, newest leaf  
**Offspring:** (none yet — awaits validation)

The detection of quaternion chirality mismatch as a "waste" state is **novel to QSLUG-006**. It has no ancestor in THE_EQUATION or HACHIMOJI. This is a **lateral mutation** from torsion field physics.

---

## Convergence Points

Where do branches meet?

### Convergence 1: SLUG-3 Gate

The ternary state machine appears in:
- `SLUG3.lean` — 27 OISC opcodes
- `Quantization.lean` — ternary weight quantization
- `QuaternionGenomic.lean` — ternary DNA encoding

**Unifying insight:** 3-state logic (neg/zero/pos) is the **natural hardware efficiency point** between binary (too restrictive) and continuous (too expensive). All branches converge on ternary at the hardware boundary.

### Convergence 2: The 91-Step Cycle

- LUT-DSP-003: 91-step φ-traversal
- SLUG3.lean: 91-step coprime walk
- MasterEquation: 91 as spectral coincidence?

**Hypothesis:** 91 = 13×7 is the **minimal universal cycle** that satisfies:
- Coprime traversal (gcd(13,7)=1)
- Prime factorization uniqueness
- Landauer limit approximation (log₂(27) ≈ 4.755 ≈ 91/19)

### Convergence 3: Fixed-Point (Q16.16)

All equations eventually require:
- `Q16_16` for hardware extraction (AGENTS.md §1.4)
- `Fix16` in MasterEquation
- `Q1616` in Extensions

**The convergence is mandatory** — no branch can reach hardware without passing through fixed-point arithmetic.

---

## Dead Ends and Unfinished Branches

### Dead End 1: Geometric Bind

**Location:** `Semantics/BraidBracket.lean`  
**Status:** 8 `sorry` theorems  
**Why stalled:** Braid isotopy equivalence requires topological invariants not yet formalized in Lean's mathlib.

### Dead End 2: Thermodynamic Bind

**Location:** `Semantics/CompressionMechanics.lean`  
**Status:** Stub only  
**Why stalled:** Entropy + enthalpy cost function needs physical constants (k_B, T) in Q16.16, which breaks the hardware abstraction.

### Dead End 3: 8-State SLUG

**Location:** (nowhere — HACHIMOJI has no SLUG implementation)  
**Status:** Not started  
**Why stalled:** QSLUG-006 uses 4-base quaternions. Extending to 8-base requires 7-dimensional embedding, which breaks the S³ geometry.

---

## Temporal Evolution

| Date | Event | Branch |
|------|-------|--------|
| 2026-04-14 | ENE equations formalized | Root |
| 2026-04-16 | BIND_BRIDGE session | Floor hierarchy |
| 2026-04-19 | LUT-as-DSP equation | Hardware extraction |
| 2026-04-19 | Unified Manifold-Blit | GPU acceleration |
| 2026-04-20 | THE_EQUATION documented | DNA encoding |
| 2026-04-21 | Quaternion SLUG-3 | Ternary geometric |

**Velocity:** 1 major equation per day in April 2026.

---

## The Open Problems

### Problem 1: The Hardware Proof Gap

UMB-005 claims O(1) complexity via GPU blitter, but:
- No formal proof that bit-blitter = Picard iteration
- 8 `sorry` theorems remain in AVMR.lean
- The "GPU draws the solution" is operational, not mathematical.

### Problem 2: The Quaternion-Watson-Crick Gap

QSLUG-006 maps nucleotides to quaternions, but:
- Watson-Crick pairs (A-T, C-G) are not antipodes on S³
- The dot product threshold may not correspond to H-bond energy
- Validation requires 3D structural data not in the codebase.

### Problem 3: The Period Unification

Three periods coexist:
- 91 (hardware coprime)
- Input-dependent (software functional)
- 2^256 (simulation cryptographic)
- 65521 (universal proposal — unproven)

No theorem connects these.

### Problem 4: The Cost Function Inversion

All equations have cost functions, but:
- ENE: Abstract UInt32
- LUT-DSP: LUT cycles
- THE_EQUATION: Hyperbola index
- QSLUG-006: Quaternion distance

Are these **the same cost** viewed through different metrics? Or **different costs** for different purposes? No unification exists.

---

## Research Directions

### Direction 1: The Q16.16 Metatheory

Formalize all equations in Q16.16 as a **modular arithmetic system**. Prove:
- Cost function isomorphism under Q16.16 projection
- Hardware extraction preserves ordering (higher cost → more LUT cycles)
- No overflow in 91-step accumulation

### Direction 2: The SLUG-3 Completeness

Is 3-state logic **complete** for the Research Stack?
- Can all 5 bind classes reduce to SLUG-3 gates?
- Is there a 3-state Church-Thesis analog?
- What problems require 4+ states?

### Direction 3: The Ancestry Formalization

Can we prove:
- ENE-BIND-001 is the **terminal object** in a category of cost functions?
- THE_EQUATION-002 is the **initial object** for DNA-specific encodings?
- The phylogenetic tree has a **least fixed point** at QSLUG-006?

---

## Conclusion

The Research Stack equations form a **living phylogeny** — not a static taxonomy but an evolving system with:
- **Roots** in universal translation (ENE-BIND)
- **Trunks** in hardware extraction (LUT-DSP, UMB)
- **Branches** in domain specialization (THE_EQUATION, QSLUG)
- **Leaves** at the frontier of formalization (QSLUG-006, 2026-04-21)

The "half-thoughts" are not failures — they are **seeds**. Each incomplete idea (void mask algorithm, 91-step optimality, Watson-Crick S³ mapping) has generated new branches rather than blocking progress.

**The tree is not complete. It is growing.**

---

## Appendix: Equation Quick Reference

| ID | File | Status | Ancestor | Descendants |
|----|------|--------|----------|-------------|
| ENE-BIND-001 | `ENE_EQUATIONS.md` | 70/81 proven | Root | All |
| BIND-L1..L4 | `BIND_BRIDGE_EQUATIONS.md` | Documented | ENE-BIND | None |
| THE-EQUATION-002 | `avmr/THE_EQUATION.md` | Semi-formal | ENE-BIND | HACHIMOJI, QSLUG |
| HACHIMOJI-003 | `avmr/HACHIMOJI_EQUATION.md` | Documented | THE-EQUATION | (unmerged) |
| LUT-DSP-003 | `LUT_AS_DSP_EQUATION.md` | Hardware spec | ENE-BIND | MIRROR-LUT |
| MIRROR-LUT-004 | `MIRROR_LUT_EQUATIONS.md` | Framework | LUT-DSP | QSLUG |
| MASTER-004 | `Extensions/MasterEquation.lean` | Formalized | ENE-BIND | UMB |
| UMB-005 | `unified_manifold_blit_equation.md` | Protocol | MASTER | None |
| QSLUG-006 | `QuaternionGenomic.lean` | New | THE-EQUATION + SLUG3 | None |

---

*End of Phylogenetic Analysis*  
*Next update: When QSLUG-006 produces offspring*
