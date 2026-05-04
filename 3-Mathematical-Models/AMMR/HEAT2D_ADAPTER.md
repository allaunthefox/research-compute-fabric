# Heat-2D Adapter

This repository is the 2D diffusion / dissipative-residue sandbox for the pressure-cavitation-vibration model catalog.

## Core role

```text
shock / pressure / vibration / combustion / friction event
    -> deposited scalar residue
    -> 2D diffusion
    -> measurable afterimage field
```

In the broader stack:

```text
Burgers handles shock smoothing.
heat-2D handles deposited residue.
```

## Native PDE

The upstream README defines the supported PDE family as:

```math
\partial_t u = \nabla\cdot(\alpha\nabla u)+f
```

where `u(x,y,t)` is the diffusive variable, `alpha(x,y)` is a space-dependent diffusivity, and `f(x,y,t)` is a source term.

For catalog integration, reinterpret these as:

| Field | Catalog interpretation |
|---|---|
| `u` | residual field: heat, deposited shock energy, vibration residue, or pressure-afterimage proxy |
| `alpha` | material / geometry-dependent diffusivity |
| `f` | source term from cavitation, combustion, friction, impact, or acoustic deposit |
| boundary conditions | heat/pressure residue sinks, walls, insulation, or imposed driving surfaces |

## Adapter definition

```math
X_{heat2D}=(u,\alpha,f,\Omega,\partial\Omega,\Delta x,\Delta y,\Delta t,B)
```

```math
\alpha_{heat2D}:X_{heat2D}\rightarrow U_T(x,y,t)
```

The adapter is admissible when:

1. boundary conditions are explicit,
2. source units are documented,
3. geometry masks are kept separate from solver logic,
4. stability requirements are checked for explicit integration,
5. implicit or Crank-Nicolson runs include linear-solver receipt metadata.

## Candidate source projections

### Cavitation collapse deposit

```math
f(x,y,t)=E_{shock}\exp\left(-\frac{(x-x_0)^2+(y-y_0)^2}{2\sigma_s^2}\right)\delta(t-t_0)
```

### Rocket cooling proxy

```math
\partial_t T=\nabla\cdot(\alpha\nabla T)+q''_{combustion}-q''_{coolant}
```

### Passive fluidic residue map

Use `alpha(x,y)` to encode channels, walls, pockets, and damping zones:

```math
\partial_t u=\nabla\cdot(\alpha(x,y)\nabla u)+f
```

### Burgers dissipative afterimage

```math
f_{diss}(x,y,t)=\lambda\nu(\partial_x U)^2
```

## Minimal tests

| Test | Purpose | Expected behavior |
|---|---|---|
| point impulse | pure diffusion sanity check | radial spread, decaying max |
| line source | shock-front residue proxy | front thickens like sqrt(t) |
| geometry mask | passive fluidic damping test | pockets and channels alter residue storage |
| cooling channel | rocket wall proxy | stable gradient under balanced source/sink |

## Failure modes

| Failure | Meaning |
|---|---|
| oscillation in pure explicit heat solve | timestep instability |
| negative values from nonnegative initial/source field | instability or source bug |
| energy growth with no source | boundary/source accounting error |
| claiming CFD from diffusion | category error |

## Scope warning

This repository should not be treated as a full Navier-Stokes, cavitation, rocket-engine, or acoustic solver.

Its correct role is narrower and more useful:

```text
Given a source event, what dissipative residue field remains?
```
