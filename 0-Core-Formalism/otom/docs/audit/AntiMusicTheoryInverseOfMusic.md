# Anti-Music Theory: Inverse-of-Music Number Set Search

## Purpose

This note defines the internal project concept `Anti-Music Theory`.

The goal is to intentionally invert music-theoretic regularities to find finite number sets that approximate the inverse of music: not random noise, but structured anti-consonance, anti-resolution, anti-tonality, and anti-stability.

The resulting finite sets are candidate arithmetic lenses for the virtual Sidon / spectral-remainder pipeline.

## Core Statement

```text
music theory finds stable perceptual order in pitch/time/interval space
anti-music theory searches for finite number sets that maximize structured instability
while remaining finite, auditable, and arithmetic-testable
```

This is not a claim that unpleasant sound is automatically useful. It is a finite search strategy:

```text
invert consonance metrics
invert tonal attraction
invert recurrence peaks
invert harmonicity
invert resolution paths
preserve enough structure for measurement and compression/audit
```

## What Is Being Inverted

### Ordinary music-theory attractors

```text
small-integer frequency ratios
high recurrence / periodicity
low roughness
stable tonal centers
strong harmonicity
predictable tension-release arcs
pitch-class distributions with tonal bias
```

### Anti-music targets

```text
large or irregular interval ratios
low recurrence against known consonant ratios
high but controlled roughness
weak or shifting tonal center
low harmonicity
blocked or inverted resolution
maximal residual after DFT/FFT tonal filtering
```

## Candidate Objective

For a finite candidate set:

```text
A = {a_1,...,a_m} subset {1,...,N}
```

construct spectral fingerprint:

```text
S_A[k] = sum_{a in A} w_a exp(i 2*pi*k*a/N)
P_A[k] = |S_A[k]|^2
```

Define a music-likeness score:

```text
MusicScore(A) =
  w_C * Consonance(A)
  + w_H * Harmonicity(A)
  + w_R * Recurrence(A)
  + w_T * TonalStability(A)
  + w_res * ResolutionScore(A)
```

Then define the anti-music score:

```text
AntiMusicScore(A) =
  w_rough * Roughness(A)
  + w_void * VoidFit(A)
  + w_rem * RemainderResonance(A)
  + w_topo * DefectAlignment(A)
  - w_music * MusicScore(A)
  - w_rand * RandomnessPenalty(A)
```

The `RandomnessPenalty` matters. Anti-music is not white noise; it is structured inverse order.

## Remainder Resonance Version

Given a finite filtered remainder:

```text
R_N[k] = F_N[k] - H_N[k]F_N[k]
```

score:

```text
Res(A;R_N) = <normalize(P_A), normalize(|R_N|^2)>
```

Anti-music candidate acceptance:

```text
A accepted iff
  AntiMusicScore(A) >= theta_anti(N)
  and AvgRes(A) >= theta_res(N)
  and VarRes(A) <= theta_var(N)
  and MusicScore(A) <= theta_music(N)
  and RandomnessPenalty(A) <= theta_rand(N)
```

## Arithmetic Constraints

Anti-music candidates must still be finite and audit-ready.

Difference-set audit:

```text
|{ |a_i-a_j| : i<j }| = m(m-1)/2
```

Sum-set audit:

```text
|{ a_i+a_j : i<=j }| = m(m+1)/2
```

If these fail, the set may still be passed into a virtual nonseparable encoding:

```text
S_N(a,b) = Phi_N(a)+Phi_N(b)+Lambda_N(a,b)
```

but it cannot be called classical Sidon without the pair-sum receipt.

## Inverse-Music Transform

A practical transform:

```text
1. Compute pitch-class / interval / spectral feature vector X_music.
2. Build a filter H_music that captures known tonal/consonant structure.
3. Remove or invert it: R_anti = X - H_music X.
4. Search finite candidate sets A whose fingerprints match R_anti.
5. Reject random-looking sets using compression / recurrence / variance penalties.
6. Audit accepted A with difference and sum-set tests.
```

## FAMM / Inverted FAMM Use

Forward FAMM:

```text
successful anti-music candidates that pass finite audits become basins
```

Inverted FAMM:

```text
scarred regions of music-like attractors suggest where inverse intervals may exist
persistent torsion in tonal filters suggests missing anti-music law sets
quarantine triggers if the inverse only works by deleting evidence or exploiting noise
```

## Why This Helps the Current Stack

The virtual Sidon pipeline needs finite candidate sets that are:

```text
structured enough to be recoverable
irregular enough to avoid trivial resonance/collision
spectrally visible after filtering
arithmetically auditable
```

Anti-Music Theory is a way to search that zone.

## Literature Anchors

The literature supports the pieces that are being inverted:

```text
consonance/dissonance as recurrence or dynamical signal structure
DFT-based tonal interval spaces
roughness / harmonicity / familiarity models of consonance
pitch-class DFT methods
music as ordered phase of sound
```

These support the construction of music-likeness metrics. They do not validate any specific anti-music set until finite testing is performed.

## Boundary

Do not claim:

```text
anti-music proves Sidon
unpleasant sound equals useful structure
inverted music theory produces theorem-grade number sets automatically
```

Allowed claim:

```text
Anti-Music Theory defines a finite search objective for finding structured inverse-tonal number sets that resonate with FFT-filtered remainders and can then be audited as Golomb/Sidon/virtual-Sidon candidates.
```

## Audit Classification

```text
Receipt: AntiMusicTheoryInverseOfMusic
Status: SEARCH_OBJECTIVE_DRAFT
Gate: U_scope
Reason: coherent as a finite candidate-generation method, but requires explicit metrics, finite data, threshold calibration, randomness controls, and arithmetic audits.
```

## Required Receipts

```text
MusicFeatureReceipt
MusicFilterReceipt
InverseTransformReceipt
AntiMusicScoreReceipt
RandomnessPenaltyReceipt
RemainderResonanceReceipt
FiniteWindowAverageReceipt
DifferenceSetReceipt
SumSetReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```
