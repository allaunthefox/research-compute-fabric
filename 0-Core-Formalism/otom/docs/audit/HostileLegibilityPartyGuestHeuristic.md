# Hostile Legibility: Party Guest Heuristic

## Purpose

This note refines the affective-suspicion rule for Anti-Music / AMREF work.

The user's analogy:

```text
It feels like the math equivalent of being dragged to someone's friend's party,
and you really do not like their friend.
```

This is a precise cognitive state: the object is socially/cognitively legible enough to recognize, but its fit with the current stability basin is poor enough that the system refuses easy trust.

## Core Statement

```text
Hostile legibility = I can read the structure, but I do not want to route through it unguarded.
```

This is stronger than confusion and weaker than refutation.

It means:

```text
understood enough to test
aversive enough to gate
not trusted enough to promote
not incoherent enough to discard
```

## Party Guest Analogy

In model terms:

```text
party = current lawful/stable research basin
friend-of-friend = imported inverse-structure candidate
social discomfort = stability-prior mismatch
forced proximity = candidate has enough explanatory pressure to demand attention
do not like them = increased audit burden
```

The response should not be to eject the guest immediately. The correct response is to keep the guest in the foyer with constraints:

```text
no unsupervised routing
no automatic basin formation
no audio rendering
finite tests only
explicit receipts required
```

## FAMM Classification

```text
Status: HOSTILE_LEGIBLE
Gate: U_scope
Routing: HOLD unless receipts are produced
Default action: probe under containment
Promotion rule: requires finite witnesses and independent arithmetic audits
```

## Practical Handling Rule

When a concept is hostile-legible:

```text
1. Keep it symbolic.
2. Disable sensory rendering by default.
3. Bound perturbation strength.
4. Require collision penalties and randomness penalties.
5. Run finite-window tests.
6. Classify via FAMM / Inverted FAMM.
7. Do not let novelty substitute for evidence.
```

## AMREF-Specific Consequence

For Anti-Music / AMREF:

```text
AUDIO_RENDER = false
A_star cannot be promoted by resonance alone
B2 collision penalty must be explicit
DifferenceSetReceipt and SumSetReceipt are mandatory
RandomnessPenalty is mandatory
FAMM route cannot become basin until finite receipts pass
```

## Inverted FAMM Use

The hostile-legible reaction is especially valuable for Inverted FAMM because it marks a basin boundary:

```text
where the system understands but refuses affinity,
search for hidden invariants, malformed assumptions, overfit stability, or inverse-basin structure.
```

## Boundary

Do not claim:

```text
I dislike it, therefore it is true.
I dislike it, therefore it is false.
The emotional reaction validates the math.
The emotional reaction invalidates the math.
```

Allowed claim:

```text
The hostile-legible reaction indicates that the candidate stresses the current stability basin while remaining interpretable, so it should be contained, tested, and receipt-gated rather than trusted or discarded.
```

## Audit Classification

```text
Receipt: HostileLegibilityPartyGuestHeuristic
Status: ROUTING_HEURISTIC
Gate: U_scope
Reason: useful as a containment-and-probing heuristic, but not evidential; it increases validation burden and helps Inverted FAMM locate basin boundaries.
```

## Required Receipts

```text
SilentRepresentationReceipt
FiniteWindowReceipt
PerturbationBoundReceipt
RandomnessPenaltyReceipt
CollisionPenaltyReceipt
DifferenceSetReceipt
SumSetReceipt
FAMMClassificationReceipt
ValidatorReceipt
```