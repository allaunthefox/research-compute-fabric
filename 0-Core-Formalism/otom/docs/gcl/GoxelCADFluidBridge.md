# Goxel CAD / Fluid Simulator Bridge

Status: HOLD / workbench projection
Authority: runtime-bridge spec; not canonical proof
Related: `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/AutopoieticNScalarField.md`, `docs/gcl/ThreeJSGoxelWeirdnessBridge.md`, `docs/gcl/SidonMatrixGoxelModel.md`, `docs/gcl/SidonSolvedDomainTestProtocol.md`

## Purpose

This document defines how Goxels slot into CAD systems and fluid simulators.

A Goxel is an N-space shape inhabiting a geometric volume:

```text
G = { v in R^n : Phi_G(v) <= iso }
```

CAD and fluid simulation consume that same object differently:

```text
CAD runtime:
  Goxel -> constraint/solid/surface/feature candidate

Fluid runtime:
  Goxel -> boundary/obstacle/source/sink/vorticity/field-domain candidate
```

The Goxel is the shared geometric-volume element. CAD and fluid systems are projections / runtime realizations.

## Core bridge

```text
GCL object / seed code
  -> Goxel bounded scalar sub-manifold
  -> CAD realization or fluid realization
  -> audit state
  -> receipts or HOLD
```

The same Goxel may have multiple runtime phenotypes:

```text
Goxel genotype:
  local potential Phi_G
  support domain
  projection
  gates
  receipts

CAD phenotype:
  B-rep / CSG / NURBS / STEP / mesh / constraint feature

Fluid phenotype:
  boundary condition / immersed body / source field / material region / vorticity patch
```

## CAD interpretation

In CAD, a Goxel becomes a shape feature or constraint-bearing volume.

Possible CAD realizations:

```text
implicit solid
signed-distance body
CSG primitive or tree
B-rep candidate
NURBS/spline patch
meshlet or triangulated approximation
STEP export candidate
constraint patch
repair patch
```

CAD bridge object:

```ts
type GoxelCADRealization = {
  goxel_id: string;
  cad_id: string;
  realization_type:
    | "implicit_solid"
    | "sdf_body"
    | "csg_tree"
    | "brep_candidate"
    | "nurbs_patch"
    | "meshlet"
    | "step_candidate"
    | "constraint_patch"
    | "repair_patch";
  source_potential: string;
  projection: string;
  tolerance: number;
  manifold_status: "unknown" | "regular" | "singular" | "repaired";
  constraint_status: "unconstrained" | "partially_constrained" | "fully_constrained" | "overconstrained";
  receipts: string[];
};
```

## CAD audit questions

A CAD realization must answer:

```text
Is the boundary regular enough to export?
Is the shape watertight if required?
Are constraints satisfied?
Is the approximation within tolerance?
Did projection from N-space create artifacts?
Does the derived CAD math match the source Goxel domain?
```

Failure modes:

```text
non_manifold_boundary
self_intersection
overconstraint
projection_artifact
tolerance_failure
missing_receipt
invalid_step_export
```

## Fluid interpretation

In a fluid simulator, a Goxel becomes a field participant.

Possible fluid realizations:

```text
solid obstacle
immersed boundary
source
sink
vorticity patch
density region
pressure region
viscosity modifier
phase interface
flow constraint
```

Fluid bridge object:

```ts
type GoxelFluidRealization = {
  goxel_id: string;
  fluid_id: string;
  realization_type:
    | "solid_obstacle"
    | "immersed_boundary"
    | "source"
    | "sink"
    | "vorticity_patch"
    | "density_region"
    | "pressure_region"
    | "viscosity_modifier"
    | "phase_interface"
    | "flow_constraint";
  source_potential: string;
  boundary_condition:
    | "no_slip"
    | "free_slip"
    | "inflow"
    | "outflow"
    | "periodic"
    | "pressure"
    | "custom";
  field_coupling: "passive" | "active" | "bidirectional";
  stability_status: "unknown" | "stable" | "unstable" | "needs_smaller_dt";
  receipts: string[];
};
```

