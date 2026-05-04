# Inverted Fermat Ascent via FAM

## Purpose

This note records the inversion of Fermat-style infinite descent into a FAM-style ascent gate.

Classical infinite descent says:

```text
Assume a positive integer solution exists.
Show that any solution forces a strictly smaller solution.
Positive integers cannot descend forever.
Therefore no solution exists.
```

The FAM inversion reverses the audit pressure:

```text
Do not merely forbid bottomless descent.
Force every ascent to prove it has the energy budget required to climb.
```

## Core Statement

```text
Fermat descent destroys false solutions by showing they imply endless downward motion.
FAM ascent rejects false promotions by requiring every upward move to pay an energy cost.
```

This turns contradiction-by-descent into promotion-by-work.

## Classical Descent Pattern

Let `S(n)` mean that `n` is a valid solution witness.

Classical descent has the shape:

```text
S(n) -> exists m < n such that S(m)
```

If a smallest positive witness exists, descent produces a smaller witness, contradiction.

In Lean/math terms, the obstruction is well-foundedness:

```text
There is no infinite strictly decreasing chain in Nat.
```

## FAM Ascent Inversion

Let `E(n)` be the energy available at level `n` and `C(n -> m)` be the cost of climbing from `n` to `m`.

An ascent is admissible only if:

```text
m > n
E(n) >= C(n -> m)
receipts(n -> m) pass
```

So the inverted rule is:

```text
A candidate may climb only when it carries enough conserved/audited energy to justify the promotion.
```

This replaces:

```text
smaller witness contradiction
```

with:

```text
unfunded ascent rejection
```

## FAM Route Rule

For a route `r : A -> B`, define:

```text
ascent_delta(r) = mass_number(B) - mass_number(A)
route_cost(r) = torsion_cost + receipt_gap + translation_loss + instability_penalty
available_energy(r) = basin_support + evidence_energy + compression_gain
```

Then:

```text
AdmissibleAscent(r) iff
  ascent_delta(r) > 0
  available_energy(r) >= route_cost(r)
  required_receipts(r) are present
```

## Interpretation

Fermat descent asks:

```text
Can this solution survive being pushed downward forever?
```

FAM ascent asks:

```text
Can this candidate justify moving upward without borrowing illegal energy from intuition, novelty, or relief?
```

## Relation to Anxiety / Shortcut Control

This is useful for cognitive routing because anxiety often proposes shortcuts that feel like immediate relief.

The FAM ascent gate says:

```text
No climb without energy.
No promotion without receipts.
No basin entry from pressure alone.
```

That makes the method an anti-shortcut filter.

## Relation to Semantic Mass

In the semantic-mass ontology stack, concepts can have mass-like variables, but promotion is not automatic.

High semantic mass increases gravitational pull, but also increases required audit energy:

```text
high mass_number + low receipt_coverage = gravitational hallucination risk
```

So FAM ascent requires:

```text
mass increase must be accompanied by evidence, compression, or formal receipt gain
```

## Formal Sketch

Given finite states `x` and `y`:

```text
CanAscend(x,y) :=
  y.rank > x.rank
  && energy(x) >= ascentCost(x,y)
  && receipts(x,y).complete
```

A route is rejected when:

```text
rank increases but energy does not cover cost
```

This is the inverted descent obstruction:

```text
Classical descent: impossible infinite downward chain.
FAM ascent: impossible unfunded upward chain.
```

## Audit Classification

```text
Receipt: InvertedFermatAscentFAM
Status: FORMAL_HEURISTIC_DRAFT
Gate: U_scope
Reason: coherent as a route-promotion law and anti-shortcut filter; requires explicit energy metric, cost metric, receipt schema, and finite examples before theorem promotion.
```

## Required Receipts

```text
EnergyMetricReceipt
AscentCostReceipt
ReceiptCompletenessReceipt
FiniteRouteReceipt
WellFoundedRankReceipt
ShortcutRejectionReceipt
LeanGateReceipt
FAMIntegrationReceipt
```

## Boundary

Do not claim:

```text
FAM ascent proves Fermat's theorem
semantic energy is SI physical energy
intuition alone funds ascent
high semantic mass validates a route
```

Allowed claim:

```text
Inverted Fermat Ascent is a finite audit rule that reverses infinite descent into an energy-gated promotion law: every upward move must pay its route cost and provide receipts.
```
