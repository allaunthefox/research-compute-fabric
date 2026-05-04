# Surf MCP Fusion Gate

Status: HOLD / external-tool fusion gate
Authority: workbench integration note; not calibration proof
Related:

- `docs/gcl/AVMFixedPointComplianceRemediation.md`
- `docs/gcl/ThreeLayerBuilderJudgeWardenGate.md`
- `docs/gcl/NanokernelCompressionOrchestrationUndici.md`
- `docs/gcl/RunawayDigitalCellDivisionDoctrine.md`
- `docs/gcl/FederatedNanokernelSwarmDoctrine.md`
- `docs/gcl/SovereignHyperEquationSynthesisIngestion.md`

## Purpose

This note defines how Surf MCP or Google MCP-style external tool surfaces may fuse into the stack.

External MCP tools can help finish the orchestration layer, but they do not automatically calibrate AVM, prove the Hyper Equation, validate hardware parity, or promote claims.

## Core rule

```text
MCP tools are external route phenotypes.
They are not roots of truth.
```

Any MCP-sourced action or result must pass:

```text
Builder
  -> construct tool request and declare capability

Judge
  -> validate schema, result shape, receipts, and claim scope

Warden
  -> enforce egress, credentials, destructive-action limits, redaction, and inheritance policy

Adaptive AngrySphinx
  -> scar/throttle/quarantine repeated bad patterns
```

## Fusion placement

```text
MCP tool surface
  -> nanokernel orchestration route
  -> dispatch policy
  -> external call
  -> compressed receipt
  -> Judge replay or schema validation
  -> Warden authority decision
  -> ENE inheritance or HOLD/quarantine/refusal
```

## What Surf MCP can contribute

Depending on which Surf MCP is meant, it may provide:

```text
browser automation / web interaction
API data fetches
OpenAPI-derived tools
external search or data grounding
crypto/API telemetry
web-surface inspection
```

These are useful as tool phenotypes.

They are not formal receipts unless the stack records:

```text
tool identity
tool version
request shape hash
response shape hash
credential redaction status
policy hash
timestamp / sampling context
Warden decision
claim scope
```

## Google MCP placement

Google MCP surfaces may expose cloud/product APIs through MCP endpoints.

They must be treated as external capability routes:

```text
Google MCP call
  -> declared capability
  -> credential boundary
  -> request receipt
  -> response receipt
  -> Warden authority limit
```

A successful Google MCP call proves only that the call returned under the declared conditions.

It does not prove:

```text
AVM calibration
Lean theorem validity
hardware parity
Hyper Equation correctness
formal core lock
```

## AVM calibration boundary

The transcript claims AVM is `CALIBRATED`, but that status requires repo-visible receipts.

Required receipt files or equivalent:

```text
FixedPoint.lean with Q0_16 and Q16_16 definitions
AVM step / bind semantics file
validator script rejecting float/f32/f64/double in core semantics
lake build log or CI receipt
cross-target determinism test receipt
hardware parity test plan or log
```

Until those are present and checked:

```text
AVM status remains HOLD / CLAIM_BUNDLE_PENDING_RECEIPTS
```

## External float boundary

MCP tools may return JSON numbers or platform-native numeric strings.

These must not enter AVM authority as floats.

```text
MCP numeric output
  -> boundary parser
  -> declared quantization policy
  -> Q0_16 or Q16_16 atom
  -> conversion receipt
  -> AVM core
```

## Claim-state mapping

```text
MCP response received
  -> HOLD

MCP response with schema validation and receipt
  -> V_scope

MCP response replayed / independently checked
  -> REVIEWED candidate

MCP response plus Lean theorem / build / hardware logs
  -> may support CALIBRATED claim only for the exact theorem/test scope
```

## Hardware parity gate

Hardware parity is not complete until the router/FPGA target produces comparable receipts.

Required:

```text
AVM reference trace
Verilog/router trace
input vector set
state hash comparison
fixed-point arithmetic equivalence
UART packet boundary test
partial-commit rejection test
metastability-safe boundary documentation
```

## Operating sentence

```text
Surf MCP and Google MCP can finish the fusion only as external route phenotypes: they may provide tool access, data, browser/API interaction, and receipts, but every result must pass Builder/Judge/Warden, fixed-point boundary conversion, compressed receipt capture, and scoped claim promotion before it can influence AVM, ENE, GCL, MOIM, or hardware parity.
```
