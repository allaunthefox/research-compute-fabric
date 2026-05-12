# Stellar Gas Full Cell Eigenmass Stability

Status: `FULL_CELL_EIGENMASS_STABILITY`

Decision: `REPORT_FULL_CELL_EIGENMASS_STABILITY_WITH_NULL_CONTROLS_HOLD_PHYSICAL_CLAIMS`

This probe checks the 25-cell DESI/MaNGA joined-cell eigenmass against all
available joined cells, leave-one-cell-out slices, deterministic null shuffles,
and feature ablations.

Claim boundary: this is evidence-geometry quality control only. It does not
promote physical mass, gas density, shock proof, object-level crossmatch, or
cosmology.

## Full-Cell Baseline

Cell count: `25`

Dominant eigenvalue:

```text
4.872368819
```

Dominant explained mass share:

```text
0.584684258
```

Dominant eigenvector:

- `log_desi_count`: 0.407663945
- `log_manga_count`: 0.045003218
- `partial_full_shock_fraction`: 0.391682145
- `shock_lier_fraction`: 0.375112377
- `BGS_share`: -0.370321192
- `ELG_share`: 0.443075496
- `LRG_share`: 0.443094949
- `QSO_share`: -0.088734468

## Stored 25-Cell Comparison

```text
common-basis cosine to stored probe: 1.0
top-cell overlap at 5:              5
max abs component delta:            0.0
```

## Eigensolver Diagnostics

```text
method:                 jacobi_symmetric
converged:              True
iterations:             87
final max off-diagonal: 6.353076600207743e-13
dominant residual L2:   0.0
```

## Leave-One-Cell-Out Stability

```text
loo count:                 25
min cosine to original:    0.996495428
median cosine to original: 0.99984468
mean cosine to original:   0.999501223
mean top5 overlap:         0.96
```

## Null And Ablation Controls

- `shuffled_feature_columns`: cosine `0.32053877`, explained share `0.251750194`, top5 overlap `0.0`
- `shuffled_shock_channels`: cosine `0.738854689`, explained share `0.460461221`, top5 overlap `1.0`
- `desi_count_removed`: cosine `0.998817144`, explained share `0.56433804`, top5 overlap `1.0`
- `shock_proxy_removed`: cosine `0.993658602`, explained share `0.589466219`, top5 overlap `1.0`
- `tracer_mix_removed`: cosine `0.992371346`, explained share `0.629616192`, top5 overlap `1.0`

## Holds

- `HOLD_PHYSICAL_MASS_INTERPRETATION`
- `HOLD_DIRECT_GAS_DENSITY_INFERENCE`
- `HOLD_SHOCK_PROOF`
- `HOLD_OBJECT_LEVEL_CROSSMATCH`
- `HOLD_SELECTION_FUNCTION_FIT`
- `HOLD_COSMOLOGY_FIT`
