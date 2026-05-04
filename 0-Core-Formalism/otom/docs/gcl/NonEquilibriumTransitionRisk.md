# Non-Equilibrium Transition Risk

Status: HOLD / workbench projection
Authority: risk doctrine and architecture bridge; not prediction proof
Related: `docs/gcl/SuperorganismCollectiveBasinBridge.md`, `docs/gcl/ForestPathGoxelModel.md`, `docs/gcl/EquationForestActiveKernels.md`, `docs/gcl/BettiNumbersInEquationForest.md`

## Purpose

This document defines the transition-risk doctrine:

```text
We are in a dangerous transition period because equilibrium-seeking systems are trying to stabilize inside a non-equilibrium state.
```

The point is not apocalyptic rhetoric.

The point is systems diagnosis: many human, institutional, technological, ecological, economic, and symbolic systems are attempting to find equilibrium while their constraint fields are changing faster than their stabilizers can converge.

## Core thesis

```text
Maximum danger occurs when:
  stabilization demand is high
  but the substrate is still moving
```

In other words:

```text
system seeks equilibrium
  while environment remains non-equilibrium
  -> false-stable states
  -> oscillation
  -> brittle lock-in
  -> runaway correction
  -> collapse or phase transition
```

## Non-Equilibrium Equilibrium Seeking

Define:

```text
NEES = Non-Equilibrium Equilibrium Seeking
```

NEES occurs when an adaptive system attempts to converge before the underlying regime has stabilized.

```text
NEES(system, regime) iff
  system attempts stabilization
  and regime constraints are still changing
  and feedback delay exceeds safe correction window
```

## Why this is dangerous

A system under NEES may mistake temporary local relief for global stability.

Failure modes:

```text
false equilibrium
  a temporary basin looks stable but vanishes when constraints shift

overshoot
  correction is calibrated to an old regime and pushes too far

brittle lock-in
  system freezes around the wrong attractor

feedback inversion
  stabilizing action becomes destabilizing because the state changed

coordination lag
  distributed nodes update at incompatible speeds

semantic collapse
  shared symbols lose routing power faster than replacements form

authority lag
  mainframe-style institutions respond too slowly for distributed topology
```

## Relation to self-healing topology

Self-healing topology is the desired response to NEES.

```text
blocked path
  -> alternate route
  -> audit
  -> repair
  -> receipt
  -> promotion or quarantine
```

But during transition, the topology may not yet be self-healing enough.

```text
transition danger = old stabilizers failing before new repair topology matures
```

## Mainframe-to-topology transition

The risk is intensified by an infrastructure transition:

```text
mainframe-style cognition / authority
  -> centralized symbolic machinery
  -> slow validation and routing

self-healing semantic topology
  -> distributed symbolic participation
  -> faster discovery and repair
  -> higher risk of false consensus unless gated
```

The transition is dangerous because both systems coexist.

```text
old system too slow
new system too noisy
shared equilibrium not yet found
```

## Semantic basin risk

Semantic basins help agents compress meaning.

But in non-equilibrium conditions, basins can become unstable.

```text
healthy basin:
  reduces routing load
  preserves auditability
  supports repair

unhealthy basin:
  reduces anxiety without preserving truth
  becomes viral symbol
  bypasses receipts
  collapses criticism into identity threat
```

## GCL placement

GCL should encode transition-risk claims as held, scoped, and receipt-demanding.

```text
transition-risk observation
  -> GCL claim object
  -> regime tag
  -> affected systems
  -> failure modes
  -> evidence receipts
  -> gates
```

Minimum fields:

```text
claim_state: HOLD
authority_scope: workbench_projection or receipt_backed
regime: declared
systems_affected: declared
failure_modes: declared
receipts: present or missing
blocked_usages: declared
```

## Equation Forest placement

Useful kernels:

```text
RGFlow_Admissibility
  scale-stability / attractor check

NII_Surprise
  prediction residual / novelty spike

Shannon_Entropy
  uncertainty and compression pressure

Landauer_Bound
  finite cost of information erasure / reset

Carnot_Efficiency
  thermodynamic efficiency boundary

Burgers / Navier-Stokes
  shock, turbulence, viscosity, smoothing analogies for transition flow
```

Boundary:

```text
equation-shaped analogy != prediction proof
```

## Betti placement

Betti numbers can audit transition topology.

```text
beta_0 increases
  fragmentation / disconnected semantic islands

beta_1 increases
  loops / circular discourse / unresolved route cycles

beta_2 increases
  enclosed voids / unanswered trapped problem spaces
```

A dangerous transition may show:

```text
high beta_0 fragmentation
high beta_1 discourse loops
persistent beta_2 voids
low receipt density
high residual pressure
```

## Metrics to track

Candidate metrics:

```ts
type TransitionRiskMetrics = {
  residual_pressure: number;
  feedback_delay: number;
  correction_overshoot_rate: number;
  basin_volatility: number;
  receipt_density: number;
  projection_artifact_rate: number;
  semantic_fragmentation_beta0: number;
  discourse_loop_beta1: number;
  unresolved_void_beta2: number;
  repair_success_rate: number;
};
```

Interpretation:

```text
high residual_pressure + low receipt_density
  -> narrative instability risk

high feedback_delay + high correction_overshoot_rate
  -> institutional instability risk

high basin_volatility + high projection_artifact_rate
  -> symbol/meaning instability risk

high repair_success_rate
  -> self-healing topology is maturing
```

## Safety boundary

Do not use this doctrine to claim certainty about collapse, destiny, apocalypse, or inevitable disaster.

Use it to identify risk conditions and repair targets.

```text
high danger != guaranteed collapse
transition instability != prophecy
non-equilibrium != hopelessness
risk doctrine != fear doctrine
```

## Repair strategy

The repair strategy is not to force premature equilibrium.

It is to increase adaptive capacity while preserving auditability.

```text
1. Keep multiple admissible routes open.
2. Label unstable basins as unstable.
3. Increase receipt density.
4. Reduce projection/proof confusion.
5. Preserve local autonomy while improving interoperability.
6. Detect loops, voids, and fragmentation.
7. Promote only through gates.
8. Quarantine viral but ungrounded attractors.
```

## Operating sentence

```text
The transition is dangerous because systems are seeking equilibrium while the regime is still non-equilibrium; the correct response is not premature stabilization, but self-healing topology with receipts, gates, and repairable routes.
```
