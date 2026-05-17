# QC Flagger Build DAG — Automated Inspection Tool

**Date:** 2026-05-13

## Files Created
- `scripts/qc-flag/lean_qc_flagger.py`
- `scripts/qc-flag/run_qc_flag.sh`
- `scripts/qc-flag/AGENTS.md`

## Verification
- **Test run:** `python3 scripts/qc-flag/lean_qc_flagger.py 0-Core-Formalism/lean/Semantics/Semantics/Physics/UniversalBridge.lean`
- **Result:** PASS — 10 issues found (all WARNING, no ERROR)
- **Errors:** None (script runs without errors)

## Protocol Coverage
| # | Protocol Point | Implemented |
|---|----------------|-------------|
| 1 | Structural Health | YES |
| 2 | Naming Conventions | YES |
| 3 | Q16_16 Compliance | YES |
| 4 | Proof Quality | YES |
| 5 | Dependency Analysis | YES |

## Test Results

### Single file scan
```bash
python3 scripts/qc-flag/lean_qc_flagger.py \
  0-Core-Formalism/lean/Semantics/Semantics/Physics/UniversalBridge.lean
```
- 26 theorems, 20 defs, 11 #eval!, 0 sorries
- 10 issues: 9 naming, 1 proof quality
- Verdict: PASS

### Directory scan (20 files)
```bash
python3 scripts/qc-flag/lean_qc_flagger.py \
  0-Core-Formalism/lean/Semantics/Semantics/Physics/
```
- 20/20 files pass
- 227 total issues (0 ERROR, 227 WARNING/INFO)
- Comment filtering: correctly ignores `sorry`/`Float`/type names in comments
- Data defs (`struct { ... }`, integer constants): correctly excluded from companion theorem check

### Shell wrapper
```bash
bash scripts/qc-flag/run_qc_flag.sh \
  0-Core-Formalism/lean/Semantics/Semantics/Physics/UniversalBridge.lean
```
- Reports saved to `scripts/qc-flag/reports/<timestamp>/`
- JSON + Markdown output generated

### Python compile check
```bash
python3 -m py_compile scripts/qc-flag/lean_qc_flagger.py
```
- Compiles cleanly (stdlib only, no external dependencies)

## Exit Codes
- 0: all files pass (no ERROR-severity issues)
- 1: at least one file has ERROR-severity issues
