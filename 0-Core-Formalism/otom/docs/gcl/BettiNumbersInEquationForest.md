# Betti Numbers in the Equation Forest

Status: HOLD / workbench projection
Authority: topology/audit bridge spec; not canonical proof
Related: `docs/gcl/EquationForestActiveKernels.md`, `docs/gcl/ForestPathGoxelModel.md`, `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/SidonMatrixGoxelModel.md`, `docs/gcl/GoxelCADFluidBridge.md`

## Purpose

This document answers where Betti numbers live in the Equation Forest.

Betti numbers are the topology counters for the forest, the Goxel field, the Sidon matrix, and the CAD/fluid projections.

They count structural holes in a declared space.

```text
Betti numbers
  -> connected components
  -> loops / independent cycles
  -> voids / cavities
  -> higher-dimensional holes
```

They do not replace the active kernels. They audit the topology produced by the kernels.

## Core definition

For a topological space or filtered complex `X`, the kth Betti number is:

```text
beta_k(X) = rank H_k(X)
```

where:

```text
H_k(X) = kth homology group of X
beta_0 = number of connected components
beta_1 = number of independent loops / tunnels
beta_2 = number of enclosed voids / cavities
beta_k = number of k-dimensional holes
```

## Plain-language placement

In the forest metaphor:

```text
beta_0 counts clearings / disconnected forest regions
beta_1 counts loops in the trail system
beta_2 counts enclosed voids / caves / trapped chambers
higher beta_k counts higher-dimensional holes in the N-space forest
```

In the Goxel model:

```text
beta_0 counts disconnected Goxel bodies
beta_1 counts tunnels through Goxel assemblies
beta_2 counts enclosed cavities inside Goxel volumes
beta_k counts higher-dimensional voids in projected or native N-space domains
```

## Where they sit architecturally

```text
Equation Forest kernels
  -> generate fields / paths / domains / relations

Goxel / Sidon / CAD / Fluid runtime
  -> materializes candidate structure

Betti audit layer
  -> counts holes and connectivity

OTOM gates
  -> decide whether topology is admissible, held, repaired, or quarantined
```

So the Betti layer is a topology receipt layer.

## Betti numbers are not kernels

The 15 active kernels include PDE, GR, signal, thermodynamic, information, and encoding forms.

Betti numbers are not another PDE kernel. They are a measurement over the shape of the result.

```text
Burgers / Navier-Stokes
  -> evolve or transport field structure

RGFlow_Admissibility
  -> checks torsion/curvature/lawfulness

BettiAudit
  -> checks whether the resulting topology has expected components, loops, cavities, and higher holes
```

## Proposed registry entry

```yaml
kernel_id: BettiAudit
class: TOPOLOGY_AUDIT
formula: beta_k(X) = rank H_k(X)
role: hole-count and connectivity audit over Goxel fields, Sidon matrices, forest paths, CAD solids, and fluid domains
claim_state: HOLD
authority_scope: workbench_projection
allowed_runtimes:
  - goxel_field
  - forest_path
  - sidon_matrix
  - cad_bridge
  - fluid_sim
  - threejs_projection
blocked_usages:
  - Betti counts do not prove physical truth.
  - Betti stability does not prove semantic validity.
  - Projection Betti numbers may differ from native N-space Betti numbers.
receipt_refs: []
```

## Betti vector

Use a finite Betti vector for each audited domain:

```text
B(X) = (beta_0, beta_1, beta_2, ..., beta_d)
```

where `d` is finite and regime-declared.

No infinite Betti vector in executable GCL. If the required dimension is unbounded, route to:

```text
NaNMass
LimitBoundary
ProjectionArtifact
RegimeMismatch
```

## Forest path use

For a forest path complex `F_R`, Betti numbers answer:

```text
How many disconnected reasoning regions exist?
How many independent loops are in the path system?
Are there enclosed ambiguous voids?
Did a repair create or destroy a hole?
Did a projection make a fake loop?
```

Example:

```text
B(F_R) = (1, 3, 0)
```

means:

```text
one connected forest
three independent loops
no enclosed 2D cavities detected in the selected complex
```

## Goxel use

