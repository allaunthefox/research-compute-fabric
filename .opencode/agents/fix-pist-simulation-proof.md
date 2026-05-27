---
description: Complete the goldenContractionEnergyDecrease proof in PistSimulation.lean. Use ONLY when asked to fix PistSimulation pending proofs or resolve TODO(lean-port) markers in Semantics/PistSimulation.lean.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Fix PistSimulation pending proof

## Context

`Semantics/PistSimulation.lean` has three `TODO(lean-port)` markers with `sorry` blocks:

- Line 1317: `TODO(lean-port): complete the proof; currently verified by #eval`
- Line 1604: `TODO(lean-port): complete the proof; currently verified by #eval`
- Line 1614: `TODO(lean-port): General proof requires Jensen's inequality for discrete`

The P0 target is line 1614: `goldenContractionEnergyDecrease` — a theorem requiring Jensen's inequality for discrete convex combinations on Q16_16. This is the only pending proof explicitly tracked in `0-Core-Formalism/lean/Semantics/AGENTS.md` under "Pending Proof Work."

## What to do

1. Read `Semantics/PistSimulation.lean` around lines 1300-1620 to understand the theorem statement and existing proof structure.
2. Read `Semantics/FixedPoint.lean` and `Semantics/Q16_16.lean` for available Q16_16 lemmas.
3. Attempt to complete the proof using Jensen's inequality for discrete convex combinations.
4. If a full proof is not possible, add a detailed blocker comment explaining what lemmas are missing.
5. Run `lake build Semantics.PistSimulation` to verify no build breaks.
6. Run `lake build Compiler` to verify the narrow surface.

## Constraints

- Do NOT delete or comment-out the theorem — either fix the proof or leave the `sorry` + `TODO(lean-port)` intact.
- Do NOT import Float (`ofFloat`) — use `Q16_16.ofNat`/`Q16_16.ofRatio`/`Q16_16.ofInt`.
- If the proof requires Jensen's inequality, look for or create a `convexOn` lemma on Q16_16 before using generic mathlib versions.
