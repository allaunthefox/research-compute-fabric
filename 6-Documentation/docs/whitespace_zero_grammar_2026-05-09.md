# Whitespace-Zero Grammar Probe

**Date:** 2026-05-09

Zero whitespace-code grammar for canonical single-space token streams. Whitespace is reconstructed from symbol count/order. Non-canonical spacing requires an explicit residual and is not admitted by this gate.

## Rule

- Store symbol payloads.
- Store zero ordinary whitespace codes.
- Reconstruct one canonical display space between adjacent symbols.
- HOLD any non-canonical whitespace unless a residual is declared.

## Status

- Lean module: `Semantics.WhitespaceFreeGrammar`
- Lean build: `PASS`
- Probe status: `PASS_ZERO_WHITESPACE_CANONICAL`
- Admitted canonical fixtures: `3`
- HOLD fixtures needing residual: `3`
- Stored whitespace codes total: `0`

## Cases

- `canonical_1`: `ADMIT_FIXTURE`, symbols `5`, payload `42` bytes, raw `46` bytes, derived boundaries `4`, exact replay `True`
- `canonical_2`: `ADMIT_FIXTURE`, symbols `5`, payload `21` bytes, raw `25` bytes, derived boundaries `4`, exact replay `True`
- `canonical_3`: `ADMIT_FIXTURE`, symbols `6`, payload `37` bytes, raw `42` bytes, derived boundaries `5`, exact replay `True`
- `hold_1`: `HOLD_NEEDS_WHITESPACE_RESIDUAL`, symbols `4`, payload `21` bytes, raw `25` bytes, derived boundaries `3`, exact replay `False`
- `hold_2`: `HOLD_NEEDS_WHITESPACE_RESIDUAL`, symbols `4`, payload `25` bytes, raw `29` bytes, derived boundaries `3`, exact replay `False`
- `hold_3`: `HOLD_NEEDS_WHITESPACE_RESIDUAL`, symbols `3`, payload `16` bytes, raw `18` bytes, derived boundaries `2`, exact replay `False`

## Machine Receipt

- `shared-data/data/stack_solidification/whitespace_zero_grammar_probe.json`
