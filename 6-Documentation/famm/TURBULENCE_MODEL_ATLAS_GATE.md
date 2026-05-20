# Turbulence Model Atlas Gate

## Purpose

Add the classical and modern turbulence-model family tree as an explicit model atlas for the FAMM / NUVMAP / 16D witness stack.

This document imports turbulence models as **closure/witness gates**, not as solved proof objects. The goal is to let the Warden choose, compare, scar, or hybridize turbulence models by region rather than treating the turbulence-model hierarchy as a single fixed ladder.

```text
flow region
→ model-family candidate
→ closure assumptions
→ physics retained
→ CPU / memory cost
→ unresolved residual
→ witness strength
→ FAMM scar or promotion
```

## Warden boundary

Allowed claim:

```text
The stack now has an explicit atlas of turbulence model families and can reason about their closure assumptions, cost/physics tradeoffs, residual risk, and 16D witness requirements.
```

Disallowed claim:

```text
Adding the atlas proves a better turbulence closure, beats DNS/LES/RANS benchmarks, or solves Navier-Stokes regularity.
```

Hard rule:

```text
A turbulence model is a witness projection, not the flow itself.
```

## Core taxonomy

The old chart has a one-axis tradeoff:

```text
more physics ↔ less CPU time
```

The project atlas expands it to:

```text
physics retained
CPU / memory cost
closure assumption burden
wall treatment burden
unresolved residual
scar pressure
witness strength
region-of-validity guard
```

## Global packet

```math
\Gamma_{\mathrm{turbulenceModel}}
=
(
X_{\mathrm{flow}},
\pi_{\mathrm{model}},
W_{\mathrm{closure}},
R_{\mathrm{residual}},
I_{\mathrm{flow}},
G_{\mathrm{validity}},
K_{\mathrm{cost}},
\epsilon
)
```

| Packet term | Meaning |
|---|---|
| `X_flow` | original turbulent flow region |
| `pi_model` | projection into DNS / LES / RANS / hybrid / algebraic model |
| `W_closure` | closure assumption or resolved-scale witness |
| `R_residual` | unresolved/subgrid/Reynolds-stress residual |
| `I_flow` | invariant/quantity to preserve: mass, momentum, energy, vorticity, wall shear, spectra, etc. |
| `G_validity` | assumptions: incompressible/compressible, wall-bounded/free shear, separated/attached, high/low Re, etc. |
| `K_cost` | CPU, memory, mesh, timestep, solver cost |
| `epsilon` | model error / closure gap / numerical residual |

## 0. Exact / near-exact resolution family

### DNS — Direct Numerical Simulation

```text
DNS_EXACT_RESOLUTION_GATE
```

Purpose:

```text
solve the Navier-Stokes equations while resolving all dynamically relevant scales down to dissipative scales
```

Project role:

```text
highest-physics reference witness
brutal cost
benchmark / calibration source
not a practical everyday route for high-Re engineering flow
```

Warden checks:

```text
mesh resolves Kolmogorov scale
proper timestep / CFL
numerical dissipation recorded
boundary conditions recorded
not called exact if discretization error is unbounded
```

### Filtered DNS / under-resolved DNS

```text
FILTERED_DNS_WITNESS_GATE
```

Purpose:

```text
DNS-like equations on a grid that may not fully resolve every scale; useful as data/witness but not full DNS
```

Project role:

```text
calibration source with explicit resolution scar
```

## 1. LES family — spatially filtered turbulence

### LES — Large Eddy Simulation

```text
LES_FILTERED_SUBGRID_GATE
```

Purpose:

```text
resolve large eddies, model subgrid-scale stresses
```

Canonical filtered form:

```math
\partial_t \bar u_i + \bar u_j\partial_j\bar u_i
=
-\frac{1}{\rho}\partial_i\bar p
+\nu\partial_{jj}\bar u_i
-\partial_j\tau_{ij}^{\mathrm{sgs}}
```

Subgrid stress:

