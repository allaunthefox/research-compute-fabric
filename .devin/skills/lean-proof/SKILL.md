---
name: lean-proof
description: >
  Writing, reviewing, and completing Lean 4 proofs and modules in the Research Stack.
  Use this skill whenever creating or editing .lean files, adding theorems, filling
  sorries, or auditing a Lean module for quality. Enforces the project's proof quality
  contract: no tautologies, no unexplained sorries, no floating TODOs without notes.
---

# Lean Proof Skill

This skill governs all Lean 4 authoring and review work in the Research Stack.

## Core Rules

### 1. Double-check every output
After writing or editing any Lean content, re-read the produced definitions and
proofs before considering the task done. Verify:
- Types match the stated intent.
- No accidental namespace clash or shadowing.
- `#eval` witnesses print the expected values (check them against hand-computed
  expected values in comments).

Run `lake build <Module.Name>` after every edit. Review the output for errors
**and** for unexpected `info:` / `#eval` values that contradict expectations.
If the first build pass reveals surprises, fix and rebuild before committing.

### 2. Sorries must be explained or eliminated

**Preferred:** complete the proof.

If a `sorry` cannot be closed immediately:
- Add a structured comment immediately above it explaining **why** it is deferred:
  ```lean
  -- TODO(lean-port): blocked on missing Mathlib lemma X. Tracked in TODO_MAP.md §A7.
  -- Proof sketch: show Y by induction on Z; use Finset.sum_congr.
  sorry
  ```
- The comment must state: what is needed, a proof sketch if possible, and where
  it is tracked.
- A bare `sorry` with no explanation is **not acceptable**.

`sorry`-free is the goal. Every new module should aim for 0 sorries. Use
`#check`, `exact?`, `apply?`, `omega`, `simp`, `decide`, `norm_num`, and
`Finset` / `List` lemmas from Mathlib before reaching for `sorry`.

### 3. TODOs follow the same contract as sorries

A `-- TODO(lean-port): ...` comment is acceptable only when:
- It names the specific thing that needs to be done.
- It gives a proof sketch or a pointer to where the logic lives in Python/Rust.
- It is tracked in `TODO_MAP.md` if it affects a blessed Compiler surface module.

Bare `-- TODO` with no explanation is not acceptable in Lean files.

### 4. No tautological theorems

Every theorem and lemma must prove something **non-trivial**. Forbidden patterns:

```lean
-- Forbidden: trivially true by rfl
theorem foo : 1 = 1 := by rfl

-- Forbidden: restating a definition with no additional content
theorem bar (x : Nat) : x + 0 = x := Nat.add_zero x   -- only if this adds nothing new

-- Forbidden: wrapper with no proof obligation
theorem baz : True := trivial
```

A theorem is acceptable only if it:
- Establishes a property of a **domain type** defined in this project (e.g., alignment
  scores, density bounds, receipt validity, Q16_16 arithmetic invariants).
- Is used by another definition, downstream theorem, or `#eval` witness.
- Would not be provable by `rfl` / `trivial` alone without domain-specific reasoning.

Acceptable examples:
- Bounds on `alignmentScore`: `∀ s, alignmentScore s ≤ 100`
- Monotonicity: density increases as more axes are hit
- Receipt validity gate: `compileRow r |>.receipt.valid ↔ r.alignmentStatus ≠ .missingPrediction`

### 5. Proof must have a purpose

Before writing a theorem, answer:
> "What does this proof guarantee about the system's behavior?"

If the answer is "nothing specific beyond what the definition already states
by construction," the theorem should not be written. Convert it to a `#eval`
witness or a comment instead.

Proofs that are justified:
- **Invariant proofs**: the scoring sum stays in [0, 1].
- **Gate proofs**: a gate only passes when preconditions are met.
- **Monotonicity / ordering proofs**: more evidence → higher score.
- **Receipt proofs**: receipt is valid iff alignment passed.

## Workflow

1. Read the nearest `AGENTS.md` before editing any subtree.
2. For new modules in the Compiler surface, check `lakefile.toml` to see if the
   module needs to be added to `[[lean_lib]] roots`.
3. Write the module, including `#eval` witnesses with expected values in comments.
4. Run `lake build <Module>`. Fix all errors.
5. **Re-read the produced code.** Check:
   - Every `sorry` has an explanation comment.
   - Every theorem has a clear domain purpose.
   - `#eval` outputs match the expected values stated in comments.
6. If the Compiler surface was touched, run `lake build Compiler` and confirm
   the job count matches the baseline in `0-Core-Formalism/lean/Semantics/AGENTS.md`.
7. Run `python3 -m py_compile` on any Python shims updated to add BOUNDARY comments.

## Q16_16 Fixed-Point Contract

- **No `Float` in compute paths.** `ofFloat` is only permitted at the external
  boundary (parsing JSON, reading sensor data) and must be immediately bracketed.
  In particular: Compiler-surface modules (`Semantics.RRC.*`, `Semantics.AVMIsa.*`,
  `Semantics.ReceiptCore`) must contain zero `ofFloat` calls in any definition
  that feeds into a receipt, score, or gate decision.
- Use `Q16_16.ofRatio num den` for rational constants.
- Use `Q16_16.ofRawInt` only when the raw integer is documented with its float
  equivalent in a comment on the same line:
  `Q16_16.ofRawInt 53739  -- 0.82 * 65536`
  An undocumented magic integer is a bug.
