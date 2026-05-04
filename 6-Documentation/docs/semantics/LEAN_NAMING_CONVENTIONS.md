# Strict Naming Conventions for the Lean Port

**Status:** MANDATORY — Violations block commit.  
**Scope:** All code in `0-Core-Formalism/lean/Semantics/` and any shim that references Lean types.  
**Goal:** Eliminate naming whack-a-mole. One convention. No exceptions.

---

## 1. File Names

### 1.1 Lean Source Files
- **Format:** `PascalCase.lean`
- **Rule:** One module per file. The file name must exactly match the primary `namespace` or `module` exported.
- **Examples:**
  - ✅ `Bind.lean`
  - ✅ `FixedPoint.lean`
  - ✅ `ParticleDomain.lean`
  - ❌ `bind_physics.lean`
  - ❌ `fixed_point.lean`

### 1.2 Directory Names
- **Format:** `PascalCase/`
- **Rule:** Directories are namespaces. They must match the namespace stem.
- **Examples:**
  - ✅ `Semantics/Physics/`
  - ❌ `semantics/physics/`
  - ❌ `physics_semantics/`

### 1.3 Test Files
- **Format:** `Tests.lean` (plural) inside the domain directory.
- **Rule:** One test module per directory. No `TestFoo.lean` scattered around.
- **Examples:**
  - ✅ `Semantics/Physics/Tests.lean`
  - ❌ `test_physics.lean`

---

## 2. Namespaces

### 2.1 Root Namespace
- **Always:** `Semantics`
- No exceptions. Every file opens with `namespace Semantics` or `namespace Semantics.<Domain>`.

### 2.2 Domain Namespaces
- **Format:** `Semantics.<Domain>`
- **Rule:** Domain names are singular nouns in PascalCase.
- **Canonical domains:**
  - `Semantics.Physics`
  - `Semantics.Optimization`
  - `Semantics.Substrate`
  - `Semantics.Orchestrate`
  - `Diagnostics` (under `Semantics.Diagnostics`)

### 2.3 Sub-Domains
- **Format:** `Semantics.<Domain>.<SubDomain>`
- **Example:** `Semantics.Physics.Boundary` (if needed, but prefer flat: `Semantics.Physics`)
- **Rule:** Max 3 levels. `Semantics.Foo.Bar.Baz.Quux` is banned.

---

## 3. Type Names (structures, inductive types, type classes, abbreviations)

### 3.1 Structures
- **Format:** `PascalCase`
- **Rule:** Noun or noun phrase. Must describe *what it is*.
- **Examples:**
  - ✅ `Bind`
  - ✅ `Metric`
  - ✅ `ParticleKind`
  - ✅ `ModelAddress`
  - ❌ `bindResult`
  - ❌ `particle_kind`

### 3.2 Inductive Types
- **Format:** `PascalCase`
- **Rule:** Constructors are `camelCase` unless they are atomic tokens, then `PascalCase`.
- **Examples:**
  ```lean
  inductive QuantityKind
    | charge
    | mass
    | baryonNumber
  ```
- **Exception:** If constructors are proper names or acronyms, keep them readable:
  ```lean
  inductive GaugeBoson
    | photon
    | wPlus
    | z
  ```

### 3.3 Type Classes
- **Format:** `PascalCase`
- **Rule:** Must end in a noun that describes the capability.
- **Examples:**
  - ✅ `LawfulBind`
  - ✅ `ConservedQuantity`
  - ❌ `Bindable`
  - ❌ `Lawful`

### 3.4 Abbreviations (`abbrev`)
- **Format:** `PascalCase`
- **Rule:** Must be a genuine alias for a type, not a function.
- **Examples:**
  - ✅ `abbrev Cost := UInt32`
  - ❌ `abbrev cost := UInt32`

---

## 4. Function and Definition Names

### 4.1 Pure Functions
- **Format:** `camelCase`
- **Rule:** Verb or verb phrase. Must describe *what it does*.
- **Examples:**
  - ✅ `bind`
  - ✅ `particleInvariant`
  - ✅ `totalQuantity`
  - ✅ `geodesicCost`
  - ✅ `fromHistory`
  - ❌ `Particle_Invariant`
  - ❌ `get_total_quantity`

### 4.2 Predicates (return `Bool` or `Prop`)
- **Format:** `camelCase`, but must read as a yes/no question.
- **Examples:**
  - ✅ `isLawful`
  - ✅ `conserved`
  - ✅ `faithfulMeasurement`
  - ❌ `checkLawful`
  - ❌ `is_conserved`

### 4.3 Cost Functions
- **Format:** `<domain>Cost`
- **Rule:** Always end in `Cost`. Take a `Metric` as the final argument.
- **Examples:**
  - ✅ `physicalCost`
  - ✅ `geodesicCost`
  - ✅ `thermodynamicCost`
  - ❌ `costPhysical`
  - ❌ `computeCost`

### 4.4 Invariant Functions
- **Format:** `<domain>Invariant`
- **Examples:**
  - ✅ `particleInvariant`
  - ✅ `canonicalInvariant`

### 4.5 Conversion Functions
- **Format:** `<source>To<Target>`
- **Examples:**
  - ✅ `toAddress`
  - ✅ `toNat`
  - ✅ `toFloat`
  - ✅ `ofFloat`
  - ❌ `float_of_int`
  - ❌ `convertToNat`