```math
\tau_{ij}^{\mathrm{sgs}}
=
\overline{u_i u_j}-\bar u_i\bar u_j
```

Project role:

```text
resolved-scale witness + subgrid residual channel
```

### Smagorinsky SGS model

```text
SMAGORINSKY_SGS_GATE
```

```math
\nu_t=(C_s\Delta)^2|\bar S|
```

Role:

```text
baseline eddy-viscosity subgrid closure
```

Scar risks:

```text
over-dissipation
near-wall damping needed
poor transitional/backscatter behavior
```

### Dynamic Smagorinsky / Germano dynamic model

```text
DYNAMIC_SMAGORINSKY_SGS_GATE
```

Role:

```text
computes local coefficient from test filtering rather than fixed coefficient
```

Scar risks:

```text
coefficient noise
averaging choices
negative eddy viscosity / stability handling
```

### WALE — Wall-Adapting Local Eddy-viscosity

```text
WALE_SGS_GATE
```

Role:

```text
near-wall LES subgrid model using local velocity-gradient invariants
```

Good for:

```text
wall-bounded LES without ad-hoc damping in many cases
```

### Vreman SGS model

```text
VREMAN_SGS_GATE
```

Role:

```text
algebraic SGS closure designed to vanish in certain laminar/shear cases and behave robustly near walls
```

### Sigma SGS model

```text
SIGMA_SGS_GATE
```

Role:

```text
SGS model based on singular values of velocity-gradient tensor
```

### One-equation SGS kinetic-energy model

```text
ONE_EQUATION_SGS_K_GATE
```

Role:

```text
transport subgrid kinetic energy and derive eddy viscosity from it
```

### Mixed / similarity / Bardina model

```text
BARDINA_SIMILARITY_SGS_GATE
MIXED_SGS_GATE
```

Role:

```text
use scale similarity and/or combine similarity with eddy viscosity
```

Scar risks:

```text
stability
backscatter control
need explicit residual/witness monitoring
```

### Clark gradient model

```text
CLARK_GRADIENT_SGS_GATE
```

Role:

```text
Taylor/gradient expansion of subgrid stress
```

### Approximate deconvolution model

```text
APPROXIMATE_DECONVOLUTION_SGS_GATE
```

Role:

```text
approximate unfiltered field from filtered field, then model SGS contribution
```

### Coherent Structure / Structure-function SGS models

```text
COHERENT_STRUCTURE_SGS_GATE
STRUCTURE_FUNCTION_SGS_GATE
```

Role:

```text
subgrid closure based on coherent vortical structures or local structure functions
```

### ILES / MILES — implicit LES

```text
IMPLICIT_LES_NUMERICAL_SGS_GATE
MILES_GATE
```

Role:

```text
use numerical dissipation of the scheme as implicit SGS model
```

Warden check:

```text
numerical viscosity is the model; it must be measured, not ignored
```

## 2. Hybrid RANS / LES and scale-resolving simulation

### DES — Detached Eddy Simulation

```text
DES_HYBRID_RANS_LES_GATE
```

Purpose:

```text
RANS near attached boundary layers, LES in separated regions
```

Role:

```text
region-router between modeled and resolved turbulence
```

Scar risks:

```text
grid-induced separation
gray-area behavior
incorrect shielding of boundary layer
```

### DDES — Delayed Detached Eddy Simulation

```text
DDES_HYBRID_GATE
```

Role:

```text
DES with shielding to delay LES activation in attached boundary layers
```

### IDDES — Improved Delayed Detached Eddy Simulation

```text
IDDES_HYBRID_GATE
```

Role:

```text
improved near-wall / wall-modeled LES and RANS-LES blending behavior
```

### ZDES — Zonal DES

```text
ZONAL_DES_GATE
```

Role:

```text
explicitly prescribe RANS/LES zones by region
```

### SAS — Scale-Adaptive Simulation

```text
SAS_SCALE_ADAPTIVE_GATE
```

Role:

