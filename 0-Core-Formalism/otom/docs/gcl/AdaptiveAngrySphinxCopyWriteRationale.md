# Adaptive AngrySphinx Copy/Write and Overload Rationale

Status: HOLD / rationale note
Authority: security-economics and overload-control doctrine; not formal proof
Related:

- `docs/gcl/ThreeLayerBuilderJudgeWardenGate.md`
- `docs/gcl/NanokernelCompressionOrchestrationUndici.md`
- `docs/gcl/SovereignSurfaceRouterTelemetryIngestion.md`
- `docs/gcl/MOIMConcepts.md`

## Purpose

This note records the motivating intuition behind Adaptive AngrySphinx:

```text
Adaptive AngrySphinx is a sane measure.
It pays a small finite cost to prevent unchecked shortcuts from becoming durable inherited state.
It also prevents malformed, ambiguous, or adversarial route pressure from overloading the whole system.
```

The mental model is Linux-kernel-style copy/write flaw prevention plus load shedding.

A small per-boundary validation cost is cheaper than allowing a low-level state transition to silently become owned, persistent, inherited, or system-exhausting.

## Core doctrine

```text
Adaptive AngrySphinx is not paranoia.
It is finite immune cost against unbounded cleanup cost and total-system overload.
```

Or:

```text
A small adaptive refusal tax is rational when the cost of inherited compromise or overload is much larger than the cost of checking, scarring, throttling, redacting, refusing, or shedding load.
```

## Compartmentalization doctrine

A flaw in one layer must not compromise all layers.

```text
local flaw
  -> local containment
  -> scar / hold / quarantine / refusal
  -> no automatic cross-layer inheritance
```

This is the reason Builder, Judge, Warden, and Adaptive AngrySphinx remain separated.

```text
Builder compromise must not imply Judge trust.
Judge mistake must not imply Warden permission.
Warden permission must not imply future inheritance without receipt.
Adaptive AngrySphinx escalation must not erase the need for evidence.
```

The desired failure mode is degradation, not collapse:

```text
one layer fails
  -> route loses authority
  -> other layers tighten gates
  -> system remains bounded
```

The prohibited failure mode is cascade ownership:

```text
one layer fails
  -> route becomes trusted everywhere
  -> compressed receipt inherits false state
  -> ENE stores contaminated memory
  -> future routes treat compromise as precedent
```

## Copy/write flaw analogy

A copy/write flaw class is dangerous because the vulnerable transition often looks mundane:

```text
copy data
write state
commit result
inherit state
```

The disaster appears when one of those steps silently crosses a boundary:

```text
untrusted -> trusted
partial -> committed
temporary -> persistent
mock -> live
snapshot -> current truth
useful -> authorized
unchecked -> inherited
finite route -> runaway loop
local confusion -> global overload
local flaw -> cross-layer compromise
```

Adaptive AngrySphinx exists to prevent those boundary crossings from becoming normal.

## Total-system overload doctrine

Adaptive AngrySphinx also prevents system overload.

Malformed or ambiguous routes can consume the whole stack by forcing repeated construction, validation, repair, retry, compression, and telemetry loops.

```text
repeated malformed route
  -> Builder rebuilds
  -> Judge revalidates
  -> Warden rechecks
  -> Retry repairs
  -> telemetry expands
  -> receipts multiply
  -> ENE stores scars
  -> system load rises
```

Without an adaptive refusal layer, the stack can become owned by resource pressure even without a successful exploit.

```text
not owned by payload
owned by overload
```

Adaptive AngrySphinx breaks this pattern by turning repeated unresolved pressure into a finite state:

```text
repeat pressure
  -> scar
  -> throttle
  -> quarantine
  -> refuse
  -> stop expanding
```

## Nanokernel reading

In nanokernel terms, a copy/write-style flaw or overload flaw is not merely a memory bug.

It is a route-ownership failure:

```text
candidate route
  -> malformed or under-validated transition
  -> repeated repair / retry / rebuild pressure
  -> written into durable state or consumes finite resources
  -> later treated as trusted inheritance or keeps the system busy forever
```

That is exactly what Builder/Judge/Warden is designed to block.

Adaptive AngrySphinx adds the adaptive part:

```text
if the same boundary-crossing or overload pattern repeats,
  increase friction
  demand stronger receipts
  shed load
  write a scar
  throttle the route family
  quarantine or refuse the route family
```

## Sane measure sentence

Canonical sentence:

```text
Adaptive AngrySphinx is a sane measure: it pays a small finite cost to prevent unchecked shortcuts from becoming durable inherited state or total-system overload.
```

Security-economics sentence:

```text
The stack pays Builder/Judge/Warden/AngrySphinx overhead the same way a kernel pays copy/write checks: the local cost is small, but the avoided ownership, persistence, leakage, and overload failures are catastrophic.
```

Compartmentalization sentence:

