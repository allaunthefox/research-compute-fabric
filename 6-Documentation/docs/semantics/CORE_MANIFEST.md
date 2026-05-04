# Core Manifest — Honest Status of the Semantics Library

> **Document ID**: CORE_MANIFEST_v1  
> **Date**: 2026-04-17  
> **Status**: LIVING — updated as modules stabilize or debt is resolved

---

## 1. Philosophy

This document exists because **AGENTS.md** mandates zero-guesswork, proven-correct code — yet the current codebase has unfinished foundations. Rather than pretend everything is core, we document:

- **STABLE**: No `sorry`, no `Float` in hot paths, total functions, with witnesses
- **BETA**: Functional but with known gaps (marked `TODO` or `sorry`)
- **SHIM**: Boundary/interop code that admits non-core types (`Float`, `String` parsing)
- **EXPLORATORY**: Research modules not yet ready for canonical use

---

## 2. Core Status by Module

### 2.1 STABLE — Core Contract

| Module | Status | Witnesses | Notes |
|--------|--------|-----------|-------|
| `Basic.lean` | ✅ STABLE | None needed | Empty scaffolding |
| `Atoms.lean` | ✅ STABLE | None needed | Type aliases only |
| `FixedPoint.lean` | ✅ STABLE | `Q16_16.one`, `Q16_16.zero` | Foundation for all fixed-point math |
| `Bind.lean` | ✅ STABLE | `bindPreservesInvariant` | Core `bind` primitive |
| `Lemmas.lean` | ✅ STABLE | Various proof helpers | Utility lemmas |
| `Graph.lean` | ⚠️ BETA | `#eval` witnesses | 8 `Float` uses — geometry needs Q16_16 port |
| `Canon.lean` | ⚠️ BETA | `q16_16_field_kind_core_safe`, `core_schema_implies_prohibition` | `float64` marked non-core-safe; `timestamp` still `Float` |
| `Constitution.lean` | ⚠️ BETA | 1 `sorry` in `validRecordCount` | Needs totality proof |

### 2.2 BETA — Known Debt

| Module | Debt | Severity | Plan |
|--------|------|----------|------|
| `BraidCross.lean` | 2 `sorry` (associativity/commutativity) | MEDIUM | Pending `Fix16.add` proofs |
| `BraidStrand.lean` | Uses `UInt32` directly | LOW | Acceptable — no logic |
| `Constitution.lean` | 1 `sorry` | MEDIUM | Totality witness needed |
| `SurfaceCore.lean` | 1 `sorry` | LOW | Deferred to extension |
| `Tests.lean` | 18 `sorry` | MEDIUM | Test debt, not production |

### 2.3 SHIM — Boundary Code

| Module | Purpose | Why `Float` is OK |
|--------|---------|-------------------|
| `Canon.lean` | `float64` field kind | Interop with external JSON; excluded from core-safe paths |
| `Diagnostics.lean` | Telemetry/logging | Human-readable output |
| `EquationTranslation.lean` | LaTeX/OMT bridge | External format conversion |

### 2.4 EXPLORATORY — ExtensionScaffold

All modules in `ExtensionScaffold/` are explicitly NOT core:
- `Temporal/` — Time-variant systems research (CMYKFrequencyCore)
- `ENE/` — Session provenance and research archive (SessionArchive)
- `Thermodynamics/` — Energy/entropy extensions
- `Topology/` — Geometric structure experiments

---

## 3. The Float Boundary

**Rule**: `Float` is permitted only in these contexts:

1. **External interop** — parsing JSON, CSV, hardware ADC values
2. **Human output** — telemetry, logs, visualization
3. **Research experiments** — ExtensionScaffold modules

**Core-safe predicate**: `FieldKind.coreSafe` correctly returns `false` for `float64`, ensuring core ENE operations reject float-backed state.

**Violations to fix**:
- `CanonicalState.timestamp : Float` → should be `UInt64` epoch or `String` ISO
- `SourceInfo.trustLevel : Float` → should be `Q16_16` (0.0 to 1.0)

---

## 4. The `sorry` Inventory

```
File                        Count  Context
--------------------------  -----  -----------------------------------
BraidCross.lean             2      Fix16.add associativity/commutativity
Constitution.lean           1      validRecordCount totality
SurfaceCore.lean            1      surfaceCost (deferred)
Tests.lean                  18     Test scaffolding debt
TOTAL                       22
```

**Acceptable**: 0 in production core logic.  
**Target**: Resolve BraidCross and Constitution `sorry`s before v0.2.0.

---

## 5. Integration Points — ENE Layer

Current ENE integration status:

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| SessionArchive | `ExtensionScaffold/ENE/` | ✅ **CORRECT** | Session provenance for research — extension |
| PhiRedundancy | `ExtensionScaffold/Compression/` | ✅ CORE | Hachimoji nibble recovery is canonical |
| CBFTests | `Semantics/` | ❌ **DEPRECATED** | Removed from main import; old test pollution |
| CMYKFrequencyCore | `ExtensionScaffold/Temporal/` | ✅ CORRECT | Decode-cheap frequency chart — extension |

**Decision needed**: `SessionArchive` is typed session provenance. If ENE requires historical session awareness for canonical operation, promote it to core with full verification. If it's audit/logging only, move to `ExtensionScaffold/`.

---

## 6. Honest Completion Status

### What IS finished:
- [x] `bind` primitive with lawful checks
- [x] Q16_16 fixed-point foundation
- [x] Phi-permuted redundancy scheme (3-stream, weighted voting)
- [x] PBACS canonical state projection
- [x] ENE graph structure (nodes, edges, paths)
- [x] Prohibition framework (negative-space rules)
- [x] FieldKind.coreSafe boundary

### What IS NOT finished:
- [ ] BraidCross associativity/commutativity proofs (2 `sorry`)
- [ ] Constitution totality (1 `sorry`)
- [ ] Canon timestamp/trustLevel Float → Q16_16
- [ ] Graph geometry port from Float to Q16_16
- [ ] Full Hutter context integration (spec exists, implementation partial)
- [ ] Waveprobe QUBO → Lean extraction
- [ ] ENE session archive: core vs extension decision

### What's exploration (correctly in extensions):
- [x] CMYK frequency core
- [x] Temporal variant index framework
- [x] Thermodynamic throat physics
- [x] Spike sync neural networks

---

## 7. Build Status

```bash
$ lake build Semantics          # ✅ PASS (with warnings)
$ lake build ExtensionScaffold  # ✅ PASS
$ lake build Tests              # ❌ FAIL (pre-existing test debt)
```

**Warnings** (acceptable for now):
- `BraidCross.lean:72:8` — declaration uses `sorry`
- `BraidCross.lean:84:8` — declaration uses `sorry`
- Various unused variables — linter only

---

## 8. Next Actions

Priority order:

1. **Decide SessionArchive fate**: Core ENE dependency → keep in Semantics/; audit-only → move to ExtensionScaffold/
2. **Fix Canon Floats**: `timestamp` → `UInt64`, `trustLevel` → `Q16_16`
3. **Prove BraidCross**: Fix16.add associativity/commutativity
4. **Complete Constitution**: `validRecordCount` totality witness
5. **Port Graph**: Float geometry → Q16_16 vectors

---

## 9. Document History

- **v1.0** (2026-04-17): Initial honest inventory after SessionArchive expansion

---

> *"The bind bridge operates on invariant preservation — guessing an invariant is worse than doing nothing."* — AGENTS.md
