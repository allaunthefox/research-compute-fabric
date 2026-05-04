# Band-Gap Phonon Dump Material Gate Audit

## Purpose

This note refines the density/selector problem into a material mechanism:

A shockwave entering a structured material can activate an alignment window. At the material level, the shock perturbs lattice strain, interlayer registry, and electronic/elastic band structure. Energy that cannot propagate through the selected bandgap is redirected into localized phonon modes, dissipation, or interface reconstruction.

This supports the physical selector/gate layer only. It does not prove the arithmetic Sidon property or the compact density constant.

## Corrected Physical Reading

The phrase "fills the valence of the atomic lattice" should be interpreted carefully.

Safer formulation:

```text
shockwave perturbs lattice strain and interlayer registry
-> band structure / phononic bandgap changes
-> blocked or localized wave energy couples into phonon modes
-> phonon load dissipates or relaxes through lattice damping
```

For electronic materials, the relevant mechanism is electron-phonon coupling or band-gap modulation under strain/shock. For phononic crystals and elastic metamaterials, the relevant mechanism is an engineered phononic bandgap that blocks, localizes, attenuates, or redirects elastic wave energy.

## Mechanism Chain

```text
Shockwave enters field
  -> local strain and compression gradient rises
  -> Burgers alignment gate opens
  -> quasi-charged cells become temporarily aligned
  -> phononic/electronic band structure shifts
  -> forbidden/blocked propagation region appears
  -> excess energy localizes into phonon modes
  -> viscosity/damping dissipates phonon load
  -> lattice relaxes back toward anisotropy
```

## Relation to Density Selector

The previous density target said that, for sigma = 1, the active cells selected over an interval `[1,N]` must scale like `sqrt(N)`.

The material interpretation is:

```text
active cells = cells where shock gradient crosses threshold and bandgap/phonon coupling admits localized transfer
```

So the selector should be treated as a combined gate:

```text
chi_N(i) = BurgersGradientGate_N(i) AND BandGapPhononGate_N(i)
```

The density receipt then becomes:

```text
|{ i <= N : chi_N(i) = true }| ~ sqrt(N)
```

This is not automatic. It requires tuning the viscosity, threshold, bandgap, geometry period, and shock amplitude as functions of scale.

## Candidate Mathematical Gate

Discrete form:

```text
chi_N(i) = 1 iff |u_x(i,t;nu_N)| >= theta_A(N)
              and omega_shock(i,t) lies in the local bandgap window
              and phonon_dump(i,t) >= theta_P(N)
```

where:

```text
u_N       = viscosity scale
 theta_A(N) = alignment threshold
omega_shock = dominant local shock frequency
bandgap window = frequency range where propagation is suppressed
phonon_dump = localized phonon energy / dissipated wave energy
```

## Evidence Anchors

The literature supports the pieces of this mechanism:

- phononic crystals use bandgaps to suppress elastic-wave propagation;
- shock excitation can be attenuated by phononic bandgaps;
- metamaterials can localize, guide, or harvest mechanical wave energy;
- shock waves can alter optical band gaps in crystals through lattice/defect effects;
- electron-phonon coupling can strongly modulate band gaps in some semiconductors;
- pressure and strain can tune layered van der Waals / graphene heterostructure band structure.

## Audit Classification

```text
Receipt: BandGapPhononDumpMaterialGate
Status: LITERATURE_PLAUSIBLE
Gate: U_scope
Reason: literature supports shock/bandgap/phonon coupling and wave attenuation, but the project still needs a material-specific band structure, shock spectrum, phonon dissipation model, and active-cell counting proof.
```

## Required Receipts

```text
MaterialBandGapReceipt
ShockSpectrumReceipt
PhononCouplingReceipt
BandGapAttenuationReceipt
ActiveCellCountingReceipt
ScaleTuningReceipt
DissipationRelaxationReceipt
```

## Boundary

This layer strengthens the selector mechanism:

```text
Burgers shock kernel + bandgap phonon dump -> physically grounded active-cell selector
```

It does not provide:

```text
NonseparableEncodingReceipt
GlobalSidonReceipt
CompactDensityReceipt
```

Those remain algebraic obligations in the Burgers-Ruzsa decoupling layer.
