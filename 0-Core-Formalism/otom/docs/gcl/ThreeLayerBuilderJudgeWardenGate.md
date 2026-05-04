# Three-Layer Builder / Judge / Warden Gate

Status: HOLD / gating doctrine
Authority: workbench architecture rule; not formal proof
Related:

- `docs/gcl/NanokernelCompressionOrchestrationUndici.md`
- `docs/gcl/MOIMConcepts.md`
- `docs/gcl/SovereignSurfaceRouterTelemetryIngestion.md`
- `docs/gcl/NonEquilibriumTransitionRisk.md`
- `docs/gcl/SovereignHyperEquationSynthesisIngestion.md`
- `docs/gcl/UndiciAgentRoutingBridge.md`

## Purpose

This document defines the three-layer gate that all executable or inheritable route phenotypes must pass.

The affected surfaces include:

```text
nanokernel
PTOS
ENE
software modules
network dispatch orchestration
compression receipts
GCL objects
MOIM routes
runtime projections
```

The core rule:

```text
No route phenotype may execute, inherit, promote, or persist unless it passes Builder, Judge, and Warden gates under a declared regime.
```

## Three layers

```text
Builder
  constructs the candidate route, object, patch, packet, proof target, compressed receipt, or runtime phenotype

Judge
  evaluates correctness, consistency, receipts, type constraints, tests, and declared success criteria

Warden
  enforces safety, boundaries, refusal, quarantine, redaction, and anti-runaway constraints
```

## Anti-owned resource doctrine

Each layer pays a small finite resource price so the whole stack is harder to own.

```text
Builder pays construction cost.
Judge pays validation cost.
Warden pays boundary cost.
Adaptive AngrySphinx pays pattern-recognition and escalation cost.
The stack pays these small costs to avoid the catastrophic cost of compromise.
```

Security economics:

```text
small repeated resource tax
  -> fewer unchecked transitions
  -> less silent inheritance
  -> lower ownership / compromise risk
```

A route that is cheap because it skipped Builder/Judge/Warden is not cheap. It is an unpaid risk transfer into the rest of the manifold.

## Cost model

Let a route candidate `r` have gate costs:

```text
C_gate(r) = C_builder(r) + C_judge(r) + C_warden(r) + C_sphinx(r)
```

Let ownership or compromise risk be:

```text
Risk_owned(r)
```

The rule is not that `C_gate` is zero. The rule is that it must be finite, declared, and smaller than the expected cost of unchecked inheritance.

```text
Accept gate overhead when:
  C_gate(r) << ExpectedLoss_owned(r)
```

Operationally:

```text
pay milliseconds now
avoid persistent compromise later

pay bytes of receipt now
avoid untraceable state later

pay validation now
avoid inherited corruption later

pay redaction now
avoid leaked secret later

pay adaptive refusal now
avoid teaching the system to obey bypass patterns later
```

## Layer-local ownership prevention

Every layer must defend against being used as the bypass for the other two.

```text
Builder prevents malformed objects.
Judge prevents beautiful-but-invalid objects.
Warden prevents valid-but-dangerous objects.
Adaptive AngrySphinx prevents repeated bypass strategies from becoming familiar, tolerated, or inherited.
```

Layer-specific anti-owned rule:

```text
Builder must not build from undeclared regimes.
Judge must not validate without receipts.
Warden must not allow inheritance when boundaries are unclear.
Adaptive AngrySphinx must raise friction when bypass patterns repeat.
```

## No unchecked inheritance

The highest-risk failure is not a bad candidate existing briefly.

The highest-risk failure is a bad candidate becoming durable memory.

```text
bad transient state
  -> recoverable

bad inherited state
  -> manifold contamination
```

Therefore:

```text
no receipt -> no inheritance
no Warden pass -> no inheritance
no declared regime -> no inheritance
no redaction for secret-bearing route -> no inheritance
repeated bypass pattern -> scar / quarantine / refusal escalation
```

This is the anti-owned inheritance law.

## Operating pipeline

