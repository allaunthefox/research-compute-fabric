# Filename Alignment Audit - 2026-04-29

## Applied Low-Risk Renames

- `docs/field_equation_comparison.md` -> `docs/FIELD_EQUATION_COMPARISON.md`
- `docs/geometry/BUCKYBALL_6.5SIGMA_HARD_BOUNDS.md` -> `docs/geometry/BUCKYBALL_STATISTICAL_HARD_BOUNDS.md`
- `Q0_64_Experimental.lean` -> `0-Core-Formalism/lean/Semantics/Quarantine/Q064Experimental.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/MOF_CO2_Reduction.lean` -> `0-Core-Formalism/lean/Semantics/Semantics/MOFCO2Reduction.lean`

## Current Naming Rule

Per `docs/AGENTS.md`, live Lean module files should use `PascalCase.lean`.
Python, shell, Verilog, JSON, JSONL, TSV, and data artifacts retain their
ecosystem-native naming unless a local convention says otherwise.

## Remaining Import-Sensitive Lean Name Debt

These should be renamed only with import/reference updates and a targeted
`lake build` pass:

- `0-Core-Formalism/lean/Semantics/ExtensionScaffold/Seed/uSeed.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/Q16_16.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/S3C_test.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/S3C_test2.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/SSMS_nD.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/WSM_WR_EGS_WC.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/WSM_WR_EGS_WC_Mathlib.lean`
- `0-Core-Formalism/lean/Semantics/Semantics/WSM_WR_EGS_WC_Mathlib_temp.lean`

Archived prior art and generated metadata were excluded from this rename pass.
