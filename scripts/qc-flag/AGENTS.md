# QC Flagger — AGENTS.md

## Purpose
Automated code quality inspection for Lean files, implementing the Lean Expert Agent's 5-point inspection protocol.

## Usage

```bash
# Run on a single file
python3 scripts/qc-flag/lean_qc_flagger.py path/to/file.lean

# Run on a directory (recursive)
python3 scripts/qc-flag/lean_qc_flagger.py path/to/dir/

# Save reports
python3 scripts/qc-flag/lean_qc_flagger.py path/to/file.lean --json report.json --markdown report.md

# Shell wrapper (saves dated reports to scripts/qc-flag/reports/)
bash scripts/qc-flag/run_qc_flag.sh path/to/file.lean
bash scripts/qc-flag/run_qc_flag.sh path/to/dir/ --verbose
```

## Protocol Coverage

| # | Check | Implementation |
|---|-------|----------------|
| 1 | Structural Health | theorem/def/eval/sorry counts, empty theorems, tautologies, unused imports, `set_option` suppressions |
| 2 | Naming Conventions | PascalCase files/types, camelCase functions/theorems, banned prefixes/suffixes |
| 3 | Q16_16 Compliance | Float usage in hot-path code |
| 4 | Proof Quality | defs without companion theorems, `.get!` without `.isSome`, native_decide coverage |
| 5 | Dependency Analysis | Unused imports, circular and transitive circular dependencies |

## Output

- **JSON**: structured per-file results with issue details
- **Markdown**: human-readable report with summary table and issue tables
- **Exit code**: 0 if all files pass, 1 if any file has ERROR-severity issues
