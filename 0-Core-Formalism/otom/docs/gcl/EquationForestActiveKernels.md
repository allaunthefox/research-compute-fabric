# Equation Forest: Active Kernel Registry

Status: HOLD / workbench projection
Authority: internal kernel registry; not external proof
Related: `docs/gcl/ForestPathGoxelModel.md`, `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/GoxelCADFluidBridge.md`, `docs/gcl/SidonMatrixGoxelModel.md`, `docs/wiki/NotationNomenclatureRegistry.md`

## Purpose

This document registers the 15 active kernels in the Equation Forest.

The Equation Forest is the active equation/kernel layer that lets Goxels, Sidon matrices, CAD/fluid simulators, signal systems, thermodynamic gates, and information-theoretic audit rules reference shared mathematical forms without duplicating or drifting names.

```text
Equation Forest
  -> active kernels
  -> typed domains
  -> runtime roles
  -> audit boundaries
  -> receipts / Lean targets
```

## Boundary

The word `canonical` in this registry means:

```text
canonical inside the current Sovereign / OTOM workbench registry
```

It does not automatically mean:

```text
externally proven
Lean-verified
physically validated
empirically measured
```

Each kernel still needs claim state, authority scope, and receipts.

## Kernel type

```ts
type EquationKernel = {
  kernel_id: string;
  domain_class:
    | "PDE"
    | "GR"
    | "SNN"
    | "TOPOLOGY"
    | "ENCODING"
    | "SIGNAL"
    | "STOCHASTIC"
    | "PHYSICS"
    | "MATH"
    | "ENERGY"
    | "THERMODYNAMICS"
    | "INFORMATION";
  display_equation: string;
  variables: string[];
  role: string;
  claim_state: "U_scope" | "HOLD" | "V_scope" | "REVIEWED" | "CANONICAL_LEAN" | "QUARANTINE";
  authority_scope:
    | "workbench_projection"
    | "simulation_only"
    | "receipt_backed"
    | "canonical_lean"
    | "external_source"
    | "safety_policy";
  allowed_runtimes: string[];
  blocked_usages: string[];
  receipt_refs: string[];
};
```

## The 15 active kernels

| # | Kernel ID | Class | Equation | Registry role |
|---:|---|---|---|---|
| 1 | `Burgers_Inviscid` | PDE | `u_t + u*u_x = 0` | shock / transport / nonlinear steepening kernel |
| 2 | `Burgers_Viscous` | PDE | `u_t + u*u_x = nu * u_xx` | transport with diffusion / viscosity / smoothing kernel |
| 3 | `Planet_Nine_Manifold` | GR | `G_uv = 8*pi*T_uv + Lambda*g_uv` | curvature/stress-energy manifold kernel |
| 4 | `PIST_Neural_Topology` | SNN | `S(t) = sum(w_i * h_i(t))` | spiking/neural topology accumulation kernel |
| 5 | `RGFlow_Admissibility` | TOPOLOGY | `Gamma(g) = torsion(g) + curvature(g)` | lawfulness / scale-stability / admissibility kernel |
| 6 | `Genome18_Address` | ENCODING | `addr = sum(8^i * bin_i)` | hachimoji/genomic address kernel |
| 7 | `S3C_Codec` | SIGNAL | `phi_sw = pulse_intensity / stability` | pulse/stability signal codec kernel |
| 8 | `NII_Surprise` | STOCHASTIC | `n_t = o_t - p_t` | prediction residual / novelty / surprise kernel |
| 9 | `Standard_Model_Simplified` | PHYSICS | `L = -1/4 F_uv F^uv + i psi_bar D psi` | simplified field/interactions Lagrangian kernel |
| 10 | `Riemann_Zeta_Critical` | MATH | `zeta(1/2 + it) = 0` | critical-line / analytic-number-theory kernel |
| 11 | `Landauer_Bound` | ENERGY | `E >= k * T * ln(2)` | bit erasure / thermodynamic lower-bound kernel |
| 12 | `Carnot_Efficiency` | THERMODYNAMICS | `eta = 1 - Tc/Th` | heat-engine efficiency boundary kernel |
| 13 | `Shannon_Entropy` | INFORMATION | `H = -sum(p_i * log(p_i))` | information uncertainty / compression kernel |
| 14 | `Bekenstein_Bound` | PHYSICS | `S <= 2*pi*k*R*E / (hbar*c)` | finite entropy/information bound kernel |
| 15 | `Navier_Stokes_Incompressible` | PDE | `u_t + (u.grad)u = -grad(p) + nu*laplacian(u)` | incompressible fluid dynamics kernel |

## Runtime clustering

### Fluid / field dynamics cluster

```text
Burgers_Inviscid
Burgers_Viscous
Navier_Stokes_Incompressible
```

Use for:

```text
fluid simulator
field residual flow
goxel boundary flow
shock/smoothing experiments
transport of scalar intent
```

Boundary:

```text
fluid simulation success != physical proof
stable PDE integration != theorem
```

### Geometry / manifold / topology cluster

```text
Planet_Nine_Manifold
RGFlow_Admissibility
Riemann_Zeta_Critical
```

Use for:

```text
curvature and torsion checks
manifold admissibility
critical-line / criticality metaphors
lawfulness filters
```

Boundary:

```text
metaphoric criticality != RH proof
GR-shaped equation != validated cosmology
```

### Neural / stochastic / signal cluster

```text
PIST_Neural_Topology
NII_Surprise
S3C_Codec
```

Use for:

```text
spiking/neural topology
surprise residuals
signal/noise discrimination
steganographic/SETI-like protocols
codec pulse stability
```

Boundary:

```text
residual != source truth
signal-looking pattern != verified signal
```

### Encoding / genetic-code cluster

```text
Genome18_Address
```

Use for:

