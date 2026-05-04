# Goxel Audit Bridge

Status: HOLD / workbench projection
Authority: bridge spec; not canonical proof
Related: `docs/gcl/AutopoieticNScalarField.md`, `docs/gcl/GCLCompleteSurface.md`, `docs/gcl/MassNumberGCLSubset.md`

## Purpose

The Goxel Audit Bridge explains how N-space geometric shapes can inhabit existing voxel, microvoxel, mesh, SDF, CAD, and rendering workflows while keeping their derived mathematics auditable under a declared field regime.

The goal is not to replace existing voxel work. The goal is to let richer geometric-volume elements dock into it.

```text
N-space shape
  -> Goxel geometric-volume element
  -> voxel-like editable structure
  -> microvoxel / mesh / SDF / WebGPU projection
  -> scalar-field audit
  -> receipts or HOLD
```

## Canonical definition

A **Goxel** is an N-space shape that inhabits a geometric volume.

More formally, a Goxel is a finite geometric-volume element: a bounded scalar sub-manifold with local geometric intent.

```text
G = { v in R^n : Phi_G(v) <= iso }
```

where:

```text
G        = Goxel domain
v        = coordinate in active n-space
R^n      = finite active ambient regime
Phi_G    = local Goxel potential function
iso      = level/sublevel threshold
```

A Goxel is not merely a container of data. It is a topological domain inside n-space.

It is a packet of the field equation carrying local geometric intent.

## Core idea

```text
voxel:      discrete sample cell / occupancy slot
hoxel:      4D unit block / spatiotemporal grid element
goxel:      geometric-volume element / scalar sub-manifold
```

A voxel asks:

```text
Where is occupancy sampled?
```

A Goxel asks:

```text
What N-space shape inhabits this geometric volume?
```

A microvoxel asks:

```text
Where must local detail be materialized?
```

## Element evolution

| Element | Space representation | Dimensionality | Mathematical nature |
|---|---|---|---|
| Voxel | point sample / grid cell | 3D | discrete value |
| Hoxel | unit block | 4D | spatiotemporal grid |
| Goxel | geometric volume | n-dimensional | scalar sub-manifold |

## Why this matters

Existing voxel systems are useful because they provide:

- edit locality
- chunking
- collision approximation
- storage layouts
- rendering pipelines
- user-understandable world editing

But pure voxels tend to flatten geometry into cells.

Goxels preserve the existing workflow while allowing the underlying object to be:

- an implicit surface
- a signed-distance fragment
- a spline patch
- a capsule or convex primitive
- a meshlet
- a field sample packet
- a higher-dimensional projected shape
- a repair patch derived from scalar-field residuals
- a bounded scalar sub-manifold

## Informational DNA

Every Goxel carries a local potential function:

```text
Phi_G : Omega_G -> R
```

This local potential is the Goxel's informational DNA.

It defines:

- boundary behavior
- curvature
- local topology
- field contribution
- fusion/repulsion behavior
- zero-crossing or sublevel-set structure
- audit obligations

## N-space inhabitation rule

An N-space shape may inhabit an existing editable world only through a declared projection.

```text
Shape_n in R^n
  -> chart selection
  -> Goxel encoding
  -> projection to local world coordinates
  -> voxel-like occupancy / mesh / SDF / microvoxel detail
```

No N-space shape may silently pretend to be native 3D geometry without declaring the projection that made it visible or editable.

## Fusion rule

When multiple Goxels occupy compatible regions of n-space, they compose through a declared field-fusion operator.

Draft default:

```text
Phi_Total = SmoothMax(Phi_G1, Phi_G2, ..., Phi_Gk)
```

SmoothMax is a projection/operator choice, not automatically a theorem. It must declare its regime, smoothing parameter, continuity class, and audit obligations.

Goal:

```text
compatible Goxel junctions
  -> smooth transition
  -> low or zero local Anti-Music residual
```

Do not globally assume every SmoothMax fusion has zero residual. Zero residual is a gate result, not a default property.

## Mass-number and metabolic cost

Because a Goxel inhabits geometric volume, it carries field inertia in the accounting sense.

```text
m_A(G) = mass-number / metabolic cost proxy for the Goxel domain
```

Mass-number may depend on:

- occupied geometric volume
- scalar curvature / residual
- topological complexity
- internal zero-crossing complexity
- support size
- projection complexity
- GPU/compute budget
- route cost

Boundary:

```text
m_A is finite accounting mass.
m_A is not SI physical mass.
m_A is not automatically distance.
```

## Audit rule

Any math derived from a Goxelized N-space shape must be auditable in a declared field.

```text
DerivedMath(Goxel)
  -> declare source shape
  -> declare projection
  -> declare scalar field / chart
  -> compute gates
  -> attach receipts
```

If the audit cannot close, the result remains `HOLD` or routes to `NaNMass` / `ProjectionArtifact` / `RegimeMismatch`.

## Proven field boundary

A “proven field” does not mean the rendered shape proves reality.

