# Paper Stub: THE EQUATION (DNA Compression Gate)

**Equation ID:** THE-EQUATION-002  
**Status:** Semi-formal (documented, not yet Lean-proven)  
**Lineage:** Descends from ENE-BIND-001 via geometric specialization  
**Date:** 2026-04-20  
**Ancestry:** S3C Framework master equation — 185 model convergence point

---

## The Equation

```
encode?(n) = κ_A(n) ∧ κ_C(n) ∧ [J(n) > 0]

Expanded:
encode?(n) = [field(n - 2k - 1) > θ]                 -- left contact
          ∧ [field(n + 2k + 1) > θ]                 -- right contact
          ∧ [a·b·F_m + (a-b)·F_p + χ·F_c > 0]       -- positive energy

where:
  n = k² + a,   b = (k+1)² - n,   k = ⌊√n⌋
  θ = ⟨field⟩ / 2
  a = n - k²          (lower offset)
  b = (k+1)² - n      (upper offset)
```

## Mutation History

| Variant | File | Mutation | Notes |
|---------|------|----------|-------|
| THE-EQUATION-002 | `docs/avmr/THE_EQUATION.md` | Original (m=2, N=4) | DNA-specific |
| HACHIMOJI-003 | `docs/avmr/HACHIMOJI_EQUATION.md` | Generalized to m=3, N=8 | 8-base DNA |
| MASTER-EQUATION-004 | `Semantics/Extensions/MasterEquation.lean` | Discrete time recurrence | 6-step pipeline |
| QUATERNION-SLUG-005 | `Semantics/QuaternionGenomic.lean` | Quaternion encoding | Ternary output |

## Half-Thought: The Throat Geometry

The equation identifies "throat" positions where shell structure, topological contact, and thermodynamics align. But the original formulation left ambiguous:

> "These are the only positions worth encoding"

**Unfinished:** What happens at the throat boundary? The equation returns boolean (encode? ∈ {T,F}) but the physics suggests a fuzzy threshold. This gap is addressed in:
- `GenomicCompression.lean` — uses field-weighted compression ratio instead of boolean gate
- `QuaternionGenomic.lean` — SLUG-3 gate provides ternary classification (high/mid/low)

## Genealogy

```
ENE-BIND-001 (universal translator)
    ↓ geometric specialization
THE-EQUATION-002 (DNA-specific gate)
    ↓ alphabet generalization
HACHIMOJI-003 (8-base extension)
    ↓ discrete-time + hardware
MASTER-EQUATION-004 (6-step pipeline)
    ↓ quaternion encoding
QUATERNION-SLUG-005 (ternary SLUG-3)
```

## Mutation: From Boolean to Ternary

The most significant evolution is the output type:

| Version | Output | Meaning |
|---------|--------|---------|
| THE-EQUATION-002 | Boolean | encode? ∈ {T,F} |
| HACHIMOJI-003 | Boolean | Same gate logic |
| MASTER-EQUATION-004 | Q16.16 score | Continuous energy |
| QUATERNION-SLUG-005 | Ternary | {high, mid, low} |

The QUATERNION-SLUG-005 variant adds **chiral collapse detection** — when quaternions have incompatible chirality (negative scalar product), the system collapses to a "W" (waste) state. This is absent from all prior variants.

## Open Questions

1. Can the hyperbola index `ab` be generalized to non-square geometries?
2. Does the `χ·F_c` (codon recognition) term have a quaternion analog?
3. Is there a continuous-field version between THE-EQUATION-002 and MASTER-EQUATION-004?

---

*Part of the Equation Ancestry Project*
