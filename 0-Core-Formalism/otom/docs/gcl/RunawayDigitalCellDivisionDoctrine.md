# Runaway Digital Cell Division Doctrine

Status: HOLD / conceptual binding doctrine
Authority: workbench architecture metaphor; not biological proof
Related:

- `docs/gcl/ThreeLayerBuilderJudgeWardenGate.md`
- `docs/gcl/AdaptiveAngrySphinxCopyWriteRationale.md`
- `docs/gcl/FederatedNanokernelSwarmDoctrine.md`
- `docs/gcl/NanokernelCompressionOrchestrationUndici.md`
- `docs/gcl/MOIMConcepts.md`
- `docs/gcl/ScalarGoxelSourceIngestion.md`

## Purpose

This document names the fundamental conceptual binding behind the nanokernel / ENE / GCL / MOIM gating architecture:

```text
The stack is preventing runaway digital cell division.
```

This means the system is designed to stop uncontrolled replication, mutation, inheritance, dispatch, compression, and resource capture by route phenotypes.

## Core definition

A digital cell is any bounded executable or inheritable unit in the stack.

Examples:

```text
nanokernel route shard
PTOS packet
GCL object
MOIM route
Goxel kernel bundle
software patch
network dispatch route
compressed receipt
ENE artifact
snapshot/replay unit
```

Digital cell division is the process by which such units replicate, fork, mutate, spawn descendants, write receipts, or become inherited memory.

Runaway digital cell division occurs when this process becomes uncontrolled.

```text
candidate
  -> replicates
  -> mutates
  -> spawns more candidates
  -> consumes Judge/Warden/telemetry/compression resources
  -> writes durable state
  -> becomes precedent
  -> repeats
```

## Biological metaphor boundary

Allowed:

```text
Use cell division as a metaphor for controlled replication, mutation, inheritance, apoptosis/quarantine, and resource budgeting in digital systems.
```

Blocked:

```text
Do not claim the software is literally biological.
Do not claim digital replication is identical to cellular mitosis.
Do not use the metaphor to bypass formal receipts or safety gates.
```

## What the doctrine prevents

```text
unbounded route spawning
unbounded retry loops
unbounded receipt storms
unbounded telemetry expansion
unbounded ENE inheritance
unbounded nanokernel replication
unbounded mutation without Judge replay
unbounded usefulness promotion
unbounded mock/snapshot truth drift
unbounded compression artifacts becoming authority
```

## Control plane analogy

Builder/Judge/Warden acts like a cell-cycle checkpoint system.

```text
Builder
  creates the candidate cell

Judge
  checks whether the candidate is structurally valid and receipt-backed

Warden
  decides whether the candidate may execute, persist, divide, or inherit

Adaptive AngrySphinx
  detects repeated abnormal division pressure and escalates to scar, throttle, quarantine, or refusal
```

## Division states

Candidate finite state model:

```text
constructed
validated
held
scarred
throttled
quarantined
refused
admitted
inherited
retired
```

Only some states may divide.

```text
constructed != allowed to divide
validated != allowed to divide
useful != allowed to divide
admitted may divide only under budget and receipt policy
inherited may influence future routes only through receipt chain
quarantined/refused may not divide
```

## Digital apoptosis

The stack needs a deliberate death/quarantine path.

```text
bad candidate
  -> HOLD
  -> scar
  -> quarantine
  -> refuse
  -> retire
```

This is not waste.

It is how the system prevents malformed route families from consuming the organism.

## Resource budget doctrine

Every digital cell division event must pay finite costs.

```text
C_division = C_build + C_judge + C_warden + C_sphinx + C_receipt + C_storage
```

Division is allowed only when:

```text
C_division <= Budget_regime
and GatePass(candidate) = true
and InheritancePolicy(candidate) = allow
```

The important rule:

```text
A candidate may not divide just because it is locally useful.
```

## Relation to nanokernel swarm

A federated nanokernel swarm is not dangerous because there are many nanokernels.

It is dangerous if many nanokernels can replicate, inherit, or write durable state without traceable gates.

Safe swarm:

