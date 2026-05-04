# Autopoietic n-Scalar Field

Status: HOLD / workbench projection
Authority: mathematical architecture draft; not canonical proof
Related: `docs/gcl/GCLCompleteSurface.md`, `docs/gcl/MassNumberGCLSubset.md`, `docs/wiki/NotationNomenclatureRegistry.md`

## Purpose

This document formalizes the field-engine interpretation of Genetic Coding Language.

The old hoxel / block / fixed `1024^4` concept is excised. The new object is an adaptive scalar field generated from 0D scalar seeds under finite-regime thermodynamic and topological gates.

```text
0D scalar seeds
  -> encoded genotype
  -> adaptive scalar field
  -> expressed phenotype
  -> audit gates
  -> projection/rendering
```

## Lineage: dynamic voxel editing, goxels, and MOF/microvoxel work

This model extends the dynamic voxel-world editing problem rather than rejecting it.

The motivating engineering problem is the familiar voxel-editing question:

```text
How do you support dynamic world edits without treating every tiny volume element as a permanent, expensive, independent block?
```

The MOF/microvoxel line answers that at a fine material/projection scale: it gives a way to represent localized detail, edits, and materialized surface fragments.

The missing middle unit is the **goxel**.

```text
voxel  = volume cell / sample slot
goxel  = geometric shape token / primitive
microvoxel = tiny materialized local detail/cache cell
```

A goxel is a geometric primitive or compact shape-description assembled into voxel-like editable structures. Instead of saying the world is made of fixed cubes, a goxel says that local editable volume can be expressed by shapes: planes, patches, signed-distance fragments, convex pieces, splines, capsules, fields, or other geometric tokens.

```text
goxel = geometry-first editable unit
```

A goxel may occupy, cut, fill, or approximate voxel-like regions, but it is not identical to a voxel.

The generalized chain is:

```text
dynamic voxel editing
  -> goxel geometric shape tokens
  -> microvoxel / MOF materialization
  -> sparse 0D scalar seeds
  -> adaptive scalar field
  -> residual-heavy regions materialize only when needed
```

In this architecture, voxels, goxels, and microvoxels have different roles:

```text
field ontology      = scalar seeds + regime + field equation + gates
goxel layer         = geometric shape-token assembly / edit grammar
microvoxel layer    = local cache / materialized detail / edit substrate
renderer layer      = mesh, raymarch, brickmap, atlas, or WebGPU projection
```

Therefore, the model keeps the practical strengths of dynamic voxel editing while avoiding the assumption that reality is fundamentally made of fixed voxels.

## Goxel definition

A goxel is a finite geometric token used to assemble editable, voxel-like structures without committing the ontology to uniform grid cells.

```ts
type Goxel = {
  goxel_id: string;
  chart_id: string;
  primitive:
    | "plane_patch"
    | "sdf_fragment"
    | "convex_cell"
    | "spline_patch"
    | "capsule"
    | "implicit_blob"
    | "meshlet"
    | "field_sample_packet";
  support_region: string;
  parameters: Record<string, unknown>;
  source_seeds: string[];
  boolean_role?: "fill" | "cut" | "blend" | "constraint" | "repair";
  residual_score?: number;
  mass_number_cost?: number;
  receipts: string[];
};
```

A goxel can be rasterized into voxels or refined into microvoxels, but the goxel itself is geometric.

```text
goxel -> voxel-like occupancy
goxel -> microvoxel refinement
goxel -> mesh / SDF / raymarch projection
goxel -> field repair patch
```

## Design intent: diversity without secret knowledge

The purpose of this model is to create a more diverse specification surface without assuming the author already possesses secret geometric knowledge.

The system does not require a hidden completed manifold, secret equation, or pre-known topology. It starts from declared 0D scalar seeds, declared regimes, declared kernels, and declared gates.

```text
known seed facts
  -> candidate field expression
  -> multiple admissible morphologies
  -> audit / closure / receipts
  -> selected projection
```

This means GCL can encode possible structures without pretending they are already known truths.

Allowed:

```text
candidate geometry
candidate topology
candidate field equation
candidate seed mutation
candidate projection
candidate repair path
```

Forbidden:

```text
assume hidden complete manifold
assume secret physical law
assume field expression proves source truth
assume visual phenotype proves genotype
assume generated morphology is automatically valid
```

The field equation is therefore an exploratory generator plus gate system, not an oracle.

## Canonical framing

GCL is Genetic Coding Language.

In this field model:

```text
GCL genotype  = 0D scalar seed code + constraints + mutation/repair rules
GCL phenotype = zero-crossing manifold expressed by the scalar field
```

The field is not a static container. It is an adaptive carrier that expresses geometry according to seed pressure, local regime, resource budgets, and admissibility constraints.

## Finite-regime axiom

