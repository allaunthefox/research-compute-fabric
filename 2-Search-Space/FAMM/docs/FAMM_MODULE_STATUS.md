# FAMM Module Status

Status: `HOLD_DOCUMENTED_NOT_DEAD`

Claim boundary: this document resolves the dead-code audit ambiguity for the
FAMM Lean surfaces. It does not promote every FAMM file to an active build
target. It records which files are canonical, which files are fixtures or
experiments, and which proof debts must close before promotion.

## Current Files

| File | Status | Decision |
|---|---|---|
| `FAMM.lean` | active search-space surface | keep as current canonical FAMM module in this directory |
| `FAMM_minimal.lean` | minimal lemma/proof fixture | HOLD; keep until its lemma fixtures are either ported or explicitly retired |
| `FAMM_refactored.lean` | refactor/test-vector candidate | HOLD; keep with `FAMM_refactored_test_vectors.json` until owner selects canonical replacement |
| `FAMM_hyperheuristic.lean` | WIP extension | HOLD; standalone typecheck passes with no `sorry`, but do not promote until its stronger performance-bound claims are receipted |

## Why Not Delete

The audit correctly found that `FAMM_minimal.lean` and `FAMM_refactored.lean`
are not imported by the active search-space module. That is not enough evidence
to delete them, because this directory also contains proof-space mapping,
test-vector, and Verilog fixture material.

The permanent decision is:

```text
unimported != dead
unreceipted != active
```

So the files are retained as documented HOLD surfaces until a later pass either:

1. ports their unique fixtures into the canonical module,
2. moves them under an explicit archive/fixture path, or
3. removes them with owner approval and a receipt.

## Proof Debt

`FAMM_hyperheuristic.lean` now typechecks without `sorry` with:

```text
cd 0-Core-Formalism/lean/Semantics
lake env lean ../../../2-Search-Space/FAMM/FAMM_hyperheuristic.lean
```

The closed local laws are:

- out-of-bounds hyper-heuristic adjustment fails closed,
- switch count is monotone,
- a concrete LUT entry replays to its projected best heuristic.

The remaining documented proof debt is not a `sorry` in source. It is the
stronger performance-bound claim:

```text
LUT lookup existence does not by itself prove a frustration bound against
missPath.performanceHistory.
```

Those are real theorem-shape issues, not syntax cleanup. The next Lean pass
should split over-broad theorem statements into smaller replayable laws before
trying to close them.

## Receipt

Machine-readable status receipt:

```text
shared-data/data/stack_solidification/famm_module_status_receipt.json
```
