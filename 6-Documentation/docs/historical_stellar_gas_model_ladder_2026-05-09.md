# Historical Stellar Gas Model Ladder

**Date:** 2026-05-09

**Decision:** `ADMIT_HISTORICAL_PRIOR_SURFACE`

**Claim boundary:** this is a historical prior and routing surface. It
does not claim that the current MaNGA proxy fit validates any physical
law or detects a specific shock event.

## Why This Helps

The stack now has a wide historical basis for stellar gas modeling rather
than a single modern blob. Each law family gets a receipt role:

```text
historical law -> observable hook -> current column/proxy -> gate
```

## Current Support

- Models mapped: 15
- Admitted prior support: 4
- Partial prior support: 11
- No current observable: 0

## Ladder

| Period | Law family | Names | Support | Decision |
|---|---|---|---:|---|
| 1687 | `gravity_and_orbital_context` | Isaac Newton | 1.000000 | `ADMIT_PRIOR_SUPPORT` |
| 1738 | `pressure_flow_energy` | Daniel Bernoulli | 0.995165 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1750s | `inviscid_fluid_conservation` | Leonhard Euler | 0.992577 | `ADMIT_PRIOR_SUPPORT` |
| 1820s-1840s | `viscous_fluid_dynamics` | Claude-Louis Navier, George Gabriel Stokes | 0.983193 | `ADMIT_PRIOR_SUPPORT` |
| 1860s-1870s | `kinetic_theory` | James Clerk Maxwell, Ludwig Boltzmann | 0.983193 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1870s-1880s | `shock_jump_conservation` | William John Macquorn Rankine, Pierre-Henri Hugoniot | 0.989179 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1800s-1900s | `spectral_line_identification` | Fraunhofer, Kirchhoff, Bunsen, many later spectroscopists | 0.560264 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1870s-1900s | `polytropic_stellar_structure` | Jonathan Homer Lane, Robert Emden | 0.970548 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1920 | `ionization_state` | Meghnad Saha | 0.758040 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1900s-1930s | `absorption_emission_transport` | Karl Schwarzschild, Arthur Eddington, Subrahmanyan Chandrasekhar | 0.634580 | `ADMIT_PRIOR_SUPPORT` |
| 1902 | `gravitational_instability` | James Jeans | 0.983193 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1940s-1950s | `self_similar_blast_front` | Leonid Sedov, Geoffrey Taylor, John von Neumann | 0.995165 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1940s | `magnetized_plasma_flow` | Hannes Alfven | 0.983193 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| 1958 | `stellar_wind_outflow` | Eugene Parker | 0.991283 | `HOLD_PARTIAL_PRIOR_SUPPORT` |
| late_1900s-2000s | `radiation_hydrodynamic_breakout` | radiation hydrodynamics community | 0.995165 | `HOLD_PARTIAL_PRIOR_SUPPORT` |

## Source Notes

- NASA Report 1135: Equations, Tables, and Charts for Compressible Flow: `https://www.nasa.gov/wp-content/uploads/2023/03/equations-tables-charts-compressibleflow-report-1135.pdf`
- NASA Technical Reports Server: Local stability analysis for a planar shock wave: `https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19850004556.pdf`
- Sedov Equation, Wolfram ScienceWorld: `https://scienceworld.wolfram.com/physics/SedovEquation.html`
- Coupling of matter and radiation at supernova shock breakout: `https://doi.org/10.1093/mnras/sts577`

## Next Gate

The current support is strongest for velocity, dispersion, and named
line-ratio proxy lanes. The next refinement is adding uncertainty,
electron-density, temperature, and attenuation gates so Saha, radiative
transfer, and shock-excitation support can move beyond proxy status.
