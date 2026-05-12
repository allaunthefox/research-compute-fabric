# Stellar Gas Multiscale Eigenmass Alignment

Status: `MULTISCALE_EIGENMASS_ALIGNMENT`

Decision: `ADMIT_MULTISCALE_EIGENMASS_ALIGNMENT_HOLD_PHYSICAL_MASS`

This probe compares the row-level DESI epoviz eigenmass with the DESI/MaNGA
joined-cell eigenmass. It reports a tracer-subspace cosine and explained-share
ratio between the literal row data and the coarse joined-cell overlap surface.

Claim boundary: this is not physical mass, not stellar mass, not gas-density
inference, and not a cosmology fit.

## Alignment Result

Tracer-subspace cosine:

```text
0.702922832
```

Alignment class:

```text
MODERATE_ALIGNMENT
```

Constraint sharpening factor:

```text
1.784206501
```

Dominant eigenvalue ratio, cell over row:

```text
1.48683875
```

## Tracer Subvectors

- `QSO`: row `0.178308871`, cell `-0.088734468`
- `ELG`: row `0.373691964`, cell `0.443075496`
- `LRG`: row `-0.001480357`, cell `0.443094949`
- `BGS`: row `-0.485709225`, cell `-0.370321192`

## Scale Comparison

```text
row level rows:        669377
row explained share:   0.327699881
cell level cells:      25
cell explained share:  0.584684258
```

## Holds

- `HOLD_PHYSICAL_MASS_INTERPRETATION`
- `HOLD_DIRECT_GAS_DENSITY_INFERENCE`
- `HOLD_OBJECT_LEVEL_CROSSMATCH`
- `HOLD_SELECTION_FUNCTION_FIT`
- `HOLD_COSMOLOGY_FIT`
