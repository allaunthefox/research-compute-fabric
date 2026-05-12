# DESI Epoviz Row Eigenmass Probe

Status: `DESI_ROW_EIGENMASS`

Decision: `ADMIT_DESI_ROW_EIGENMASS_HOLD_PHYSICAL_MASS`

This probe streams the DESI EDR epoviz CSV row-by-row and computes the dominant
correlation eigenvector over geometry, redshift, rosette phase, and tracer
identity. It is a literal-data stress pass over the DESI epoviz surface.

Claim boundary: this is SMN/evidence-load mass, not physical mass, not stellar
mass, not gas-density inference, and not a cosmology fit.

## Result

Rows read: `669377`

Dominant eigenvalue:

```text
3.276998814
```

Dominant explained mass share:

```text
0.327699881
```

## Dominant Eigenvector

- `x_glyr`: -0.339632035
- `y_glyr`: -0.350843233
- `z_glyr`: 0.284495161
- `redshift`: 0.51941062
- `rosette_sin`: -0.005671442
- `rosette_cos`: -0.058708375
- `tracer_QSO`: 0.178308871
- `tracer_ELG`: 0.373691964
- `tracer_LRG`: -0.001480357
- `tracer_BGS`: -0.485709225

## Eigensolver Diagnostics

```text
method:                 jacobi_symmetric
converged:              True
iterations:             149
final max off-diagonal: 1.5584514983054888e-13
dominant residual L2:   0.0
```

## Population Counts

Tracer counts:

- `BGS`: 228630
- `ELG`: 261489
- `LRG`: 125174
- `QSO`: 54084

Cosmic redshift bins:

- `z_0_0p1`: 24267
- `z_0p1_0p5`: 224101
- `z_0p5_1`: 213259
- `z_1_2`: 196842
- `z_2_plus`: 10908

## Holds

- `HOLD_PHYSICAL_MASS_INTERPRETATION`
- `HOLD_DIRECT_STELLAR_GAS_INFERENCE`
- `HOLD_OBJECT_LEVEL_MANGA_CROSSMATCH`
- `HOLD_SELECTION_FUNCTION_FIT`
- `HOLD_COSMOLOGY_FIT`
