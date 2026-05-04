/-
AlphabetReduction.lean — Biological Alphabet Reduction Filter v0.1

Core lesson:
  Local edit viability does not imply composed-system viability.

No Float. No probabilistic claims. No claim that a true 19-amino-acid organism
has been built.
-/

import Std

namespace Semantics.AlphabetReduction

inductive ClaimState where
  | beautifulProvisional
  | calibratedEngineeringDelta
  | reviewed
  deriving Repr, DecidableEq, Inhabited

inductive AminoAcid where
  | Ala | Arg | Asn | Asp | Cys
  | Gln | Glu | Gly | His | Ile
  | Leu | Lys | Met | Phe | Pro
  | Ser | Thr | Trp | Tyr | Val
  deriving Repr, DecidableEq, Inhabited

structure Alphabet where
  contains : AminoAcid → Bool

def canonical20 : Alphabet :=
  { contains := fun _ => true }

def noIleAlphabet : Alphabet :=
  { contains := fun aa =>
      match aa with
      | .Ile => false
      | _ => true }

structure SymbolDeletion where
  removed : AminoAcid
  deriving Repr, DecidableEq, Inhabited

structure Subsystem where
  name : String
  proteinCount : Nat
  deriving Repr, DecidableEq, Inhabited

structure LocalEdit where
  editId : String
  targetProtein : String
  removes : AminoAcid
  replacements : List AminoAcid
  compensatoryMutationCount : Nat
  fitness : Nat
  deriving Repr, DecidableEq, Inhabited

structure ComposedEdit where
  batchId : String
  edits : List LocalEdit
  fitness : Nat
  deriving Repr, DecidableEq, Inhabited

def PassesLocalGate (threshold : Nat) (e : LocalEdit) : Prop :=
  threshold ≤ e.fitness

def PassesCompositionGate (threshold : Nat) (c : ComposedEdit) : Prop :=
  threshold ≤ c.fitness

def AllLocalPass (threshold : Nat) (edits : List LocalEdit) : Prop :=
  ∀ e, e ∈ edits → PassesLocalGate threshold e

def localPassA : LocalEdit :=
  { editId := "local-pass-a"
    targetProtein := "ribosomal-protein-a"
    removes := .Ile
    replacements := [.Val, .Leu]
    compensatoryMutationCount := 2
    fitness := 90 }

def localPassB : LocalEdit :=
  { editId := "local-pass-b"
    targetProtein := "ribosomal-protein-b"
    removes := .Ile
    replacements := [.Leu]
    compensatoryMutationCount := 8
    fitness := 91 }

def composedFail : ComposedEdit :=
  { batchId := "composed-fail"
    edits := [localPassA, localPassB]
    fitness := 0 }

theorem localPassA_passes_90 : PassesLocalGate 90 localPassA := by
  unfold PassesLocalGate localPassA
  decide

theorem localPassB_passes_90 : PassesLocalGate 90 localPassB := by
  unfold PassesLocalGate localPassB
  decide

theorem composedFail_fails_90 : ¬ PassesCompositionGate 90 composedFail := by
  unfold PassesCompositionGate composedFail
  decide

theorem local_viability_does_not_imply_composed_viability :
    ∃ c : ComposedEdit,
      AllLocalPass 90 c.edits ∧ ¬ PassesCompositionGate 90 c := by
  refine ⟨composedFail, ?_, composedFail_fails_90⟩
  intro e h
  simp [composedFail] at h
  cases h with
  | inl hA =>
      subst e
      exact localPassA_passes_90
  | inr hRest =>
      cases hRest with
      | inl hB =>
          subst e
          exact localPassB_passes_90
      | inr hNil =>
          cases hNil

structure AlphabetReductionResult where
  subsystem : Subsystem
  deletion : SymbolDeletion
  localEditsValidated : Nat
  composedEditsIntegrated : Nat
  removedResidueCount : Nat
  generationsObserved : Nat
  fitness : Nat
  claimState : ClaimState
  caveat : String
  deriving Repr, Inhabited

def ec19ProvisionalRecord : AlphabetReductionResult :=
  { subsystem := { name := "E. coli ribosomal proteins", proteinCount := 52 }
    deletion := { removed := .Ile }
    localEditsValidated := 21
    composedEditsIntegrated := 21
    removedResidueCount := 382
    generationsObserved := 450
    fitness := 90
    claimState := .beautifulProvisional
    caveat := "Partial ribosomal-protein alphabet reduction; not a true 19-amino-acid organism." }

def ResultPassesFitnessGate (threshold : Nat) (r : AlphabetReductionResult) : Prop :=
  threshold ≤ r.fitness

theorem ec19_record_passes_90_gate :
    ResultPassesFitnessGate 90 ec19ProvisionalRecord := by
  unfold ResultPassesFitnessGate ec19ProvisionalRecord
  decide

end Semantics.AlphabetReduction
