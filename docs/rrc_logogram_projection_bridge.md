# RRC Logogram Projection Bridge

Date: 2026-05-08

Status: projection bridge, not a mathematical proof.

Runner:

```text
4-Infrastructure/shim/rrc_logogram_projection_bridge.py
```

Receipt:

```text
4-Infrastructure/shim/rrc_logogram_projection_bridge_receipt.json
```

Curriculum:

```text
4-Infrastructure/shim/rrc_logogram_projection_bridge_curriculum.jsonl
```

Receipt hash:

```text
83f44e8341788f6cbb2013704af2622f95f140b5a98402d69cd4ddde5ea88826
```

## Primary Read

Logograms are now RRC projection objects.

The bridge binds:

```text
canonical cell hash
bounded glyph payload
substitution receipt
semantic regime
RRC type witness
```

into a single `LogogramProjection` receipt.

## Projection Equation

```text
P_logogram(source) =
  (
    canonical_hash,
    cell_hash,
    glyph_payload_16,
    semantic_regime,
    substitution_receipt,
    rrc_type_witness
  )
```

## Result Summary

```text
sample_count: 5
RRC CANDIDATE witnesses: 5
RRC HOLD witnesses: 0
projection_admissible: 5
merge_admissible: 4
repaired_tear: 1
```

The distinction matters:

```text
RRC CANDIDATE
  means the object fits the LogogramProjection type-shape well enough for the
  next proof / route stage.

projection_admissible
  means the projection is also safe under local payload and semantic-regime
  guards.

merge_admissible
  means the projection may be merged into ordinary tokenbook / route space.

quarantine_projection
  means the projection is preserved as an isolated tear-boundary receipt, not
  merged.
```

## Per-Sample Results

```text
quadratic_formula
  shape: LogogramProjection
  type witness: CANDIDATE
  projection admissible: true

pde_residual
  shape: LogogramProjection
  type witness: CANDIDATE
  projection admissible: true

metaglyph_fold
  shape: LogogramProjection
  type witness: CANDIDATE
  projection admissible: true

semantic_tear
  shape: LogogramProjection
  type witness: CANDIDATE
  projection admissible: true
  merge admissible: false
  projection lane: quarantine_projection
  repair status: isolated_not_merged
  detached mass: detached_mass:3e2412df1702b180

mhchem_surface
  shape: LogogramProjection
  type witness: CANDIDATE
  projection admissible: true
```

The `semantic_tear` case is useful.  It confirms that RRC type admission,
projection admission, and merge admission are separate gates.  A torn object can
be preserved as an auditable projection receipt while still being refused as a
tokenbook merge.

## Tear Repair

The tearing fix is not to smooth the tear away.  The fix is:

```text
horrible_manifold_tearing
  -> contradiction_witness_hash
  -> tear_boundary_hash
  -> detached_mass_id
  -> semantic_boundary_residual
  -> quarantine_projection
  -> merge_admissible = false
```

Current repaired tear:

```text
sample: semantic_tear
contradiction_witness_hash:
  3e2412df1702b1800594d5e570e390518a13c52891e3f034c0419f0c17dbdabb
tear_boundary_hash:
  47ae66c7227687763d915d4eacda4d8971546255b3df46b1966df9ed82283f04
repair_receipt_hash:
  68433cb400970b62d4e6b095b013b83b7e875a39d40465f183818c23a3afd68b
```

## RRC Shape Addition

The RRC shim now includes a `LogogramProjection` lawful shape.  Its field
equation is:

```text
logogram_cell -> canonical_hash -> glyph_payload -> projection_lane

admit iff
  cell hash,
  payload bound,
  substitution receipt,
  and regime guard close
```

## Failure Rules

```text
logogram projection reported as proof of equation                       -> invalid
payload over 16 bytes without residual lane                             -> HOLD
horrible_manifold_tearing merged without contradiction witness           -> invalid
repaired tear treated as merge-admissible without separate proof receipt -> invalid
missing RRC witness or weak projection axis                             -> HOLD
```

## Next Steps

```text
1. Add a residual lane for logograms that need more than 16 payload bytes.
2. Feed projection-admissible logograms into E1/E2 symbolic route features.
3. Add Lean RRCShape.LogogramProjection and an admission theorem.
4. Use quarantine projections to preserve tears without unsafe tokenbook merges.
```
