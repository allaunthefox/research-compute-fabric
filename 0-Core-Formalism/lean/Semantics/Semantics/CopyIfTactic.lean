/-
CopyIfTactic.lean — Pre-filter tactic for Lean 4

Implements the copy-if pattern as a native Lean tactic:
1. Check if goal is trivially closable (zero delta) → close immediately
2. If non-trivial (non-zero delta) → delegate to solver

Usage:
  theorem foo : 1 = 1 := by copy_if
  theorem bar : x + 0 = x := by copy_if
  theorem baz : complex_statement := by copy_if

The tactic tries fast closers in order of cost:
  1. rfl (instant — zero delta)
  2. decide (fast — decidable)
  3. omega (fast — linear arithmetic)
  4. simp (slow — full simplification)
-/
import Mathlib.Tactic

namespace Semantics.CopyIfTactic

open Lean Elab Tactic

/-- The copy_if tactic: try fast closers in order, fail if none work.
    Lean implementation of the vectorized copy_if pattern.
    Each closer is a "zero delta" check — if the goal is already in
    normal form for that tactic, it closes instantly. -/
macro "copy_if" : tactic => `(tactic|
  first
  | rfl
  | decide
  | omega
  | norm_num
  | simp
  | fail "copy_if: non-trivial goal, needs solver"
)

/-- The copy_if? tactic: like copy_if but reports which closer worked. -/
elab "copy_if?" : tactic => do
  let tactics : List (String × Syntax) := [
    ("rfl",     ← `(tactic| rfl)),
    ("decide",  ← `(tactic| decide)),
    ("omega",   ← `(tactic| omega)),
    ("norm_num",← `(tactic| norm_num)),
    ("simp",    ← `(tactic| simp)),
  ]

  for (name, tac) in tactics do
    try
      evalTactic tac
      logInfo s!"copy_if?: closed with {name}"
      return
    catch _ =>
      continue

  logWarning "copy_if?: non-trivial goal"
  throwError "copy_if?: goal is non-trivial"

end Semantics.CopyIfTactic
