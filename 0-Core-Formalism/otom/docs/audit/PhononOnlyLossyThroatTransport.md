# Phonon-Only Lossy Throat Transport Audit

## Purpose

This note records the safety correction to the higher-dimensional throat model:

```text
The forming throat is not a stable, high-fidelity transport channel.
It is highly lossy under torsion, curvature, chirality mismatch, memory strain, and boundary stress.
```

Therefore, the throat should not be modeled as a suitable channel for fragile, high-integrity payloads such as DNA or identity-bearing molecular structure. It is better treated as a coarse-grained transport model for phonons, vibrational energy, shock modes, and dissipative lattice signals.

## Core Statement

```text
not DNA transport
not identity-preserving matter transport
not lossless information transfer

yes phonon transport
yes shock-wave / vibrational mode transport
yes lossy energy-channel model
yes dissipative metamaterial selector model
```

## Corrected Doctrine

The throat is a lossy torsional corridor:

```text
I_out = I_in * exp(-L_throat) * R_repair
```

where the loss functional can include:

```text
L_throat = integral_gamma [
  lambda_T ||T(p)||^2
  + lambda_kappa |kappa(p)|
  + lambda_chi chi_mismatch(p)
  + lambda_mu memory_strain(p)
  + lambda_beta boundary_stress(p)
] dp
```

For fragile structured payloads, the loss budget is too severe:

```text
DNA / molecular identity requires near-exact ordering, chirality, phase, and bonding preservation.
The throat model does not provide that fidelity.
```

For phonons, the requirements are weaker:

```text
phonon transport only requires recoverable vibrational-mode statistics,
energy transfer, spectral envelope, attenuation profile, and dissipation accounting.
```

## Payload Classification

| Payload type | Throat suitability | Reason |
|---|---:|---|
| DNA / molecular identity | Rejected | Requires bond-level and sequence-level preservation through a lossy torsional corridor. |
| Protein folding state | Rejected / speculative | Requires fragile conformational identity and solvent/environment preservation. |
| Classical bitstream | Conditional | Possible only with redundancy, error correction, and explicit repair model. |
| Phonon packet | Plausible | Vibrational energy can survive as attenuated spectral content rather than exact structure. |
| Shock front | Plausible | Coarse energy/momentum transfer can be modeled through lossy Burgers-style dynamics. |
| Metamaterial activation signal | Plausible | Selector only needs threshold crossing, not perfect identity preservation. |

## Phonon Transport Reading

The useful channel is not object transport. It is mode transport:

```text
incoming shock / vibrational packet
  -> torsional throat deformation
  -> spectral attenuation and mode mixing
  -> phonon-load transfer
  -> bandgap localization or rejection
  -> dissipative relaxation
  -> active-cell selector update
```

In the material stack, this maps to:

```text
Burgers shock kernel          -> transport clock / compression gradient
phonon packet                 -> lossy signal payload
bandgap phonon dump           -> mode filter / energy localization
atomic tensegrity interlock   -> near-critical contact state
flexure misalignment          -> controlled defect / stress-localization point
virtual Sidon selector        -> admissible active-state projection
```

## Information-Theoretic Boundary

The throat can transmit information only in the Shannon / coarse-grained sense:

```text
recoverable signal = transmitted spectral structure - torsion/noise/loss
```

It should not be treated as preserving identity-bearing microstate structure.

Admissibility condition:

```text
SNR_out >= SNR_min
mode_overlap(phi_in, phi_out) >= eta_min
energy_loss <= L_max
repair_or_decoding_capacity > torsional_degradation
```

For phonons, a useful mode-overlap criterion is:

```text
eta = |<phi_in, phi_out>|^2 / (||phi_in||^2 ||phi_out||^2)
```

The throat is useful when eta remains above a task-specific threshold after attenuation.

## Relation to Active-Cell Counting

For the metamaterial selector, the relevant question is not whether the throat preserves a complex object. The relevant question is whether the phonon/shock signal can still trigger the correct active cells:

```text
chi_N(i,t) = 1 iff
  BurgersGradientGate_N(i,t)
  and BandGapPhononGate_N(i,t)
  and PhononModeOverlap_i(t) >= eta_min(N)
```

Density target remains:

```text
|{ i <= N : chi_N(i,t_N)=1 }| ~ sqrt(N)
```

## Audit Classification

```text
Receipt: PhononOnlyLossyThroatTransport
Status: STABILITY_CORRECTION
Gate: U_scope
Reason: the throat is coherent as a lossy phonon/shock/metamaterial selector model, but not as a high-fidelity matter or DNA transport model. It still requires spectral attenuation, torsion-loss, mode-overlap, and active-cell-counting receipts.
```

## Required Receipts

```text
TorsionLossReceipt
SpectralAttenuationReceipt
ModeOverlapReceipt
BandGapCouplingReceipt
PhononDissipationReceipt
ActiveCellCountingReceipt
ErrorCorrectionOrRepairReceipt optional for bitstream transport
```

## Boundary

This note explicitly rejects overclaiming:

```text
The throat model is not a safe or credible DNA transport channel.
It is a lossy vibrational/phononic transport abstraction for modeling shock, bandgap, and metamaterial activation.
```

The Sidon/arithmetic layer remains separate:

```text
phonon throat selector -> active cells
nonseparable encoding -> virtual or classical Sidon lock
compact density receipt -> sigma target
```