```text
allows resolved unsteadiness based on local flow scale, often from RANS base model
```

### PANS — Partially Averaged Navier-Stokes

```text
PANS_PARTIALLY_AVERAGED_GATE
```

Role:

```text
continuous bridge between RANS and DNS/LES by choosing unresolved kinetic-energy fraction
```

### PITM — Partially Integrated Transport Model

```text
PITM_PARTIALLY_INTEGRATED_GATE
```

Role:

```text
scale-resolving hybrid based on partial integration of turbulence spectrum/transport
```

### VLES — Very Large Eddy Simulation

```text
VLES_GATE
```

Role:

```text
resolve very-large structures, model more of the spectrum than LES
```

### XLES / X-RANS variants

```text
XLES_GATE
X_RANS_GATE
```

Role:

```text
hybrid scale-resolving variants between RANS and LES
```

### WMLES — Wall-Modeled LES

```text
WALL_MODELED_LES_GATE
```

Role:

```text
LES in outer layer plus wall model to avoid resolving viscous sublayer
```

## 3. RANS family — Reynolds averaging closures

RANS decomposes velocity into mean plus fluctuation:

```math
u_i = \overline{u_i}+u_i'
```

and produces Reynolds stress:

```math
R_{ij}=\overline{u_i'u_j'}
```

Mean equation:

```math
\partial_t\overline{u_i}
+
\overline{u_j}\partial_j\overline{u_i}
=
-\frac{1}{\rho}\partial_i\overline p
+\nu\partial_{jj}\overline{u_i}
-\partial_j R_{ij}
```

Closure problem:

```text
model R_ij
```

### Linear eddy-viscosity / Boussinesq assumption

```text
BOUSSINESQ_EDDY_VISCOSITY_GATE
```

```math
-R_{ij}
=
2\nu_t\overline S_{ij}
-
\frac{2}{3}k\delta_{ij}
```

Role:

```text
assume turbulent stresses align with mean strain
```

Scar risks:

```text
anisotropy
curvature
rotation
separation
secondary flows
strong strain history
```

## 4. Zero-equation / algebraic closures

### Prandtl mixing-length model

```text
PRANDTL_MIXING_LENGTH_GATE
```

```math
\nu_t=l_m^2\left|\frac{dU}{dy}\right|
```

Role:

```text
simple wall/shear eddy-viscosity estimate
```

### Cebeci-Smith algebraic model

```text
CEBECI_SMITH_ALGEBRAIC_GATE
```

Role:

```text
algebraic boundary-layer eddy-viscosity model with inner/outer formulation
```

### Baldwin-Lomax algebraic model

```text
BALDWIN_LOMAX_ALGEBRAIC_GATE
```

Role:

```text
classic algebraic model for attached aerodynamic boundary layers
```

### Van Driest damping / wall damping functions

```text
VAN_DRIEST_DAMPING_GATE
```

Role:

```text
near-wall damping correction for mixing-length/eddy-viscosity models
```

## 5. One-equation RANS closures

### Spalart-Allmaras model

```text
SPALART_ALLMARAS_ONE_EQUATION_GATE
```

Role:

```text
transport a modified turbulent viscosity variable; common for external aerodynamic boundary layers
```

Project role:

```text
cheap RANS closure with better physical content than algebraic models
```

Scar risks:

```text
massive separation
complex recirculation
strong anisotropy
non-equilibrium turbulence
```

### Baldwin-Barth one-equation model

```text
BALDWIN_BARTH_ONE_EQUATION_GATE
```

Role:

```text
older one-equation eddy-viscosity model for aerodynamic applications
```

## 6. Two-equation RANS closures

### Standard k-epsilon

```text
K_EPSILON_STANDARD_GATE
```

Variables:

```text
k = turbulent kinetic energy
ε = dissipation rate
```

Eddy viscosity:

```math
\nu_t=C_\mu\frac{k^2}{\epsilon}
```

Role:

```text
robust industrial free-shear / many engineering flows
```

