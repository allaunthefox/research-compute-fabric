# Sidon Field Review: Combinatorial Optimization and Signal Integrity

## Purpose

This note records a reviewer-style synthesis of the Sidon/Golomb/AMREF/GCL/FAM-gated ascent framework as a finite optimization stack for signal integrity.

The framework treats a candidate set `A` as a finite object that must survive several independent attack surfaces:

```text
additive uniqueness
subtractive uniqueness
spectral aliasing
harmonic collapse
white-noise collapse
compression spoofing
probe overfitting
unfunded ascent
```

## Clean Thesis

```text
The Sidon field is a rigorous filter against redundant correlation.
Redundancy can hide in additive structure, subtractive structure, spectral aliases, compression artifacts, or probe bias.
```

The hard classical boundary remains:

```text
C_B2(A) = 0
```

Everything else is supporting pressure, diagnostics, or promotion gating.

## Collision Domains

### Primary collision field: Sidon / B2

A set `A` is Sidon if every unordered pair-sum is unique.

Attack:

```text
a_i + a_j = a_k + a_l
with {i,j} != {k,l}
```

Metric:

```text
C_B2(A) = sum_s max(0, mu_+(s; A) - 1)
```

Goal:

```text
C_B2(A) = 0
```

This ensures no hidden additive collision debt.

### Difference field: Golomb

Attack:

```text
a_i - a_j = a_k - a_l
```

Metric:

```text
C_D(A) = sum_d max(0, mu_D(d; A) - 1)
```

Goal:

```text
C_D(A) = 0
```

This removes repeated spacing echoes that create spectral aliases and false stability.

## Spectral Probing and AMREF

Fourier fingerprint:

```text
S_A(k) = sum_{a in A} w_a exp(2*pi*i*k*a/N)
P_A(k) = |S_A(k)|^2
```

Important boundary:

```text
P_A probes A - A directly.
P_A does not prove A + A uniqueness.
```

Void alignment:

```text
V_A = sum_k W_void(k) * P_A(k)
```

B2-hardened AMREF:

```text
AMREF_B2(A, epsilon) = AMREF(A, epsilon) - lambda_B2 * C_B2(A)
```

Purpose:

```text
Prevent the optimizer from selecting a candidate that is spectrally attractive but arithmetically invalid.
```

## GCL and Metaprobe Filters

GCL profile:

```text
GCL(A) = (
  geometry,
  compression,
  cognitive_load,
  spectral_profile,
  topology,
  arithmetic_profile
)
```

Metaprobe checks:

```text
WindowStability
PermutationStability
EncodingInvariance
NoiseRobustness
ReceiptPreservation
CounterexampleYield
```

Purpose:

```text
Prevent metric gaming, where a candidate looks valid only under a privileged window, encoding, or probe configuration.
```

## FAM-Gated Ascent

Transition:

```text
A -> B
```

Energy available:

```text
EnergyAvailable(A -> B) =
  valid compression gain
  + residual gain
  + void-fit gain
  + metaprobe surplus
  + basin support
  + receipt integrity
```

Ascent cost:

```text
AscentCost(A -> B) =
  lambda_B2 * C_B2(B)
  + lambda_D * C_D(B)
  + GCL diff penalty
  + randomness penalty
  + uncontrolled torsion penalty
  + missing receipt penalty
```

Promotion condition:

```text
EnergyAvailable(A -> B) >= AscentCost(A -> B)
```

with hard receipts required for theorem-level promotion.

## Attack / Defense Table

| Attack vector | Mathematical metric | Defense / constraint |
|---|---|---|
| Pair-sum degeneracy | `C_B2(A)` | B2 hardness, `C_B2 = 0` |
| Spacing echoes / aliasing | `C_D(A)` | Golomb constraint, `C_D = 0` |
| Harmonic collapse | `P_A(k)` and music score | Spectral void alignment and AMREF residual pressure |
| Compression spoofing | `Delta_CR(A -> B)` | Threshold plus receipt integrity |
| Probe overfitting | `M_meta(P,A)` | Metaprobe stability requirement |
| Unfunded ascent | `AscentCost(r)` | FAM-gated energy balance |

## Final Review Conclusion

The framework turns Sidon-set search into a high-integrity finite optimization problem.

A candidate set is not allowed to claim structure merely because it is sparse, compressible, spectrally clean, or visually attractive. It must survive the hard additive collision audit and then pass supporting probes without deleting constraints.

The correct final claim is:

```text
The Sidon field attacks every route by which redundancy can disguise itself as structure.
```

## Boundary

Do not claim:

```text
compression proves Sidon
spectral cleanliness proves Sidon
metaprobe score proves Sidon
FAM energy balance replaces the B2 audit
```

Allowed claim:

```text
Compression, spectral probes, GCL diff, and metaprobe filters strengthen candidate selection, but classical Sidon validity still requires C_B2(A)=0.
```

## Audit Classification

```text
Receipt: SidonField_CombinatorialOptimization_SignalIntegrityReview
Status: REVIEW_SYNTHESIS
Gate: U_scope
Reason: coherent finite optimization and signal-integrity interpretation; still requires implemented counters, thresholds, proof receipts, and worked examples before V_scope promotion.
```
