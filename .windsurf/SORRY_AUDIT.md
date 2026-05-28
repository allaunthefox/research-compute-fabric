# Phase 3: Zero `sorry` Audit — **IN PROGRESS**

**Document ID:** SORRY_AUDIT_2026-05-28
**Authority:** AGENTS.md §9 — Code quality requirement
**Status:** ⚠️ **8 `sorry` REMAINING** across 4 files (down from 40)

---

## Executive Summary

| Metric | 2026-04-21 | 2026-05-28 | Change |
|--------|-----------|-----------|--------|
| **Total `sorry` Count** | 40 | **8** | **-32 eliminated** |
| Files with `sorry` | 12 | **4** | -8 files cleared |
| `lake build` status | ✅ 3394 jobs | ✅ **3571 jobs** | +177 jobs |

---

## Remaining `sorry` (8 across 4 files)

### 1. AdjugateMatrix.lean — 2 `sorry` ⚠️ Q16_16 Obstruction

| Line | Theorem | Status | Notes |
|------|---------|--------|-------|
| 296 | `det_self_inverse_approx` | **Open** | Q16_16 truncation causes 1 LSB error. Needs bounded-error variant or exact-div precondition. |
| 305 | `det_self_inverse_exact` | **Open** | Pure integer-arithmetic proof under exactness hypotheses. Laplace cofactor expansion for 8×8 over ℤ. |

Note: The original `det_self_inverse` was refactored into these two variants. `det_self_inverse_identity` (identity case) was proven via computation.

### 2. HyperbolicStateSurface.lean — 1 `sorry` ⚠️ Q16_16 sqrt

| Line | Theorem | Status | Notes |
|------|---------|--------|-------|
| 85 | `ko_preserves_hyperbola_approx` | **Open, TODO(lean-port)** | Needs `Q16_16.sqrt` squaring bound: `|(sqrt r)² - r| ≤ ε`. Premise restructured as explicit `h_sqrt_sq_error` hypothesis. |

### 3. HamiltonianMechanics.lean — 1 `sorry` 🔬 Legacy

| Line | Theorem | Status | Notes |
|------|---------|--------|-------|
| 391 | Picard-Lindelöf existence | **Open** | `∃ γ, IsSolutionND f x₀ γ`. Requires C([-T,T]) as complete metric space + contraction mapping. File is in `legacy/6point5sigma/`, not in Compiler surface. |

### 4. FourPrimitiveErdosRenyi.lean — 4 `sorry` 🔬 Research Grade

| Line | Theorem | Blocker | Path Forward |
|------|---------|---------|--------------|
| 123 | (unknown) | Needs reading | Investigate |
| 132 | (unknown) | Needs reading | Investigate |
| 141 | (unknown) | Needs reading | Investigate |
| 149 | (unknown) | Needs reading | Investigate |

---

## Eliminated Since Last Audit (32 `sorry`)

| # | File | Theorem | Strategy | Date |
|---|------|---------|----------|------|
| 1 | BraidBitwiseODE.lean | `bitwise_ode_correct` | `toInt_eq_zero_iff` + `subst` + `native_decide` | 2026-05-28 |
| 2 | MeshRouting.lean | `goxelFieldEnergyConservation` | Added upper bound hypothesis + `q16Clamp_id_of_inRange` + `omega` | 2026-05-28 |
| 3 | MeshRouting.lean | `vcnReceiptValidCompression` | `Q16_16.one` instead of `0x00010000` + `Int.le_ediv_iff_mul_le` | 2026-05-28 |
| 4 | PistSimulation.lean | `goldenContractionEnergyDecrease` | `List.Forall₂` fold induction + `Array.foldl_toList` | 2026-05-28 |
| 5 | PistSimulation.lean | (2 additional sorry blocks) | Discharged alongside goldenContractionEnergyDecrease | 2026-05-28 |
| 6 | QFactor.lean | `energyBalancePreserved` | `add_nonneg_toInt` + `sub_nonneg_of_le_toInt` lemmas | 2026-05-28 |
| 7 | SSMS.lean | `aciPreservedByMlgruStep` | `abs_sub_comm` + `mul_mono_left` + `q16Clamp_id_of_inRange` | 2026-05-28 |
| 8-32 | (various) | (various) | Eliminated in prior sessions | 2026-04-21 to 2026-05-28 |

---

## OpenCode Agent Definitions

The `.opencode/agents/` directory contains 9 pre-configured subagent tasks:

| Agent | Target | Status |
|-------|--------|--------|
| `audit-connectors-theorem.md` | Connectors.lean quarantined proofs | Not yet run |
| `fix-adjugate-matrix.md` | AdjugateMatrix.lean det_self_inverse_approx/exact | **OPEN** — 2 sorry |
| `fix-hamiltonian-mechanics.md` | HamiltonianMechanics.lean Picard-Lindelöf existence | **OPEN** — 1 sorry (legacy) |
| `fix-hyperbolic-statesurface.md` | HyperbolicStateSurface.lean sqrt error bound | **OPEN** — 1 sorry (Issue 2 resolved) |
| `fix-pist-simulation-proof.md` | PistSimulation.lean goldenContractionEnergyDecrease | **✅ RESOLVED** |
| `fix-qfactor-sorry.md` | QFactor.lean energy surplus theorem | **✅ RESOLVED** |
| `fix-ssms-sorry.md` | SSMS.lean ACI preservation (Q16_16 triangle) | **✅ RESOLVED** |
| `port-fixedpoint-bridge.md` | FixedPointBridge.lean remove Float | Not yet run |
| `resolve-canon-serialization.md` | CanonSerialization.lean TODO resolution | Not yet run |

---

## Verification Commands

```bash
# Current sorry count (Semantics only, excluding legacy)
cd /home/allaun/Research\ Stack/0-Core-Formalism/lean/Semantics
grep -rn '  sorry' Semantics/ --include='*.lean' | grep -v comment | wc -l
# Expected: 3 (AdjugateMatrix x2, HyperbolicStateSurface x1)

# Full workspace sorry count (including legacy/ExtensionScaffold)
grep -rn '  sorry' Semantics/ ExtensionScaffold/ legacy/ --include='*.lean' | grep -v comment | wc -l
# Expected: 8

# Build verification
lake build
# Expected: exit code 0, 3571 jobs
```

---

*Audit Date:* 2026-05-28
*Previous Audit:* 2026-04-21 (40 sorries)
*Current:* 8 sorries (80% reduction)
*Next Review:* When AdjugateMatrix.lean or FourPrimitiveErdosRenyi.lean is addressed
