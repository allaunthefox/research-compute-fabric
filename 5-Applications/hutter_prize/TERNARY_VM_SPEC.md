# Minimal Trinary VM Spec

This document defines a deliberately small execution model for the Hutter Prize lab.

It is not the final codec machine. It is the smallest useful machine that lets us
test the subregister and audit ideas with deterministic behavior.

## Goals

- keep execution deterministic
- keep state small enough to inspect by hand
- attach each operation to a subregister boundary
- produce a replayable execution trace
- give the audit layer something boring to verify

## Value Domain

Every cell stores one trinary value:

- `-1`
- `0`
- `+1`

No other values are valid in machine state.

## State Model

The machine state is a mapping of subregister names to fixed-length cell arrays.

Each subregister has:

- `name`
- `width`
- `cells`

Example:

```json
{
  "alpha": [0, 1, -1, 0],
  "beta": [1, 0, 0, -1]
}
```

## Operation Boundary

Each instruction executes against exactly one named subregister.

An instruction may optionally read from a second subregister, but it must still declare
one primary writable subregister. This keeps the audit claim local:

- which subregister was targeted
- what cells changed
- what rule was applied
- whether the rule stayed within the trinary domain

## Instruction Set

The minimal instruction set is:

- `SET`
  Write one cell to `-1`, `0`, or `+1`.
- `ADD`
  Add one trinary delta to one cell with saturation at `-1` and `+1`.
- `SUB`
  Subtract one trinary delta from one cell with saturation at `-1` and `+1`.
- `SHIFT`
  Rotate a subregister left or right by one cell.
- `MERGE`
  Add another subregister cellwise into the target with saturation.
- `PROJECT`
  Copy a contiguous slice from one subregister into another.
- `W`
  Apply an integer weight to one cell, then clamp the result back into the trinary
  domain. This is a placeholder for the broader weighting primitive.

All instructions must be deterministic and side-effect free outside their declared
target subregister.

## Saturation Rule

Arithmetic never leaves the trinary domain.

If an operation would produce a value below `-1`, it is clamped to `-1`.
If an operation would produce a value above `+1`, it is clamped to `+1`.

## Trace Model

Every executed instruction should emit a trace entry with:

- `step`
- `op`
- `target`
- `args`
- `before`
- `after`

That gives the audit layer a simple replay surface.

## Example Program

```json
{
  "subregisters": {
    "alpha": [0, 0, 0, 0],
    "beta": [1, -1, 0, 1]
  },
  "program": [
    {"op": "SET", "target": "alpha", "index": 0, "value": 1},
    {"op": "ADD", "target": "alpha", "index": 1, "value": 1},
    {"op": "MERGE", "target": "alpha", "source": "beta"},
    {"op": "SHIFT", "target": "alpha", "direction": "right"},
    {"op": "W", "target": "alpha", "index": 2, "weight": -2}
  ]
}
```

## Audit Posture

This VM is intentionally boring.

It is useful because a verifier can answer:

- what state existed before the step
- what instruction was allowed
- what subregister was touched
- whether the resulting state remained valid

If we later move toward a proof system, this VM gives us a clean baseline trace to
formalize first.
