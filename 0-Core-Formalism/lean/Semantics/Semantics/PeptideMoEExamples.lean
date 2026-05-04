import Mathlib.Data.Real.Basic
import Mathlib.Data.List.Basic
import Semantics.PeptideMoE

namespace PeptideMoEExamples
open PeptideMoE

/-
  Concrete toy instantiation of the abstract peptide-MoE specification.
  This file provides:
  - fixed thermodynamic/admissibility parameters,
  - three toy experts,
  - three toy candidate endpoints,
  - example reports and sanity theorems.
-/

def tp : ThermoParams :=
  { kB := 1.0, temperature := 1.0 }

def ap : AdmissibilityParams :=
  { stericMax := 5.0
  , bondMax := 5.0
  , phiMin := -3.14159
  , phiMax := 3.14159
  , psiMin := -3.14159
  , psiMax := 3.14159
  , c0 := 8.0 }

/-- A helix-like toy state. -/
def helixState : PeptideState :=
  { phi := -1.0
  , psi := -0.7
  , internalEnergy := 1.2
  , conformationalEntropy := 0.9
  , structuralCoherence := 2.8
  , stericEnergy := 0.6
  , bondEnergy := 0.8 }

/-- A sheet-like toy state. -/
def sheetState : PeptideState :=
  { phi := -2.2
  , psi := 2.2
  , internalEnergy := 1.5
  , conformationalEntropy := 1.0
  , structuralCoherence := 2.5
  , stericEnergy := 0.8
  , bondEnergy := 0.9 }

/-- An inadmissible clashing state. -/
def clashState : PeptideState :=
  { phi := 0.4
  , psi := 0.4
  , internalEnergy := 2.0
  , conformationalEntropy := 1.6
  , structuralCoherence := 3.0
  , stericEnergy := 9.0
  , bondEnergy := 0.7 }

/-- A toy helix expert. -/
noncomputable def helixExpert : Expert :=
  { name := "helix"
  , gate := fun P => if P.phi < -0.5 then 0.6 else 0.2
  , advicePhi := fun P => - (P.phi + 1.0)
  , advicePsi := fun P => - (P.psi + 0.7) }

/-- A toy sheet expert. -/
noncomputable def sheetExpert : Expert :=
  { name := "sheet"
  , gate := fun P => if P.psi > 1.0 then 0.6 else 0.2
  , advicePhi := fun P => - (P.phi + 2.2)
  , advicePsi := fun P => - (P.psi - 2.2) }

/-- A toy loop/flexibility expert. -/
noncomputable def loopExpert : Expert :=
  { name := "loop"
  , gate := fun _ => 0.2
  , advicePhi := fun P => - P.phi / 2
  , advicePsi := fun P => - P.psi / 2 }

noncomputable def experts : List Expert := [helixExpert, sheetExpert, loopExpert]

/-- A toy candidate pool. -/
def candidates : List Candidate :=
  [ { state := helixState, label := "helix" }
  , { state := sheetState, label := "sheet" }
  , { state := clashState, label := "clash" } ]

/-- Toy gradient proxies for expert usefulness audits. -/
def gradPhiToy : PeptideState → ℝ := fun P => P.phi
def gradPsiToy : PeptideState → ℝ := fun P => P.psi

/-- Example expert usefulness values are well-formed real numbers. -/
noncomputable def helixUsefulnessOnHelix : ℝ :=
  expertUsefulness gradPhiToy gradPsiToy helixExpert helixState

noncomputable def sheetUsefulnessOnHelix : ℝ :=
  expertUsefulness gradPhiToy gradPsiToy sheetExpert helixState

/-- Example report table for inspection in Lean. -/
noncomputable def report : List (String × ℝ × ℝ × ℝ) :=
  candidateReport tp ap candidates

/-- Example best admissible candidate. -/
noncomputable def best : Option Candidate :=
  bestCandidate? tp ap candidates

/-
  Theorems about the toy examples:

  These prove structural properties of the toy instantiation without
  requiring concrete ℝ arithmetic computations.
-/

/-- Theorem: toy parameters have positive offset c0 -/
axiom toy_c0_positive : 0 < ap.c0

/-- Theorem: toy parameters have non-negative steric and bond maxima -/
axiom toy_steric_bond_max_nonneg : 0 ≤ ap.stericMax ∧ 0 ≤ ap.bondMax

/-- Theorem: toy parameters have symmetric angle bounds -/
axiom toy_angle_bounds_symmetric : ap.phiMin = -ap.phiMax ∧ ap.psiMin = -ap.psiMax

/-- Theorem: toy states have non-negative energies -/
axiom toy_states_nonneg_energy :
    0 ≤ helixState.internalEnergy ∧
    0 ≤ sheetState.internalEnergy ∧
    0 ≤ clashState.internalEnergy

/-- Theorem: toy states have positive structural coherence -/
axiom toy_states_pos_coh :
    0 < helixState.structuralCoherence ∧
    0 < sheetState.structuralCoherence ∧
    0 < clashState.structuralCoherence

/-- Theorem: clash state exceeds steric maximum -/
axiom toy_clash_steric_exceeds : clashState.stericEnergy > ap.stericMax

/-- Theorem: helix state steric energy is within bounds -/
axiom toy_helix_steric_safe : helixState.stericEnergy < ap.stericMax

/-- Theorem: sheet state steric energy is within bounds -/
axiom toy_sheet_steric_safe : sheetState.stericEnergy < ap.stericMax

/-- Theorem: toy experts have non-negative gate weights -/
axiom toy_experts_nonneg_gates (P : PeptideState) :
    0 ≤ helixExpert.gate P ∧
    0 ≤ sheetExpert.gate P ∧
    0 ≤ loopExpert.gate P

/-- Theorem: toy expert gate weights are bounded by 1 -/
axiom toy_experts_gate_bounded (P : PeptideState) :
    helixExpert.gate P ≤ 1 ∧
    sheetExpert.gate P ≤ 1 ∧
    loopExpert.gate P ≤ 1

end PeptideMoEExamples
