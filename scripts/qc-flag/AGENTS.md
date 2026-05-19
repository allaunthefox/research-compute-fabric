# QC Flagger — AGENTS.md

## Purpose
Automated code quality inspection for Lean files, implementing the Lean Expert Agent's 7-check inspection protocol.

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
| 3 | Q16_16 Compliance | Float usage in hot-path code. Historical contamination sites at `BraidCross.lean:49,50,84` and `BraidStrand.lean:57,71` are the canonical fixed-point constructor template. Flag any `ofFloat` outside JSON/sensor boundary shims. |
| 4 | Proof Quality | defs without companion theorems, `.get!` without `.isSome`, native_decide coverage |
| 5 | Dependency Analysis | Unused imports, circular and transitive circular dependencies |
| 6 | Compression Theorem Pair | Every module defining a compression path MUST provide both `eigensolid_convergence` (crossing loop stabilizes) and `receipt_invertible` (receipt bijectively reconstructs original including zero/gap/timing dimensions). Flag missing pairs. |
| 7 | AGENTS.md Compliance | Root `AGENTS.md` Compression First Principles apply to all Lean code. Check that no compute path uses `ofFloat` and that receipt dimensions are explicitly captured (C, σ, k, ε_seq, t, ∅_scars). |

## Output

- **JSON**: structured per-file results with issue details
- **Markdown**: human-readable report with summary table and issue tables
- **Exit code**: 0 if all files pass, 1 if any file has ERROR-severity issues
