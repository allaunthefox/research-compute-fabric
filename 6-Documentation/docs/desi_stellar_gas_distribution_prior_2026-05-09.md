# DESI Stellar Gas Distribution Prior

**Date:** 2026-05-09

**Status:** `PRIOR_BRIDGE_HOLD_FIT`

**Decision:** `ADMIT_PRIOR_BRIDGE_HOLD_FIT`

**Claim boundary:** DESI large-scale structure can supply an environment prior
for stellar-gas distribution. A coarse DESI/MaNGA cell join exists; object-level
crossmatch remains `HOLD`. This is not a direct gas map, not a cosmology fit,
and not a local shock model.

## Core Idea

DESI does not directly measure stellar gas. It measures a huge galaxy/quasar
redshift tracer field. That is still useful because gas is not randomly placed:
it follows halos, filaments, nodes, voids, star-formation history, feedback, and
selection effects.

So the safe inference is:

```text
DESI tracer density
  -> matter / environment prior
  -> probable stellar-gas distribution
  -> local update from MaNGA line ratios
  -> residual map where the prior fails
```

## Inference Ladder

```text
L0: delta_g(x,z) = (n_g(x,z) - mean(n_g(z))) / mean(n_g(z))
L1: delta_m(x,z) ~= delta_g(x,z) / b_g(type,z)
L2: P(env | x,z) = softmax([void, sheet, filament, node]; delta_m, grad(delta_m), Hessian(Phi))
L3: rho_gas_prior(x,z) proportional_to f_b * rho_m(x,z) * G(env,z) * S(selection)
L4: P(gas_state | DESI_env, MaNGA_lines) proportional_to P(MaNGA_lines | gas_state) * P(gas_state | DESI_env)
```

The important step is L4. DESI supplies the wide-field environment prior; MaNGA
supplies local emission-line evidence.

## What This Gives Us Now

- A principled way to turn large-scale topology into a gas-distribution prior.
- A join target for MaNGA line-ratio diagnostics.
- A residual surface: places where cosmic-web environment predicts gas state
  poorly become high-value FAMM/scar targets.
- A clean SMN interpretation: DESI environment classes and MaNGA diagnostic
  classes are high semantic-load objects, but still not proof.

## What Remains HOLD

```text
direct stellar gas map             HOLD
cosmology fit                      HOLD
dark-energy evolution claim        HOLD
shock transfer claim               HOLD
object-level DESI/MaNGA crossmatch HOLD
coarse DESI/MaNGA cell join        EXISTS
```

## Next Tool Step

Use the existing coarse DESI/MaNGA cell join as the population prior, then keep
the object-level crossmatch path explicitly held until a cone and redshift
window receipt exists:

```text
match if angular_sep < theta_max and |z_DESI - z_MaNGA| < dz_max
```

After that, fit environment bins against MaNGA line-ratio classes and keep the
negative controls visible.

## Receipt

```text
shared-data/data/stack_solidification/desi_stellar_gas_distribution_prior_receipt.json
```

## Receipt Backlinks

- Coarse cell join receipt: `shared-data/data/stellar_gas_observation/desi_epoviz_manga_population_cell_join_receipt.json`
- Tiddler: `6-Documentation/tiddlywiki-local/wiki/tiddlers/DESI Stellar Gas Distribution Prior.tid`