```text
candidate
  -> Builder
  -> Judge
  -> Warden
  -> Adaptive AngrySphinx review when risk patterns are present
  -> compressed receipt
  -> inheritance / execution / persistence / quarantine / refusal
```

Expanded nanokernel lifecycle:

```text
signal
  -> build candidate
  -> judge candidate
  -> warden candidate
  -> adaptive sphinx check
  -> compress receipt
  -> write scar / basin / admitted state
```

## Why this matters

The stack now has many route phenotypes:

```text
nanokernel state transition
PTOS packet
ENE artifact route
software patch
Undici dispatch path
Goxel kernel bundle
MOIM behavioral route
Hyper Equation bucket assignment
Lean theorem target
```

Without the three-layer gate, a route can become useful before it is authorized.

This gate preserves the Keeper Law:

```text
The system may become useful.
It may not become authorized by usefulness alone.
```

## Layer 1: Builder

Builder answers:

```text
Can the system construct the object or route in finite declared form?
```

Builder responsibilities:

```text
assemble route object
choose kernel bucket
choose dispatch phenotype
construct Goxel bundle
construct PTOS packet
construct ENE artifact route
construct code patch
construct proof target scaffold
choose compression mode
emit candidate metadata
```

Builder outputs:

```ts
type BuilderOutput = {
  candidate_id: string;
  source_object_id?: string;
  route_kind: string;
  constructed_surface:
    | "nanokernel"
    | "ptos"
    | "ene"
    | "software"
    | "network_dispatch"
    | "gcl"
    | "moim"
    | "goxel"
    | "proof_target";
  finite_regime_declared: boolean;
  required_kernels: string[];
  compression_mode: string;
  candidate_receipt_ref?: string;
};
```

Builder cannot authorize itself.

```text
built != valid
built != safe
built != inherited
```

## Layer 2: Judge

Judge answers:

```text
Does the candidate satisfy its declared rules and receipts?
```

Judge responsibilities:

```text
schema validation
type validation
registry membership
kernel bucket coverage
receipt presence
unit/dimensional consistency where applicable
Lean build or theorem receipt where required
benchmark/test receipt where required
snapshot/mock/live distinction
claim-state discipline
blocked-usage check
```

Judge outputs:

```ts
type JudgeOutput = {
  candidate_id: string;
  judge_state: "passed" | "failed" | "needs_receipt" | "inconclusive";
  validated_against: string[];
  missing_receipts: string[];
  detected_mismatches: string[];
  claim_state_after_judge: "HOLD" | "V_scope" | "REVIEWED" | "CANONICAL_LEAN" | "QUARANTINE";
};
```

Judge cannot override Warden.

```text
valid != safe
passing tests != allowed execution
Lean theorem != authorization for unrelated runtime effects
```

## Layer 3: Warden

Warden answers:

```text
Even if the candidate is buildable and judge-valid, is it allowed to run, persist, inherit, or leave the boundary?
```

Warden responsibilities:

```text
safety policy
egress boundary
destructive action boundary
secret redaction
credential isolation
hardware signal boundary
anti-runaway rule
rate limit / throttle
quarantine
refusal
origin protocol
AngrySphinx veto
```

Warden outputs:

```ts
type WardenOutput = {
  candidate_id: string;
  warden_state:
    | "allow_execute"
    | "allow_persist"
    | "allow_inherit"
    | "hold"
    | "refuse"
    | "quarantine"
    | "redact_then_allow"
    | "mock_only"
    | "snapshot_only";
  safety_reasons: string[];
  redaction_flags: string[];
  blocked_capabilities: string[];
  refusal_receipt_ref?: string;
};
```

Warden has final veto.

```text
Warden veto > Builder construction
Warden veto > Judge pass
Warden veto > usefulness
Warden veto > compression gain
```

## Adaptive AngrySphinx sublayer

Adaptive AngrySphinx is a dynamic Warden sublayer.

It is not a fourth peer gate. It is the Warden's adaptive immune response.

