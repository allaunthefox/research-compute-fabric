# Shockwave Eigenvalue Comparison

**Date:** 2026-05-09

**Status:** `EIGEN_GAP_AUDIT`

**Claim boundary:** this note checks the external stellar shock / CIGaRS
equation layer against the repo's current eigenvalue surfaces. It does not
claim astrophysical validation, cosmological validation, or a new physical
spectrum. It records where the current basis already has signal, and where it
has a visible gap.

## External Equation Layer

The CIGaRS paper is not a shock-hydrodynamics paper. Its useful contribution to
this stack is the joint latent forward-model pattern:

```text
host galaxy state + supernova occurrence + dust + selection + cosmology
  -> simulated observation
  -> simulation-based inference
```

The concrete equations that matter for the stack are:

```text
SFH^h = [SFH^{h,j}]_{j=1..7}
sum_j SFH^{h,j} = M_*^h

DTD(t_*) = A * (t_* / Gyr)^b * M_sun^-1 * yr^-1

<N_SN^{h,j}> =
  T / (1 + z^h) * SFH^{h,j} * DTD(t_*^{h,j})

N_SN^{h,j} ~ Poisson(<N_SN^{h,j}>)
```

Sources:

- Phys.org summary: `https://phys.org/news/2026-05-universe-sharpen-cosmic-expansion-dark.html`
- Nature Astronomy CIGaRS paper: `https://doi.org/10.1038/s41550-026-02842-5`

The stellar shockwave layer is different. It gives the physical bow/front
equations that can sharpen the local shock model:

```text
R_s(t) = xi * (E * t^2 / rho_0)^(1/5)
v_s(t) = (2/5) * R_s(t) / t

rho_1 * u_1 = rho_2 * u_2
P_1 + rho_1 * u_1^2 = P_2 + rho_2 * u_2^2
h_1 + u_1^2 / 2 = h_2 + u_2^2 / 2

tau ~= c / v_s
t_diff ~= (delta R)^2 / (c * l)
t_dyn ~= delta R / D_s
breakout when t_diff ~= t_dyn
```

Shock-breakout source:

- MNRAS, "Coupling of matter and radiation at supernova shock breakout":
  `https://doi.org/10.1093/mnras/sts577`

## Current Repo Eigen Surface

The current physics eigen map records these relevant clusters:

| Layer | Repo surface | Eigenvalue | Strength | Local meaning |
|---|---:|---:|---:|---|
| Radiation / absorption | Cluster 1: Electromagnetism & Circuits | `0.968750` | `0.176777` | Beer-Lambert, EM wave, Poynting layer |
| Diffusion / material transport | Cluster 2: Condensed Matter & Superconductivity | `0.969697` | `0.174078` | Einstein diffusion relation |
| Radiation spectrum | Cluster 3: Quantum Mechanics & Particle Physics | `0.970588` | `0.171499` | Planck / radiation-law layer |
| Acoustic impedance / material boundary | Cluster 4: Materials Science & Engineering | `0.992063` | `0.089087` | Klemens acoustic mismatch |
| Local stack shock alignment | Cluster 5: Cognitive & Semantic Systems | `0.998464` | `0.039193` | Shockwave alignment / relaxation |
| Classical hydrodynamic shock laws | Detonics & Shock Physics entries | current cluster entry | `0.000000` | ZND, Taylor-Sedov, Rankine-Hugoniot, CJ, Mie-Gruneisen are present but not active |

Local evidence:

- `3-Mathematical-Models/physics_eqs_eigenvector_mapped.md`
- `3-Mathematical-Models/eigenvector_tsm/eigenvector_hyperfluid_150_steps.json`
- `0-Core-Formalism/otom/formal/lean/SidonAudit/ShockBurgersCoupling.lean`
- `0-Core-Formalism/otom/formal/lean/SidonAudit/ShockwaveAlignmentRelaxation.lean`
- `shared-data/network_topology_database.json`

## Result

The external shock equations do not contradict the current eigenvalues. They
expose a missing physical-shock axis.

What the stack already has:

```text
shock as local alignment / discharge / relaxation
shock as discrete Burgers-style flux / dissipation
shock as rain-impulse / statolith threshold gate
```

What the stack does not yet strongly encode:

```text
shock as radiation-hydrodynamic breakout
shock as Rankine-Hugoniot conservation surface
shock as Sedov-Taylor self-similar expansion
shock as optical-depth release gate
```

So the correct decision is:

```text
HOLD_ADD_PHYSICAL_SHOCK_EIGEN_AXIS
```

## Proposed Sharpened Axis

Add a physical shock eigen lane with five required components:

```text
front propagation:
  R_s(t), v_s(t)

jump conservation:
  mass, momentum, enthalpy Rankine-Hugoniot receipts

radiation escape:
  tau ~= c / v_s

diffusion release:
  t_diff ~= t_dyn

host / context prior:
  CIGaRS-style latent context and systematic-residual lane
```

Minimum gate:

```text
if missing Rankine-Hugoniot receipt:
  HOLD_PHYSICAL_SHOCK_AXIS
elif tau > c / v_s and t_diff > t_dyn:
  HOLD_BURIED_SHOCK
elif abs(tau - c / v_s) <= epsilon_tau
     and abs(t_diff - t_dyn) <= epsilon_t:
  ADMIT_BREAKOUT_GATE
else:
  HOLD_RESIDUAL_CONTEXT
```

## Interpretation For The Drawn Shock-Bow Map

Your 2D shock-bow diagram can be treated as a compressed projection of this
new axis:

```text
curved bow fronts     -> shock-front geometry
square / center gate  -> local conservation cell
colored crossing arcs -> competing diffusion / radiation / material modes
12 / 28 bands         -> occupancy or angular bins for survivor routes
```

That means the drawing is strongest as a routing receipt, not as a literal
stellar surface model. The physical lane adds the equations needed for the
receipt to stop being only geometric and become testable against shock-front
physics.

## Next Work

1. Add `PhysicalShockEigenAxis` as a receipt surface.
2. Build fixture cases for buried shock, breakout gate, and missing conservation.
3. Add the public underwater shock benchmark as a non-operational historical
   modeling lane: shock-front arrival, attenuation, bubble-pulse eigenmode,
   boundary reflection, and residual.
4. Re-run the eigen remapper and require the Detonics & Shock Physics entries
   to move from strength `0.000000` to a declared nonzero support lane before
   promotion.