All dimensions are regime-declared and finite for executable purposes.

```text
n is a finite positive integer inside the active compute regime.
```

Do not write `n = infinity` in executable GCL. If apparent infinite dimensionality appears, route it to `NaNMass`, `LimitBoundary`, or `ProjectionArtifact` until a finite surrogate or quotient closure is declared.

## Seed set

Let the active seed set be:

```text
S = { (s_i, psi_i, theta_i) } for i = 1,...,k
```

where:

```text
s_i      in R^n    seed coordinate
psi_i    in R      scalar perturbation strength
theta_i           optional seed parameters / type / regime metadata
k                 finite number of active seeds
```

A seed is 0D in the sense that it is a point-like source of scalar potential.

It is not a voxel. It is not a hoxel. It is not a stored block.

## Global scalar potential

The scalar field is:

```text
Phi : Omega x T -> R
```

where:

```text
Omega subset R^n   active finite domain / chart / local regime
T                  update index or time parameter
```

The seed-induced forcing term is:

```text
F_S(v) = sum_i psi_i * K_theta(v, s_i)
```

where `K_theta` is a regime-scoped geodesic or radial kernel.

## Recommended field equation

Use a finite-resource gradient-flow form rather than an unconstrained self-referential equation.

```text
partial_t Phi(v,t)
  = - delta E[Phi; S] / delta Phi(v,t)
```

with energy functional:

```text
E[Phi; S]
  = integral_Omega [
      alpha/2 * ||grad Phi||^2
    + beta/2  * |Delta Phi|^2
    + gamma   * V(Phi)
    + eta     * R_anti(Phi)
    - F_S(v) * Phi(v)
    ] dv
```

where:

```text
alpha       smoothness / membrane tension weight
beta        curvature penalty weight
gamma       potential / phase preference weight
eta         anti-music residual penalty weight
V(Phi)      local potential function
R_anti      anti-music residual density
F_S         seed forcing term
```

This gives a controlled morphogenesis equation:

```text
partial_t Phi
  = alpha * Delta Phi
    - beta * Delta^2 Phi
    - gamma * V'(Phi)
    - eta * dR_anti/dPhi
    + F_S
```

All terms are regime-scoped. No symbol is globally universal by default.

## Candidate diversity rule

A seed set may generate more than one admissible field expression.

Rather than choosing one morphology by assertion, GCL should preserve a finite candidate family:

```text
Candidates(S, R) = { Phi_1, Phi_2, ..., Phi_m }
```

where each `Phi_j` uses a declared kernel, energy functional, boundary condition, and regime.

A candidate survives only if it passes gates:

```text
Survives(Phi_j) iff
  finite_regime(Phi_j)
  and Regular(M_iso_j)
  and CB2(Phi_j) = 0
  and m_A(Phi_j; R) <= Budget_R
  and receipts are present or explicitly marked missing
```

This supports diversity without pretending all candidates are true.

## Surface / phenotype definition

The expressed manifold is the regular level set:

```text
M_iso(t) = { v in Omega : Phi(v,t) = iso and ||grad Phi(v,t)|| > epsilon_grad }
```

Usually `iso = 0`.

The non-vanishing gradient condition prevents ambiguous cloudy surfaces and makes the level set locally regular.

## Anti-music residual

Music is the predictable / harmonic part of the field.
Anti-music is the structured residual that cannot be explained by the harmonic component.

One admissible draft definition is:

```text
E_R(Phi) = integral_Omega || (I - H_R) Phi ||^2 dv
```

where:

```text
H_R = regime-scoped harmonic / interpolation / low-curvature projector
I   = identity operator
```

A curvature-based surrogate is:

```text
E_R_curv(Phi) = integral_Omega |Delta Phi|^2 dv
```

Interpretation:

```text
low E_R  -> smooth / harmonic / cheap to interpolate
high E_R -> structured residual / high curvature / must be audited or materialized
```

## Mass-number as metabolic cost

Mass-number in this model is a finite accounting score for the cost of maintaining expressed field detail.

```text
m_A(Phi; R)
  = w_R * E_R(Phi)
    + w_G * G_topo(Phi)
    + w_B * B_active(Phi)
    + w_C * C_route(Phi)
```

where:

```text
E_R       anti-music residual / curvature cost
G_topo    topological complexity estimate
B_active  active brick / tile / cache budget usage
C_route   routing or adapter cost
w_*       nonnegative regime weights
```

Mass-number is not distance.
Mass-number is not physical SI mass.
Mass-number may contribute to route cost only after admissibility closure.

## Goxel assembly rule

Goxels assemble into voxel-like editable structures without requiring every local detail to begin as a cell.

```text
field residual / edit request
  -> choose goxel primitive(s)
  -> assemble shape-token patch
  -> optionally rasterize to voxel occupancy
  -> optionally refine to microvoxel packet
  -> project to mesh/SDF/WebGPU renderer
```