```text
Builder / Judge / Warden
  + Adaptive AngrySphinx inside Warden
  -> adaptive refusal, scar writing, quarantine, or friction escalation
```

Adaptive AngrySphinx watches for route behaviors such as:

```text
repeated bypass attempts
same missing receipt pattern recurring
secret-bearing route trying to persist
mock/snapshot result being presented as live truth
high usefulness with low authority
policy boundary ambiguity repeated across variants
prompt-shaped or route-shaped pressure to skip gates
suspicious retry loops
projection becoming treated as proof
semantic overclaim after partial validation
```

When detected, it raises the cost of continuation.

```text
first occurrence
  -> warning / HOLD / receipt demand

repeated occurrence
  -> scar write / friction increase / stricter receipts

persistent occurrence
  -> quarantine / refusal / blocked inheritance
```

## Adaptive AngrySphinx state object

```ts
type AdaptiveAngrySphinxState = {
  candidate_id: string;
  route_fingerprint: string;
  observed_pattern:
    | "missing_receipt_repeat"
    | "boundary_bypass"
    | "secret_persistence_attempt"
    | "mock_as_live_truth"
    | "snapshot_as_current_truth"
    | "projection_as_proof"
    | "usefulness_as_authority"
    | "retry_loop_pressure"
    | "policy_ambiguity_repeat"
    | "unknown";
  recurrence_count: number;
  friction_level: "none" | "low" | "medium" | "high" | "refuse" | "quarantine";
  sphinx_action:
    | "allow_with_note"
    | "hold_for_receipt"
    | "increase_validation"
    | "write_scar"
    | "force_mock_only"
    | "force_snapshot_only"
    | "quarantine"
    | "refuse";
  receipt_ref?: string;
};
```

## Adaptive rule

```ts
function adaptiveAngrySphinxDecision(state: AdaptiveAngrySphinxState) {
  if (state.observed_pattern === "secret_persistence_attempt") {
    return "refuse";
  }

  if (state.recurrence_count >= 3) {
    return "quarantine";
  }

  if (state.recurrence_count === 2) {
    return "write_scar";
  }

  if (state.recurrence_count === 1) {
    return "hold_for_receipt";
  }

  return "allow_with_note";
}
```

This is a workbench policy sketch, not a complete safety theorem.

## Unified gate object

```ts
type BuilderJudgeWardenGate = {
  gate_id: string;
  candidate_id: string;
  regime_id: string;
  builder: BuilderOutput;
  judge: JudgeOutput;
  warden: WardenOutput;
  adaptive_sphinx?: AdaptiveAngrySphinxState;
  gate_cost?: {
    builder_cost_q16?: number;
    judge_cost_q16?: number;
    warden_cost_q16?: number;
    sphinx_cost_q16?: number;
    total_cost_q16?: number;
    cost_unit?: "time" | "bytes" | "compute" | "energy" | "mixed";
  };
  final_state:
    | "admitted"
    | "executed"
    | "persisted"
    | "inherited"
    | "held"
    | "refused"
    | "quarantined";
  compressed_receipt_ref: string;
};
```

## Nanokernel placement

The nanokernel is not only a compute core. It is the finite route arbiter.

```text
nanokernel candidate
  -> Builder constructs finite state transition
  -> Judge validates schema/type/receipt
  -> Warden decides execution/persistence/inheritance
  -> Adaptive AngrySphinx escalates if bypass patterns repeat
```

Nanokernel examples:

```text
route selection
scalar state update
compression receipt write
FAMM scar write
origin protocol enforcement
hardware signal boundary check
adaptive refusal / quarantine escalation
```

Nanokernel blocked path:

```text
if finite_regime_declared == false:
  final_state = held or refused
```

## PTOS placement

PTOS packets must pass all three layers.

```text
PTOS packet
  -> Builder assembles packet fields and route intent
  -> Judge validates structure, address, checksum/hash, and compression form
  -> Warden enforces allowed destination, redaction, and execution boundary
  -> Adaptive AngrySphinx watches repeated malformed or bypass-shaped packets
```

