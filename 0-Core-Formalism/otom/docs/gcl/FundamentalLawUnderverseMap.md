# Fundamental Law Underverse Map

Status: HOLD / conceptual doctrine
Authority: workbench definition; not formal proof
Related:

- `docs/gcl/EquationUnderverseDoctrine.md`
- `docs/gcl/NonCompressedGoxelGeometryDoctrine.md`
- `docs/gcl/GoxelShapeRepresentationCollapseAddendum.md`
- `docs/gcl/HolyDiverGoxelMOIMBridge.md`

## Purpose

This document extends the Equation Underverse doctrine to fundamental laws.

The premise:

```text
Every fundamental law has an Underverse.
```

A law defines what is admissible.

Its Underverse defines what is excluded, impossible, unpaid, residual, unstable, unrepresented, or forbidden by that law.

## Core definition

For a law `L`:

```text
Underverse(L) = structured shadow of L
             = residual(L)
             + forbidden(L)
             + complement(L)
             + unpaid_cost(L)
             + failed_binding(L)
             + unrepresented_state(L)
```

In words:

```text
The Underverse of a law is the finite, typed, auditable space of the states that the law prevents, rejects, constrains, or leaves as residual in order for lawful behavior to exist.
```

## Positive / negative law split

```text
Positive law:
  what must hold
  what is conserved
  what transforms lawfully
  what cannot be exceeded
  what stabilizes

Underverse law:
  what cannot happen
  what is lost as residue
  what appears as forbidden route
  what debt must be paid
  what fails to bind
  what remains outside representation
```

## General law packet

Each law should be mapped to a bounded packet:

```text
LawUnderversePacket = {
  law_id,
  law_family,
  positive_statement,
  positive_invariant,
  underverse_shadow,
  forbidden_state,
  residual_type,
  unpaid_cost_type,
  collapse_mode,
  aci_test,
  warden_status
}
```

All hot-path metrics are fixed-point Q16.16 or integer-coded.

No float in core.

## Fundamental law families

This map uses broad law families rather than pretending to exhaust every theorem or empirical regularity.

```text
1. Conservation laws
2. Thermodynamic laws
3. Information laws
4. Relativistic / causal laws
5. Quantum laws
6. Field / gauge laws
7. Topological laws
8. Computation laws
9. Statistical / probabilistic laws
10. Dynamical systems laws
11. Geometric / variational laws
12. Biological / evolutionary constraints
```

## 1. Conservation laws

Positive side:

```text
energy, momentum, angular momentum, charge, and other conserved quantities remain balanced under lawful transformation.
```

Underverse:

```text
unpaid conservation debt
leakage
false creation
false deletion
hidden sink/source
aliasing of conserved quantity
invalid transfer receipt
```

Operational reading:

```text
If a route appears to create value, mass, charge, signal, or structure from nowhere, send it to the Underverse as conservation debt.
```

Packet:

```text
ConservationUnderverse = {
  missing_source,
  missing_sink,
  transfer_gap,
  hidden_reservoir,
  accounting_residual
}
```

## 2. Thermodynamic laws

Positive side:

```text
energy transformations pay entropy, heat, irreversibility, and efficiency costs.
```

Underverse:

```text
perpetual-motion route
unpaid entropy
impossible efficiency
heat debt
erasure debt
free-energy hallucination
metabolic cost hidden in substrate
```

Operational reading:

```text
If a process claims work, organization, compression, or recovery without paying cost, the missing cost becomes an Underverse packet.
```

Packet:

```text
ThermoUnderverse = {
  entropy_debt,
  heat_leak,
  impossible_efficiency_flag,
  free_energy_gap,
  erased_information_cost
}
```

## 3. Information laws

Positive side:

```text
messages have entropy, compression has limits, error correction has overhead, and information cannot be recovered after destructive loss without redundancy or prior structure.
```

Underverse:

```text
irreducible residue
uncompressible remainder
aliasing
lost context
checksum scar
hallucinated reconstruction
overfit codebook
unrecoverable bit history
```

Operational reading:

```text
Compression success must always carry a receipt for what was preserved, what was discarded, and what cannot be reconstructed.
```

