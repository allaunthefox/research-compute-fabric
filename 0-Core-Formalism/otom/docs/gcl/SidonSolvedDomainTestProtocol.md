# Solved Sidon Domain Test Protocol for Goxel Matrices

Status: HOLD / workbench projection
Authority: benchmark/test-design spec; not canonical proof
Related: `docs/gcl/SidonMatrixGoxelModel.md`, `docs/gcl/GoxelAuditBridge.md`, `docs/gcl/AutopoieticNScalarField.md`

## Purpose

This document defines how to test the Goxel-based Sidon matrix on already-solved Sidon domains.

The goal is calibration, not proof-by-analogy.

Solved Sidon domains provide known-good combinatorial fixtures. Goxels provide geometric-volume elements. The test asks whether the Goxel/Sidon audit matrix can recover, preserve, or use known Sidon constraints while exposing additional geometric, field, and mass-number structure.

## Core hypothesis

```text
If a solved Sidon domain has known pairwise uniqueness constraints,
then a Goxelized representation should produce a Sidon matrix whose conflicts,
compatibilities, and fusion/repulsion recommendations agree with those constraints
under a declared projection and field regime.
```

## What counts as a solved Sidon domain

Use domains where the Sidon property or equivalent pairwise uniqueness property is already known.

Examples of calibration fixtures:

```text
Classical Sidon sets in finite integer intervals
Sidon sets in finite cyclic groups Z_n
Singer difference sets / finite projective-plane constructions
Costas arrays as distinct displacement fixtures
Golomb rulers as distinct distance fixtures
known non-Sidon counterexamples
near-Sidon sets with one deliberate collision
```

Each fixture must declare:

```ts
type SolvedSidonFixture = {
  fixture_id: string;
  domain: string;
  elements: string[];
  operation: "sum" | "difference" | "distance" | "displacement" | "custom";
  expected_unique_pairs: boolean;
  known_collisions: string[];
  source_receipt: string;
  notes: string;
};
```

## Why this helps the research goals

The solved fixtures give a controlled way to test whether Goxel relations preserve lawfulness.

They support four project goals:

```text
1. Auditability
   Does the matrix catch known collisions and preserve known non-collisions?

2. Compression
   Can lawful Sidon structure reduce representation cost versus naive pairwise storage?

3. Mass-Number calibration
   Do row/column interaction costs identify heavy or collision-prone Goxels?

4. Projection discipline
   Does the same solved domain behave consistently across voxel, goxel, graph, and field projections?
```

## Goxelization of solved domains

Each solved Sidon element becomes a Goxel seed or bounded domain.

Minimal embedding:

```text
a_i in D
  -> seed s_i
  -> local potential Phi_Gi
  -> Goxel G_i = { v : Phi_Gi(v) <= iso }
```

For integer/cyclic domains, use simple finite embeddings first:

```text
integer element a_i -> point seed on R^1 or circular seed on S^1/Z_n
pair relation       -> field-domain relation or graph edge
Sidon violation     -> CB2/compatibility failure candidate
```

For Costas/Golomb-like fixtures:

```text
array/ruler mark -> Goxel seed
pair displacement/distance -> derived math object
duplicate displacement/distance -> Sidon collision candidate
```

## Expected matrix behavior

For a valid Sidon fixture:

```text
S_R[i,j].compatibility should not produce duplicate relation classes
for distinct unordered pairs that are required to be unique.
```

For a known non-Sidon fixture:

```text
S_R[i,j] and S_R[k,l] should expose the duplicated sum/difference/distance/displacement.
```

Expected response mapping:

| Fixture condition | Expected Sidon matrix response |
|---|---|
| valid Sidon pair | compatible / no_action / audited |
| duplicate pair relation | needs_closure or incompatible |
| geometric overlap without combinatorial collision | projection_artifact or geometry-only collision |
| combinatorial collision without geometric overlap | derived_math_collision |
| near miss | hold / request_receipts / anti-music residual check |
| known invalid construction | quarantine or repel |

## Separate collision classes

The protocol must distinguish these.

```text
combinatorial_collision
  duplicate sum/difference/distance/displacement in solved Sidon domain

geometric_collision
  overlapping or singular Goxel domains in the scalar field

projection_collision
  false overlap created by projecting N-space shape into lower-dimensional view

field_collision
  SmoothMax/residual/regularity failure after attempted fusion

mass_collision
  finite budget or Mass-Number cost failure
```

Do not collapse all failures into `CB2 fail`.

## Metrics

Use these metrics for each fixture.

```ts
type SidonGoxelTestMetrics = {
  true_collision_recall: number;
  false_collision_rate: number;
  valid_pair_preservation: number;
  projection_artifact_rate: number;
  row_cost_entropy: number;
  mass_budget_delta_total: number;
  compression_delta_vs_naive_pairs: number;
  repair_success_rate: number;
};
```