```text
GCL / Genetic Coding Language
hachimoji / 8-symbol address spaces
codon-like expansion slots
seed indexing
```

Boundary:

```text
addressability != biological proof
encoding capacity != semantic truth
```

### Thermodynamic / information bound cluster

```text
Landauer_Bound
Carnot_Efficiency
Shannon_Entropy
Bekenstein_Bound
```

Use for:

```text
finite-regime rules
NaNMass boundary
compression accounting
energy/information budget constraints
claim against raw infinity-as-mass
```

Boundary:

```text
bound analogy != measured SI system
information bound != automatic physical implementation
```

### Physics / field-theory cluster

```text
Standard_Model_Simplified
Bekenstein_Bound
Planet_Nine_Manifold
```

Use for:

```text
field-theoretic notation
physics-inspired kernels
energy/entropy boundaries
manifold stress-energy analogies
```

Boundary:

```text
simplified Lagrangian != full Standard Model
physics-shaped kernel != experimental validation
```

## How this slots into Goxels

A Goxel may reference one or more Equation Forest kernels as its local field behavior.

```text
Goxel G
  -> local potential Phi_G
  -> active kernel set K_G
  -> runtime phenotype
  -> audit gates
```

Example:

```yaml
goxel_id: goxel_fluid_patch_001
local_potential: Phi_G
active_kernels:
  - Burgers_Viscous
  - Navier_Stokes_Incompressible
  - Shannon_Entropy
  - Landauer_Bound
claim_state: HOLD
authority_scope: simulation_only
```

## How this slots into CAD/fluid simulators

CAD use:

```text
RGFlow_Admissibility
Bekenstein_Bound
Shannon_Entropy
```

for checking:

```text
geometric complexity
finite representation cost
constraint admissibility
projection artifacts
```

Fluid use:

```text
Burgers_Inviscid
Burgers_Viscous
Navier_Stokes_Incompressible
Landauer_Bound
Shannon_Entropy
```

for checking:

```text
flow evolution
shock/smoothing behavior
solver cost
entropy/residual change
```

## How this slots into Sidon matrices

The Sidon matrix can include kernel-specific compatibility checks.

```text
S_R[i,j,kernel] = KernelCompatibility_R(G_i, G_j, kernel)
```

Examples:

```text
Burgers_Viscous:
  do adjacent Goxel potentials smooth without excessive residual?

RGFlow_Admissibility:
  does the pair remain lawfully stable under coarse-graining?

Shannon_Entropy:
  does the relation compress or expand uncertainty?

Landauer_Bound:
  does the edit imply finite erasure/work accounting?
```

## How this slots into the Forest Path model

Paths can be typed by active kernel family.

```text
PDEPath
  path whose transitions are governed by PDE kernels

ThermoPath
  path whose transitions are governed by finite energy/information bounds

SignalPath
  path whose transitions are governed by signal/surprise kernels

TopologyPath
  path whose transitions are governed by admissibility/curvature/torsion kernels
```

A path through the Equation Forest must declare:

```text
start kernel
end kernel
transition reason
shared variables or adapter
claim state
authority scope
receipts
```

## Kernel-to-kernel transition map

Initial useful transitions:

```text
Burgers_Viscous -> Navier_Stokes_Incompressible
  viscosity/smoothing kernel lifts into fluid solver kernel

Navier_Stokes_Incompressible -> GoxelCADFluidBridge
  fluid equation drives Goxel boundary behavior

RGFlow_Admissibility -> SidonMatrixGoxelModel
  topology kernel audits compatibility matrix lawfulness

Shannon_Entropy -> S3C_Codec
  entropy kernel informs codec stability/pulse structure

Landauer_Bound -> NaNMass / finite-regime rule
  thermodynamic bound blocks raw infinity-as-mass

Genome18_Address -> GCLCompleteSurface
  encoding kernel supports Genetic Coding Language slots/codons

NII_Surprise -> Signal-GCL / SETI protocol
  surprise residual becomes signal/noise audit input
```

## Validator requirements

Every Equation Forest kernel must declare:

```text
kernel_id
domain_class
display_equation
variables
claim_state
authority_scope
allowed_runtimes
blocked_usages
receipt_refs
```

If any are missing, the kernel remains `HOLD`.

## Immediate implementation target

Create a machine-readable mirror:

```text
registry/equation_forest_kernels.json
```

Suggested object:

```json
{
  "kernel_id": "Burgers_Viscous",
  "domain_class": "PDE",
  "display_equation": "u_t + u*u_x = nu * u_xx",
  "variables": ["u", "t", "x", "nu"],
  "claim_state": "HOLD",
  "authority_scope": "workbench_projection",
  "allowed_runtimes": ["fluid_sim", "goxel_field", "threejs_projection"],
  "blocked_usages": ["do not claim physical proof from simulation alone"],
  "receipt_refs": []
}
```

## Lean targets

Initial Lean target should formalize registry typing first, not all equations.

```lean
namespace OTOM.EquationForest

inductive KernelClass
  | pde
  | gr
  | snn
  | topology
  | encoding
  | signal
  | stochastic
  | physics
  | math
  | energy
  | thermodynamics
  | information

structure EquationKernel where
  id : String
  class : KernelClass
  display : String
  claimState : String
  authorityScope : String

end OTOM.EquationForest
```

Full mathematical formalization comes later per kernel.

## Canonical warning

```text
Equation Forest kernel != theorem
canonical registry entry != external proof
simulation kernel != physical validation
physics-shaped equation != measured physics
beautiful equation path != valid derivation
```

## Operating sentence

```text
The Equation Forest is the active kernel registry that lets every Goxel, path, Sidon relation, CAD feature, fluid region, and signal protocol declare which mathematical engine it is using and what audit gates still block promotion.
```