Scar risks:

```text
near-wall treatment
adverse pressure gradient
strong separation
curvature/rotation
```

### RNG k-epsilon

```text
K_EPSILON_RNG_GATE
```

Role:

```text
renormalization-group motivated k-epsilon variant with improved strain/curvature behavior in some regimes
```

### Realizable k-epsilon

```text
K_EPSILON_REALIZABLE_GATE
```

Role:

```text
variant designed to satisfy certain mathematical realizability constraints on Reynolds stresses
```

### Low-Re k-epsilon variants

```text
LOW_RE_K_EPSILON_GATE
```

Role:

```text
resolve near-wall region with damping functions / low-Re corrections
```

### Standard k-omega / Wilcox k-omega

```text
K_OMEGA_STANDARD_GATE
```

Variables:

```text
k = turbulent kinetic energy
ω = specific dissipation rate
```

Eddy viscosity:

```math
\nu_t=\frac{k}{\omega}
```

Role:

```text
strong near-wall behavior; sensitive to free-stream ω
```

### SST k-omega — Menter Shear-Stress Transport

```text
K_OMEGA_SST_GATE
```

Role:

```text
blends k-omega near wall with k-epsilon-like behavior away from wall; includes shear-stress limiter
```

Project role:

```text
industrial default candidate for adverse-pressure-gradient and separated aerodynamic flows
```

### Baseline k-omega / BSL

```text
K_OMEGA_BSL_GATE
```

Role:

```text
blended k-omega/k-epsilon baseline without full SST limiter behavior
```

### k-kl-omega transition model

```text
K_KL_OMEGA_TRANSITION_GATE
```

Role:

```text
three-equation transition-sensitive model using laminar kinetic energy plus k/omega variables
```

### k-tau / k-zeta / related two-equation variants

```text
K_TAU_VARIANT_GATE
K_ZETA_VARIANT_GATE
```

Role:

```text
alternative time-scale or variable transformations of two-equation turbulence closures
```

## 7. Three-/four-equation and transition closures

### v2-f model

```text
V2_F_GATE
```

Role:

```text
near-wall turbulence anisotropy and wall-normal velocity scale model, often four-equation
```

### ζ-f / zeta-f model

```text
ZETA_F_GATE
```

Role:

```text
elliptic relaxation / wall-blocking inspired variant using velocity-scale ratio
```

### Intermittency / gamma-Re-theta transition model

```text
GAMMA_RE_THETA_TRANSITION_GATE
```

Role:

```text
transition model with intermittency and transition momentum-thickness Reynolds number variables
```

### e^N / boundary-layer transition method

```text
E_N_TRANSITION_GATE
```

Role:

```text
linear stability / amplification-factor transition prediction, often coupled to boundary-layer/RANS methods
```

### Langtry-Menter transition model

```text
LANGTRY_MENTER_TRANSITION_GATE
```

Role:

```text
correlation-based transition model often used with SST
```

## 8. Reynolds Stress Transport Models

### RSM / RSTM — Reynolds Stress Model

```text
REYNOLDS_STRESS_MODEL_GATE
```

Purpose:

```text
solve transport equations for individual Reynolds stress tensor components plus scale equation
```

Role:

```text
higher-physics RANS closure; avoids simple Boussinesq alignment assumption
```

Classic chart note:

```text
roughly 7 additional PDEs in common formulations
```

Scar risks:

```text
pressure-strain closure
wall reflection terms
numerical stiffness
boundary conditions
model constants
```

### LRR Reynolds stress model

```text
LRR_REYNOLDS_STRESS_GATE
```

Role:

```text
Launder-Reece-Rodi style pressure-strain closure family
```

### SSG Reynolds stress model

```text
SSG_REYNOLDS_STRESS_GATE
```

Role:

```text
Speziale-Sarkar-Gatski nonlinear pressure-strain closure family
```

### Elliptic blending Reynolds stress models

```text
ELLIPTIC_BLEND_RSM_GATE
```