- Arithmetic inside `def` bodies: accumulate in raw `Int`, then call `Q16_16.ofRawInt`
  once at the end. Never use native `+` / `*` on two `Q16_16` values without going
  through `Q16_16.mul` / `Q16_16.add`.

## #eval Witness Contract

Every `#eval` in a Compiler-surface module **must** carry a `-- expect:` comment
on the same or preceding line stating the expected output:

```lean
#eval determineAlignment fixtureClf   -- expect: alignedExact
#eval (emitFixture.totalRows, emitFixture.candidateRows)  -- expect: (6, 3)
```

- The expected value must be hand-computed or derived from first principles, not
  copy-pasted from a previous build output.
- After each build, manually confirm the `info:` lines from `lake build` match
  the `-- expect:` comments. If they diverge, treat it as a failing test.
- `#eval` blocks without `-- expect:` comments are **not acceptable** in new code.
  Existing ones without comments should be annotated when the file is next touched.

## Namespace and Closing Discipline

- Every module must open with `namespace Semantics.X.Y` and close with
  `end Semantics.X.Y` (exact match, including case).
- The closing `end` must be the last non-blank line of the file.
- `open` statements are scoped to the namespace block only; do not `open` at file
  level outside a namespace (causes leakage into downstream imports).
- To use `RRCShape` constructors with dot notation, add inside the namespace:
  `open Semantics.RRCLogogramProjection`
- `DecidableEq RRCShape` is derived but `BEq RRCShape` is not automatically
  synthesized. Use exhaustive `match` for shape comparisons, not `==`.

## Lakefile / Compiler Surface Discipline

- The blessed Compiler target roots are fixed:
  `Semantics.RRC.Emit`, `Semantics.AVMIsa.Emit`, `Semantics.RRC.Corpus278`
- **Do not add new roots to `[[lean_lib]] name = "Compiler"`** without explicit
  user approval. New modules under `Semantics/RRC/` are imported by existing roots,
  not added as independent Compiler roots.
- After any change to `lakefile.toml`, run `lake build Compiler` and verify the
  job count matches the baseline in `0-Core-Formalism/lean/Semantics/AGENTS.md`.
  A job-count decrease means a module was silently dropped — investigate before
  committing.

## Schema and Claim Boundary Strings

Receipt JSON schemas are versioned strings. Existing values must not be renamed:

| Module | Schema string |
|---|---|
| `Semantics.RRC.Emit` | `"rrc_emit_fixture_v1"` |
| `Semantics.AVMIsa.Emit` | `"avm_canary_emit_v1"` / `"avm_rrc_corpus278_v1"` |
| `Semantics.RRC.ReceiptDensity` | `"receipt-density-scoring-only; not-a-proof; promotion=not_promoted"` |

- To add a new schema, use the next version suffix (e.g. `_v2`) and document the
  change in `ARCHITECTURE.md` §7.1.
- `claim_boundary` strings must end with `"admissibility-and-routing-pass-only"`
  or an equivalent explicit limitation. Never use vague strings like `"ok"` or `"verified"`.

## Promotion Gate Invariant

`promotion = not_promoted` is a hard invariant at this stage of the pipeline.
No Lean definition, theorem, or `#eval` block may set `Promotion.candidate` on
any row without explicit user approval and a corresponding update to `TODO_MAP.md`.

Violation pattern to reject:
```lean
-- Forbidden: silently promoting a row
promotion := .candidate
```

## Axiom / Unsafe / native_decide Prohibition

The following are **forbidden** in all Compiler-surface modules without explicit
sign-off:
- `axiom` (introducing an unproven assumption)
- `unsafe` (bypassing the type system)
- `native_decide` (compiles to native code, bypasses kernel — allowed in test
  harnesses only, never in blessed Compiler modules)

If you believe one of these is necessary, stop, document the reason in a comment,
and flag it to the user before proceeding.

## Python Shim BOUNDARY Comment Format

When a Python shim's logic has been ported to Lean, the shim file must be updated
with a BOUNDARY block in this **exact format**, immediately after the docstring:

```python
# BOUNDARY: Python thin IO shim; logic in <Lean.Module.Name>.
#   - python_function_name  → Lean.Module.Name.leanDefinitionName
#   - ...
```

- One entry per ported function.
- Lean module name must be fully qualified.
- The comment must appear **before** any `import` statements that are not part of
  the original shim header.
- If a file still contains un-ported logic, the BOUNDARY comment must say
  `# PARTIAL BOUNDARY` and list both what is ported and what remains.

## Reference Files

- Build baseline and Compiler surface: `0-Core-Formalism/lean/Semantics/AGENTS.md`
- Lakefile targets: `0-Core-Formalism/lean/Semantics/lakefile.toml`
- Q16_16 / Q0_16 primitives: `Semantics/FixedPoint.lean`
- Receipt infrastructure: `Semantics/ReceiptCore.lean`
- RRC alignment gate: `Semantics/RRC/Emit.lean`
- Receipt density scoring: `Semantics/RRC/ReceiptDensity.lean`
- Logogram projection types: `Semantics/RRCLogogramProjection.lean`
- Sorry/TODO audit and porting queue: `TODO_MAP.md` (project root)
- Architecture and output boundary: `ARCHITECTURE.md` §7.1