## Fluid audit questions

A fluid realization must answer:

```text
Does the Goxel boundary create stable solver behavior?
Is the timestep finite and safe?
Does the boundary condition match the Goxel's intended role?
Does fusion/repulsion create discontinuities?
Does Mass-Number cost reflect solver load?
Does the simulation output remain simulation_only rather than proof?
```

Failure modes:

```text
solver_instability
boundary_condition_mismatch
exploding_pressure
aliasing_artifact
projection_artifact
mass_budget_failure
unclosed_flow_region
```

## Shared audit pipeline

```text
1. Define or import Goxel G.
2. Declare target runtime: CAD, fluid, or both.
3. Select realization phenotype.
4. Declare projection and tolerance/budget.
5. Generate CAD/fluid object.
6. Run runtime-specific audits.
7. Run shared GCL gates: finite regime, projection boundary, Sidon compatibility, Mass-Number budget, receipt status.
8. If pass: mark locally valid under scope.
9. If fail: HOLD, repair, quarantine, or route to ProjectionArtifact / NaNMass / RegimeMismatch.
```

## Why the same Goxel can serve both

CAD and fluid systems disagree about what geometry is for.

```text
CAD asks:
  What is the solid/surface/constraint?

Fluid asks:
  How does this volume affect flow?
```

The Goxel answers both by keeping geometry upstream:

```text
local potential Phi_G
  -> boundary definition
  -> domain support
  -> audit gates
```

Then each runtime chooses a phenotype.

## Zero-To-CAD / constructive geometry link

Zero-To-CAD style datasets and constructive CAD traces can become calibration material for the CAD side.

```text
CAD operation trace
  -> Goxel feature sequence
  -> construction work cost
  -> Mass-Number / hidden work debt
  -> audit receipts
```

This tests whether a visually simple shape hides high construction cost.

## Newtonian / superfluid simulation link

Particle-fluid and superfluid-like simulators can consume Goxels as field domains.

```text
Goxel boundary
  -> particle force region
  -> attraction/repulsion/spin field
  -> collision/fusion audit
  -> Mass-Number solver cost
```

This keeps visual simulation status honest:

```text
fluid sim success != physical proof
stable flow != theorem
beautiful vortex != validation
```

## Three.js link

Three.js renders the runtime phenotype:

```text
CAD Goxel -> surface/solid/feature visualization
Fluid Goxel -> boundary/source/vorticity/flow visualization
Audit state -> overlays and weirdness classes
```

Renderable states should expose:

```text
runtime_type: CAD | fluid | both
realization_type
claim_state
authority_scope
audit_state
Mass-Number cost
projection boundary
receipt status
```

## Sidon matrix link

The Sidon matrix audits interactions between runtime Goxels.

CAD examples:

```text
feature intersection
constraint collision
non-manifold union
invalid boolean operation
```

Fluid examples:

```text
boundary collision
source/sink contradiction
vorticity incompatibility
unstable pressure junction
```

A runtime collision should be classified, not flattened:

```text
cad_collision
fluid_collision
projection_collision
field_collision
mass_collision
combinatorial_collision
```

## Validator requirements

Any CAD/fluid Goxel bridge entry must declare:

```text
goxel_id
runtime_type
realization_type
source_potential
projection
tolerance or budget
claim_state
authority_scope
audit_state
receipts or missing-receipt status
blocked usages
```

If any are missing, the entry remains `HOLD`.

## Boundary

CAD realization is not proof of field ontology.

Fluid simulation is not proof of physical law.

```text
CAD export != theorem
fluid stability != truth
runtime phenotype != genotype proof
projection != source geometry
```

## Operating sentence

```text
Goxels let the same N-space geometric-volume element become a CAD feature, a fluid-domain participant, or a Three.js visualization while preserving projection boundaries, Mass-Number cost, and audit receipts.
```
