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
- Use `Q16_16.ofRatio num den` for rational constants.
- Use `Q16_16.ofRawInt` when the raw integer encoding is documented with its
  float equivalent in a comment (e.g., `Q16_16.ofRawInt 53739  -- 0.82`).
- Arithmetic: `Q16_16.add`, `.sub`, `.mul`, `.div` — never native `+` on `Int`
  unless building a raw value for `ofRawInt`.

## Namespace and Import Conventions

- Modules under `Semantics/RRC/` import `Semantics.RRC.Emit` for `RRCShape`,
  `WitnessStatus`, `AlignmentStatus`, and `FixtureRow`.
- To use `RRCShape` constructors with dot notation, add:
  `open Semantics.RRCLogogramProjection`
- `DecidableEq RRCShape` is derived but may not resolve via `==`; use exhaustive
  `match` or `if decEq s t then` with the instance made explicit if needed.
- The blessed Compiler surface roots are:
  `Semantics.RRC.Emit`, `Semantics.AVMIsa.Emit`, `Semantics.RRC.Corpus278`
  Do not add these as imports in new files unless intentional — importing them
  is fine, but do not change their content without a build verification pass.

## Reference Files

- Build baseline and Compiler surface: `0-Core-Formalism/lean/Semantics/AGENTS.md`
- Lakefile targets: `0-Core-Formalism/lean/Semantics/lakefile.toml`
- Q16_16 / Q0_16 primitives: `Semantics/FixedPoint.lean`
- Receipt infrastructure: `Semantics/ReceiptCore.lean`
- RRC alignment gate: `Semantics/RRC/Emit.lean`
- Receipt density scoring: `Semantics/RRC/ReceiptDensity.lean`
- Logogram projection types: `Semantics/RRCLogogramProjection.lean`
- Sorry/TODO audit: `TODO_MAP.md` (project root)
