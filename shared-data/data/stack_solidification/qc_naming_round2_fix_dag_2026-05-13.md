# QC Naming Round 2 Fix DAG — 2026-05-13

## Summary

Completed 20 renames across 4 files in `Physics/`. Build passes (`lake build`: 3530/3530 jobs).

## File-by-file results

### 1. `UniversalBridge.lean` — 9 renames, all PASS

| Old Name | New Name | References | Cross-file |
|----------|----------|------------|------------|
| `RE_LAMINAR` | `reLaminar` | 10 (def + usages in theorems, `#eval`, `frictionFactor`, `intermittency`, `normalizedT`, `classifyRegime`) | none outside file |
| `RE_TURBULENT` | `reTurbulent` | 9 | none outside file |
| `H_INTERVAL` | `hInterval` | 2 (def + `normalizedT`) | none outside file |
| `Y0` | `y0` | 9 (def + usages in `hermiteSpline`, `frictionFactor`, `intermittency`, theorems, `#eval`; comments also updated) | none — `pY0`/`pY1` in `MorphicTopologyMetaprobe.lean` are unrelated locals |
| `Y1` | `y1` | 9 | same |
| `H_M0` | `hM0` | 2 (def + `hermiteSpline`); `h10_s0` local untouched | none |
| `H_M1` | `hM1` | 2 (def + `hermiteSpline`); `h11_s1` local untouched | none |
| `q16_add` | `q16Add` | 5 (def + `hermiteSpline` callers) | `q16_add_dsp48` in `EntropyPhaseEngine.lean` is a different symbol — not renamed |
| `q16_sub` | `q16Sub` | 7 (def + 6 usages) | none outside file |

### 2. `QCLEnergy.lean` — 1 stale `#eval` fix, PASS

- `#eval hc_eV_nm` → `#eval hcEvNm` (the def was already `hcEvNm`; only the eval reference was stale)
- `eV_one` → `eVOne`: the def was already `eVOne`; no stale `eV_one` references existed → SKIP (already clean)

### 3. `StringStarConstants.lean` — 4 stale `#eval` fixes, PASS

| Stale Ref | New Ref | Notes |
|-----------|---------|-------|
| `#eval G_const` | `#eval gConst` | Def was already `gConst` |
| `#eval c_const` | `#eval cConst` | Def was already `cConst` |
| `#eval hbar_const` | `#eval hbarConst` | Def was already `hbarConst` |
| `#eval kB_const` | `#eval kBConst` | Def was already `kBConst` |

Cross-file: `NBody.lean:224` had a stale `c_const` reference → updated to `cConst`. PASS.
The `c_const` parameter in `SoftTissuePressureDynamics.lean:27` and `StoichiometricMetabolicDynamics.lean:28` are independent function parameters, NOT references to the StringStarConstants symbol → not touched.

### 4. `Tests.lean` — 0 changes needed

Theorems are already camelCase (e.g. `exampleChargeNotConserved`, `electronDomainFermion`). Grep for snake_case patterns (`example_charge`, `electron_domain`, etc.) returned no matches. SKIP.

## Build

```text
lake build → 3530/3530 jobs, no errors.
```

## Revert instructions

If any rename causes downstream breakage:

```bash
git checkout -- 0-Core-Formalism/lean/Semantics/Semantics/Physics/UniversalBridge.lean
git checkout -- 0-Core-Formalism/lean/Semantics/Semantics/Physics/QCLEnergy.lean
git checkout -- 0-Core-Formalism/lean/Semantics/Semantics/Physics/StringStarConstants.lean
git checkout -- 0-Core-Formalism/lean/Semantics/Semantics/Physics/NBody.lean
```