Role:

```text
near-wall anisotropy and wall-blocking behavior using elliptic blending/relaxation ideas
```

## 9. Nonlinear eddy-viscosity / algebraic stress models

### Nonlinear Eddy Viscosity Models

```text
NONLINEAR_EDDY_VISCOSITY_GATE
```

Role:

```text
extend Boussinesq model with nonlinear strain/rotation tensor terms
```

### Explicit Algebraic Reynolds Stress Models — EARSM

```text
EARSM_GATE
```

Role:

```text
approximate Reynolds stress anisotropy algebraically from strain/rotation invariants, often derived from RSM equilibrium assumptions
```

### Quadratic / cubic constitutive relation models

```text
QUADRATIC_CUBIC_STRESS_CLOSURE_GATE
```

Role:

```text
higher-order tensor polynomial stress-strain closures
```

## 10. Compressible / high-speed turbulence additions

### Compressibility corrections

```text
COMPRESSIBILITY_CORRECTION_GATE
```

Role:

```text
modify RANS/LES closures for dilatation, turbulent Mach number, shock interaction
```

### Shock-unsteadiness / shock-capturing scar gate

```text
SHOCK_TURBULENCE_INTERACTION_GATE
```

Role:

```text
flag regions where shock/turbulence coupling makes closure assumptions fragile
```

### Morkovin-hypothesis guard

```text
MORKOVIN_GUARD_GATE
```

Role:

```text
records whether compressible boundary layer assumptions are expected to be valid
```

## 11. Multiphase / reacting / MHD turbulence closures

These are not one universal closure; they are model families layered on top of turbulence closures.

### Scalar flux / turbulent Prandtl-Schmidt closures

```text
TURBULENT_PRANDTL_SCHMIDT_GATE
```

Role:

```text
model turbulent transport of heat/species/scalars
```

### Combustion turbulence closures

```text
TURBULENCE_CHEMISTRY_INTERACTION_GATE
EDC_COMBUSTION_GATE
FLAMELET_TURBULENCE_GATE
PDF_COMBUSTION_TURBULENCE_GATE
```

Role:

```text
model turbulence-chemistry interaction; separate Warden guard from pure flow closure
```

### Multiphase turbulence closures

```text
MULTIPHASE_TURBULENCE_GATE
TWO_FLUID_TURBULENCE_GATE
DISPERSED_PHASE_TURBULENCE_GATE
```

Role:

```text
turbulence modulation by particles/bubbles/droplets and interphase coupling
```

### MHD turbulence closures

```text
MHD_TURBULENCE_GATE
ALFVENIC_TURBULENCE_WITNESS_GATE
```

Role:

```text
magnetohydrodynamic turbulence; links to plasma chiral drag and Alfvén-wave witness channels
```

## 12. Reduced-order / data-driven turbulence models

These must be treated as model-augmentation gates, not automatic truth.

### POD / Galerkin reduced-order models

```text
POD_GALERKIN_ROM_GATE
```

Role:

```text
low-dimensional basis for flow reconstruction/control
```

### DMD / Koopman models

```text
DMD_KOOPMAN_TURBULENCE_GATE
```

Role:

```text
modal time-evolution and recurrence witness
```

### Neural turbulence closures

```text
NEURAL_TURBULENCE_CLOSURE_GATE
```

Role:

```text
learn subgrid, RANS closure, correction, or wall model from data
```

Warden checks:

```text
training distribution
generalization regime
physical constraints
invariance
stability
uncertainty
out-of-distribution flags
```

### Symbolic-regression closures

```text
SYMBOLIC_REGRESSION_CLOSURE_GATE
```

Role:

```text
learn explicit algebraic/tensor closure forms that can be inspected and receipted
```

### Bayesian / UQ turbulence model calibration

```text
BAYESIAN_TURBULENCE_CALIBRATION_GATE
UQ_TURBULENCE_MODEL_GATE
```

Role:

