import Mathlib

/-! # AVMR Core
Shell decomposition foundation structures and functions.
Split from AVMRProofs.lean per swarm suggestion (USER AUTHORIZED).
-/

/-- ShellState represents the decomposition n = k² + a, b = (k+1)² - n -/
structure ShellState where
  n : Nat
  k : Nat
  a : Nat
  b : Nat
  deriving Repr, BEq

/-- TipCoord captures the physical interpretation of shell position -/
structure TipCoord where
  mass : Int      -- a·b = GC_content × H_bond_energy
  polarity : Int  -- a - b = AT_skew
  deriving Repr, BEq

/-- Square shell decomposition: n = k² + a where k = ⌊√n⌋ -/
def shellState (n : Nat) : ShellState :=
  let k := Nat.sqrt n
  let a := n - k*k
  let b := (k+1)*(k+1) - n
  { n := n, k := k, a := a, b := b }

/-- Verify: n = k² + a (shell identity) -/
lemma squareShellIdentity (n : Nat) :
  let s := shellState n
  s.n = s.k * s.k + s.a := by
  dsimp [shellState]
  let k := Nat.sqrt n
  have hk : k*k ≤ n := Nat.sqrt_le n
  omega

/-- Verify: (k+1)² = n + b (complementary identity) -/
lemma complementaryIdentity (n : Nat) :
  let s := shellState n
  (s.k + 1) * (s.k + 1) = s.n + s.b := by
  dsimp [shellState]
  let k := Nat.sqrt n
  have hk1 : n < (k+1)*(k+1) := Nat.lt_succ_sqrt n
  have hk2 : k*k ≤ n := Nat.sqrt_le n
  omega
