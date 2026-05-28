---
description: Fix the Picard-Lindelöf existence sorry in HamiltonianMechanics.lean (legacy). Use ONLY when asked to fix HamiltonianMechanics sorry or formalize ODE existence.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Fix HamiltonianMechanics.lean sorry

## Context

`Semantics/legacy/6point5sigma/HamiltonianMechanics.lean:391` has:

```lean
have hex : ∃ γ, IsSolutionND f x₀ γ := sorry
```

This is the Picard-Lindelöf existence theorem for ODEs. The uniqueness half (`picard_lindelof_uniqueness`) is already proven. The existence half requires:

1. Formalizing `C([-T,T])` as a complete metric space
2. The weighted-norm contraction estimate
3. The local-to-global extension argument
4. The linear growth bound `‖f(x)‖ ≤ ‖f(x₀)‖ + K‖x - x₀‖` prevents blowup

**Note:** This file is in `legacy/6point5sigma/` and is not part of the active Compiler surface. It does not block `lake build Compiler` or `lake build`. Priority is low.

## Steps

1. Read `Semantics/legacy/6point5sigma/HamiltonianMechanics.lean` around lines 380-395
2. Read the `IsSolutionND` definition and `picard_lindelof_uniqueness` theorem
3. Determine if Mathlib has a Picard-Lindelöf existence theorem that can be used
4. If not, formalize the contraction mapping argument on `C([-T,T])`
5. Build: `lake build Semantics.legacy.6point5sigma.HamiltonianMechanics` (if in lakefile)