Interpretation:

```text
high true_collision_recall
  good: known Sidon violations are detected

low false_collision_rate
  good: valid Sidon relations are not falsely rejected

high projection_artifact_rate
  warning: the embedding/projection is misleading

high row_cost_entropy
  useful: interaction load is uneven and may identify structural hubs

positive compression_delta_vs_naive_pairs
  useful: lawful structure is reducing representation cost
```

## Test phases

### Phase 0: Baseline combinatorial matrix

Build the ordinary Sidon matrix directly from the solved domain.

```text
M_base[pair] = operation(a_i, a_j)
```

Expected:

```text
valid Sidon set -> all relevant pair outputs unique
invalid set -> duplicate outputs appear
```

### Phase 1: Goxel encoding

Encode each element as a Goxel.

```text
a_i -> G_i
```

Start with simple local potentials:

```text
Phi_Gi(v) = ||v - s_i||^2 - r_i^2
```

Then test richer shapes only after baseline passes.

### Phase 2: Matrix lift

Construct:

```text
S_R[i,j] = SidonAudit_R(G_i, G_j)
```

Attach the original solved-domain pair relation as a `derived_math_ref`.

### Phase 3: Collision-class separation

For each flagged event, classify it as:

```text
combinatorial_collision
geometric_collision
projection_collision
field_collision
mass_collision
```

A good model does not confuse these.

### Phase 4: Repair actions

Apply candidate responses:

```text
fuse
repel
hold
quarantine
request_receipts
```

Then re-measure whether the solved-domain invariant is preserved.

### Phase 5: Compression and lawfulness check

Compare representation cost:

```text
naive pair table cost
vs
Goxel/Sidon audited representation cost
```

Look for lawfulness:

```text
stable relation classes
low residual
repeatable collision detection
reduced encoding cost
consistent results across projections
```

## Minimal JSON fixture format

```json
{
  "fixture_id": "sidon_integer_valid_01",
  "domain": "integer_interval",
  "elements": [0, 1, 4, 6],
  "operation": "sum",
  "expected_unique_pairs": true,
  "known_collisions": [],
  "embedding": {
    "type": "R1_point_seed",
    "radius": 0.1
  },
  "receipts": ["source_or_generated_receipt"]
}
```

Counterexample fixture:

```json
{
  "fixture_id": "sidon_integer_invalid_01",
  "domain": "integer_interval",
  "elements": [0, 1, 2, 3],
  "operation": "sum",
  "expected_unique_pairs": false,
  "known_collisions": ["0+3 = 1+2"],
  "embedding": {
    "type": "R1_point_seed",
    "radius": 0.1
  },
  "receipts": ["generated_counterexample"]
}
```

## First implementation target

Create a small executable harness:

```text
scripts/sidon_goxel_fixture_runner.py
```

Required outputs:

```text
fixtures/*.json
outputs/sidon_matrix/*.json
outputs/sidon_matrix/*.csv
outputs/sidon_matrix/summary.md
```

The runner should:

```text
1. Load fixture.
2. Compute baseline pair relation table.
3. Encode elements as simple Goxels.
4. Compute Goxel Sidon matrix entries.
5. Compare detected collisions against expected collisions.
6. Emit metrics and failure classes.
```

## Lean targets

Initial Lean mirror can stay combinatorial.

```lean
-- Candidate namespace
namespace OTOM.SidonGoxel

-- finite domain
-- pair operation
-- uniqueness predicate
-- collision predicate
-- matrix entry typing
-- theorem: valid Sidon fixture has no duplicate pair outputs
-- theorem: known counterexample has duplicate pair output

end OTOM.SidonGoxel
```

Do not formalize scalar-field geometry first. Prove the fixture logic first, then lift.

## How this furthers the larger goals

This protocol connects several stack goals:

```text
Mass-Number theory
  row/column costs become finite interaction-mass estimates

GCL
  fixtures become Genetic Coding Language objects with genotype/phenotype split

Goxels
  N-space shapes become auditable geometric-volume elements

OTOM
  derived math gets traced through projection, closure, and receipts

Compression
  lawful Sidon structure tests whether relation uniqueness compresses better than naive pair tables

Signal/noise research
  known collision vs false collision becomes a controlled residual/noise discrimination task
```

## Boundary

A successful solved-domain test does not prove the Goxel field ontology.

It proves only that:

```text
under declared fixture, operation, embedding, and regime,
the Goxel/Sidon audit matrix preserved or detected the expected solved-domain invariant.
```

That is enough for calibration.

## Operating sentence

```text
Solved Sidon domains are calibration fixtures for the Goxel matrix: they let us test whether N-space geometric-volume auditing preserves known pairwise uniqueness laws before applying it to open research structures.
```
