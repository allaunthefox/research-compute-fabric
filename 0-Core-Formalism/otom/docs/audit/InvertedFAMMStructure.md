# Inverted FAMM Structure

## Purpose

This note defines an inverted FAMM structure as the dual of ordinary FAMM route-memory.

Ordinary FAMM records how validated routes become basins, hazardous failures become scars, and unresolved adapter stress becomes torsion.

Inverted FAMM reverses the question:

```text
Instead of asking: which routes became lawful basins?
Ask: which basins, scars, or torsion fields predict missing routes, hidden constraints, or adversarial shortcuts?
```

## Core Statement

```text
FAMM = forward route memory from traversal outcomes
Inverted FAMM = inverse inference from memory geometry back to missing laws, hidden bottlenecks, and absent receipts
```

The inverted structure is not anti-evidence. It is an error-field and negative-space analyzer.

## Forward FAMM

Forward FAMM update:

```text
route traversal -> receipt -> PASS/HOLD/SCAR/QUARANTINE/MISSING -> basin/scar/torsion update
```

Forward state:

```text
FAMM_r = {
  basin_strength,
  scar_strength,
  unresolved_torsion,
  evidence_mass,
  provenance_integrity,
  loss_budget,
  repair_capacity,
  finite_witness_count,
  validator_status,
  last_outcome
}
```

## Inverted FAMM

Inverted FAMM performs inverse reconstruction:

```text
basin/scar/torsion field -> infer missing receipt / hidden constraint / absent bridge / unstable law boundary
```

Inverted state:

```text
IFAMM_q = {
  missing_law_pressure,
  hidden_constraint_score,
  inverse_route_likelihood,
  scar_shadow_strength,
  basin_boundary_gradient,
  torsion_source_estimate,
  adversarial_shortcut_risk,
  counterexample_pressure,
  receipt_deficit,
  suggested_probe
}
```

## Interpretive Meaning

### Basin inversion

A strong basin with a sharp boundary implies an undiscovered constraint:

```text
high basin_strength + sharp basin_boundary_gradient -> hidden law boundary candidate
```

Use:

```text
find the invariant that explains why lawful routes cluster here and fail nearby
```

### Scar inversion

A repeated scar pattern implies a possible negative theorem, forbidden transition, or missing adapter:

```text
repeated scar geometry -> obstruction candidate
```

Use:

```text
extract common failure invariant
```

### Torsion inversion

Unresolved torsion that accumulates without becoming a scar implies an incomplete bridge:

```text
persistent torsion + nonfatal loss -> missing receipt / missing metric / missing transfer operator
```

Use:

```text
ask what receipt would convert HOLD into PASS or SCAR
```

### Quarantine inversion

Repeated quarantine can indicate adversarial compression, invalid evidence promotion, or route spoofing:

```text
quarantine cluster -> trust-boundary defect
```

Use:

```text
separate genuine missing evidence from unsafe inference route
```

## Inverted Update Law

Given a region of route-memory state `R`, compute:

```text
MissingLawPressure(R) =
  w_t * unresolved_torsion
  + w_s * scar_shadow_strength
  + w_b * basin_boundary_gradient
  + w_m * missing_receipt_count
  - w_v * validator_coverage
```

A high value means the system should search for a missing law, invariant, proof obligation, or empirical measurement.

## Negative-Space Probe

The inverted system emits probes instead of conclusions:

```text
probe = {
  suspected_missing_receipt,
  route_region,
  failure_cluster,
  candidate_invariant,
  minimum_test,
  expected_disambiguation,
  risk_if_ignored
}
```

Probe examples:

```text
Need DifferenceSetReceipt for this spectral candidate.
Need finite-window active-cell count before density promotion.
Need LandauerCostReceipt because route claims information deletion without dissipation.
Need dimensional calibration because raw temperature was mixed with dimensionless loss.
Need nonseparable encoding because spectral voids do not prove Sidon sums.
```

## Relation to Current Pipeline

Forward pipeline:

```text
finite signal
-> FFT/Hodge/Dirac filter
-> remainder resonance candidate set
-> void/topological defect receipt
-> active-cell set
-> nonseparable encoding
-> Sidon audit
-> crossing receipt
-> FAMM update
```

Inverted pipeline:

```text
FAMM memory field
-> locate scar/torsion/basin gradients
-> infer missing receipt or hidden invariant
-> generate finite probe
-> run measurement/proof/search
-> update FAMM with result
```

## Main Use Cases

```text
counterexample discovery
missing receipt detection
hidden invariant extraction
adversarial route detection
negative-space search
proof-obligation prioritization
model drift detection
research question refinement
```

## Inverted FAMM Gates

```text
IFAMM_PASS: predicted missing receipt was found and validated
IFAMM_HOLD: missing route is plausible but underconstrained
IFAMM_SCAR: predicted route collapses into a repeatable obstruction
IFAMM_QUARANTINE: inverse route exploits evidence gap or unsafe promotion path
IFAMM_MISSING: not enough finite evidence to form a probe
```

## Boundary

Inverted FAMM cannot promote a claim by itself.

Correct role:

```text
Inverted FAMM finds where the project should look next.
It identifies missing laws, missing receipts, hidden constraints, and likely counterexamples.
```

Incorrect role:

```text
Inverted FAMM proves the theorem.
Inverted FAMM converts scars into evidence.
Inverted FAMM treats absence of failure as proof.
```

## Audit Classification

```text
Receipt: InvertedFAMMStructure
Status: ARCHITECTURE_DRAFT
Gate: U_scope
Reason: coherent as a negative-space route-memory analyzer, but it requires explicit finite scoring functions, probe-generation rules, validator wiring, and safeguards against promoting absence-of-evidence into evidence.
```

## Required Receipts

```text
FAMMStateReceipt
BasinBoundaryGradientReceipt
ScarClusterReceipt
TorsionSourceReceipt
MissingReceiptDetector
CounterexampleProbeReceipt
AdversarialShortcutReceipt
FiniteProbeReceipt
ValidatorReceipt
FAMMUpdateReceipt
```
