# Hawking Analog Phonon Loss Refinement

## Purpose

This note refines the finite, lossy throat / phonon-only transport model using Hawking-style horizon equations and analogue-gravity results.

The intent is not to claim a physical astrophysical black hole or a literal engineered wormhole. The equations are used as an analogue-horizon accounting layer for phonon emission, entropy flow, greybody filtering, and finite information recovery inside a lossy metamaterial throat.

## Core Statement

```text
forming throat / active material horizon
-> surface-gravity-like gradient
-> effective Hawking temperature
-> phonon emission spectrum
-> greybody / bandgap filtering
-> entropy and information budget
-> finite recoverable active events
```

This strengthens the selector by giving the phonon-only throat a thermodynamic emission model instead of only a threshold model.

## Hawking Baseline Equations

For a gravitational black hole, Hawking temperature is:

```text
T_H = hbar * kappa / (2*pi*k_B*c)
```

where `kappa` is surface gravity.

For analogue acoustic horizons, the equivalent form replaces light-speed geometry with an effective flow/sound-speed gradient. In simplified form:

```text
T_H,acoustic ~ hbar / (2*pi*k_B) * |d(v_flow - c_s)/dx|_horizon
```

In the project model, this becomes a material-throat emission temperature:

```text
T_eff(i,t) = hbar/(2*pi*k_B) * kappa_eff(i,t)
```

where:

```text
kappa_eff(i,t) = |partial_x(v_shock(i,t) - v_mode(i,t))| at the active horizon/gate
```

## Phonon Emission Spectrum

The emitted phonon occupation can be modeled by a thermal-like factor:

```text
n_omega(i,t) = Gamma_i(omega,t) / (exp[hbar*omega/(k_B*T_eff(i,t))] - 1)
```

where:

```text
Gamma_i(omega,t) = greybody / bandgap / transmission coefficient
```

This coefficient is the bridge to the existing bandgap phonon-dump model:

```text
Gamma_i small -> propagation blocked / localized / dissipated
Gamma_i large -> mode transmits through the gate
```

## Entropy and Finite Information Budget

Use a finite entropy budget for each timelike emission window:

```text
Delta S_emit(N) = integral_{T_emit(N)} integral d_omega s[n_omega(i,t)] dt
```

where a bosonic mode entropy proxy is:

```text
s(n) = (1+n)log(1+n) - n log n
```

Recoverable information is bounded by the channel capacity after loss:

```text
I_recoverable <= C_channel(T_emit, Gamma, T_eff, noise)
```

This prevents treating the throat as a lossless or infinite data source.

## Page-Curve / Recovery Analogy

The Page-curve lesson is not imported as a theorem about the material. It is used as an accounting discipline:

```text
early radiation alone may be insufficient
late radiation may be correlated with earlier modes
recovery requires collecting enough finite emitted modes
```

For the phonon throat:

```text
recoverable mode set = finite subset of emitted phonons whose correlations survive torsion and greybody loss
```

## Updated Selector Gate

The active-cell gate becomes:

```text
chi_N(i,t) = 1 iff
  t in T_emit(N)
  and |u_x(i,t;nu_N)| >= theta_A(N)
  and T_eff(i,t) >= T_min(N)
  and omega_shock(i,t) in BandGap_i(theta_i,N)
  and n_omega(i,t) >= n_min(N)
  and mode_overlap(phi_in,phi_out) >= eta_min(N)
  and Survivability_i(t) >= I_min(N)
```

The projected active set remains:

```text
I_active(N) = { i <= N : exists t in T_emit(N), chi_N(i,t)=1 }
```

Density target:

```text
|I_active(N)| / sqrt(N) -> 1 in limsup
```

## Loss Functional Update

The throat loss functional now includes Hawking/analogue-horizon emission terms:

```text
L_total = L_throat + L_greybody + L_entropy + L_mode_mixing
```

with:

```text
L_greybody = integral -log Gamma_i(omega,t) d_omega dt
L_entropy  = lambda_S * Delta S_emit
L_mode_mixing = lambda_M * (1 - mode_overlap)
```

and prior throat loss:

```text
L_throat = integral_gamma [
  lambda_T ||T||^2
  + lambda_kappa |kappa|
  + lambda_chi chi_mismatch
  + lambda_mu memory_strain
  + lambda_beta boundary_stress
] dp dt
```

Recoverability:

```text
I_out = I_in * exp(-L_total) * R_repair
```

Admissibility:

```text
I_out/I_in >= I_min(N)
T_emit(N) finite
Delta S_emit(N) finite
RepairRate_N > DegradationRate_N
```

## Interpretation for Virtual Sidon Forcing

The Hawking analogue layer does not create Sidon pair-sum injectivity. It refines the active event accounting:

```text
Hawking analogue equations -> finite phonon emission budget
phonon/bandgap/greybody loss -> recoverable active cells
Burgers shock -> alignment clock
nonseparable algebraic encoding -> Sidon lock
```

The virtual Sidon pair state remains:

```text
S_N(a,b) = Phi_N(a) + Phi_N(b) + Lambda_N(a,b)
```

where `Lambda_N` can include a nonseparable, finite-window, emission-correlation term derived from surviving phonon correlations.

## Evidence Anchors

Analogue black hole and acoustic horizon work supports using Hawking-style equations as a phonon emission model. Acoustic holes can spontaneously emit phonons at a Hawking temperature, and analogue systems have observed thermal Hawking-like spectra with temperature tied to surface gravity.

These are analogues, not evidence for literal spacetime throat transport.

## Audit Classification

```text
Receipt: HawkingAnalogPhononLossRefinement
Status: FORMAL_ANALOGY_DRAFT
Gate: U_scope
Reason: Hawking/analogue-horizon equations provide a strong phonon-emission and entropy-accounting model, but project-specific surface-gravity analogue, greybody/bandgap factor, finite emission budget, and active-cell counting proof remain required.
```

## Required Receipts

```text
AnalogHorizonReceipt
EffectiveSurfaceGravityReceipt
HawkingTemperatureReceipt
GreybodyBandgapReceipt
FiniteEntropyBudgetReceipt
ModeCorrelationReceipt
RecoverableEmissionReceipt
FiniteWindowActiveCountingReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```

## Boundary

This note does not claim:

```text
literal black holes
literal spacetime wormhole engineering
lossless information transfer
DNA or molecular transport through a throat
```

It claims only:

```text
Hawking-style analogue-horizon equations are useful for modeling finite phonon emission, entropy flow, greybody filtering, and recoverable active events in a lossy metamaterial throat.
```
