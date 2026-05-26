# Canonical Specification for the Adaptive Virtual Machine (AVM)
## State: CALIBRATED_PENDING_VALIDATION

This document is the canonical design for **AVM as a Lean-defined core ISA**.

**Core rule:**

> **Lean is the source of truth. AVM is a Lean-only ISA.**

All non-Lean languages (Python, Rust, C/C++, Go, etc.) are **adapter shims** (a.k.a.
backends) that *strip / serialize / reinterpret* into AVM programs and execute
AVM semantics. They do not define new semantics.

---

## 0. Definitions

### 0.1 AVM Core
The **AVM core** is the ISA + operational semantics defined in Lean.

- Finite opcode set (closed-world)
- Finite value type set (closed-world)
- Deterministic step/run semantics
- No open string matching in decisions
- No dynamic "Any" values in the ISA

### 0.2 Adapter shims (backends)
Adapter shims are **extraction/interop targets**, not sources of truth.

They may:
- Encode/decode AVM programs and values (serialization)
- Interpret AVM programs (runtime interpreter)
- Emit target artifacts (Python bytecode, C, Rust, Verilog, FPGA netlists)

They may **not**:
- Introduce new ISA meaning
- Add ad-hoc branching policy
- Decide invariants or costs outside Lean

---

## 1. AVM Instruction Set Architecture (ISA) — Lean-only

The AVM ISA is a **Lean inductive** instruction set.

### 1.1 Closed-world opcodes
The opcode set MUST be finite and enumerable.

A minimal core (illustrative, not final):

- Stack ops: `push`, `pop`, `dup`, `swap`
- Locals: `load`, `store` (indexed by `Fin n`)
- Control flow: `jump`, `jumpIf`, `halt`
- Fixed-point arithmetic primitives: `addSat`, `subSat`, `mul`, etc.

### 1.2 Strict typing
The ISA operates over a finite type universe:

- `Q0_16` (default for dimensionless scalars)
- `Q16_16` (only when range/precision forces it)
- `Bool`
- (Optional later) `UInt8`, `UInt16`, `UInt32`, fixed-width words for IO/register surfaces

**No Float in core.** Float may exist only at boundary conversion shims.

### 1.3 No dynamic foreign calls in ISA
The ISA must not contain opcodes like `CALL("pythonMethod")` or `IMPORT("module")`.

If extensibility is needed, it must be via **finite enums** (e.g. `Prim : Type`)
with semantics defined in Lean:

- `Prim` is finite
- `evalPrim : Prim -> ...` is defined in Lean
- backends implement `Prim` by matching the Lean semantics

---

## 2. Execution model

### 2.1 Step semantics
AVM execution is defined by a Lean function:

- `step : Program -> State -> Outcome State`

### 2.2 Run semantics (fuel)
AVM execution must have a fuel-bounded run function:

- `run : Fuel -> Program -> State -> Outcome State`

This is required for totality and for extraction to bounded substrates.

### 2.3 Determinism invariant
The state transition must be deterministic:

For any two backend environments implementing the same AVM ISA,

- `run_backend1(program, state) == run_backend2(program, state)`

up to the same observable projection.

---

## 3. Serialization boundary (shim responsibility)

Adapters may represent AVM programs and values in JSON or binary form.

Rules:
- Serialization formats must be versioned.
- No semantic meaning may depend on string parsing.
- Decoders must reject unknown opcodes/types.

---

## 4. Receipt / provenance policy

Every adapter execution must be able to emit a receipt packet containing:

- AVM ISA version
- adapter version
- input program hash
- output state hash
- (optional) projection hash

This makes drift observable and auditable.

---

## 5. Relationship to prior "universal adapter" language

Earlier drafts described AVM as a universal adapter from many math languages.

**This spec supersedes that framing.** The correct architecture is:

- **Lean -> AVM ISA (Lean-defined) -> adapter shims/backends**

If other languages are supported as inputs, they must be compiled into AVM by a
shim that produces AVM programs; but the AVM ISA itself remains Lean-only.

---

## 6. Claim boundary

This document defines AVM as a Lean-only ISA and a backend adapter ecosystem.

It does not claim:
- that every backend already exists
- that all proofs are complete
- that the ISA opcodes are final

It does claim:
- strict typing + closed-world opcodes is mandatory
- all semantics live in Lean
- all non-Lean code is an adapter shim, not a semantic authority
