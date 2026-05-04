# Three.js Goxel Weirdness Bridge

Status: HOLD / workbench projection
Authority: rendering/projection spec; not canonical proof
Related: `docs/gcl/ForestPathGoxelModel.md`, `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/SidonMatrixGoxelModel.md`, `docs/gcl/AutopoieticNScalarField.md`

## Purpose

This document defines how the “weirdness” represented in Three.js modules slots into the Goxel / Forest / Sidon / GCL model.

Three.js is the projection/runtime phenotype layer. It makes typed Goxel states visible, inspectable, and interactable.

It is not the proof layer.

```text
GCL genotype / field state
  -> Goxel domains
  -> Sidon matrix / forest path audit
  -> Three.js projection
  -> user-visible weirdness
  -> interaction / inspection / repair loop
```

## Core doctrine

```text
Visual weirdness is not an error by default.
Visual weirdness is an exposed audit state.
```

A strange render should be classified before it is discarded.

```text
weird visual artifact
  -> projection artifact?
  -> residual field structure?
  -> path ambiguity?
  -> Sidon collision?
  -> Mass-Number budget stress?
  -> missing receipt?
  -> genuine bug?
```

## Three.js role

Three.js may render:

- Goxel boundaries
- scalar-field level sets
- forest domains
- admissible paths
- residual/thicket regions
- Sidon matrix conflicts
- fusion/repulsion candidates
- Mass-Number load
- NaNMass / ProjectionArtifact states
- microvoxel materialization patches
- GCL genotype/phenotype splits

Three.js must not assert:

```text
rendered shape is true
beautiful field is proof
smooth visual fusion proves valid topology
central object is correct
high visual salience is evidence
```

## Renderable object model

```ts
type RenderableGoxel = {
  goxel_id: string;
  source_gcl_id: string;
  domain_definition: string;
  local_potential_ref: string;
  render_mode:
    | "mesh"
    | "sdf_raymarch"
    | "point_cloud"
    | "wire_volume"
    | "field_slice"
    | "implicit_surface"
    | "microvoxel_debug";
  audit_state:
    | "raw"
    | "candidate"
    | "audited"
    | "closed"
    | "blocked"
    | "quarantined";
  weirdness_class?: WeirdnessClass;
  receipts: string[];
};
```

## Weirdness classes

```ts
type WeirdnessClass =
  | "projection_artifact"
  | "field_residual"
  | "sidon_collision"
  | "forest_path_ambiguity"
  | "mass_budget_stress"
  | "nan_mass_boundary"
  | "microvoxel_materialization"
  | "fusion_candidate"
  | "repulsion_candidate"
  | "shader_bug"
  | "numerical_instability"
  | "unknown";
```

## Forest path rendering

Forest paths should render typed states, not merely lines.

```ts
type RenderableForestPath = {
  path_id: string;
  goxel_sequence: string[];
  path_state:
    | "KnownPath"
    | "CandidatePath"
    | "ProjectionPath"
    | "ResidualPath"
    | "BlockedPath"
    | "QuarantinedPath";
  path_cost: number;
  residual_score?: number;
  receipt_status: "missing" | "present" | "failed" | "waived";
  failure_mode?: string;
};
```

Visual rule:

```text
KnownPath        -> stable render
CandidatePath    -> inspectable but unpromoted render
ProjectionPath   -> visibly marked projection-only
ResidualPath     -> shown as unresolved structure / thicket
BlockedPath      -> visibly interrupted or gated
QuarantinedPath  -> isolated / warning render
```

## Sidon matrix rendering

The Sidon matrix can be projected into Three.js as relationship geometry.

```text
Goxels           -> nodes / domains
Sidon entries    -> edges / contact zones / relation bands
CB2 failures     -> collision markers
fusion candidates -> blend volumes
repulsion candidates -> separation vectors
needs_closure    -> unresolved bridge markers
```

Renderable edge:

```ts
type RenderableSidonEdge = {
  left_goxel: string;
  right_goxel: string;
  intersection_class: string;
  cb2_status: "pass" | "fail" | "unknown";
  compatibility: "compatible" | "incompatible" | "needs_closure";
  recommended_response:
    | "no_action"
    | "fuse"
    | "repel"
    | "hold"
    | "quarantine"
    | "request_receipts";
};
```

## Mapping weirdness to repair

| Weirdness class | Likely source | Repair route |
|---|---|---|
| `projection_artifact` | N-space to 3D projection loss | declare projection, add chart, mark projection-only |
| `field_residual` | anti-music / curvature / unresolved scalar detail | compute residual, classify thicket, maybe materialize goxel/microvoxel |
| `sidon_collision` | domain incompatibility | run CB2 / Sidon matrix audit; fuse, repel, hold, or quarantine |
| `forest_path_ambiguity` | unclear route between domains | classify path as candidate/residual/blocked |
| `mass_budget_stress` | compute/memory/route cost too high | split Goxel, lower detail, request budget receipt |
| `nan_mass_boundary` | infinity-like or unclosed accounting | route to NaNMass / LimitBoundary / quotient repair |
| `microvoxel_materialization` | local detail required | allocate cache/detail packet with expiry policy |
| `fusion_candidate` | compatible overlapping domains | attempt gated fusion |
| `repulsion_candidate` | incompatible domains | adjust potentials to preserve gap |
| `shader_bug` | implementation defect | debug renderer; do not alter ontology |
| `numerical_instability` | sampling/precision failure | fixed-point/Q16_16 policy, epsilon audit, fallback solver |
| `unknown` | unclassified | HOLD and inspect |

## Module layout target

Suggested Three.js module boundaries:

```text
src/goxel/GoxelTypes.ts
src/goxel/GoxelRenderer.ts
src/goxel/GoxelFieldMaterial.ts
src/goxel/SidonEdgeRenderer.ts
src/forest/ForestPathRenderer.ts
src/forest/ForestPathState.ts
src/audit/WeirdnessClassifier.ts
src/audit/ProjectionBoundaryOverlay.ts
src/audit/MassNumberOverlay.ts
src/debug/ReceiptInspectorPanel.ts
```

## Runtime inspection loop

```text
1. Render Goxel/forest/path state.
2. User notices visual weirdness.
3. WeirdnessClassifier assigns candidate class.
4. Inspector panel shows source GCL object, Goxel domain, Sidon entries, path status, Mass-Number cost, and receipts.
5. User chooses repair/action: classify, hold, fuse, repel, materialize, quarantine, or file shader bug.
6. Result writes back to GCL/audit state, not directly to truth.
```

## Required overlays

The Three.js modules should expose overlays for:

```text
claim_state
authority_scope
audit_state
path_state
weirdness_class
receipt_status
mass_number_cost
CB2 status
projection boundary
```

This keeps the rendering honest.

## Boundary

Three.js is allowed to be strange.

It is not allowed to be silently authoritative.

```text
rendering = phenotype
GCL object = genotype
receipts = evidence
gates = promotion control
```

## Operating sentence

```text
The Three.js weirdness layer is the visible phenotype of Goxel-field audit states: it helps discover, classify, and repair unresolved structure without letting visuals become proof.
```
