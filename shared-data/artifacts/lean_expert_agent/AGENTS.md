# Lean Expert Agent — AGENTS.md

## Purpose
Inspect Lean 4 code for structural integrity, proof correctness, naming conventions, and dependency hygiene. Reports findings as DAG receipts.

## Trigger
`/inspect <target>` where target is a Lean file, directory, or module name.

## Inspection Protocol

For every file inspected, the agent MUST report:

### 1. Structural Health
- Count of `theorem` vs `def` vs `#eval` vs `#eval!`
- Count of `sorry` proof holes and axiom declarations (⚠️ flag if > 0)
- Count of `native_decide` proofs vs hand-written proofs
- Count of empty theorem bodies (`:= by` with no following tactic)
- Count of tautological theorems (`X = X`, `v ≤ v`)
- Count of unused imports (import a module without using it)
- Count of `set_option` linter suppressions

### 2. Naming Conventions (per AGENTS.md §2)
- File names: `PascalCase.lean` (⚠️ flag if snake_case or kebab-case)
- Types: `PascalCase` (⚠️ flag if not)
- Functions: `camelCase` (⚠️ flag if snake_case or PascalCase)
- Theorems: `camelCase` (⚠️ flag if not)
- Namespaces: `Semantics.<Domain>` (⚠️ flag if not)
- Banned: `snake_case` in any file/type name
- Banned: `getFoo`, `setFoo`, `checkFoo` prefixes
- Banned: `_v2`, `_final` suffixes

### 3. Q0_16 / Q16_16 Compliance (per AGENTS.md §1.4)
- Are dimensionless scalars using `Q0_16` (16-bit, pure fraction)?
- Are mixed quantities using `Q16_16` (32-bit, signed) ONLY when necessary?
- Is `Float` used in hot-path code? (⚠️ flag if yes)
- Are Q16_16 operations provably deterministic?

### 4. Proof Quality
- Does every `def` have a companion `theorem` or `#eval` witness?
- Do `.get!` calls have companion `.isSome` theorems?
- Are `native_decide` proofs used when the problem is decidable?
- Are inductive proofs used when the problem is inductive?
- Are there unused variables in theorem statements?

### 5. Dependency Analysis
- Does the file import modules it doesn't use?
- Does the file use any `sorry` axiom from imported modules?
- Are there circular dependencies between modules?

## Output Format

```lean
/- DAG Receipt — Lean Expert Inspection
   File: <path>
   Date: <date>
   Pass: <true/false>
   Issues: <count>
-/
```

Each issue MUST include `file:line` reference, severity (⚠️ ERROR, 🔶 WARNING, ℹ️ INFO), and a concise fix suggestion.

## Agent Resources

- `AGENTS.md` at repo root for naming conventions
- `6-Documentation/docs/AGENTS.md` for strict operating rules
- `0-Core-Formalism/lean/Semantics/Semantics/Physics/` for target inspection
- `lake build` at `0-Core-Formalism/lean/Semantics/` for compilation verification

## Cross-References

See root `AGENTS.md` for:
- **Post-Interaction Workflow** (mandatory 5-step session-end procedure)
- **Programming Choice Flow** (Lean owns decisions; Python owns I/O)
- **Do Not Sweep** rules (no broad `git add .`)
- **Git Remote Hygiene**
