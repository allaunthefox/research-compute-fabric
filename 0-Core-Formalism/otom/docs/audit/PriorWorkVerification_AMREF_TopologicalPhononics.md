# Prior Work Verification: AMREF / Sidon / Torsional Overlap

## Purpose

This note checks where prior work already solves large parts of the AMREF / virtual-Sidon / torsional-corridor stack.

The result is high overlap in acoustic topology, sparse recovery, and non-Hermitian loss modeling, but low overlap in explicit arithmetic Sidon integration.

## Core Finding

```text
Topological phononics solves robust protected transport.
Compressed sensing solves sparse recovery from partial acoustic measurements.
Non-Hermitian acoustic systems solve gain/loss and complex spectral localization.
AMREF adds the finite arithmetic audit layer: Golomb/Sidon/virtual-Sidon structure.
```

## Prior-Work Buckets

### 1. Topological phononics

Relevant for:

```text
topological voids
protected edge/interface states
robust transport through bends, defects, and disorder
acoustic information routing
```

Use in AMREF:

```text
parameterizes VoidFit(A), DefectAlignment(A), and protected transport basins
```

### 2. Compressed sensing / sparse acoustic recovery

Relevant for:

```text
recovering sparse acoustic sources
near-field acoustic holography
sub-Nyquist acoustic sampling
sparse modal reconstruction
```

Use in AMREF:

```text
parameterizes Repair/RemainderRecovery and finite measurement design
```

### 3. Non-Hermitian acoustic metamaterials

Relevant for:

```text
complex-valued spectra
gain/loss engineering
skin effects
exceptional points
loss-induced topology
edge/corner localization
```

Use in AMREF:

```text
parameterizes L_total, Gamma(omega), spectral localization, and lossy throat dynamics
```

## What Prior Work Does Not Yet Solve

Prior work generally treats sparsity as statistical/geometric and topology as wave-structural.

AMREF's missing/original bridge is:

```text
finite candidate number set A
-> spectral/remainder/topological score
-> DifferenceSetReceipt and SumSetReceipt
-> optional nonseparable virtual pair-state encoding
-> compact-density audit
```

In short:

```text
prior work supports physical and inverse-problem layers;
AMREF adds arithmetic admissibility and route-memory integration.
```

## Safer Replacement for Strong Claim

Do not say:

```text
these papers prove the Sidon/AMREF theory
```

Say:

```text
these papers solve major substrate layers: protected acoustic transport, sparse acoustic recovery, and gain/loss spectral modeling. The Sidon/arithmetic integration remains the project-specific proof obligation.
```

## Audit Table

| OTOM / AMREF component | Prior-work support | Remaining project gap |
|---|---|---|
| Acoustic/topological voids | Topological phononics / acoustic topological insulators | Map protected modes to finite candidate sets |
| Robust transport | Protected edge/interface/hinge/corner states | Finite recoverability through AMREF loss model |
| Sparse recovery | Compressive sensing / sparse acoustic holography | Map sparse recovery to active-cell selector |
| Lossy complex spectra | Non-Hermitian acoustic metamaterials | Calibrate Gamma, L_total, and repair terms |
| Arithmetic nonredundancy | Golomb/Sidon audit, not acoustic prior work | DifferenceSetReceipt / SumSetReceipt |
| Virtual Sidon state | AMREF-specific synthesis | Nonseparable pair-state proof |

## Required Receipts

```text
PriorWorkCitationReceipt
TopologicalPhononicsReceipt
SparseRecoveryReceipt
NonHermitianLossReceipt
AMREFMappingReceipt
DifferenceSetReceipt
SumSetReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```

## Audit Classification

```text
Receipt: PriorWorkVerification_AMREF_TopologicalPhononics
Status: HIGH_SUBSTRATE_OVERLAP_LOW_ARITHMETIC_OVERLAP
Gate: U_scope
Reason: prior work strongly supports acoustic topology, sparse recovery, and non-Hermitian loss layers, but does not by itself establish Sidon arithmetic, compact density, or virtual-pair injectivity.
```