```text
The stack isolates flaws by layer so one mistake degrades one route instead of authorizing compromise across the whole manifold.
```

## Boundary classes to protect

Adaptive AngrySphinx should watch transitions where the state class changes:

```text
untrusted_input -> trusted_state
partial_packet -> active_route
mock_result -> live_truth
snapshot_replay -> current_external_claim
projection -> theorem
telemetry -> proof
useful_behavior -> authorized_behavior
secret_bearing_data -> persistent_receipt
volatile_experiment -> inherited_memory
local_failure -> global_retry_loop
single_bad_candidate -> route_family_overload
repeated_confusion -> system_resource_drain
local_layer_flaw -> cross_layer_compromise
```

These are the copy/write, overload, and compartment-break boundaries of the research stack.

## Resource price framing

Each gate layer pays a different small price:

```text
Builder pays construction checks.
Judge pays validation checks.
Warden pays boundary checks.
Adaptive AngrySphinx pays repeated-pattern and overload checks.
```

This is acceptable because:

```text
C_gate << ExpectedLoss_owned_or_overloaded
```

where:

```text
C_gate = finite overhead of checking, redacting, scarring, throttling, refusing, or shedding load
ExpectedLoss_owned_or_overloaded = cost of inherited compromise, leaked secrets, corrupted memory, trusted falsehood, system exhaustion, or cross-layer cascade
```

## Practical examples

### Partial commit

```text
partial PTOS packet
  -> tries to update active route
  -> Builder/Judge/Warden blocks commit
  -> Adaptive AngrySphinx scars repeated mutation around same gate
```

### Mock treated as live

```text
MockAgent response
  -> passes test
  -> someone treats it as live external truth
  -> Warden blocks claim
  -> Adaptive AngrySphinx escalates if repeated
```

### Snapshot treated as current truth

```text
Snapshot replay
  -> deterministic receipt
  -> later claimed as current network truth
  -> Warden blocks overclaim
  -> Adaptive AngrySphinx writes projection-as-proof scar
```

### Useful route without authority

```text
route produces useful compression
  -> missing receipt or boundary check
  -> Judge/Warden keep HOLD
  -> Adaptive AngrySphinx raises friction if usefulness is repeatedly used as authority
```

### Overload by repeated ambiguity

```text
ambiguous route family
  -> keeps forcing retries, rebuilds, revalidations, and receipts
  -> no decisive progress
  -> resource pressure rises
  -> Adaptive AngrySphinx throttles, scars, or quarantines the route family
```

### Overload by retry loop

```text
network or simulator route fails repeatedly
  -> RetryAgent repairs repeatedly
  -> logs and receipts expand
  -> dispatch mass increases
  -> Adaptive AngrySphinx forces snapshot-only, mock-only, quarantine, or refusal
```

### Cross-layer cascade attempt

```text
Builder emits a malformed but useful candidate
  -> Judge does not inherit Builder trust automatically
  -> Warden blocks execution if boundaries are unclear
  -> Adaptive AngrySphinx scars repeated attempts to repackage the same flaw
```

## Relation to the three-layer gate

Builder/Judge/Warden blocks the first failure.

Adaptive AngrySphinx blocks normalization, overload, and cascade of the pattern.

```text
Builder blocks malformed construction.
Judge blocks invalid promotion.
Warden blocks valid-but-dangerous inheritance.
Adaptive AngrySphinx blocks repeated bypass and overload patterns from becoming familiar enough to inherit, expensive enough to consume the system, or broad enough to compromise every layer.
```

## Load-shedding outputs

Adaptive AngrySphinx may emit:

```text
HOLD
scar
throttle
lower route priority
force mock-only
force snapshot-only
require stronger receipt
quarantine route family
refuse route family
```

These are not failures of intelligence. They are protective finite states.

## Allowed claim

```text
Adaptive AngrySphinx is a rational defensive layer for a nanokernel/compression/ENE stack because it pays bounded local overhead to reduce the risk of unchecked boundary transitions becoming durable inherited state, total-system overload, or cross-layer compromise.
```

## Blocked claims

```text
Adaptive AngrySphinx proves safety.
Adaptive AngrySphinx proves attacker intent.
Adaptive AngrySphinx replaces Builder/Judge/Warden.
Adaptive AngrySphinx can eliminate all copy/write flaws.
Adaptive AngrySphinx can eliminate all overload states.
Adaptive AngrySphinx guarantees compartment isolation.
Adaptive AngrySphinx may bypass receipts because it is protective.
```

## Operating sentence

```text
Adaptive AngrySphinx is the copy/write, overload, and compartmentalization sanity layer for the manifold: it treats repeated boundary-crossing and unresolved resource-pressure patterns as signal, pays small finite costs to check, scar, throttle, quarantine, or refuse them, and prevents temporary unchecked transitions from becoming owned inherited state, total-system overload, or cross-layer compromise.
```
