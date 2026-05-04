import Mathlib
import AVMRCore

/-! # AVMR Classification
Event classification to DNA bases.
Split from AVMRProofs.lean per swarm suggestion (USER AUTHORIZED).
-/

/-- The four axial generators correspond to DNA bases -/
inductive EventType | a | g | c | t
  deriving Repr, BEq, DecidableEq

/-- Classification of shell positions to DNA bases.
    These 4 special positions on each shell correspond to
    the 4 nucleotide bases, mapping structural features
    to biochemical properties:
    - a (n = k²):        Purine, 2 H-bonds (A)
    - g (n = k² + k):    Purine, 3 H-bonds (G)  
    - c (n = k² + k + 1): Pyrimidine, 3 H-bonds (C)
    - t (n = (k+1)² - 1): Pyrimidine, 2 H-bonds (T)
-/
def classifyEvent (s : ShellState) : Option EventType :=
  let k := s.k; let n := s.n
  if n = k*k then some .a
  else if n = k*k + k then some .g
  else if n = k*k + k + 1 then some .c
  else if n = (k+1)*(k+1) - 1 then some .t
  else none
