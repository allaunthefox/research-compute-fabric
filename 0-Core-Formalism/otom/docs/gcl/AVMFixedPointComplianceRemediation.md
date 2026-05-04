# AVM Fixed-Point Compliance Remediation

Status: HOLD / compliance remediation
Authority: fixed-point determinism rule for AVM core semantics
Related:

- `docs/gcl/ThreeLayerBuilderJudgeWardenGate.md`
- `docs/gcl/RunawayDigitalCellDivisionDoctrine.md`
- `docs/gcl/NanokernelCompressionOrchestrationUndici.md`
- `docs/gcl/FederatedNanokernelSwarmDoctrine.md`

## Purpose

This note records a critical AVM compliance correction.

The AVM is intended to bridge formal math and executable bytecode. Therefore its core numeric semantics must be deterministic and fixed-point only.

## Compliance alert

The synthesized AVM Canonical Specification reportedly includes `float` as a primitive type.

That is a promotion blocker.

```text
float / f32 / f64 / double are not allowed as AVM core primitive numeric types.
```

## Required type correction

Replace:

```text
int, float, bool, list, dict, function
```

with:

```text
int, Q0_16, Q16_16, bool, list, dict, function
```

## Canonical numeric atoms

### Q0_16

```text
Q0_16 = unsigned fractional fixed-point atom
scale = 2^16
intended use = probabilities, normalized weights, bounded gates, ratios in [0, 1)
```

### Q16_16

```text
Q16_16 = fixed-point scalar atom with 16 integer bits and 16 fractional bits
canonical one = 0x00010000
intended use = route mass, scalar costs, field values, timing, geometry scalars
```

## Determinism invariant

```text
same bytecode + same input state + same receipt context = same output state hash
```

This must hold across the declared AVM compatibility regime.

## Boundary rule

Floating-point values may appear only outside AVM authority, such as UI display, debug visualization, external import, or export formatting.

Before a value enters AVM core semantics, it must be quantized into `Q0_16` or `Q16_16` under a declared conversion policy.

## Bind requirement

The AVM must expose an explicit bind/composition primitive so route-state transitions can be reasoned about and later formalized.

Minimal target:

```text
AVM action A produces value plus state plus receipt.
Bind feeds that value into the next AVM action.
The composed action must preserve explicit state and receipt flow.
```

## Promotion blocker

The AVM may not be promoted to `CALIBRATED` until:

```text
1. Core primitive `float` references are removed.
2. Q0_16 and Q16_16 are defined.
3. Arithmetic, rounding, and overflow behavior are declared.
4. Boundary conversion from external numeric formats is declared.
5. The determinism invariant is stated.
6. Bind/composition semantics are specified.
7. A validator rejects core `float`, `f32`, `f64`, and `double` references.
```

## Operating sentence

```text
The AVM may only serve as the bridge between formal math and bytecode if its core semantics are fixed-point deterministic: float primitives are excluded from core authority, Q0_16 and Q16_16 become canonical numeric atoms, bind composition is explicit, and bit-exact reproducibility is required before calibration.
```