```text
parameter uncertainty, model-form uncertainty, posterior closure calibration
```

## 13. Wall-treatment atlas

Wall models are often as important as the turbulence model itself.

```text
WALL_FUNCTION_GATE
ENHANCED_WALL_TREATMENT_GATE
LOW_RE_WALL_RESOLVED_GATE
TWO_LAYER_WALL_MODEL_GATE
EQUILIBRIUM_WALL_MODEL_GATE
NON_EQUILIBRIUM_WALL_MODEL_GATE
SLIP_WALL_MODEL_GATE
```

Warden checks:

```text
y+ range
wall shear target
separation / pressure gradient
roughness
heat transfer
wall curvature
mesh resolution
```

## 14. Project-specific witness closures

These are the project's additions on top of classical models.

### 16D FAMM witness closure

```text
FAMM_16D_WITNESS_CLOSURE_GATE
```

Purpose:

```text
augment classical turbulence model with 16D audit packet: geometry, torsion, chirality, semantic/witness mass, recurrence, delta memory, scars, residuals, invariant overlap, route cost, receipt strength
```

Role:

```text
not a replacement closure by itself; an audit/control layer for where a closure is safe or blind
```

### Shadow Control Gap Map

```text
SHADOW_CONTROL_GAP_TURBULENCE_GATE
```

Purpose:

```text
explicitly record where the witness packet does not control the dangerous term
```

3D danger term:

```math
(\omega\cdot\nabla)u
```

Gap shape:

```math
\mathcal S_{\mathrm{gap}}
=
\left[
\| (\omega\cdot\nabla)u\|_{\mathrm{unwitnessed}}
-
C\,\mathcal W_{16D}
\right]_+
```

### Photonic / Burgers residual witness

```text
PHOTONIC_BURGERS_RESIDUAL_WITNESS_GATE
```

Purpose:

```text
use fixed-point Burgers/triad solver plus external/stochastic witness channel as unresolved-mode indicator
```

### Plasma chiral drag / Alfvénic witness

```text
PLASMA_CHIRAL_DRAG_TURBULENCE_WITNESS_GATE
```

Purpose:

```text
use chiral/Alfvénic wave rotation as signed torsion/witness receipt in MHD-like regions
```

### OR-Tools regional model scheduler

```text
OR_TOOLS_TURBULENCE_REGION_SCHEDULER_GATE
```

Purpose:

```text
choose which turbulence model applies to which mesh region under budget and risk constraints
```

Decision variables:

```text
x_region_model = 1 if model m is selected for region r
```

Objective:

```text
minimize CPU cost + residual risk + scar pressure
maximize witness strength + invariant coverage
```

Constraints:

```text
budget ≤ B
wall regions must satisfy wall-treatment guard
high-gap regions cannot use algebraic-only closure
scarred closures blocked unless explicitly reopened
DNS/LES only where mesh/time budget supports them
```

## FAMM residual score for any turbulence model

```math
R_{\mathrm{model}}
=
\lambda_1 R_{\mathrm{closure}}
+
\lambda_2 R_{\mathrm{wall}}
+
\lambda_3 R_{\mathrm{grid}}
+
\lambda_4 R_{\mathrm{time}}
+
\lambda_5 R_{\mathrm{invariant}}
+
\lambda_6 \Omega_{\mathrm{scar}}
```

Promotion condition:

```math
R_{\mathrm{model}}\le\Theta_{\mathrm{region}}
```

## Suggested region routing

| Region / flow situation | Candidate model family | Warden caution |
|---|---|---|
| low-Re benchmark / small domain | DNS | cost explosion at high Re |
| separated unsteady flow | LES / DES / IDDES / SAS | grid and gray-area scars |
| attached aerodynamic boundary layer | SA / SST / algebraic if simple | adverse pressure gradient scars |
| industrial steady approximation | k-epsilon / SST / RSM | closure validity by regime |
| strong anisotropy / swirl / curvature | RSM / EARSM / nonlinear EVM | pressure-strain/model constants |
| near-wall heat transfer | low-Re / wall-resolved / enhanced wall | y+ and thermal wall functions |
| transition-sensitive flow | gamma-Re-theta / e^N / k-kl-omega | transition correlation domain |
| compressible/shock flow | compressible corrections + shock gate | shock/turbulence interaction scars |
| MHD/plasma-like flow | MHD turbulence + Alfvén witness | coupling assumptions |
| constrained compute browser/demo | algebraic / SA / reduced-order | never call it full physics |