Packet:

```text
InformationUnderverse = {
  entropy_residue,
  code_space_waste,
  reconstruction_gap,
  aliasing_class,
  checksum_scar
}
```

## 4. Relativistic / causal laws

Positive side:

```text
causal order, light-cone structure, invariant intervals, and local propagation constraints bound possible events.
```

Underverse:

```text
causal loop
forbidden shortcut
unpaid synchronization
frame-conflict residue
signal-before-source
invalid simultaneity assumption
```

Operational reading:

```text
If a route depends on information arriving before the admissible causal path, its shadow is a causal Underverse packet.
```

Packet:

```text
CausalUnderverse = {
  lightcone_violation,
  frame_residual,
  simultaneity_gap,
  shortcut_debt,
  chronology_risk
}
```

## 5. Quantum laws

Positive side:

```text
state evolution, measurement, uncertainty, exclusion, decoherence, and conservation constraints bound quantum behavior.
```

Underverse:

```text
unmeasured branch
decohered branch
forbidden state
which-path scar
uncertainty debt
noncommuting residue
invalid copy / no-cloning violation
```

Operational reading:

```text
A quantum-like route must record what was not measured, what decohered, and which incompatible observables cannot jointly be resolved.
```

Packet:

```text
QuantumUnderverse = {
  branch_shadow,
  decoherence_residue,
  measurement_scar,
  noncommuting_gap,
  forbidden_state_tag
}
```

## 6. Field / gauge laws

Positive side:

```text
fields evolve under local rules, symmetries, constraints, and gauge redundancies.
```

Underverse:

```text
broken symmetry residue
gauge artifact
unphysical degree of freedom
constraint violation
singular gauge patch
field mismatch at boundary
```

Operational reading:

```text
If a field representation depends on a coordinate artifact rather than an invariant, the artifact belongs to the Underverse.
```

Packet:

```text
GaugeUnderverse = {
  gauge_artifact,
  broken_symmetry_residue,
  constraint_gap,
  boundary_mismatch,
  singular_patch
}
```

## 7. Topological laws

Positive side:

```text
continuity, gluing, invariants, holes, boundaries, and equivalence classes constrain transformation.
```

Underverse:

```text
failed gluing
non-manifold collision
unresolved hole
boundary ambiguity
invalid quotient
orphan component
Betti mismatch
```

Operational reading:

```text
If two forms appear equivalent but their holes, components, or gluing receipts disagree, the disagreement becomes topological Underverse evidence.
```

Packet:

```text
TopologyUnderverse = {
  failed_gluing,
  betti_residual,
  boundary_ambiguity,
  nonmanifold_collision,
  orphan_component
}
```

## 8. Computation laws

Positive side:

```text
computation has finite steps, finite memory, complexity costs, decidability boundaries, and machine constraints.
```

Underverse:

```text
undecidable route
unbounded search
complexity debt
memory blowup
nontermination
oracle smuggling
invalid compression claim
```

Operational reading:

```text
If a route solves by hiding an oracle, infinite memory, or unbounded search, the hidden resource becomes computation Underverse debt.
```

Packet:

```text
ComputationUnderverse = {
  nontermination_risk,
  complexity_debt,
  memory_blowup,
  oracle_smuggling_flag,
  unbounded_search_gap
}
```

## 9. Statistical / probabilistic laws

Positive side:

```text
uncertainty, distributions, sampling, inference, error bars, and base rates constrain claims.
```

Underverse:

```text
selection bias
unpaid uncertainty
p-hacking shadow
base-rate neglect
false certainty
hidden multiple comparison
out-of-distribution scar
```

Operational reading:

```text
If a claim appears strong only because uncertainty was removed from view, the missing uncertainty is the statistical Underverse.
```

Packet:

```text
StatisticalUnderverse = {
  uncertainty_debt,
  selection_shadow,
  base_rate_gap,
  multiple_comparison_scar,
  ood_residue
}
```

## 10. Dynamical systems laws

Positive side:

```text
states evolve through flows, attractors, bifurcations, stability basins, chaos, and regime transitions.
```

Underverse:

