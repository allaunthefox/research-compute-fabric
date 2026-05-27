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

### 1.3 Float prohibition (strong)
**Float must not be used anywhere if at all possible.**

- **AVM core**: Float is forbidden.
- **Backends**: Float is forbidden for any semantic computation.
- **Boundary-only exception**: A backend may accept Float *only* at an external I/O boundary (JSON, sensor ingest, UI display), and must immediately convert it to `Q0_16` or `Q16_16`.

If Float appears anywhere, it must carry an explicit justification comment/receipt field:

- why fixed-point abstraction was not possible
- what exact conversion policy was used (clamp/range/rounding)
- what determinism guarantee remains

Default is: **reject**.

### 1.4 No dynamic foreign calls in ISA
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

## 3. Stripping policy ("bad code gets stripped out")

The phrase "bad code gets stripped out in the conversion" is made precise here.

### 3.1 What "bad" means
"Bad" does NOT mean "inelegant". Bad means one of:

- Not representable in the AVM closed-world ISA.
- Violates AVM typing rules (ill-typed stack/locals).
- Uses forbidden substrate features in core semantics (e.g. Float).
- Requires open string parsing or reflection to make a decision.
- Cannot be made deterministic under the fixed-point policy.

### 3.2 What stripping is allowed to do
When converting an external artifact into an AVM program, a shim may:

- Drop unreachable code (dead branches) if reachability is proven by the shim's proof/receipt boundary.
- Inline and normalize expressions into AVM primitives.
- Replace dynamic dispatch with finite enums (`Prim`, `Opcode`).
- Reject unsupported constructs with a hard error.

### 3.3 What stripping is NOT allowed to do
A shim must NOT:

- Silently change behavior to "make it fit" AVM.
- Replace unknown operations with placeholders.
- Substitute heuristic approximations without explicit residual/receipt fields.

If a construct cannot be represented, the correct action is **reject**, not "strip silently".

### 3.4 Stripping output receipts
Every strip/conversion pass must emit a receipt packet containing:

- input hash
- output program hash
- strip decisions (what was dropped, what was rewritten)
- unsupported constructs encountered (if any)
- AVM ISA version targeted

This makes "bad code elimination" auditable.

---

## 4. Serialization boundary (shim responsibility)

Adapters may represent AVM programs and values in JSON or binary form.

Rules:
- Serialization formats must be versioned.
- No semantic meaning may depend on string parsing.
- Decoders must reject unknown opcodes/types.

---

## 5. Receipt / provenance policy

Every adapter execution must be able to emit a receipt packet containing:

- AVM ISA version
- adapter version
- input program hash
- output state hash
- (optional) projection hash

This makes drift observable and auditable.

---

## 6. Relationship to prior "universal adapter" language

Earlier drafts described AVM as a universal adapter from many math languages.

**This spec supersedes that framing.** The correct architecture is:

- **Lean -> AVM ISA (Lean-defined) -> adapter shims/backends**

If other languages are supported as inputs, they must be compiled into AVM by a
shim that produces AVM programs; but the AVM ISA itself remains Lean-only.

---

## 7. Claim boundary

This document defines AVM as a Lean-only ISA and a backend adapter ecosystem.

It does not claim:
- that every backend already exists
- that all proofs are complete
- that the ISA opcodes are final

It does claim:
- strict typing + closed-world opcodes is mandatory
- all semantics live in Lean
- all non-Lean code is an adapter shim, not a semantic authority
- stripping must be explicit (reject or receipt), never silent behavior change
- float is forbidden by default; boundary-only conversion requires justification