For a Goxel assembly:

```text
G_total = union_i G_i
```

Audit:

```text
B(G_total) = (beta_0, beta_1, beta_2, ...)
```

This tells whether fusion/repulsion changed topology.

Example gate:

```text
FusionAllowed_R(G_A, G_B) only if
  BettiChange_R(G_A union G_B) is allowed
```

where:

```text
BettiChange_R = B(after) - B(before)
```

## Sidon matrix use

The Sidon matrix gives pairwise compatibility.

Betti numbers give global topology.

```text
Sidon matrix:
  Are pairwise relations compatible?

Betti audit:
  Did the whole relation complex create loops, voids, or disconnected components?
```

This catches failures that pairwise checks can miss.

```text
Pairwise OK
  but global beta_1 increases unexpectedly
  -> hidden loop / path ambiguity / closure debt
```

## CAD use

For CAD solids:

```text
beta_0 = number of disconnected solid bodies
beta_1 = number of handles/tunnels
beta_2 = number of enclosed cavities
```

CAD bridge checks:

```text
expected Betti vector
  vs
actual Betti vector after export/boolean/repair
```

Useful failures:

```text
boolean operation accidentally creates a tunnel
repair closes intended hole
projection creates fake cavity
mesh export changes connected components
```

## Fluid use

For fluid domains, Betti numbers describe accessible flow topology.

```text
beta_0 = disconnected fluid regions
beta_1 = circulation loops / tunnels around obstacles
beta_2 = enclosed trapped voids / bubbles / cavities
```

This helps audit:

```text
boundary conditions
obstacle topology
vorticity traps
source/sink accessibility
flow-domain connectivity
```

## Three.js use

Three.js should expose Betti overlays as visualization hints, not proof.

Renderable overlay fields:

```ts
type BettiOverlay = {
  source_domain_id: string;
  betti_vector: number[];
  filtration_value?: number;
  persistence?: number[];
  native_space: string;
  projection_space: string;
  audit_state: "raw" | "held" | "audited" | "closed" | "quarantined";
  receipt_refs: string[];
};
```

Visual rule:

```text
display beta changes when a Goxel fuses, repels, splits, or projects
mark projection-only Betti counts clearly
never let the render itself promote topology claims
```

## Persistent homology slot

A single Betti vector at one scale may be fragile.

Use persistent homology when scale matters:

```text
PH_k(X, filtration) -> birth/death intervals for k-dimensional features
```

Interpretation:

```text
short-lived holes -> likely noise / projection artifact / micro-detail
long-lived holes  -> stable topology candidate / audit priority
```

This is where Betti numbers become useful for signal/noise separation.

## Relation to Mass-Number

Betti numbers can contribute to Mass-Number as topological complexity cost:

```text
m_A(G; R)
  includes w_Betti * TopoCost(B(G))
```

Candidate cost:

```text
TopoCost(B) = sum_k lambda_k * beta_k
```

where weights `lambda_k` are nonnegative and regime-declared.

Boundary:

```text
Betti complexity contributes to Mass-Number.
It is not Mass-Number by itself.
```

## Relation to Anti-Music

Anti-Music residual catches field disharmony.

Betti numbers catch topological structure.

```text
low residual + unexpected Betti change
  -> smooth but topologically surprising

high residual + stable Betti vector
  -> noisy field with stable topology

high residual + changing Betti vector
  -> unstable topology / repair priority
```

## Validator requirements

Every Betti audit must declare:

```text
source domain
native dimension/regime
projection, if any
complex construction method
filtration, if persistent
computed Betti vector
expected Betti vector, if known
claim state
authority scope
receipt status
failure mode if mismatch
```

If any are missing, the Betti result remains `HOLD`.

## Boundary

```text
Betti number != proof of physical truth
projection Betti != native Betti unless projection preserves topology
pretty loop != homology class
homology class != semantic validity
stable topology != complete correctness
```

## Operating sentence

```text
Betti numbers are the Equation Forest's hole counters: they audit the connected components, loops, cavities, and higher-dimensional voids created by Goxels, Sidon relations, forest paths, CAD solids, and fluid domains.
```
