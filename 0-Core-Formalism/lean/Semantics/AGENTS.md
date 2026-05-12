# AGENTS.md - Lean/Semantics

Scope: `0-Core-Formalism/lean/Semantics/`

The strict operating rules live in `../../../6-Documentation/docs/AGENTS.md`.
Follow those rules for all Lean, proof, fixed-point, hardware-extraction, and
shim-boundary work.

## Local Rules

- Keep module names aligned with file names and namespaces.
- Prefer small domain modules over utility files.
- Every new computational gate needs an executable witness: theorem, `#eval`,
  or native-decision proof.
- Run the narrow build target first, for example:

```bash
lake build Semantics.BeaverMaskFreshness
```

- Run the broader build before claiming a stable Lean surface:

```bash
lake build
```

- Do not delete difficult theorems to make builds pass. Fix proofs or quarantine
  with an explicit `TODO(lean-port): ...` boundary.
- Treat generated Python, Rust, Verilog, and JSON as shims or receipts, not as
  the formal source of truth.

## Current Stack-Solidification Anchors

- `Semantics.BeaverMaskFreshness` is a finite admission gate for Beaver-mask
  freshness negative controls.
- Stack status receipts live under `shared-data/data/stack_solidification/`.
- The current staged slice is documented in
  `../../../6-Documentation/docs/stack_solidification_staging_manifest_2026-05-09.md`.
