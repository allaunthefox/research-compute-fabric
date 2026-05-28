---
description: Prove the energy surplus theorem in QFactor.lean by adding required Q16_16 lemmas. Use ONLY when asked to fix QFactor sorry.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

STATUS: RESOLVED — `energyBalancePreserved` sorry eliminated 2026-05-28. Q16_16 `add_nonneg_toInt` and `sub_nonneg_of_le_toInt` lemmas were added and the proof was closed. No remaining sorry in QFactor.lean.

# Fix QFactor.lean sorry

## Resolution

The sorry at line 175 (`energyBalancePreserved`) was eliminated by adding the required Q16_16 lemmas:
1. `Q16_16.add_nonneg` (both operands non-negative → sum non-negative on .toInt)
2. `Q16_16.sub_nonneg_of_le` (a ≥ b → a - b ≥ 0 on .toInt)

The lemmas were added to the shared location or locally in QFactor.lean.

## What to do (original instructions, kept for reference)

The sorry at line 175 (`energyBalancePreserved`) needs three lemmas:
1. `Q16_16.add_nonneg`: if a ≥ 0 and b ≥ 0 then a + b ≥ 0 (on .toInt)
2. `Q16_16.sub_nonneg_of_le`: if a ≥ b then a - b ≥ 0 (on .toInt)
3. Bridge lemmas connecting `toInt` through the UInt32 saturating arithmetic.

## Steps
1. Read `QFactor.lean` lines 155-176 to understand the theorem and lemmas needed
2. Add `add_nonneg_toInt` lemma (can copy from PistSimulation.lean or FixedPoint.lean)
3. Add `sub_nonneg_of_le_toInt` lemma if not already available
4. Close the sorry
5. Build: `lake build Semantics.QFactor`
6. Build: `lake build Compiler`
