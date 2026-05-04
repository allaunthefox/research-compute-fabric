# Semantic Basin Shapers

## Status

`BEAUTIFUL_PROVISIONAL`

Source pointer: <https://www.sciencedaily.com/releases/2026/04/260420014748.htm>

Source content has not yet been independently verified in this repository. Treat the link as provenance to review, not as an evidence receipt.

---

## One-sentence definition

```text
Semantic Basin Shapers are structures, interventions, examples, constraints, or identifiers that alter the attractor landscape through which concepts are interpreted, routed, merged, quarantined, or promoted.
```

---

## Why this concept exists

The SCW-8192 semantic-attractor guardrails define how to prevent false ontology merges when motifs become too gravitational.

Semantic Basin Shapers describe the complementary positive mechanism:

```text
not only how to stop runaway attractors,
but how to shape the basin so useful concepts settle into safer, testable paths.
```

This matters because OTOM does not only classify finished artifacts. It routes evolving concepts through changing schemas, adapters, evidence receipts, simulations, projections, and quarantine states.

---

## Basin model

Let a concept state be:

```math
x \in \mathcal{C}
```

where `C` is the conceptual state space.

Let semantic energy or routing cost be:

```math
E(x)
```

An attractor basin is a region where iterative interpretation tends to descend toward a stable concept:

```math
x_{t+1}=F(x_t, A, R, S)
```

where:

| Symbol | Meaning |
|---|---|
| `A` | adapter set |
| `R` | evidence receipts |
| `S` | salt / namespace / schema context |
| `F` | routing and reinterpretation operator |

A semantic basin shaper modifies the landscape:

```math
E'(x)=E(x)+\Phi_{shape}(x)
```

or modifies the transition:

```math
x_{t+1}=F'(x_t,A,R,S,Q)
```

where `Q` is the shaping intervention.

---

## Examples of basin shapers

| Shaper | Effect |
|---|---|
| leading salt | separates causal universes |
| quarantine salt | isolates legacy or contaminated concepts |
| adapter boundary | prevents metaphor from applying outside its domain |
| evidence receipt | deepens legitimate basins |
| failure mode | raises the cost of invalid routing |
| negative test | prevents universalization of a motif |
| schema version | prevents old and new interpretations from collapsing |
| claim-state ladder | controls promotion pressure |
| residual metric | gives an attractor a quantitative test |
| provenance link | anchors concept to source context |

---

## Relationship to semantic attractor collapse

Semantic attractor collapse is the failure mode:

```text
motif recurrence becomes ontology without evidence gates
```

Semantic basin shaping is the control mechanism:

```text
change the route, evidence threshold, salt domain, or failure boundary so the motif cannot collapse domains without earning the merge
```

Together:

```text
attractor guardrails = stop false ontology merges
basin shapers       = steer concepts toward testable basins
```

---

## SCW-8192 integration

SCW-8192 acts as a basin shaper because the leading salt and witness body alter permissible interpretation paths.

```text
same concept + different salt = different basin
same concept + different adapter = different basin
same concept + different evidence state = different basin
same concept + quarantine flag = isolated basin
```

SCW-8192 must therefore bind:

- salt domain,
- schema version,
- adapter lineage,
- evidence state,
- quarantine state,
- mutation lineage,
- failure-mode receipts.

This prevents an attractive motif from automatically merging into the active ontology.

---

## Routing rule

```text
A concept may only move between basins when the receiving basin explicitly accepts its salt domain, adapter class, evidence state, and failure-mode profile.
```

If the target basin cannot validate those fields:

```text
route := quarantine_review
```

---

## Basin promotion ladder

| State | Meaning |
|---|---|
| `METAPHOR` | useful phrase or analogy, no formal adapter |
| `PROVISIONAL_BASIN` | adapter sketch exists |
| `TESTABLE_BASIN` | variables, failure modes, and negative tests exist |
| `CALIBRATED_BASIN` | evidence receipts support monotonic or predictive behavior |
| `REVIEWED_BASIN` | formal or externally reviewed support exists |
| `QUARANTINED_BASIN` | motif is too gravitational relative to receipts |

Promotion requires receipts.

Demotion requires only one serious contamination or ambiguity event.

---

## Basin pressure metric

Suggested risk score:

```math
B_{pressure}
=
\frac{F_{motif}\,D_{spread}\,P_{routing}}{1+E_{receipts}+N_{negative}+F_{failures}}
```

Where:

| Symbol | Meaning |
|---|---|
| `F_motif` | motif frequency |
| `D_spread` | number of unrelated domains using it |
| `P_routing` | how often it becomes the default route |
| `E_receipts` | evidence receipts |
| `N_negative` | negative tests |
| `F_failures` | explicit failure modes |

If:

```math
B_{pressure}>\theta_{basin}
```

then the concept must be reviewed for attractor collapse.

---

## Productive basin shaping

Not every shaper is defensive. Some shapers intentionally create better conceptual flow.

Examples:

```text
add a negative test
add a domain boundary
add a receipt requirement
split a concept into two adapters
rename a misleading metaphor
salt legacy context separately
force a calibration benchmark
require a simulation harness
```

These actions do not kill the concept. They reshape the basin so the concept becomes safer to use.

---

## Application to violently weird research systems

In a stable product, ordinary identifiers and ordinary tags are enough.

In OTOM-scale research, concepts can mutate quickly across math, physics, biology, compression, manufacturing, fluidics, and observability.

So the system needs explicit basin shapers because conceptual velocity is high.

```text
When conceptual velocity is high, semantic collisions arrive before hash collisions.
```

Semantic Basin Shapers exist to slow false merges without slowing legitimate synthesis.

---

## Forbidden inference

Invalid:

```text
This concept shapes many basins, therefore it is true.
```

Valid:

```text
This concept shapes many basins, therefore it needs stronger receipts, clearer domain boundaries, and explicit failure modes.
```

---

## Minimal implementation checklist

- [ ] Add `basin_state` to SCW companion receipts.
- [ ] Add `basin_id` or `basin_digest` to concept receipts.
- [ ] Add `basin_pressure` metric.
- [ ] Add quarantine route when `basin_pressure` exceeds threshold.
- [ ] Require adapter-specific receipts for cross-basin promotion.
- [ ] Record basin transitions in AMMR.
- [ ] Add tests for false motif merge, schema drift, and salt-domain mismatch.

---

## Summary

```text
Semantic Basin Shapers are how the system intentionally changes the interpretive landscape so that weird ideas remain usable, testable, quarantinable, and capable of safe mutation.
```

They are not proof. They are control surfaces for concept flow.
