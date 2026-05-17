# RRC Logogram Projection Formalism

Date: 2026-05-08

Status: formal scaffold with Lean-checked routing theorems.

Lean module:

```text
0-Core-Formalism/lean/Semantics/Semantics/RRCLogogramProjection.lean
```

Upstream executable bridge receipt:

```text
4-Infrastructure/shim/rrc_logogram_projection_bridge_receipt.json
```

Bridge receipt hash:

```text
83f44e8341788f6cbb2013704af2622f95f140b5a98402d69cd4ddde5ea88826
```

## Claim

The proven claim is deliberately narrow:

```text
A torn logogram can be projection-admissible after repair/quarantine while
remaining not merge-admissible.
```

This proves the control structure, not the truth of the represented equation.

## Objects

Let a compiled logogram receipt be:

```text
L =
  (shape,
   status,
   regime,
   payloadBound,
   contradictionWitness,
   tearBoundary,
   detachedMass,
   residualLane)
```

The Lean structure is:

```lean
structure LogogramReceipt where
  shape : RRCShape
  status : WitnessStatus
  regime : SemanticRegime
  payloadBound : Bool
  contradictionWitness : Bool
  tearBoundary : Bool
  detachedMass : Bool
  residualLane : Bool
```

## Axioms

### Axiom 1: Shape Admission

A logogram is type-admissible only when it has the declared RRC shape, candidate
witness status, and bounded payload:

```text
TypeAdmissible(L) :=
  L.shape = LogogramProjection
  and L.status = Candidate
  and L.payloadBound
```

Lean:

```lean
def typeAdmissible (r : LogogramReceipt) : Bool :=
  r.shape == RRCShape.logogramProjection &&
  r.status == WitnessStatus.candidate &&
  r.payloadBound
```

### Axiom 2: Tear Repair

A torn logogram has repair evidence only if it carries all four quarantine
witnesses:

```text
HasTearRepair(L) :=
  contradictionWitness
  and tearBoundary
  and detachedMass
  and residualLane
```

Lean:

```lean
def hasTearRepair (r : LogogramReceipt) : Bool :=
  r.contradictionWitness && r.tearBoundary && r.detachedMass && r.residualLane
```

### Axiom 3: Merge Admission Is Stricter Than Type Admission

A logogram may merge into ordinary route/tokenbook space only when it is
type-admissible and not a tearing regime:

```text
MergeAdmissible(L) :=
  TypeAdmissible(L)
  and L.regime != HorribleManifoldTearing
```

Lean:

```lean
def mergeAdmissible (r : LogogramReceipt) : Bool :=
  typeAdmissible r &&
  r.regime != SemanticRegime.horribleManifoldTearing
```

### Axiom 4: Projection Admission Allows Quarantine

A logogram may enter projection space if it is type-admissible and either not
torn, or torn with repair evidence:

```text
ProjectionAdmissible(L) :=
  TypeAdmissible(L)
  and (
    L.regime != HorribleManifoldTearing
    or HasTearRepair(L)
  )
```

Lean:

```lean
def projectionAdmissible (r : LogogramReceipt) : Bool :=
  typeAdmissible r &&
  (r.regime != SemanticRegime.horribleManifoldTearing || hasTearRepair r)
```

### Axiom 5: Torn Projections Use Quarantine Lane

The projection lane is normal for non-torn regimes and quarantine for torn
regimes:

```text
ProjectionLane(L) =
  quarantine_projection if L.regime = HorribleManifoldTearing
  normal_projection otherwise
```

Lean:

```lean
def projectionLane (r : LogogramReceipt) : ProjectionLane :=
  if r.regime == SemanticRegime.horribleManifoldTearing then
    ProjectionLane.quarantineProjection
  else
    ProjectionLane.normalProjection
```

## Theorems

### Theorem 1: Repaired Tear Projects

```text
ProjectionAdmissible(semanticTearReceipt) = true
```

Lean:

```lean
theorem semantic_tear_projects_after_repair :
    projectionAdmissible semanticTearReceipt = true := by
  native_decide
```

### Theorem 2: Repaired Tear Does Not Merge

```text
MergeAdmissible(semanticTearReceipt) = false
```

Lean:

```lean
theorem semantic_tear_does_not_merge :
    mergeAdmissible semanticTearReceipt = false := by
  native_decide
```

### Theorem 3: Repaired Tear Routes To Quarantine

```text
ProjectionLane(semanticTearReceipt) = quarantine_projection
```

Lean:

```lean
theorem semantic_tear_uses_quarantine_lane :
    projectionLane semanticTearReceipt = ProjectionLane.quarantineProjection := by
  native_decide
```

### Theorem 4: Unrepaired Tear Does Not Project

```text
ProjectionAdmissible(unrepairedTearReceipt) = false
```

Lean:

```lean
theorem unrepaired_tear_does_not_project :
    projectionAdmissible unrepairedTearReceipt = false := by
  native_decide
```

### Theorem 5: Merge Implies Projection

```text
MergeAdmissible(L) -> ProjectionAdmissible(L)
```

Lean:

```lean
theorem merge_implies_projection (r : LogogramReceipt) :
    mergeAdmissible r = true -> projectionAdmissible r = true
```

### Theorem 6: Repaired Tears Separate Projection From Merge

For any logogram receipt:

```text
TypeAdmissible(L)
and L.regime = HorribleManifoldTearing
and HasTearRepair(L)
implies
  ProjectionAdmissible(L)
  and not MergeAdmissible(L)
```

Lean:

```lean
theorem repaired_tear_separates_projection_from_merge
    (r : LogogramReceipt)
    (hType : typeAdmissible r = true)
    (hTear : r.regime = SemanticRegime.horribleManifoldTearing)
    (hRepair : hasTearRepair r = true) :
    projectionAdmissible r = true ∧ mergeAdmissible r = false
```

## Executable Witnesses

The module includes these `#eval` witnesses:

```text
projectionAdmissible semanticTearReceipt      -> true
mergeAdmissible semanticTearReceipt           -> false
projectionLane semanticTearReceipt            -> quarantineProjection
projectionAdmissible unrepairedTearReceipt    -> false
mergeAdmissible ordinaryLogogramReceipt       -> true
```

Observed build output:

```text
true
false
Semantics.RRCLogogramProjection.ProjectionLane.quarantineProjection
false
true
```

## What This Proves

The RRC/logogram layer now proves a routing invariant:

```text
type admission != projection admission != merge admission
```

The important preserved fact is:

```text
semantic tearing is not erased.
```

It is transformed into a quarantine projection with a residual/contradiction
witness, detached mass id, and explicit non-merge status.

## What This Does Not Prove

This formalism does not prove:

```text
the semantic meaning of the source logogram
the truth of the mathematical expression
compression gain on held-out corpora
physical reality of the manifold metaphor
```

Those require separate receipts and theorem surfaces.