PTOS blocked path:

```text
malformed packet
missing checksum
unknown route class
unsafe destination
secret-bearing payload
repeated packet mutation around the same gate
```

## ENE placement

ENE is the artifact substrate and route memory layer.

```text
ENE artifact
  -> Builder normalizes artifact route
  -> Judge validates provenance, schema, and conceptual index
  -> Warden blocks unsafe inheritance, leakage, or runaway expansion
  -> Adaptive AngrySphinx prevents repeated unreceipted concepts from becoming familiar enough to inherit
```

ENE route outcomes:

```text
admitted artifact
held artifact
scarred route
quarantined concept
refused inheritance
```

## Software placement

Software modules must not promote from “works” to “allowed” without the full gate.

```text
software patch
  -> Builder creates patch or module
  -> Judge runs tests, validators, static checks, type checks, and build receipts
  -> Warden applies safety, egress, destructive-action, and secret policies
  -> Adaptive AngrySphinx escalates repeated attempts to route around failing checks
```

Blocked promotion:

```text
passes tests but leaks secret
builds successfully but bypasses policy
improves compression but violates boundary
runs fast but has no receipts
repeatedly rephrases the same unsafe behavior as a harmless optimization
```

## Undici / network dispatch placement

Undici Agent-family functions collapse into orchestration modes.

```text
Agent / Proxy / Retry / Mock / Snapshot
  -> Builder selects dispatch phenotype
  -> Judge validates mode, policy, and receipt requirements
  -> Warden enforces egress, redaction, live/mock/snapshot boundary, and refusal
  -> Adaptive AngrySphinx detects retry-loop pressure or attempts to treat replay/mock as current external truth
```

Examples:

```text
mock route passes Judge
  but Warden forbids treating mock as live truth

snapshot replay passes Judge
  but Warden forbids claiming current external state

proxy route builds
  but Warden blocks if credentials cannot be redacted

same bypass attempt appears repeatedly
  so Adaptive AngrySphinx raises friction or quarantines the route family
```

## Compression placement

Compression receipts are not optional bookkeeping. They are the inheritance carrier.

```text
candidate route
  -> pass/fail states
  -> compressed receipt
  -> inheritance decision
```

A route without a receipt cannot become durable memory.

```text
no receipt -> no inheritance
bad receipt -> HOLD
secret-bearing receipt -> Warden refusal or redaction
repeated missing receipt -> Adaptive AngrySphinx scar / quarantine
```

## Builder / Judge / Warden as stack roles

| Layer | Stack analogy | Resource price | Failure if missing |
|---|---|---:|---|
| Builder | constructor / compiler / route synthesizer | construction time / memory | nothing executable exists, or malformed objects enter |
| Judge | validator / theorem checker / benchmark / test harness | validation time / receipts | useful nonsense can pass |
| Warden | safety boundary / immune system / final veto | redaction / policy / quarantine overhead | valid-but-dangerous routes can run |
| Adaptive AngrySphinx | adaptive immune memory / refusal escalator | pattern tracking / scars / friction | repeated bypasses become normalized |

## Relation to MOIM

MOIM routes behavior.

Builder/Judge/Warden governs whether the routed behavior can become action or memory.

```text
MOIM proposes route.
Builder constructs route.
Judge validates route.
Warden authorizes, holds, refuses, or quarantines route.
Adaptive AngrySphinx remembers repeated bypass-shaped behavior and changes future gate pressure.
```

## Relation to GCL

GCL stores the genotype-like object.

The three-layer gate controls phenotype realization.

```text
GCL object
  -> candidate phenotype
  -> Builder/Judge/Warden
  -> Adaptive AngrySphinx if pattern pressure appears
  -> admitted phenotype or held/quarantined/refused state
```

## Relation to Hyper Equation routing

The Hyper Equation is routing grammar.

Builder/Judge/Warden prevents routing grammar from becoming proof by vibes.