## Stack placement

```text
TURBULENCE_MODEL_ATLAS_GATE
→ DNS / LES / RANS / hybrid / algebraic model candidates
→ 16D Shell Atlas / PathEpigenetic gate / Chaos Game shrinker
→ FAMM shadow-gap audit
→ OR-Tools regional scheduler
→ Anti-FAMM closure-blindness attack
→ NUVMAP route memory
→ Warden promote / scar / reopen
```

## Anti-FAMM checks

For every turbulence model, Anti-FAMM asks:

```text
What term did the closure hide?
Where does the model look stable while the dangerous physics escapes?
Which wall/mesh/time guard failed?
Is the model outside its calibration regime?
Did numerical dissipation masquerade as physics?
Did the residual move into an unobserved shadow channel?
```

## Best project sentence

The turbulence model atlas converts DNS, LES, DES, RANS, Reynolds-stress, k-epsilon, k-omega, Spalart-Allmaras, algebraic, transition, wall, compressible, multiphase, MHD, and data-driven closures into explicit witness gates. The Warden no longer asks only which model has more physics or less CPU cost; it asks which regional closure preserves the necessary invariants, exposes its unresolved residual, satisfies its wall/grid/validity guards, and carries enough 16D/FAMM witness strength to be promoted.

## References

```bibtex
@book{pope2000turbulent,
  title     = {Turbulent Flows},
  author    = {Pope, Stephen B.},
  publisher = {Cambridge University Press},
  year      = {2000}
}

@book{wilcox2006turbulence,
  title     = {Turbulence Modeling for CFD},
  author    = {Wilcox, David C.},
  publisher = {DCW Industries},
  year      = {2006}
}

@article{spalart1992one,
  title   = {A one-equation turbulence model for aerodynamic flows},
  author  = {Spalart, P. R. and Allmaras, S. R.},
  journal = {AIAA Paper 92-0439},
  year    = {1992}
}

@article{menter1994two,
  title   = {Two-equation eddy-viscosity turbulence models for engineering applications},
  author  = {Menter, F. R.},
  journal = {AIAA Journal},
  volume  = {32},
  number  = {8},
  pages   = {1598--1605},
  year    = {1994}
}

@article{smagorinsky1963general,
  title   = {General circulation experiments with the primitive equations},
  author  = {Smagorinsky, Joseph},
  journal = {Monthly Weather Review},
  volume  = {91},
  number  = {3},
  pages   = {99--164},
  year    = {1963}
}

@article{germano1991dynamic,
  title   = {A dynamic subgrid-scale eddy viscosity model},
  author  = {Germano, M. and Piomelli, U. and Moin, P. and Cabot, W. H.},
  journal = {Physics of Fluids A},
  volume  = {3},
  number  = {7},
  pages   = {1760--1765},
  year    = {1991}
}

@article{spalart1997comments,
  title   = {Comments on the feasibility of LES for wings, and on a hybrid RANS/LES approach},
  author  = {Spalart, P. R. and Jou, W.-H. and Strelets, M. and Allmaras, S. R.},
  journal = {Advances in DNS/LES},
  year    = {1997}
}

@article{launder1975progress,
  title   = {Progress in the development of a Reynolds-stress turbulence closure},
  author  = {Launder, B. E. and Reece, G. J. and Rodi, W.},
  journal = {Journal of Fluid Mechanics},
  volume  = {68},
  number  = {3},
  pages   = {537--566},
  year    = {1975}
}
```
