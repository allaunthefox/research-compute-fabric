# Skepticism Gradient Reassessment - 2026-04-29

## Gate

Sigma language is valid only for statistical surprise claims, such as detection
confidence, model-selection confidence, false-positive rates, and benchmark
deltas with enough samples to justify a distributional claim.

Sigma language is not a validator for:

- Lean theorem correctness
- Compression ratios
- Physical measurements
- Hardware extraction
- Biological or cognitive claims
- Workflow telemetry

## Applied Alignment

- Updated `docs/AGENTS.md` so the PR checklist and claim-state ladder require
  domain-specific validators instead of universal uncertainty/sigma wording.
- Downgraded manifesto and architecture claims that used sigma as proof quality.
- Reworded FPGA, physics, compression, and numerical-analysis docs to require
  theorem/build evidence, SI measurement provenance, corpus provenance, baseline
  comparison, or audit evidence as appropriate.
- Reworded Lean comments and output strings where "6.5 sigma formal
  verification" was being used as shorthand for proof/build gates.
- Preserved legitimate statistical sigma use for statistical intervals and
  finite-regime extrapolation, while marking scope limits where needed.

## Filename Alignment

See `docs/FILENAME_ALIGNMENT_AUDIT_2026-04-29.md` for the rename pass and the
remaining import-sensitive Lean filename debt.

## Verification Run

- `git diff --check`: clean.
- Generated junk scan: clean.
- `python3 -m py_compile 5-Applications/text-to-cad/models/mobile_microgripper_sci_refined.py`: passed.
- `lake env lean 0-Core-Formalism/lean/Semantics/Semantics/S3C.lean`: passed.
- `lake env lean 0-Core-Formalism/lean/Semantics/Quarantine/Q064Experimental.lean`: passed.
- `lake env lean 0-Core-Formalism/lean/Semantics/Semantics/MOFCO2Reduction.lean`: elaborated with two existing `sorry` warnings.

## Known Build Limits

Targeted Lean checks for several touched files still hit pre-existing missing
`.olean` dependencies or existing theorem errors. This pass did not claim full
Lean build health.
