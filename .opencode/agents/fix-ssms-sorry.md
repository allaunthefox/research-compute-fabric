---
description: Prove the ACI preservation theorem in SSMS.lean by adding required Q16_16 triangle inequality lemmas. Use ONLY when asked to fix SSMS sorry.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

STATUS: RESOLVED — `aciPreservedByMlgruStep` sorry eliminated 2026-05-28. The proof was completed using `abs_sub_comm`, `mul_mono_left`, `q16Clamp_id_of_inRange`, and `f_eps`/`omf_eps` sub-lemmas. No remaining sorry in SSMS.lean.

# Fix SSMS.lean sorry

## Resolution

The sorry at line 576 (`aciPreservedByMlgruStep`) was eliminated. The proof uses:
- `abs_sub_comm` with correct argument ordering (lines 559–571)
- `f_eps` and `omf_eps` sub-lemmas proved via `mul_mono_left` + `one_mul` (lines 605–614)
- `omf_toInt` equality proved via `q16Clamp_id_of_inRange` (lines 575–599)
- `h_ft_range` hypothesis added to theorem signature (line 546)

## What to do (original instructions, kept for reference)

The sorry at line 576 (`aciPreservedByMlgruStep`) needs Q16_16 lemmas:
1. Triangle inequality: `abv_add_le` or similar
2. `mul_le_of_nonneg_of_le`
3. `sub_eq_add_neg` for Q16_16

The blocker comment (lines 529-533) says: "Q16_16 uses saturating arithmetic over UInt32, which makes these algebraic lemmas non-trivial."

## Approach
The simplest fix may be to prove a weaker version that works for the specific case: if all inputs are non-negative and in range, the saturating arithmetic behaves like standard integer arithmetic.

## Steps
1. Read `SSMS.lean` around lines 529-576 to understand the theorem
2. Assess which Q16_16 lemmas are missing
3. Either add them locally or use existing lemmas
4. Close the sorry
5. Build: `lake build Semantics.SSMS`
6. Build: `lake build Compiler`