A goxel patch may represent:

```text
terrain cut
surface repair
cavity fill
constraint boundary
smooth blend
collision audit region
field residual patch
```

A valid goxel patch must declare:

```text
support region
primitive type
parameter schema
source seeds or edit action
boolean role
budget/mass cost
projection target
receipts or missing-receipt status
```

## Microvoxel materialization rule

MOF/microvoxels enter only after the field says local detail must be materialized.

```text
if E_R(local) <= epsilon_R and edit_pressure(local) <= epsilon_edit:
  keep implicit / interpolate / evaluate on demand
else:
  allocate microvoxel materialization packet
```

A microvoxel packet should carry:

```ts
type MicrovoxelPacket = {
  packet_id: string;
  chart_id: string;
  support_region: string;
  source_seeds: string[];
  residual_score: number;
  mass_number_cost: number;
  materialization_reason:
    | "high_curvature"
    | "active_edit"
    | "collision_audit"
    | "render_cache"
    | "repair_patch";
  expiry_policy: "persistent" | "cache" | "atrophy_when_smooth";
};
```

This preserves the dynamic editing substrate without committing the ontology to permanent fixed cells.

## Inverse Ascent Gate

A proposed update `A : Phi -> Phi'` may ascend into the active/rendered state only if it passes the gate:

```text
AscentAllowed(A, Phi, Phi') iff
  m_A(Phi'; R) <= Budget_R
  and CB2(Phi') = 0
  and Regular(M_iso')
  and ReceiptsRequired(A) are present or explicitly waived by regime
```

where:

```text
Regular(M_iso') := for all v in M_iso', ||grad Phi'(v)|| > epsilon_grad
```

## Corrected hard boundary

Do not state:

```text
CB2(A) = 0 implies the manifold is fully viable.
```

That is too strong.

Use the corrected boundary:

```text
CB2(Phi) = 0 is necessary for topological admissibility under this gate.
```

Full viability is conjunctive:

```text
Viable_R(Phi) iff
  CB2(Phi) = 0
  and Regular(M_iso)
  and m_A(Phi; R) <= Budget_R
  and ClosureStatus(Phi) in {closed, quotiented, reviewed}
```

## Collision / CB2 interpretation

`CB2` is a collision or contradiction detector. It should be treated as a gate predicate, not a complete proof of manifold health.

Allowed interpretations:

```text
self-intersection candidate
non-manifold singularity candidate
contradictory scalar assignment
route collision
admissibility failure
```

Forbidden interpretation:

```text
CB2 = 0 proves all topology is correct.
```

## Rendering / materialization rule

The field may be evaluated continuously, but only residual-heavy regions need storage or materialization.

```text
if E_R(local) <= epsilon_R:
  interpolate/evaluate on demand
else:
  allocate active detail cache / brick / tile / sample packet
```

This replaces the fixed grid model.

There is no required `1024^4` atlas. Any atlas, cache, brickmap, goxel layer, microvoxel layer, or tile layer is a projection/runtime optimization, not the ontology.

## GCL genetic analogy

| GCL / biological term | Field interpretation |
|---|---|
| Genotype | 0D scalar seed set plus constraints |
| Codon | Typed seed/slot entry |
| Phenotype | Expressed level-set manifold |
| Mutation | Proposed seed/edit/update |
| Repair | Limit, quotient, finite surrogate, smoothing, goxel patch, or reparameterization |
| Metabolism | Mass-number / compute / memory cost |
| Homeostasis | Anti-music minimization and budget rebalancing |
| Natural selection | Inverse Ascent Gate |

## Update lifecycle

```text
1. User or process proposes seed mutation A.
2. Compute candidate forcing F_S'.
3. Generate a finite candidate family Candidates(S', R).
4. Evolve or solve each Phi_j under its declared field equation.
5. Extract regular level-set candidate M_iso_j.
6. Compute E_R, m_A, CB2, and Regularity.
7. If local geometric edit is needed, synthesize goxel patch candidates.
8. Apply Inverse Ascent Gate.
9. If pass: promote candidate to active projection/cache, goxel assembly, or microvoxel materialization with receipts.
10. If fail: HOLD, repair, simplify, quarantine, or route to NaNMass.
```

## Status boundary

This model is currently a workbench architecture.

It may guide code and simulation design. It does not yet prove physical realism, biological realism, or complete topological correctness.

Required future receipts:

```text
SchemaReceipt
SimulationTrace
CB2DefinitionReceipt
RegularLevelSetReceipt
BudgetAccountingReceipt
LeanTheorem targets for gate predicates
CandidateDiversityReceipt
GoxelAssemblyReceipt
MicrovoxelMaterializationReceipt
```
