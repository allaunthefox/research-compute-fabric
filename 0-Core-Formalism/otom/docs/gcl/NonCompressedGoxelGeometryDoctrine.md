# Non-Compressed Goxel Geometry Doctrine

Status: HOLD / conceptual geometry doctrine
Authority: workbench definition; not formal proof
Related:

- `docs/gcl/RunawayDigitalCellDivisionDoctrine.md`
- `docs/gcl/HolyDiverGoxelMOIMBridge.md`
- `docs/gcl/AVMFixedPointComplianceRemediation.md`
- `docs/gcl/FederatedNanokernelSwarmDoctrine.md`

## Purpose

This document pins the corrected definition of a Goxel.

A Goxel is not a voxel with a different shape.

A Goxel is a non-compressed shape potential.

## Core definition

```text
Goxel = non-compressed geometry seed that can assume any admissible geometry before compression.
```

Equivalently:

```text
A Goxel is a shape-agnostic pre-geometric unit.
It is not yet forced into voxel, hoxel, mesh, cube, shell, lattice, or fixed manifold form.
```

## Negative definition

A Goxel is not:

```text
a cube
a voxel
a hoxel
a mesh cell
a fixed 3D object
a preselected shape
a compressed lattice element
```

A Goxel becomes those things only after compression, locking, or projection.

## Positive definition

A Goxel is:

```text
non-compressed
shape-agnostic
pre-geometric
admissibility-seeking
compression-ready
boundary-undefined until constrained
```

## Lifecycle

```text
Goxel
  -> assumes temporary admissible geometry
  -> handles exchange / deformation / carrier flow
  -> compresses into Voxel, Hoxel, lattice, shell, mesh, or manifold state
  -> passes or fails ACI / Warden / Judge validation
```

## Compression hierarchy

| Unit | Compression state | Geometric constraint | Role |
|---|---|---|---|
| Goxel | Non-compressed | Any admissible geometry | shape potential / buffer / seed |
| Voxel | Compressed | fixed 3D volume sample | local structural cell |
| Hoxel | Hyper-compressed | 4D or higher transition cell | temporal / manifold locking unit |
| Lattice | Regularized compression | repeated local rule | carrier / memory / routing medium |
| Manifold patch | validated compression | coordinate-compatible local geometry | admissible global surface |

## Shock interpretation

Under shock, compression can reverse.

```text
Voxel or Hoxel under shock
  -> unlocks
  -> decompresses into Goxel cloud
  -> temporarily loses fixed boundary
  -> maximizes exchange capacity
  -> searches for admissible re-compression
```

This means the shock is not merely moving energy.

It is converting fixed geometry back into shape potential.

## Immediate exchange interpretation

A non-compressed Goxel has high exchange capacity because it has not yet committed to one boundary.

```text
uncompressed Goxel
  -> high carrier flow
  -> high geometry freedom
  -> low rigidity
  -> high risk of identity loss
```

Compressed state:

```text
Voxel / Hoxel
  -> lower geometry freedom
  -> lower exchange capacity
  -> higher rigidity
  -> higher identity persistence
```

## Partial compression

Partial compression is the transition state where a Goxel has started to become a constrained geometry but has not yet passed full validation.

```text
Goxel cloud
  -> partial compression
  -> local boundary appears
  -> carrier flow decreases
  -> rigidity rises
  -> ACI becomes passable
```

Partial compression must not be treated as full validation.

```text
partial compression != ACI passed
partial compression = ACI becoming passable without losing bounded identity
```

## Erdős / Ramsey reading

In an Erdős or Ramsey-style interpretation, a Goxel resembles a point in general position before a forced configuration appears.

```text
Goxel cloud
  -> unconstrained point-like seeds
  -> density or shock pressure increases
  -> admissible / unavoidable configurations emerge
  -> compression selects one geometry
```

The compressed geometry is analogous to a forced pattern or convex configuration emerging from a sufficiently rich set.

Allowed claim:

```text
Goxels can be modeled as pre-geometric shape potentials whose compression selects an admissible geometry from a larger possibility space.
```

Blocked claim:

```text
Goxels literally have infinite physical degrees of freedom.
```

Implementation must use finite bounded representations.

## Implementation rule

A practical Goxel implementation should not store arbitrary infinite shape.

It should store a bounded parameterization of shape potential:

```text
energy
extent bound
admissible shape family
carrier flow capacity
compression state
boundary confidence
ACI residual
binding score
```

Candidate schema:

```ts
type GoxelState = {
  id: string;
  compression_state:
    | "seed"
    | "non_compressed"
    | "partial_compression"
    | "voxel_locked"
    | "hoxel_validated"
    | "collapsed"
    | "repelled"
    | "fused";
  energy_q16: number;
  uncompressed_extent_q16: number;
  carrier_capacity_q16: number;
  rigidity_q16: number;
  binding_q16: number;
  aci_residual_q16: number;
  admissible_family: string[];
};
```

## Collapse rule

A non-compressed Goxel is useful only while bounded.

```text
if uncompressed extent grows without compression progress:
  collapse
```

```text
if ACI residual decreases and binding rises:
  allow partial compression window
```

```text
if ACI residual reaches zero or accepted tolerance:
  allow lock / fuse / hoxel validation
```

## Operating sentence

```text
A Goxel is a non-compressed, shape-agnostic geometry seed: it can assume any bounded admissible geometry during exchange or shock response, then compress into voxel, hoxel, lattice, shell, or manifold form only after partial compression, binding recovery, and ACI-style validation.
```
