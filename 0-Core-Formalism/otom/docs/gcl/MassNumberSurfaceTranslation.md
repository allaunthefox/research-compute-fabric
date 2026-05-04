# Mass Number Surface Translation

Status: HOLD / translation doctrine
Authority: workbench synthesis; not formal proof
Related:

- `docs/gcl/ErdosMentalModelMassNumberMap.md`
- `docs/gcl/FrameworkReaderRamp.md`
- `docs/gcl/NonCompressedGoxelGeometryDoctrine.md`
- `docs/gcl/EquationUnderverseDoctrine.md`

## Purpose

This document pins the next correction.

The point of a Mass Number is not only to hold a modeling move.

The point is to translate that modeling move into a surface.

```text
Mass Number -> Surface
```

The surface is the readable / testable projection of the cognitive model.

## Core statement

```text
A Mass Number is a holder packet.
A Surface is the rendered projection of that holder packet.
```

In Erdős-style work:

```text
The theorem says what is true.
The Mass Number records how the mind made truth visible.
The Surface shows where that visibility lives.
```

## Why surface translation matters

A mental model is hard to compare while it remains inside language.

A surface gives it observable structure.

```text
mental model
  -> Mass Number packet
  -> scalar/vector fields
  -> surface projection
  -> measurable ridges, basins, thresholds, folds, holes, seams, and obstructions
```

This turns a proof strategy into a geometry of constraint.

## Surface definition

A Mass Surface is a bounded projection generated from a Mass Number packet.

```text
Surface(M) = project(
  invariant,
  threshold_pressure,
  obstruction_shape,
  proof_engine,
  underverse_shadow
)
```

Interpretation:

```text
invariant             -> surface anchor / conserved contour
threshold_pressure    -> height / slope / gradient pressure
obstruction_shape     -> holes / walls / forbidden ridges
proof_engine          -> flow rule over the surface
underverse_shadow     -> negative relief / missing region / scar field
```

## Surface fields

A practical Mass Surface can expose these fields:

```text
height                = threshold pressure
slope                 = rate at which structure becomes forced
curvature             = difficulty of representation shift
basins                = stable modeling regimes
ridges                = forcing thresholds
holes                 = forbidden configurations / avoiders
seams                 = representation-change boundaries
scar field            = Underverse residue
flow lines            = proof-engine routes
compression gradient  = reduction from raw problem to tractable model
```

## Erdős example

### Happy Ending / convex polygon forcing

Mass Number:

```text
problem_id: HappyEnding_g(n)
source_domain: planar geometry
mental_model: general-position convexity forcing
representation_shift: coordinates -> order type / cups-caps
invariant: convex n-gon
threshold: point count
obstruction: point configuration avoiding convex n-gon
proof_engine: geometric Ramsey / cups-caps / finite enumeration
underverse_shadow: nonconvex delay configurations
```

Surface translation:

```text
height                = point count / threshold pressure
ridge                 = point count where convex n-gon becomes forced
holes                 = configurations avoiding the convex n-gon
seams                 = transition from coordinate geometry to order type
flow lines            = cups/caps subsequence routes
scar field            = near-counterexample configurations
basin                 = general-position assumptions
```

## Sidon / additive example

Mass Number:

```text
problem_id: Sidon_set
source_domain: integer additive combinatorics
mental_model: additive collision topology
representation_shift: integers -> sum-pair collision surface
invariant: uniqueness of pair sums
threshold: set size relative to ambient interval
obstruction: repeated-sum collision
proof_engine: counting / modular construction / finite geometry
underverse_shadow: additive collision residue
```

Surface translation:

```text
height                = additive density
ridge                 = density where repeated sums become unavoidable
holes                 = collision-free regions
walls                 = forbidden repeated-sum equalities
flow lines            = admissible sum-pair routes
scar field            = repeated-sum residue
basin                 = Sidon-valid set families
```

## Surface as Goxel collapse target

A Goxel is pre-representation manifold potential.

A Mass Number selects the modeling representation.

A Mass Surface is the shape that appears after projection.

```text
Goxel phase:
  unresolved mathematical possibility

Mass Number phase:
  cognitive holder selects invariant / threshold / obstruction / proof engine

Surface phase:
  model becomes visible as a geometric projection
```

So the pipeline is:

```text
Goxel -> Mass Number -> Surface -> ACI/Warden validation
```

## Surface as anti-confusion layer

A surface prevents future confusion because it forces each abstract term to map to a visible or computable feature.

```text
If a concept cannot be mapped to a surface feature,
then it remains metaphorical and should not be promoted.
```

Surface feature mapping:

```text
threshold -> ridge
obstruction -> hole/wall
proof path -> flow line
underverse -> scar field / negative relief
representation shift -> seam
invariant -> contour / anchor
compression gain -> gradient shortening
failure mode -> rupture / unbounded basin / NaN tear
```

## Implementation packet

A practical surface packet should be finite and auditable.

```text
MassSurfacePacket = {
  surface_id,
  source_mass_number_id,
  coordinate_system,
  fields,
  invariant_contours,
  threshold_ridges,
  obstruction_holes,
  representation_seams,
  proof_flow_lines,
  underverse_scar_field,
  validation_status,
  receipt_hash
}
```

All hot-path numeric fields should use fixed-point or integer-coded values.

## Surface translation rule

```text
For every Mass Number, ask:

1. What is the surface height?
2. What are the ridges?
3. What are the holes?
4. What are the seams?
5. What are the basins?
6. What are the flow lines?
7. What is the Underverse scar?
8. What would count as a surface rupture?
```

## Compact doctrine

```text
Mass Numbers hold the modeling move. Surfaces render the modeling move. A theorem becomes usable in the stack when its mental model can be translated into a surface whose ridges, holes, seams, basins, flow lines, and scar fields make the invariant, threshold, obstruction, proof engine, and Underverse residue visible.
```
