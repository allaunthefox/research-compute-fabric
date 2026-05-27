# LEAN_FIRST_BOUNDARY — Lean-first compliance contract

**Status:** Canonical enforcement doc

> **Lean is the source of truth. Everything else is a shim.**

This document is the short, contributor-facing boundary contract referenced by
AGENTS.md and all architecture/spec files.

---

## 1) Definitions

### 1.1 Canonical

"Canonical" means:

- the semantics are defined in Lean under `0-Core-Formalism/lean/Semantics/`
- `lake build` is the authority gate for formal claims
- invariants/cost functions/typed residual policies are Lean-owned

### 1.2 Shim / adapter

"Shim" means:

- boundary-only code in Python/Rust/JS/etc.
- allowed to do I/O, parsing, serialization, DB connections, subprocess spawn
- forbidden to define semantics

---

## 2) What belongs in Lean (required)

Lean MUST own:

1. **Finite types / enumerations**
   - no open string matching in the core
   - strings are boundary I/O only

2. **Invariants + cost functions**
   - any logic that decides ACCEPT/REJECT/QUARANTINE/PROMOTE

3. **Provenance + attestation policy**
   - required provenance fields
   - deterministic hashing / chain rules
   - receipt typing

4. **Surface/tool manifests**
   - the list of supported tool names for an MCP surface
   - the mapping from tool name → schema/behavior class

5. **Validators**
   - any configuration payload (yaml/json/env inputs) must be validated by Lean
   - missing required fields must be rejected or typed as residuals
   - never silently default “unknown” into a guessed value

---

## 3) What belongs in shims (allowed)

Shims MAY do:

- read env vars / config files
- JSON/YAML parsing
- open sqlite/postgres connections
- call subprocesses (including Lean executables)
- transport: HTTP/MCP stdio plumbing
- emit logs

Shims MUST NOT:

- compute or approximate a cost function
- decide lawfulness
- guess missing fields (no “conservative defaults”)
- introduce new invariants
- implement branching that changes semantics (routing must be driven by Lean-owned tags/enums)

---

## 4) Float prohibition summary

- New core logic must not use `Float`.
- Use fixed-point:
  - Q0_16 for dimensionless scalars
  - Q16_16 only when range/precision is proven necessary

If a shim accepts float input from the outside world, it must convert at the
boundary and pass fixed-point values onward.

---

## 5) Receipts vs rejection

When adapter input is malformed or underspecified:

- **Preferred:** reject with a typed reason (Lean)
- **Alternative (when required):** accept as a *workbench_projection* artifact
  but emit an explicit receipt describing:
  - what was missing
  - what was assumed
  - what must be repaired to become receipt_backed

No silent repair.

---

## 6) Quick examples

### 6.1 BAD shim behavior

- A Python script reads `nodes.yaml`, sees missing CPU/RAM, and fills defaults.
- A Rust MCP server hardcodes tool names as strings.

### 6.2 GOOD shim behavior

- A shim reads `nodes.yaml`, passes JSON to a Lean validator, and exits nonzero
  with a Lean-produced error if required fields are missing.
- A shim queries Lean for the canonical MCP tool manifest and exposes exactly
  those tools.

---

## 7) Enforcement

- Any PR that introduces semantics in non-Lean code is an invariant violation.
- Any PR that adds new dependencies without explicit approval is rejected.
- Any PR that adds open-ended string parsing in the core is rejected.

---

## 8) References

- `6-Documentation/docs/AGENTS.md`
- `0-Core-Formalism/lean/Semantics/Semantics/JsonLSurfaceConnector.lean`
