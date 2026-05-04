# Sovereign Surface / Router Telemetry Ingestion

Status: HOLD / source-ingestion note
Authority: local assistant transcript and defensive design note; not proof
Related:

- `docs/gcl/SovereignHyperEquationSynthesisIngestion.md`
- `docs/gcl/MOIMConcepts.md`
- `docs/gcl/NonEquilibriumTransitionRisk.md`
- `docs/gcl/EquationForestActiveKernels.md`

## Purpose

This document normalizes a pasted local-source transcript covering two adjacent surfaces:

```text
1. Defensive router copy-fail threat model
2. Sovereign Surface telemetry and reasoning-progress claims
```

The material is accepted as provenance for workbench design direction, not as verification evidence.

## Source classification

```text
source_type: local assistant transcript / image transcription
claim_state: HOLD
authority_scope: workbench_projection
receipt_status: missing code diff / missing build log / missing hardware trace / missing formal proof
```

## Surface 1: router copy-fail threat model

The paste discusses whether a copy-fail-style issue could affect a router-like hardware module.

Accepted defensive interpretation:

```text
The current router is likely low-risk while the route logic is purely combinational.
Risk increases when a multi-byte or multi-cycle packet interface is added.
UART RX / command ingress must not expose partially copied state.
```

Blocked interpretation:

```text
This proves the router is immune.
This provides an exploit path to attack routers.
This validates future UART packet safety without implementation review.
```

## Defensive design rules extracted

### 1. No partial-command commit

A command decoder must not commit route state, address state, regime state, or control flags until the full packet has been received and validated.

```text
receive bytes
  -> assemble shadow packet
  -> validate length / checksum / command type / regime bounds
  -> atomically commit to active register
```

### 2. Synchronous double-buffer

Use a shadow buffer and active buffer split.

```text
uart_shadow_packet
  -> validated_packet
  -> active_route_state
```

Rule:

```text
active_route_state changes only on valid_commit.
```

### 3. Metastability containment

Any asynchronous or externally timed signal must pass through synchronization before influencing control state.

```text
external_signal
  -> synchronizer
  -> debounced / qualified event
  -> control FSM
```

A status LED may be allowed to reflect non-critical states, but it must not feed back into route decisions.

### 4. Packet ingress FSM requirements

The future UART ingress state machine must declare:

```text
IDLE
RECEIVE_HEADER
RECEIVE_PAYLOAD
VALIDATE
COMMIT
ERROR_DROP
```

No state before `COMMIT` may alter active routing semantics.

### 5. Regime-collapse protection

Any command capable of changing regime state must require stricter validation than ordinary telemetry commands.

Recommended gates:

```text
complete packet
valid checksum or CRC
valid command class
valid address bounds
valid regime transition
rate limit / cooldown
explicit commit edge
error path clears shadow only
```

## Surface 2: Sovereign Surface telemetry

The paste claims a Sovereign Surface provided live telemetry such as:

```text
PHI / phi
GPU load
reasoning ETC
formal core status
live heartbeat
```

Accepted interpretation:

```text
The Sovereign Surface is a useful runtime dashboard concept for exposing workbench state.
```

Blocked interpretation:

```text
A displayed GPU load proves a model is reasoning.
A displayed ETC proves actual completion time.
A live heartbeat proves formal validity.
A locked formal core proves all dependent claims.
```

## Telemetry normalization

Telemetry should be divided into measured, inferred, and narrative fields.

```ts
type SovereignTelemetryField = {
  field_id: string;
  value: string | number | boolean;
  source_class: "measured" | "inferred" | "reported" | "narrative";
  unit?: string;
  sampling_window?: string;
  receipt_ref?: string;
  claim_state: "HOLD" | "V_scope" | "REVIEWED" | "CANONICAL_LEAN";
};
```

Examples:

| Field | Class | Boundary |
|---|---|---|
| GPU load | measured if from `nvidia-smi` or OS API | not proof of active reasoning |
| GPU power draw | measured if sourced from hardware monitor | not proof of model state |
| Reasoning ETC | inferred | heuristic only |
| Heartbeat | reported/runtime | liveness only, not correctness |
| Formal core locked | reported unless backed by build log | must cite Lean build receipt |
| PHI | narrative/inferred unless formula declared | must declare metric and units |

## Reasoning ETC rule

A statistical ETC may be displayed only as heuristic.

Required fields:

```text
source signal
time window
estimation method
confidence band or uncertainty label
last update timestamp
```

Blocked claim:

```text
ETC is a reliable measure of model thought progress.
```

Allowed claim:

```text
ETC is a dashboard heuristic based on observable runtime signals.
```

## Formal core claim discipline

The phrase `FORMAL CORE LOCKED` is high-risk unless tied to receipts.

Allowed only with explicit receipt:

```text
Lean build command
commit SHA
number of goals/theorems checked
number of sorry/admit markers
build log location
```

Do not use `locked` to mean emotionally stable, visually green, or assistant-reported.

## Relation to MOIM

MOIM can consume telemetry as behavioral signals.

```text
telemetry signal
  -> scalar
  -> confusion / confidence state
  -> gate
  -> receipt
  -> inheritance or quarantine
```

But telemetry cannot bypass the Keeper Law:

```text
The system may become useful.
It may not become authorized by usefulness alone.
```

## Relation to non-equilibrium transition risk

Telemetry dashboards can reduce transition risk when they improve observability.

They can increase risk when they create false stability.

```text
good telemetry:
  measured, sourced, scoped, uncertainty-aware

bad telemetry:
  aesthetic confidence without receipts
```

## Required future receipts

Before promoting this surface, require:

```text
1. Actual source files modified in the UI/server/router stack.
2. Commit hashes for telemetry changes.
3. Hardware telemetry source path, e.g. `nvidia-smi`, OS API, FPGA counter, or simulator log.
4. UART/router FSM implementation or design doc.
5. Test showing partial packets cannot commit active state.
6. Lean/build receipt if `formal core locked` is displayed.
```

## Suggested implementation targets

```text
src/telemetry/GpuLoadIndex.ts
src/telemetry/ReasoningEtcEstimator.ts
src/telemetry/TelemetryField.ts
rtl/router/uart_rx_fsm.v
rtl/router/synchronous_double_buffer.v
tests/router/test_no_partial_commit.py
Semantics/RouterIngress.lean
```

## Security boundary

This document is for defensive design hardening only.

Allowed:

```text
threat modeling
partial-write prevention
metastability containment
double-buffering
commit-gate design
test requirements
```

Blocked:

```text
instructions for attacking real routers
payloads for inducing malformed-packet failures
weaponized exploit development
bypassing authorization or access controls
```

## Operating sentence

```text
The Sovereign Surface router transcript is accepted as a defensive telemetry and ingress-hardening source: it identifies partial-commit risk at the future UART boundary, motivates synchronous double-buffering, and separates measured dashboard telemetry from inferred or narrative confidence claims.
```
