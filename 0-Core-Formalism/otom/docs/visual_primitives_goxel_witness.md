---
project: OTOM
domain: axis-04-formalization
type: ResearchNote
settlement: FORMING
authority: registry
route_signature: otom/axis-04-formalization/researchnote/visual-primitives-goxel-witness/v0
source_url: https://www.alphaxiv.org/abs/visual-primitives
---

# Visual Primitives as Goxel Witnesses

## External anchor

The linked visual-primitives work frames a multimodal reasoning bottleneck as a
reference problem: language alone is often too ambiguous to identify the exact
spatial object or region involved in a visual reasoning step.

The project-facing interpretation is narrow and engineering-safe:

> Coordinate-bearing visual primitives can act as witness objects that bind a
> linguistic claim to a bounded visual/manifold region.

This note does **not** treat the external work as validation of the full OTOM or
TSM ontology. It only records the bridge:

```text
language-only reference is under-bound
coordinate witness reduces reference ambiguity
reduced reference ambiguity can reduce replay/compression cost
bounded witness can be formalized as a Goxel-facing primitive
```

## Stack translation

| External phrase | Stack phrase | Meaning |
|---|---|---|
| visual primitive | coordinate-bearing witness | point/box/mask-like spatial reference unit |
| reference gap | binding ambiguity | language does not uniquely bind to a field region |
| point while reasoning | witness trace atom | reasoning emits a spatial receipt |
| bounding box / point | bounded region | finite coordinate support |
| visual token efficiency | witness compression pressure | spatial grounding may reduce reference entropy |

## Canonical formal bridge

Lean module:

```text
0-Core-Formalism/otom/tools/lean/Semantics/Semantics/VisualPrimitive.lean
```

Primary objects:

```text
PrimitiveKind
BoundedRegion
VisualPrimitive
GoxelWitness
```

First theorem-level gates:

```text
BoundedRegion.Nonempty
VisualPrimitive.Binds
GoxelWitness.Grounded
area_positive_of_grounded
```

## Proposed compression objective

A visual primitive is useful when the cost of storing the witness is lower than
the ambiguity it removes:

```text
minimize:
  H(reference | primitive)
+ lambda * primitive_cost
+ mu     * replay_cost
+ nu     * hallucination_penalty
```

Equivalent operational rule:

> A good primitive reduces reference entropy more than it costs to encode and
> replay.

## Relationship to TSM

The TSM direction should treat a visual primitive as a finite state-transition
receipt, not as passive annotation:

```text
VisualPrimitive -> GoxelWitness -> TSM register / checkpoint trace
```

This preserves the important distinction:

- annotation: a label attached after perception
- witness: a bounded coordinate receipt used during reasoning/replay

## Evidence discipline

Allowed claim state: `BEAUTIFUL_PROVISIONAL` until benchmarked.

Acceptable near-term claims:

1. A coordinate-bearing primitive can be represented as a finite bounded region.
2. A Goxel witness can bind a semantic tag to a nonempty coordinate region.
3. A grounded witness has positive spatial receipt cost.

Blocked claims without evidence receipts:

1. Any universal claim about multimodal model capability.
2. Any claim that this validates OTOM as a full ontology.
3. Any claim of compression improvement without measured baselines.
4. Any claim of hallucination reduction without controlled evaluation.

## Next tests

1. Add a small synthetic scene corpus with known reference targets.
2. Compare text-only references against point/box witness references.
3. Measure reference entropy, replay cost, and error rate.
4. Add evidence receipts before promoting beyond `BEAUTIFUL_PROVISIONAL`.
