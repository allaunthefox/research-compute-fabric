# 16D Chaos Game Field Shrinker

## Purpose

Lift the chaos game from a 2D visual attractor into a 16D FAMM field-shrinking engine.

Classic chaos game:

```math
x_{t+1}=a_i+r(x_t-a_i)
```

FAMM lift:

```math
X_{t+1}=A_{\sigma_t}+C_{\sigma_t}(X_t-A_{\sigma_t})+\epsilon_t
```

where `X_t ∈ R^16`, anchors are shortcut objects, and selection is weighted by semantic mass, scar pressure, invariant overlap, route cost, and receipt strength.

## Core idea

```text
2D chaos game
→ projected attractor toy

16D chaos game
→ manifold-addressed contraction engine
```

The visible fractal is only a projection:

```math
Y_t=P_{2D}(X_t)
```

Do not confuse the projection with the object. The object is the 16D route/address state.

## Typical anchors

```text
THEODORUS_SHELL
SIDON_PAIR_SUM_GATE
Z_DOMAIN_GATE
SEMANTIC_MASS_Z_ACCELERATOR
FAMM_ROUTE_PLOW
HESSIAN_EIGEN
DELTA_MEM
SYSTEM_CLOSURE
RESIDUAL_SEAL
CFD_LADDER
BraiNCA_LONG_RANGE_GATE
```

## Anchor selection

```math
P(\sigma_t=i\mid X_t)
\propto
\exp[
-\alpha d_i
-\beta\Omega_i
+\gamma I_i
-\eta C_i
+\lambda\mu_i
+\rho R_i
]
```

where `d_i` is anchor distance, `Ω_i` scar pressure, `I_i` invariant overlap, `C_i` route cost, `μ_i` semantic mass, and `R_i` receipt strength.

## Integration spine

```text
THEODORUS_SHELL
→ 16D_CHAOS_GAME_FIELD_SHRINKER
→ SIDON_PAIR_SUM_GATE
→ SEMANTIC_MASS_Z_ACCELERATOR
→ FAMM_ROUTE_PLOW
→ HESSIAN_EIGEN
→ SYSTEM_CLOSURE
→ RESIDUAL_SEAL
```

## Output receipt

The runner emits selected anchor counts, orbit hash, projection hash, final 16D state, final 2D projection, transition counts, route recommendations, and a no-drift boundary.

## No-drift boundary

This is a computational field shrinker. It proposes attractor basins and route candidates. It is not proof and must hand off to exact gates such as Sidon injectivity, Lean receipts, OISC receipts, contraction proof, or bounded residual seals.

## Project sentence

The chaos game becomes useful when lifted from a 2D drawing trick into a 16D FAMM contraction engine: anchors become shortcut objects, stochastic jumps become semantic-mass-weighted route choices, scars forbid bad transitions, and the visible fractal is only the projection of a higher-dimensional attractor search.
