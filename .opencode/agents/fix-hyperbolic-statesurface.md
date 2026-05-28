---
description: Fix HyperbolicStateSurface.lean sqrt error-bound sorry. Use ONLY when asked to fix HyperbolicStateSurface.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Fix HyperbolicStateSurface.lean

One remaining issue (Issue 2 was resolved previously):

## Issue 1 (line 85, sorry) — STILL OPEN
`ko_preserves_hyperbola_approx` — needs a formal error-bound lemma for Q16_16.sqrt:
`(Q16_16.sqrt r)² ≈ r` up to 1 LSB rounding.

The theorem has been restructured: `onHyperbolaApprox` is now an explicit premise
(`h_sqrt_sq_error`) rather than a sorry in the conclusion. The sorry at line 85
is where the premise should be discharged from a formal `Q16_16.sqrt` squaring bound.

Available lemmas: `Q16_16.sqrt_zero`, `Q16_16.sqrt_one`. The sqrt implementation
is at `FixedPoint.lean:289` (Newton approximation). The lemma can be weaker:
`|(sqrt r)² - r| ≤ ε` for some small ε, or just prove the specific case needed
by the calling theorem.

## Issue 2 (lines 207/215) — RESOLVED
~~Type mismatch: `Vector HyperState n` vs `List.Vector HyperState n`.~~ Fixed in prior session.

## Steps
1. Read the full file: `Semantics/Extensions/HyperbolicStateSurface.lean`
2. Focus on line 85: prove `Q16_16.abs (Q16_16.sqrt x * Q16_16.sqrt x - x) ≤ Q16_16.epsilon`
   for non-negative `x`, or prove the specific instance used by `ko_preserves_hyperbola_approx`
3. Build: `lake build Semantics.Extensions.HyperbolicStateSurface`
4. Build: `lake build Compiler`