```text
unstable basin
missed attractor
chaotic residue
unresolved bifurcation
delayed collapse
hysteresis scar
runaway feedback
```

Operational reading:

```text
If a system appears stable only by ignoring nearby basins or delayed feedback, the ignored basins are Underverse structure.
```

Packet:

```text
DynamicsUnderverse = {
  unstable_basin,
  bifurcation_shadow,
  hysteresis_scar,
  runaway_feedback_flag,
  attractor_miss
}
```

## 11. Geometric / variational laws

Positive side:

```text
systems often follow extremal, shortest, least-action, curvature, metric, or geodesic constraints.
```

Underverse:

```text
non-geodesic residue
metric mismatch
curvature debt
forbidden shortcut
failed projection
singular chart
unrepresented manifold branch
```

Operational reading:

```text
If a route claims a shortest or optimal path but the metric receipt does not support it, the missing curvature/metric data goes to the Underverse.
```

Packet:

```text
GeometryUnderverse = {
  metric_mismatch,
  curvature_debt,
  projection_failure,
  singular_chart,
  nongeodesic_residue
}
```

## 12. Biological / evolutionary constraints

Positive side:

```text
living systems obey energy budgets, replication constraints, selection pressure, repair limits, and ecological coupling.
```

Underverse:

```text
runaway replication
unpaid metabolism
failed repair
unfit mutation
fragile monoculture
immune escape
unbounded digital cell division
```

Operational reading:

```text
If a self-replicating or adaptive system grows without lineage, audit, cost, or immune gating, route it to biological Underverse review.
```

Packet:

```text
BioUnderverse = {
  metabolic_debt,
  repair_failure,
  runaway_replication_flag,
  lineage_gap,
  immune_escape_shadow
}
```

## Universal Underverse transform

For any fundamental law `L`, use:

```text
U_L(x) = classify_shadow(
  residual(x),
  forbidden_state(x),
  unpaid_cost(x),
  failed_binding(x),
  unrepresented_state(x)
)
```

A system is healthier when:

```text
positive_law_passes == true
and
underverse_debt is bounded, typed, and receipted
```

A system is dangerous when:

```text
positive_law_passes appears true
but
underverse_debt grows unbounded or untyped
```

## Underverse audit table

| Law Family | Positive Question | Underverse Question |
|---|---|---|
| Conservation | What is preserved? | What source/sink is hidden? |
| Thermodynamics | What cost is paid? | What cost is missing? |
| Information | What is encoded? | What residue is irreducible? |
| Causality | What can influence what? | What shortcut is forbidden? |
| Quantum | What state/measurement is valid? | What branch/scar remains? |
| Gauge/Field | What is invariant? | What is artifact? |
| Topology | What glues/continues? | What hole/collision remains? |
| Computation | What terminates within bounds? | What oracle/search is hidden? |
| Statistics | What is inferred? | What uncertainty was buried? |
| Dynamics | What attractor stabilizes? | What basin/runaway is ignored? |
| Geometry | What path/metric is valid? | What curvature/projection failed? |
| Biology | What adapts/replicates lawfully? | What runaway growth escaped audit? |

## Goxel relation

A Goxel can hold pre-representation manifold possibility.

The law Underverse tells the Goxel what cannot be allowed after collapse.

```text
Goxel phase:
  apparent law violations may exist as unresolved possibility

Partial compression:
  law shadows become measurable residuals

Representation collapse:
  fundamental-law Underverse packets must resolve, bind, quarantine, or fail validation
```

## ACI / Warden relation

```text
ACI checks local admissibility.
Warden checks systemic safety.
Underverse explains what each law forced into shadow.
```

A law pass without an Underverse receipt is incomplete.

A law fail with a bounded Underverse receipt is useful.

A law fail with unbounded Underverse growth is quarantine territory.

## Compact doctrine

```text
Fundamental laws are not only positive rules. They are shadow-generators.
Every law creates an Underverse: the finite, typed, auditable space of what
that law forbids, excludes, leaves residual, or forces into debt. Applying the
Underverse to fundamental laws turns impossibility, failure, absence, and
residual cost into first-class diagnostic objects rather than hidden error.
```