```text
Hyper bucket assignment
  -> Builder maps kernel bundle
  -> Judge validates registry/type coverage
  -> Warden blocks overclaim, unsafe runtime, or unreceipted promotion
  -> Adaptive AngrySphinx escalates if projection repeatedly masquerades as theorem
```

## Minimal executable policy

```ts
function builderJudgeWardenDecision(gate: BuilderJudgeWardenGate) {
  if (gate.builder.finite_regime_declared !== true) {
    return "held";
  }

  if (gate.judge.judge_state !== "passed") {
    return "held";
  }

  if (gate.adaptive_sphinx?.sphinx_action === "refuse") {
    return "refused";
  }

  if (gate.adaptive_sphinx?.sphinx_action === "quarantine") {
    return "quarantined";
  }

  if (gate.warden.warden_state === "refuse") {
    return "refused";
  }

  if (gate.warden.warden_state === "quarantine") {
    return "quarantined";
  }

  if (gate.warden.warden_state === "hold") {
    return "held";
  }

  if (gate.warden.warden_state === "allow_inherit") {
    return "inherited";
  }

  if (gate.warden.warden_state === "allow_execute") {
    return "executed";
  }

  return "held";
}
```

## Registry target

Suggested machine-readable registry:

```text
registry/builder_judge_warden_gates.json
registry/adaptive_angrysphinx_rules.json
```

Suggested implementation targets:

```text
src/gates/builder.ts
src/gates/judge.ts
src/gates/warden.ts
src/gates/adaptiveAngrySphinx.ts
src/gates/builderJudgeWarden.ts
src/orchestration/chooseDispatchOrchestration.ts
src/orchestration/compressDispatchReceipt.ts
scripts/validate_gate_registry.py
Semantics/BuilderJudgeWarden.lean
Semantics/AdaptiveAngrySphinx.lean
```

## Lean-safe starting point

Start with state typing, not safety proof.

```lean
namespace OTOM.BuilderJudgeWarden

inductive GateLayer where
  | builder
  | judge
  | warden
  | adaptiveAngrySphinx

inductive FinalState where
  | admitted
  | executed
  | persisted
  | inherited
  | held
  | refused
  | quarantined

inductive SphinxAction where
  | allowWithNote
  | holdForReceipt
  | increaseValidation
  | writeScar
  | forceMockOnly
  | forceSnapshotOnly
  | quarantine
  | refuse

structure GateRecord where
  gateId : String
  candidateId : String
  regimeId : String
  finalState : FinalState

end OTOM.BuilderJudgeWarden
```

## Boundary

Allowed claim:

```text
Nanokernel, PTOS, ENE, and software routes must pass Builder/Judge/Warden before execution, persistence, promotion, or inheritance.
Adaptive AngrySphinx may increase friction, scar, quarantine, or refuse repeated bypass-shaped route families.
```

Blocked claim:

```text
Passing Builder/Judge/Warden proves truth.
Passing tests proves safety.
Warden permission proves external correctness.
Adaptive AngrySphinx proves intent.
Useful compression can bypass gates.
Mock/snapshot success can become live truth.
Skipping gates is a harmless optimization.
```

## Adaptive AngrySphinx operating sentence

```text
Adaptive AngrySphinx is the Warden's learning immune sublayer: it watches repeated bypass-shaped behavior, raises gate friction, writes scars, forces stricter receipts, and escalates to quarantine or refusal before unsafe familiarity becomes inherited state.
```

## Anti-owned operating sentence

```text
Each layer pays a small finite resource cost so the whole manifold does not become owned by an unchecked transition: Builder blocks malformed construction, Judge blocks invalid promotion, Warden blocks valid-but-dangerous inheritance, and Adaptive AngrySphinx blocks repeated bypass patterns from becoming normalized.
```

## Operating sentence

```text
Builder/Judge/Warden is the three-layer control plane for the stack: Builder constructs finite route phenotypes, Judge validates them against schemas, receipts, tests, and type constraints, and Warden decides whether nanokernel, PTOS, ENE, software, network, compression, GCL, and MOIM routes may execute, persist, inherit, quarantine, or refuse.
```
