# DESI NOIRLab2610 Calibration Note

**Date:** 2026-05-09

**Status:** `EXTERNAL_CALIBRATION_PRIOR`

**Source:** https://noirlab.edu/public/news/noirlab2610/

**Claim boundary:** this is an external observation-scale calibration note. It
is not imported data, not a cosmology fit, not a proof of the universe model,
and not a stellar-gas emission-line calibration by itself.

## Source Facts

The NOIRLab release is titled:

```text
DESI Completes Planned 3D Map of the Universe and Continues Exploring
```

The page metadata states that the Dark Energy Spectroscopic Instrument has
mapped more than 47 million galaxies and quasars, producing the largest
high-resolution 3D map of the Universe to date. It also states that DESI is
mounted on the NSF Nicholas U. Mayall 4-meter telescope and will continue
observations into 2028 because of instrument performance and hints that dark
energy might evolve.

## Why This Calibrates The Stack

This belongs in the stack as a large-scale-structure calibration prior:

```text
redshift sample count
+ sky footprint / selection function
+ galaxy/quasar tracer class
+ BAO / expansion-distance surface
+ survey extension window
```

For the project model, this is useful because it supplies an external anchor for
how information physics propagates through large countable tracers rather than
through a single local channel. In SMN terms, the high semantic mass comes from
population size, tracer diversity, selection-function burden, and cosmological
parameter pressure.

## Calibration Variables To Track

```text
N_tracers        > 47 million galaxies and quasars
instrument       DESI
mount            Mayall 4-meter telescope
map_kind         high-resolution 3D large-scale-structure map
continuation     observations extended into 2028
calibration_use  expansion-distance / dark-energy evolution prior
```

## Minimal Equation Hooks

These are hooks, not fitted results:

```text
z -> comoving_distance(z; H0, Omega_m, Omega_DE, w)
BAO scale -> D_M(z) / r_d and H(z) * r_d
semantic_load_DESI ~ log(N_tracers) + tracer_diversity + selection_function_burden
```

The next useful tool step is to keep DESI as a calibration-prior source for
large-scale topology and expansion models, while keeping MaNGA line-ratio data
as the local stellar-gas/shock-proxy lane.

## HOLD Conditions

- HOLD any numerical cosmology claim until a DESI data table, covariance, and
  model-fit receipt are imported.
- HOLD any stellar-gas transfer until a bridge explicitly maps large-scale
  structure statistics to local gas diagnostics.
- HOLD any dark-energy-evolution claim until source papers/data products are
  cited and fit locally.
