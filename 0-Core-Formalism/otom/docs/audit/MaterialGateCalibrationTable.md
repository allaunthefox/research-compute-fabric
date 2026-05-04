# Material Gate Calibration Table

## Purpose

This note records the first material-calibration layer for the information-theoretic emergent throat and virtual Sidon selector model.

The proposed table is useful as a hypothesis table, but the listed `sigma` values must be treated as model outputs to be calibrated, not as measured facts. Material speed of sound and shock velocity alone do not determine Sidon density.

## Core Correction

```text
Material acoustic properties can parameterize the selector.
They do not directly measure Sidon density.
```

Correct dependency chain:

```text
material parameters
  -> acoustic horizon / bandgap / damping parameters
  -> recoverable active-cell set I_active(N)
  -> finite-window active-cell counting
  -> nonseparable encoding Phi_N
  -> Sidon pair-sum audit
  -> compact-density receipt
```

## Candidate Materials

| Material type | Role in model | Expected behavior |
|---|---|---|
| Fused silica | low-loss stiff baseline | strong propagation; needs engineered isolation to suppress echoes |
| Lead | high-loss damping baseline | strong attenuation; may over-damp recoverable modes |
| Engineered resonator metamaterial | tunable selector candidate | best candidate because bandgap, damping, resonance, and horizon-like gradient can be tuned |
| Beryllium | high-rigidity low-loss baseline | useful contrast material; likely sparse unless engineered with lossy structure |

## Required Calibration Variables

Define a measured/calibrated identity quotient:

```text
Q_id(N) = Recoverability(N) * Selectivity(N) * Compactness(N)
```

where:

```text
Recoverability(N) = exp(-L_total) * R_repair
Selectivity(N)    = active fraction produced by shock/bandgap/phonon gates
Compactness(N)    = encoding-range efficiency after Phi_N or virtual pair-state projection
```

A physical material quotient can be written schematically as:

```text
Q_mat = Z_eff * T_window * Gamma_bandgap * eta_mode * R_repair / gamma_diss
```

All factors must be nondimensionalized before comparison.

## Acoustic Horizon Calibration

The Hawking-equivalent temperature cannot be determined from `v` and `c_s` alone. It depends on a gradient scale near the horizon:

```text
T_eff = hbar/(2*pi*k_B) * kappa_eff
kappa_eff = |partial_x(c_s - v_flow)| at v_flow = c_s
```

Approximation:

```text
kappa_eff ~ |c_s - v| / ell_h
```

Therefore the table must include:

```text
ell_h = horizon gradient length scale
```

or the Hawking-temperature column remains schematic.

## Audit Classification

```text
Receipt: MaterialGateCalibrationTable
Status: HYPOTHESIS_CALIBRATION_DRAFT
Gate: U_scope
Reason: useful for selecting candidate substrates, but sigma values are not empirical receipts until derived from calibrated active-cell counts, loss model, and nonseparable encoding audit.
```

## Required Receipts

```text
MaterialParameterReceipt
AcousticImpedanceReceipt
GradientLengthScaleReceipt
BandgapTransmissionReceipt
DampingCoefficientReceipt
ModeOverlapReceipt
RepairOperatorReceipt
FiniteWindowActiveCountingReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```
