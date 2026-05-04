# Spectral Void Pattern Recognition

## Purpose

This note refines the torsional-corridor model by treating voids and bandwidth drops as frequency-domain signatures of the active-cell selector.

The useful claim is:

```text
bandwidth drops / spectral voids can reveal structured destructive interference in the material throat.
```

The unsafe claim is:

```text
spectral voids by themselves prove the Sidon property.
```

Voids can be used as a diagnostic and candidate generator. A separate pair-sum audit or nonseparable encoding proof is still required.

## Core Model

For a finite active index set `A = {a_1,...,a_m}`, define an idealized spectral field:

```text
F_A(omega) = sum_{a in A} w_a cos(a omega + phi_a)
```

or complex form:

```text
S_A(omega) = sum_{a in A} w_a exp(i a omega)
Power_A(omega) = |S_A(omega)|^2
```

Expanding the power spectrum:

```text
Power_A(omega) = sum_a w_a^2 + 2 sum_{a<b} w_a w_b cos((a-b) omega + phi_ab)
```

Important correction:

The direct Fourier power spectrum exposes the **difference set** `A-A`, not the sum set `A+A`.

The Sidon/B2 property is about uniqueness of unordered sums:

```text
a+b = c+d -> {a,b} = {c,d}
```

while a Golomb ruler is about uniqueness of positive differences:

```text
a-b = c-d -> (a,b) = (c,d)
```

For finite integer sets, distinct differences imply Sidon, but the diagnostic being visualized by `cos(a omega)` is primarily a difference-spectrum diagnostic.

## Void / Bandwidth Drop Definition

A spectral void is a frequency interval where transmission or spectral power drops below threshold:

```text
Void_epsilon = { omega : Gamma(omega) <= epsilon_G }
```

or for the idealized field:

```text
Void_theta = { omega : F_A(omega) <= -Theta }
```

In a physical phononic system, the measured version is:

```text
Void_measured = { omega : TransmissionLoss(omega) >= TL_min }
```

## Physical Interpretation

Voids can come from:

```text
Bragg scattering from periodic structure
local resonance stop bands
coupled Bragg/local resonance interference
viscoelastic damping
chiral/rotational coupling
boundary/truncation resonances
self-healing repair failure windows
```

Therefore a void pattern is evidence of structured wave control, not automatically arithmetic uniqueness.

## Spectral Receipt

To use voids as an audit receipt, require:

```text
1. measured or simulated transmission spectrum Gamma(omega)
2. extracted void intervals V_k
3. model-predicted void intervals from active index set A
4. fit/error score between predicted and measured voids
5. independent pair-sum or difference-set audit of A
```

Proposed fit score:

```text
VoidFit(A) = 1 - measure(V_measured symmetric_difference V_predicted) / measure(V_measured union V_predicted)
```

For discrete samples:

```text
VoidFit(A) = 1 - |V_measured Δ V_predicted| / |V_measured ∪ V_predicted|
```

## Difference-Spectrum Diagnostic

Because power expansion exposes `A-A`, a clean diagnostic is:

```text
D_A = { |a_i - a_j| : i < j }
```

Golomb/difference uniqueness:

```text
|D_A| = m(m-1)/2
```

If this holds, then `A` is a Golomb ruler and therefore also Sidon under ordinary integer addition.

This is stronger than merely seeing repeated voids.

## Sum-Set Diagnostic

For the Sidon condition directly:

```text
Sigma_A = { a_i + a_j : i <= j }
```

Sidon/B2 uniqueness:

```text
|Sigma_A| = m(m+1)/2
```

This must be checked explicitly if the claim is Sidon rather than Golomb.

## Updated Gate

The spectral void gate selects candidate active indices:

```text
chi_void(i,t) = 1 iff
  omega_i lies outside measured voids
  and mode_overlap_i >= eta_min
  and Gamma_i(omega,t) >= Gamma_min
```

or, for destructive-threshold activation:

```text
chi_void(i,t) = 1 iff F_A(omega_i,t) <= -Theta_N
```

The selected set then requires:

```text
DifferenceSetReceipt or SumSetReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```

## Literature Anchors

Phononic crystals and metamaterials support the physical basis for voids/bandwidth drops through Bragg scattering, local resonance, destructive interference, chiral coupling, and bandgap engineering. These support the spectral receipt, not direct proof of Sidon uniqueness.

## Audit Classification

```text
Receipt: SpectralVoidPatternRecognition
Status: DIAGNOSTIC_RECEIPT_DRAFT
Gate: U_scope
Reason: spectral voids can diagnose structured destructive interference and candidate active sets, but they require explicit difference-set/sum-set audits before being treated as Sidon evidence.
```

## Required Receipts

```text
TransmissionSpectrumReceipt
VoidExtractionReceipt
VoidFitReceipt
DifferenceSetReceipt
SumSetReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```
