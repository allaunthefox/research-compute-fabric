# Rust OISC Decompressor Target

Status: `LEAN_RUST_REPLAY_SURFACE`

Claim boundary: this is a Lean/Rust replay surface for the Rust OISC
decompressor target. It is not a production decompressor, not a compression
benchmark, not an FPGA implementation, and not an ASIC implementation.

## Purpose

The decompressor core should be portable across software and hardware by
reducing the hot path to one lawful transition:

```text
compressed stream
-> instruction packet
-> one OISC state transition
-> bounded output update
-> residual accumulator update
-> replay receipt
```

Python remains outside the hot path. It can orchestrate corpora, plots,
notebooks, hardware probes, and receipt collection, but the decompressor
transition itself must be defined in Lean and lowered to Rust/FPGA/ASIC.

## Lean Surface

Lean module:

```text
0-Core-Formalism/lean/Semantics/Semantics/RustOISCDecompressor.lean
```

Imported by:

```text
0-Core-Formalism/lean/Semantics/Semantics.lean
```

The module defines:

- `Byte := Fin 256`
- `Instruction`
- `OiscState`
- `step`
- `run`
- `emittedBytes`
- `abcProgram`

The only transition primitive is `step`.

## Wire Shape

The minimal replay wire format is:

```text
magic:   "OISC"
version: 0x01
body:    repeated 3-byte instructions
instr:   (symbol, residual, final_flag)
```

`final_flag` is constrained to `0` or `1`. Header-only input is a valid empty
stream. Truncated instructions, invalid magic/version, invalid final flags,
capacity overflow, and bytes after a final instruction fail closed.

## Current Witnesses

Closed Lean witnesses:

```text
haltedStepStable
firstStepEmitsOne
abcFixtureByteExact
abcFixtureHalts
residualAccumulatorWrapsClosed
postFinalRunStableClosed
overflowFailsClosed
abcWireFixtureCloses
emptyWireCloses
overflowWireFailsClosed
invalidMagicFailsClosed
invalidVersionFailsClosed
truncatedInstructionFailsClosed
trailingAfterFinalFailsClosed
```

The tiny fixture emits `ABC`:

```text
emittedBytes abcFinal = [65, 66, 67]
abcFinal.halted = true
```

The negative/overflow fixture fails closed after capacity is exhausted:

```text
emittedBytes overflowFinal = [65, 66]
overflowFinal.halted = true
```

Residual accumulator and post-final stability are now covered by finite Lean
fixtures:

```text
emittedBytes residualWrapFinal = [120, 34]
residualWrapFinal.acc.val = 115
emittedBytes postFinalStableFinal = [65, 67]
postFinalStableFinal.acc.val = 134
```

The wire fixture closes with:

```text
emittedBytes abcReceipt.state = [65, 66, 67]
abcReceipt.state.acc.val = 201
abcReceipt.instructionCount = 3
abcReceipt.decision = done
```

## Rust Surface

Rust module:

```text
5-Applications/compression-core/src/oisc.rs
```

Feature flag:

```text
oisc
```

Public reference entrypoints:

```text
decompress_oisc(input, output_capacity)
decompress_oisc_into(input, output_capacity, output_buffer)
```

The `decompress_oisc_into` path clears and reuses the caller-provided output
buffer, returning replay metadata instead of cloning the output. The convenience
`decompress_oisc` wrapper allocates one output vector for callers that do not
provide a buffer.

## Verification

Commands run from `0-Core-Formalism/lean/Semantics`:

```bash
lake build Semantics.RustOISCDecompressor
lake build Semantics
cargo test --no-default-features --features oisc
cargo test
cargo test --no-default-features --features noop
```

Observed result:

```text
Built Semantics.RustOISCDecompressor
Built Semantics
OISC Rust tests: 13 passed
default Rust tests: passed
noop Rust tests: passed
```

The narrow build printed:

```text
[65, 66, 67]
true
[120, 34]
115
[65, 67]
134
[65, 66]
true
[65, 66, 67]
201
3
DecodeDecision.done
```

## Next Closure Gates

Closed since the first toy-only surface:

- A small byte-exact replay fixture exists outside the toy `ABC` program.

Remaining HOLDs:

- Fixture-level eigenmass replay and control accounting remain HOLD.
- Residual policy is declared for real compressed blocks.
- AMMR/O-AMMR receipt fields are wired to block/epoch replay.
- FPGA prototype or Verilog lowering implements the same transition.
- ASIC/OISC datapath sketch is constrained to the same state fields.