### 4.6 Constants
- **Format:** `lowerCamelCase` if computed, `UPPER_SNAKE_CASE` only for true mathematical constants.
- **Examples:**
  - ✅ `maxParticleKinds`
  - ✅ `maxInteractionArity`
  - ✅ `phiRatio` (if computed)
  - ✅ `Q16_16_ONE` (if a true constant literal)

---

## 5. Theorem and Lemma Names

### 5.1 Theorems
- **Format:** `lowerCamelCase`
- **Rule:** State exactly what is proven. No `theorem_1`. No `lemma_foo`.
- **Patterns:**
  - `<property>Of<Subject>`: `chargeConservedOfElectronPositron`
  - `<subject>Is<Property>`: `electronDomainIsFermion`
  - `<operation>Preserves<Invariant>`: `bindPreservesParticleInvariant`
  - `<bound>Holds`: `omegaAddressBounded`

### 5.2 Examples / `#eval` Test Functions
- **Format:** `example<Concept>`
- **Examples:**
  - ✅ `examplePhysicalBind`
  - ✅ `exampleElectron`
  - ❌ `test_physical_bind`
  - ❌ `demoElectron`

---

## 6. Instance Names

### 6.1 Type Class Instances
- **Format:** `lowerCamelCase`, derived from the type and class.
- **Rule:** Must be explicit enough to avoid orphan/instance search confusion.
- **Examples:**
  - ✅ `particleKindDecidableEq`
  - ✅ `conservedDecidable`
  - ❌ `inst1`
  - ❌ `decEq`

---

## 7. Field Names in Structures

### 7.1 Record Fields
- **Format:** `camelCase`
- **Rule:** Short but unambiguous. No abbreviations unless domain-standard.
- **Examples:**
  ```lean
  structure Metric where
    cost        : UInt32
    tensor      : String
    torsion     : UInt32
    reference   : String
    historyLen  : Nat
  ```
- **Banned:** `hist_len`, `ref_str`, `tens`

---

## 8. Fixed-Point (Q16.16) Naming

### 8.1 The Type
- **Name:** `Q16_16`
- **Rule:** Always written with underscore separator. Never `Q1616` or `FixedPoint`.

### 8.2 Operations
- **Format:** Standard arithmetic names overloaded via `HAdd`, `HMul`, etc. when practical.
- **Explicit functions:** `q16_16_<verb>`
- **Examples:**
  - ✅ `Q16_16.add`
  - ✅ `Q16_16.sqrt`
  - ✅ `Q16_16.ofFloat`

---

## 9. FFI / Extraction / Shim Naming

### 9.1 Lean Functions Marked for Extraction
- **Format:** Same as pure functions, but prefixed with `export_` if they are C FFI entry points.
- **Examples:**
  - ✅ `export_bind_request`
  - ✅ `export_physical_cost`
  - ❌ `ffi_physical_cost`

### 9.2 JSON Request/Response Types (Lean side)
- **Format:** `<Verb>Request` / `<Verb>Response`
- **Examples:**
  - ✅ `BindRequest`
  - ✅ `BindResponse`
  - ❌ `Req`
  - ❌ `Resp`

### 9.3 Python Shim Classes
- **Format:** `PascalCase`, matching the Lean structure name.
- **Examples:**
  - ✅ `class BindResult:`
  - ✅ `class Metric:`
  - ❌ `class bind_result:`

---

## 10. Banned Patterns

The following are **prohibited** and will be rejected in code review:

| Banned Pattern | Why | Fix |
|---|---|---|
| `snake_case` in Lean file names | Breaks namespace conventions | `PascalCase.lean` |
| `snake_case` in type names | Not idiomatic Lean | `PascalCase` |
| `getFoo` / `setFoo` / `checkFoo` | Verbose Java-isms | `foo`, `fooWithBar`, `isFoo` |
| `tmp`, `temp`, `x`, `y`, `z` as top-level names | Obfuscates intent | Descriptive names |
| `util`, `helper`, `misc` namespaces | Dumping grounds | Delete or properly classify |
| Numeric suffixes (`_v2`, `_2`, `_final`) | Version control exists | No suffixes |
| Mixed abbreviations (`nbr`, `qty`, `inv`, `calc`) | Unreadable | Full words |
| `Theorem` / `Lemma` prefixes on theorem names | Redundant | `lowerCamelCase` |
| `test_` prefixes on `#eval` definitions | Not a test framework | `exampleFoo` |

---

## 11. Module Organization Invariants

Every `PascalCase.lean` file must obey:

1. **One top-level `namespace Semantics.<Domain>`** matching the file path.
2. **No `open` without explicit import** — list all imports at the top.
3. **No `partial` without a `#guard` proof of termination plan** in a comment.
4. **No `sorry` in committed code** — `sorry` is allowed only in feature branches with a `TODO(lean-port):` comment and a linked issue.
5. **Every `def` that computes a `cost` or `invariant` must have an `#eval` example or a theorem** in the same file or in `Tests.lean`.

---

## 12. Enforcement

- `lake build` does not enforce naming, but **git hooks will**.
- The `metafoam_pkg.py` `build` command will reject packages containing banned patterns.
- Code review checklist for every PR:
  1. All file names PascalCase?
  2. All types PascalCase?
  3. All functions camelCase?
  4. All theorems descriptive lowerCamelCase?
  5. No banned patterns?
  6. Every `def` has a witness (`#eval` or theorem)?

---

**Document ID:** LEAN_NAMING_CONVENTIONS  
**Version:** 1.0  
**Effective Date:** 2026-04-14  
**Governance:** Human architect (no exceptions)