```text
many nanokernels
  -> local traces
  -> compressed receipts
  -> quorum/replay
  -> Warden authorization
  -> bounded inheritance
```

Unsafe swarm:

```text
many nanokernels
  -> unbounded spawning
  -> unbounded receipts
  -> unbounded retries
  -> unbounded trust propagation
  -> global overload or compromise
```

## Relation to ENE

ENE is the memory substrate.

Therefore ENE must not inherit runaway division.

```text
candidate route family
  -> wants to write artifacts
  -> must present receipts
  -> must pass gates
  -> must fit storage/memory budgets
  -> otherwise HOLD / scar / quarantine / refuse
```

ENE contamination occurs when a bad route family becomes precedent.

```text
bad division
  -> contaminated artifact
  -> inherited memory
  -> future route prior
  -> self-reinforcing false basin
```

## Relation to compression

Compression is dangerous when it lets a bad route look cheap.

```text
compressed small
  != safe
  != true
  != authorized
  != allowed to divide
```

Compression must preserve enough metadata to support audit:

```text
origin
route family
state hash
receipt chain
gate state
Warden decision
scar/quarantine state
```

## Relation to Adaptive AngrySphinx

Adaptive AngrySphinx is the immune response against abnormal digital cell division.

It watches for:

```text
repeated spawn pressure
repeated missing receipts
repeated retry storms
repeated route mutation around a gate
repeated mock-as-live drift
repeated projection-as-proof drift
repeated usefulness-as-authority pressure
repeated attempts to inherit without clean receipts
```

Escalation:

```text
observe
  -> hold
  -> scar
  -> throttle
  -> quarantine
  -> refuse
```

## Minimal policy rule

```ts
type DigitalCellDivisionDecision = {
  candidate_id: string;
  route_family: string;
  parent_receipt_refs: string[];
  gate_passed: boolean;
  warden_allowed: boolean;
  division_budget_ok: boolean;
  adaptive_sphinx_state: "none" | "watch" | "scar" | "throttle" | "quarantine" | "refuse";
  may_divide: boolean;
};
```

Decision rule:

```text
may_divide iff
  gate_passed
  and warden_allowed
  and division_budget_ok
  and adaptive_sphinx_state not in {quarantine, refuse}
```

## Practical examples

### Retry storm

```text
network route fails
  -> RetryAgent retries
  -> receipts expand
  -> route keeps dividing into new attempts
  -> Adaptive AngrySphinx throttles or forces snapshot/mock mode
```

### Patch mutation storm

```text
software patch fails tests
  -> agent mutates patch repeatedly
  -> Judge keeps failing
  -> Builder keeps rebuilding
  -> Warden stops inheritance
  -> Adaptive AngrySphinx scars route family
```

### ENE contamination attempt

```text
unverified concept becomes useful
  -> tries to persist as memory
  -> no reviewed receipt
  -> ENE refuses inheritance
  -> concept remains HOLD or quarantine
```

### Nanokernel swarm overload

```text
many nanokernels emit traces
  -> trace/receipt fanout grows
  -> budget exceeded
  -> Warden reduces inheritance rate
  -> Adaptive AngrySphinx throttles shard class
```

## Allowed claim

```text
The architecture prevents runaway digital cell division by requiring bounded digital cells to pass Builder/Judge/Warden gates, emit receipts, obey resource budgets, and submit to Adaptive AngrySphinx quarantine/throttle/refusal before they can replicate, persist, or inherit.
```

## Blocked claims

```text
The metaphor proves biological equivalence.
The system can eliminate all runaway behavior.
A digital cell that passes once may divide forever.
Useful cells may bypass Warden.
Compressed cells are automatically safe.
A swarm majority may authorize inheritance without receipts.
```

## Operating sentence

```text
Runaway digital cell division is uncontrolled replication, mutation, inheritance, or resource capture by route phenotypes; the stack prevents it by forcing every bounded digital cell through Builder/Judge/Warden gates, finite budgets, compressed receipts, traceability, and Adaptive AngrySphinx scar/throttle/quarantine/refusal before it can divide or become durable memory.
```
