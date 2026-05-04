import Semantics.Atoms
import Semantics.Lemmas

namespace Semantics.ENE

-- Decomposition
--
-- Defines how semantic objects reduce to atoms.
-- Every complex thing must prove what it is made of.
-- Uses Q16_16 fixed-point (UInt32) for weights per AGENTS.md §1.4.

/-- A weighted atom pairs an atom with an importance score (Q16_16). -/
structure WeightedAtom where
  atom : Atom
  weight : UInt32

deriving Repr, BEq

/-- An atomic decomposition breaks a semantic object into weighted atoms. -/
structure AtomicDecomposition where
  source : Lemma
  atoms : List WeightedAtom

deriving Repr, BEq

/-- A decomposition witness certifies that a decomposition was derived lawfully. -/
structure DecompositionWitness where
  decomposition : AtomicDecomposition
  derivationPath : List String
  timestamp : UInt32

deriving Repr, BEq

/-- Extract just the atoms (without weights) from a decomposition. -/
def AtomicDecomposition.unweighted (d : AtomicDecomposition) : List Atom :=
  d.atoms.map (λ wa => wa.atom)

/-- A decomposition is nonempty if it contains at least one atom. -/
def AtomicDecomposition.nonempty (d : AtomicDecomposition) : Prop :=
  d.atoms.length > 0

/-- A decomposition is faithful if its unweighted atoms exactly match the lemma's signature. -/
def FaithfulDecomposition (l : Lemma) (d : AtomicDecomposition) : Prop :=
  d.source = l ∧ d.unweighted = l.sig

/-- Two decompositions are equivalent if they have the same source and the same unweighted atoms. -/
def DecompositionEquivalent (d1 d2 : AtomicDecomposition) : Prop :=
  d1.source = d2.source ∧ d1.unweighted = d2.unweighted

-- Theorems about decomposition

/-- A faithful decomposition must be nonempty if the lemma's signature is nonempty. -/
theorem faithful_decomposition_nonempty
  (l : Lemma)
  (d : AtomicDecomposition)
  (h : FaithfulDecomposition l d)
  (hn : l.sig ≠ []) :
  d.atoms.length > 0 := by
  -- First show d.atoms.length = l.sig.length
  have eq1 : d.atoms.length = l.sig.length := by
    have map_eq : List.map WeightedAtom.atom d.atoms = l.sig := by
      rw [h.2.symm]
      rfl
    have len_eq : (List.map WeightedAtom.atom d.atoms).length = d.atoms.length := by
      simp [List.length_map]
    rw [← len_eq, map_eq]
  -- Then show l.sig.length > 0 from hn
  have pos1 : l.sig.length > 0 := by
    apply Nat.zero_lt_of_ne_zero
    intro h0
    apply hn
    exact List.eq_nil_of_length_eq_zero h0
  -- Combine to get conclusion
  rw [eq1]
  exact pos1

/-- Equivalent decompositions have the same unweighted atoms. -/
theorem equivalent_decompositions_same_atoms
  (d1 d2 : AtomicDecomposition)
  (h : DecompositionEquivalent d1 d2) :
  d1.unweighted = d2.unweighted := by
  unfold DecompositionEquivalent at h
  exact h.2

end Semantics.ENE
