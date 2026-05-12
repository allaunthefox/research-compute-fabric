# Lean Naming Conventions

**Repository:** Sovereign Stack / Research Stack
**Version:** 2.1
**Date:** 2026-05-10
**Scope:** All Lean 4 code in `0-Core-Formalism/lean/Semantics/`

---

## Zero Exceptions Rule

All code must obey these conventions. There are no exceptions.

---

## File Names

| Format | Example | Notes |
|--------|---------|-------|
| `PascalCase.lean` | `Canon.lean` | Module file |
| `PascalCase/` | `Semantics/Physics/` | Directory |

**Banned:** `snake_case.lean`, `camelCase.lean`, `lowercase.lean`

---

## Namespaces

| Format | Example |
|--------|---------|
| `Semantics.<Domain>` | `Semantics.Orchestrate` |

Every file exports exactly one namespace matching its stem.

---

## Types

| Format | Example |
|--------|---------|
| `PascalCase` | `CanonicalState`, `BindResult` |

**Banned:** `snake_case_type`, `camelCaseType`, `Type_with_underscores`

---

## Functions and Predicates

| Format | Example | Notes |
|--------|---------|-------|
| `camelCase` | `canonicalCost` | Functions |
| `camelCase` | `isLawful` | Predicates |

**Banned:** `get_foo`, `setFoo`, `check_foo`, `validate_thing`

---

## Cost Functions

| Pattern | Example |
|---------|---------|
| `<domain>Cost` | `thermodynamicCost` |
| `<domain>Cost` | `canonicalCost` |

---

## Theorems

| Format | Example |
|--------|---------|
| `camelCase` | `bindPreservesInvariant` |

**Banned:** `Theorem_Name`, `theorem_name`, `theorembind`

---

## Constants

| Format | Example |
|--------|---------|
| `camelCase` | `maxParticleKinds` |
| `camelCase` | `defaultTimeoutMs` |

---

## Fixed-Point Types

| Format | Meaning | Usage |
|--------|---------|-------|
| `Q16_16` | 32-bit, integer + fraction | Range exceeds [-1,1] |
| `Q0_16` | 16-bit, pure fraction | Dimensionless scalars |

**Priority:** Use `Q0_16` as default. Use `Q16_16` only when:
1. Integer precision required (coordinates, counters)
2. Range exceeds [-1, 1] with sub-integer precision
3. Hardware mandates 32-bit

---

## Banned Patterns

| Banned | Reason |
|--------|--------|
| `snake_case` | Violates PascalCase file/type rule |
| `getFoo`, `setFoo` | Getter/setter anti-pattern |
| `checkFoo` | Vague verb |
| `_v2`, `_final`, `_tmp` | Versioning in names |
| `test_` prefix | Test naming |
| `Utils.lean`, `Helpers.lean` | Utility file anti-pattern |
| `misc.lean`, `common.lean` | Vague naming |

---

## Examples

### Correct

```lean
-- File: CanonicalState.lean
namespace Semantics.CanonicalState

structure BindState where
  cost : UInt32
  lawful : Bool
  invariant : String

def bindCost (s : BindState) : UInt32 :=
  s.cost

def isLawfulBind (s : BindState) : Bool :=
  s.lawful

theorem bindPreservesInvariant (s : BindState) :
    isLawfulBind s → s.invariant ≠ "" := by
  -- proof

end Semantics.CanonicalState
```

### Incorrect

```lean
-- File: canonical_state.lean (WRONG: snake_case)
namespace semantics.canonical_state (WRONG: lowercase)

structure bind_state where (WRONG: snake_case)
  cost : UInt32

def get_cost (s : bind_state) : UInt32 := (WRONG: get_ prefix, snake_case)
  s.cost

theorem Bind_Preserves_Invariant (s : bind_state) : (WRONG: snake_case with underscores)
    -- proof
```

---

## Enforcement

- `lake build` linting catches naming violations
- PRs with naming violations are rejected
- When in doubt, match existing code in `Semantics.FixedPoint`

---

## References

- Primary: `6-Documentation/docs/AGENTS.md` §2
- Related: `0-Core-Formalism/lean/Semantics/AGENTS.md`
