# Stellar Gas Eigenvector Mass Probe

Status: `SMN_EIGENVECTOR_MASS`

Decision: `ADMIT_SMN_EIGENVECTOR_MASS_HOLD_PHYSICAL_MASS`

This probe computes the dominant covariance eigenvector over the coarse DESI
epoviz to MaNGA population-cell join. The output is an SMN/evidence-load mass
direction: it ranks the current coarse joined cells by this diagnostic score so
later zoom work can choose explicit follow-up targets.

Claim boundary: this is not physical mass, not stellar mass, not a direct gas
density map, and not a cosmology fit.

## Result

Dominant eigenvalue:

```text
4.872368819
```

Dominant explained mass share:

```text
0.584684258
```

## Dominant Eigenvector

- `log_desi_count`: 0.407663945
- `log_manga_count`: 0.045003218
- `partial_full_shock_fraction`: 0.391682145
- `shock_lier_fraction`: 0.375112377
- `BGS_share`: -0.370321192
- `ELG_share`: 0.443075496
- `LRG_share`: 0.443094949
- `QSO_share`: -0.088734468

## Eigensolver Diagnostics

```text
method:                 jacobi_symmetric
converged:              True
iterations:             87
final max off-diagonal: 6.353076600207743e-13
dominant residual L2:   0.0
```

## Top Cell Masses

- `ra03_north__z_008_plus`: mass `0.11642`, score `4.401578`, DESI `315331`, MaNGA `305`
- `ra03_south__z_008_plus`: mass `0.112959`, score `4.202232`, DESI `100231`, MaNGA `8`
- `ra04_north__z_008_plus`: mass `0.11274`, score `4.18963`, DESI `181621`, MaNGA `219`
- `ra02_north__z_008_plus`: mass `0.110828`, score `4.079512`, DESI `44035`, MaNGA `364`
- `ra02_south__z_008_plus`: mass `0.107057`, score `3.862327`, DESI `12520`, MaNGA `15`
- `ra02_south__z_006_008`: mass `0.047288`, score `0.419776`, DESI `91`, MaNGA `3`
- `ra03_north__z_006_008`: mass `0.039897`, score `-0.005909`, DESI `3456`, MaNGA `374`
- `ra04_north__z_006_008`: mass `0.034318`, score `-0.327257`, DESI `2102`, MaNGA `143`
- `ra02_north__z_006_008`: mass `0.03392`, score `-0.350201`, DESI `608`, MaNGA `259`
- `ra03_north__z_002_004`: mass `0.032102`, score `-0.454923`, DESI `2439`, MaNGA `1622`

## Holds

- `HOLD_PHYSICAL_MASS_INTERPRETATION`
- `HOLD_OBJECT_LEVEL_CROSSMATCH`
- `HOLD_DIRECT_GAS_DENSITY_INFERENCE`
- `HOLD_SELECTION_FUNCTION_FIT`
- `HOLD_COSMOLOGY_FIT`