It means the field has declared enough structure to audit claims locally:

```text
ProvenField_R iff
  finite_regime(R)
  and declared domain Omega
  and declared scalar field Phi
  and declared projection Pi
  and declared regularity gate
  and declared budget/mass accounting
  and declared receipt requirements
```

Within such a field, a Goxel-derived claim can be checked against:

- regular level-set conditions
- collision / CB2 gates
- mass-number budget
- projection consistency
- source-seed provenance
- residual / anti-music cost
- closure state

## CB2 collision audit

CB2 is a collision or contradiction detector. For Goxels, it checks whether combined domains create invalid topology.

Possible failure modes:

- non-manifold singularity
- invalid overlap
- contradictory scalar assignment
- Sidon collision
- regime mismatch
- projection collision

## Fusion / repulsion response

If two Goxels attempt to occupy the same n-space in a structurally incompatible way, the gate triggers an incompatibility response.

Allowed responses:

```text
Fuse:
  morph volumes into one continuous scalar surface when compatibility is established

Repel:
  adjust local potentials to maintain a gap when fusion would create invalid topology

Hold:
  preserve the conflict as unresolved until receipts exist

Quarantine:
  block the construction when it is unsafe, overbroad, or misleading
```

## Corrected Goxel boundary condition

Do not write this as an unconditional theorem:

```text
CB2(Goxel_A union Goxel_B) = 0 implies the volumes are topologically fused.
```

That is too strong.

Use the scoped gate form:

```text
FusionAllowed_R(G_A, G_B) iff
  CB2(G_A union G_B) = 0
  and Compatible_R(G_A, G_B)
  and Regular(boundary(G_A union G_B))
  and m_A(G_A union G_B; R) <= Budget_R
  and ReceiptsRequired(fusion) are present or explicitly marked missing
```

Then:

```text
FusionAllowed_R(G_A, G_B)
  -> may construct fused candidate G_AB
```

The result is a candidate fused Goxel, not universal proof of all topology.

## Goxel object

```ts
type Goxel = {
  goxel_id: string;
  source_shape_id: string;
  source_space: `R^${number}` | string;
  target_chart: string;
  projection: string;
  domain_definition: string;
  local_potential: string;
  primitive:
    | "plane_patch"
    | "sdf_fragment"
    | "convex_cell"
    | "spline_patch"
    | "capsule"
    | "implicit_blob"
    | "meshlet"
    | "field_sample_packet"
    | "nspace_projected_shape"
    | "bounded_scalar_submanifold";
  parameters: Record<string, unknown>;
  boolean_role?: "fill" | "cut" | "blend" | "constraint" | "repair" | "fuse" | "repel";
  support_region: string;
  mass_number_cost?: number;
  derived_math_refs: string[];
  audit_status: "raw" | "held" | "audited" | "closed" | "quarantined";
  receipts: string[];
};
```

## Derived math object

```ts
type GoxelDerivedMath = {
  math_id: string;
  goxel_id: string;
  expression: string;
  variables: string[];
  source_field: string;
  projection: string;
  assumptions: string[];
  gates: string[];
  claim_state: "U_scope" | "HOLD" | "V_scope" | "REVIEWED" | "CANONICAL_LEAN" | "QUARANTINE";
  failure_mode?:
    | "projection_artifact"
    | "regime_mismatch"
    | "missing_receipt"
    | "regularity_failure"
    | "collision_failure"
    | "sidon_collision"
    | "nan_mass";
};
```

## Field audit pipeline

```text
1. Receive or synthesize N-space shape.
2. Encode it as one or more Goxels.
3. Declare chart and projection into editable world space.
4. Materialize only the needed voxel/microvoxel/mesh/SDF view.
5. Derive local math from the Goxelized shape.
6. Audit derived math in declared scalar field.
7. Apply gates: finite regime, regularity, CB2, mass-number budget, projection consistency.
8. If gates pass: attach receipts and mark locally valid.
9. If gates fail: HOLD, repair, quarantine, or route to NaNMass / ProjectionArtifact.
```

## Final thesis

By defining shapes as Goxels, the editor becomes a geometric fluid.

```text
Volumetric sculpting:
  editing injects volumes of intent into n-space

Continuous topology:
  scalar-defined boundaries can remain smooth and resolution-independent

Audited organism:
  the Goxel collection forms a field body, with OTOM acting as immune/audit system
```

## Canonical warning

```text
Goxelized shape != proof
projection != proof
voxel occupancy != source geometry
microvoxel detail != ontology
rendered N-space shadow != N-space truth
CB2 = 0 alone != complete manifold viability
SmoothMax alone != guaranteed zero residual
```

A Goxel makes N-space shape usable inside existing work. It does not make the shape true.

## Operating sentence

```text
A Goxel is an N-space shape inhabiting a geometric volume, expressed as a bounded scalar sub-manifold and admitted into ordinary editing workflows only through declared projection, audit, and receipt gates.
```
